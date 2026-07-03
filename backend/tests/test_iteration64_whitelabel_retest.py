"""
Iteration 64 — FASE 1 White Label RETEST
Validates:
- GET /api/public/organizations returns 'ASTEC Cedro'
- GET /api/public/branding/{org_id} returns full tema (cor_menu, cor_login, cor_header) and identidade
- GET /api/public/branding/{unknown} default fallback contains all fields
- PUT /api/org/config/tema accepts cor_menu/cor_login/cor_header
- POST /api/auth/login works with master@maintrix.com
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

MASTER_EMAIL = "master@maintrix.com"
MASTER_PWD = "master123"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth(api):
    r = api.post(f"{BASE_URL}/api/auth/login",
                 json={"email": MASTER_EMAIL, "password": MASTER_PWD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return {
        "token": data["access_token"],
        "user": data["user"],
        "org_id": data["user"]["organization_id"],
    }


class TestPublicOrgs:
    def test_public_organizations_returns_astec_cedro(self, api):
        r = api.get(f"{BASE_URL}/api/public/organizations")
        assert r.status_code == 200
        orgs = r.json()
        assert isinstance(orgs, list) and len(orgs) >= 1
        names = [o.get("nome") for o in orgs]
        assert "ASTEC Cedro" in names, f"Expected 'ASTEC Cedro' in {names}"

    def test_public_organizations_has_required_fields(self, api):
        r = api.get(f"{BASE_URL}/api/public/organizations")
        orgs = r.json()
        target = next((o for o in orgs if o.get("nome") == "ASTEC Cedro"), None)
        assert target is not None
        for k in ("id", "nome", "cor_primaria"):
            assert k in target
        assert target["cor_primaria"].startswith("#")


class TestPublicBranding:
    def test_branding_by_org_id(self, api, auth):
        r = api.get(f"{BASE_URL}/api/public/branding/{auth['org_id']}")
        assert r.status_code == 200
        b = r.json()
        assert b["organization_id"] == auth["org_id"]
        # identidade
        ident = b["identidade"]
        assert ident.get("nome_empresa") == "ASTEC Cedro"
        # tema — includes cor_menu, cor_login, cor_header
        tema = b["tema"]
        for key in ("cor_primaria", "cor_secundaria", "cor_menu", "cor_login", "cor_header"):
            assert key in tema, f"tema missing {key}"
        assert tema["cor_primaria"] == "#10b981"

    def test_branding_fallback_unknown_identifier(self, api):
        r = api.get(f"{BASE_URL}/api/public/branding/procure-manutrix")
        assert r.status_code == 200
        b = r.json()
        # fallback returns organization_id = None
        assert b.get("organization_id") is None
        ident = b["identidade"]
        tema = b["tema"]
        # Fallback should contain full field set
        assert "subtitulo" in ident
        assert "nome_empresa" in ident
        assert "cor_menu" in tema
        assert "cor_login" in tema
        assert "cor_header" in tema


class TestOrgConfigTemaWhitelist:
    def test_put_tema_accepts_extended_colors(self, api, auth):
        headers = {"Authorization": f"Bearer {auth['token']}"}
        payload = {
            "cor_primaria": "#10b981",
            "cor_menu": "#0f172a",
            "cor_login": "#020617",
            "cor_header": "#0f172a",
        }
        r = api.put(f"{BASE_URL}/api/org/config/tema", json=payload, headers=headers)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        cfg = r.json()
        tema = cfg.get("tema", {})
        assert tema.get("cor_menu") == "#0f172a"
        assert tema.get("cor_login") == "#020617"
        assert tema.get("cor_header") == "#0f172a"
        assert tema.get("cor_primaria") == "#10b981"

    def test_get_org_config_persists_extended_colors(self, api, auth):
        headers = {"Authorization": f"Bearer {auth['token']}"}
        r = api.get(f"{BASE_URL}/api/org/config", headers=headers)
        assert r.status_code == 200
        cfg = r.json()
        tema = cfg.get("tema", {})
        assert tema.get("cor_menu") == "#0f172a"
        assert tema.get("cor_login") == "#020617"
        assert tema.get("cor_header") == "#0f172a"


class TestLogin:
    def test_login_master_maintrix(self, api):
        r = api.post(f"{BASE_URL}/api/auth/login",
                     json={"email": MASTER_EMAIL, "password": MASTER_PWD})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["organization_id"]
