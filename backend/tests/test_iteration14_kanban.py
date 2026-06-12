"""
Iteration 14 - Kanban OS + P0.5 Architecture Hardening Regression Tests
Tests:
- Backend modularization regression (plants, sectors, kpis, dashboard, ativos, os, inspecoes)
- Kanban PATCH status endpoint
- Audit log GET /historico endpoint
- Role-based permission on PATCH status
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def tecnico_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "tecnico@manutrix.com", "password": "tecnico123"})
    if r.status_code != 200:
        pytest.skip("Tecnico login failed - skipping role tests")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def tecnico_headers(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}", "Content-Type": "application/json"}


# ============== REGRESSION TESTS (Post P0.5 module split) ==============

class TestRegressionEndpoints:
    def test_plants_returns_one(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/plants", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        pp = next((p for p in data if p.get('codigo') == 'PP'), None)
        assert pp is not None, "Expected PP plant"
        assert 'sector_count' in pp and 'asset_count' in pp

    def test_sectors_returns_four(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sectors", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        codes = [s.get('codigo') for s in data]
        for expected in ['EMBA', 'MANU', 'PROD', 'UTIL']:
            assert expected in codes, f"Missing sector {expected}"

    def test_kpis(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/kpis", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        for key in ['disponibilidade_percent', 'mtbf_horas', 'mttr_horas', 'backlog_total', 'ativos_total']:
            assert key in data

    def test_dashboard_stats(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert 'ativos' in data and 'ordens_servico' in data
        assert 'abertas' in data['ordens_servico']
        assert 'planejadas' in data['ordens_servico']

    def test_ativos_returns_nine(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 9, f"Expected >=9 ativos, got {len(data)}"

    def test_ordens_servico_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_inspecoes_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/inspecoes", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_dashboard_trend(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 6


# ============== KANBAN TESTS ==============

class TestKanbanOS:
    @pytest.fixture(scope="class")
    def test_os(self, admin_headers):
        # Create an OS to test Kanban moves
        ativos = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers).json()
        assert len(ativos) > 0
        ativo_id = ativos[0]['id']
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "origem": "manual",
            "prioridade": "media",
            "titulo": "TEST_Kanban OS",
            "descricao": "Iteration 14 kanban test",
            "custo_pecas": 0,
            "custo_mao_obra": 0
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers)
        assert r.status_code == 200, f"Failed to create OS: {r.text}"
        os_doc = r.json()
        yield os_doc
        # Cleanup
        requests.delete(f"{BASE_URL}/api/ordens-servico/{os_doc['id']}", headers=admin_headers)

    def test_patch_status_aberta_to_planejada(self, admin_headers, test_os):
        os_id = test_os['id']
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{os_id}/status",
            json={"new_status": "planejada"},
            headers=admin_headers
        )
        assert r.status_code == 200, f"PATCH failed: {r.text}"
        data = r.json()
        assert data.get('success') is True
        assert data.get('new_status') == "planejada"

        # Verify persistence
        r2 = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        assert r2.status_code == 200
        assert r2.json()['status'] == "planejada"

    def test_patch_status_invalid_status(self, admin_headers, test_os):
        os_id = test_os['id']
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{os_id}/status",
            json={"new_status": "concluida"},  # not allowed via kanban
            headers=admin_headers
        )
        assert r.status_code == 400

    def test_patch_status_to_em_execucao_sets_data_inicio(self, admin_headers, test_os):
        os_id = test_os['id']
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{os_id}/status",
            json={"new_status": "em_execucao"},
            headers=admin_headers
        )
        assert r.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        assert r2.json().get('data_inicio') is not None

    def test_historico_returns_audit_logs(self, admin_headers, test_os):
        os_id = test_os['id']
        r = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}/historico", headers=admin_headers)
        assert r.status_code == 200, f"Historico failed: {r.text}"
        logs = r.json()
        assert isinstance(logs, list)
        # After previous tests we have moved to planejada and em_execucao
        actions = [l.get('action') for l in logs]
        assert 'kanban_move' in actions, f"Expected kanban_move in {actions}"

    def test_patch_status_404_for_invalid_os(self, admin_headers):
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{uuid.uuid4()}/status",
            json={"new_status": "planejada"},
            headers=admin_headers
        )
        assert r.status_code == 404

    def test_tecnico_cannot_patch_status(self, tecnico_headers, admin_headers, test_os):
        os_id = test_os['id']
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{os_id}/status",
            json={"new_status": "pausada"},
            headers=tecnico_headers
        )
        assert r.status_code in [401, 403], f"Tecnico should NOT be able to PATCH status, got {r.status_code}"
