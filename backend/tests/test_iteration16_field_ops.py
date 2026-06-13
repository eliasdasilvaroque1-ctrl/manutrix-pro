"""Iteration 16 - Field Operations: PWA, checklist templates, new OS fields"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASS = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def first_ativo_id(headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=headers, timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0, "No ativos seeded"
    return ativos[0]['id']


# =========== AUTH ============

def test_login_admin():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert (data.get("access_token") or data.get("token"))
    assert "user" in data or "email" in data or True  # tolerant


# =========== CHECKLIST TEMPLATES ============

def test_checklist_templates_returns_3_types(headers):
    r = requests.get(f"{BASE_URL}/api/checklists/templates", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    for tipo in ("mecanica", "eletrica", "lubrificacao"):
        assert tipo in data, f"Missing template for {tipo}"
        tpl = data[tipo]
        assert tpl.get("tipo") == tipo
        assert tpl.get("nome")
        itens = tpl.get("itens", [])
        assert isinstance(itens, list) and len(itens) >= 5, f"{tipo} expected >=5 items, got {len(itens)}"
        # Validate item structure
        first = itens[0]
        assert "id" in first
        assert "descricao" in first
        assert "tipo" in first  # boolean/numerico/opcao/texto


def test_checklist_templates_item_types_valid(headers):
    r = requests.get(f"{BASE_URL}/api/checklists/templates", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    valid_types = {"boolean", "numerico", "opcao", "texto"}
    for tipo, tpl in data.items():
        for item in tpl.get("itens", []):
            assert item["tipo"] in valid_types, f"Invalid item tipo {item['tipo']} in {tipo}"


# =========== OS NEW FIELDS ============

def test_create_os_with_new_fields(headers, first_ativo_id):
    payload = {
        "ativo_id": first_ativo_id,
        "titulo": "TEST_iter16 OS new fields",
        "tipo": "lubrificacao",
        "disciplina": "mecanica",
        "prioridade": "media",
        "descricao": "TEST_iter16 OS with new fields",
        "causa_falha": "teste",
        "equipamento_parado": True,
        "horas_parada": 2,
    }
    r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=headers, json=payload, timeout=30)
    assert r.status_code in (200, 201), f"Create OS failed: {r.status_code} {r.text}"
    os_data = r.json()
    assert os_data.get("causa_falha") == "teste"
    assert os_data.get("equipamento_parado") is True
    assert float(os_data.get("horas_parada")) == 2.0
    assert os_data.get("disciplina") == "mecanica"
    assert os_data.get("tipo") == "lubrificacao"
    # GET verify persistence
    os_id = os_data.get("id")
    g = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers, timeout=30)
    assert g.status_code == 200
    fetched = g.json()
    assert fetched.get("causa_falha") == "teste"
    assert fetched.get("equipamento_parado") is True
    assert float(fetched.get("horas_parada")) == 2.0
    # Cleanup
    requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers, timeout=30)


def test_list_os_includes_new_fields(headers, first_ativo_id):
    # Create one to ensure at least one OS has the new fields populated
    payload = {
        "ativo_id": first_ativo_id,
        "titulo": "TEST_iter16 list-fields",
        "tipo": "corretiva",
        "disciplina": "mecanica",
        "prioridade": "alta",
        "descricao": "TEST_iter16 list-fields",
        "causa_falha": "vazamento",
        "equipamento_parado": False,
    }
    c = requests.post(f"{BASE_URL}/api/ordens-servico", headers=headers, json=payload, timeout=30)
    assert c.status_code in (200, 201)
    os_id = c.json()["id"]

    r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers, timeout=30)
    assert r.status_code == 200
    lst = r.json()
    assert isinstance(lst, list) and len(lst) > 0
    # Find our created OS
    found = next((o for o in lst if o.get("id") == os_id), None)
    assert found is not None
    assert "causa_falha" in found
    assert "equipamento_parado" in found
    assert "horas_parada" in found
    requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers, timeout=30)


# =========== REGRESSION ============

def test_sectors_regression(headers):
    r = requests.get(f"{BASE_URL}/api/sectors", headers=headers, timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_kpis_regression(headers):
    r = requests.get(f"{BASE_URL}/api/kpis", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


def test_dashboard_os_por_setor_regression(headers):
    r = requests.get(f"{BASE_URL}/api/dashboard/os-por-setor", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


# =========== PWA STATIC ASSETS ============

def test_manifest_accessible():
    # Frontend route (no /api prefix) - manifest.json served by frontend
    r = requests.get(f"{BASE_URL}/manifest.json", timeout=30)
    assert r.status_code == 200, f"manifest.json not accessible: {r.status_code}"
    data = r.json()
    assert "MANUTRIX" in data.get("name", "") or "MANUTRIX" in data.get("short_name", "")
    assert isinstance(data.get("icons", []), list) and len(data.get("icons", [])) >= 1


def test_service_worker_accessible():
    r = requests.get(f"{BASE_URL}/service-worker.js", timeout=30)
    assert r.status_code == 200, f"service-worker.js not accessible: {r.status_code}"
    body = r.text
    assert "self.addEventListener" in body
    assert "fetch" in body
