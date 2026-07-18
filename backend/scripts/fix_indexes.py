"""
RC5.2 P0.1 — MongoDB Index Migration Script
Fixes 3 conflicting indexes identified in the audit.
Idempotent. Safe to run multiple times.

Usage:
    python3 fix_indexes.py --dry-run    # Shows what would change
    python3 fix_indexes.py --apply      # Applies changes
    python3 fix_indexes.py --rollback   # Restores original indexes
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient


FIXES = [
    {
        "collection": "password_reset_tokens",
        "index_name": "expires_at_1",
        "description": "Convert normal index to TTL index (expireAfterSeconds: 0)",
        "old": {"key": [("expires_at", 1)]},
        "new": {"key": [("expires_at", 1)], "expireAfterSeconds": 0},
        "rollback": {"key": [("expires_at", 1)]},
    },
    {
        "collection": "os_executantes",
        "index_name": "os_user",
        "description": "Add partialFilterExpression {deleted_at: null} to unique index",
        "old": {"key": [("os_id", 1), ("user_id", 1)], "unique": True},
        "new": {"key": [("os_id", 1), ("user_id", 1)], "unique": True, "partialFilterExpression": {"deleted_at": None}},
        "rollback": {"key": [("os_id", 1), ("user_id", 1)], "unique": True},
    },
    {
        "collection": "campos_personalizados",
        "index_name": "org_ident",
        "description": "Add unique: true constraint",
        "old": {"key": [("organization_id", 1), ("identificador_tecnico", 1)]},
        "new": {"key": [("organization_id", 1), ("identificador_tecnico", 1)], "unique": True},
        "rollback": {"key": [("organization_id", 1), ("identificador_tecnico", 1)]},
    },
]


async def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "maintrix")
    if not mongo_url:
        print("ERROR: MONGO_URL not set")
        sys.exit(1)
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def verify_index(db, coll_name, index_name, expected_props):
    """Verify an index matches expected properties. Returns (exists, matches, details)."""
    indexes = await db[coll_name].index_information()
    if index_name not in indexes:
        return False, False, None
    info = indexes[index_name]
    matches = True
    if "expireAfterSeconds" in expected_props:
        if info.get("expireAfterSeconds") != expected_props["expireAfterSeconds"]:
            matches = False
    if expected_props.get("unique"):
        if not info.get("unique"):
            matches = False
    if "partialFilterExpression" in expected_props:
        if info.get("partialFilterExpression") != expected_props["partialFilterExpression"]:
            matches = False
    return True, matches, info


async def run_dry_run(db):
    print("=" * 60)
    print("  DRY-RUN — No changes will be made")
    print("=" * 60)
    all_ok = True
    for fix in FIXES:
        coll = fix["collection"]
        name = fix["index_name"]
        exists, matches, info = await verify_index(db, coll, name, fix["new"])
        print(f"\n[{coll}.{name}]")
        print(f"  Description: {fix['description']}")
        if not exists:
            print(f"  Status: INDEX MISSING — will be created")
            all_ok = False
        elif matches:
            print(f"  Status: ALREADY CORRECT — no action needed")
        else:
            print(f"  Status: NEEDS FIX — will drop and recreate")
            print(f"  Current: unique={info.get('unique')}, TTL={info.get('expireAfterSeconds')}, partial={info.get('partialFilterExpression')}")
            all_ok = False
    if all_ok:
        print("\n✅ All indexes are already correct. Nothing to do.")
    else:
        print("\n⚠️  Run with --apply to fix the indexes above.")
    return 0


async def run_apply(db):
    print("=" * 60)
    print("  APPLY — Fixing indexes one at a time")
    print("=" * 60)
    for fix in FIXES:
        coll = fix["collection"]
        name = fix["index_name"]
        exists, matches, info = await verify_index(db, coll, name, fix["new"])

        print(f"\n[{coll}.{name}]")
        if matches:
            print(f"  ✅ Already correct — skipping")
            continue

        # Drop old index
        if exists:
            print(f"  Dropping old index '{name}'...")
            await db[coll].drop_index(name)
            print(f"  Dropped.")

        # Create new index
        kwargs = {"name": name, "background": True}
        if fix["new"].get("unique"):
            kwargs["unique"] = True
        if "expireAfterSeconds" in fix["new"]:
            kwargs["expireAfterSeconds"] = fix["new"]["expireAfterSeconds"]
        if "partialFilterExpression" in fix["new"]:
            kwargs["partialFilterExpression"] = fix["new"]["partialFilterExpression"]

        print(f"  Creating new index with: {kwargs}")
        await db[coll].create_index(fix["new"]["key"], **kwargs)

        # Verify
        _, ok, new_info = await verify_index(db, coll, name, fix["new"])
        if ok:
            print(f"  ✅ Verified — index is correct")
        else:
            print(f"  ❌ VERIFICATION FAILED — index state: {new_info}")
            print(f"  STOPPING. Manual intervention required.")
            return 1

    print("\n✅ All indexes fixed successfully.")
    return 0


async def run_rollback(db):
    print("=" * 60)
    print("  ROLLBACK — Restoring original indexes")
    print("=" * 60)
    for fix in FIXES:
        coll = fix["collection"]
        name = fix["index_name"]
        print(f"\n[{coll}.{name}]")

        indexes = await db[coll].index_information()
        if name in indexes:
            print(f"  Dropping current index '{name}'...")
            await db[coll].drop_index(name)

        kwargs = {"name": name, "background": True}
        if fix["rollback"].get("unique"):
            kwargs["unique"] = True

        print(f"  Recreating original index: {fix['rollback']['key']} {kwargs}")
        await db[coll].create_index(fix["rollback"]["key"], **kwargs)
        print(f"  ✅ Restored")

    print("\n✅ Rollback complete — original indexes restored.")
    return 0


async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("--dry-run", "--apply", "--rollback"):
        print("Usage: python3 fix_indexes.py [--dry-run|--apply|--rollback]")
        sys.exit(1)

    mode = sys.argv[1]
    db = await get_db()

    if mode == "--dry-run":
        code = await run_dry_run(db)
    elif mode == "--apply":
        code = await run_apply(db)
    elif mode == "--rollback":
        code = await run_rollback(db)

    sys.exit(code)


if __name__ == "__main__":
    asyncio.run(main())
