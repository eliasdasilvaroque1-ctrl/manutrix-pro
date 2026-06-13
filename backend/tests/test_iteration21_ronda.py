"""
Iteration 21 — MANUTRIX Ronda (Inspection Route) end-to-end backend tests.
Covers:
- GET /api/rondas (areas with total_ativos + inspecoes_pendentes)
- GET /api/ronda/{area_id} (ativos w/ ultima_inspecao + tem_pendente)
- POST /api/inspecoes — Ronda mode auto-conclude w/ checklist
- POST /api/inspecoes — auto-OS for non-conformities
- POST /api/inspecoes — non-Ronda (no responses) stays pendente
- POST /api/ativos — UNIQUE(area_id, tag) constraint
- GET /api/checklists/templates — mecanica/eletrica/lubrificacao
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No token in response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def test_area(auth):
    """Create an isolated test area (sector) for this test run."""
    codigo = f"T21{uuid.uuid4().hex[:6].upper()}"
    payload = {"nome": f"TEST21 Ronda Area {codigo}", "codigo": codigo, "descricao": "iter21"}
    r = auth.post(f"{API}/sectors", json=payload)
    assert r.status_code in (200, 201), f"Create sector failed: {r.status_code} {r.text}"
    area = r.json()
    yield area
    # Teardown soft-delete
    try:
        auth.delete(f"{API}/sectors/{area['id']}")
    except Exception:
        pass


@pytest.fixture(scope="module")
def test_ativo(auth, test_area):
    tag = f"T21-{uuid.uuid4().hex[:4].upper()}"
    payload = {
        "tag": tag, "nome": "Motor Teste Iter21",
        "tipo_equipamento": "motor", "fabricante": "WEG",
        "sector_id": test_area['id']
    }
    r = auth.post(f"{API}/ativos", json=payload)
    assert r.status_code in (200, 201), f"Create ativo failed: {r.status_code} {r.text}"
    return r.json()


# ============== Checklist Templates ==============

class TestChecklistTemplates:
    def test_get_templates_returns_three_types(self, auth):
        r = auth.get(f"{API}/checklists/templates")
        assert r.status_code == 200, r.text
        data = r.json()
        for tipo in ("mecanica", "eletrica", "lubrificacao"):
            assert tipo in data, f"Missing template: {tipo}. Got keys: {list(data.keys())}"
            assert "itens" in data[tipo]
            assert isinstance(data[tipo]["itens"], list)
            assert len(data[tipo]["itens"]) > 0, f"{tipo} has no items"


# ============== Rondas List ==============

class TestRondasList:
    def test_list_rondas_returns_areas_with_counts(self, auth, test_area, test_ativo):
        r = auth.get(f"{API}/rondas")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # find our test area
        found = next((x for x in data if x.get('area', {}).get('id') == test_area['id']), None)
        assert found is not None, "Test area not present in rondas list"
        assert "total_ativos" in found
        assert "inspecoes_pendentes" in found
        assert found["total_ativos"] >= 1, f"Expected >=1 ativo, got {found['total_ativos']}"


# ============== Ronda Detail ==============

class TestRondaDetail:
    def test_get_ronda_area_returns_ativos(self, auth, test_area, test_ativo):
        r = auth.get(f"{API}/ronda/{test_area['id']}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data['area_id'] == test_area['id']
        assert data['total_ativos'] >= 1
        ativos = data['ativos']
        my_entry = next((a for a in ativos if a['ativo']['id'] == test_ativo['id']), None)
        assert my_entry is not None
        assert "ultima_inspecao" in my_entry
        assert "tem_pendente" in my_entry
        assert isinstance(my_entry["tem_pendente"], bool)

    def test_get_ronda_invalid_area_returns_404(self, auth):
        r = auth.get(f"{API}/ronda/non-existent-id-xxxx")
        assert r.status_code == 404


# ============== UNIQUE(area_id, tag) ==============

class TestAtivoUniqueConstraint:
    def test_duplicate_tag_same_area_rejected(self, auth, test_area, test_ativo):
        payload = {
            "tag": test_ativo['tag'], "nome": "Duplicate",
            "tipo_equipamento": "motor", "sector_id": test_area['id']
        }
        r = auth.post(f"{API}/ativos", json=payload)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        assert "TAG" in r.text or "tag" in r.text.lower()

    def test_same_tag_different_area_succeeds(self, auth, test_ativo):
        # Create a second area
        codigo = f"T21B{uuid.uuid4().hex[:5].upper()}"
        r = auth.post(f"{API}/sectors", json={"nome": f"TEST21 Area2 {codigo}", "codigo": codigo})
        assert r.status_code in (200, 201)
        area2 = r.json()
        try:
            payload = {
                "tag": test_ativo['tag'], "nome": "Same TAG in different area",
                "tipo_equipamento": "motor", "sector_id": area2['id']
            }
            r2 = auth.post(f"{API}/ativos", json=payload)
            assert r2.status_code in (200, 201), f"Same tag in diff area should succeed: {r2.status_code} {r2.text}"
            created = r2.json()
            assert created['tag'].upper() == test_ativo['tag'].upper()
            assert created['sector_id'] == area2['id']
            # cleanup
            auth.delete(f"{API}/ativos/{created['id']}")
        finally:
            auth.delete(f"{API}/sectors/{area2['id']}")


# ============== Inspecao Auto-Conclusion (Ronda Mode) ==============

class TestInspecaoAutoConclude:
    def test_inspecao_with_filled_checklist_auto_concludes_conforme(self, auth, test_ativo):
        checklist = [
            {"id": str(uuid.uuid4()), "descricao": "Vibração OK", "tipo": "boolean", "obrigatorio": True, "conforme": True, "valor": None, "observacao": None},
            {"id": str(uuid.uuid4()), "descricao": "Temperatura OK", "tipo": "boolean", "obrigatorio": True, "conforme": True, "valor": None, "observacao": None},
        ]
        payload = {
            "ativo_id": test_ativo['id'],
            "tipo": "mecanica",
            "frequencia": "diaria",
            "checklist": checklist
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data['status'] == "concluida", f"Expected concluida, got {data.get('status')}"
        assert data['resultado'] == "conforme", f"Expected conforme, got {data.get('resultado')}"
        assert data.get('data_conclusao') is not None, "data_conclusao must be set"
        # Verify persistence
        gr = auth.get(f"{API}/inspecoes/{data['id']}")
        assert gr.status_code == 200
        assert gr.json()['status'] == "concluida"

    def test_inspecao_with_nok_auto_concludes_and_generates_os(self, auth, test_ativo):
        checklist = [
            {"id": str(uuid.uuid4()), "descricao": "Vibração OK", "tipo": "boolean", "obrigatorio": True, "conforme": True, "valor": None, "observacao": None},
            {"id": str(uuid.uuid4()), "descricao": "Temperatura OK", "tipo": "boolean", "obrigatorio": True, "conforme": False, "valor": None, "observacao": "Acima do limite"},
        ]
        payload = {
            "ativo_id": test_ativo['id'],
            "tipo": "mecanica",
            "frequencia": "diaria",
            "checklist": checklist
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data['status'] == "com_pendencias", f"Expected com_pendencias, got {data.get('status')}"
        assert data['resultado'] == "nao_conforme", f"Expected nao_conforme, got {data.get('resultado')}"
        assert data.get('data_conclusao') is not None
        # Auto-OS
        os_id = data.get('os_gerada_id')
        assert os_id, f"Expected os_gerada_id to be set, got {os_id}"
        # Verify OS exists
        os_r = auth.get(f"{API}/ordens-servico/{os_id}")
        assert os_r.status_code == 200, f"OS not found: {os_r.status_code} {os_r.text}"
        os_data = os_r.json()
        assert os_data['tipo'] == "corretiva"
        assert os_data.get('inspecao_origem_id') == data['id']

    def test_inspecao_without_responses_stays_pendente(self, auth, test_ativo):
        # No checklist provided -> defaults filled but no responses
        payload = {
            "ativo_id": test_ativo['id'],
            "tipo": "mecanica",
            "frequencia": "diaria"
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data['status'] == "pendente", f"Expected pendente, got {data.get('status')}"
        assert data['resultado'] == "pendente"
        assert data.get('data_conclusao') is None

    def test_inspecao_lubrificacao_with_responses_auto_concludes(self, auth, test_ativo):
        checklist = [
            {"id": str(uuid.uuid4()), "descricao": "Ponto acessível", "tipo": "boolean", "obrigatorio": True, "conforme": True, "valor": None, "observacao": None},
            {"id": str(uuid.uuid4()), "descricao": "Lubrificante aplicado", "tipo": "boolean", "obrigatorio": True, "conforme": True, "valor": None, "observacao": None},
        ]
        payload = {
            "ativo_id": test_ativo['id'],
            "tipo": "lubrificacao",
            "frequencia": "diaria",
            "checklist": checklist
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        # Verify user checklist was preserved (not overridden by default lubrificacao)
        assert len(data['checklist']) == 2, f"Expected user checklist preserved, got {len(data['checklist'])} items"
        assert data['status'] == "concluida"
        assert data['resultado'] == "conforme"
