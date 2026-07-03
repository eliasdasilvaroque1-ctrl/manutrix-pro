"""
Sprint 56 - GOVERNANÇA OPERACIONAL end-to-end tests.
Covers: operador flow (solicitação → status=solicitada, origem=operador),
PCM approval flow (send to approval → approve/reject/revise),
new OS statuses, dynamic stats (por_origem, aguardando_aprovacao),
free-string tipos_os.
"""
import os
import pytest
import requests
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

OPERADOR = {"email": "test.operador@maintrix.com", "password": "op123"}
PCM = {"email": "test.pcm@maintrix.com", "password": "pcm123"}
MASTER = {"email": "master@maintrix.com", "password": "master123"}

ATIVO_ID = "5af42d90-4654-4067-b67d-92d7e7f6f78d"


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def operador_token():
    return _login(OPERADOR)


@pytest.fixture(scope="module")
def pcm_token():
    return _login(PCM)


@pytest.fixture(scope="module")
def master_token():
    return _login(MASTER)


def _headers(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ---------------- OPERADOR FLOW ----------------

class TestOperadorFlow:

    def test_operador_can_create_solicitacao(self, operador_token):
        payload = {
            "ativo_id": ATIVO_ID,
            "titulo": f"TEST_SP56 vazamento bomba {uuid.uuid4().hex[:6]}",
            "justificativa": "Detectei vazamento no eixo do rolamento durante ronda.",
            "descricao": "Vazamento em rolamento",
            "prioridade": "alta",
            "tipo": "corretiva",
            "origem": "operador",
            "equipamento_parado": False,
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(operador_token), timeout=15)
        assert r.status_code == 200, f"POST /ordens-servico failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        # Data assertions
        assert data["status"] == "solicitada", f"Expected status=solicitada, got {data['status']}"
        assert data["origem"] == "operador", f"Expected origem=operador, got {data['origem']}"
        assert data["titulo"] == payload["titulo"]
        assert data["justificativa"] == payload["justificativa"]
        assert data["aprovacao"]["necessaria"] is False, "corretiva should not require approval by default"
        assert "id" in data and "numero" in data
        # Store for later
        pytest.solicitacao_id = data["id"]

    def test_get_solicitacao_persisted(self, operador_token):
        os_id = getattr(pytest, "solicitacao_id", None)
        assert os_id, "No solicitação created in prior test"
        r = requests.get(f"{API}/ordens-servico/{os_id}", headers=_headers(operador_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "solicitada"
        assert r.json()["origem"] == "operador"


# ---------------- PCM APPROVAL FLOW ----------------

class TestPCMApprovalFlow:

    def test_pcm_creates_melhoria_requires_approval(self, pcm_token):
        payload = {
            "ativo_id": ATIVO_ID,
            "titulo": f"TEST_SP56 melhoria retrofit {uuid.uuid4().hex[:6]}",
            "descricao": "Instalar variador de frequência",
            "prioridade": "media",
            "tipo": "melhoria",  # tipo em tipos_que_precisam_aprovacao
            "custo_pecas": 500,
            "custo_mao_obra": 200,
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        # PCM-created OS starts as programada, but aprovacao.necessaria=True for tipo melhoria
        assert data["tipo"] == "melhoria"
        assert data["aprovacao"]["necessaria"] is True, "melhoria must set aprovacao.necessaria=True"
        assert data["aprovacao"]["status"] == "pendente"
        pytest.melhoria_id = data["id"]

    def test_send_to_approval(self, pcm_token):
        os_id = getattr(pytest, "melhoria_id", None)
        assert os_id
        r = requests.post(f"{API}/ordens-servico/{os_id}/enviar-aprovacao",
                          headers=_headers(pcm_token), timeout=10)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert data["status"] == "aguardando_aprovacao"
        assert data["aprovacao"]["status"] == "pendente"
        assert data["aprovacao"]["necessaria"] is True

    def test_approve_by_master(self, master_token):
        """Master has admin rights; gerente user not seeded, so use master to test approval endpoint."""
        os_id = getattr(pytest, "melhoria_id", None)
        assert os_id
        r = requests.post(f"{API}/ordens-servico/{os_id}/aprovar",
                          json={"decisao": "aprovada", "observacao": "OK aprovado"},
                          headers=_headers(master_token), timeout=10)
        assert r.status_code == 200, f"aprovar failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert data["status"] == "programada", f"Expected programada after aprovada, got {data['status']}"
        assert data["aprovacao"]["status"] == "aprovada"
        assert data["aprovacao"]["observacao"] == "OK aprovado"

    def test_reject_flow(self, pcm_token, master_token):
        # Create another melhoria
        payload = {
            "ativo_id": ATIVO_ID,
            "titulo": f"TEST_SP56 reject flow {uuid.uuid4().hex[:6]}",
            "descricao": "Teste rejeição",
            "prioridade": "media",
            "tipo": "melhoria",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200
        os_id = r.json()["id"]

        # Send to approval
        r2 = requests.post(f"{API}/ordens-servico/{os_id}/enviar-aprovacao",
                           headers=_headers(pcm_token), timeout=10)
        assert r2.status_code == 200

        # Reject
        r3 = requests.post(f"{API}/ordens-servico/{os_id}/aprovar",
                           json={"decisao": "rejeitada", "observacao": "Fora do orçamento"},
                           headers=_headers(master_token), timeout=10)
        assert r3.status_code == 200
        assert r3.json()["status"] == "cancelada"
        assert r3.json()["aprovacao"]["status"] == "rejeitada"

    def test_revisao_flow(self, pcm_token, master_token):
        payload = {
            "ativo_id": ATIVO_ID,
            "titulo": f"TEST_SP56 revision flow {uuid.uuid4().hex[:6]}",
            "descricao": "Teste revisão",
            "prioridade": "media",
            "tipo": "melhoria",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(pcm_token), timeout=15)
        os_id = r.json()["id"]
        requests.post(f"{API}/ordens-servico/{os_id}/enviar-aprovacao", headers=_headers(pcm_token), timeout=10)

        r3 = requests.post(f"{API}/ordens-servico/{os_id}/aprovar",
                           json={"decisao": "revisao", "observacao": "Detalhar escopo"},
                           headers=_headers(master_token), timeout=10)
        assert r3.status_code == 200, r3.text[:200]
        assert r3.json()["status"] == "em_analise"
        assert r3.json()["aprovacao"]["status"] == "revisao"

    def test_invalid_decisao(self, master_token, pcm_token):
        payload = {"ativo_id": ATIVO_ID, "titulo": f"TEST_SP56 invalid {uuid.uuid4().hex[:6]}",
                   "descricao": "x", "tipo": "melhoria"}
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(pcm_token), timeout=15)
        os_id = r.json()["id"]
        requests.post(f"{API}/ordens-servico/{os_id}/enviar-aprovacao", headers=_headers(pcm_token), timeout=10)
        r3 = requests.post(f"{API}/ordens-servico/{os_id}/aprovar",
                           json={"decisao": "invalida"},
                           headers=_headers(master_token), timeout=10)
        assert r3.status_code == 400


# ---------------- STATISTICS ----------------

class TestEstatisticas:
    def test_estatisticas_shape(self, pcm_token):
        r = requests.get(f"{API}/ordens-servico/estatisticas", headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        # New fields must be present
        for key in ["por_status", "por_tipo", "por_disciplina", "por_origem",
                    "atrasadas", "concluidas_mes", "aguardando_aprovacao",
                    "aguardando_material", "total_abertas"]:
            assert key in data, f"Missing key in stats: {key}"
        # Types
        assert isinstance(data["por_origem"], dict)
        assert isinstance(data["por_tipo"], dict)
        assert isinstance(data["aguardando_aprovacao"], int)
        # After our tests, we should see operador in por_origem
        assert "operador" in data["por_origem"], f"Expected 'operador' key in por_origem, got {list(data['por_origem'].keys())}"

    def test_operador_stats_scoped(self, operador_token):
        r = requests.get(f"{API}/ordens-servico/estatisticas", headers=_headers(operador_token), timeout=15)
        # Operador may or may not have stats endpoint access — accept 200 or 403
        assert r.status_code in (200, 403), r.text[:200]


# ---------------- BACKWARD COMPAT / LIST FILTERS ----------------

class TestListAndFilters:
    def test_list_filter_by_origem(self, pcm_token):
        r = requests.get(f"{API}/ordens-servico?origem=operador", headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for os in data:
            assert os.get("origem") == "operador", f"Expected origem=operador, got {os.get('origem')}"

    def test_list_filter_by_status_solicitada(self, pcm_token):
        r = requests.get(f"{API}/ordens-servico?status=solicitada", headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200
        for os in r.json():
            assert os["status"] == "solicitada"


# ---------------- FREE-STRING TIPO ----------------

class TestFreeStringTipo:
    def test_custom_tipo_accepted(self, pcm_token):
        """Ensure OSCreate does NOT enforce enum on tipo."""
        payload = {
            "ativo_id": ATIVO_ID,
            "titulo": f"TEST_SP56 custom tipo {uuid.uuid4().hex[:6]}",
            "descricao": "Tipo customizado da empresa",
            "prioridade": "media",
            "tipo": "meu_tipo_custom",  # not in enum
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=_headers(pcm_token), timeout=15)
        assert r.status_code == 200, f"Custom tipo should be accepted: {r.status_code} {r.text[:200]}"
        assert r.json()["tipo"] == "meu_tipo_custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
