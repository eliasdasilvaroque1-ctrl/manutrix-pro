"""
FASE 2 - White Label MASTER Designer endpoints
Tests:
  - Login master@maintrix.com/master123
  - GET /api/master/organizations
  - POST /api/master/organizations (create new org)
  - GET /api/master/organizations/{org_id}/config
  - PUT /api/master/organizations/{org_id}/config (update branding)
  - Isolation: updating one org doesn't affect another
  - Non-master denied (403)
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MASTER_EMAIL = "master@maintrix.com"
MASTER_PASSWORD = "master123"


@pytest.fixture(scope="module")
def master_token():
    r = requests.post(f"{API}/auth/login", json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Master login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    assert data.get("user", {}).get("role") == "master"
    return data["access_token"]


@pytest.fixture(scope="module")
def headers(master_token):
    return {"Authorization": f"Bearer {master_token}", "Content-Type": "application/json"}


# ---------- 1. Login ----------
def test_master_login_success():
    r = requests.post(f"{API}/auth/login", json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "master"
    assert isinstance(body.get("access_token"), str) and len(body["access_token"]) > 10


# ---------- 2. List organizations ----------
def test_master_list_organizations(headers):
    r = requests.get(f"{API}/master/organizations", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    orgs = r.json()
    assert isinstance(orgs, list)
    assert len(orgs) >= 1, "Expected at least 1 organization"
    # Each org should have id, nome, config
    for o in orgs:
        assert "id" in o
        assert "nome" in o
        assert "config" in o
        # config may include identidade/tema/dominio
        if o["config"]:
            assert "organization_id" in o["config"]


def test_non_master_cannot_list_organizations():
    """Non-master tries to hit /master/organizations -> 403."""
    # Try admin login (may not exist on this instance)
    for cred in [
        {"email": "test.admin@maintrix.com", "password": "admin123"},
        {"email": "admin@manutrix.com", "password": "admin123"},
    ]:
        rlogin = requests.post(f"{API}/auth/login", json=cred, timeout=30)
        if rlogin.status_code == 200:
            tok = rlogin.json().get("access_token")
            r = requests.get(f"{API}/master/organizations", headers={"Authorization": f"Bearer {tok}"}, timeout=30)
            assert r.status_code in (401, 403), f"Non-master got {r.status_code} for /master/organizations"
            return
    pytest.skip("No non-master credentials available")


# ---------- 3. GET config for specific org ----------
def test_master_get_org_config(headers):
    orgs = requests.get(f"{API}/master/organizations", headers=headers, timeout=30).json()
    assert orgs
    org_id = orgs[0]["id"]
    r = requests.get(f"{API}/master/organizations/{org_id}/config", headers=headers, timeout=30)
    assert r.status_code == 200
    cfg = r.json()
    assert cfg["organization_id"] == org_id
    assert "identidade" in cfg
    assert "tema" in cfg


def test_master_get_config_nonexistent_org(headers):
    fake_id = str(uuid.uuid4())
    r = requests.get(f"{API}/master/organizations/{fake_id}/config", headers=headers, timeout=30)
    assert r.status_code == 404


# ---------- 4. Create new organization ----------
def test_master_create_organization(headers):
    new_name = f"TEST_WL_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{API}/master/organizations", headers=headers, json={"nome": new_name}, timeout=30)
    assert r.status_code == 200, r.text
    org = r.json()
    assert org["nome"] == new_name
    assert "id" in org
    assert "config" in org
    assert org["config"]["organization_id"] == org["id"]
    # Verify persistence via GET list
    orgs = requests.get(f"{API}/master/organizations", headers=headers, timeout=30).json()
    ids = [o["id"] for o in orgs]
    assert org["id"] in ids


def test_master_create_organization_empty_name(headers):
    r = requests.post(f"{API}/master/organizations", headers=headers, json={"nome": ""}, timeout=30)
    assert r.status_code == 400


# ---------- 5. PUT config (update branding) ----------
def test_master_update_org_config_and_verify(headers):
    # Create a fresh org
    new_name = f"TEST_WL_UPD_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{API}/master/organizations", headers=headers, json={"nome": new_name}, timeout=30)
    org_id = r.json()["id"]

    payload = {
        "nome_empresa": "TEST_WL EMPRESA",
        "nome_sistema": "TEST_WL SISTEMA",
        "subtitulo": "TEST_WL subtitulo",
        "rodape": "TEST_WL rodape",
        "mostrar_powered_by": False,
        "texto_login": "TEST bem-vindo",
        "texto_institucional": "TEST institucional",
        "cor_primaria": "#ff0000",
        "cor_secundaria": "#00ff00",
        "cor_menu": "#123456",
        "cor_header": "#654321",
        "cor_login": "#abcdef",
        "cor_fundo": "#111111",
        "cor_texto": "#eeeeee",
        "cor_destaque": "#ff00ff",
        "subdominio": f"test{uuid.uuid4().hex[:5]}",
        "dominio_customizado": "test.example.com",
    }
    r = requests.put(f"{API}/master/organizations/{org_id}/config", headers=headers, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    cfg = r.json()
    ident = cfg["identidade"]
    tema = cfg["tema"]
    dom = cfg.get("dominio", {})
    assert ident["nome_empresa"] == "TEST_WL EMPRESA"
    assert ident["nome_sistema"] == "TEST_WL SISTEMA"
    assert ident["subtitulo"] == "TEST_WL subtitulo"
    assert ident["rodape"] == "TEST_WL rodape"
    assert ident["mostrar_powered_by"] is False
    assert ident["texto_login"] == "TEST bem-vindo"
    assert ident["texto_institucional"] == "TEST institucional"
    assert tema["cor_primaria"] == "#ff0000"
    assert tema["cor_menu"] == "#123456"
    assert tema["cor_header"] == "#654321"
    assert tema["cor_login"] == "#abcdef"
    assert tema["cor_destaque"] == "#ff00ff"
    assert dom.get("subdominio") == payload["subdominio"]
    assert dom.get("dominio_customizado") == "test.example.com"

    # Re-GET to verify persistence
    r2 = requests.get(f"{API}/master/organizations/{org_id}/config", headers=headers, timeout=30)
    assert r2.status_code == 200
    cfg2 = r2.json()
    assert cfg2["tema"]["cor_primaria"] == "#ff0000"
    assert cfg2["identidade"]["nome_empresa"] == "TEST_WL EMPRESA"


# ---------- 6. Isolation between orgs ----------
def test_org_config_isolation(headers):
    # Create two orgs, update ONE, verify OTHER unchanged
    n1 = f"TEST_WL_ISO_A_{uuid.uuid4().hex[:6]}"
    n2 = f"TEST_WL_ISO_B_{uuid.uuid4().hex[:6]}"
    o1 = requests.post(f"{API}/master/organizations", headers=headers, json={"nome": n1}, timeout=30).json()
    o2 = requests.post(f"{API}/master/organizations", headers=headers, json={"nome": n2}, timeout=30).json()

    # Update org1 only
    requests.put(f"{API}/master/organizations/{o1['id']}/config", headers=headers,
                 json={"cor_primaria": "#aa11bb", "nome_empresa": "ORG1_UPDATED"}, timeout=30)

    # Fetch org2
    cfg2 = requests.get(f"{API}/master/organizations/{o2['id']}/config", headers=headers, timeout=30).json()
    assert cfg2["tema"]["cor_primaria"] != "#aa11bb"
    assert cfg2["identidade"].get("nome_empresa") != "ORG1_UPDATED"

    # Fetch org1 (must have update)
    cfg1 = requests.get(f"{API}/master/organizations/{o1['id']}/config", headers=headers, timeout=30).json()
    assert cfg1["tema"]["cor_primaria"] == "#aa11bb"
    assert cfg1["identidade"]["nome_empresa"] == "ORG1_UPDATED"


# ---------- 7. Update nonexistent org config ----------
def test_master_update_nonexistent_org_config(headers):
    fake_id = str(uuid.uuid4())
    r = requests.put(f"{API}/master/organizations/{fake_id}/config", headers=headers, json={"cor_primaria": "#123456"}, timeout=30)
    # Should 404 (org doesn't exist)
    assert r.status_code == 404
