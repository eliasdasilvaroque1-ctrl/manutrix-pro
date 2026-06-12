"""Iteration 15 - Plants removed, Sectors top-level, OS disciplina + 6 new tipos"""
import os
import pytest
import requests
import uuid

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


# ============ Sectors / Plants ============

def test_sectors_no_plant_id(headers):
    r = requests.get(f"{BASE_URL}/api/sectors", headers=headers, timeout=30)
    assert r.status_code == 200
    sectors = r.json()
    assert isinstance(sectors, list)
    assert len(sectors) > 0, "Expected seeded sectors"
    for s in sectors:
        assert 'plant_id' not in s, f"Sector still has plant_id: {s}"
        assert 'id' in s and 'nome' in s and 'codigo' in s


def test_ativos_no_plant_id_has_sector(headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=headers, timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert isinstance(ativos, list)
    for a in ativos:
        assert 'plant_id' not in a, f"Ativo still has plant_id: {a.get('tag')}"
        assert 'sector_id' in a, f"Ativo missing sector_id: {a.get('tag')}"


def test_plantas_endpoint_removed(headers):
    """Legacy /api/plantas should not exist (or return 404/405)"""
    r = requests.get(f"{BASE_URL}/api/plantas", headers=headers, timeout=30)
    assert r.status_code in (404, 405), f"Plants endpoint still exists: {r.status_code}"


# ============ Migration report ============

def test_migration_report(headers):
    r = requests.get(f"{BASE_URL}/api/migration/report", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("hierarchy") == "Sector -> Asset (no Plants)"
    assert data.get("status") == "complete"
    assert "summary" in data
    assert data["summary"]["ativos_orphan"] == 0


# ============ Dashboard endpoints ============

def test_dashboard_os_por_setor(headers):
    r = requests.get(f"{BASE_URL}/api/dashboard/os-por-setor", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "sector" in data[0]
        assert "os_abertas" in data[0]


def test_dashboard_os_por_disciplina(headers):
    r = requests.get(f"{BASE_URL}/api/dashboard/os-por-disciplina", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5, f"Expected 5 disciplines, got {len(data)}"
    keys = {d["key"] for d in data}
    assert keys == {"mecanica", "eletrica", "instrumentacao", "civil", "producao"}


def test_dashboard_ativos_mais_falhas(headers):
    r = requests.get(f"{BASE_URL}/api/dashboard/ativos-mais-falhas", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        assert "tag" in item and "falhas" in item


def test_kpis_with_sector_filter(headers):
    # Pick first sector
    s = requests.get(f"{BASE_URL}/api/sectors", headers=headers).json()
    if s:
        sid = s[0]['id']
        r = requests.get(f"{BASE_URL}/api/kpis?sector_id={sid}", headers=headers, timeout=30)
        assert r.status_code == 200
        kpis = r.json()
        assert "ativos_total" in kpis


# ============ Sector creation ============

def test_create_sector_and_verify(headers):
    code = f"TBRT{uuid.uuid4().hex[:4].upper()}"
    payload = {"codigo": code, "nome": "TEST_Britagem Primária", "cor": "#10b981"}
    r = requests.post(f"{BASE_URL}/api/sectors", json=payload, headers=headers, timeout=30)
    assert r.status_code == 200, f"Failed create: {r.status_code} {r.text}"
    sec = r.json()
    assert sec['codigo'] == code.upper()
    assert sec['nome'] == "TEST_Britagem Primária"
    sid = sec['id']

    # toggle
    rt = requests.patch(f"{BASE_URL}/api/sectors/{sid}/toggle", headers=headers, timeout=30)
    assert rt.status_code == 200
    assert "is_active" in rt.json()

    # cleanup
    requests.delete(f"{BASE_URL}/api/sectors/{sid}", headers=headers, timeout=30)


# ============ OS creation - disciplina + new tipos ============

def test_create_os_with_disciplina_and_lubrificacao(headers):
    ativos = requests.get(f"{BASE_URL}/api/ativos", headers=headers).json()
    if not ativos:
        pytest.skip("No ativos available")
    ativo_id = ativos[0]['id']

    payload = {
        "ativo_id": ativo_id,
        "tipo": "lubrificacao",
        "disciplina": "mecanica",
        "prioridade": "media",
        "titulo": "TEST_OS Lubrificação"
    }
    r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    os_obj = r.json()
    assert os_obj['tipo'] == 'lubrificacao'
    assert os_obj['disciplina'] == 'mecanica'
    os_id = os_obj['id']

    # GET verify persistence
    rg = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers).json()
    assert rg['disciplina'] == 'mecanica'
    assert rg['tipo'] == 'lubrificacao'

    # Kanban status update
    rp = requests.patch(f"{BASE_URL}/api/ordens-servico/{os_id}/status",
                       json={"new_status": "planejada"}, headers=headers, timeout=30)
    assert rp.status_code == 200, f"{rp.status_code} {rp.text}"
    assert rp.json()['new_status'] == 'planejada'

    # cleanup
    requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers)


def test_create_os_missing_disciplina_rejected(headers):
    ativos = requests.get(f"{BASE_URL}/api/ativos", headers=headers).json()
    if not ativos:
        pytest.skip("No ativos available")
    payload = {
        "ativo_id": ativos[0]['id'],
        "tipo": "corretiva",
        "prioridade": "media",
        "titulo": "TEST_no_disciplina"
    }
    r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=headers, timeout=30)
    assert r.status_code == 422, f"Expected 422 missing disciplina, got {r.status_code}"


def test_os_estatisticas_includes_por_disciplina(headers):
    r = requests.get(f"{BASE_URL}/api/ordens-servico/estatisticas", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "por_disciplina" in data
    assert "por_tipo" in data
    # All 6 OSTipo keys present
    expected_tipos = {"lubrificacao", "limpeza_organizacao", "preventiva", "corretiva", "preparacao_material", "fabricacao_melhorias"}
    assert expected_tipos.issubset(set(data['por_tipo'].keys()))
