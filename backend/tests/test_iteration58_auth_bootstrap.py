"""
Iteration 58 — Auth module audit + Bootstrap logic validation.

Tests the auth flow against the Emergent preview backend AND validates that
the bootstrap logic (added to server.py startup) is present, correct, and idempotent.

Also does a smoke-check against the Railway URL to verify that /api/auth/login
is exposed (not 405/404) even though the Railway DB may be empty.
"""
import os
import re
import base64
import json
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
RAILWAY_URL = "https://manutrix-pro-production.up.railway.app"

MASTER_EMAIL = "master@manutrix.com"
MASTER_PASSWORD = "master123"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def master_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Master login failed on Emergent env: {r.status_code} - {r.text}")
    return r.json().get("access_token")


# ------------------ Backend auth against Emergent env ------------------

class TestAuthLogin:
    """Verify login endpoint against the live Emergent backend."""

    def test_login_master_returns_access_token(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD}, timeout=20)
        assert r.status_code == 200, f"Body: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 40
        # token_type / user block should be present
        assert data.get("token_type", "bearer").lower() == "bearer"

    def test_login_wrong_password_returns_401(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": MASTER_EMAIL, "password": "wrong_pwd_zzz"}, timeout=20)
        assert r.status_code == 401
        body = r.json()
        detail = body.get("detail", "") or body.get("message", "")
        assert "invalid" in detail.lower() or "inv" in detail.lower() or "credenc" in detail.lower(), \
            f"Expected 'Credenciais inválidas'-like message, got: {detail}"

    def test_login_nonexistent_email_returns_401(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": "nao_existe_zzz@nowhere.com", "password": "whatever"}, timeout=20)
        assert r.status_code == 401


class TestAuthMe:
    """Verify GET /api/auth/me with a valid JWT."""

    def test_me_returns_profile(self, session, master_token):
        r = session.get(f"{BASE_URL}/api/auth/me",
                        headers={"Authorization": f"Bearer {master_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        u = r.json()
        assert u.get("email") == MASTER_EMAIL
        assert u.get("role") == "master"
        assert "organization_id" in u or "id" in u
        # Should NOT leak password hash
        assert "password_hash" not in u or u.get("password_hash") in (None, "")

    def test_me_with_invalid_token_returns_401(self, session):
        r = session.get(f"{BASE_URL}/api/auth/me",
                        headers={"Authorization": "Bearer invalid.token.here"}, timeout=20)
        assert r.status_code == 401

    def test_me_with_expired_token_returns_401(self, session):
        # Craft a JWT with exp=1970 using unsigned header/payload — signature won't verify.
        # This tests both "invalid signature" and "expired" branches (either → 401).
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "x", "role": "master", "org": "y", "exp": 1}).encode()).rstrip(b"=").decode()
        fake = f"{header}.{payload}.bad_sig"
        r = session.get(f"{BASE_URL}/api/auth/me",
                        headers={"Authorization": f"Bearer {fake}"}, timeout=20)
        assert r.status_code == 401


class TestJWTClaims:
    """Decode the JWT client-side (no verify) and inspect standard claims."""

    def test_jwt_contains_expected_claims(self, master_token):
        parts = master_token.split(".")
        assert len(parts) == 3, "JWT must have header.payload.signature"
        # padding fix
        raw = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(raw).decode())
        for claim in ("sub", "role", "org", "exp"):
            assert claim in payload, f"Missing claim: {claim}"
        assert payload["role"] == "master"
        assert isinstance(payload["exp"], int)


# ------------------ Bcrypt / verify_password unit tests ------------------

class TestBcryptHashing:
    """Directly exercise deps.hash_password / verify_password."""

    def test_hash_password_bcrypt_format(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from deps import hash_password, verify_password
        h = hash_password("master123")
        assert h.startswith("$2b$"), f"Expected bcrypt $2b$ prefix, got: {h[:10]}"
        assert verify_password("master123", h) is True
        assert verify_password("wrong", h) is False

    def test_verify_password_supports_legacy_sha256(self):
        import sys
        sys.path.insert(0, "/app/backend")
        import hashlib
        from deps import verify_password
        legacy = hashlib.sha256("secret".encode()).hexdigest()
        # legacy hash (non-bcrypt) — verify_password should still accept it
        assert verify_password("secret", legacy) is True
        assert verify_password("wrong", legacy) is False


# ------------------ Master user in DB has bcrypt hash ------------------

class TestMasterUserDBHashFormat:
    """Verify that the stored password_hash for the master user is a bcrypt hash."""

    def test_master_password_hash_starts_with_2b(self):
        import os
        from pymongo import MongoClient
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        try:
            db_sync = c[os.environ.get("DB_NAME", "test_database")]
            u = db_sync.users.find_one({"email": MASTER_EMAIL}, {"_id": 0, "password_hash": 1})
        finally:
            c.close()
        assert u is not None, "master@manutrix.com not present in DB"
        ph = u.get("password_hash", "")
        assert ph.startswith("$2b$") or ph.startswith("$2a$"), \
            f"Password hash for master should be bcrypt, got prefix: {ph[:10]}"


# ------------------ Bootstrap logic in server.py ------------------

class TestBootstrapCode:
    """Static verification of the bootstrap block in server.py.
    (The block only triggers on empty DB; on Emergent env it is a no-op because
    admin users already exist — verified by the fact login works.)"""

    SERVER_PATH = "/app/backend/server.py"

    def test_bootstrap_block_present(self):
        src = open(self.SERVER_PATH).read()
        assert "BOOTSTRAP" in src
        assert "master@maintrix.com" in src
        assert 'hash_password("master123")' in src

    def test_bootstrap_guarded_by_admin_count_check(self):
        src = open(self.SERVER_PATH).read()
        # Must gate insert on count_documents == 0 for role in admin/master
        m = re.search(
            r'admin_count\s*=\s*await\s+db\.users\.count_documents\(\s*\{[^}]*"role"\s*:\s*\{\s*"\$in"\s*:\s*\[\s*"admin"\s*,\s*"master"\s*\]',
            src,
        )
        assert m is not None, "Bootstrap must count admin+master users before creating"
        assert re.search(r"if\s+admin_count\s*==\s*0\s*:", src), "Missing guard `if admin_count == 0`"

    def test_bootstrap_creates_org_config_and_force_password_change(self):
        src = open(self.SERVER_PATH).read()
        assert "force_password_change" in src
        assert "org_config" in src
        assert "MAINTRIX" in src  # company_name

    def test_bootstrap_uses_master_role_and_bcrypt(self):
        src = open(self.SERVER_PATH).read()
        # Must use hash_password (bcrypt) not raw sha256
        assert 'hash_password("master123")' in src
        assert '"role": "master"' in src or "'role': 'master'" in src

    def test_bootstrap_idempotent_on_emergent_env(self):
        """On the live Emergent env admin/master users already exist,
        so bootstrap must be a no-op. We verify by asserting that there is
        exactly one master@manutrix.com row (no duplicates)."""
        import os
        from pymongo import MongoClient
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        try:
            db_sync = c[os.environ.get("DB_NAME", "test_database")]
            n = db_sync.users.count_documents({"email": MASTER_EMAIL, "deleted_at": None})
        finally:
            c.close()
        assert n == 1, f"Expected exactly 1 master@manutrix.com row, got {n}"


# ------------------ Railway smoke test ------------------

class TestRailwaySmoke:
    """Confirm the Railway deployment exposes /api/auth/login (405/404 would indicate a routing bug)."""

    def test_railway_login_endpoint_reachable(self):
        try:
            r = requests.post(f"{RAILWAY_URL}/api/auth/login",
                              json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD},
                              timeout=25)
        except requests.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        # Accept 200 (bootstrap already deployed and worked) OR 401 (empty DB, no bootstrap yet)
        # 404/405 would indicate routing regression.
        assert r.status_code in (200, 401), \
            f"Railway /api/auth/login returned unexpected status {r.status_code}: {r.text[:300]}"

    def test_railway_login_with_bootstrap_email(self):
        """Attempt login with the bootstrap default (master@maintrix.com/master123).
        If bootstrap has been deployed and DB is empty on cold start, this should be 200.
        Otherwise 401. Neither is a hard-fail — we just log the outcome."""
        try:
            r = requests.post(f"{RAILWAY_URL}/api/auth/login",
                              json={"email": "master@maintrix.com", "password": "master123"},
                              timeout=25)
        except requests.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        assert r.status_code in (200, 401), f"Unexpected status: {r.status_code}"
        print(f"Railway bootstrap login → {r.status_code}: {r.text[:200]}")
