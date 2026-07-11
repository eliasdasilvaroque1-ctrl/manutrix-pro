/**
 * Offline Queue Engine for MAINTRIX — RC1 Field Operations
 * Stores pending operations in IndexedDB and syncs when online.
 * Supports: text mutations, photo blobs, exponential backoff, ordered sync.
 */

const DB_NAME = 'maintrix_offline';
const DB_VERSION = 2;
const STORE_NAME = 'pending_operations';
const CACHE_STORE = 'cached_data';
const PHOTO_STORE = 'pending_photos';

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
        store.createIndex('status', 'status', { unique: false });
        store.createIndex('priority', 'priority', { unique: false });
      }
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'key' });
      }
      if (!db.objectStoreNames.contains(PHOTO_STORE)) {
        db.createObjectStore(PHOTO_STORE, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ============== OPERATION QUEUE ==============

// Queue a mutation for later sync
// priority: 1=create, 2=status-change, 3=update, 4=attachment
export async function queueOperation(operation) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const record = {
      ...operation,
      timestamp: Date.now(),
      retries: 0,
      status: 'pending',
      priority: operation.priority || 2,
    };
    const req = store.add(record);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// Get all pending operations
export async function getPendingOperations() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result.filter(r => r.status === 'pending'));
    req.onerror = () => reject(req.error);
  });
}

// Get count of pending ops (operations + photos)
export async function getPendingCount() {
  const ops = await getPendingOperations();
  const photos = await getPendingPhotos();
  return ops.length + photos.length;
}

// Remove a completed operation
export async function removeOperation(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// Mark operation as failed with exponential backoff tracking
export async function markRetry(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(id);
    getReq.onsuccess = () => {
      const record = getReq.result;
      if (record) {
        record.retries = (record.retries || 0) + 1;
        // Exponential backoff: don't retry for 2^retries seconds
        record.nextRetryAt = Date.now() + Math.min(Math.pow(2, record.retries) * 1000, 300000);
        if (record.retries >= 10) record.status = 'failed';
        store.put(record);
      }
      resolve();
    };
    getReq.onerror = () => reject(getReq.error);
  });
}

// ============== PHOTO QUEUE ==============

// Store a photo blob for offline upload
export async function queuePhoto({ entityType, entityId, categoria, blob, filename }) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(PHOTO_STORE, 'readwrite');
    const store = tx.objectStore(PHOTO_STORE);
    const record = {
      entityType,
      entityId,
      categoria: categoria || 'foto',
      blob,
      filename: filename || `photo_${Date.now()}.jpg`,
      timestamp: Date.now(),
      status: 'pending',
    };
    const req = store.add(record);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function getPendingPhotos() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(PHOTO_STORE, 'readonly');
    const store = tx.objectStore(PHOTO_STORE);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result.filter(r => r.status === 'pending'));
    req.onerror = () => reject(req.error);
  });
}

export async function removePhoto(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(PHOTO_STORE, 'readwrite');
    const store = tx.objectStore(PHOTO_STORE);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ============== DATA CACHE (READ) ==============

export async function cacheData(key, data) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(CACHE_STORE, 'readwrite');
    const store = tx.objectStore(CACHE_STORE);
    store.put({ key, data, timestamp: Date.now() });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getCachedData(key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(CACHE_STORE, 'readonly');
    const store = tx.objectStore(CACHE_STORE);
    const req = store.get(key);
    req.onsuccess = () => resolve(req.result?.data || null);
    req.onerror = () => reject(req.error);
  });
}

// ============== SYNC ENGINE ==============

// Sync all pending operations with ordering and dedup
export async function syncPendingOperations(apiInstance) {
  const pending = await getPendingOperations();
  const now = Date.now();
  
  // Filter out operations in backoff period
  const ready = pending.filter(op => !op.nextRetryAt || op.nextRetryAt <= now);
  if (ready.length === 0) return { synced: 0, failed: 0, photos: 0 };

  let synced = 0;
  let failed = 0;

  // Sort by priority (creates first), then timestamp (oldest first)
  ready.sort((a, b) => (a.priority || 2) - (b.priority || 2) || a.timestamp - b.timestamp);

  // Dedup: if same url+method exists multiple times, keep latest
  const seen = new Map();
  const deduped = [];
  for (const op of ready) {
    const key = `${op.method}:${op.url}`;
    // Only dedup PATCH/PUT (status changes) — never dedup POST (creates)
    if ((op.method === 'PATCH' || op.method === 'PUT') && seen.has(key)) {
      // Remove the older duplicate
      await removeOperation(seen.get(key).id);
      synced++;
    }
    seen.set(key, op);
    deduped.push(op);
  }

  for (const op of deduped) {
    try {
      const { method, url, data } = op;
      if (method === 'POST') {
        await apiInstance.post(url, data);
      } else if (method === 'PUT') {
        await apiInstance.put(url, data);
      } else if (method === 'PATCH') {
        await apiInstance.patch(url, data);
      }
      await removeOperation(op.id);
      synced++;
    } catch (error) {
      const status = error.response?.status;
      // 409 Conflict or 400 Bad Request = data already exists or invalid, remove
      if (status === 409 || status === 400) {
        await removeOperation(op.id);
        synced++;
      } else {
        await markRetry(op.id);
        failed++;
      }
    }
  }

  // Sync photos after operations
  let photosSynced = 0;
  try {
    photosSynced = await syncPendingPhotos(apiInstance);
  } catch {}

  return { synced, failed, photos: photosSynced };
}

// Sync pending photos
async function syncPendingPhotos(apiInstance) {
  const photos = await getPendingPhotos();
  if (photos.length === 0) return 0;

  let synced = 0;
  for (const photo of photos) {
    try {
      const formData = new FormData();
      formData.append('file', new Blob([photo.blob], { type: 'image/jpeg' }), photo.filename);
      formData.append('entity_type', photo.entityType);
      formData.append('entity_id', photo.entityId);
      formData.append('categoria', photo.categoria);
      await apiInstance.post('/attachments', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await removePhoto(photo.id);
      synced++;
    } catch {
      // Photo sync failures are not critical — will retry next cycle
    }
  }
  return synced;
}

// Register service worker with auto-update
export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then((reg) => {
          console.log('SW registered:', reg.scope);
          setInterval(() => reg.update(), 60000);
          reg.addEventListener('updatefound', () => {
            const newWorker = reg.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'activated') {
                  console.log('SW updated, reloading...');
                  window.location.reload();
                }
              });
            }
          });
        })
        .catch((err) => {
          console.log('SW registration failed:', err);
        });
    });
  }
}
