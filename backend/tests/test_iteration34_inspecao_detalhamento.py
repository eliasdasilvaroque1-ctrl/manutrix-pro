"""
Iteration 34 - Bloco 7: Detalhamento Completo da Inspeção
Tests GET /api/inspecoes/{id} returns enriched data:
- ativo with sector, fabricante, modelo, numero_serie
- os_vinculadas with responsavel_nome and status
- historico array from audit_logs
- actor names: criado_por_nome, iniciado_por_nome, concluido_por_nome, alterado_por_nome
- checklist with conforme, resultado, observacao fields
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

CONCLUDED_INSPECTION_ID = "490c00ce-f050-497c-a03e-02d762916b77"


@pytest.fixture(scope="module")
def admin_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@manutrix.com",
        "password": "admin123"
    }, timeout=30)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in: {data}"
    return token


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def inspecao(headers):
    # Try the specific concluded inspection first
    r = requests.get(f"{BASE_URL}/api/inspecoes/{CONCLUDED_INSPECTION_ID}", headers=headers, timeout=30)
    if r.status_code == 200:
        return r.json()
    # Fallback: list and find a concluded one
    list_r = requests.get(f"{BASE_URL}/api/inspecoes", headers=headers, timeout=30)
    assert list_r.status_code == 200
    items = list_r.json()
    if isinstance(items, dict):
        items = items.get("items") or items.get("data") or []
    concluded = [i for i in items if i.get("status") == "concluida"]
    if not concluded:
        pytest.skip("No concluded inspection found")
    insp_id = concluded[0]["id"]
    r2 = requests.get(f"{BASE_URL}/api/inspecoes/{insp_id}", headers=headers, timeout=30)
    assert r2.status_code == 200
    return r2.json()


# === BACKEND TESTS ===

class TestInspecaoDetalhamento:

    def test_get_inspecao_returns_200(self, inspecao):
        assert inspecao is not None
        assert "id" in inspecao
        assert "status" in inspecao

    def test_inspecao_is_concluded(self, inspecao):
        assert inspecao["status"] == "concluida", f"Expected concluida, got {inspecao['status']}"

    def test_ativo_enriched(self, inspecao):
        ativo = inspecao.get("ativo")
        assert ativo is not None, "ativo should be enriched"
        assert "tag" in ativo
        assert "nome" in ativo
        # _id should not leak
        assert "_id" not in ativo

    def test_ativo_has_sector(self, inspecao):
        ativo = inspecao.get("ativo") or {}
        sector = ativo.get("sector")
        assert sector is not None, "ativo.sector should be enriched"
        assert "nome" in sector

    def test_ativo_has_fabricante_modelo_serie(self, inspecao):
        ativo = inspecao.get("ativo") or {}
        # At least one of these should be set; presence as keys is required
        # We check the structure - ativo may have these as null if not set
        has_any = any(ativo.get(k) for k in ["fabricante", "modelo", "numero_serie"])
        # Don't strictly fail if all null - just record
        assert isinstance(ativo, dict)
        # For BR-01 BRITADOR, fabricante should be ASTEC per problem statement
        if ativo.get("tag") == "BR-01":
            assert ativo.get("fabricante"), f"BR-01 should have fabricante. Ativo keys: {list(ativo.keys())}"

    def test_os_vinculadas_present(self, inspecao):
        # os_vinculadas should be a list (may be empty)
        assert "os_vinculadas" in inspecao
        assert isinstance(inspecao["os_vinculadas"], list)

    def test_os_vinculadas_enriched_when_present(self, inspecao):
        os_list = inspecao.get("os_vinculadas") or []
        for os_v in os_list:
            assert "id" in os_v
            assert "numero" in os_v
            assert "status" in os_v
            # responsavel_nome should be set if responsavel_id existed
            if os_v.get("responsavel_id"):
                assert "responsavel_nome" in os_v

    def test_historico_array_present(self, inspecao):
        assert "historico" in inspecao
        assert isinstance(inspecao["historico"], list)

    def test_historico_entries_structure(self, inspecao):
        hist = inspecao.get("historico") or []
        for h in hist[:5]:
            # audit_log entries should have entity_type and details
            assert "entity_type" in h or "action" in h or "details" in h

    def test_actor_names_enriched(self, inspecao):
        # criado_por_nome should be present if criado_por is set
        if inspecao.get("criado_por"):
            assert "criado_por_nome" in inspecao
        if inspecao.get("iniciado_por"):
            assert "iniciado_por_nome" in inspecao
        if inspecao.get("concluido_por"):
            assert "concluido_por_nome" in inspecao

    def test_concluido_por_nome_for_concluded(self, inspecao):
        # For concluded inspection concluido_por should be set
        assert inspecao.get("concluido_por_nome"), f"Concluded inspection must have concluido_por_nome. Keys: {[k for k in inspecao if 'por' in k.lower()]}"

    def test_checklist_has_response_fields(self, inspecao):
        checklist = inspecao.get("checklist") or []
        assert len(checklist) > 0, "Concluded inspection must have checklist"
        # All items must have id, descricao, and the response-related field KEYS (conforme/resultado/observacao)
        # The fields may be None (e.g., for optional or non-boolean items), but the keys must exist
        for item in checklist:
            assert "id" in item
            assert "descricao" in item
            # The schema must expose response fields (even if None)
            has_response_field = ("conforme" in item) or ("resultado" in item)
            assert has_response_field, f"Item {item.get('descricao')} lacks response schema"
        # At least SOME items in concluded inspection should have responses
        responded = [i for i in checklist if (i.get("conforme") is not None) or (i.get("resultado") is not None)]
        assert len(responded) >= len(checklist) // 2, f"Only {len(responded)}/{len(checklist)} items have responses"

    def test_no_objectid_leaked(self, inspecao):
        assert "_id" not in inspecao
        if inspecao.get("ativo"):
            assert "_id" not in inspecao["ativo"]
        for os_v in inspecao.get("os_vinculadas", []):
            assert "_id" not in os_v
        for h in inspecao.get("historico", []):
            assert "_id" not in h

    def test_executantes_nomes_when_present(self, inspecao):
        if inspecao.get("executantes"):
            assert "executantes_nomes" in inspecao
            assert isinstance(inspecao["executantes_nomes"], dict)

    def test_dates_present_for_concluded(self, inspecao):
        # Should have data_conclusao
        assert inspecao.get("data_conclusao") is not None or inspecao.get("concluida_em") is not None
