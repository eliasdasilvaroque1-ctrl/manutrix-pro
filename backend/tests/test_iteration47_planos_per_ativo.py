"""
Iteration 47 — Test refactored PlanosInspecao (per-ATIVO) + auto-load on Inspecao creation.

Scope (per review_request):
- POST /api/planos-inspecao (new field types: tipo_campo, obrigatoria, foto_obrigatoria, valor_min/max, unidade, ordem)
- GET /api/planos-inspecao?ativo_id=
- GET /api/planos-inspecao/por-ativo/{ativo_id}
- GET /api/planos-inspecao/resolver?ativo_id=&tipo=
- GET /api/planos-inspecao/categorias-disponiveis?ativo_id=
- PUT /api/planos-inspecao/{id}
- DELETE /api/planos-inspecao/{id} (soft delete)
- POST /api/inspecoes auto-loads plan (plano_id, plano_nome populated, checklist matches perguntas)
- POST /api/inspecoes with tipo=mecanica (backward compat) works
- POST /api/inspecoes with tipo=lubrificacao works
- POST /api/inspecoes for ativo WITHOUT plan -> minimal default checklist (no error)
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"no token in {data}"
    return tok


@pytest.fixture(scope="module")
def auth(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def ativo_id(auth):
    """Get or create an ativo for testing."""
    r = auth.get(f"{API}/ativos")
    assert r.status_code == 200
    ativos = r.json()
    if ativos:
        return ativos[0]["id"]
    # create one
    r = auth.post(f"{API}/ativos", json={
        "tag": f"TEST-AV-{uuid.uuid4().hex[:6]}",
        "nome": "Test Ativo",
        "tipo_equipamento": "motor",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def ativo_sem_plano(auth):
    """Create an ativo guaranteed to have no plan."""
    # Need a sector_id; try to find one from existing assets or sectors API
    sector_id = None
    r = auth.get(f"{API}/sectors")
    if r.status_code == 200 and r.json():
        sector_id = r.json()[0].get("id")
    if not sector_id:
        # fallback: use any existing ativo's sector
        r2 = auth.get(f"{API}/ativos")
        if r2.status_code == 200 and r2.json():
            sector_id = r2.json()[0].get("sector_id")
    payload = {
        "tag": f"TEST-NOPLAN-{uuid.uuid4().hex[:6]}",
        "nome": "Test Ativo Sem Plano",
        "tipo_equipamento": f"tipo-unico-{uuid.uuid4().hex[:6]}",
    }
    if sector_id:
        payload["sector_id"] = sector_id
    r = auth.post(f"{API}/ativos", json=payload)
    if r.status_code not in (200, 201):
        pytest.skip(f"could not create test ativo without plan: {r.status_code} {r.text}")
    return r.json()["id"]


# ---------- PlanosInspecao CRUD ----------
class TestPlanosInspecaoCRUD:
    created_ids = []

    def test_01_create_plano_inspecao(self, auth, ativo_id):
        payload = {
            "nome": "TEST_Plano Inspecao Mecanica",
            "tipo": "inspecao",
            "ativo_id": ativo_id,
            "frequencia": "mensal",
            "disciplina": "mecanica",
            "status": "ativo",
            "versao": 1,
            "perguntas": [
                {"texto": "Verificar vibração", "tipo_campo": "escala_4", "obrigatoria": True,
                 "foto_obrigatoria": False, "ordem": 1},
                {"texto": "Temperatura mancal", "tipo_campo": "numero", "obrigatoria": True,
                 "valor_min": 30, "valor_max": 80, "unidade": "C", "ordem": 2},
                {"texto": "Há ruído anormal?", "tipo_campo": "boolean", "obrigatoria": True,
                 "foto_obrigatoria": True, "ordem": 3},
                {"texto": "Observações gerais", "tipo_campo": "texto", "obrigatoria": False, "ordem": 4},
                {"texto": "Selecione condição", "tipo_campo": "lista", "obrigatoria": True,
                 "opcoes": ["Bom", "Regular", "Ruim"], "ordem": 5},
            ]
        }
        r = auth.post(f"{API}/planos-inspecao", json=payload)
        assert r.status_code == 200, r.text
        plano = r.json()
        assert plano["nome"] == payload["nome"]
        assert plano["tipo"] == "inspecao"
        assert plano["ativo_id"] == ativo_id
        assert plano["frequencia"] == "mensal"
        assert plano["status"] == "ativo"
        assert len(plano["perguntas"]) == 5
        # field types preserved
        p0 = plano["perguntas"][0]
        assert p0["texto"] == "Verificar vibração"
        assert p0["tipo_campo"] == "escala_4"
        assert p0["obrigatoria"] is True
        p1 = plano["perguntas"][1]
        assert p1["valor_min"] == 30
        assert p1["valor_max"] == 80
        assert p1["unidade"] == "C"
        # _id excluded
        assert "_id" not in plano
        TestPlanosInspecaoCRUD.created_ids.append(plano["id"])

    def test_02_create_plano_lubrificacao(self, auth, ativo_id):
        payload = {
            "nome": "TEST_Plano Lubrificacao",
            "tipo": "lubrificacao",
            "ativo_id": ativo_id,
            "frequencia": "semanal",
            "status": "ativo",
            "perguntas": [
                {"texto": "Tipo de lubrificante", "tipo_campo": "texto", "obrigatoria": True, "ordem": 1},
                {"texto": "Quantidade aplicada (g)", "tipo_campo": "numero", "unidade": "g", "ordem": 2},
            ]
        }
        r = auth.post(f"{API}/planos-inspecao", json=payload)
        assert r.status_code == 200, r.text
        plano = r.json()
        assert plano["tipo"] == "lubrificacao"
        TestPlanosInspecaoCRUD.created_ids.append(plano["id"])

    def test_03_list_planos_filter_by_ativo(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao", params={"ativo_id": ativo_id})
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        # both planos we created should be returned
        ids = {p["id"] for p in planos}
        for cid in TestPlanosInspecaoCRUD.created_ids:
            assert cid in ids, f"created plano {cid} missing from list"

    def test_04_planos_por_ativo(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao/por-ativo/{ativo_id}")
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        ids = {p["id"] for p in planos}
        for cid in TestPlanosInspecaoCRUD.created_ids:
            assert cid in ids

    def test_05_resolver_plano_inspecao(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao/resolver",
                     params={"ativo_id": ativo_id, "tipo": "inspecao"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["plano"] is not None, f"resolver returned no plano: {data}"
        assert data["plano"]["tipo"] == "inspecao"
        assert data["fonte"] == "ativo"
        assert len(data["perguntas"]) == 5

    def test_06_resolver_plano_lubrificacao(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao/resolver",
                     params={"ativo_id": ativo_id, "tipo": "lubrificacao"})
        assert r.status_code == 200
        data = r.json()
        assert data["plano"] is not None
        assert data["plano"]["tipo"] == "lubrificacao"

    def test_07_categorias_disponiveis(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao/categorias-disponiveis",
                     params={"ativo_id": ativo_id})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        tipos = {c["tipo"]: c for c in data}
        # expected 5 tipos
        for t in ["inspecao", "preventiva", "lubrificacao", "limpeza", "melhoria"]:
            assert t in tipos, f"tipo {t} missing"
        assert tipos["inspecao"]["disponivel"] is True
        assert tipos["lubrificacao"]["disponivel"] is True
        assert tipos["preventiva"]["disponivel"] is False  # no plan of this tipo
        assert tipos["limpeza"]["disponivel"] is False
        assert tipos["melhoria"]["disponivel"] is False

    def test_08_update_plano(self, auth):
        plano_id = TestPlanosInspecaoCRUD.created_ids[0]
        payload = {
            "nome": "TEST_Plano Atualizado",
            "perguntas": [
                {"texto": "Pergunta atualizada", "tipo_campo": "boolean", "obrigatoria": True, "ordem": 1},
            ]
        }
        r = auth.put(f"{API}/planos-inspecao/{plano_id}", json=payload)
        assert r.status_code == 200, r.text
        updated = r.json()
        assert updated["nome"] == "TEST_Plano Atualizado"
        assert len(updated["perguntas"]) == 1
        assert updated["perguntas"][0]["texto"] == "Pergunta atualizada"


# ---------- Inspecao auto-load ----------
class TestInspecaoAutoLoad:
    created_inspecoes = []

    def test_01_create_inspecao_loads_plan_checklist(self, auth, ativo_id):
        """POST /inspecoes with tipo=lubrificacao auto-loads plan and populates plano_id."""
        payload = {
            "ativo_id": ativo_id,
            "tipo": "lubrificacao",
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code == 200, r.text
        insp = r.json()
        assert insp["tipo"] == "lubrificacao"
        assert insp["plano_id"] is not None, f"plano_id should be populated: {insp}"
        assert insp["plano_nome"] is not None, f"plano_nome should be populated: {insp}"
        # checklist should match plan perguntas (2 items)
        assert len(insp["checklist"]) == 2, f"expected 2 checklist items, got {len(insp['checklist'])}"
        # checklist items should have descricao/tipo
        item0 = insp["checklist"][0]
        assert "descricao" in item0
        assert "tipo" in item0
        TestInspecaoAutoLoad.created_inspecoes.append(insp["id"])

    def test_02_create_inspecao_backward_compat_mecanica(self, auth, ativo_id):
        """tipo=mecanica (backward compat) still works."""
        payload = {
            "ativo_id": ativo_id,
            "tipo": "mecanica",
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code == 200, r.text
        insp = r.json()
        assert insp["tipo"] == "mecanica"
        # Either auto-loaded a plan or fell back to default checklist — must not error
        assert isinstance(insp["checklist"], list)
        assert len(insp["checklist"]) >= 1
        TestInspecaoAutoLoad.created_inspecoes.append(insp["id"])

    def test_03_create_inspecao_sem_plano_uses_default(self, auth, ativo_sem_plano):
        """Ativo without plan -> minimal default checklist (2 items), no error."""
        payload = {
            "ativo_id": ativo_sem_plano,
            "tipo": "inspecao",
        }
        r = auth.post(f"{API}/inspecoes", json=payload)
        assert r.status_code == 200, r.text
        insp = r.json()
        assert insp["plano_id"] is None
        assert insp["plano_nome"] is None
        assert isinstance(insp["checklist"], list)
        assert len(insp["checklist"]) >= 2  # default minimal
        TestInspecaoAutoLoad.created_inspecoes.append(insp["id"])

    def test_04_get_inspecao_persists_plano_fields(self, auth):
        """Verify plano_id is persisted by reading back the inspection."""
        if not TestInspecaoAutoLoad.created_inspecoes:
            pytest.skip("no inspecoes created")
        insp_id = TestInspecaoAutoLoad.created_inspecoes[0]
        r = auth.get(f"{API}/inspecoes/{insp_id}")
        assert r.status_code == 200, r.text
        insp = r.json()
        assert insp["plano_id"] is not None
        assert insp["plano_nome"] is not None
        assert insp["tipo"] == "lubrificacao"


# ---------- Cleanup: soft-delete + verify ----------
class TestPlanoCleanup:
    def test_01_delete_plano_soft_deletes(self, auth):
        if not TestPlanosInspecaoCRUD.created_ids:
            pytest.skip("nothing to delete")
        for plano_id in TestPlanosInspecaoCRUD.created_ids:
            r = auth.delete(f"{API}/planos-inspecao/{plano_id}")
            assert r.status_code == 200, r.text
            assert r.json().get("success") is True

    def test_02_deleted_plano_not_in_list(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao", params={"ativo_id": ativo_id})
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        for cid in TestPlanosInspecaoCRUD.created_ids:
            assert cid not in ids, f"deleted plano {cid} still in list"

    def test_03_resolver_returns_none_after_delete(self, auth, ativo_id):
        r = auth.get(f"{API}/planos-inspecao/resolver",
                     params={"ativo_id": ativo_id, "tipo": "inspecao"})
        assert r.status_code == 200
        # may still return another plan from another ativo via tipo_equipamento fallback,
        # but the specific one we created should be gone (or plano None)
        data = r.json()
        if data["plano"]:
            assert data["plano"]["id"] not in TestPlanosInspecaoCRUD.created_ids


# ---------- Regression smoke ----------
class TestRegressionSmoke:
    def test_login_admin(self, session):
        r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200

    def test_dashboard_kpis(self, auth):
        # Try common dashboard endpoints
        for path in ["/dashboard/kpis", "/dashboard", "/dashboard/stats"]:
            r = auth.get(f"{API}{path}")
            if r.status_code == 200:
                return
        pytest.skip("no dashboard endpoint available")

    def test_ordens_servico(self, auth):
        r = auth.get(f"{API}/ordens-servico")
        assert r.status_code == 200

    def test_ativos(self, auth):
        r = auth.get(f"{API}/ativos")
        assert r.status_code == 200

    def test_metricas_equipe(self, auth):
        r = auth.get(f"{API}/metricas/equipe")
        assert r.status_code == 200
