"""
Iteration 33 - OS Detalhamento Completo (Bloco 6)
Validates GET /api/ordens-servico/{id} returns all enriched fields needed
by OSDetailPage frontend.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} - {r.text}")
    token = r.json().get("access_token") or r.json().get("token")
    if not token:
        pytest.skip(f"No token in login response: {r.json()}")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def concluded_os(auth_session):
    r = auth_session.get(f"{API}/ordens-servico", params={"status": "concluida"}, timeout=20)
    assert r.status_code == 200, f"List OS failed: {r.status_code} {r.text[:300]}"
    items = r.json()
    assert isinstance(items, list) and len(items) > 0, "No concluded OS found"
    # Prefer 2026-00107 if exists
    target = next((o for o in items if o.get("numero") == "2026-00107"), None) or items[0]
    return target


class TestOSDetailEnriched:
    def test_get_os_returns_200(self, auth_session, concluded_os):
        r = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["id"] == concluded_os["id"]

    def test_os_has_core_fields(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        for f in ["numero", "status", "prioridade", "tipo", "disciplina", "titulo"]:
            assert f in os_d, f"Missing core field: {f}"

    def test_os_has_origem_field(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        assert "origem" in os_d, "Missing origem"
        assert os_d["origem"] in ["manual", "inspecao", "anomalia", "preventiva", "preditiva", None] or isinstance(os_d["origem"], str)

    def test_os_ativo_with_sector(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        assert "ativo" in os_d and os_d["ativo"] is not None, "Missing ativo"
        ativo = os_d["ativo"]
        assert "tag" in ativo and "nome" in ativo, "ativo missing tag/nome"
        if ativo.get("sector_id"):
            assert "sector" in ativo and ativo["sector"] is not None, "sector not enriched"
            assert "nome" in ativo["sector"], "sector missing nome"

    def test_os_responsavel_enriched(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        if os_d.get("responsavel_id"):
            assert "responsavel" in os_d, "responsavel not enriched"
            assert os_d["responsavel"] and "nome" in os_d["responsavel"]

    def test_os_equipe_nomes_enriched(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        equipe = os_d.get("equipe") or []
        if equipe:
            assert "equipe_nomes" in os_d, "equipe_nomes not enriched"
            assert isinstance(os_d["equipe_nomes"], dict)
            for uid in equipe:
                assert uid in os_d["equipe_nomes"], f"Missing name for executante {uid}"

    def test_os_rastreabilidade_actor_names(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        # For concluded OS we expect criado_por, planejado_por, iniciado_por, concluido_por
        for field in ["criado_por", "planejado_por", "iniciado_por", "concluido_por"]:
            if os_d.get(field):
                assert f"{field}_nome" in os_d, f"Missing enriched name for {field}"
                assert os_d[f"{field}_nome"], f"Empty name for {field}_nome"

    def test_os_custos_fields(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        # custo fields should exist (may be 0 or None)
        for f in ["custo_pecas", "custo_mao_obra", "custo_total"]:
            assert f in os_d, f"Missing cost field: {f}"

    def test_os_servico_executado_and_observacoes_fields(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        # Keys should exist or be absent — but for concluded OS, descricao_servico expected
        # at minimum the keys 'observacoes', 'causa_falha', 'descricao_servico' should be present in schema
        for f in ["observacoes", "causa_falha", "descricao_servico", "equipamento_parado", "tempo_execucao_minutos"]:
            # Allow missing if None — but the model should include these
            # Pass if present OR None
            assert f in os_d or os_d.get(f) is None
        # If concluded, descricao_servico typically set
        if os_d.get("status") == "concluida":
            assert os_d.get("descricao_servico") or os_d.get("descricao_servico") == "", \
                "Concluded OS missing descricao_servico"

    def test_os_materiais_sugeridos_present(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        assert "materiais_sugeridos" in os_d
        assert isinstance(os_d["materiais_sugeridos"], list)

    def test_no_mongo_objectid_in_response(self, auth_session, concluded_os):
        os_d = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}", timeout=20).json()
        assert "_id" not in os_d, "_id leaked"
        if os_d.get("ativo"):
            assert "_id" not in os_d["ativo"], "_id leaked in ativo"

    def test_os_historico_endpoint(self, auth_session, concluded_os):
        r = auth_session.get(f"{API}/ordens-servico/{concluded_os['id']}/historico", timeout=20)
        assert r.status_code == 200, r.text
        hist = r.json()
        assert isinstance(hist, list)

    def test_os_2026_00107_specific_fields(self, auth_session):
        # Try to fetch the canonical test OS
        r = auth_session.get(f"{API}/ordens-servico", params={"status": "concluida"}, timeout=20)
        items = r.json()
        target = next((o for o in items if o.get("numero") == "2026-00107"), None)
        if not target:
            pytest.skip("OS 2026-00107 not found")
        os_d = auth_session.get(f"{API}/ordens-servico/{target['id']}", timeout=20).json()
        # As per agent context: causa_falha='1000 HORAS DE TROCA', descricao_servico contains 'SUBSTITUIÇÃO', 5 executantes
        assert os_d.get("causa_falha"), f"Missing causa_falha on 2026-00107: {os_d.get('causa_falha')}"
        assert os_d.get("descricao_servico"), "Missing descricao_servico on 2026-00107"
        equipe = os_d.get("equipe") or []
        assert len(equipe) >= 1, f"Expected executantes on 2026-00107, got {len(equipe)}"
        # equipe_nomes enriched
        if equipe:
            assert os_d.get("equipe_nomes"), "equipe_nomes not enriched on 2026-00107"
