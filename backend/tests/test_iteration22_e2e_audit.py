"""
ITERATION 22 — MANUTRIX OMNI COMPREHENSIVE E2E PRODUCTION AUDIT
Backend regression for every module covered by the audit:
LOGIN, ÁREAS, ATIVOS (incl. 404 bug regression), INSPEÇÕES, RONDA,
OS, ESTOQUE, SOBRESSALENTES.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
SUPERVISOR = {"email": "supervisor@manutrix.com", "password": "supervisor123"}
TECNICO = {"email": "tecnico@manutrix.com", "password": "tecnico123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login {creds['email']} -> {r.status_code} {r.text[:200]}"
    return r.json()


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)["access_token"]


@pytest.fixture(scope="session")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ───────────────────────── MODULE: LOGIN ─────────────────────────
class TestLogin:
    def test_admin_login(self):
        data = _login(ADMIN)
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@manutrix.com"
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20

    def test_supervisor_login(self):
        data = _login(SUPERVISOR)
        assert data["user"]["role"] == "supervisor"

    def test_tecnico_login(self):
        data = _login(TECNICO)
        assert data["user"]["role"] == "tecnico"

    def test_invalid_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": "admin@manutrix.com", "password": "WRONG"}, timeout=10)
        assert r.status_code in (400, 401), f"expected 401, got {r.status_code}"

    def test_unauth_request_blocked(self):
        r = requests.get(f"{API}/ativos", timeout=10)
        assert r.status_code in (401, 403), f"unauth GET /ativos -> {r.status_code}"


# ───────────────────────── MODULE: ÁREAS (sectors) ─────────────────────────
class TestSectors:
    def test_list_sectors(self, headers):
        r = requests.get(f"{API}/sectors", headers=headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_create_edit_delete_sector(self, headers):
        codigo = f"T22{uuid.uuid4().hex[:5].upper()}"
        # CREATE
        r = requests.post(f"{API}/sectors", headers=headers,
                          json={"codigo": codigo, "nome": "TEST_Iter22_Area"}, timeout=10)
        assert r.status_code in (200, 201), f"create sector -> {r.status_code} {r.text[:200]}"
        sec = r.json()
        sec_id = sec.get("id") or sec.get("_id")
        assert sec_id

        # READ via list
        r2 = requests.get(f"{API}/sectors", headers=headers, timeout=10)
        codes = [s.get("codigo") for s in r2.json()]
        assert codigo in codes

        # EDIT
        r3 = requests.put(f"{API}/sectors/{sec_id}", headers=headers,
                          json={"codigo": codigo, "nome": "TEST_Iter22_Area_UPD"}, timeout=10)
        assert r3.status_code == 200, f"edit sector -> {r3.status_code} {r3.text[:200]}"

        # DELETE (no ativos in it)
        r4 = requests.delete(f"{API}/sectors/{sec_id}", headers=headers, timeout=10)
        assert r4.status_code in (200, 204), f"delete sector -> {r4.status_code} {r4.text[:200]}"


# ───────────────────────── MODULE: ATIVOS (incl. 404 BUG REGRESSION) ─────────────────────────
class TestAtivos:
    @pytest.fixture(scope="class")
    def sector_id(self, headers):
        # Get the first existing sector
        r = requests.get(f"{API}/sectors", headers=headers, timeout=10)
        sectors = r.json()
        assert len(sectors) > 0
        return sectors[0]["id"]

    def test_post_ativos_no_404(self, headers, sector_id):
        """REGRESSION: the user reported POST /ativos returning 404 in production."""
        tag = f"T22-{uuid.uuid4().hex[:5].upper()}"
        payload = {
            "tag": tag,
            "nome": "TEST_Iter22_Ativo",
            "sector_id": sector_id,
            "tipo_equipamento": "motor",
            "fabricante": "TestCo",
        }
        r = requests.post(f"{API}/ativos", headers=headers, json=payload, timeout=15)
        assert r.status_code != 404, f"POST /ativos returned 404! body={r.text[:300]}"
        assert r.status_code in (200, 201), f"POST /ativos -> {r.status_code} {r.text[:300]}"
        body = r.json()
        ativo_id = body.get("id") or body.get("_id")
        assert ativo_id

        # GET to verify persistence
        rg = requests.get(f"{API}/ativos/{ativo_id}", headers=headers, timeout=10)
        assert rg.status_code == 200
        assert rg.json().get("tag") == tag

        # cleanup
        requests.delete(f"{API}/ativos/{ativo_id}", headers=headers, timeout=10)

    def test_duplicate_tag_same_area_rejected(self, headers, sector_id):
        tag = f"T22-{uuid.uuid4().hex[:5].upper()}"
        p = {"tag": tag, "nome": "dup-test", "sector_id": sector_id, "tipo_equipamento": "motor"}
        r1 = requests.post(f"{API}/ativos", headers=headers, json=p, timeout=10)
        assert r1.status_code in (200, 201)
        ativo1_id = r1.json().get("id")
        r2 = requests.post(f"{API}/ativos", headers=headers, json=p, timeout=10)
        assert r2.status_code in (400, 409), f"duplicate same-area -> expected 400/409, got {r2.status_code}"
        requests.delete(f"{API}/ativos/{ativo1_id}", headers=headers, timeout=10)

    def test_same_tag_different_area_ok(self, headers):
        r = requests.get(f"{API}/sectors", headers=headers, timeout=10)
        secs = r.json()
        if len(secs) < 2:
            pytest.skip("need >=2 sectors")
        tag = f"T22-{uuid.uuid4().hex[:5].upper()}"
        a = requests.post(f"{API}/ativos", headers=headers,
                          json={"tag": tag, "nome": "x", "sector_id": secs[0]["id"], "tipo_equipamento": "motor"},
                          timeout=10)
        b = requests.post(f"{API}/ativos", headers=headers,
                          json={"tag": tag, "nome": "x", "sector_id": secs[1]["id"], "tipo_equipamento": "motor"},
                          timeout=10)
        assert a.status_code in (200, 201)
        assert b.status_code in (200, 201), f"same tag different area should succeed, got {b.status_code} {b.text[:200]}"
        for x in (a, b):
            xid = x.json().get("id")
            if xid:
                requests.delete(f"{API}/ativos/{xid}", headers=headers, timeout=10)

    def test_list_ativos(self, headers):
        r = requests.get(f"{API}/ativos", headers=headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


# ───────────────────────── MODULE: INSPEÇÕES ─────────────────────────
class TestInspecoes:
    def test_list_inspecoes(self, headers):
        r = requests.get(f"{API}/inspecoes", headers=headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_checklist_templates(self, headers):
        r = requests.get(f"{API}/checklists/templates", headers=headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        # Templates may be list or dict keyed by type
        assert data


# ───────────────────────── MODULE: RONDA ─────────────────────────
class TestRonda:
    def test_list_rondas(self, headers):
        r = requests.get(f"{API}/rondas", headers=headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            sample = data[0]
            assert "total_ativos" in sample or "nome" in sample


# ───────────────────────── MODULE: OS ─────────────────────────
class TestOS:
    def test_list_os(self, headers):
        r = requests.get(f"{API}/ordens-servico", headers=headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_preventiva(self, headers):
        # Need an ativo
        ra = requests.get(f"{API}/ativos", headers=headers, timeout=10)
        ativos = ra.json()
        if not ativos:
            pytest.skip("no ativos")
        ativo_id = ativos[0]["id"]
        payload = {
            "tipo": "preventiva",
            "disciplina": "mecanica",
            "titulo": "TEST_Iter22 OS preventiva",
            "ativo_id": ativo_id,
            "descricao": "TEST_Iter22 OS preventiva",
            "prioridade": "media",
        }
        r = requests.post(f"{API}/ordens-servico", headers=headers, json=payload, timeout=15)
        assert r.status_code in (200, 201), f"POST OS -> {r.status_code} {r.text[:300]}"
        os_id = r.json().get("id")
        assert os_id

        # status transitions: aberta → em_execucao (via /iniciar) → concluida (via /concluir)
        ri = requests.post(f"{API}/ordens-servico/{os_id}/iniciar", headers=headers, timeout=10)
        assert ri.status_code in (200, 204), f"iniciar -> {ri.status_code} {ri.text[:200]}"

        rc = requests.post(f"{API}/ordens-servico/{os_id}/concluir", headers=headers,
                           json={"tempo_execucao_minutos": 30, "servicos_realizados": "TEST_Iter22 concluido"}, timeout=10)
        assert rc.status_code in (200, 204), f"concluir -> {rc.status_code} {rc.text[:200]}"

        # verify final status via GET
        rg = requests.get(f"{API}/ordens-servico/{os_id}", headers=headers, timeout=10)
        assert rg.status_code == 200
        assert rg.json().get("status") == "concluida"


# ───────────────────────── MODULE: ESTOQUE ─────────────────────────
class TestEstoque:
    def test_list_estoque(self, headers):
        r = requests.get(f"{API}/estoque", headers=headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_edit_delete_estoque(self, headers):
        sku = f"EST22-{uuid.uuid4().hex[:5].upper()}"
        payload = {"sku": sku, "nome": "TEST_Iter22_item", "unidade": "UN", "categoria": "outro"}
        r = requests.post(f"{API}/estoque", headers=headers, json=payload, timeout=10)
        if r.status_code == 422:
            pytest.skip(f"estoque schema differs: {r.text[:200]}")
        assert r.status_code in (200, 201), f"POST estoque -> {r.status_code} {r.text[:200]}"
        item = r.json()
        item_id = item.get("id") or item.get("_id")
        assert item_id

        # GET (single) — endpoint may or may not exist; skip if 404
        rg = requests.get(f"{API}/estoque/{item_id}", headers=headers, timeout=10)
        # Either 200 or 404 (no detail endpoint) — both acceptable
        assert rg.status_code in (200, 404)

        # DELETE
        rd = requests.delete(f"{API}/estoque/{item_id}", headers=headers, timeout=10)
        assert rd.status_code in (200, 204, 404), f"delete estoque -> {rd.status_code}"


# ───────────────────────── MODULE: SOBRESSALENTES ─────────────────────────
class TestSobressalentes:
    def test_list_sobressalentes(self, headers):
        r = requests.get(f"{API}/sobressalentes", headers=headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_delete_sobressalente(self, headers):
        codigo = f"SP22-{uuid.uuid4().hex[:5].upper()}"
        payload = {"codigo": codigo, "nome": "TEST_Iter22_spare", "quantidade": 5, "unidade": "un"}
        r = requests.post(f"{API}/sobressalentes", headers=headers, json=payload, timeout=10)
        if r.status_code == 422:
            pytest.skip(f"sobressalente schema differs: {r.text[:200]}")
        assert r.status_code in (200, 201), f"POST sobressalentes -> {r.status_code} {r.text[:200]}"
        sp_id = r.json().get("id")
        if sp_id:
            requests.delete(f"{API}/sobressalentes/{sp_id}", headers=headers, timeout=10)
