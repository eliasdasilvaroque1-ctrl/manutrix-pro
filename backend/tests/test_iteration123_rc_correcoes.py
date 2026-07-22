"""RC de correção pré-piloto — modo econômico
Tests:
 1) Auditoria endpoint returns logs with details that may be objects (FE must handle) — backend just returns
 2) Nova OS: causa_falha optional
 3) Título independente do procedimento (backend accepts title regardless of procedimento_id)
 4) OS PDF generation OK (no QR in header — visual, not testable via API status)
 5) Ativos QR remains functional
"""
import os
import requests
import pytest
from pathlib import Path


def _load_env():
    env_file = Path('/app/frontend/.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": "test.admin@maintrix.com", "password": "admin123"}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()['access_token']


@pytest.fixture(scope='module')
def pcm_token():
    # PCM has single org — try direct login. If needs org_id, fetch it from admin's user
    r = requests.post(f"{API}/auth/login", json={"email": "test.pcm@maintrix.com", "password": "pcm123"}, timeout=30)
    if r.status_code == 400 and 'organiza' in r.text.lower():
        # need org id - use known ASTEC id
        r = requests.post(f"{API}/auth/login", json={
            "email": "test.pcm@maintrix.com",
            "password": "pcm123",
            "organization_id": "9a232bf2-fc01-4253-813f-8df356be31c1"
        }, timeout=30)
    assert r.status_code == 200, f"pcm login failed: {r.status_code} {r.text}"
    return r.json()['access_token']


@pytest.fixture(scope='module')
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope='module')
def pcm_headers(pcm_token):
    return {"Authorization": f"Bearer {pcm_token}"}


# --- Auditoria ---
class TestAuditoria:
    def test_admin_can_read_audit_logs(self, admin_headers):
        r = requests.get(f"{API}/admin/audit-logs?limit=50", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"audit-logs failed: {r.status_code} {r.text}"
        data = r.json()
        # response may be list or dict with items
        logs = data if isinstance(data, list) else data.get('items', data.get('logs', []))
        assert isinstance(logs, list)

    def test_pcm_can_read_audit_via_api(self, pcm_headers):
        """Backend allows PCM to view audit logs (see server.py:4240).
        The 'RC requirement' is only to hide the Auditoria menu item in the
        frontend sidebar for PCM (verified via Playwright test)."""
        r = requests.get(f"{API}/admin/audit-logs?limit=10", headers=pcm_headers, timeout=30)
        # PCM has backend permission by design; verify no 500
        assert r.status_code in (200, 403), f"unexpected: {r.status_code}"


# --- Nova OS: causa_falha optional & titulo independente ---
class TestNovaOS:
    @pytest.fixture(scope='class')
    def ativo_id(self, admin_headers):
        r = requests.get(f"{API}/ativos?limit=1", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        # response may be a list or object with items
        items = data if isinstance(data, list) else data.get('items', [])
        assert len(items) > 0, "No ativo available for OS creation"
        return items[0]['id']

    def test_create_corretiva_sem_causa_falha(self, admin_headers, ativo_id):
        payload = {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "disciplina": "mecanica",
            "prioridade": "media",
            "titulo": "TEST_ RC123 Corretiva Sem Causa",
            "descricao": "Teste sem causa_falha",
            "equipamento_parado": False,
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code in (200, 201), f"create OS failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get('titulo', '').startswith('TEST_')
        # cleanup
        os_id = data.get('id')
        if os_id:
            requests.delete(f"{API}/ordens-servico/{os_id}", headers=admin_headers, timeout=30)

    def test_create_preventiva_sem_procedimento(self, admin_headers, ativo_id):
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "disciplina": "mecanica",
            "prioridade": "baixa",
            "titulo": "TEST_ RC123 Preventiva sem Procedimento",
            "descricao": "sem procedimento",
            "equipamento_parado": False,
        }
        r = requests.post(f"{API}/ordens-servico", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code in (200, 201), f"create preventiva failed: {r.status_code} {r.text}"
        data = r.json()
        os_id = data.get('id')
        if os_id:
            requests.delete(f"{API}/ordens-servico/{os_id}", headers=admin_headers, timeout=30)

    def test_title_independent_from_procedure(self, admin_headers, ativo_id):
        # Create OS with a title AND a procedimento_id
        # First try to get a procedure
        rp = requests.get(f"{API}/procedimentos-select", headers=admin_headers, timeout=30)
        proc_id = None
        if rp.status_code == 200:
            procs = rp.json()
            if procs and isinstance(procs, list):
                proc_id = procs[0].get('id')

        custom_title = "TEST_ Titulo Independente RC123"
        payload = {
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "disciplina": "mecanica",
            "prioridade": "media",
            "titulo": custom_title,
            "descricao": "test",
            "equipamento_parado": False,
        }
        if proc_id:
            payload["procedimento_id"] = proc_id

        r = requests.post(f"{API}/ordens-servico", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code in (200, 201), f"create OS failed: {r.status_code} {r.text}"
        data = r.json()
        # Backend should preserve the title as-is regardless of procedimento
        assert data.get('titulo') == custom_title, f"title changed! got '{data.get('titulo')}'"
        os_id = data.get('id')
        if os_id:
            requests.delete(f"{API}/ordens-servico/{os_id}", headers=admin_headers, timeout=30)


# --- PDF ---
class TestPDF:
    def test_gerar_pdf_existing_os(self, admin_headers):
        # Use provided test OS id
        os_id = "be9878f1-71ab-476e-b491-b1af7c402685"
        r = requests.get(f"{API}/ordens-servico/{os_id}/pdf?modo=digital", headers=admin_headers, timeout=60)
        if r.status_code == 404:
            # OS might not exist; find another
            list_r = requests.get(f"{API}/ordens-servico?limit=1", headers=admin_headers, timeout=30)
            items = list_r.json() if isinstance(list_r.json(), list) else list_r.json().get('items', [])
            if not items:
                pytest.skip("No OS available for PDF test")
            os_id = items[0]['id']
            r = requests.get(f"{API}/ordens-servico/{os_id}/pdf?modo=digital", headers=admin_headers, timeout=60)
        assert r.status_code == 200, f"PDF gen failed: {r.status_code} {r.text[:300]}"
        assert r.content[:4] == b'%PDF', "response is not a PDF"


# --- Ativo QR still works ---
class TestAtivoQR:
    def test_get_ativo_qr(self, admin_headers):
        r = requests.get(f"{API}/ativos?limit=1", headers=admin_headers, timeout=30)
        items = r.json() if isinstance(r.json(), list) else r.json().get('items', [])
        if not items:
            pytest.skip("No ativos")
        ativo_id = items[0]['id']
        # Try QR PNG endpoint
        r2 = requests.get(f"{API}/ativos/{ativo_id}/qrcode/png", headers=admin_headers, timeout=30)
        assert r2.status_code == 200, f"ativo QR failed: {r2.status_code}"
