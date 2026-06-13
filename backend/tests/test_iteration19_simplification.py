"""Iteration 19 - Simplification audit:
- Ativo create with only required fields (sector_id, nome, tipo_equipamento)
- GET /ativos/{id} returns kpis + materiais
- POST /ativos/{id}/materiais
- /kpis auto-calculated
- OS with prioridade=emergencia
- /dashboard/os-por-setor regression
- Sectors endpoint (used as Áreas)
"""
import os
import pytest
import requests

BASE = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def sector_id(H):
    code = "TEST19"
    # try get existing first via list
    lst = requests.get(f"{BASE}/api/sectors", headers=H).json()
    for s in lst:
        if s.get('codigo') == code:
            return s['id']
    r = requests.post(f"{BASE}/api/sectors", headers=H, json={"codigo": code, "nome": "TEST Área 19", "cor": "#10b981"})
    assert r.status_code == 200, r.text
    return r.json()['id']


# ----- Sectors as Áreas -----

def test_list_sectors(H):
    r = requests.get(f"{BASE}/api/sectors", headers=H)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_sector_exp(H):
    # try delete if any
    code = "EXP19"
    r = requests.post(f"{BASE}/api/sectors", headers=H, json={"codigo": code, "nome": "Expedição"})
    # may be 400 if exists already
    assert r.status_code in (200, 400), r.text
    if r.status_code == 200:
        assert r.json()['codigo'] == code
        assert r.json()['nome'] == 'Expedição'


# ----- Ativo simplified create -----

def test_create_ativo_minimal(H, sector_id):
    payload = {
        "sector_id": sector_id,
        "nome": "TEST19 Bomba",
        "tipo_equipamento": "Bomba"
    }
    r = requests.post(f"{BASE}/api/ativos", headers=H, json=payload)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['nome'] == "TEST19 Bomba"
    assert d['tipo_equipamento'] == "Bomba"
    assert d['sector_id'] == sector_id
    assert d['tag']  # auto-generated
    pytest.ativo_id = d['id']


def test_create_ativo_with_extra_fields_rejected_or_ignored(H, sector_id):
    """Frontend currently sends mtbf_horas, valor_aquisicao, area_id; pydantic should ignore extras"""
    payload = {
        "sector_id": sector_id,
        "nome": "TEST19 Extra",
        "tipo_equipamento": "Motor",
        "area_id": sector_id,
        "mtbf_horas": 500,
        "valor_aquisicao": 1000,
        "depreciacao_anual": 100,
        "criticidade": "alta",
        "status": "operacional"
    }
    r = requests.post(f"{BASE}/api/ativos", headers=H, json=payload)
    assert r.status_code == 200, r.text
    d = r.json()
    # Verify simplified: no criticidade/status/valor_aquisicao stored
    assert 'criticidade' not in d or d.get('criticidade') is None
    assert d['nome'] == "TEST19 Extra"


def test_get_ativo_has_kpis_and_materiais(H):
    aid = getattr(pytest, 'ativo_id', None)
    assert aid
    r = requests.get(f"{BASE}/api/ativos/{aid}", headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    assert 'kpis' in d, "Asset must expose 'kpis' object"
    k = d['kpis']
    for key in ('mtbf_horas', 'mttr_horas', 'disponibilidade_percent', 'total_os', 'total_falhas'):
        assert key in k, f"Missing KPI: {key}"
    assert 'materiais' in d
    assert isinstance(d['materiais'], list)


# ----- Materiais por equipamento -----

def test_add_material_to_ativo(H):
    aid = getattr(pytest, 'ativo_id', None)
    assert aid
    payload = {"nome": "Rolamento 6205", "quantidade": 2, "unidade": "UN"}
    r = requests.post(f"{BASE}/api/ativos/{aid}/materiais", headers=H, json=payload)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['nome'] == "Rolamento 6205"
    assert d['quantidade'] == 2
    pytest.material_id = d['id']


def test_list_materiais(H):
    aid = getattr(pytest, 'ativo_id', None)
    r = requests.get(f"{BASE}/api/ativos/{aid}/materiais", headers=H)
    assert r.status_code == 200
    assert any(m['id'] == getattr(pytest, 'material_id') for m in r.json())


# ----- Auto-calculated KPIs in /api/kpis -----

def test_kpis_auto_calculated(H):
    r = requests.get(f"{BASE}/api/kpis", headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    for key in ('disponibilidade_percent', 'mtbf_horas', 'mttr_horas', 'backlog_total', 'ativos_total'):
        assert key in d, f"Missing KPI: {key}"
    assert isinstance(d['mtbf_horas'], (int, float))


# ----- OS with prioridade=emergencia -----

def test_os_create_emergencia(H, sector_id):
    aid = getattr(pytest, 'ativo_id', None)
    assert aid
    payload = {
        "ativo_id": aid,
        "tipo": "corretiva",
        "disciplina": "mecanica",
        "prioridade": "emergencia",
        "titulo": "TEST19 OS Emergencia",
        "equipamento_parado": True
    }
    r = requests.post(f"{BASE}/api/ordens-servico", headers=H, json=payload)
    assert r.status_code in (200, 201), r.text
    d = r.json()
    assert d['prioridade'] == "emergencia"
    pytest.os_id = d.get('id')


# ----- Dashboard regressions -----

def test_dashboard_os_por_setor(H):
    r = requests.get(f"{BASE}/api/dashboard/os-por-setor", headers=H)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_dashboard_stats(H):
    r = requests.get(f"{BASE}/api/dashboard/stats", headers=H)
    assert r.status_code == 200
    d = r.json()
    assert 'ativos' in d
    assert 'ordens_servico' in d


def test_dashboard_ativos_mais_falhas(H):
    r = requests.get(f"{BASE}/api/dashboard/ativos-mais-falhas", headers=H)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ----- Estoque regression -----

def test_estoque_list(H):
    r = requests.get(f"{BASE}/api/estoque", headers=H)
    assert r.status_code == 200


# ----- Kanban regression -----

def test_kanban_data(H):
    r = requests.get(f"{BASE}/api/ordens-servico", headers=H)
    assert r.status_code == 200


# ----- Inspecoes regression -----

def test_inspecoes_list(H):
    r = requests.get(f"{BASE}/api/inspecoes", headers=H)
    assert r.status_code == 200


# ----- Cleanup -----

def test_zzz_cleanup(H):
    aid = getattr(pytest, 'ativo_id', None)
    if aid:
        requests.delete(f"{BASE}/api/ativos/{aid}", headers=H)
    osid = getattr(pytest, 'os_id', None)
    if osid:
        # soft delete OS may not exist; ignore
        requests.delete(f"{BASE}/api/ordens-servico/{osid}", headers=H)
