"""
Iteration 56 — Sprint Produção 001 tests.
Validates:
 - Login works on Emergent env (master + test.mec)
 - Auth-protected endpoints reachable after login
 - Railway backend endpoint responds (401 expected due to different DB, NOT 405/404)
 - Railway CORS preflight OPTIONS returns 200/204
 - Frontend files: vercel.json, api.js, index.html cleaned of Emergent
"""
import os
import re
import json
import pathlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Fallback to reading frontend/.env
    env_path = pathlib.Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")

RAILWAY_URL = "https://manutrix-pro-production.up.railway.app"

MASTER = {"email": "master@manutrix.com", "password": "master123"}
TEC_MEC = {"email": "test.mec@maintrix.com", "password": "tec123"}


# ---------- Emergent backend login ----------
class TestEmergentAuth:
    def test_login_master(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json=MASTER, timeout=30)
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "access_token" in data, f"No access_token in: {data}"
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20

    def test_login_test_mec(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json=TEC_MEC, timeout=30)
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "access_token" in data

    def test_login_wrong_password(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER["email"], "password": "wrong"},
            timeout=30,
        )
        assert r.status_code in (400, 401, 403), f"Expected 4xx got {r.status_code}"


@pytest.fixture(scope="module")
def master_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=MASTER, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Master login failed: {r.status_code}")
    return r.json()["access_token"]


# ---------- Auth-protected endpoints ----------
class TestProtectedEndpoints:
    def test_central_after_login(self, master_token):
        r = requests.get(
            f"{BASE_URL}/api/central",
            headers={"Authorization": f"Bearer {master_token}"},
            timeout=30,
        )
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert isinstance(data, (dict, list))

    def test_ativos_after_login(self, master_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos",
            headers={"Authorization": f"Bearer {master_token}"},
            timeout=30,
        )
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Expected at least 1 ativo"

    def test_ativos_no_auth(self):
        r = requests.get(f"{BASE_URL}/api/ativos", timeout=30)
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"


# ---------- Railway backend reachability ----------
class TestRailwayBackend:
    def test_railway_login_endpoint_responds(self):
        """Railway should NOT return 405 or 404 — should return 401 (different DB) or 200.
        This proves the endpoint exists and accepts POST."""
        try:
            r = requests.post(
                f"{RAILWAY_URL}/api/auth/login", json=MASTER, timeout=30
            )
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        assert r.status_code not in (
            404,
            405,
        ), f"Railway endpoint broken: {r.status_code} — {r.text[:200]}"
        # Expected: 401 unauthorized (different DB has no such user) or 200 if user exists
        assert r.status_code in (200, 400, 401, 403, 422), (
            f"Unexpected status {r.status_code}: {r.text[:200]}"
        )

    def test_railway_cors_preflight(self):
        try:
            r = requests.options(
                f"{RAILWAY_URL}/api/auth/login",
                headers={
                    "Origin": "https://maintrix.com.br",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Railway unreachable: {e}")
        assert r.status_code in (
            200,
            204,
        ), f"CORS preflight failed: {r.status_code} — {r.text[:200]}"


# ---------- File assertions ----------
class TestFrontendFiles:
    def test_vercel_json_has_rewrites(self):
        p = pathlib.Path("/app/frontend/vercel.json")
        assert p.exists(), "vercel.json missing"
        cfg = json.loads(p.read_text())
        assert "rewrites" in cfg, "no rewrites key"
        rw = cfg["rewrites"]
        assert isinstance(rw, list) and len(rw) >= 1
        found = False
        for r in rw:
            src = r.get("source", "")
            dst = r.get("destination", "")
            if "/api/:path*" in src and "manutrix-pro-production.up.railway.app" in dst:
                found = True
                break
        assert found, f"expected /api/:path* → Railway rewrite, got {rw}"

    def test_api_js_fallback_empty(self):
        p = pathlib.Path("/app/frontend/src/lib/api.js")
        content = p.read_text()
        # Look for BACKEND_URL with empty string fallback
        assert re.search(
            r"REACT_APP_BACKEND_URL\s*\|\|\s*[\"']{2}", content
        ), "api.js missing BACKEND_URL fallback to empty string"

    def test_index_html_no_emergent(self):
        p = pathlib.Path("/app/frontend/public/index.html")
        content = p.read_text()
        lower = content.lower()
        for banned in ["emergent", "posthog", "made with"]:
            assert banned not in lower, (
                f"index.html still contains '{banned}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
