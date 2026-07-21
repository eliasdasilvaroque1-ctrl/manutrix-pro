"""
Migrate files from Emergent Object Storage to Supabase Storage.
Idempotent: re-running skips already-migrated objects.
"""
import os
import sys
import hashlib
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

import pymongo
from storage import EmergentStorageProvider, SupabaseStorageProvider, MIME_TYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migration")

MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "maintrix")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def supabase_path_for(url: str, org_id: str, is_branding: bool) -> str:
    """Map legacy /api/storage/... URL to Supabase object path."""
    filename = url.split("/")[-1]
    subdir = "branding" if is_branding else "private"
    return f"organizations/{org_id}/{subdir}/{filename}"


def run_migration():
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]

    emergent = EmergentStorageProvider()
    supabase = SupabaseStorageProvider()

    if not emergent.healthcheck():
        logger.error("Emergent storage not available. Cannot migrate.")
        return {"migrated": 0, "failed": 0, "skipped": 0, "error": "emergent_unavailable"}
    if not supabase.healthcheck():
        logger.error("Supabase storage not available. Cannot migrate.")
        return {"migrated": 0, "failed": 0, "skipped": 0, "error": "supabase_unavailable"}

    entries = list(db.file_registry.find({"url": {"$regex": "^/api/storage/"}}))
    logger.info(f"Found {len(entries)} file_registry entries to process")

    stats = {"migrated": 0, "failed": 0, "skipped": 0, "already_done": 0}
    results = []

    for entry in entries:
        url = entry.get("url", "")
        org_id = entry.get("organization_id", "unknown")
        is_branding = entry.get("category") == "branding"
        filename = url.split("/")[-1]

        # Skip already migrated
        if entry.get("migration_status") == "completed" and entry.get("storage_provider") == "supabase":
            stats["already_done"] += 1
            continue

        # Extract Emergent storage path
        emergent_path = url[len("/api/storage/"):]
        target_path = supabase_path_for(url, org_id, is_branding)

        try:
            # 1. Download from Emergent
            data, content_type = emergent.download(emergent_path)
            source_hash = sha256(data)
            source_size = len(data)
            logger.info(f"Downloaded {filename}: {source_size} bytes, sha256={source_hash[:16]}...")

            # 2. Check if already exists in Supabase (idempotent)
            if supabase.exists(target_path):
                existing_data, _ = supabase.download(target_path)
                if sha256(existing_data) == source_hash and len(existing_data) == source_size:
                    # Already migrated correctly
                    db.file_registry.update_one(
                        {"url": url},
                        {"$set": {
                            "storage_provider": "supabase",
                            "storage_bucket": "maintrix-files",
                            "storage_path": target_path,
                            "sha256": source_hash,
                            "migrated_at": datetime.now(timezone.utc).isoformat(),
                            "migration_status": "completed",
                        }}
                    )
                    stats["already_done"] += 1
                    logger.info(f"Already in Supabase (verified): {filename}")
                    continue

            # 3. Upload to Supabase
            supabase.upload(target_path, data, content_type)

            # 4. Verify upload
            verify_data, verify_ct = supabase.download(target_path)
            verify_hash = sha256(verify_data)
            verify_size = len(verify_data)

            if verify_hash != source_hash or verify_size != source_size:
                raise ValueError(
                    f"Verification failed: expected {source_size}B/{source_hash[:16]}, "
                    f"got {verify_size}B/{verify_hash[:16]}"
                )

            # 5. Update file_registry
            db.file_registry.update_one(
                {"url": url},
                {"$set": {
                    "storage_provider": "supabase",
                    "storage_bucket": "maintrix-files",
                    "storage_path": target_path,
                    "sha256": source_hash,
                    "content_type": content_type,
                    "size_bytes": source_size,
                    "migrated_at": datetime.now(timezone.utc).isoformat(),
                    "migration_status": "completed",
                }}
            )
            stats["migrated"] += 1
            logger.info(f"✅ Migrated: {filename} -> {target_path} ({source_size}B, sha256 verified)")
            results.append({"file": filename, "status": "completed", "size": source_size, "sha256": source_hash})

        except Exception as e:
            stats["failed"] += 1
            error_msg = f"{type(e).__name__}: {str(e)[:200]}"
            logger.error(f"❌ Failed: {filename} — {error_msg}")
            db.file_registry.update_one(
                {"url": url},
                {"$set": {
                    "migration_status": "failed",
                    "migration_error": error_msg,
                    "migration_attempted_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
            results.append({"file": filename, "status": "failed", "error": error_msg})

    logger.info(f"Migration complete: {stats}")
    return stats


def fix_branding_registry():
    """Etapa 3: Fix branding entries using $set (not $setOnInsert)."""
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]

    logger.info("=== Fixing branding registry entries ===")
    fixed = 0

    for doc in db.org_config.find({}, {"_id": 0, "organization_id": 1, "identidade": 1}):
        org_id = doc.get("organization_id", "")
        ident = doc.get("identidade", {}) or {}
        for key in ["logo_url", "logo_branca_url", "wallpaper_url", "favicon_url"]:
            url = ident.get(key)
            if url:
                result = db.file_registry.update_one(
                    {"url": url},
                    {
                        "$set": {
                            "is_public": True,
                            "category": "branding",
                            "organization_id": org_id,
                        },
                        "$setOnInsert": {
                            "url": url,
                            "uploaded_by": "backfill",
                            "registered_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                    upsert=True
                )
                if result.modified_count > 0:
                    fixed += 1
                    logger.info(f"Fixed: {url.split('/')[-1]} -> category=branding, is_public=true")

    logger.info(f"Branding fix complete: {fixed} entries updated")
    return fixed


if __name__ == "__main__":
    import json
    print("=" * 60)
    print("MAINTRIX Storage Migration — Emergent → Supabase")
    print("=" * 60)

    # Step 1: Fix branding registry
    print("\n--- Step 1: Fix branding registry ---")
    fixed = fix_branding_registry()
    print(f"Branding entries fixed: {fixed}")

    # Step 2: Migrate files
    print("\n--- Step 2: Migrate files ---")
    stats = run_migration()
    print(f"\nResults: {json.dumps(stats, indent=2)}")
