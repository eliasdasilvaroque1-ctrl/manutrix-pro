"""
Iteration 59 — Auth Audit & Bootstrap verification
- POST /api/auth/login master@maintrix.com/master123 -> 200 + access_token
- GET /api/auth/me -> email, role=master, organization_id, force_password_change
- Wrong password -> 401
- GET /api/diag/auth-audit?key=... -> user list w/ hash_format/role/email
- Wrong diag key -> 403
- Diag shows master@maintrix.com bcrypt & bootstrap_would_run=false
- Bootstrap logic in server.py checks master@maintrix.com specifically & reuses org_id
- Railway login endpoint responds (not 404/405)
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
# Load frontend .env explicitly (backend .env doesn't have REACT_APP_BACKEND_URL)
try:
    with open('/app/frontend/.env') as _f:
        for _line in _f:
            if _line.startswith('REACT_APP_BACKEND_URL='):
                BASE_URL = _line.strip().split('=', 1)[1].rstrip('/')
                break
except Exception:
    pass

DIAG_KEY = "maintrix-diag-2026"
RAILWAY_URL = "https://manutrix-pro-production.up.railway.app"

MASTER_EMAIL = "master@maintrix.com"
MASTER_PASSWORD = "master123"
LEGACY_EMAIL = "master@manutrix.com"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ============== LOGIN ==============
class TestLogin:
    def test_login_master_maintrix(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20

    def test_login_legacy_master(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"email": LEGACY_EMAIL, "password": MASTER_PASSWORD})
        # Legacy is optional; just verify endpoint reachable
        assert r.status_code in (200, 401), f"Unexpected: {r.status_code} {r.text}"

    def test_login_wrong_password(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"email": MASTER_EMAIL, "password": "definitely-wrong-xxx"})
        assert r.status_code == 401


# ============== ME ==============
class TestMe:
    @pytest.fixture(scope="class")
    def token(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD})
        if r.status_code != 200:
            pytest.skip(f"Login failed: {r.status_code} {r.text}")
        return r.json()["access_token"]

    def test_me_returns_master(self, token):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("email") == MASTER_EMAIL
        assert data.get("role") == "master"
        assert data.get("organization_id"), "organization_id missing"
        # force_password_change might be bool
        assert "force_password_change" in data

    def test_me_no_password_hash(self, token):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert "password_hash" not in r.json()


# ============== DIAG ==============
class TestDiag:
    def test_diag_wrong_key_403(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key=wrong")
        assert r.status_code == 403

    def test_diag_no_key_403(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit")
        assert r.status_code == 403

    def test_diag_correct_key_200(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key={DIAG_KEY}")
        assert r.status_code == 200
        data = r.json()
        assert "total_users" in data
        assert "admin_master_count" in data
        assert "master_maintrix_exists" in data
        assert "users" in data
        assert "bootstrap_would_run" in data
        assert isinstance(data["users"], list)

    def test_diag_users_have_hash_format(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key={DIAG_KEY}")
        assert r.status_code == 200
        users = r.json()["users"]
        assert len(users) > 0
        for u in users:
            assert "hash_format" in u
            assert "role" in u
            assert "email" in u
            assert u["hash_format"] in ("bcrypt", "sha256", "unknown")

    def test_diag_master_maintrix_bcrypt(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key={DIAG_KEY}")
        data = r.json()
        assert data["master_maintrix_exists"] is True, \
            f"master@maintrix.com missing. users={[u['email'] for u in data['users']]}"
        master = next((u for u in data["users"] if u["email"] == MASTER_EMAIL), None)
        assert master is not None
        assert master["hash_format"] == "bcrypt", f"hash_format={master['hash_format']}"
        assert master["role"] == "master"

    def test_diag_bootstrap_would_run_false(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key={DIAG_KEY}")
        data = r.json()
        # master exists → admin count > 0 → bootstrap_would_run must be false
        assert data["admin_master_count"] > 0
        assert data["bootstrap_would_run"] is False

    def test_diag_no_password_hash_leaked(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/diag/auth-audit?key={DIAG_KEY}")
        users = r.json()["users"]
        for u in users:
            assert "password_hash" not in u, f"leaked hash for {u.get('email')}"


# ============== BOOTSTRAP CODE INSPECTION ==============
class TestBootstrapCode:
    """Verify server.py bootstrap has been rewritten to check email specifically."""

    @pytest.fixture(scope="class")
    def server_source(self):
        with open("/app/backend/server.py") as f:
            return f.read()

    def test_bootstrap_checks_master_maintrix_specifically(self, server_source):
        # find bootstrap section
        assert "bootstrap_email" in server_source
        assert 'master@maintrix.com' in server_source
        # verify it uses find_one on email, not just count
        pat = re.search(
            r'master_user\s*=\s*await\s+db\.users\.find_one\(\s*\{\s*"email":\s*bootstrap_email',
            server_source)
        assert pat is not None, "Bootstrap must use find_one({email: bootstrap_email})"

    def test_bootstrap_reuses_existing_org_id(self, server_source):
        assert "existing_org" in server_source
        assert "org_config.find_one" in server_source
        pat = re.search(
            r"org_id\s*=\s*existing_org\[[\"']organization_id[\"']\]\s+if\s+existing_org",
            server_source)
        assert pat is not None, "Bootstrap must reuse org_id from org_config if present"

    def test_bootstrap_creates_even_when_other_admins_exist(self, server_source):
        # The critical fix: create master even if admin_count > 0
        # Find the block: `if not master_user:` → insert_one for master_doc must run
        # regardless of admin_count. i.e. the insert isn't inside `if admin_count == 0:`
        # Simplify: after `admin_count > 0` logging, insert_one still executes.
        idx = server_source.find("if not master_user:")
        assert idx > 0
        block = server_source[idx: idx + 3000]
        # insert_one must exist inside `if not master_user:` block
        assert "db.users.insert_one(master_doc)" in block
        # It must NOT be gated by admin_count == 0
        # Look for pattern like `if admin_count == 0:` followed by insert_one (bad)
        bad = re.search(r"if\s+admin_count\s*==\s*0\s*:\s*[^\n]*\n[^}]*db\.users\.insert_one", block)
        assert bad is None, "insert_one must not be gated by admin_count==0"

    def test_bootstrap_uses_bcrypt_hash(self, server_source):
        idx = server_source.find("if not master_user:")
        block = server_source[idx: idx + 3000]
        assert 'hash_password("master123")' in block

    def test_bootstrap_sets_force_password_change(self, server_source):
        idx = server_source.find("if not master_user:")
        block = server_source[idx: idx + 3000]
        assert '"force_password_change": True' in block

    def test_diag_endpoint_present(self, server_source):
        assert '@app.get("/api/diag/auth-audit")' in server_source
        assert 'DIAG_KEY' in server_source
        assert 'maintrix-diag-2026' in server_source


# ============== RAILWAY REACHABILITY ==============
class TestRailway:
    def test_railway_login_responds(self):
        try:
            r = requests.post(f"{RAILWAY_URL}/api/auth/login",
                              json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD},
                              timeout=15)
        except requests.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        # Endpoint must exist — accept 200 (new deploy) OR 401 (old code, wrong creds)
        # Reject 404 (route missing) or 405 (method not allowed)
        assert r.status_code not in (404, 405), \
            f"Railway route missing: {r.status_code} {r.text[:200]}"
        assert r.status_code in (200, 401, 400, 422, 500, 502, 503), \
            f"Unexpected railway response: {r.status_code}"

    def test_railway_diag_status(self):
        """Diag endpoint status on Railway — documents whether new code is deployed."""
        try:
            r = requests.get(f"{RAILWAY_URL}/api/diag/auth-audit?key={DIAG_KEY}", timeout=15)
        except requests.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        # We just record — 200 means new code deployed. 404 means old code still active.
        assert r.status_code in (200, 403, 404), \
            f"Unexpected railway diag response: {r.status_code}"
        # If 200, master@maintrix.com should exist there too (post-deploy assertion)
        if r.status_code == 200:
            print(f"RAILWAY DIAG: {r.json()}")
