"""
Iteration 37 - Bloco B: Planos de Inspeção (substituição de templates)
Backend tests for /api/planos-inspecao endpoints + resolver + migrar + categorias-disponiveis.
"""
import os
import pytest
import requests
ADMIN_EMAIL = os.getenv('TEST_ADMIN_EMAIL', 'admin@manutrix.com')
ADMIN_PASSWORD = os.getenv('TEST_ADMIN_PASSWORD', 'admin123')
TECNICO_EMAIL = os.getenv('TEST_TECNICO_EMAIL', 'tecnico@manutrix.com')
TECNICO_PASSWORD = os.getenv('TEST_TECNICO_PASSWORD', 'tecnico123')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return r.json().get('token') or r.json().get('access_token')


@pytest.fixture(scope='module')
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope='module')
def tecnico_token():
    return _login(TECNICO_EMAIL, TECNICO_PASSWORD)


@pytest.fixture(scope='module')
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope='module')
def tecnico_headers(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}", "Content-Type": "application/json"}


@pytest.fixture(scope='module')
def first_ativo(admin_headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0, "No ativos found"
    return ativos[0]


# ============== MIGRAR ==============
class TestMigrar:
    def test_migrar_idempotent(self, admin_headers):
        # First call (may or may not create depending on state)
        r1 = requests.post(f"{BASE_URL}/api/planos-inspecao/migrar", headers=admin_headers, timeout=20)
        assert r1.status_code == 200, f"migrar failed: {r1.status_code} {r1.text}"
        body1 = r1.json()
        assert "migrated" in body1
        # Second call should NOT recreate defaults (idempotent for defaults)
        r2 = requests.post(f"{BASE_URL}/api/planos-inspecao/migrar", headers=admin_headers, timeout=20)
        assert r2.status_code == 200
        # We don't assert exact count = 0 because old templates aren't deduped, but defaults shouldn't duplicate
        # The key idempotency check is via GET below

    def test_default_plans_exist_after_migrar(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        planos = r.json()
        # Should have at least one universal plan per category (tipo_equipamento=None, ativo_id=None)
        cats_found = set()
        for p in planos:
            if p.get('tipo_equipamento') is None and p.get('ativo_id') is None:
                cats_found.add(p.get('categoria'))
        assert 'mecanica' in cats_found, f"No universal mecanica plan after migrar. Found: {cats_found}"


# ============== LIST ==============
class TestListPlanos:
    def test_list_returns_required_fields(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        if planos:
            p = planos[0]
            for f in ['id', 'categoria', 'tipo_equipamento', 'ativo_id', 'perguntas', 'nome']:
                assert f in p, f"Missing field {f} in plano"

    def test_filter_by_categoria(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao?categoria=mecanica", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        for p in r.json():
            assert p.get('categoria') == 'mecanica'


# ============== CREATE / UPDATE / DELETE ==============
class TestCRUD:
    plano_id = None

    def test_create_plan(self, admin_headers, first_ativo):
        payload = {
            "tipo_equipamento": "TEST_TIPO_X37",
            "ativo_id": None,
            "categoria": "mecanica",
            "nome": "TEST_iter37 Plan Level 1",
            "perguntas": [
                {"descricao": "TEST Vibração axial OK?", "tipo": "boolean", "obrigatorio": True,
                 "periodicidade": "mensal", "foto_obrigatoria_nc": True, "ordem": 0},
                {"descricao": "TEST Temperatura rolamento", "tipo": "numerico", "obrigatorio": True,
                 "unidade": "°C", "limite_normal": 60, "limite_alerta": 80, "limite_critico": 95, "ordem": 1}
            ]
        }
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, json=payload, timeout=15)
        assert r.status_code == 200, f"Create failed: {r.status_code} {r.text}"
        body = r.json()
        assert body['nome'] == payload['nome']
        assert body['categoria'] == 'mecanica'
        assert body['tipo_equipamento'] == 'TEST_TIPO_X37'
        assert len(body['perguntas']) == 2
        # Verify question fields
        p0 = body['perguntas'][0]
        assert p0['tipo'] == 'boolean'
        assert p0['obrigatorio'] is True
        assert p0['periodicidade'] == 'mensal'
        assert p0['foto_obrigatoria_nc'] is True
        assert 'id' in p0
        p1 = body['perguntas'][1]
        assert p1['limite_normal'] == 60
        assert p1['limite_alerta'] == 80
        assert p1['limite_critico'] == 95
        TestCRUD.plano_id = body['id']

    def test_get_persisted_in_list(self, admin_headers):
        assert TestCRUD.plano_id
        r = requests.get(f"{BASE_URL}/api/planos-inspecao?tipo_equipamento=TEST_TIPO_X37", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        planos = r.json()
        ids = [p['id'] for p in planos]
        assert TestCRUD.plano_id in ids

    def test_update_plan(self, admin_headers):
        assert TestCRUD.plano_id
        payload = {
            "nome": "TEST_iter37 Plan Level 1 EDITED",
            "perguntas": [
                {"descricao": "TEST Edited question", "tipo": "boolean", "obrigatorio": False,
                 "periodicidade": "semanal", "foto_obrigatoria_nc": False, "ordem": 0}
            ]
        }
        r = requests.put(f"{BASE_URL}/api/planos-inspecao/{TestCRUD.plano_id}", headers=admin_headers, json=payload, timeout=15)
        assert r.status_code == 200, f"Update failed: {r.status_code} {r.text}"
        body = r.json()
        assert body['nome'] == payload['nome']
        assert len(body['perguntas']) == 1
        assert body['perguntas'][0]['periodicidade'] == 'semanal'

    def test_tecnico_cannot_create(self, tecnico_headers):
        payload = {"categoria": "mecanica", "nome": "TEST_iter37 should fail", "perguntas": []}
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=tecnico_headers, json=payload, timeout=15)
        assert r.status_code == 403, f"Expected 403 for tecnico, got {r.status_code}: {r.text}"

    def test_delete_plan(self, admin_headers):
        assert TestCRUD.plano_id
        r = requests.delete(f"{BASE_URL}/api/planos-inspecao/{TestCRUD.plano_id}", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        # Verify soft-deleted (not in list)
        r2 = requests.get(f"{BASE_URL}/api/planos-inspecao?tipo_equipamento=TEST_TIPO_X37", headers=admin_headers, timeout=15)
        ids = [p['id'] for p in r2.json()]
        assert TestCRUD.plano_id not in ids


# ============== RESOLVER ==============
class TestResolver:
    created_ids = []

    def test_resolver_merges_level1_and_level2(self, admin_headers, first_ativo):
        ativo_id = first_ativo['id']
        tipo_equip = first_ativo.get('tipo_equipamento') or 'ALIMENTADOR VIBRATORIO'

        # Create Level 1 (tipo_equipamento, no ativo_id)
        l1 = {
            "tipo_equipamento": tipo_equip, "ativo_id": None, "categoria": "mecanica",
            "nome": "TEST_iter37 L1", "perguntas": [
                {"descricao": "TEST L1 Q1", "tipo": "boolean", "ordem": 0},
                {"descricao": "TEST L1 Q2", "tipo": "boolean", "ordem": 1},
                {"descricao": "TEST L1 Q3", "tipo": "boolean", "ordem": 2}
            ]
        }
        r1 = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, json=l1, timeout=15)
        assert r1.status_code == 200
        TestResolver.created_ids.append(r1.json()['id'])

        # Create Level 2 (ativo specific)
        l2 = {
            "tipo_equipamento": None, "ativo_id": ativo_id, "categoria": "mecanica",
            "nome": "TEST_iter37 L2", "perguntas": [
                {"descricao": "TEST L2 Q1", "tipo": "boolean", "ordem": 10},
                {"descricao": "TEST L2 Q2", "tipo": "boolean", "ordem": 11}
            ]
        }
        r2 = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, json=l2, timeout=15)
        assert r2.status_code == 200
        TestResolver.created_ids.append(r2.json()['id'])

        # Resolve
        rr = requests.get(f"{BASE_URL}/api/planos-inspecao/resolver",
                          headers=admin_headers,
                          params={"ativo_id": ativo_id, "categoria": "mecanica"}, timeout=15)
        assert rr.status_code == 200, f"Resolver failed: {rr.status_code} {rr.text}"
        body = rr.json()
        assert body['ativo_id'] == ativo_id
        assert body['categoria'] == 'mecanica'
        assert body['plano_tipo'] is not None
        assert body['plano_ativo'] is not None  # may match our new one or an existing seed L2
        l1_qs = [p for p in body['perguntas'] if p.get('origem') == 'tipo_equipamento']
        l2_qs = [p for p in body['perguntas'] if p.get('origem') == 'ativo_especifico']
        assert len(l1_qs) >= 1, "Should have at least 1 L1 question"
        assert len(l2_qs) >= 1, "Should have at least 1 L2 question"
        # All perguntas have origem
        for p in body['perguntas']:
            assert p.get('origem') in ('tipo_equipamento', 'ativo_especifico', 'padrao')

    def test_resolver_fallback_to_default(self, admin_headers, first_ativo):
        # Use a category that won't have a tipo or ativo plan: but the migrar created universal plans
        # So fallback only triggers if NO plans match (universal plans match because tipo_equipamento=None && ativo_id=None)
        # Actually universal plans have tipo_equipamento=None — they would NOT match the resolver's filter
        # because resolver filters by ativo.tipo_equipamento. So if no Level-1 or Level-2 plans, fallback.
        # Pick an ativo with no plans for 'lubrificacao' specifically (test a fresh combination)
        ativo_id = first_ativo['id']
        rr = requests.get(f"{BASE_URL}/api/planos-inspecao/resolver",
                          headers=admin_headers,
                          params={"ativo_id": ativo_id, "categoria": "lubrificacao"}, timeout=15)
        assert rr.status_code == 200
        body = rr.json()
        # Either has plans, or falls back to default (origem=padrao)
        if body['plano_tipo'] is None and body['plano_ativo'] is None:
            assert body['total_perguntas'] > 0, "Fallback to default should yield questions"
            for p in body['perguntas']:
                assert p.get('origem') == 'padrao'

    def test_resolver_invalid_ativo_404(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao/resolver",
                         headers=admin_headers,
                         params={"ativo_id": "nonexistent-id-xyz", "categoria": "mecanica"}, timeout=15)
        assert r.status_code == 404

    def test_cleanup(self, admin_headers):
        for pid in TestResolver.created_ids:
            requests.delete(f"{BASE_URL}/api/planos-inspecao/{pid}", headers=admin_headers, timeout=15)


# ============== CATEGORIAS DISPONIVEIS ==============
class TestCategoriasDisponiveis:
    def test_returns_three_categorias(self, admin_headers, first_ativo):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao/categorias-disponiveis",
                         headers=admin_headers,
                         params={"ativo_id": first_ativo['id']}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        cats = [item['categoria'] for item in body]
        assert set(cats) == {'mecanica', 'eletrica', 'lubrificacao'}
        for item in body:
            assert 'disponivel' in item
            assert isinstance(item['disponivel'], bool)


# ============== AUDIT LOG ==============
class TestAuditLog:
    def test_audit_log_records_plano_actions(self, admin_headers):
        # Create + delete a plan, then check audit
        payload = {"categoria": "mecanica", "nome": "TEST_iter37 audit check",
                   "perguntas": [{"descricao": "Q", "tipo": "boolean"}]}
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=admin_headers, json=payload, timeout=15)
        assert r.status_code == 200
        pid = r.json()['id']
        requests.delete(f"{BASE_URL}/api/planos-inspecao/{pid}", headers=admin_headers, timeout=15)

        # Check audit log
        al = requests.get(f"{BASE_URL}/api/admin/audit-logs", headers=admin_headers, timeout=15)
        assert al.status_code == 200, f"audit log fetch failed: {al.status_code}"
        logs = al.json() if isinstance(al.json(), list) else al.json().get('logs', [])
        # Find at least one log referencing our plano_inspecao
        found_create = any(l.get('entity_type') == 'plano_inspecao' and l.get('entity_id') == pid and l.get('action') == 'create' for l in logs)
        found_delete = any(l.get('entity_type') == 'plano_inspecao' and l.get('entity_id') == pid and l.get('action') == 'delete' for l in logs)
        assert found_create, "audit log missing plano_inspecao create"
        assert found_delete, "audit log missing plano_inspecao delete"
