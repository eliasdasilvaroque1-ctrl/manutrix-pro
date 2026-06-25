"""
Iteration 43 - MANUTRIX Phase 1 Block A
Tests:
  - RBAC hierarchy (master > admin > tecnico)
  - Plantas CRUD
  - Master cleanup endpoints
  - admin_actions audit log
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")

CREDS = {
    "master": {"email": "master@manutrix.com", "password": "master123"},
    "admin": {"email": "admin@manutrix.com", "password": "admin123"},
    "tecnico": {"email": "tecnico@manutrix.com", "password": "tecnico123"},
}


def _login(role):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=CREDS[role], timeout=20)
    assert r.status_code == 200, f"{role} login failed: {r.text}"
    return r.json()


@pytest.fixture(scope="session")
def tokens():
    return {role: _login(role)["access_token"] for role in CREDS}


@pytest.fixture(scope="session")
def users():
    return {role: _login(role)["user"] for role in CREDS}


def _hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- AUTH / ROLES ----------

class TestAuthRoles:
    def test_master_login_role(self, users):
        assert users["master"]["role"] == "master"
        assert users["master"]["email"] == "master@manutrix.com"

    def test_admin_login_role(self, users):
        assert users["admin"]["role"] == "admin"

    def test_tecnico_login_role(self, users):
        assert users["tecnico"]["role"] == "tecnico"


# ---------- MASTER CLEANUP RBAC ----------

class TestMasterEndpointsRBAC:
    def test_master_cleanup_allowed_for_master(self, tokens):
        r = requests.post(f"{BASE_URL}/api/master/cleanup",
                          headers=_hdr(tokens["master"]),
                          params=[("targets", "notificacoes")], timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("success") is True
        assert "deleted" in body

    def test_master_cleanup_denied_for_admin(self, tokens):
        r = requests.post(f"{BASE_URL}/api/master/cleanup",
                          headers=_hdr(tokens["admin"]),
                          params=[("targets", "notificacoes")], timeout=20)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

    def test_master_cleanup_denied_for_tecnico(self, tokens):
        r = requests.post(f"{BASE_URL}/api/master/cleanup",
                          headers=_hdr(tokens["tecnico"]),
                          params=[("targets", "notificacoes")], timeout=20)
        assert r.status_code == 403

    def test_prepare_production_denied_for_admin(self, tokens):
        r = requests.post(f"{BASE_URL}/api/master/prepare-production",
                          headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 403

    def test_prepare_production_denied_for_tecnico(self, tokens):
        r = requests.post(f"{BASE_URL}/api/master/prepare-production",
                          headers=_hdr(tokens["tecnico"]), timeout=20)
        assert r.status_code == 403

    def test_admin_actions_only_master(self, tokens):
        # master allowed
        r = requests.get(f"{BASE_URL}/api/master/admin-actions",
                         headers=_hdr(tokens["master"]), timeout=20)
        assert r.status_code == 200
        actions = r.json()
        assert isinstance(actions, list)
        # admin denied
        r2 = requests.get(f"{BASE_URL}/api/master/admin-actions",
                          headers=_hdr(tokens["admin"]), timeout=20)
        assert r2.status_code == 403


# ---------- PLANTAS CRUD ----------

class TestPlantasCRUD:
    created_ids = []

    def test_list_plantas_anyone(self, tokens):
        for role in ("master", "admin", "tecnico"):
            r = requests.get(f"{BASE_URL}/api/plantas", headers=_hdr(tokens[role]), timeout=20)
            assert r.status_code == 200, f"{role}: {r.text}"
            assert isinstance(r.json(), list)

    def test_tecnico_cannot_create_planta(self, tokens):
        payload = {"nome": "TEST_PlantaTec_" + uuid.uuid4().hex[:6], "codigo": "TPT" + uuid.uuid4().hex[:4]}
        r = requests.post(f"{BASE_URL}/api/plantas", json=payload,
                          headers=_hdr(tokens["tecnico"]), timeout=20)
        assert r.status_code == 403, r.text

    def test_admin_can_create_planta(self, tokens):
        payload = {
            "nome": "TEST_PlantaAdm_" + uuid.uuid4().hex[:6],
            "codigo": "TPA" + uuid.uuid4().hex[:4],
            "endereco": "Rua Teste, 100",
        }
        r = requests.post(f"{BASE_URL}/api/plantas", json=payload,
                          headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["nome"] == payload["nome"]
        assert body["codigo"] == payload["codigo"]
        assert "id" in body
        TestPlantasCRUD.created_ids.append(body["id"])

    def test_master_can_create_planta(self, tokens):
        payload = {
            "nome": "TEST_PlantaMst_" + uuid.uuid4().hex[:6],
            "codigo": "TPM" + uuid.uuid4().hex[:4],
        }
        r = requests.post(f"{BASE_URL}/api/plantas", json=payload,
                          headers=_hdr(tokens["master"]), timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["nome"] == payload["nome"]
        TestPlantasCRUD.created_ids.append(body["id"])

        # GET verification
        list_r = requests.get(f"{BASE_URL}/api/plantas", headers=_hdr(tokens["master"]), timeout=20)
        ids = [p["id"] for p in list_r.json()]
        assert body["id"] in ids

    def test_update_planta(self, tokens):
        if not TestPlantasCRUD.created_ids:
            pytest.skip("no planta created")
        pid = TestPlantasCRUD.created_ids[0]
        new_name = "TEST_Updated_" + uuid.uuid4().hex[:6]
        r = requests.put(f"{BASE_URL}/api/plantas/{pid}",
                         json={"nome": new_name},
                         headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["nome"] == new_name

    def test_delete_planta_soft(self, tokens):
        if not TestPlantasCRUD.created_ids:
            pytest.skip()
        for pid in TestPlantasCRUD.created_ids:
            r = requests.delete(f"{BASE_URL}/api/plantas/{pid}",
                                headers=_hdr(tokens["admin"]), timeout=20)
            assert r.status_code == 200, r.text
            assert r.json().get("success") is True

        # verify removed from list
        list_r = requests.get(f"{BASE_URL}/api/plantas", headers=_hdr(tokens["admin"]), timeout=20)
        ids = [p["id"] for p in list_r.json()]
        for pid in TestPlantasCRUD.created_ids:
            assert pid not in ids, f"Soft-deleted planta {pid} still listed"


# ---------- REGRESSION ----------

class TestRegression:
    def test_dashboard(self, tokens):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats",
                         headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200

    def test_ordens_servico(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ordens-servico",
                         headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_ativos(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ativos",
                         headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200

    def test_inspecoes(self, tokens):
        r = requests.get(f"{BASE_URL}/api/inspecoes",
                         headers=_hdr(tokens["admin"]), timeout=20)
        assert r.status_code == 200


# ---------- AUDIT VERIFICATION ----------

class TestAuditAdminActions:
    def test_cleanup_logged_in_admin_actions(self, tokens):
        # Issue a cleanup as master, then verify it shows up
        marker_target = "notificacoes"
        r = requests.post(f"{BASE_URL}/api/master/cleanup",
                          headers=_hdr(tokens["master"]),
                          params=[("targets", marker_target)], timeout=20)
        assert r.status_code == 200

        r2 = requests.get(f"{BASE_URL}/api/master/admin-actions",
                          headers=_hdr(tokens["master"]), timeout=20)
        assert r2.status_code == 200
        actions = r2.json()
        assert len(actions) > 0, "admin_actions should have at least one entry"
        assert any(a.get("action") == "cleanup" and marker_target in a.get("targets", [])
                   for a in actions), "cleanup action with target not found"
