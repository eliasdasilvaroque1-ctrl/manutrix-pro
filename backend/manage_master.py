#!/usr/bin/env python3
"""Emergency Master Password Reset CLI — MAINTRIX Enterprise

Usage:
    MASTER_RESET_PASSWORD=<new_password> python manage_master.py

Security:
    - Password via env var only (not visible in terminal history)
    - Generates bcrypt hash
    - Forces password change on next login
    - Invalidates existing sessions
    - Creates audit log entry
    - Never logs the password itself
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def reset_master_password():
    new_pwd = os.environ.get("MASTER_RESET_PASSWORD", "")
    if not new_pwd:
        print("ERROR: Set MASTER_RESET_PASSWORD env var before running.")
        print("Usage: MASTER_RESET_PASSWORD=<new_password> python manage_master.py")
        sys.exit(1)

    if len(new_pwd) < 8:
        print("ERROR: Password must be at least 8 characters.")
        sys.exit(1)

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "maintrix")]

    from deps import hash_password
    email = "master@maintrix.com"
    user = await db.users.find_one({"email": email, "deleted_at": None}, {"_id": 0, "id": 1, "email": 1, "role": 1})

    if not user:
        print(f"ERROR: Master user '{email}' not found.")
        sys.exit(1)

    new_hash = hash_password(new_pwd)
    now = datetime.now(timezone.utc).isoformat()

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": new_hash,
            "force_password_change": True,
            "updated_at": now
        }}
    )

    # Invalidate existing sessions by incrementing token version
    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"token_version": 1}}
    )

    # Audit log
    await db.audit_logs.insert_one({
        "action": "master_password_reset",
        "entity_type": "user",
        "entity_id": user["id"],
        "details": "Emergency master password reset via CLI",
        "performed_by": "system_cli",
        "organization_id": "system",
        "created_at": now
    })

    print(f"OK: Master password reset for {email}")
    print("    force_password_change = True")
    print("    Previous sessions invalidated")
    print("    Audit log created")
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_master_password())
