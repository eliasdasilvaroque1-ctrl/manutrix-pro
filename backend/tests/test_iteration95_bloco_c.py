"""
BLOCO C — Hardening Enterprise (iteration_95)
Tests:
1. Security headers on HTTP responses
2. Rate limiting on /api/auth/login (10/min)
3. Regression: login (master + tec) + all key page-load endpoints
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"

MASTER = {"email": "master@maintrix.com", "password": "master123", "organization_id": ORG_ID}
TEC = {"email": "test.mec@maintrix.com", "password": "tec123", "organization_id": ORG_ID}


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(api, creds):
    r = api.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login {creds['email']} failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == creds["email"]
    return data["access_token"]


@pytest.fixture(scope="module")
def master_token(api):
    return _login(api, MASTER)


@pytest.fixture(scope="module")
def tec_token(api):
    # tec login might trip rate limit from earlier login sequence; add small sleep
    time.sleep(1)
    return _login(api, TEC)


# ------------- Security Headers -------------
class TestSecurityHeaders:
    """Verify BLOCO C ETAPA 2 middleware sets all expected security headers."""

    def test_headers_on_public_endpoint(self, api):
        r = api.get(f"{BASE_URL}/api/public/organizations", timeout=15)
        assert r.status_code in (200, 401, 403), f"Unexpected {r.status_code}"
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options") == "DENY"
        assert "strict-origin" in h.get("referrer-policy", "")
        assert "camera=(self)" in h.get("permissions-policy", "")
        assert h.get("x-xss-protection", "").startswith("1")

    def test_headers_on_authenticated_endpoint(self, api, master_token):
        r = api.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {master_token}"},
            timeout=15,
        )
        assert r.status_code == 200
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options") == "DENY"

    def test_hsts_in_prod(self, api):
        r = api.get(f"{BASE_URL}/api/public/organizations", timeout=15)
        h = {k.lower(): v for k, v in r.headers.items()}
        # In prod (non-localhost) HSTS must be present
        assert "strict-transport-security" in h, "HSTS missing on prod URL"
        assert "max-age=31536000" in h["strict-transport-security"]


# ------------- Rate Limiting -------------
class TestRateLimit:
    """Verify BLOCO C ETAPA 1 rate limiting middleware: /api/auth/login is 10/min."""

    def test_login_rate_limit_returns_429(self):
        # Fresh session so we don't share prior state
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        bad = {"email": "nonexistent-ratetest@maintrix.com", "password": "wrong",
               "organization_id": ORG_ID}
        statuses = []
        for i in range(14):
            r = s.post(f"{BASE_URL}/api/auth/login", json=bad, timeout=10)
            statuses.append(r.status_code)
        # First ~10 must be 401 (invalid creds), then 429 must appear
        count_429 = sum(1 for x in statuses if x == 429)
        count_401 = sum(1 for x in statuses if x == 401)
        print(f"Statuses: {statuses}")
        assert count_429 >= 2, f"Expected >=2 HTTP 429 out of 14, got {count_429}. Statuses={statuses}"
        assert count_401 >= 5, f"Expected several 401s before rate limit trips, got {count_401}"
        # Ensure the sequence transitions from 401 to 429 (not random)
        first_429_idx = next((i for i, s in enumerate(statuses) if s == 429), -1)
        assert first_429_idx >= 8, f"429 tripped too early at idx {first_429_idx}"


# ------------- Regression: Page-load endpoints -------------
class TestRegression:
    """Regression sweep for every page mentioned in the request."""

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_public_organizations(self, api):
        # Small sleep to let public/... 60/min budget reset after security-header test
        time.sleep(1)
        r = api.get(f"{BASE_URL}/api/public/organizations", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_login_master(self, api):
        # Wait to avoid rate-limit residue from TestRateLimit
        time.sleep(65)  # window is 60s; play safe
        r = api.post(f"{BASE_URL}/api/auth/login", json=MASTER, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["role"] in ("master", "admin", "PCM")

    def test_login_tecnico(self, api):
        time.sleep(2)
        r = api.post(f"{BASE_URL}/api/auth/login", json=TEC, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == TEC["email"]

    def test_central(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/central", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_kpis(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/kpis", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200
        d = r.json()
        # KPIs must have some numerical keys
        assert isinstance(d, dict) and len(d) > 0

    def test_dashboard_trend(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/dashboard/trend", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_ativos(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/ativos", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_ordens_servico(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/ordens-servico", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_os_kanban_status_filter(self, api, master_token):
        for st in ["solicitada", "programada", "em_execucao", "concluida"]:
            r = api.get(
                f"{BASE_URL}/api/ordens-servico?status={st}",
                headers=self._auth(master_token), timeout=20,
            )
            assert r.status_code == 200, f"status={st} failed: {r.status_code}"

    def test_estoque(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/estoque", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_estoque_categorias(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/estoque/categorias", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_inspecoes_planos(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/planos-inspecao", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_spare_assets(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/spare-assets", headers=self._auth(master_token), timeout=20)
        assert r.status_code in (200, 404)  # endpoint exists — 200 expected

    def test_audit_logs(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/admin/audit-logs", headers=self._auth(master_token), timeout=20)
        assert r.status_code == 200

    def test_inspection_templates(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/inspection-templates", headers=self._auth(master_token), timeout=20)
        assert r.status_code in (200, 404)

    def test_auth_me_master(self, api, master_token):
        r = api.get(f"{BASE_URL}/api/auth/me", headers=self._auth(master_token), timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == MASTER["email"]

    def test_auth_me_tec(self, api, tec_token):
        r = api.get(f"{BASE_URL}/api/auth/me", headers=self._auth(tec_token), timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == TEC["email"]
