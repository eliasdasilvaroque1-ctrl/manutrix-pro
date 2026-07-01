"""Iteration 53: Plan usability improvements + Central sem_data bug fix retest."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

MASTER_EMAIL = "master@manutrix.com"
MASTER_PASSWORD = "master123"
OPERADOR_EMAIL = "test.operador@maintrix.com"
OPERADOR_PASSWORD = "op123"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def master_token():
    return _login(MASTER_EMAIL, MASTER_PASSWORD)


@pytest.fixture(scope="module")
def master_headers(master_token):
    return {"Authorization": f"Bearer {master_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def operador_token():
    return _login(OPERADOR_EMAIL, OPERADOR_PASSWORD)


@pytest.fixture(scope="module")
def operador_headers(operador_token):
    return {"Authorization": f"Bearer {operador_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def first_ativo(master_headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=master_headers, timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0, "Need at least one ativo for testing"
    # Prefer AV-01 if exists
    for a in ativos:
        if a.get("tag") == "AV-01":
            return a
    return ativos[0]


class TestListPlanosEnrichment:
    """GET /api/planos-inspecao returns plans enriched with hierarchy."""

    def test_list_planos_returns_hierarchy_fields(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, timeout=30)
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        # Must have at least one plan linked to an ativo (per problem statement: AV-01)
        planos_com_ativo = [p for p in planos if p.get("ativo_id")]
        assert len(planos_com_ativo) > 0, "Expected at least one plan linked to an ativo"
        for p in planos_com_ativo:
            # New enrichment fields must exist
            assert "ativo_tag" in p, f"Missing ativo_tag in plan {p.get('id')}"
            assert "ativo_nome" in p, f"Missing ativo_nome in plan {p.get('id')}"
            assert "area_nome" in p, f"Missing area_nome in plan {p.get('id')}"
        # Verify a plan for AV-01 has correct enrichment
        av01_plans = [p for p in planos_com_ativo if p.get("ativo_tag") == "AV-01"]
        if av01_plans:
            plan = av01_plans[0]
            assert plan["ativo_tag"] == "AV-01"
            assert plan["ativo_nome"], "ativo_nome should not be empty"
            assert plan["area_nome"], "area_nome should not be empty"


class TestDuplicateValidation:
    """POST /api/planos-inspecao duplicate check (tipo+disciplina+ativo)."""

    _created_ids = []

    def test_create_baseline_plan(self, master_headers, first_ativo):
        # Use 'eletrica' to avoid clashing with pre-seeded mecanica plans on AV-01
        payload = {
            "nome": "TEST_Plan_Baseline_Dup",
            "tipo": "lubrificacao",
            "disciplina": "eletrica",
            "ativo_id": first_ativo["id"],
            "status": "rascunho",
            "perguntas": []
        }
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        # May already exist -> 409, if so cleanup previous and retry
        if r.status_code == 409:
            # Fetch and delete existing duplicate
            det = r.json().get("detail", {})
            eid = det.get("existing_plan_id")
            if eid:
                requests.delete(f"{BASE_URL}/api/planos-inspecao/{eid}", headers=master_headers, timeout=30)
            r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        assert r.status_code == 200, f"Baseline create failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["nome"] == "TEST_Plan_Baseline_Dup"
        assert data["ativo_id"] == first_ativo["id"]
        assert data["tipo"] == "lubrificacao"
        assert data["disciplina"] == "eletrica"
        TestDuplicateValidation._created_ids.append(data["id"])

    def test_duplicate_returns_409(self, master_headers, first_ativo):
        payload = {
            "nome": "TEST_Plan_Duplicate_Attempt",
            "tipo": "lubrificacao",
            "disciplina": "eletrica",
            "ativo_id": first_ativo["id"],
            "status": "rascunho",
            "perguntas": []
        }
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
        body = r.json()
        # FastAPI wraps HTTPException detail
        detail = body.get("detail", body)
        assert detail.get("action_required") == "duplicate_conflict"
        assert "existing_plan_id" in detail
        assert "existing_plan_nome" in detail

    def test_force_override_bypasses_check(self, master_headers, first_ativo):
        payload = {
            "nome": "TEST_Plan_ForceOverride",
            "tipo": "lubrificacao",
            "disciplina": "eletrica",
            "ativo_id": first_ativo["id"],
            "status": "rascunho",
            "force_override": True,
            "perguntas": []
        }
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        assert r.status_code == 200, f"force_override should bypass check: {r.status_code} {r.text}"
        data = r.json()
        assert data["nome"] == "TEST_Plan_ForceOverride"
        TestDuplicateValidation._created_ids.append(data["id"])

    def test_generic_plan_no_ativo_no_dup_check(self, master_headers):
        # Create two generic plans (ativo_id=None) with same tipo+disciplina — both should succeed
        payload = {
            "nome": "TEST_Plan_Generic_1",
            "tipo": "inspecao",
            "disciplina": "mecanica",
            "tipo_equipamento": "Motor",
            "status": "rascunho",
            "perguntas": []
        }
        r1 = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        assert r1.status_code == 200
        TestDuplicateValidation._created_ids.append(r1.json()["id"])

        payload["nome"] = "TEST_Plan_Generic_2"
        r2 = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=master_headers, json=payload, timeout=30)
        assert r2.status_code == 200, f"Generic plan (no ativo_id) should not trigger dup check: {r2.status_code} {r2.text}"
        TestDuplicateValidation._created_ids.append(r2.json()["id"])

    @classmethod
    def teardown_class(cls):
        # Cleanup TEST_ plans
        try:
            t = _login(MASTER_EMAIL, MASTER_PASSWORD)
            h = {"Authorization": f"Bearer {t}"}
            for pid in cls._created_ids:
                requests.delete(f"{BASE_URL}/api/planos-inspecao/{pid}", headers=h, timeout=30)
        except Exception as e:
            print(f"Cleanup error: {e}")


class TestPlanosPorAtivo:
    """GET /api/planos-inspecao/por-ativo/{id} returns only approved plans."""

    def test_por_ativo_returns_only_approved(self, master_headers, first_ativo):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao/por-ativo/{first_ativo['id']}", headers=master_headers, timeout=30)
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        for p in planos:
            assert p.get("status") == "aprovado", f"Plan {p.get('id')} has status {p.get('status')} - should be 'aprovado'"

    def test_por_ativo_invalid_id_returns_empty(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/planos-inspecao/por-ativo/nonexistent-id-xyz", headers=master_headers, timeout=30)
        assert r.status_code == 200
        assert r.json() == []


class TestCentralOperadorSemDataFix:
    """Bug fix retest: GET /api/central sem_data does not leak restricted disciplines for operador."""

    def test_operador_sem_data_no_restricted_disciplines(self, operador_headers):
        r = requests.get(f"{BASE_URL}/api/central", headers=operador_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("role") == "operador"
        sem_data = data.get("sem_data", {})
        os_list = sem_data.get("os", [])
        # Operador should ONLY see producao/civil disciplines
        restricted = {"mecanica", "eletrica", "instrumentacao"}
        leaked = [o for o in os_list if o.get("disciplina") in restricted]
        assert not leaked, f"Operador sem_data leaks {len(leaked)} restricted OS: {[(o.get('id'), o.get('disciplina')) for o in leaked]}"

    def test_operador_all_sections_no_restricted(self, operador_headers):
        r = requests.get(f"{BASE_URL}/api/central", headers=operador_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        restricted = {"mecanica", "eletrica", "instrumentacao"}
        for section in ("vencidas", "hoje", "semana", "em_execucao", "sem_data"):
            sec = data.get(section, {})
            os_list = sec.get("os", [])
            leaked = [o for o in os_list if o.get("disciplina") in restricted]
            assert not leaked, f"Section {section} leaks: {[(o.get('id'), o.get('disciplina')) for o in leaked]}"
