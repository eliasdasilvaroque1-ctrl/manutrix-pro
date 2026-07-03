"""Sprint 59 — RBAC Consolidation tests.
Validates the centralized permission matrix in deps.py via the
GET /api/auth/permissions endpoint, plus enforcement on estoque and export.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

CREDS = {
    'tec_mecanico': ('test.mec@maintrix.com', 'tec123'),
    'operador': ('test.operador@maintrix.com', 'op123'),
    'pcm': ('test.pcm@maintrix.com', 'pcm123'),
    'gerente': ('test.gerente@maintrix.com', 'ger123'),
    'master': ('master@maintrix.com', 'master123'),
}


def _login(role_key: str) -> dict:
    email, pwd = CREDS[role_key]
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": pwd}, timeout=15)
    assert r.status_code == 200, f"login {role_key} failed: {r.status_code} {r.text[:200]}"
    return r.json()


@pytest.fixture(scope="module")
def tokens():
    out = {}
    for k in CREDS:
        try:
            out[k] = _login(k)['access_token']
        except AssertionError:
            out[k] = None
    return out


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- /api/auth/permissions matrix checks ----------

class TestAuthPermissionsMatrix:

    def test_tec_mecanico_permissions(self, tokens):
        tok = tokens['tec_mecanico']
        assert tok, "tec_mecanico login failed"
        r = requests.get(f"{BASE_URL}/api/auth/permissions", headers=_headers(tok), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'tec_mecanico'
        assert data['role_label'] == 'Técnico Mecânico'
        perms = set(data['permissions'])
        assert len(perms) == 16, f"expected 16 perms, got {len(perms)}: {sorted(perms)}"
        # Positive
        for p in ('os.executar', 'os.concluir', 'solicitacao.criar', 'qr.escanear',
                  'ronda.executar', 'hh.registrar'):
            assert p in perms, f"tec_mecanico missing {p}"
        # Negative
        for p in ('exportar', 'estoque.criar', 'dashboard.visualizar',
                  'planos.criar', 'os.aprovar', 'admin.usuarios'):
            assert p not in perms, f"tec_mecanico should NOT have {p}"
        # available_roles present
        assert 'available_roles' in data and isinstance(data['available_roles'], list)
        ids = [r['id'] for r in data['available_roles']]
        # 'tecnico' legacy must be excluded
        assert 'tecnico' not in ids
        for expected in ('master','admin','pcm','supervisor','gerente','tec_mecanico',
                         'tec_eletrico','instrumentista','lubrificador','operador',
                         'inspetor','visualizador'):
            assert expected in ids, f"available_roles missing {expected}"

    def test_operador_permissions(self, tokens):
        tok = tokens['operador']
        assert tok
        r = requests.get(f"{BASE_URL}/api/auth/permissions", headers=_headers(tok), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'operador'
        perms = set(data['permissions'])
        assert len(perms) == 10, f"expected 10 perms, got {len(perms)}: {sorted(perms)}"
        for p in ('solicitacao.criar', 'qr.escanear', 'ronda.executar',
                  'inspecoes.executar', 'os.criar'):
            assert p in perms, f"operador missing {p}"
        for p in ('os.executar', 'os.concluir', 'exportar', 'dashboard.visualizar',
                  'estoque.criar', 'planos.criar'):
            assert p not in perms, f"operador should NOT have {p}"

    def test_pcm_permissions(self, tokens):
        tok = tokens['pcm']
        assert tok
        r = requests.get(f"{BASE_URL}/api/auth/permissions", headers=_headers(tok), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'pcm'
        assert data['role_label'] == 'PCM'
        perms = set(data['permissions'])
        assert len(perms) == 31, f"expected 31 perms, got {len(perms)}: {sorted(perms)}"
        for p in ('estoque.criar', 'estoque.editar', 'planos.criar', 'planos.editar',
                  'exportar', 'dashboard.visualizar', 'ativos.criar', 'os.programar',
                  'biblioteca.gerenciar'):
            assert p in perms, f"pcm missing {p}"
        # PCM should NOT execute OS or approve
        for p in ('os.executar', 'os.concluir', 'os.aprovar', 'admin.usuarios',
                  'admin.white_label'):
            assert p not in perms, f"pcm should NOT have {p}"

    def test_gerente_permissions(self, tokens):
        tok = tokens['gerente']
        assert tok
        r = requests.get(f"{BASE_URL}/api/auth/permissions", headers=_headers(tok), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'gerente'
        perms = set(data['permissions'])
        assert len(perms) == 15, f"expected 15 perms, got {len(perms)}: {sorted(perms)}"
        for p in ('os.aprovar', 'exportar', 'dashboard.visualizar',
                  'planos.visualizar', 'admin.auditoria'):
            assert p in perms, f"gerente missing {p}"
        for p in ('estoque.criar', 'planos.criar', 'os.executar', 'os.editar',
                  'admin.usuarios'):
            assert p not in perms, f"gerente should NOT have {p}"

    def test_matrix_contains_46_permissions(self, tokens):
        tok = tokens['master']
        assert tok, "master login required"
        r = requests.get(f"{BASE_URL}/api/auth/permissions", headers=_headers(tok), timeout=10)
        assert r.status_code == 200
        data = r.json()
        # master should have most (but not necessarily all) perms
        master_perms = set(data['permissions'])
        assert len(master_perms) >= 40, f"master should have >=40, got {len(master_perms)}"
        # Aggregate all perms across roles = 46
        all_perms = set()
        for role in data['available_roles']:
            all_perms.update(role['permissions'])
        assert len(all_perms) == 46, f"expected 46 unique permissions total, got {len(all_perms)}"


# ---------- Endpoint enforcement ----------

class TestEstoquePermissionEnforcement:

    def test_operador_cannot_create_estoque(self, tokens):
        tok = tokens['operador']
        assert tok
        payload = {
            "nome": "TEST_RBAC_OPERADOR",
            "descricao": "should be rejected",
            "categoria": "outro",
            "quantidade": 1,
            "estoque_minimo": 0,
            "estoque_maximo": 10,
            "unidade": "UN",
            "custo_unitario": 1.0,
        }
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload,
                          headers=_headers(tok), timeout=10)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"

    def test_pcm_can_create_estoque(self, tokens):
        tok = tokens['pcm']
        assert tok
        payload = {
            "nome": "TEST_RBAC_PCM_ITEM",
            "descricao": "sprint59 test",
            "categoria": "outro",
            "quantidade": 1,
            "estoque_minimo": 0,
            "estoque_maximo": 10,
            "unidade": "UN",
            "custo_unitario": 1.5,
        }
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload,
                          headers=_headers(tok), timeout=15)
        assert r.status_code in (200, 201), f"pcm create should succeed, got {r.status_code}: {r.text[:200]}"
        body = r.json()
        item_id = body.get('id') or (body.get('item') or {}).get('id')
        # cleanup best-effort
        if item_id:
            requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=_headers(tok), timeout=10)


class TestExportPermissionEnforcement:

    def test_operador_cannot_export(self, tokens):
        tok = tokens['operador']
        assert tok
        r = requests.get(f"{BASE_URL}/api/export/ativos?format=excel",
                         headers=_headers(tok), timeout=15)
        assert r.status_code == 403, f"operador export should be 403, got {r.status_code}"

    def test_tec_mecanico_cannot_export(self, tokens):
        tok = tokens['tec_mecanico']
        assert tok
        r = requests.get(f"{BASE_URL}/api/export/ativos?format=excel",
                         headers=_headers(tok), timeout=15)
        assert r.status_code == 403

    def test_pcm_can_export(self, tokens):
        tok = tokens['pcm']
        assert tok
        r = requests.get(f"{BASE_URL}/api/export/ativos?format=excel",
                         headers=_headers(tok), timeout=30)
        assert r.status_code == 200, f"pcm export should succeed, got {r.status_code}"
        assert 'spreadsheet' in r.headers.get('content-type', '') or len(r.content) > 100

    def test_gerente_can_export(self, tokens):
        tok = tokens['gerente']
        assert tok
        r = requests.get(f"{BASE_URL}/api/export/ativos?format=excel",
                         headers=_headers(tok), timeout=30)
        assert r.status_code == 200


# ---------- Visibility of OS/inspecoes for tec_mecanico ----------

class TestTecMecanicoVisibility:

    def test_login_and_list_os(self, tokens):
        tok = tokens['tec_mecanico']
        assert tok
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_headers(tok), timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        # Every returned OS must belong to mechanical scope, be assigned to user,
        # or have empty disciplina (default). We accept the list — validate no
        # electrical/instrumentation disciplines leak in.
        disallowed = {'eletrica', 'instrumentacao'}
        # user id from /auth/me
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=_headers(tok), timeout=10).json()
        uid = me.get('id')
        for o in items:
            d = o.get('disciplina') or ''
            if d in disallowed:
                # must be personally assigned
                assert o.get('responsavel_id') == uid or uid in (o.get('equipe') or []), \
                    f"OS {o.get('id')} disc={d} leaked to tec_mecanico"

    def test_list_inspecoes(self, tokens):
        tok = tokens['tec_mecanico']
        assert tok
        r = requests.get(f"{BASE_URL}/api/inspecoes", headers=_headers(tok), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
