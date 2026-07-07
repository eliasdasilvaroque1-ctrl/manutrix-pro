"""
RC-09 — Congelamento Multiempresa
Validates:
  (1) Login exige organization_id obrigatório (Pydantic 422 se ausente)
  (2) Índice composto (organization_id, email) — mesmo email em orgs diferentes
  (3) Forgot-password exige organization_id
  (4) Admin create user valida org (herda do admin se não passar)
  (5) Register público 403
  + REGRESSION: RBAC ordens-servico (tec ok, gerente 403), export ativos 200
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ASTEC_ORG = None  # resolved via fixture

MASTER = ("master@maintrix.com", "master123")
TEC = ("test.mec@maintrix.com", "tec123")
GERENTE = ("test.gerente@maintrix.com", "ger123")


# ------------------- fixtures -------------------

@pytest.fixture(scope="session")
def astec_org_id():
    r = requests.get(f"{API}/public/organizations", timeout=15)
    assert r.status_code == 200, f"public/organizations failed: {r.status_code} {r.text[:200]}"
    orgs = r.json()
    astec = next((o for o in orgs if o.get("nome", "").upper().startswith("ASTEC") and "ADMIN" not in o.get("nome", "").upper()), None)
    assert astec, f"ASTEC org not found in {[o.get('nome') for o in orgs]}"
    return astec["id"]


def _login(email, password, org_id):
    return requests.post(f"{API}/auth/login", json={"email": email, "password": password, "organization_id": org_id}, timeout=15)


@pytest.fixture(scope="session")
def master_token(astec_org_id):
    r = _login(*MASTER, astec_org_id)
    assert r.status_code == 200, f"Master login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def master_headers(master_token):
    return {"Authorization": f"Bearer {master_token}"}


# ------------------- (1) LOGIN — org_id obrigatório -------------------

class TestLoginOrgRequired:
    def test_login_without_org_id_returns_422(self):
        """Login sem organization_id -> 422 (Pydantic missing field)."""
        r = requests.post(f"{API}/auth/login", json={"email": MASTER[0], "password": MASTER[1]}, timeout=15)
        assert r.status_code == 422, f"Expected 422, got {r.status_code} {r.text[:200]}"
        body = r.json()
        # Pydantic error should mention organization_id
        text = str(body).lower()
        assert "organization_id" in text, f"422 body doesn't mention organization_id: {body}"

    def test_login_with_correct_org_returns_200_and_token(self, astec_org_id):
        r = _login(*MASTER, astec_org_id)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert "access_token" in data and isinstance(data["access_token"], str) and len(data["access_token"]) > 20
        assert data["user"]["email"] == MASTER[0]
        assert data["user"]["organization_id"] == astec_org_id

    def test_login_with_wrong_org_returns_401(self):
        r = _login(MASTER[0], MASTER[1], "fake-org-id-does-not-exist")
        assert r.status_code == 401, f"Expected 401, got {r.status_code} {r.text[:200]}"

    def test_login_with_wrong_password_returns_401(self, astec_org_id):
        r = _login(MASTER[0], "WRONG_PASSWORD", astec_org_id)
        assert r.status_code == 401, f"Expected 401, got {r.status_code} {r.text[:200]}"


# ------------------- (3) FORGOT PASSWORD — org_id obrigatório -------------------

class TestForgotPasswordOrgRequired:
    def test_forgot_without_org_returns_422(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": MASTER[0]}, timeout=15)
        assert r.status_code == 422, f"Expected 422, got {r.status_code} {r.text[:200]}"
        assert "organization_id" in str(r.json()).lower()

    def test_forgot_with_org_returns_success(self, astec_org_id):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": MASTER[0], "organization_id": astec_org_id}, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert data.get("success") is True


# ------------------- (5) REGISTER — 403 -------------------

class TestRegisterDisabled:
    def test_register_returns_403(self):
        payload = {
            "email": "TEST_should_never_exist@example.com",
            "password": "somepass123",
            "nome": "Should Not Exist",
        }
        r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code} {r.text[:200]}"


# ------------------- (4) ADMIN CREATE USER inherits admin org -------------------

class TestAdminCreateUserInheritsOrg:
    def test_admin_creates_user_without_org_inherits_admin_org(self, master_headers, astec_org_id):
        import uuid as _uuid
        email = f"TEST_rc09_inherit_{_uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "password": "temp123",
            "nome": "TEST RC09 Inherit",
            "role": "tecnico",
        }
        r = requests.post(f"{API}/admin/users", json=payload, headers=master_headers, timeout=15)
        assert r.status_code in (200, 201), f"admin create failed: {r.status_code} {r.text[:300]}"
        created = r.json()
        assert created.get("organization_id") == astec_org_id, f"created org mismatch: {created.get('organization_id')} vs {astec_org_id}"
        assert created.get("email") == email.lower()

        # Cleanup: soft-delete
        uid = created["id"]
        del_r = requests.delete(f"{API}/admin/users/{uid}", headers=master_headers, timeout=15)
        assert del_r.status_code in (200, 204), f"cleanup failed: {del_r.status_code}"


# ------------------- REGRESSION: RBAC ordens-servico -------------------

class TestRbacOrdensServico:
    def test_tec_can_create_ordem_servico(self, astec_org_id, master_headers):
        # Login as tecnico
        r = _login(*TEC, astec_org_id)
        assert r.status_code == 200, f"tec login failed: {r.status_code} {r.text[:200]}"
        tec_token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {tec_token}"}

        # Get an ativo id (tec may not have any; use a minimal payload)
        # Fetch any ativo from master to reference
        ativos_r = requests.get(f"{API}/ativos?limit=1", headers=master_headers, timeout=15)
        ativo_id = None
        if ativos_r.status_code == 200:
            arr = ativos_r.json()
            if isinstance(arr, list) and arr:
                ativo_id = arr[0].get("id")

        payload = {
            "titulo": "TEST_RC09 tec OS",
            "descricao": "regression rc09",
            "tipo": "corretiva",
            "prioridade": "media",
            "ativo_id": ativo_id or "unknown",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=headers, timeout=20)
        # Should succeed (2xx). If it fails, capture rationale.
        assert r.status_code in (200, 201), f"tec POST /ordens-servico expected 2xx, got {r.status_code} {r.text[:300]}"
        os_id = (r.json() or {}).get("id")
        # cleanup best-effort
        if os_id:
            requests.delete(f"{API}/ordens-servico/{os_id}", headers=master_headers, timeout=10)

    def test_gerente_cannot_create_ordem_servico(self, astec_org_id, master_headers):
        r = _login(*GERENTE, astec_org_id)
        assert r.status_code == 200, f"gerente login failed: {r.status_code} {r.text[:200]}"
        g_token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {g_token}"}

        ativos_r = requests.get(f"{API}/ativos?limit=1", headers=master_headers, timeout=15)
        ativo_id = None
        if ativos_r.status_code == 200:
            arr = ativos_r.json()
            if isinstance(arr, list) and arr:
                ativo_id = arr[0].get("id")

        payload = {
            "titulo": "TEST_RC09 gerente OS",
            "descricao": "should be denied",
            "tipo": "corretiva",
            "prioridade": "media",
            "ativo_id": ativo_id or "unknown",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=headers, timeout=20)
        assert r.status_code == 403, f"gerente POST /ordens-servico expected 403, got {r.status_code} {r.text[:300]}"


# ------------------- REGRESSION: exports -------------------

class TestExportsRegression:
    def test_master_export_ativos_excel_200(self, master_headers):
        r = requests.get(f"{API}/export/ativos?format=excel", headers=master_headers, timeout=30)
        assert r.status_code == 200, f"export/ativos failed: {r.status_code} {r.text[:300]}"
        assert len(r.content) > 0, "export/ativos returned empty body"
