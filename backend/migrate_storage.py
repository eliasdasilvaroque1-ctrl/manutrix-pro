"""Migration script: Move existing local files to cloud Object Storage.
Run once: python migrate_storage.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).parent / '.env')

from motor.motor_asyncio import AsyncIOMotorClient
import storage as objstore

UPLOAD_DIR = Path(__file__).parent / 'uploads'
MANUALS_DIR = UPLOAD_DIR / 'manuals'

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]


async def migrate_attachments():
    """Migrate attachments (fotos OS, inspeções, anomalias) to object storage."""
    print("\n=== MIGRATING ATTACHMENTS ===")
    attachments = await db.attachments.find({}, {"_id": 0}).to_list(1000)
    migrated = 0
    skipped = 0
    errors = 0
    total_bytes = 0

    for att in attachments:
        file_url = att.get('file_url', '')
        
        # Skip if already migrated to cloud storage
        if '/api/storage/' in file_url:
            skipped += 1
            continue
        
        # Extract local filename from URL like /api/uploads/work_order_xxx.jpeg
        local_filename = file_url.split('/')[-1] if '/' in file_url else file_url
        local_path = UPLOAD_DIR / local_filename
        
        if not local_path.exists():
            print(f"  SKIP (file missing): {local_filename}")
            skipped += 1
            continue
        
        try:
            data = local_path.read_bytes()
            content_type = att.get('mime_type', 'application/octet-stream')
            entity_type = att.get('entity_type', 'unknown')
            entity_id = att.get('entity_id', 'unknown')
            
            storage_path = objstore.upload_file(
                entity_type, entity_id,
                att.get('filename', local_filename),
                data, content_type
            )
            new_url = f"/api/storage/{storage_path}"
            
            # Update MongoDB record
            await db.attachments.update_one(
                {"id": att['id']},
                {"$set": {"file_url": new_url}}
            )
            
            migrated += 1
            total_bytes += len(data)
            print(f"  OK: {local_filename} -> {storage_path} ({len(data)} bytes)")
        except Exception as e:
            errors += 1
            print(f"  ERROR: {local_filename} — {e}")
    
    print(f"\nAttachments: {migrated} migrated, {skipped} skipped, {errors} errors, {total_bytes / 1024 / 1024:.2f} MB total")
    return migrated, total_bytes


async def migrate_manuals():
    """Migrate manual PDFs to object storage."""
    print("\n=== MIGRATING MANUALS ===")
    manuais = await db.manuais.find({}, {"_id": 0}).to_list(1000)
    migrated = 0
    skipped = 0
    errors = 0
    total_bytes = 0

    for manual in manuais:
        file_url = manual.get('url', '')
        
        # Skip if already migrated
        if '/api/storage/' in file_url:
            skipped += 1
            continue
        
        # Extract local filename from URL like /api/uploads/manuals/xxx.pdf
        local_filename = file_url.split('/')[-1] if '/' in file_url else ''
        local_path = MANUALS_DIR / local_filename
        
        if not local_path.exists():
            # Try filepath field
            fp = manual.get('filepath', '')
            if fp and Path(fp).exists():
                local_path = Path(fp)
            else:
                print(f"  SKIP (file missing): {local_filename}")
                skipped += 1
                continue
        
        try:
            data = local_path.read_bytes()
            ativo_id = manual.get('ativo_id', 'unknown')
            
            storage_path = objstore.upload_file(
                "manuals", ativo_id,
                manual.get('filename', local_filename),
                data, "application/pdf"
            )
            new_url = f"/api/storage/{storage_path}"
            
            # Update MongoDB record
            await db.manuais.update_one(
                {"id": manual['id']},
                {"$set": {"url": new_url, "filepath": new_url}}
            )
            
            migrated += 1
            total_bytes += len(data)
            print(f"  OK: {local_filename} -> {storage_path} ({len(data)} bytes)")
        except Exception as e:
            errors += 1
            print(f"  ERROR: {local_filename} — {e}")
    
    print(f"\nManuals: {migrated} migrated, {skipped} skipped, {errors} errors, {total_bytes / 1024 / 1024:.2f} MB total")
    return migrated, total_bytes


async def main():
    print("MAINTRIX Storage Migration — Local -> Object Storage")
    print("=" * 60)
    
    # Initialize storage
    key = objstore.init_storage()
    if not key:
        print("ERROR: Object storage not available. Check EMERGENT_LLM_KEY.")
        sys.exit(1)
    print(f"Storage initialized OK")
    
    att_count, att_bytes = await migrate_attachments()
    man_count, man_bytes = await migrate_manuals()
    
    total_files = att_count + man_count
    total_mb = (att_bytes + man_bytes) / 1024 / 1024
    
    print("\n" + "=" * 60)
    print(f"MIGRATION COMPLETE")
    print(f"  Files migrated: {total_files}")
    print(f"  Total size: {total_mb:.2f} MB")
    print(f"  Attachments: {att_count}")
    print(f"  Manuals: {man_count}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
