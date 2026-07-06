"""RC-04 P0 Fix Verification Tests

Verifies:
 - FIX 1: Gerente can approve OS (deps.py check_write_permission checks allowed_roles BEFORE gerente block)
 - FIX 1: Gerente still blocked from POST /ordens-servico and POST /ativos (regression)
 - FIX 2: Concluir OS auto-computes tempo when omitted (routes/work_orders.py uses `is None` + max(1,...))
 - FIX 2: Concluir OS accepts explicit tempo_execucao_minutos
 - REGRESSION: master full access; PCM manage; operador create sol / blocked; visualizador read-only.
"""

import os
import time
import uuid

import pytest
import requests

# --- Configuration ------------------------------------------------------------
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.strip().split("=", 1)[1].rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "master":       ("master@maintrix.com",       "master123"),
    "gerente":      ("test.gerente@maintrix.com",  "ger123"),
    "pcm":          ("test.pcm@maintrix.com",      "pcm123"),
    "tec_mec":      ("test.mec@maintrix.com",      "tec123"),
    "operador":     ("test.operador@maintrix.com", "op123"),
    "sup_mec":      ("test.sup.mec@maintrix.com",  "sup123"),
}


# --- Helpers ------------------------------------------------------------------
def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token")
    assert tok, f"No access_token for {email}"
    return tok


def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# --- Session-scoped fixtures --------------------------------------------------
@pytest.fixture(scope="session")
def tokens():
    return {role: _login(email, pw) for role, (email, pw) in CREDS.items()}


@pytest.fixture(scope="session")
def ativo_id(tokens):
    """Pick any active ativo in the master org."""
    r = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15)
    assert r.status_code == 200, r.text[:200]
    ativos = r.json()
    assert ativos, "No ativos available in master org"
    return ativos[0]["id"]


@pytest.fixture(scope="session")
def sector_id(tokens):
    r = requests.get(f"{API}/sectors", headers=_hdr(tokens["master"]), timeout=15)
    assert r.status_code == 200
    sectors = r.json()
    assert sectors, "No sectors available"
    return sectors[0]["id"]


# =============================================================================
# FIX 1 — Gerente aprova OS
# =============================================================================
class TestFix1GerenteAprovacao:
    """Gerente must be able to approve OS in aguardando_aprovacao."""

    def test_gerente_can_approve_os(self, tokens, ativo_id):
        # 1) PCM creates a high-cost OS to force aprovacao.necessaria = True
        payload = {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "prioridade": "alta",
            "titulo": f"TEST_RC04 Aprovacao Gerente {uuid.uuid4().hex[:6]}",
            "descricao": "Trigger approval via custo_total >= 10000",
            "custo_pecas": 8000.0,
            "custo_mao_obra": 5000.0,  # Total 13000 > 10000 default limit
        }
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["pcm"]), timeout=15)
        assert r.status_code == 200, f"PCM create OS failed: {r.status_code} {r.text[:200]}"
        os_doc = r.json()
        os_id = os_doc["id"]
        assert os_doc.get("aprovacao", {}).get("necessaria") is True, \
            f"Approval flag not set: {os_doc.get('aprovacao')}"

        # 2) PCM sends OS to aprovacao
        r = requests.post(f"{API}/ordens-servico/{os_id}/enviar-aprovacao",
                          headers=_hdr(tokens["pcm"]), timeout=15)
        assert r.status_code == 200, f"enviar-aprovacao failed: {r.status_code} {r.text[:200]}"
        assert r.json().get("status") == "aguardando_aprovacao"

        # 3) Gerente APPROVES (FIX 1 target)
        r = requests.post(
            f"{API}/ordens-servico/{os_id}/aprovar",
            json={"decisao": "aprovada", "observacao": "TEST_RC04 gerente aprova"},
            headers=_hdr(tokens["gerente"]), timeout=15,
        )
        assert r.status_code == 200, \
            f"FIX 1 REGRESSION — Gerente approval blocked: {r.status_code} {r.text[:300]}"
        approved = r.json()
        assert approved.get("aprovacao", {}).get("status") == "aprovada"
        assert approved.get("status") == "programada"
        # aprovador identified as gerente
        gerente_me = requests.get(f"{API}/auth/me", headers=_hdr(tokens["gerente"])).json()
        assert approved["aprovacao"].get("aprovador") == gerente_me.get("id")


# =============================================================================
# FIX 1 REGRESSION — Gerente still blocked from other writes
# =============================================================================
class TestFix1GerenteWritesBlocked:
    """Gerente must still be BLOCKED from generic writes not in allowed_roles."""

    def test_gerente_cannot_create_os(self, tokens, ativo_id):
        payload = {
            "ativo_id": ativo_id,
            "titulo": "TEST_RC04 gerente should NOT create",
            "tipo": "corretiva",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["gerente"]), timeout=15)
        assert r.status_code == 403, \
            f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_gerente_cannot_create_ativo(self, tokens, sector_id):
        payload = {
            "sector_id": sector_id,
            "nome": f"TEST_RC04 Ativo Gerente {uuid.uuid4().hex[:6]}",
            "tipo_equipamento": "bomba",
        }
        r = requests.post(f"{API}/ativos", json=payload,
                          headers=_hdr(tokens["gerente"]), timeout=15)
        assert r.status_code == 403, \
            f"Expected 403, got {r.status_code}: {r.text[:200]}"


# =============================================================================
# FIX 2 — Concluir OS: tempo auto-calc & explicit tempo
# =============================================================================
class TestFix2ConcluirTempo:
    """Concluir OS must succeed when tempo omitted (auto ≥1) and when explicit."""

    def _create_and_start_os(self, tokens, ativo_id, titulo_prefix: str) -> str:
        # tec_mec creates OS (status_inicial=programada) then iniciar
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",   # avoid foto_check on corretiva
            "prioridade": "media",
            "titulo": f"{titulo_prefix} {uuid.uuid4().hex[:6]}",
            "descricao": "TEST_RC04 concluir tempo",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["tec_mec"]), timeout=15)
        assert r.status_code == 200, f"tec_mec create OS: {r.status_code} {r.text[:200]}"
        os_id = r.json()["id"]

        r = requests.post(f"{API}/ordens-servico/{os_id}/iniciar",
                          headers=_hdr(tokens["tec_mec"]), timeout=15)
        assert r.status_code == 200, f"iniciar: {r.status_code} {r.text[:200]}"
        return os_id

    def test_concluir_auto_tempo_minimum_1(self, tokens, ativo_id):
        """FIX 2 — When tempo omitted and elapsed < 1min, must default to 1."""
        os_id = self._create_and_start_os(tokens, ativo_id, "TEST_RC04 auto-tempo")

        r = requests.post(
            f"{API}/ordens-servico/{os_id}/concluir",
            json={"servicos_realizados": "TEST_RC04 auto tempo", "skip_foto_check": True},
            headers=_hdr(tokens["tec_mec"]), timeout=15,
        )
        assert r.status_code == 200, \
            f"FIX 2 auto-tempo failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("success") is True
        assert body.get("tempo_execucao_minutos", 0) >= 1, \
            f"Auto tempo not applied: {body}"

        # Verify persisted
        got = requests.get(f"{API}/ordens-servico/{os_id}",
                           headers=_hdr(tokens["master"])).json()
        assert got.get("status") == "concluida"
        assert got.get("tempo_execucao_minutos", 0) >= 1

    def test_concluir_explicit_tempo(self, tokens, ativo_id):
        """FIX 2 — Explicit tempo_execucao_minutos must be respected."""
        os_id = self._create_and_start_os(tokens, ativo_id, "TEST_RC04 explicit-tempo")

        r = requests.post(
            f"{API}/ordens-servico/{os_id}/concluir",
            json={
                "servicos_realizados": "TEST_RC04 explicit tempo",
                "skip_foto_check": True,
                "tempo_execucao_minutos": 120,
            },
            headers=_hdr(tokens["tec_mec"]), timeout=15,
        )
        assert r.status_code == 200, \
            f"FIX 2 explicit-tempo failed: {r.status_code} {r.text[:300]}"
        assert r.json().get("tempo_execucao_minutos") == 120

        got = requests.get(f"{API}/ordens-servico/{os_id}",
                           headers=_hdr(tokens["master"])).json()
        assert got.get("tempo_execucao_minutos") == 120


# =============================================================================
# REGRESSION — master full cycle
# =============================================================================
class TestRegressionMaster:
    def test_master_endpoints(self, tokens):
        h = _hdr(tokens["master"])
        checks = [
            ("/dashboard/stats", 200),
            ("/ativos", 200),
            ("/ordens-servico", 200),
            ("/export/ativos?format=excel", 200),
            ("/admin/users", 200),
        ]
        for path, expected in checks:
            r = requests.get(f"{API}{path}", headers=h, timeout=20)
            assert r.status_code == expected, \
                f"MASTER {path}: expected {expected}, got {r.status_code} {r.text[:150]}"


# =============================================================================
# REGRESSION — PCM
# =============================================================================
class TestRegressionPCM:
    def test_pcm_can_create_os_and_export(self, tokens, ativo_id):
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "titulo": f"TEST_RC04 pcm create {uuid.uuid4().hex[:6]}",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["pcm"]), timeout=15)
        assert r.status_code == 200, r.text[:200]

        r = requests.get(f"{API}/export/ativos?format=excel",
                         headers=_hdr(tokens["pcm"]), timeout=20)
        assert r.status_code == 200

    def test_pcm_cannot_iniciar_os(self, tokens, ativo_id):
        # PCM creates OS
        payload = {"ativo_id": ativo_id, "titulo": "TEST_RC04 pcm iniciar block",
                   "tipo": "preventiva"}
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["pcm"]), timeout=15)
        assert r.status_code == 200
        os_id = r.json()["id"]
        # PCM tries to iniciar → should be 403
        r = requests.post(f"{API}/ordens-servico/{os_id}/iniciar",
                          headers=_hdr(tokens["pcm"]), timeout=15)
        assert r.status_code == 403, \
            f"PCM iniciar should be 403, got {r.status_code}: {r.text[:150]}"


# =============================================================================
# REGRESSION — Operador
# =============================================================================
class TestRegressionOperador:
    def test_operador_can_create_solicitation(self, tokens, ativo_id):
        payload = {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "titulo": f"TEST_RC04 operador solicitacao {uuid.uuid4().hex[:6]}",
            "descricao": "TEST_RC04",
        }
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(tokens["operador"]), timeout=15)
        assert r.status_code == 200, r.text[:200]
        assert r.json().get("status") == "solicitada"

    def test_operador_cannot_approve(self, tokens):
        # find any OS
        r = requests.get(f"{API}/ordens-servico", headers=_hdr(tokens["master"]))
        os_list = r.json()
        assert os_list
        os_id = os_list[0]["id"]
        r = requests.post(f"{API}/ordens-servico/{os_id}/aprovar",
                          json={"decisao": "aprovada", "observacao": "x"},
                          headers=_hdr(tokens["operador"]), timeout=15)
        assert r.status_code == 403

    def test_operador_cannot_access_admin_users(self, tokens):
        r = requests.get(f"{API}/admin/users",
                         headers=_hdr(tokens["operador"]), timeout=15)
        assert r.status_code == 403


# =============================================================================
# REGRESSION — Visualizador (create temp user via master; delete after)
# =============================================================================
class TestRegressionVisualizador:
    @pytest.fixture(scope="class")
    def visualizador(self, tokens):
        email = f"test.rc04.viewer.{uuid.uuid4().hex[:8]}@maintrix.com"
        password = "viewer123"
        # Create via admin/users
        payload = {
            "nome": "TEST RC04 Visualizador",
            "email": email,
            "password": password,
            "role": "visualizador",
        }
        r = requests.post(f"{API}/admin/users", json=payload,
                          headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code in (200, 201), \
            f"Create visualizador failed: {r.status_code} {r.text[:200]}"
        created = r.json()
        user_id = created.get("id")

        # Login
        tok = _login(email, password)
        yield {"token": tok, "id": user_id, "email": email}

        # Teardown
        if user_id:
            requests.delete(f"{API}/admin/users/{user_id}",
                            headers=_hdr(tokens["master"]), timeout=15)

    def test_visualizador_can_read(self, visualizador):
        h = _hdr(visualizador["token"])
        r = requests.get(f"{API}/ativos", headers=h, timeout=15)
        assert r.status_code == 200
        r = requests.get(f"{API}/ordens-servico", headers=h, timeout=15)
        assert r.status_code == 200

    def test_visualizador_cannot_write_os(self, visualizador, ativo_id):
        payload = {"ativo_id": ativo_id, "titulo": "TEST_RC04 viewer block",
                   "tipo": "corretiva"}
        r = requests.post(f"{API}/ordens-servico", json=payload,
                          headers=_hdr(visualizador["token"]), timeout=15)
        assert r.status_code == 403, r.text[:200]

    def test_visualizador_cannot_write_estoque(self, visualizador):
        payload = {"nome": "TEST_RC04 viewer estoque",
                   "quantidade": 5, "custo_unitario": 1.0}
        r = requests.post(f"{API}/estoque", json=payload,
                          headers=_hdr(visualizador["token"]), timeout=15)
        assert r.status_code == 403, r.text[:200]
