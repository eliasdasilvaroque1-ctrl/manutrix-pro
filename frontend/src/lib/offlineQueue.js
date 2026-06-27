/**
 * Offline Queue Engine for MAINTRIX
 * Stores pending operations in IndexedDB and syncs when online
 */

const DB_NAME = 'maintrix_offline';
const DB_VERSION = 1;
const STORE_NAME = 'pending_operations';
const CACHE_STORE = 'cached_data';

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// Queue an operation for later sync
export async function queueOperation(operation) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const record = {
      ...operation,
      timestamp: Date.now(),
      retries: 0,
      status: 'pending'
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

// Get count of pending ops
export async function getPendingCount() {
  const ops = await getPendingOperations();
  return ops.length;
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

// Mark operation as failed (increment retries)
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
        if (record.retries >= 5) record.status = 'failed';
        store.put(record);
      }
      resolve();
    };
    getReq.onerror = () => reject(getReq.error);
  });
}

// Cache data locally for offline reads
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

// Read cached data
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

// Sync engine: process all pending operations
export async function syncPendingOperations(apiInstance) {
  const pending = await getPendingOperations();
  if (pending.length === 0) return { synced: 0, failed: 0 };

  let synced = 0;
  let failed = 0;

  // Sort by timestamp (oldest first)
  pending.sort((a, b) => a.timestamp - b.timestamp);

  for (const op of pending) {
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
      // Conflict: 409 means data was already created — remove from queue
      if (error.response?.status === 409 || error.response?.status === 400) {
        await removeOperation(op.id);
        synced++;
      } else {
        await markRetry(op.id);
        failed++;
      }
    }
  }

  return { synced, failed };
}

// Register service worker with auto-update
export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then((reg) => {
          console.log('SW registered:', reg.scope);
          // Check for updates every 60 seconds
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
