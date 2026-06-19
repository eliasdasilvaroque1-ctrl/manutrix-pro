"""
Iteration 36 - MANUTRIX Sobressalentes Avançado (Bloco A)
- Tests origem + condicoes + quantidade_total on POST/PUT/GET /api/sobressalentes
- Tests POST/GET/DELETE /api/sobressalentes/{id}/reformas
- Tests reformas array + reformas_count on GET /api/sobressalentes/{id}
- Tests audit log records spare_reforma create/delete
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "admin@manutrix.com", "password": "admin123"},
                      timeout=20)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("token") or data.get("access_token")
    assert token, "no token in login response"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def created_spare_id(admin_headers):
    """Create a spare with condicoes + origem and return its id. Cleanup at end."""
    payload = {
        "nome": "TEST_iter36_spare",
        "descricao": "TEST iteration 36 spare advanced",
        "modelo": "MDL-36",
        "fabricante": "TEST_FAB",
        "status": "disponivel",
        "origem": "compra_nova",
        "condicoes": {"novo": 2, "reformado": 1, "em_reforma": 0, "reservado": 0, "instalado": 0, "descartado": 0},
    }
    r = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers, timeout=15)
    assert r.status_code in (200, 201), f"create spare failed: {r.status_code} {r.text}"
    data = r.json()
    sid = data.get("id")
    assert sid
    yield sid
    # cleanup
    try:
        requests.delete(f"{BASE_URL}/api/sobressalentes/{sid}", headers=admin_headers, timeout=10)
    except Exception:
        pass


# ---------- A. CRUD with origem/condicoes/quantidade_total ----------

class TestSpareCondicoesOrigem:
    def test_create_returns_origem_condicoes_total(self, admin_headers):
        payload = {
            "nome": "TEST_iter36_create",
            "descricao": "Create+verify spare",
            "origem": "reforma_externa",
            "condicoes": {"novo": 3, "reformado": 2, "em_reforma": 1, "reservado": 0, "instalado": 0, "descartado": 0},
        }
        r = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        assert d.get("origem") == "reforma_externa"
        assert isinstance(d.get("condicoes"), dict)
        assert d["condicoes"].get("novo") == 3
        assert d["condicoes"].get("reformado") == 2
        assert d.get("quantidade_total") == 6, f"expected sum=6 got {d.get('quantidade_total')}"
        sid = d["id"]
        # cleanup
        requests.delete(f"{BASE_URL}/api/sobressalentes/{sid}", headers=admin_headers, timeout=10)

    def test_get_list_includes_fields(self, admin_headers, created_spare_id):
        r = requests.get(f"{BASE_URL}/api/sobressalentes", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        items = r.json()
        match = [x for x in items if x.get("id") == created_spare_id]
        assert match, "created spare not in list"
        sp = match[0]
        assert "origem" in sp
        assert "condicoes" in sp
        assert "quantidade_total" in sp
        assert sp["quantidade_total"] == 3  # novo:2+reformado:1

    def test_get_single_includes_reformas_array(self, admin_headers, created_spare_id):
        r = requests.get(f"{BASE_URL}/api/sobressalentes/{created_spare_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "reformas" in d, "missing reformas array on GET single"
        assert isinstance(d["reformas"], list)

    def test_put_recalculates_quantidade_total(self, admin_headers, created_spare_id):
        new_cond = {"novo": 5, "reformado": 3, "em_reforma": 2, "reservado": 1, "instalado": 0, "descartado": 0}
        r = requests.put(f"{BASE_URL}/api/sobressalentes/{created_spare_id}",
                         json={"condicoes": new_cond, "origem": "transferencia"},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("quantidade_total") == 11, f"expected 11 got {d.get('quantidade_total')}"
        assert d.get("origem") == "transferencia"
        # Verify via GET persistence
        r2 = requests.get(f"{BASE_URL}/api/sobressalentes/{created_spare_id}", headers=admin_headers, timeout=15)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["condicoes"]["novo"] == 5
        assert d2["quantidade_total"] == 11


# ---------- B. Reformas endpoints ----------

class TestSpareReformas:
    reforma_id = None

    def test_create_reforma(self, admin_headers, created_spare_id):
        body = {
            "empresa_reparadora": "TEST_Empresa_Reparadora_LTDA",
            "data_envio": "2026-01-05",
            "data_retorno": "2026-01-20",
            "observacao": "TEST_iter36 reforma observacao",
            "valor": 1500.50,
        }
        r = requests.post(f"{BASE_URL}/api/sobressalentes/{created_spare_id}/reformas",
                          json=body, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        assert d.get("empresa_reparadora") == "TEST_Empresa_Reparadora_LTDA"
        assert d.get("valor") == 1500.50
        assert d.get("spare_id") == created_spare_id
        assert "id" in d
        TestSpareReformas.reforma_id = d["id"]

    def test_list_reformas_sorted_desc(self, admin_headers, created_spare_id):
        # Add a 2nd reforma so we can verify sort
        body2 = {"empresa_reparadora": "TEST_Empresa_2", "data_envio": "2026-01-15", "valor": 200}
        r2 = requests.post(f"{BASE_URL}/api/sobressalentes/{created_spare_id}/reformas",
                           json=body2, headers=admin_headers, timeout=15)
        assert r2.status_code in (200, 201)

        r = requests.get(f"{BASE_URL}/api/sobressalentes/{created_spare_id}/reformas",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 2
        # sorted by created_at desc
        cas = [x.get("created_at", "") for x in items]
        assert cas == sorted(cas, reverse=True), "reformas not sorted desc by created_at"

    def test_single_spare_includes_reformas(self, admin_headers, created_spare_id):
        r = requests.get(f"{BASE_URL}/api/sobressalentes/{created_spare_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("reformas"), list)
        assert len(d["reformas"]) >= 2

    def test_delete_reforma_soft_deletes(self, admin_headers, created_spare_id):
        rid = TestSpareReformas.reforma_id
        assert rid, "no reforma to delete"
        r = requests.delete(f"{BASE_URL}/api/sobressalentes/{created_spare_id}/reformas/{rid}",
                            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        # verify it no longer appears in list
        r2 = requests.get(f"{BASE_URL}/api/sobressalentes/{created_spare_id}/reformas",
                          headers=admin_headers, timeout=15)
        assert r2.status_code == 200
        items = r2.json()
        ids = [x.get("id") for x in items]
        assert rid not in ids, "soft-deleted reforma still appears in list"

    def test_audit_log_records_reforma_actions(self, admin_headers, created_spare_id):
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs?entity_type=spare_reforma&limit=50",
                         headers=admin_headers, timeout=15)
        if r.status_code == 404:
            pytest.skip("audit-logs endpoint not available")
        assert r.status_code == 200, r.text
        logs = r.json()
        # accept list or dict containers
        if isinstance(logs, dict):
            logs = logs.get("items") or logs.get("logs") or []
        actions = [(l.get("action"), l.get("entity_type")) for l in logs]
        assert ("create", "spare_reforma") in actions, f"no create audit log for spare_reforma. sample: {actions[:5]}"
        assert ("delete", "spare_reforma") in actions, f"no delete audit log for spare_reforma. sample: {actions[:5]}"
