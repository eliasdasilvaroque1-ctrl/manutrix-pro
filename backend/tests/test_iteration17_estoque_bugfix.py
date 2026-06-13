"""
Iteration 17 - Critical bug fix tests for Estoque (Inventory) creation.

Bug Context:
  (1) Backend was returning 500 on POST /api/estoque because EstoqueCreate
      model was missing `estoque_maximo` and `posicao` fields referenced in server.py
  (2) Frontend crashed with "Objects are not valid as a React child" because
      toast.error(error.response.data.detail) received a Pydantic 422 validation
      array of objects. Fixed by normalizeError() helper.

Tests cover:
  - POST /api/estoque happy path -> 200 with id+sku
  - POST /api/estoque empty body -> 422 with detail array
  - Regression: login, dashboard, OS list, checklist templates
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.skip(f"No token in login response: {data}")
    return token


@pytest.fixture(scope="module")
def api(auth_token):
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    })
    return s


# --------- Estoque BUGFIX tests ---------

class TestEstoqueCreate:
    """The P0 fix: estoque creation must work and 422 must return array of validation messages."""

    created_ids = []

    def test_create_estoque_happy_path(self, api):
        payload = {
            "nome": "TEST_BugFix Item",
            "categoria": "rolamento",
            "quantidade": 5,
            "estoque_minimo": 2,
            "custo_unitario": 10,
        }
        r = api.post(f"{BASE_URL}/api/estoque", json=payload, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert "id" in body, f"missing id in response: {body}"
        assert "sku" in body and body["sku"], f"missing/empty sku: {body}"
        assert body.get("nome") == payload["nome"]
        assert body.get("categoria") == payload["categoria"]
        assert float(body.get("quantidade", -1)) == 5.0
        assert float(body.get("estoque_minimo", -1)) == 2.0
        assert float(body.get("custo_unitario", -1)) == 10.0
        TestEstoqueCreate.created_ids.append(body["id"])

    def test_create_estoque_with_optional_fields(self, api):
        """Verify estoque_maximo and posicao (the previously missing fields) are accepted."""
        payload = {
            "nome": f"TEST_OptFields_{uuid.uuid4().hex[:6]}",
            "categoria": "mecanico",
            "quantidade": 1,
            "estoque_minimo": 0,
            "estoque_maximo": 10,
            "posicao": "A1-B2",
            "custo_unitario": 25.5,
        }
        r = api.post(f"{BASE_URL}/api/estoque", json=payload, timeout=30)
        assert r.status_code == 200, f"Optional fields rejected: {r.status_code} {r.text}"
        body = r.json()
        # Accept regardless of whether server echoes them back, but must not 500
        TestEstoqueCreate.created_ids.append(body["id"])

    def test_create_estoque_empty_body_returns_422_array(self, api):
        r = api.post(f"{BASE_URL}/api/estoque", json={}, timeout=30)
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
        body = r.json()
        assert "detail" in body, f"422 response missing detail: {body}"
        detail = body["detail"]
        assert isinstance(detail, list), f"detail must be a list of validation errors, got {type(detail)}"
        assert len(detail) > 0, "422 detail should not be empty"
        # Each item should be a dict with msg (Pydantic style)
        first = detail[0]
        assert isinstance(first, dict), f"detail[0] not a dict: {first}"
        assert "msg" in first or "loc" in first, f"unexpected validation item shape: {first}"

    def test_get_created_estoque_persisted(self, api):
        if not TestEstoqueCreate.created_ids:
            pytest.skip("No created estoque to verify")
        eid = TestEstoqueCreate.created_ids[0]
        r = api.get(f"{BASE_URL}/api/estoque/{eid}", timeout=30)
        # Some APIs only expose list endpoint - accept 200 from list endpoint
        if r.status_code == 404:
            r2 = api.get(f"{BASE_URL}/api/estoque", timeout=30)
            assert r2.status_code == 200
            items = r2.json()
            assert any(i.get("id") == eid for i in items), "Created item not in list"
        else:
            assert r.status_code == 200, f"GET estoque/{eid}: {r.status_code}"

    def teardown_class(cls):
        # best-effort cleanup
        try:
            r = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=15,
            )
            if r.status_code != 200:
                return
            token = r.json().get("access_token") or r.json().get("token")
            if not token:
                return
            h = {"Authorization": f"Bearer {token}"}
            for eid in cls.created_ids:
                requests.delete(f"{BASE_URL}/api/estoque/{eid}", headers=h, timeout=15)
        except Exception:
            pass


# --------- Regression ---------

class TestRegression:

    def test_login_works(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("access_token") or data.get("token")

    def test_dashboard_loads(self, api):
        r = api.get(f"{BASE_URL}/api/dashboard/stats", timeout=30)
        assert r.status_code == 200, f"dashboard/stats: {r.status_code} {r.text[:300]}"

    def test_os_list(self, api):
        r = api.get(f"{BASE_URL}/api/ordens-servico", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_checklists_templates_3(self, api):
        r = api.get(f"{BASE_URL}/api/checklists/templates", timeout=30)
        assert r.status_code == 200
        data = r.json()
        # Accept dict or list - count >= 3 templates
        if isinstance(data, dict):
            assert len(data.keys()) >= 3, f"expected >=3 templates, got {list(data.keys())}"
        else:
            assert isinstance(data, list) and len(data) >= 3, f"expected >=3 templates, got {data}"

    def test_inspecoes_list(self, api):
        r = api.get(f"{BASE_URL}/api/inspecoes", timeout=30)
        assert r.status_code == 200
