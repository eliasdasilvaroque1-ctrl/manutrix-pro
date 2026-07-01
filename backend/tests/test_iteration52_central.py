"""Iteration 52 — Central de Trabalho adaptive by role.
Tests GET /api/central and POST /api/migrate/planos-legados."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


def login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()['access_token']


@pytest.fixture(scope="module")
def master_token():
    return login("master@manutrix.com", "master123")


@pytest.fixture(scope="module")
def tecnico_token():
    return login("test.mec@maintrix.com", "tec123")


@pytest.fixture(scope="module")
def operador_token():
    return login("test.operador@maintrix.com", "op123")


def _hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===== GET /api/central =====

class TestCentralMaster:
    def test_master_returns_all_sections(self, master_token):
        r = requests.get(f"{API}/central", headers=_hdr(master_token), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get('role') == 'master'
        # base sections
        for section in ('vencidas', 'hoje', 'semana', 'em_execucao', 'sem_data'):
            assert section in d, f"missing section: {section}"
            assert 'total' in d[section]
        # master-specific
        assert 'resumo' in d, "master must have 'resumo'"
        assert 'planos_pendentes' in d, "master must have 'planos_pendentes'"
        assert 'os_criticas' in d, "master must have 'os_criticas'"
        # resumo structure
        for key in ('total_os_abertas', 'total_insp_pendentes', 'total_ativos', 'ativos_parados'):
            assert key in d['resumo']
            assert isinstance(d['resumo'][key], int)
        assert 'total_atividades' in d
        assert isinstance(d['total_atividades'], int)


class TestCentralTecnico:
    def test_tecnico_no_resumo_no_planos(self, tecnico_token):
        r = requests.get(f"{API}/central", headers=_hdr(tecnico_token), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get('role') == 'tecnico'
        # base sections must be present
        for section in ('vencidas', 'hoje', 'semana', 'em_execucao', 'sem_data'):
            assert section in d
        # role-restricted
        assert 'resumo' not in d, "tecnico must NOT have resumo"
        assert 'planos_pendentes' not in d, "tecnico must NOT have planos_pendentes"
        assert 'os_criticas' not in d, "tecnico must NOT have os_criticas"


class TestCentralOperador:
    def test_operador_visibility_filter(self, operador_token):
        r = requests.get(f"{API}/central", headers=_hdr(operador_token), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get('role') == 'operador'
        # ensure OS listed do NOT include mecanica/eletrica/instrumentacao
        forbidden = {"mecanica", "eletrica", "instrumentacao"}
        collected = []
        for section in ('vencidas', 'hoje', 'semana', 'em_execucao', 'sem_data'):
            sec = d.get(section, {})
            for o in sec.get('os', []) or []:
                collected.append(o)
        for o in collected:
            disc = (o.get('disciplina') or '').lower()
            assert disc not in forbidden, f"operador leaking OS disciplina={disc}: {o.get('numero_os') or o.get('id')}"


# ===== POST /api/migrate/planos-legados =====

class TestMigratePlanos:
    def test_master_can_migrate(self, master_token):
        r = requests.post(f"{API}/migrate/planos-legados", headers=_hdr(master_token), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert 'migrated' in d
        assert isinstance(d['migrated'], int)
        assert d['migrated'] >= 0

    def test_second_call_returns_zero(self, master_token):
        """Idempotency — after first migration, second call should return 0."""
        # Ensure first run done
        requests.post(f"{API}/migrate/planos-legados", headers=_hdr(master_token), timeout=30)
        r = requests.post(f"{API}/migrate/planos-legados", headers=_hdr(master_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d['migrated'] == 0, f"expected 0 after re-migration, got {d}"

    def test_tecnico_forbidden(self, tecnico_token):
        r = requests.post(f"{API}/migrate/planos-legados", headers=_hdr(tecnico_token), timeout=30)
        assert r.status_code == 403, r.text
