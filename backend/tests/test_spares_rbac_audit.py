"""
Tests for Sobressalentes (Spares) module:
- Admin can create / update / delete
- Tecnico is forbidden from write
- Audit log records update + delete actions
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
TECNICO = {"email": "tecnico@manutrix.com", "password": "tecnico123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def tecnico_token():
    return _login(TECNICO)


@pytest.fixture(scope="module")
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def tec_h(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}"}


# ---------- Admin CRUD ----------
class TestAdminSparesCRUD:
    spare_id = None

    def test_admin_create_spare(self, admin_h):
        payload = {
            "descricao": "TEST_SPARE_iter27_rolamento",
            "fabricante": "SKF",
            "modelo": "6205-2RS",
            "localizacao": "Almox A1",
            "status": "estoque",
            "custo": 49.90,
        }
        r = requests.post(f"{API}/sobressalentes", json=payload, headers=admin_h, timeout=15)
        assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("descricao") == payload["descricao"]
        assert "id" in body
        TestAdminSparesCRUD.spare_id = body["id"]

    def test_admin_list_includes_created(self, admin_h):
        assert TestAdminSparesCRUD.spare_id, "previous test must create spare"
        r = requests.get(f"{API}/sobressalentes", headers=admin_h, timeout=15)
        assert r.status_code == 200
        ids = [s.get("id") for s in r.json()]
        assert TestAdminSparesCRUD.spare_id in ids

    def test_admin_update_spare(self, admin_h):
        sid = TestAdminSparesCRUD.spare_id
        assert sid
        payload = {
            "descricao": "TEST_SPARE_iter27_rolamento_UPDATED",
            "fabricante": "SKF",
            "modelo": "6205-2RS",
            "localizacao": "Almox A1",
            "status": "estoque",
            "custo": 59.90,
        }
        r = requests.put(f"{API}/sobressalentes/{sid}", json=payload, headers=admin_h, timeout=15)
        assert r.status_code == 200, f"update failed: {r.status_code} {r.text}"
        # Verify via GET (list and find)
        r2 = requests.get(f"{API}/sobressalentes", headers=admin_h, timeout=15)
        match = next((s for s in r2.json() if s.get("id") == sid), None)
        assert match, "spare missing after update"
        assert match["descricao"] == payload["descricao"]

    def test_admin_delete_spare(self, admin_h):
        sid = TestAdminSparesCRUD.spare_id
        assert sid
        r = requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)
        assert r.status_code in (200, 204), f"delete failed: {r.status_code} {r.text}"
        # Verify deletion
        r2 = requests.get(f"{API}/sobressalentes", headers=admin_h, timeout=15)
        ids = [s.get("id") for s in r2.json()]
        assert sid not in ids, "spare still present after delete"


# ---------- RBAC: Tecnico read-only ----------
class TestTecnicoRBAC:
    def test_tecnico_can_list(self, tec_h):
        r = requests.get(f"{API}/sobressalentes", headers=tec_h, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_tecnico_cannot_create(self, tec_h):
        payload = {"descricao": "TEST_TEC_should_fail", "status": "estoque"}
        r = requests.post(f"{API}/sobressalentes", json=payload, headers=tec_h, timeout=15)
        assert r.status_code in (401, 403), f"tecnico create not blocked: {r.status_code} {r.text}"

    def test_tecnico_cannot_update(self, admin_h, tec_h):
        # Create with admin
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_admin_for_rbac", "status": "estoque"}, headers=admin_h, timeout=15)
        sid = c.json().get("id")
        try:
            r = requests.put(f"{API}/sobressalentes/{sid}", json={"descricao": "hack", "status": "estoque"}, headers=tec_h, timeout=15)
            assert r.status_code in (401, 403), f"tecnico update not blocked: {r.status_code}"
        finally:
            requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)

    def test_tecnico_cannot_delete(self, admin_h, tec_h):
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_admin_for_rbac_del", "status": "estoque"}, headers=admin_h, timeout=15)
        sid = c.json().get("id")
        try:
            r = requests.delete(f"{API}/sobressalentes/{sid}", headers=tec_h, timeout=15)
            assert r.status_code in (401, 403), f"tecnico delete not blocked: {r.status_code}"
        finally:
            requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)


# ---------- Audit Log ----------
class TestAuditLogs:
    def test_audit_log_update_and_delete(self, admin_h):
        # Create
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_AUDIT_iter27", "status": "estoque"}, headers=admin_h, timeout=15)
        assert c.status_code in (200, 201), c.text
        sid = c.json().get("id")
        assert sid

        # Update
        u = requests.put(f"{API}/sobressalentes/{sid}", json={"descricao": "TEST_AUDIT_iter27_upd", "status": "estoque"}, headers=admin_h, timeout=15)
        assert u.status_code == 200, u.text

        # Delete
        d = requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)
        assert d.status_code in (200, 204), d.text

        time.sleep(1.0)  # give writes a moment

        # Fetch audit logs
        r = requests.get(f"{API}/admin/audit-logs", headers=admin_h, timeout=15, params={"limit": 200})
        assert r.status_code == 200, f"audit-logs fetch failed: {r.status_code} {r.text}"
        logs = r.json()
        if isinstance(logs, dict):
            logs = logs.get("items") or logs.get("data") or logs.get("logs") or []

        # filter for this entity_type and entity id
        spare_logs = [l for l in logs if (l.get("entity_type") in ("sobressalentes", "sobressalente"))]
        # Match by entity_id when available
        update_logs = [l for l in spare_logs if l.get("action") in ("update", "updated") and (l.get("entity_id") == sid or str(l.get("entity_id")) == str(sid))]
        delete_logs = [l for l in spare_logs if l.get("action") in ("delete", "deleted") and (l.get("entity_id") == sid or str(l.get("entity_id")) == str(sid))]

        assert update_logs, f"No update audit log for spare {sid}. Sample: {spare_logs[:3]}"
        assert delete_logs, f"No delete audit log for spare {sid}. Sample: {spare_logs[:3]}"
