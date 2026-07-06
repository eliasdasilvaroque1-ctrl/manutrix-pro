"""RC-07 Viewer role hardening tests.

Verifies:
  * Master can create a viewer user
  * Viewer can login (after force_password_change flipped)
  * Viewer is BLOCKED (403) from write endpoints and export endpoints
  * Viewer can READ /api/ativos and the public portal endpoint

Cleanup:
  * The created viewer is deleted at the end of the module.
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

MASTER_EMAIL = "master@maintrix.com"
MASTER_PWD = "master123"

VIEWER_EMAIL = "rc07test@maintrix.com"
VIEWER_PWD = "v123"

_state = {}


def _get_astec_org(session):
    r = session.get(f"{API}/public/organizations")
    r.raise_for_status()
    orgs = r.json()
    astec = next((o for o in orgs if "ASTEC" in (o.get("nome") or "").upper()), orgs[0] if orgs else None)
    assert astec is not None, "No ASTEC org found"
    return astec["id"]


def _login(session, email, pwd, org_id):
    r = session.post(f"{API}/auth/login", json={
        "email": email,
        "password": pwd,
        "organization_id": org_id,
    })
    return r


@pytest.fixture(scope="module")
def master_token():
    s = requests.Session()
    org_id = _get_astec_org(s)
    _state["org_id"] = org_id
    r = _login(s, MASTER_EMAIL, MASTER_PWD, org_id)
    assert r.status_code == 200, f"Master login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def viewer_user(master_token):
    """Create a viewer, flip force_password_change=False, yield ID, delete."""
    headers = {"Authorization": f"Bearer {master_token}"}
    # Clean any leftover with same email
    r = requests.get(f"{API}/admin/users", headers=headers)
    if r.status_code == 200:
        for u in r.json():
            if u.get("email") == VIEWER_EMAIL:
                requests.delete(f"{API}/admin/users/{u['id']}", headers=headers)

    payload = {
        "email": VIEWER_EMAIL,
        "password": VIEWER_PWD,
        "nome": "RC07 Test Viewer",
        "role": "visualizador",
    }
    r = requests.post(f"{API}/admin/users", headers=headers, json=payload)
    assert r.status_code in (200, 201), f"Create viewer failed: {r.status_code} {r.text}"
    user = r.json()
    uid = user.get("id") or user.get("_id")
    assert uid, f"No id in {user}"

    # Flip force_password_change
    r = requests.put(f"{API}/admin/users/{uid}",
                     headers=headers,
                     json={"force_password_change": False})
    assert r.status_code == 200, f"PUT force_password_change failed: {r.status_code} {r.text}"

    yield uid

    # Cleanup
    requests.delete(f"{API}/admin/users/{uid}", headers=headers)


@pytest.fixture(scope="module")
def viewer_token(viewer_user):
    s = requests.Session()
    org_id = _state["org_id"]
    r = _login(s, VIEWER_EMAIL, VIEWER_PWD, org_id)
    assert r.status_code == 200, f"Viewer login failed: {r.status_code} {r.text}"
    data = r.json()
    # force_password_change must be false
    assert data.get("user", {}).get("force_password_change") in (False, None), \
        f"force_password_change still true: {data}"
    return data["access_token"]


# --------- READ endpoints must succeed ---------

class TestViewerReadAccess:
    def test_viewer_can_list_ativos(self, viewer_token):
        r = requests.get(f"{API}/ativos", headers={"Authorization": f"Bearer {viewer_token}"})
        assert r.status_code == 200, f"GET /ativos {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert isinstance(data, list)
        # Do not hard-fail on count; but expect >0 in seeded ASTEC
        assert len(data) >= 1, "expected at least 1 ativo"


# --------- WRITE endpoints must be 403 ---------

class TestViewerBlockedWrites:
    def _hdr(self, tok):
        return {"Authorization": f"Bearer {tok}"}

    def test_post_ordens_servico_forbidden(self, viewer_token):
        r = requests.post(f"{API}/ordens-servico", headers=self._hdr(viewer_token),
                          json={"ativo_id": "x", "titulo": "TEST_RC07", "tipo": "corretiva",
                                "disciplina": "mecanica", "prioridade": "media", "descricao": "t"})
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"

    def test_post_ativos_forbidden(self, viewer_token, master_token):
        # Get a valid sector_id from an existing ativo so request survives pydantic.
        r_at = requests.get(f"{API}/ativos", headers={"Authorization": f"Bearer {master_token}"})
        sector_id = None
        if r_at.status_code == 200 and r_at.json():
            sector_id = r_at.json()[0].get("sector_id") or r_at.json()[0].get("area_id")
        payload = {"tag": "TEST_RC07", "nome": "TEST", "tipo_equipamento": "outros"}
        if sector_id:
            payload["sector_id"] = sector_id
        r = requests.post(f"{API}/ativos", headers=self._hdr(viewer_token), json=payload)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"

    def test_post_estoque_forbidden(self, viewer_token):
        # try to create a stock item
        r = requests.post(f"{API}/estoque", headers=self._hdr(viewer_token),
                          json={"codigo": "TEST_RC07", "nome": "TEST", "quantidade": 1})
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"

    def test_export_ativos_forbidden(self, viewer_token):
        r = requests.get(f"{API}/export/ativos", headers=self._hdr(viewer_token))
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"


# --------- Master regression ---------

class TestMasterRegression:
    def test_master_can_list_ativos(self, master_token):
        r = requests.get(f"{API}/ativos", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200

    def test_master_can_export_ativos(self, master_token):
        r = requests.get(f"{API}/export/ativos", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200
