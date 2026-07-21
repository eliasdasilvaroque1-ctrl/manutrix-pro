"""
Storage abstraction for MAINTRIX file management.
Supports Supabase Storage (primary) and Emergent Object Storage (fallback).
Fallback providers are lazy-loaded: only initialized on first actual use.
"""
import os
import logging
import requests
import uuid
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("storage")

# ─── Configuration ───
STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "supabase")
STORAGE_FALLBACK = os.environ.get("STORAGE_FALLBACK_PROVIDER", "emergent")
APP_NAME = "maintrix"
BUCKET_NAME = "maintrix-files"

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "pdf": "application/pdf",
    "jfif": "image/jpeg", "ico": "image/x-icon", "svg": "image/svg+xml",
}


# ─── Abstract Provider ───
class StorageProvider(ABC):
    @abstractmethod
    def upload(self, path: str, data: bytes, content_type: str) -> dict:
        """Upload file. Returns {"path": ..., "size": ..., "provider": ...}"""

    @abstractmethod
    def download(self, path: str) -> tuple:
        """Download file. Returns (bytes, content_type)"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists."""

    @abstractmethod
    def healthcheck(self) -> bool:
        """Check if provider is operational."""

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete file. Returns True if deleted."""


# ─── Supabase Provider ───
class SupabaseStorageProvider(StorageProvider):
    def __init__(self):
        self._url = os.environ.get("SUPABASE_URL", "")
        self._key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        self._bucket = BUCKET_NAME
        self._ready = bool(self._url and self._key)
        if self._ready:
            logger.info("SupabaseStorageProvider configured")
        else:
            logger.warning("SupabaseStorageProvider: SUPABASE_URL or SUPABASE_SERVICE_KEY missing")

    def _headers(self, content_type=None):
        h = {"apikey": self._key, "Authorization": f"Bearer {self._key}"}
        if content_type:
            h["Content-Type"] = content_type
        return h

    def upload(self, path: str, data: bytes, content_type: str) -> dict:
        if not self._ready:
            raise RuntimeError("Supabase storage not configured")
        resp = requests.post(
            f"{self._url}/storage/v1/object/{self._bucket}/{path}",
            headers={**self._headers(content_type), "x-upsert": "true"},
            data=data,
            timeout=120,
        )
        if resp.status_code in (200, 201):
            logger.info(f"SUPABASE_UPLOAD: path={path}, size={len(data)}, status={resp.status_code}")
            return {"path": path, "size": len(data), "provider": "supabase"}
        resp.raise_for_status()

    def download(self, path: str) -> tuple:
        if not self._ready:
            raise RuntimeError("Supabase storage not configured")
        resp = requests.get(
            f"{self._url}/storage/v1/object/{self._bucket}/{path}",
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
        if resp.status_code == 404:
            raise FileNotFoundError(f"Object not found: {path}")
        resp.raise_for_status()

    def exists(self, path: str) -> bool:
        if not self._ready:
            return False
        try:
            resp = requests.get(
                f"{self._url}/storage/v1/object/{self._bucket}/{path}",
                headers=self._headers(),
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def healthcheck(self) -> bool:
        if not self._ready:
            return False
        try:
            resp = requests.get(
                f"{self._url}/storage/v1/bucket",
                headers=self._headers(),
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def delete(self, path: str) -> bool:
        if not self._ready:
            return False
        try:
            resp = requests.delete(
                f"{self._url}/storage/v1/object/{self._bucket}/{path}",
                headers=self._headers(),
                timeout=30,
            )
            return resp.status_code in (200, 204)
        except Exception:
            return False


# ─── Emergent Provider (fully lazy) ───
class EmergentStorageProvider(StorageProvider):
    """Lazy-initialized: no HTTP calls or warnings until first actual use."""
    STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"

    def __init__(self):
        self._emergent_key = os.environ.get("EMERGENT_LLM_KEY", "")
        self._storage_key = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy init: only called when an operation actually needs Emergent."""
        if self._initialized:
            return self._storage_key is not None
        self._initialized = True
        if not self._emergent_key:
            logger.debug("Emergent fallback requested but EMERGENT_LLM_KEY is not configured")
            return False
        try:
            resp = requests.post(
                f"{self.STORAGE_URL}/init",
                json={"emergent_key": self._emergent_key},
                timeout=30,
            )
            resp.raise_for_status()
            self._storage_key = resp.json()["storage_key"]
            logger.info("EmergentStorageProvider initialized on demand")
            return True
        except Exception as e:
            logger.error(f"EmergentStorageProvider init failed: {e}")
            return False

    def _get_key(self):
        if self._storage_key:
            return self._storage_key
        if self._ensure_initialized():
            return self._storage_key
        return None

    def upload(self, path: str, data: bytes, content_type: str) -> dict:
        key = self._get_key()
        if not key:
            raise RuntimeError("Emergent storage not available")
        resp = requests.put(
            f"{self.STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
        if resp.status_code == 403:
            self._storage_key = None
            self._initialized = False
            key = self._get_key()
            if not key:
                raise RuntimeError("Emergent storage re-init failed")
            resp = requests.put(
                f"{self.STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key, "Content-Type": content_type},
                data=data,
                timeout=120,
            )
        resp.raise_for_status()
        return {"path": path, "size": len(data), "provider": "emergent"}

    def download(self, path: str) -> tuple:
        key = self._get_key()
        if not key:
            raise RuntimeError("Emergent storage not available")
        resp = requests.get(
            f"{self.STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
        if resp.status_code == 403:
            self._storage_key = None
            self._initialized = False
            key = self._get_key()
            if not key:
                raise RuntimeError("Emergent storage re-init failed")
            resp = requests.get(
                f"{self.STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key},
                timeout=60,
            )
        if resp.status_code == 200:
            return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
        if resp.status_code == 404:
            raise FileNotFoundError(f"Object not found in Emergent: {path}")
        resp.raise_for_status()

    def exists(self, path: str) -> bool:
        try:
            self.download(path)
            return True
        except Exception:
            return False

    def healthcheck(self) -> bool:
        """Only reports True if already initialized. Does NOT trigger init."""
        return self._storage_key is not None

    def delete(self, path: str) -> bool:
        return False  # Never delete from Emergent during migration


# ─── Storage Manager with lazy fallback ───
class StorageManager:
    """Primary provider initialized eagerly. Fallback lazy-loaded on first use."""

    PROVIDER_CLASSES = {
        "supabase": SupabaseStorageProvider,
        "emergent": EmergentStorageProvider,
    }

    def __init__(self):
        self.primary = None
        self._fallback = None
        self._fallback_name = STORAGE_FALLBACK if STORAGE_FALLBACK != STORAGE_PROVIDER else ""
        # Initialize ONLY the primary provider
        if STORAGE_PROVIDER in self.PROVIDER_CLASSES:
            self.primary = self.PROVIDER_CLASSES[STORAGE_PROVIDER]()

    @property
    def fallback(self):
        """Lazy property: fallback created on first access."""
        if self._fallback is None and self._fallback_name and self._fallback_name in self.PROVIDER_CLASSES:
            self._fallback = self.PROVIDER_CLASSES[self._fallback_name]()
        return self._fallback

    def upload_file(self, entity_type: str, entity_id: str, filename: str, data: bytes, content_type: str) -> str:
        """Upload to primary provider. Returns storage_path (legacy-compatible)."""
        ext = Path(filename).suffix.lower().lstrip('.') or "bin"
        mime = content_type or MIME_TYPES.get(ext, "application/octet-stream")
        storage_path = f"{APP_NAME}/{entity_type}/{entity_id}/{uuid.uuid4().hex[:8]}.{ext}"
        self.primary.upload(storage_path, data, mime)
        return storage_path

    def get_file(self, storage_path: str) -> tuple:
        """Download from primary. Falls back ONLY for FileNotFoundError."""
        if self.primary:
            try:
                return self.primary.download(storage_path)
            except FileNotFoundError:
                pass  # May be a legacy file — try fallback
            except Exception as e:
                logger.warning(f"Primary download error for {storage_path}: {type(e).__name__}")
                raise
        # Fallback: only for files not yet migrated
        fb = self.fallback
        if fb:
            try:
                data, ct = fb.download(storage_path)
                logger.info(f"FALLBACK_READ: path={storage_path}, provider={self._fallback_name}, size={len(data)}")
                return data, ct
            except Exception as e:
                logger.warning(f"Fallback download failed for {storage_path}: {type(e).__name__}")
        raise FileNotFoundError(f"File not found in any provider: {storage_path}")

    def is_available(self) -> bool:
        """Primary provider health only."""
        return bool(self.primary and self.primary.healthcheck())

    def healthcheck_detail(self) -> dict:
        """Detailed health. Does NOT trigger fallback initialization."""
        result = {
            "provider": STORAGE_PROVIDER,
            "fallback": self._fallback_name or "none",
        }
        if self.primary:
            result["primary_status"] = "online" if self.primary.healthcheck() else "offline"
        else:
            result["primary_status"] = "not_configured"
        # Report fallback status only if already instantiated
        if self._fallback is not None:
            result["fallback_status"] = "online" if self._fallback.healthcheck() else "offline"
        else:
            result["fallback_status"] = "not_initialized"
        return result


# ─── Module-level singleton (backward compatible) ───
_manager = None


def _get_manager() -> StorageManager:
    global _manager
    if _manager is None:
        _manager = StorageManager()
    return _manager


def init_storage():
    """Initialize storage. Called at startup. Only initializes primary."""
    mgr = _get_manager()
    if mgr.is_available():
        logger.info(f"Storage ready: primary={STORAGE_PROVIDER}")
    else:
        logger.warning(f"Storage primary ({STORAGE_PROVIDER}) not available")
    return mgr.is_available()


def upload_file(entity_type, entity_id, filename, data, content_type):
    return _get_manager().upload_file(entity_type, entity_id, filename, data, content_type)


def get_file(storage_path):
    return _get_manager().get_file(storage_path)


def is_available():
    return _get_manager().is_available()


def healthcheck_detail():
    return _get_manager().healthcheck_detail()
