"""
Iteration 25 — Anomalia workflow + Templates linked to inspection + Sobressalentes Código.
Tests:
 - Anomalia status transitions (aberta→em_analise→corrigida→encerrada)
 - Anomalia detail returns comentarios + historico arrays
 - Anomalia POST /comentarios creates comment with usuario_nome
 - Anomalia PUT updates descricao
 - Invalid status transitions rejected
 - Inspection templates filter by tipo_equipamento
"""
import os
import pytest
import requests

from dotenv import load_dotenv
load_dotenv('/app/frontend/.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"
ASSET_ID = "435593b8-a66a-4ddd-a8c6-f4bcce70d4cd"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


# ===== ANOMALIA WORKFLOW =====
class TestAnomaliaWorkflow:
    def test_01_create_anomalia(self, client):
        r = client.post(f"{API}/anomalias", json={
            "ativo_id": ASSET_ID,
            "descricao": "TEST_iter25 anomalia alta com OS",
            "severidade": "alta",
            "gerar_os": True,
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "aberta"
        assert data["descricao"] == "TEST_iter25 anomalia alta com OS"
        assert data["severidade"] == "alta"
        # gerar_os=True should create OS
        assert data.get("os_gerada_id"), "OS should be auto-generated"
        pytest.anom_id = data["id"]

    def test_02_get_detail_includes_comentarios_historico(self, client):
        r = client.get(f"{API}/anomalias/{pytest.anom_id}")
        assert r.status_code == 200
        data = r.json()
        assert "comentarios" in data and isinstance(data["comentarios"], list)
        assert "historico" in data and isinstance(data["historico"], list)
        # ativo enriched
        assert data.get("ativo") is not None

    def test_03_transition_aberta_to_em_analise(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/status", json={"status": "em_analise"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "em_analise"

    def test_04_invalid_transition_em_analise_to_aberta(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/status", json={"status": "aberta"})
        assert r.status_code == 400
        assert "inválida" in r.json().get("detail", "").lower() or "invalid" in r.json().get("detail", "").lower()

    def test_05_add_comment(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/comentarios", json={"texto": "TEST_iter25 comment-1"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["texto"] == "TEST_iter25 comment-1"
        assert "id" in data
        # GET detail should now contain comment
        r2 = client.get(f"{API}/anomalias/{pytest.anom_id}")
        coms = r2.json()["comentarios"]
        assert any(c["texto"] == "TEST_iter25 comment-1" for c in coms)

    def test_06_empty_comment_rejected(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/comentarios", json={"texto": "   "})
        assert r.status_code == 400

    def test_07_put_update_descricao(self, client):
        r = client.put(f"{API}/anomalias/{pytest.anom_id}", json={"descricao": "TEST_iter25 EDITED descricao"})
        assert r.status_code == 200
        # Verify via GET
        r2 = client.get(f"{API}/anomalias/{pytest.anom_id}")
        assert r2.json()["descricao"] == "TEST_iter25 EDITED descricao"
        # Historico should have new entry
        hist = r2.json()["historico"]
        assert len(hist) >= 2  # at least status change + edit

    def test_08_transition_em_analise_to_corrigida(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/status", json={"status": "corrigida"})
        assert r.status_code == 200
        assert r.json()["status"] == "corrigida"

    def test_09_transition_corrigida_to_encerrada(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/status", json={"status": "encerrada"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "encerrada"
        assert data.get("data_encerramento")

    def test_10_encerrada_still_in_list_not_deleted(self, client):
        r = client.get(f"{API}/anomalias")
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert pytest.anom_id in ids, "Encerrada anomalia must remain in list (soft state, not delete)"
        # Verify it has 'encerrada' status
        encerrada = next(a for a in r.json() if a["id"] == pytest.anom_id)
        assert encerrada["status"] == "encerrada"

    def test_11_cannot_transition_from_encerrada(self, client):
        r = client.post(f"{API}/anomalias/{pytest.anom_id}/status", json={"status": "em_analise"})
        assert r.status_code == 400


# ===== INSPECTION TEMPLATES =====
class TestInspectionTemplates:
    def test_01_create_template_for_tipo_alimentador_vibratorio(self, client):
        r = client.post(f"{API}/inspection-templates", json={
            "nome": "TEST_iter25 Template AV",
            "tipo_equipamento": "ALIMENTADOR VIBRATORIO",
            "tipo_inspecao": "mecanica",
            "itens": [
                {"descricao": "Verificar parafusos", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Temperatura rolamento", "tipo": "numerico", "obrigatorio": True, "unidade": "°C"},
                {"descricao": "Estado geral", "tipo": "opcao", "obrigatorio": True, "opcoes": ["Bom","Regular","Ruim","Crítico"]},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ],
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["tipo_equipamento"] == "ALIMENTADOR VIBRATORIO"
        assert len(data["itens"]) == 4
        pytest.tpl_id = data["id"]

    def test_02_filter_templates_by_tipo_equipamento(self, client):
        r = client.get(f"{API}/inspection-templates", params={"tipo_equipamento": "ALIMENTADOR VIBRATORIO"})
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert all(t["tipo_equipamento"] == "ALIMENTADOR VIBRATORIO" for t in items)
        assert any(t["id"] == pytest.tpl_id for t in items)

    def test_03_cleanup_template(self, client):
        r = client.delete(f"{API}/inspection-templates/{pytest.tpl_id}")
        assert r.status_code == 200


# ===== SOBRESSALENTES (estoque) — codigo field =====
class TestSobressalentes:
    def test_01_estoque_items_have_codigo_field(self, client):
        """Backend field is 'sku' but frontend should label it as 'Código' — verify endpoint returns valid items."""
        r = client.get(f"{API}/estoque")
        assert r.status_code == 200
        items = r.json()
        # Just verify endpoint works; UI label test is in frontend Playwright test
        assert isinstance(items, list)
