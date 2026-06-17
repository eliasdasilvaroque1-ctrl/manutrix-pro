"""
Iteration 29 - PCM Permissions Audit (Bloco 1)
Verifies PCM role can:
- GET /api/ordens-servico, POST create, PUT edit, PATCH kanban move
- GET /api/inspecoes, PUT edit
- GET /api/export/ordens-servico?format=excel
And CANNOT:
- POST iniciar/concluir/pausar OS, DELETE OS
- POST iniciar/concluir inspecao, DELETE inspecao
"""
import os
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
PCM = {"email": "pcm@manutrix.com", "password": "pcm123"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login {creds['email']} failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def pcm_token():
    return _login(PCM)


@pytest.fixture(scope="module")
def pcm_headers(pcm_token):
    return {"Authorization": f"Bearer {pcm_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def sample_ativo_id(admin_headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    items = r.json()
    assert items, "No ativos in system"
    return items[0]["id"]


@pytest.fixture(scope="module")
def existing_os_id(admin_headers):
    r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    lst = r.json()
    assert lst, "No OS exist in system"
    # Pick a non-concluded OS for kanban testing
    for o in lst:
        if o.get("status") not in ("concluida", "cancelada"):
            return o["id"]
    return lst[0]["id"]


@pytest.fixture(scope="module")
def existing_inspecao_id(admin_headers):
    r = requests.get(f"{BASE_URL}/api/inspecoes", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    lst = r.json()
    if not lst:
        pytest.skip("No inspecoes in system")
    return lst[0]["id"]


# ---------------- PCM ALLOWED ----------------

class TestPCMAllowed:
    def test_pcm_can_list_os(self, pcm_headers):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=pcm_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_pcm_can_create_os(self, pcm_headers, sample_ativo_id):
        payload = {
            "ativo_id": sample_ativo_id,
            "tipo": "corretiva",
            "disciplina": "mecanica",
            "origem": "manual",
            "prioridade": "media",
            "titulo": "TEST_PCM_CREATE_OS_iter29",
            "descricao": "Created by PCM role in iteration 29 test",
            "data_planejada": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "custo_pecas": 0,
            "custo_mao_obra": 0,
            "equipamento_parado": False,
            "horas_parada": 0
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=pcm_headers, json=payload, timeout=15)
        assert r.status_code == 200, f"PCM create OS failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert "id" in data
        assert data["titulo"] == payload["titulo"]
        # Save for later tests via class attr
        TestPCMAllowed.created_os_id = data["id"]

    def test_pcm_can_edit_os_priority(self, pcm_headers):
        os_id = getattr(TestPCMAllowed, "created_os_id", None)
        assert os_id, "Need OS from create test"
        r = requests.put(
            f"{BASE_URL}/api/ordens-servico/{os_id}",
            headers=pcm_headers,
            json={"prioridade": "alta"},
            timeout=15
        )
        assert r.status_code == 200, f"PCM edit OS failed: {r.status_code} {r.text[:300]}"
        # Verify persistence
        g = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=pcm_headers, timeout=15)
        assert g.status_code == 200
        assert g.json()["prioridade"] == "alta"

    def test_pcm_can_kanban_move(self, pcm_headers):
        os_id = getattr(TestPCMAllowed, "created_os_id", None)
        assert os_id
        r = requests.patch(
            f"{BASE_URL}/api/ordens-servico/{os_id}/status",
            headers=pcm_headers,
            json={"new_status": "planejada"},
            timeout=15
        )
        assert r.status_code == 200, f"PCM kanban move failed: {r.status_code} {r.text[:300]}"
        assert r.json().get("new_status") == "planejada"

    def test_pcm_can_list_inspecoes(self, pcm_headers):
        r = requests.get(f"{BASE_URL}/api/inspecoes", headers=pcm_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_pcm_can_edit_inspecao(self, pcm_headers, existing_inspecao_id):
        r = requests.put(
            f"{BASE_URL}/api/inspecoes/{existing_inspecao_id}",
            headers=pcm_headers,
            json={"observacoes": "TEST_PCM_EDIT iter29"},
            timeout=15
        )
        assert r.status_code == 200, f"PCM edit inspecao failed: {r.status_code} {r.text[:300]}"

    def test_pcm_can_export_os_excel(self, pcm_headers):
        r = requests.get(
            f"{BASE_URL}/api/export/ordens-servico?format=excel",
            headers={"Authorization": pcm_headers["Authorization"]},
            timeout=30
        )
        assert r.status_code == 200, f"PCM export failed: {r.status_code} {r.text[:200]}"
        # Spreadsheet content-type
        assert "spreadsheet" in r.headers.get("content-type", "").lower() or len(r.content) > 100


# ---------------- PCM FORBIDDEN ----------------

class TestPCMForbidden:
    def test_pcm_cannot_iniciar_os(self, pcm_headers, existing_os_id):
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{existing_os_id}/iniciar",
                          headers=pcm_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_concluir_os(self, pcm_headers, existing_os_id):
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{existing_os_id}/concluir",
                          headers=pcm_headers, json={"observacoes": "x", "tempo_execucao_minutos": 10},
                          timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_pausar_os(self, pcm_headers, existing_os_id):
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{existing_os_id}/pausar",
                          headers=pcm_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_delete_os(self, pcm_headers, existing_os_id):
        r = requests.delete(f"{BASE_URL}/api/ordens-servico/{existing_os_id}",
                            headers=pcm_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_iniciar_inspecao(self, pcm_headers, existing_inspecao_id):
        r = requests.post(f"{BASE_URL}/api/inspecoes/{existing_inspecao_id}/iniciar",
                          headers=pcm_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_concluir_inspecao(self, pcm_headers, existing_inspecao_id):
        r = requests.post(f"{BASE_URL}/api/inspecoes/{existing_inspecao_id}/concluir",
                          headers=pcm_headers, json={"checklist": [], "observacoes": "x"},
                          timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_cannot_delete_inspecao(self, pcm_headers, existing_inspecao_id):
        r = requests.delete(f"{BASE_URL}/api/inspecoes/{existing_inspecao_id}",
                            headers=pcm_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"
