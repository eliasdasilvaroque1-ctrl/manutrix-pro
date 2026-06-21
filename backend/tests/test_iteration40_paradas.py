"""
Iteration 40 - Bloco 3: Paradas Programadas
Tests CRUD, indicators, asset history integration and RBAC.
"""
import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

ADMIN_CREDS = {"email": "admin@manutrix.com", "password": "admin123"}
TEC_CREDS = {"email": "tecnico@manutrix.com", "password": "tecnico123"}


def login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return login(ADMIN_CREDS)


@pytest.fixture(scope="module")
def tec_token():
    return login(TEC_CREDS)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def tec_headers(tec_token):
    return {"Authorization": f"Bearer {tec_token}"}


@pytest.fixture(scope="module")
def sample_area(admin_headers):
    r = requests.get(f"{BASE_URL}/api/sectors", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    sectors = r.json()
    assert len(sectors) > 0, "No sectors available to use as area"
    return sectors[0]


@pytest.fixture(scope="module")
def sample_os_ids(admin_headers):
    r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    return [os['id'] for os in r.json()[:2]]


# ====== LIST ======
class TestListParadas:
    def test_list_returns_array_with_enrichment(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/paradas-programadas", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            p = data[0]
            for field in ['id', 'numero', 'tipo', 'status', 'area_id',
                          'os_total', 'os_concluidas', 'os_pendentes', 'custo_materiais']:
                assert field in p, f"Missing {field} in list response"
            assert isinstance(p['os_total'], int)
            # area enriched (object with nome) - may be None if sector deleted
            if p.get('area'):
                assert 'nome' in p['area']

    def test_existing_p01_indicators(self, admin_headers):
        """Validate the seeded P01 parada has expected indicators."""
        r = requests.get(f"{BASE_URL}/api/paradas-programadas", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        paradas = r.json()
        p01 = next((p for p in paradas if p.get('numero') == 'P01'), None)
        if p01:
            assert p01['os_total'] >= 0
            assert p01['os_concluidas'] >= 0
            assert p01['os_pendentes'] == p01['os_total'] - p01['os_concluidas']
            assert isinstance(p01['custo_materiais'], (int, float))


# ====== CREATE ======
class TestCreateParada:
    def test_create_minimal(self, admin_headers, sample_area):
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-03-15",
            "data_fim": "2026-03-16",
            "tipo": "preventiva",
            "descricao": "TEST_parada minimal"
        }
        r = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=admin_headers, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        d = r.json()
        assert d.get('id')
        # numero auto-generated as P01, P02, ...
        assert d.get('numero', '').startswith('P'), f"Expected P-prefixed numero, got {d.get('numero')}"
        assert len(d['numero']) >= 3
        assert d['status'] == 'planejada'
        assert d['tipo'] == 'preventiva'
        assert d['area_id'] == sample_area['id']
        return d

    def test_create_with_os_and_full_payload(self, admin_headers, sample_area, sample_os_ids):
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-04-10",
            "data_fim": "2026-04-12",
            "duracao_horas": 48.0,
            "tipo": "grande_parada",
            "descricao": "TEST_grande parada com OS",
            "observacoes": "obs teste",
            "os_vinculadas": sample_os_ids
        }
        r = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=admin_headers, timeout=20)
        assert r.status_code in (200, 201)
        d = r.json()
        assert d['tipo'] == 'grande_parada'
        assert d['duracao_horas'] == 48.0
        assert d['os_vinculadas'] == sample_os_ids
        return d

    def test_tecnico_forbidden(self, tec_headers, sample_area):
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-05-01",
            "data_fim": "2026-05-02",
            "tipo": "corretiva"
        }
        r = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=tec_headers, timeout=20)
        assert r.status_code == 403, f"Expected 403 for tecnico, got {r.status_code}: {r.text}"


# ====== DETAIL ======
class TestDetailParada:
    def test_detail_has_os_detalhes_and_indicators(self, admin_headers, sample_area, sample_os_ids):
        # create with OS
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-06-01",
            "data_fim": "2026-06-02",
            "tipo": "preventiva",
            "descricao": "TEST_detail",
            "os_vinculadas": sample_os_ids
        }
        c = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=admin_headers, timeout=20)
        assert c.status_code in (200, 201)
        pid = c.json()['id']

        r = requests.get(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        d = r.json()
        # required indicators
        for field in ['os_detalhes', 'os_total', 'os_concluidas', 'os_pendentes',
                      'horas_executadas', 'custo_materiais', 'area']:
            assert field in d, f"Missing {field} in detail response"
        assert isinstance(d['os_detalhes'], list)
        assert d['os_total'] == len(sample_os_ids)
        # Each OS detail has expected fields
        for od in d['os_detalhes']:
            assert 'id' in od
            assert 'numero' in od
            assert 'titulo' in od
            assert 'status' in od
        assert isinstance(d['horas_executadas'], (int, float))
        assert isinstance(d['custo_materiais'], (int, float))

    def test_detail_existing_p01(self, admin_headers):
        pid = "e2595813-eb62-4eda-980a-b532db4289ea"
        r = requests.get(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=admin_headers, timeout=20)
        if r.status_code == 404:
            pytest.skip("Seed parada P01 not present")
        assert r.status_code == 200
        d = r.json()
        assert d['numero'] == 'P01'
        assert d['os_total'] == 3
        assert d['os_concluidas'] == 1
        assert d['os_pendentes'] == 2
        # 36h duration, R$40 materials per problem statement
        assert d.get('duracao_horas') == 36 or d.get('duracao_horas') == 36.0
        assert d['custo_materiais'] == 40 or d['custo_materiais'] == 40.0

    def test_detail_not_found(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/paradas-programadas/non-existent-id", headers=admin_headers, timeout=20)
        assert r.status_code == 404


# ====== UPDATE ======
class TestUpdateParada:
    def test_update_creates_field_change_audit(self, admin_headers, sample_area):
        # create
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-07-01",
            "data_fim": "2026-07-02",
            "tipo": "preventiva",
            "descricao": "TEST_update before"
        }
        c = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=admin_headers, timeout=20)
        assert c.status_code in (200, 201)
        pid = c.json()['id']

        # update
        u = requests.put(f"{BASE_URL}/api/paradas-programadas/{pid}",
                         json={"descricao": "TEST_update after", "status": "em_andamento"},
                         headers=admin_headers, timeout=20)
        assert u.status_code == 200
        d = u.json()
        assert d['descricao'] == "TEST_update after"
        assert d['status'] == "em_andamento"

        # GET to verify persisted
        g = requests.get(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=admin_headers, timeout=20)
        assert g.status_code == 200
        assert g.json()['descricao'] == "TEST_update after"

        # Audit field_change
        a = requests.get(f"{BASE_URL}/api/admin/audit-logs",
                         params={"action": "field_change", "entity_id": pid},
                         headers=admin_headers, timeout=20)
        if a.status_code == 200:
            logs = a.json()
            logs = logs if isinstance(logs, list) else logs.get('items', [])
            matching = [l for l in logs if l.get('entity_id') == pid]
            assert len(matching) >= 1, f"No field_change audit log found for parada {pid}"

    def test_tecnico_cannot_update(self, tec_headers, admin_headers, sample_area):
        payload = {
            "area_id": sample_area['id'],
            "data_inicio": "2026-08-01",
            "data_fim": "2026-08-02",
            "tipo": "preventiva",
            "descricao": "TEST_tec_no_update"
        }
        c = requests.post(f"{BASE_URL}/api/paradas-programadas", json=payload, headers=admin_headers, timeout=20)
        pid = c.json()['id']
        u = requests.put(f"{BASE_URL}/api/paradas-programadas/{pid}",
                         json={"descricao": "hacker"}, headers=tec_headers, timeout=20)
        assert u.status_code == 403


# ====== DELETE ======
class TestDeleteParada:
    def test_soft_delete(self, admin_headers, sample_area):
        c = requests.post(f"{BASE_URL}/api/paradas-programadas",
                          json={"area_id": sample_area['id'], "data_inicio": "2026-09-01",
                                "data_fim": "2026-09-02", "tipo": "corretiva",
                                "descricao": "TEST_delete"},
                          headers=admin_headers, timeout=20)
        pid = c.json()['id']
        d = requests.delete(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=admin_headers, timeout=20)
        assert d.status_code in (200, 204)
        # not in list
        l = requests.get(f"{BASE_URL}/api/paradas-programadas", headers=admin_headers, timeout=20)
        ids = [p['id'] for p in l.json()]
        assert pid not in ids
        # detail returns 404 (deleted_at filter)
        g = requests.get(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=admin_headers, timeout=20)
        assert g.status_code == 404

    def test_tecnico_cannot_delete(self, tec_headers, admin_headers, sample_area):
        c = requests.post(f"{BASE_URL}/api/paradas-programadas",
                          json={"area_id": sample_area['id'], "data_inicio": "2026-10-01",
                                "data_fim": "2026-10-02", "tipo": "corretiva",
                                "descricao": "TEST_del_forb"},
                          headers=admin_headers, timeout=20)
        pid = c.json()['id']
        d = requests.delete(f"{BASE_URL}/api/paradas-programadas/{pid}", headers=tec_headers, timeout=20)
        assert d.status_code == 403


# ====== ASSET HISTORY ======
class TestAssetHistorico:
    def test_historico_includes_parada_event(self, admin_headers, sample_area):
        # find an asset in this area
        r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        ativos = r.json()
        ativo = next((a for a in ativos if a.get('sector_id') == sample_area['id']), None)
        if not ativo:
            pytest.skip(f"No ativo found in area {sample_area['id']}")

        # create a parada in that area
        c = requests.post(f"{BASE_URL}/api/paradas-programadas",
                          json={"area_id": sample_area['id'], "data_inicio": "2026-11-01",
                                "data_fim": "2026-11-02", "tipo": "preventiva",
                                "duracao_horas": 12.0,
                                "descricao": "TEST_historico parada"},
                          headers=admin_headers, timeout=20)
        assert c.status_code in (200, 201)
        pid = c.json()['id']

        # query historico filtered by tipo=parada
        h = requests.get(f"{BASE_URL}/api/ativos/{ativo['id']}/historico",
                         params={"tipo": "parada"}, headers=admin_headers, timeout=20)
        assert h.status_code == 200, f"{h.status_code}: {h.text}"
        events = h.json()
        assert isinstance(events, list)
        # at least one event should be the parada we created
        match = [e for e in events if e.get('id') == pid]
        assert len(match) >= 1, f"Parada {pid} not in asset historico"
        ev = match[0]
        assert ev['tipo_evento'] == 'parada'
        assert 'Parada' in ev.get('titulo', '')
        assert ev.get('duracao_horas') == 12.0
