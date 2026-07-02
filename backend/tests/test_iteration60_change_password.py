"""
Iteration 60 — POST /api/auth/change-password bug fix verification.

Bug: Pydantic ChangePasswordRequest required current_password as str, but frontend
sends only {new_password} when force_password_change=true. This caused HTTP 422.

Fix: current_password is now Optional[str] = None (models.py:381) and server.py:271
skips current-password verification when user.force_password_change is true.

These tests cover the scenarios in the review_request and restore the master password
to 'master123' with force_password_change=false at the end so the environment is clean.
"""
import os
import time
import requests
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MASTER_EMAIL = "master@maintrix.com"
ORIGINAL_PASSWORD = "master123"
TEMP_PASSWORD_1 = "master999"  # new password used in force-change scenario
TEMP_PASSWORD_2 = "master888"  # new password used in normal-change scenario

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# --- helpers -----------------------------------------------------------------

def _login(email: str, password: str):
    return requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)


async def _set_force_password_change(value: bool):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.users.update_one({"email": MASTER_EMAIL}, {"$set": {"force_password_change": value}})
    client.close()


async def _reset_master(hash_password_str: str, force_flag: bool):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.users.update_one(
        {"email": MASTER_EMAIL},
        {"$set": {"password_hash": hash_password_str, "force_password_change": force_flag}},
    )
    client.close()


def _hash(pw: str) -> str:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(pw)


# --- fixtures ----------------------------------------------------------------

@pytest.fixture(scope="module")
def restore_master_at_end():
    """Ensure master@maintrix.com is 'master123' with force_password_change=false after tests."""
    yield
    asyncio.get_event_loop().run_until_complete(
        _reset_master(_hash(ORIGINAL_PASSWORD), False)
    )
    # sanity check
    r = _login(MASTER_EMAIL, ORIGINAL_PASSWORD)
    assert r.status_code == 200, f"Restore failed: master login returned {r.status_code} {r.text}"


# --- baseline ----------------------------------------------------------------

def test_00_baseline_login_ok():
    """Verify environment: master can log in with master123 before any changes."""
    r = _login(MASTER_EMAIL, ORIGINAL_PASSWORD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    assert body["user"]["email"] == MASTER_EMAIL


# --- force_password_change scenario -----------------------------------------

def test_01_force_change_only_new_password_succeeds(restore_master_at_end):
    """
    Set force_password_change=true, then POST /api/auth/change-password with only
    {new_password} — must return 200 (the original bug returned 422).
    """
    # 1. flip force_password_change to true in DB
    asyncio.get_event_loop().run_until_complete(_set_force_password_change(True))

    # 2. login and confirm flag is true
    r = _login(MASTER_EMAIL, ORIGINAL_PASSWORD)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["force_password_change"] is True, "Setup failed: flag not true"
    token = data["access_token"]

    # 3. call change-password with ONLY {new_password}
    resp = requests.post(
        f"{API}/auth/change-password",
        json={"new_password": TEMP_PASSWORD_1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("success") is True
    assert "senha" in body.get("message", "").lower()

    # 4. verify /api/auth/me now has force_password_change=false
    #    (login with new password to get a fresh token)
    r2 = _login(MASTER_EMAIL, TEMP_PASSWORD_1)
    assert r2.status_code == 200, r2.text
    tok2 = r2.json()["access_token"]
    me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok2}"}, timeout=15)
    assert me.status_code == 200
    me_body = me.json()
    assert me_body.get("force_password_change") is False, me_body

    # 5. verify old password no longer works — this exposes a SEPARATE Supabase sync
    #    bug (see test_07). We record but do not fail here so the primary bug-fix
    #    assertion (422 → 200) is not shadowed.
    old = _login(MASTER_EMAIL, ORIGINAL_PASSWORD)
    if old.status_code == 200:
        print(
            "[WARN] Old password master123 still returns 200 after change to master999. "
            "Root cause: login endpoint (server.py:141) tries Supabase Auth first, but "
            "change-password (server.py:264) only updates MongoDB. Supabase never learns "
            "of the new password. This is a SECURITY bug tracked in test_07."
        )


# --- normal change scenario --------------------------------------------------

def test_02_normal_change_with_current_and_new_succeeds():
    """
    force_password_change is now false (from prior test). Change password normally,
    supplying both current_password and new_password.
    """
    # login with the current password (TEMP_PASSWORD_1 from previous test)
    r = _login(MASTER_EMAIL, TEMP_PASSWORD_1)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    resp = requests.post(
        f"{API}/auth/change-password",
        json={"current_password": TEMP_PASSWORD_1, "new_password": TEMP_PASSWORD_2},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    # confirm login with new password
    r2 = _login(MASTER_EMAIL, TEMP_PASSWORD_2)
    assert r2.status_code == 200, r2.text

    # confirm login with the previous one fails
    r3 = _login(MASTER_EMAIL, TEMP_PASSWORD_1)
    assert r3.status_code == 401, f"Old password should be rejected: {r3.status_code} {r3.text}"


# --- wrong current password --------------------------------------------------

def test_03_wrong_current_password_returns_400():
    """
    Providing wrong current_password when force_password_change=false must return
    400 with 'Senha atual incorreta'.
    """
    r = _login(MASTER_EMAIL, TEMP_PASSWORD_2)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    resp = requests.post(
        f"{API}/auth/change-password",
        json={"current_password": "wrong-password-xyz", "new_password": "novasenha123"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    body = resp.json()
    detail = body.get("detail", "")
    assert "incorreta" in detail.lower() or "atual" in detail.lower(), body


# --- short new password ------------------------------------------------------

def test_04_short_new_password_returns_400():
    """new_password shorter than 6 chars must return 400."""
    r = _login(MASTER_EMAIL, TEMP_PASSWORD_2)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    resp = requests.post(
        f"{API}/auth/change-password",
        json={"current_password": TEMP_PASSWORD_2, "new_password": "123"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    body = resp.json()
    detail = body.get("detail", "")
    assert "6" in detail or "caracteres" in detail.lower(), body


# --- pydantic-level bug regression ------------------------------------------

def test_05_only_new_password_when_force_false_returns_400_not_422():
    """
    When force_password_change=false and payload has ONLY {new_password}, the
    endpoint must return 400 'Senha atual é obrigatória' (business rule) NOT 422
    (pydantic validation error). This proves the schema fix (Optional) is in
    place and the check moved to route logic.
    """
    r = _login(MASTER_EMAIL, TEMP_PASSWORD_2)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    resp = requests.post(
        f"{API}/auth/change-password",
        json={"new_password": "algumaSenha1"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert resp.status_code == 400, (
        f"Expected 400 (business rule) after schema fix. Got {resp.status_code}: {resp.text}. "
        "If this returns 422, the Optional[str] fix in models.py:381 has regressed."
    )
    body = resp.json()
    detail = body.get("detail", "")
    assert "obrigat" in detail.lower() or "atual" in detail.lower(), body


# --- no auth token -----------------------------------------------------------

def test_06_change_password_without_token_returns_401_or_403():
    resp = requests.post(
        f"{API}/auth/change-password",
        json={"new_password": "algumaSenha1"},
        timeout=15,
    )
    assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}: {resp.text}"


# --- SEPARATE bug: password change does not invalidate Supabase session -----

def test_07_old_password_still_works_after_change_supabase_bug():
    """
    Regression check for a SECURITY bug uncovered while testing the 422 fix.

    Steps:
      * Current DB password is TEMP_PASSWORD_2 (master888).
      * Old original password is ORIGINAL_PASSWORD (master123) — this is what
        Supabase Auth still has because change-password only writes MongoDB.
      * Login with ORIGINAL_PASSWORD should return 401 (old password invalid).
        If it returns 200, Supabase Auth path (server.py:141-172) is accepting
        the old password because /api/auth/change-password (server.py:264)
        does not sync the new hash to Supabase.

    This test is expected to FAIL until change-password / admin-reset propagate
    the new password to Supabase via supabase_client.auth.admin.update_user_by_id.
    """
    r = _login(MASTER_EMAIL, ORIGINAL_PASSWORD)
    assert r.status_code == 401, (
        f"SECURITY BUG: old password '{ORIGINAL_PASSWORD}' still returns "
        f"{r.status_code} after change-password. "
        f"Response: {r.text[:400]}. "
        f"Root cause: server.py:141 tries supabase_client.auth.sign_in_with_password "
        f"first; server.py:278 only updates MongoDB password_hash; therefore "
        f"Supabase Auth continues to accept the original password. "
        f"Fix: after change-password, call supabase_client.auth.admin.update_user_by_id"
        f"(user['supabase_id'], {{'password': new_password}})."
    )
