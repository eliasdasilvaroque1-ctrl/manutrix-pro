"""
FASE 1 — White Label Enterprise (Iteration 63)
Tests public branding endpoints and org_config theme fields powering FE CSS variables.
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MASTER_EMAIL = "master@maintrix.com"
MASTER_PASS = "master123"


@pytest.fixture(scope="module")
def master_token():
    r = requests.post(f"{API}/auth/login", json={"email": MASTER_EMAIL, "password": MASTER_PASS}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def org():
    r = requests.get(f"{API}/public/organizations", timeout=10)
    assert r.status_code == 200
    orgs = r.json()
    assert isinstance(orgs, list) and len(orgs) >= 1, "Expected at least 1 organization"
    return orgs[0]


# ============== Public endpoints (no auth) ==============
class TestPublicBranding:
    def test_list_organizations_public(self):
        r = requests.get(f"{API}/public/organizations", timeout=10)
        assert r.status_code == 200
        orgs = r.json()
        assert isinstance(orgs, list)
        assert len(orgs) >= 1, "At least 1 org must exist for auto-select on LoginPage"
        o = orgs[0]
        for k in ["id", "nome", "cor_primaria"]:
            assert k in o, f"Missing key {k} in org listing"

    def test_public_branding_by_org_id(self, org):
        r = requests.get(f"{API}/public/branding/{org['id']}", timeout=10)
        assert r.status_code == 200
        b = r.json()
        assert b.get("organization_id") == org["id"]
        # identidade + tema present
        assert "identidade" in b and "tema" in b
        ident = b["identidade"]
        tema = b["tema"]
        # nome for LoginPage should not fall back to hardcoded MAINTRIX
        nome_display = ident.get("nome_empresa") or ident.get("nome_sistema")
        assert nome_display and nome_display != "MAINTRIX", \
            f"Expected a dynamic org name; got '{nome_display}'"
        # Theme colors present
        for k in ["cor_primaria", "cor_secundaria", "cor_fundo"]:
            assert k in tema and tema[k].startswith("#"), f"Missing/invalid {k}"

    def test_public_branding_unknown_returns_default(self):
        r = requests.get(f"{API}/public/branding/nonexistent-xyz-123", timeout=10)
        # Endpoint returns default payload instead of 404
        assert r.status_code == 200
        b = r.json()
        assert b.get("organization_id") is None
        assert b.get("identidade", {}).get("nome_sistema") == "MAINTRIX"


# ============== Authenticated /api/org/config (feeds branding) ==============
class TestOrgConfig:
    def test_get_org_config_authenticated(self, master_token):
        r = requests.get(f"{API}/org/config", headers={"Authorization": f"Bearer {master_token}"}, timeout=10)
        assert r.status_code == 200
        cfg = r.json()
        assert "identidade" in cfg
        assert "tema" in cfg
        tema = cfg["tema"]
        # Core color CSS variables required by FE applyCSS — MUST be present
        for k in ["cor_primaria", "cor_secundaria", "cor_fundo", "cor_texto", "cor_destaque"]:
            assert k in tema, f"Missing tema.{k} required for FE CSS variable"

    def test_org_config_optional_menu_colors(self, master_token):
        """
        Documenting: cor_menu / cor_login / cor_header live in identidade/tema
        for the White Label. The org_config default builder sets them (org_config.py:176-178),
        but PUT /org/config/tema does NOT allow them — only PUT /org/config/branding does.
        Existing (already-seeded) org rows created before the branding fields existed
        may be missing them. FE branding.js has DEFAULT_BRANDING fallbacks, so UI still works.
        """
        r = requests.get(f"{API}/org/config", headers={"Authorization": f"Bearer {master_token}"}, timeout=10)
        assert r.status_code == 200
        tema = r.json().get("tema", {})
        missing = [k for k in ["cor_menu", "cor_login", "cor_header"] if k not in tema]
        # Not a hard failure — FE has fallbacks. Report as informational.
        if missing:
            print(f"INFO: tema missing extended color keys: {missing} (FE has fallbacks)")

    def test_login_returns_user_with_org_id(self):
        r = requests.post(f"{API}/auth/login", json={"email": MASTER_EMAIL, "password": MASTER_PASS}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "user" in data
        # organization_id needed for BrandingLoader.loadFromUser(user)
        assert data["user"].get("organization_id"), "User missing organization_id — BrandingLoader will not load branding"


# ============== Pages exercised by the E2E flow ==============
class TestKeyPagesAvailable:
    def _client(self, tok):
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {tok}"})
        return s

    def test_central_endpoint(self, master_token):
        s = self._client(master_token)
        r = s.get(f"{API}/central", timeout=15)
        assert r.status_code == 200, f"/central failed: {r.status_code}"

    def test_dashboard_kpis(self, master_token):
        s = self._client(master_token)
        r = s.get(f"{API}/kpis", timeout=15)
        assert r.status_code == 200

    def test_list_ativos(self, master_token):
        s = self._client(master_token)
        r = s.get(f"{API}/ativos", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_os(self, master_token):
        s = self._client(master_token)
        r = s.get(f"{API}/ordens-servico", timeout=15)
        assert r.status_code == 200
