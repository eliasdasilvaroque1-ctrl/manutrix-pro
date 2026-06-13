"""
Iteration 20 - QR Code integration regression tests
Tests:
- /api/ativos/tag/{tag} route ordering (must NOT be captured by /ativos/{ativo_id})
- /api/ativos/qr/{qr_code}
- get_ativo returns kpis + materiais auto-calculated
- materiais CRUD
- regression: kanban, dashboard, OS create, ativos list
"""

import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"no token in response: {data}"
    return token


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def seeded_ativo(headers):
    """Create a sector + ativo with known TAG for the QR/tag tests."""
    # ensure a sector
    sec_code = f"T20{uuid.uuid4().hex[:4].upper()}"
    sec_r = requests.post(f"{BASE_URL}/api/sectors",
                          json={"nome": "TEST20 Area QR", "codigo": sec_code},
                          headers=headers, timeout=15)
    assert sec_r.status_code in (200, 201), sec_r.text
    sector_id = sec_r.json()["id"]

    tag = f"TEST20-{uuid.uuid4().hex[:6].upper()}"
    a_r = requests.post(f"{BASE_URL}/api/ativos",
                        json={"sector_id": sector_id, "nome": "TEST20 Ativo QR",
                              "tipo_equipamento": "bomba", "tag": tag,
                              "fabricante": "ACME", "modelo": "X1"},
                        headers=headers, timeout=15)
    assert a_r.status_code in (200, 201), a_r.text
    ativo = a_r.json()
    return {"sector_id": sector_id, **ativo, "tag": tag.upper()}


# ---------- Route ordering: /api/ativos/tag/{tag} ----------
class TestRouteOrdering:
    def test_get_ativo_by_tag_works(self, headers, seeded_ativo):
        r = requests.get(f"{BASE_URL}/api/ativos/tag/{seeded_ativo['tag']}",
                         headers=headers, timeout=15)
        assert r.status_code == 200, f"tag route was likely shadowed by /{{ativo_id}}: {r.status_code} {r.text}"
        data = r.json()
        assert data["tag"] == seeded_ativo["tag"]
        assert data["id"] == seeded_ativo["id"]

    def test_get_ativo_by_tag_404(self, headers):
        r = requests.get(f"{BASE_URL}/api/ativos/tag/NOPE-XYZ-000",
                         headers=headers, timeout=15)
        assert r.status_code == 404

    def test_get_ativo_by_qr_works(self, headers, seeded_ativo):
        qr = seeded_ativo.get("qr_code")
        assert qr, "ativo missing qr_code"
        r = requests.get(f"{BASE_URL}/api/ativos/qr/{qr}", headers=headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["id"] == seeded_ativo["id"]


# ---------- KPIs + materiais auto on detail ----------
class TestAtivoDetailKPIs:
    def test_detail_has_kpis_object(self, headers, seeded_ativo):
        r = requests.get(f"{BASE_URL}/api/ativos/{seeded_ativo['id']}",
                         headers=headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "kpis" in data
        for k in ("mtbf_horas", "mttr_horas", "disponibilidade_percent", "total_os", "total_falhas"):
            assert k in data["kpis"], f"missing kpi {k}"
        assert isinstance(data["kpis"]["total_os"], int)
        # No falhas yet for brand new ativo
        assert data["kpis"]["total_falhas"] == 0
        # default disponibilidade is 100 when no corretivas
        assert data["kpis"]["disponibilidade_percent"] == 100

    def test_detail_has_materiais_array(self, headers, seeded_ativo):
        r = requests.get(f"{BASE_URL}/api/ativos/{seeded_ativo['id']}",
                         headers=headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "materiais" in data
        assert isinstance(data["materiais"], list)


# ---------- Materiais CRUD ----------
class TestMateriais:
    def test_create_list_delete_material(self, headers, seeded_ativo):
        ativo_id = seeded_ativo["id"]
        c = requests.post(f"{BASE_URL}/api/ativos/{ativo_id}/materiais",
                          json={"nome": "Rolamento 6205", "quantidade": 2},
                          headers=headers, timeout=15)
        assert c.status_code in (200, 201), c.text
        material = c.json()
        assert material["nome"] == "Rolamento 6205"
        mat_id = material.get("id")
        assert mat_id

        l = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}/materiais",
                         headers=headers, timeout=15)
        assert l.status_code == 200
        assert any(m["id"] == mat_id for m in l.json())

        d = requests.delete(f"{BASE_URL}/api/ativos/{ativo_id}/materiais/{mat_id}",
                            headers=headers, timeout=15)
        assert d.status_code in (200, 204)


# ---------- Regression ----------
class TestRegression:
    def test_dashboard_stats(self, headers):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers, timeout=15)
        assert r.status_code == 200

    def test_kanban_endpoint(self, headers):
        # kanban screen consumes /api/ordens-servico
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_ativos_list(self, headers):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_ativo_create_ignores_legacy_fields(self, headers, seeded_ativo):
        # Form must NOT require criticidade/status. POSTing them should be ignored.
        tag = f"TEST20R-{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(f"{BASE_URL}/api/ativos",
                          json={"sector_id": seeded_ativo["sector_id"],
                                "nome": "TEST20 Regression",
                                "tipo_equipamento": "motor",
                                "tag": tag,
                                "criticidade": "alta",  # legacy
                                "status": "operacional"},  # legacy
                          headers=headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        # legacy fields should be absent (silently dropped) or harmless
        assert body["tag"] == tag.upper()


# ---------- Cleanup ----------
class TestZZZCleanup:
    def test_cleanup(self, headers, seeded_ativo):
        # soft delete the ativo
        requests.delete(f"{BASE_URL}/api/ativos/{seeded_ativo['id']}",
                        headers=headers, timeout=15)
