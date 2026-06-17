"""Iteration 30 - Rastreabilidade (Bloco 2): planejado_por/iniciado_por/concluido_por + executantes"""
import os
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    data = r.json()
    return data.get('access_token'), data.get('user', {})


@pytest.fixture(scope="module")
def pcm_ctx():
    token, user = _login("pcm@manutrix.com", "pcm123")
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}


@pytest.fixture(scope="module")
def tec_ctx():
    token, user = _login("tecnico@manutrix.com", "tecnico123")
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}


@pytest.fixture(scope="module")
def admin_ctx():
    token, user = _login("admin@manutrix.com", "admin123")
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}


@pytest.fixture(scope="module")
def ativo_id(admin_ctx):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_ctx['headers'], timeout=20)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0, "No ativos found in system"
    return ativos[0]['id']


@pytest.fixture(scope="module")
def users_for_team(admin_ctx):
    r = requests.get(f"{BASE_URL}/api/users", headers=admin_ctx['headers'], timeout=20)
    assert r.status_code == 200
    users = r.json()
    tec_ids = [u['id'] for u in users if u.get('role') == 'tecnico'][:2]
    assert len(tec_ids) >= 1
    return tec_ids


class TestOSRastreabilidade:
    """Full OS flow: PCM creates → moves to planejada → Tecnico starts → Tecnico concludes"""

    def test_full_traceability_flow(self, pcm_ctx, tec_ctx, ativo_id, users_for_team):
        # 1) PCM creates OS with equipe
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "disciplina": "mecanica",
            "prioridade": "media",
            "titulo": "TEST_ITER30_Rastreabilidade",
            "descricao": "OS para testar rastreabilidade",
            "equipe": users_for_team,
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=pcm_ctx['headers'], timeout=20)
        assert r.status_code == 200, f"create OS failed: {r.status_code} {r.text}"
        os_data = r.json()
        os_id = os_data['id']

        # criado_por should be set to PCM user id
        assert os_data.get('criado_por') == pcm_ctx['user']['id']
        assert os_data.get('planejado_por') is None
        assert os_data.get('data_planejamento') is None
        assert os_data.get('iniciado_por') is None
        assert os_data.get('concluido_por') is None
        assert os_data.get('equipe') == users_for_team

        # 2) PCM moves to planejada via kanban PATCH
        r = requests.patch(f"{BASE_URL}/api/ordens-servico/{os_id}/status",
                           json={"new_status": "planejada"}, headers=pcm_ctx['headers'], timeout=20)
        assert r.status_code == 200, f"kanban move failed: {r.text}"

        r = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=pcm_ctx['headers'], timeout=20)
        assert r.status_code == 200
        os_after_plan = r.json()
        assert os_after_plan['status'] == 'planejada'
        assert os_after_plan.get('planejado_por') == pcm_ctx['user']['id'], f"planejado_por not set: {os_after_plan.get('planejado_por')}"
        assert os_after_plan.get('data_planejamento') is not None, "data_planejamento not set"

        # 3) Tecnico starts OS
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/iniciar", headers=tec_ctx['headers'], timeout=20)
        assert r.status_code == 200, f"iniciar failed: {r.text}"

        r = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=tec_ctx['headers'], timeout=20)
        os_after_start = r.json()
        assert os_after_start['status'] == 'em_execucao'
        assert os_after_start.get('iniciado_por') == tec_ctx['user']['id']
        assert os_after_start.get('data_inicio') is not None

        # 4) Tecnico concludes OS
        concluir_body = {
            "servicos_realizados": "Serviço realizado para teste iter30",
            "tempo_execucao_minutos": 30,
        }
        # Preventiva does NOT require photo (only corretiva does)
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/concluir",
                          json=concluir_body, headers=tec_ctx['headers'], timeout=20)
        assert r.status_code == 200, f"concluir failed: {r.text}"

        # 5) GET enriched response
        r = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=tec_ctx['headers'], timeout=20)
        assert r.status_code == 200
        final = r.json()
        assert final['status'] == 'concluida'
        assert final.get('concluido_por') == tec_ctx['user']['id']
        assert final.get('data_conclusao') is not None

        # Enriched names
        assert 'criado_por_nome' in final and final['criado_por_nome']
        assert 'planejado_por_nome' in final and final['planejado_por_nome']
        assert 'iniciado_por_nome' in final and final['iniciado_por_nome']
        assert 'concluido_por_nome' in final and final['concluido_por_nome']

        # equipe_nomes should be a dict {user_id: nome}
        assert 'equipe_nomes' in final, "equipe_nomes missing"
        assert isinstance(final['equipe_nomes'], dict), f"equipe_nomes should be dict, got {type(final['equipe_nomes'])}"
        for uid in users_for_team:
            assert uid in final['equipe_nomes'], f"equipe member {uid} missing from equipe_nomes"


class TestInspecaoExecutantes:
    """Inspection with executantes array + enriched names"""

    def test_create_with_executantes_and_get_enriched(self, admin_ctx, ativo_id, users_for_team):
        payload = {
            "ativo_id": ativo_id,
            "tipo": "mecanica",
            "frequencia": "diaria",
            "executantes": users_for_team,
            "observacoes": "TEST_ITER30_Inspecao_Executantes",
            "checklist": [],
        }
        r = requests.post(f"{BASE_URL}/api/inspecoes", json=payload, headers=admin_ctx['headers'], timeout=20)
        assert r.status_code == 200, f"create inspecao failed: {r.status_code} {r.text}"
        insp = r.json()
        insp_id = insp['id']
        assert insp.get('executantes') == users_for_team

        # GET enrichment
        r = requests.get(f"{BASE_URL}/api/inspecoes/{insp_id}", headers=admin_ctx['headers'], timeout=20)
        assert r.status_code == 200
        full = r.json()
        assert 'executantes_nomes' in full, "executantes_nomes missing"
        assert isinstance(full['executantes_nomes'], dict), f"executantes_nomes should be dict, got {type(full['executantes_nomes'])}"
        for uid in users_for_team:
            assert uid in full['executantes_nomes'], f"executante {uid} missing"

        # criado_por_nome should be present (admin)
        assert 'criado_por_nome' in full and full['criado_por_nome']

        # ativo.sector info should be enriched
        ativo = full.get('ativo')
        assert ativo is not None, "ativo missing from inspecao detail"
        # sector enrichment may be inside ativo or as ativo.sector
        # Just confirm sector_id exists; sector dict optional
        assert ativo.get('sector_id') or ativo.get('sector'), "sector info missing on ativo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
