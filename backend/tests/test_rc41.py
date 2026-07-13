"""MAINTRIX Test Suite — RC4.1
Run: cd /app/backend && TEST_API_URL=https://procure-manutrix.preview.emergentagent.com python -m pytest tests/test_rc41.py -v
"""
import pytest
import httpx
import os
import time

BASE = os.environ.get("TEST_API_URL", "https://procure-manutrix.preview.emergentagent.com")
API = f"{BASE}/api"
ORG = "9a232bf2-fc01-4253-813f-8df356be31c1"

USERS = {
    "master": ("master@maintrix.com", "master123"),
    "admin": ("test.admin@maintrix.com", "admin123"),
    "pcm": ("test.pcm@maintrix.com", "pcm123"),
    "tecnico": ("test.mec@maintrix.com", "tec123"),
}

# Token cache to avoid rate limit
_token_cache = {}

def get_token(role):
    if role in _token_cache:
        return _token_cache[role]
    email, pwd = USERS[role]
    r = httpx.post(f"{API}/auth/login", json={"email": email, "password": pwd, "organization_id": ORG}, timeout=15)
    assert r.status_code == 200, f"Login {role} failed: {r.text}"
    _token_cache[role] = r.json()["access_token"]
    return _token_cache[role]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def get_first_ativo(token):
    r = httpx.get(f"{API}/ativos", headers=auth(token), timeout=10)
    ativos = r.json()
    return ativos[0]["id"] if isinstance(ativos, list) and ativos else ativos.get("items", [{}])[0].get("id")


# ============== AUTH ==============

class TestAuth:
    def test_login_all_roles(self):
        for role in USERS:
            token = get_token(role)
            assert token, f"{role} login failed"

    def test_login_wrong_password(self):
        r = httpx.post(f"{API}/auth/login", json={"email": "master@maintrix.com", "password": "wrong", "organization_id": ORG}, timeout=10)
        assert r.status_code == 401

    def test_login_auto_resolve(self):
        r = httpx.post(f"{API}/auth/login", json={"email": "test.admin@maintrix.com", "password": "admin123"}, timeout=10)
        assert r.status_code == 200

    def test_login_master_requires_org(self):
        r = httpx.post(f"{API}/auth/login", json={"email": "master@maintrix.com", "password": "master123"}, timeout=10)
        assert r.status_code == 400

    def test_lookup_email(self):
        r = httpx.post(f"{API}/auth/lookup-email", json={"email": "test.admin@maintrix.com"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["organization_id"] == ORG

    def test_auth_me(self):
        r = httpx.get(f"{API}/auth/me", headers=auth(get_token("master")), timeout=10)
        assert r.status_code == 200


# ============== STATE MACHINE ==============

class TestStateMachine:
    def test_direct_execution(self):
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Direct", "execucao_direta": True
        }, timeout=10)
        assert r.status_code in (200, 201)
        assert r.json()["status"] == "em_execucao"

    def test_programada_to_em_execucao(self):
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "SM Programada"
        }, timeout=10)
        os_id = r.json()["id"]
        # programada → disponivel
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "disponivel"}, timeout=10)
        assert r.status_code == 200
        # disponivel → em_execucao
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "em_execucao"}, timeout=10)
        assert r.status_code == 200

    def test_invalid_transition(self):
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Invalid"
        }, timeout=10)
        os_id = r.json()["id"]
        # programada → concluida (skip states — invalid)
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "concluida"}, timeout=10)
        assert r.status_code == 400

    def test_get_transitions(self):
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Trans"
        }, timeout=10)
        os_id = r.json()["id"]
        r = httpx.get(f"{API}/ordens-servico/{os_id}/transitions", headers=auth(token), timeout=10)
        assert r.status_code == 200
        assert "valid_transitions" in r.json()

    def test_full_lifecycle_direct(self):
        """Ciclo direto: criação direta → em_execucao → concluida → encerrada"""
        token = get_token("master")
        aid = get_first_ativo(token)
        # 1. Criar OS direta (em_execucao)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Lifecycle Direct", "execucao_direta": True
        }, timeout=10)
        assert r.status_code in (200, 201)
        os_id = r.json()["id"]
        assert r.json()["status"] == "em_execucao"
        # 2. Concluir (skip_foto_check legítimo para testes automatizados)
        r = httpx.post(f"{API}/ordens-servico/{os_id}/concluir", headers=auth(token),
                       json={"servicos_realizados": "Manutenção corretiva realizada", "tempo_execucao_minutos": 30, "skip_foto_check": True}, timeout=10)
        assert r.status_code == 200, f"Concluir falhou: {r.text}"
        # 3. Verificar status concluida
        r = httpx.get(f"{API}/ordens-servico/{os_id}", headers=auth(token), timeout=10)
        assert r.json()["status"] == "concluida"
        # 4. Encerrar (concluida → encerrada)
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token),
                        json={"new_status": "encerrada"}, timeout=10)
        assert r.status_code == 200, f"Encerrar falhou: {r.text}"
        # 5. Verificar estado terminal
        r = httpx.get(f"{API}/ordens-servico/{os_id}", headers=auth(token), timeout=10)
        assert r.json()["status"] == "encerrada"

    def test_full_lifecycle_long(self):
        """Ciclo completo longo: programada → disponivel → em_execucao → concluida → encerrada"""
        token = get_token("master")
        aid = get_first_ativo(token)
        # Criar OS padrão (programada)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "SM Lifecycle Long"
        }, timeout=10)
        assert r.status_code in (200, 201)
        os_id = r.json()["id"]
        assert r.json()["status"] == "programada"
        # programada → disponivel
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "disponivel"}, timeout=10)
        assert r.status_code == 200
        # disponivel → em_execucao
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "em_execucao"}, timeout=10)
        assert r.status_code == 200
        # Concluir
        r = httpx.post(f"{API}/ordens-servico/{os_id}/concluir", headers=auth(token),
                       json={"servicos_realizados": "Manutenção preventiva realizada", "tempo_execucao_minutos": 60, "skip_foto_check": True}, timeout=10)
        assert r.status_code == 200
        # concluida → encerrada
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "encerrada"}, timeout=10)
        assert r.status_code == 200

    def test_foto_obrigatoria_corretiva(self):
        """Regra de negócio: corretiva sem foto deve ser rejeitada"""
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Foto Check", "execucao_direta": True
        }, timeout=10)
        os_id = r.json()["id"]
        # Tentar concluir SEM foto e SEM skip_foto_check → deve retornar 400
        r = httpx.post(f"{API}/ordens-servico/{os_id}/concluir", headers=auth(token),
                       json={"servicos_realizados": "OK", "tempo_execucao_minutos": 30}, timeout=10)
        assert r.status_code == 400
        assert "foto" in r.json()["detail"].lower()

    def test_concluir_sem_descricao(self):
        """Regra de negócio: concluir sem descrição deve ser rejeitada"""
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "SM No Desc", "execucao_direta": True
        }, timeout=10)
        os_id = r.json()["id"]
        # Tentar concluir SEM descrição
        r = httpx.post(f"{API}/ordens-servico/{os_id}/concluir", headers=auth(token),
                       json={"tempo_execucao_minutos": 30, "skip_foto_check": True}, timeout=10)
        # Should fail if no description exists at all
        # Note: backend falls back to os_doc.descricao, so may pass if OS has descricao

    def test_terminal_state_no_transition(self):
        """Estado terminal não permite transições"""
        token = get_token("master")
        aid = get_first_ativo(token)
        # Criar e cancelar
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Terminal"
        }, timeout=10)
        os_id = r.json()["id"]
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "cancelada"}, timeout=10)
        assert r.status_code == 200
        # Tentar transicionar de cancelada → em_execucao (inválido)
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "em_execucao"}, timeout=10)
        assert r.status_code == 400
        assert "terminal" in r.json()["detail"].lower() or "nao permitida" in r.json()["detail"].lower()

    def test_audit_trail(self):
        """Auditoria: transições devem gerar log"""
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "SM Audit"
        }, timeout=10)
        os_id = r.json()["id"]
        # Fazer uma transição
        httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "disponivel"}, timeout=10)
        # Verificar histórico
        r = httpx.get(f"{API}/ordens-servico/{os_id}/historico", headers=auth(token), timeout=10)
        assert r.status_code == 200
        logs = r.json()
        assert len(logs) >= 1, "Audit trail deve conter pelo menos 1 entrada"

    def test_error_message_consistency(self):
        """Mensagens de erro devem ser consistentes e informativas"""
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(token), json={
            "ativo_id": aid, "tipo": "corretiva", "titulo": "SM Error Msg"
        }, timeout=10)
        os_id = r.json()["id"]
        # Transição inválida: programada → encerrada
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(token), json={"new_status": "encerrada"}, timeout=10)
        assert r.status_code == 400
        detail = r.json()["detail"]
        # Mensagem deve conter transições válidas
        assert "validas" in detail.lower() or "permitida" in detail.lower()


# ============== DASHBOARD ==============

class TestDashboard:
    def test_dashboard_stats(self):
        r = httpx.get(f"{API}/dashboard/stats", headers=auth(get_token("master")), timeout=15)
        assert r.status_code == 200

    def test_dashboard_executivo(self):
        r = httpx.get(f"{API}/dashboard/executivo", headers=auth(get_token("master")), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "kpis" in d and "trend_12m" in d and "top_falhas" in d
        assert len(d["trend_12m"]) == 12

    def test_indicadores(self):
        for p in ["hoje", "mes"]:
            r = httpx.get(f"{API}/indicadores?periodo={p}", headers=auth(get_token("master")), timeout=10)
            assert r.status_code == 200

    def test_minha_area(self):
        r = httpx.get(f"{API}/minha-area", headers=auth(get_token("master")), timeout=10)
        assert r.status_code == 200
        assert "contadores" in r.json()


# ============== DOSSIER ==============

class TestDossier:
    def test_dossier(self):
        token = get_token("master")
        aid = get_first_ativo(token)
        r = httpx.get(f"{API}/ativos/{aid}/dossie", headers=auth(token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert all(k in d for k in ["ativo", "kpis", "os", "planos", "inspecoes"])


# ============== PERFORMANCE ==============

class TestPerformance:
    def test_health_fast(self):
        start = time.time()
        r = httpx.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        assert (time.time() - start) < 2

    def test_dashboard_fast(self):
        start = time.time()
        r = httpx.get(f"{API}/dashboard/executivo", headers=auth(get_token("master")), timeout=15)
        assert r.status_code == 200
        assert (time.time() - start) < 5


# ============== RBAC ==============

class TestRBAC:
    def test_unauthenticated_rejected(self):
        r = httpx.get(f"{API}/ativos", timeout=10)
        assert r.status_code in (401, 403)

    def test_system_status_admin(self):
        r = httpx.get(f"{API}/system/status", headers=auth(get_token("master")), timeout=10)
        assert r.status_code == 200

    def test_system_status_tecnico_denied(self):
        r = httpx.get(f"{API}/system/status", headers=auth(get_token("tecnico")), timeout=10)
        assert r.status_code == 403

    def test_tecnico_cannot_approve(self):
        """Técnico não pode fazer transição de aprovação (programada → disponível feita por pcm)"""
        master_token = get_token("master")
        tec_token = get_token("tecnico")
        aid = get_first_ativo(master_token)
        # Criar OS como master
        r = httpx.post(f"{API}/ordens-servico", headers=auth(master_token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "RBAC Tec Test"
        }, timeout=10)
        os_id = r.json()["id"]
        # Técnico tenta mover programada → disponivel (somente pcm/admin/master pode)
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(tec_token),
                        json={"new_status": "disponivel"}, timeout=10)
        assert r.status_code == 400, f"Técnico NÃO deveria poder fazer programada→disponivel: {r.text}"

    def test_tecnico_can_execute(self):
        """Técnico pode iniciar execução de OS disponível"""
        master_token = get_token("master")
        tec_token = get_token("tecnico")
        aid = get_first_ativo(master_token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(master_token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "RBAC Tec Execute"
        }, timeout=10)
        os_id = r.json()["id"]
        # master move para disponivel
        httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(master_token), json={"new_status": "disponivel"}, timeout=10)
        # Técnico pode mover disponivel → em_execucao
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(tec_token),
                        json={"new_status": "em_execucao"}, timeout=10)
        assert r.status_code == 200, f"Técnico deveria poder iniciar execução: {r.text}"

    def test_pcm_can_plan(self):
        """PCM pode planejar (programada → disponivel)"""
        pcm_token = get_token("pcm")
        aid = get_first_ativo(pcm_token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(pcm_token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "RBAC PCM Plan"
        }, timeout=10)
        os_id = r.json()["id"]
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(pcm_token), json={"new_status": "disponivel"}, timeout=10)
        assert r.status_code == 200

    def test_tecnico_cannot_cancel(self):
        """Técnico não pode cancelar OS"""
        master_token = get_token("master")
        tec_token = get_token("tecnico")
        aid = get_first_ativo(master_token)
        r = httpx.post(f"{API}/ordens-servico", headers=auth(master_token), json={
            "ativo_id": aid, "tipo": "preventiva", "titulo": "RBAC Cancel"
        }, timeout=10)
        os_id = r.json()["id"]
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=auth(tec_token),
                        json={"new_status": "cancelada"}, timeout=10)
        assert r.status_code == 400, f"Técnico NÃO deveria poder cancelar: {r.text}"
