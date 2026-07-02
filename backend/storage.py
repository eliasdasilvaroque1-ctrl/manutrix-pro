"""Object Storage integration for MAINTRIX file uploads"""
import os
import logging
import requests
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "maintrix"

storage_key = None

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "pdf": "application/pdf",
}

# Local fallback directory (for serving legacy files during migration)
LOCAL_UPLOAD_DIR = Path(__file__).parent / 'uploads'
LOCAL_MANUALS_DIR = LOCAL_UPLOAD_DIR / 'manuals'


def init_storage():
    """Initialize storage connection. Call once at startup."""
    global storage_key
    if storage_key:
        return storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set — object storage unavailable")
        return None
    try:
        resp = requests.post(
            f"{STORAGE_URL}/init",
            json={"emergent_key": EMERGENT_KEY},
            timeout=30
        )
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Object storage initialized successfully")
        return storage_key
    except Exception as e:
        logger.error(f"Object storage init failed: {e}")
        return None


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload file to object storage. Returns {"path": "...", "size": N}"""
    key = init_storage()
    if not key:
        raise RuntimeError("Object storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120
    )
    if resp.status_code == 403:
        # Key expired, reinit once
        global storage_key
        storage_key = None
        key = init_storage()
        if not key:
            raise RuntimeError("Object storage re-init failed")
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120
        )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    """Download file from object storage. Returns (bytes, content_type)"""
    key = init_storage()
    if not key:
        raise RuntimeError("Object storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60
    )
    if resp.status_code == 403:
        global storage_key
        storage_key = None
        key = init_storage()
        if not key:
            raise RuntimeError("Object storage re-init failed")
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def upload_file(entity_type: str, entity_id: str, filename: str, data: bytes, content_type: str) -> str:
    """Upload a file and return the storage path."""
    ext = Path(filename).suffix.lower().lstrip('.')
    if not ext:
        ext = "bin"
    mime = content_type or MIME_TYPES.get(ext, "application/octet-stream")
    storage_path = f"{APP_NAME}/{entity_type}/{entity_id}/{uuid.uuid4().hex[:8]}.{ext}"
    put_object(storage_path, data, mime)
    return storage_path


def get_file(storage_path: str):
    """Get file content and content_type from storage path."""
    return get_object(storage_path)


def is_available() -> bool:
    """Check if object storage is configured and available."""
    return init_storage() is not None
