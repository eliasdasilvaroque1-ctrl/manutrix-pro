"""Iteration 31 - Materials consumption + Stock movements tests"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return data['access_token'], data['user']


@pytest.fixture(scope="module")
def admin_ctx():
    token, user = _login("admin@manutrix.com", "admin123")
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}


@pytest.fixture(scope="module")
def tec_ctx():
    token, user = _login("tecnico@manutrix.com", "tecnico123")
    return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}


@pytest.fixture(scope="module")
def ativo_id(admin_ctx):
    """Pick first available active asset"""
    r = requests.get(f"{API}/ativos", headers=admin_ctx['headers'], timeout=30)
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) > 0, "No ativos available — run /api/seed"
    return items[0]['id']


@pytest.fixture(scope="module")
def stock_item(admin_ctx):
    """Create a fresh stock item for materials tests"""
    sku = f"TEST-MAT-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "sku": sku,
        "nome": f"Material teste {sku}",
        "categoria": "outro",
        "quantidade": 10,
        "unidade": "UN",
        "custo_unitario": 50,
        "almoxarifado": "Almox A"
    }
    r = requests.post(f"{API}/estoque", json=payload, headers=admin_ctx['headers'], timeout=30)
    assert r.status_code in (200, 201), f"Create stock failed: {r.status_code} {r.text}"
    item = r.json()
    return item


@pytest.fixture(scope="module")
def os_doc(admin_ctx, tec_ctx, ativo_id):
    """Create an OS, start it (em_execucao)"""
    payload = {
        "titulo": "TEST_ITER31_Materiais",
        "descricao": "OS for material consumption testing",
        "ativo_id": ativo_id,
        "tipo": "preventiva",
        "prioridade": "media",
        "disciplina": "mecanica",
        "equipe": [tec_ctx['user']['id']],
    }
    r = requests.post(f"{API}/ordens-servico", json=payload, headers=admin_ctx['headers'], timeout=30)
    assert r.status_code in (200, 201), f"Create OS failed: {r.status_code} {r.text}"
    os_d = r.json()
    os_id = os_d['id']
    # Move status to planejada then iniciar
    requests.patch(f"{API}/ordens-servico/{os_id}/status", json={"new_status": "planejada"}, headers=admin_ctx['headers'], timeout=30)
    r2 = requests.post(f"{API}/ordens-servico/{os_id}/iniciar", headers=tec_ctx['headers'], timeout=30)
    assert r2.status_code == 200, f"Iniciar failed: {r2.status_code} {r2.text}"
    return os_d


class TestMaterialConsumption:
    def test_add_material_deducts_stock(self, admin_ctx, os_doc, stock_item):
        os_id = os_doc['id']
        # Get stock before
        sb = requests.get(f"{API}/estoque/{stock_item['id']}", headers=admin_ctx['headers'], timeout=30).json()
        qty_before = sb['quantidade']
        # Add material
        r = requests.post(f"{API}/ordens-servico/{os_id}/materiais",
                          json={"item_estoque_id": stock_item['id'], "quantidade": 3},
                          headers=admin_ctx['headers'], timeout=30)
        assert r.status_code in (200, 201), f"Add material: {r.status_code} {r.text}"
        mat = r.json()
        # Validate response fields
        for f in ('id', 'codigo', 'descricao', 'quantidade', 'unidade', 'local_estoque',
                  'usuario_nome', 'ativo_tag', 'os_numero', 'custo_total'):
            assert f in mat, f"Missing field {f} in response: {mat}"
        assert mat['quantidade'] == 3
        assert mat['codigo'] == stock_item['sku']
        assert mat['custo_total'] == 3 * stock_item['custo_unitario']
        # Stock deducted
        sa = requests.get(f"{API}/estoque/{stock_item['id']}", headers=admin_ctx['headers'], timeout=30).json()
        assert sa['quantidade'] == qty_before - 3, f"Stock not deducted: {sa['quantidade']} vs {qty_before-3}"
        # Persist material id for later
        pytest.material_id = mat['id']

    def test_list_materiais(self, admin_ctx, os_doc):
        r = requests.get(f"{API}/ordens-servico/{os_doc['id']}/materiais", headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200, r.text
        lst = r.json()
        assert isinstance(lst, list)
        assert any(m['id'] == pytest.material_id for m in lst), "Material not in list"

    def test_block_negative_stock(self, admin_ctx, os_doc, stock_item):
        # Try to consume 999 (more than available)
        r = requests.post(f"{API}/ordens-servico/{os_doc['id']}/materiais",
                          json={"item_estoque_id": stock_item['id'], "quantidade": 9999},
                          headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 400, f"Expected 400 got {r.status_code} {r.text}"
        assert 'Estoque' in r.text or 'insuficiente' in r.text.lower()

    def test_block_missing_item(self, admin_ctx, os_doc):
        r = requests.post(f"{API}/ordens-servico/{os_doc['id']}/materiais",
                          json={"quantidade": 1}, headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 400, f"Expected 400 got {r.status_code} {r.text}"

    def test_block_zero_or_negative_qty(self, admin_ctx, os_doc, stock_item):
        r = requests.post(f"{API}/ordens-servico/{os_doc['id']}/materiais",
                          json={"item_estoque_id": stock_item['id'], "quantidade": 0},
                          headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 400, f"Expected 400 got {r.status_code} {r.text}"
        r2 = requests.post(f"{API}/ordens-servico/{os_doc['id']}/materiais",
                           json={"item_estoque_id": stock_item['id'], "quantidade": -1},
                           headers=admin_ctx['headers'], timeout=30)
        assert r2.status_code == 400, f"Expected 400 got {r2.status_code} {r2.text}"


class TestMovimentacoes:
    def test_list_movements_includes_consumo(self, admin_ctx, os_doc, stock_item):
        r = requests.get(f"{API}/movimentacoes", headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200, r.text
        movs = r.json()
        # Find saida for our os
        saidas = [m for m in movs if m.get('os_id') == os_doc['id'] and m.get('tipo') == 'saida']
        assert len(saidas) >= 1, f"No saida movement found for OS {os_doc['id']}"
        m = saidas[0]
        for f in ('tipo', 'item_codigo', 'quantidade', 'os_numero', 'ativo_tag', 'usuario_nome'):
            assert f in m, f"Missing field {f} in movement: {m}"
        assert m['item_codigo'] == stock_item['sku']

    def test_filter_by_item(self, admin_ctx, stock_item):
        r = requests.get(f"{API}/movimentacoes", params={"item_id": stock_item['id']},
                         headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200
        movs = r.json()
        assert len(movs) >= 1
        assert all(m['item_id'] == stock_item['id'] for m in movs)

    def test_filter_by_ativo(self, admin_ctx, os_doc):
        r = requests.get(f"{API}/movimentacoes", params={"ativo_id": os_doc['ativo_id']},
                         headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200
        movs = r.json()
        assert len(movs) >= 1
        assert all(m.get('ativo_id') == os_doc['ativo_id'] for m in movs)

    def test_filter_by_user(self, admin_ctx):
        uid = admin_ctx['user']['id']
        r = requests.get(f"{API}/movimentacoes", params={"usuario_id": uid},
                         headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200
        movs = r.json()
        assert all(m.get('usuario_id') == uid for m in movs)


class TestReturnFlow:
    def test_delete_material_returns_stock(self, admin_ctx, os_doc, stock_item):
        # Get stock before
        sb = requests.get(f"{API}/estoque/{stock_item['id']}", headers=admin_ctx['headers'], timeout=30).json()
        qty_before = sb['quantidade']
        # Delete
        r = requests.delete(f"{API}/ordens-servico/{os_doc['id']}/materiais/{pytest.material_id}",
                            headers=admin_ctx['headers'], timeout=30)
        assert r.status_code in (200, 204), f"Delete: {r.status_code} {r.text}"
        # Stock restored (we consumed 3)
        sa = requests.get(f"{API}/estoque/{stock_item['id']}", headers=admin_ctx['headers'], timeout=30).json()
        assert sa['quantidade'] == qty_before + 3, f"Stock not restored: {sa['quantidade']} vs {qty_before+3}"
        # Devolucao movement recorded
        r2 = requests.get(f"{API}/movimentacoes", params={"os_id": os_doc['id'], "tipo": "devolucao"},
                          headers=admin_ctx['headers'], timeout=30)
        assert r2.status_code == 200
        devols = r2.json()
        assert len(devols) >= 1, "No devolucao movement recorded"


class TestAlteradoPor:
    def test_os_update_sets_alterado_por(self, admin_ctx, tec_ctx, ativo_id):
        # Login PCM as the "alterador"
        pcm_token, pcm_user = _login("pcm@manutrix.com", "pcm123")
        pcm_headers = {"Authorization": f"Bearer {pcm_token}"}
        # Create OS as admin
        r = requests.post(f"{API}/ordens-servico", json={
            "titulo": "TEST_ITER31_AlteradoPor",
            "descricao": "test",
            "ativo_id": ativo_id,
            "tipo": "preventiva",
            "prioridade": "baixa",
            "disciplina": "mecanica"
        }, headers=admin_ctx['headers'], timeout=30)
        assert r.status_code in (200, 201), r.text
        os_d = r.json()
        # Update as PCM
        r2 = requests.put(f"{API}/ordens-servico/{os_d['id']}",
                          json={"observacoes": "alterado pelo pcm"},
                          headers=pcm_headers, timeout=30)
        assert r2.status_code == 200, f"Update: {r2.status_code} {r2.text}"
        # GET enriched
        r3 = requests.get(f"{API}/ordens-servico/{os_d['id']}", headers=admin_ctx['headers'], timeout=30)
        assert r3.status_code == 200
        enriched = r3.json()
        assert enriched.get('alterado_por') == pcm_user['id'], f"alterado_por mismatch: {enriched.get('alterado_por')}"
        assert enriched.get('alterado_por_nome'), f"alterado_por_nome missing: {enriched}"


class TestAuditLog:
    def test_audit_actions_present(self, admin_ctx, os_doc):
        r = requests.get(f"{API}/ordens-servico/{os_doc['id']}/historico", headers=admin_ctx['headers'], timeout=30)
        assert r.status_code == 200
        logs = r.json()
        actions = [l.get('action') for l in logs]
        assert 'material_consumo' in actions, f"material_consumo not in audit: {actions}"
        assert 'material_devolucao' in actions, f"material_devolucao not in audit: {actions}"
