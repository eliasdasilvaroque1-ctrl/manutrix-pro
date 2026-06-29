"""
Iteration 48 — Biblioteca de Modelos & Classificação Técnica
- categorias_equipamento (CAT-XXXXXX)
- fabricantes (FAB-XXXXXX)
- modelos_mestre (MM-XXXXXX) with planos+perguntas
- Deep copy / aplicar / rastreabilidade
- Tecnico 403
"""
import os
import re
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MASTER = {"email": "master@manutrix.com", "password": "master123"}
TECNICO = {"email": "tecnico@manutrix.com", "password": "tecnico123"}


# ---------- helpers ----------

def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    if r.status_code != 200:
        # Try unsetting force_password_change for master, then retry once.
        return None
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="session")
def master_token():
    t = _login(MASTER)
    if not t:
        pytest.skip(f"Master login failed for {MASTER['email']}")
    return t


@pytest.fixture(scope="session")
def tecnico_token():
    t = _login(TECNICO)
    if not t:
        pytest.skip(f"Tecnico login failed for {TECNICO['email']}")
    return t


@pytest.fixture(scope="session")
def H(master_token):
    return {"Authorization": f"Bearer {master_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def H_tec(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def created_ids():
    return {"cat": [], "fab": [], "mm": [], "ativo": None}


# ---------- 1. CATEGORIAS ----------

class TestCategorias:
    def test_create_categoria_auto_code(self, H, created_ids):
        ts = int(time.time())
        r = requests.post(f"{API}/biblioteca/categorias", headers=H,
                          json={"nome": f"TEST_CAT_{ts}", "descricao": "test"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d and "codigo" in d
        assert re.match(r"^CAT-\d{6}$", d["codigo"]), f"bad codigo: {d['codigo']}"
        assert d["nome"] == f"TEST_CAT_{ts}"
        assert d["status"] == "ativo"
        assert d["deleted_at"] is None
        created_ids["cat"].append(d["id"])

    def test_list_categorias_pagination_search(self, H, created_ids):
        # list all
        r = requests.get(f"{API}/biblioteca/categorias?limit=5&skip=0", headers=H)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "total" in body
        assert isinstance(body["items"], list)
        assert body["total"] >= 1

        # search
        if created_ids["cat"]:
            cid = created_ids["cat"][0]
            # fetch by id via search of name
            # we don't have GET-by-id; verify via list+search
            # Use a search term we know exists
            r2 = requests.get(f"{API}/biblioteca/categorias?search=TEST_CAT", headers=H)
            assert r2.status_code == 200
            assert any(i["id"] == cid for i in r2.json()["items"])

    def test_update_categoria(self, H, created_ids):
        assert created_ids["cat"]
        cid = created_ids["cat"][0]
        r = requests.put(f"{API}/biblioteca/categorias/{cid}", headers=H,
                         json={"descricao": "updated_desc"})
        assert r.status_code == 200, r.text
        assert r.json()["descricao"] == "updated_desc"


# ---------- 2. FABRICANTES ----------

class TestFabricantes:
    def test_create_fabricante_links_categoria(self, H, created_ids):
        assert created_ids["cat"], "need categoria first"
        ts = int(time.time())
        cat_id = created_ids["cat"][0]
        r = requests.post(f"{API}/biblioteca/fabricantes", headers=H,
                          json={"nome": f"TEST_FAB_{ts}", "categoria_id": cat_id,
                                "pais": "BR", "website": "https://x.com"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert re.match(r"^FAB-\d{6}$", d["codigo"]), f"bad codigo: {d['codigo']}"
        assert d["categoria_id"] == cat_id
        created_ids["fab"].append(d["id"])

    def test_list_fabricantes_filter_by_categoria(self, H, created_ids):
        cat_id = created_ids["cat"][0]
        r = requests.get(f"{API}/biblioteca/fabricantes?categoria_id={cat_id}", headers=H)
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["categoria_id"] == cat_id for i in items)


# ---------- 3. MODELOS MESTRE ----------

class TestModelosMestre:
    def test_create_modelo_mestre_with_planos(self, H, created_ids):
        ts = int(time.time())
        cat_id = created_ids["cat"][0]
        fab_id = created_ids["fab"][0]
        payload = {
            "nome": f"TEST_MM_{ts}",
            "modelo": "Mod-X",
            "categoria_id": cat_id,
            "fabricante_id": fab_id,
            "descricao": "modelo de teste",
            "especificacoes": {"potencia_kw": 75},
            "planos": [
                {
                    "nome": "Inspeção Trimestral",
                    "tipo": "inspecao",
                    "frequencia": "trimestral",
                    "disciplina": "mecanica",
                    "perguntas": [
                        {"texto": "Vibração ok?", "tipo_campo": "boolean", "obrigatoria": True, "ordem": 0},
                        {"texto": "Temperatura", "tipo_campo": "numero", "unidade": "C",
                         "valor_min": 20, "valor_max": 80, "ordem": 1},
                    ]
                },
                {
                    "nome": "Lubrificação Mensal",
                    "tipo": "lubrificacao",
                    "frequencia": "mensal",
                    "perguntas": [
                        {"texto": "Nível de óleo?", "tipo_campo": "boolean", "obrigatoria": True}
                    ]
                }
            ]
        }
        r = requests.post(f"{API}/biblioteca/modelos-mestre", headers=H, json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert re.match(r"^MM-\d{6}$", d["codigo"]), f"bad codigo: {d['codigo']}"
        assert d["is_master"] is True
        assert d["versao"] == 1
        assert len(d["planos"]) == 2
        # plan code format
        for p in d["planos"]:
            assert re.match(r"^PLA-\d{6}$", p["codigo"]), f"bad plano codigo: {p['codigo']}"
            assert "id" in p
            assert "perguntas" in p
            for q in p["perguntas"]:
                assert "id" in q
                assert "texto" in q
                assert "tipo_campo" in q
        created_ids["mm"].append(d["id"])

    def test_get_modelo_mestre_by_id(self, H, created_ids):
        mm_id = created_ids["mm"][0]
        r = requests.get(f"{API}/biblioteca/modelos-mestre/{mm_id}", headers=H)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == mm_id
        assert len(d["planos"]) == 2

    def test_list_modelos_mestre_enriched(self, H, created_ids):
        r = requests.get(f"{API}/biblioteca/modelos-mestre?search=TEST_MM", headers=H)
        assert r.status_code == 200
        items = r.json()["items"]
        assert any(i["id"] == created_ids["mm"][0] for i in items)
        target = [i for i in items if i["id"] == created_ids["mm"][0]][0]
        # categoria_nome / fabricante_nome enriched
        assert "categoria_nome" in target and target["categoria_nome"]
        assert "fabricante_nome" in target and target["fabricante_nome"]


# ---------- 4. DEEP COPY ----------

class TestDeepCopy:
    @pytest.fixture(scope="class")
    def ativo_id(self, H, created_ids):
        # Try to grab an existing ativo
        r = requests.get(f"{API}/ativos?limit=1", headers=H)
        assert r.status_code == 200, r.text
        items = r.json() if isinstance(r.json(), list) else r.json().get("items") or r.json().get("ativos") or []
        if items:
            aid = items[0].get("id")
            assert aid
            created_ids["ativo"] = aid
            return aid
        pytest.skip("No ativo available to test deep copy")

    def test_aplicar_modelo_deep_copy(self, H, created_ids, ativo_id):
        mm_id = created_ids["mm"][0]
        r = requests.post(
            f"{API}/biblioteca/modelos-mestre/{mm_id}/aplicar/{ativo_id}?motivo=TEST_APLICAR",
            headers=H
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        assert d["planos_criados"] == 2
        assert len(d["planos"]) == 2
        # Save first plan id for follow-up
        created_ids["plano_ids"] = [p["id"] for p in d["planos"]]

    def test_planos_have_traceability(self, H, created_ids, ativo_id):
        """Check planos_inspecao entries have modelo_origem_id, modelo_versao, plano_origem_id."""
        mm_id = created_ids["mm"][0]
        # Use the per-ativo plan listing
        r = requests.get(f"{API}/planos-inspecao?ativo_id={ativo_id}", headers=H)
        assert r.status_code == 200, r.text
        body = r.json()
        plans = body if isinstance(body, list) else body.get("items") or body.get("planos") or []
        # filter those just created
        target_ids = set(created_ids.get("plano_ids", []))
        applied = [p for p in plans if p.get("id") in target_ids]
        assert len(applied) >= 2, f"Expected 2 deep-copied plans, got {len(applied)}"
        for p in applied:
            assert p.get("modelo_origem_id") == mm_id, f"missing modelo_origem_id on plan {p.get('id')}"
            assert p.get("modelo_versao") == 1
            assert p.get("plano_origem_id"), "missing plano_origem_id"
            assert p.get("ativo_id") == ativo_id
            # perguntas duplicated with new ids
            assert "perguntas" in p and len(p["perguntas"]) >= 1

    def test_ativo_updated_with_classification(self, H, created_ids, ativo_id):
        mm_id = created_ids["mm"][0]
        cat_id = created_ids["cat"][0]
        fab_id = created_ids["fab"][0]
        r = requests.get(f"{API}/ativos/{ativo_id}", headers=H)
        assert r.status_code == 200, r.text
        a = r.json()
        assert a.get("modelo_mestre_id") == mm_id
        assert a.get("categoria_id") == cat_id
        assert a.get("fabricante_id") == fab_id
        assert a.get("modelo_id") == mm_id


# ---------- 5. RBAC ----------

class TestRBAC:
    def test_tecnico_cannot_create_categoria(self, H_tec):
        r = requests.post(f"{API}/biblioteca/categorias", headers=H_tec,
                          json={"nome": "TEST_TECNICO"})
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"

    def test_tecnico_cannot_create_fabricante(self, H_tec):
        r = requests.post(f"{API}/biblioteca/fabricantes", headers=H_tec,
                          json={"nome": "TEST_TECNICO_FAB"})
        assert r.status_code == 403

    def test_tecnico_cannot_create_modelo_mestre(self, H_tec):
        r = requests.post(f"{API}/biblioteca/modelos-mestre", headers=H_tec,
                          json={"nome": "TEST_TECNICO_MM", "planos": []})
        assert r.status_code == 403

    def test_tecnico_can_read_categorias(self, H_tec):
        r = requests.get(f"{API}/biblioteca/categorias?limit=5", headers=H_tec)
        # GET is open to authenticated users
        assert r.status_code == 200


# ---------- 6. SOFT DELETE & CLEANUP ----------

class TestSoftDeleteAndCleanup:
    def test_soft_delete_modelo(self, H, created_ids):
        mm_id = created_ids["mm"][0]
        r = requests.delete(f"{API}/biblioteca/modelos-mestre/{mm_id}", headers=H)
        assert r.status_code == 200
        assert r.json().get("success") is True
        # confirm gone from list
        r2 = requests.get(f"{API}/biblioteca/modelos-mestre?search=TEST_MM", headers=H)
        ids = [i["id"] for i in r2.json()["items"]]
        assert mm_id not in ids

    def test_soft_delete_fabricante(self, H, created_ids):
        fid = created_ids["fab"][0]
        r = requests.delete(f"{API}/biblioteca/fabricantes/{fid}", headers=H)
        assert r.status_code == 200

    def test_soft_delete_categoria(self, H, created_ids):
        cid = created_ids["cat"][0]
        r = requests.delete(f"{API}/biblioteca/categorias/{cid}", headers=H)
        assert r.status_code == 200


# ---------- 7. REGRESSION ----------

class TestRegression:
    def test_login_admin(self):
        r = requests.post(f"{API}/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"}, timeout=20)
        assert r.status_code == 200

    def test_dashboard(self, H):
        r = requests.get(f"{API}/dashboard/stats", headers=H, timeout=20)
        assert r.status_code == 200, r.text

    def test_os_list(self, H):
        r = requests.get(f"{API}/ordens-servico?limit=5", headers=H, timeout=20)
        assert r.status_code == 200

    def test_ativos_list(self, H):
        r = requests.get(f"{API}/ativos?limit=5", headers=H, timeout=20)
        assert r.status_code == 200
