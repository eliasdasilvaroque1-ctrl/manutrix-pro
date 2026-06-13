"""
PRODUCTION READINESS AUDIT — Iteration 18
End-to-end validation of every CMMS module before field deployment.
Pass/Fail matrix for: AUTH, SECTORS, ATIVOS, INVENTORY, SPARES, OS,
INSPECTIONS, CHECKLIST TEMPLATES, DASHBOARD, USERS, PERMISSIONS.
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = ("admin@manutrix.com", "admin123")
TECNICO = ("tecnico@manutrix.com", "tecnico123")

SUFFIX = uuid.uuid4().hex[:6].upper()


# ---------- helpers ----------
def login(email, pwd):
    r = requests.post(f"{API}/auth/login", json={"email": email, "senha": pwd}, timeout=30)
    if r.status_code != 200:
        # try password key
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=30)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token") or data.get("accessToken")
    assert tok, f"no token in login response: {data}"
    return tok


@pytest.fixture(scope="session")
def admin_token():
    return login(*ADMIN)


@pytest.fixture(scope="session")
def tecnico_token():
    try:
        return login(*TECNICO)
    except AssertionError as e:
        pytest.skip(f"tecnico login failed: {e}")


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def tecnico_headers(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}", "Content-Type": "application/json"}


# ============================================================
# === AUTH ===
# ============================================================
class TestAuth:
    def test_admin_login(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 10

    def test_me_admin(self, admin_headers):
        r = requests.get(f"{API}/auth/me", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("email") == ADMIN[0]


# ============================================================
# === SECTORS ===
# ============================================================
class TestSectors:
    sector_id = None

    def test_create_sector(self, admin_headers):
        payload = {"codigo": f"AUD{SUFFIX}", "nome": f"AUDIT_Sector_{SUFFIX}", "descricao": "audit"}
        r = requests.post(f"{API}/sectors", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        b = r.json()
        assert b.get("id"), b
        assert b.get("nome") == payload["nome"]
        TestSectors.sector_id = b["id"]

    def test_read_sector(self, admin_headers):
        assert TestSectors.sector_id
        r = requests.get(f"{API}/sectors/{TestSectors.sector_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_update_sector(self, admin_headers):
        r = requests.put(
            f"{API}/sectors/{TestSectors.sector_id}",
            headers=admin_headers,
            json={"nome": f"AUDIT_Sector_UPD_{SUFFIX}"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert "UPD" in r.json().get("nome", "")

    def test_list_sectors(self, admin_headers):
        r = requests.get(f"{API}/sectors", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list) and len(r.json()) >= 1

    def test_toggle_sector(self, admin_headers):
        r = requests.patch(f"{API}/sectors/{TestSectors.sector_id}/toggle", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_delete_sector(self, admin_headers):
        r = requests.delete(f"{API}/sectors/{TestSectors.sector_id}", headers=admin_headers, timeout=30)
        assert r.status_code in (200, 204), r.text


# ============================================================
# === ATIVOS ===
# ============================================================
class TestAtivos:
    sector_id = None
    ativo_id = None

    def test_setup_sector(self, admin_headers):
        # create a sector for the ativo
        r = requests.post(
            f"{API}/sectors",
            headers=admin_headers,
            json={"codigo": f"ATV{SUFFIX}", "nome": f"AUDIT_AtivoSec_{SUFFIX}"},
            timeout=30,
        )
        assert r.status_code in (200, 201), r.text
        TestAtivos.sector_id = r.json()["id"]

    def test_create_ativo(self, admin_headers):
        payload = {
            "tag": f"AUDIT-TAG-{SUFFIX}",
            "nome": f"AUDIT_Ativo_{SUFFIX}",
            "tipo_equipamento": "bomba",
            "setor_id": TestAtivos.sector_id,
            "sector_id": TestAtivos.sector_id,
            "criticidade": "alta",
        }
        r = requests.post(f"{API}/ativos", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        TestAtivos.ativo_id = r.json()["id"]

    def test_read_ativo(self, admin_headers):
        r = requests.get(f"{API}/ativos/{TestAtivos.ativo_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_update_ativo(self, admin_headers):
        r = requests.put(
            f"{API}/ativos/{TestAtivos.ativo_id}",
            headers=admin_headers,
            json={"status": "parado"},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_list_filter_by_sector(self, admin_headers):
        r = requests.get(
            f"{API}/ativos",
            headers=admin_headers,
            params={"sector_id": TestAtivos.sector_id},
            timeout=30,
        )
        if r.status_code != 200:
            # try setor_id
            r = requests.get(
                f"{API}/ativos", headers=admin_headers, params={"setor_id": TestAtivos.sector_id}, timeout=30
            )
        assert r.status_code == 200, r.text
        assert any(a.get("id") == TestAtivos.ativo_id for a in r.json())


# ============================================================
# === INVENTORY (ESTOQUE) ===
# ============================================================
class TestEstoque:
    item_id = None

    def test_create_estoque(self, admin_headers):
        payload = {
            "nome": f"TEST_Estoque_{SUFFIX}",
            "categoria": "outro",
            "quantidade": 10,
            "estoque_minimo": 1,
            "custo_unitario": 12.5,
            "unidade": "UN",
        }
        r = requests.post(f"{API}/estoque", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        TestEstoque.item_id = r.json()["id"]

    def test_read_estoque(self, admin_headers):
        r = requests.get(f"{API}/estoque/{TestEstoque.item_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_update_estoque(self, admin_headers):
        r = requests.put(
            f"{API}/estoque/{TestEstoque.item_id}",
            headers=admin_headers,
            json={"quantidade": 20},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_movement_saida(self, admin_headers):
        payload = {"tipo": "saida", "quantidade": 3, "motivo": "audit"}
        r = requests.post(
            f"{API}/estoque/{TestEstoque.item_id}/movimentacao",
            headers=admin_headers,
            json=payload,
            timeout=30,
        )
        # Some apps use /movimentacoes
        if r.status_code == 404:
            r = requests.post(
                f"{API}/estoque/{TestEstoque.item_id}/movimentacoes",
                headers=admin_headers,
                json=payload,
                timeout=30,
            )
        assert r.status_code in (200, 201), f"movement failed: {r.status_code} {r.text}"

    def test_list_estoque(self, admin_headers):
        r = requests.get(f"{API}/estoque", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text


# ============================================================
# === SPARE PARTS (sobressalentes) ===
# ============================================================
class TestSpares:
    sp_id = None

    def test_create(self, admin_headers):
        payload = {
            "nome": f"TEST_Spare_{SUFFIX}",
            "fabricante": "ACME",
            "tag": f"SP-{SUFFIX}",
            "numero_serie": f"SN-{SUFFIX}",
            "status": "disponivel",
            "custo": 100.0,
        }
        r = requests.post(f"{API}/sobressalentes", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        TestSpares.sp_id = r.json()["id"]

    def test_read(self, admin_headers):
        r = requests.get(f"{API}/sobressalentes/{TestSpares.sp_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_update(self, admin_headers):
        r = requests.put(
            f"{API}/sobressalentes/{TestSpares.sp_id}",
            headers=admin_headers,
            json={"fabricante": "ACME-V2"},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_list(self, admin_headers):
        r = requests.get(f"{API}/sobressalentes", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text


# ============================================================
# === WORK ORDERS ===
# ============================================================
class TestOS:
    os_id = None

    def test_create_os(self, admin_headers):
        # need an ativo
        assert TestAtivos.ativo_id, "ativo not created"
        payload = {
            "ativo_id": TestAtivos.ativo_id,
            "tipo": "corretiva",
            "disciplina": "mecanica",
            "prioridade": "alta",
            "titulo": f"AUDIT_OS_{SUFFIX}",
            "descricao": "Audit work order",
            "causa_falha": "desgaste",
            "equipamento_parado": True,
            "horas_parada": 2,
        }
        r = requests.post(f"{API}/ordens-servico", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        b = r.json()
        TestOS.os_id = b["id"]
        # verify new fields persisted
        assert b.get("disciplina") == "mecanica"
        assert b.get("causa_falha") == "desgaste"
        assert b.get("equipamento_parado") is True

    def test_read_os(self, admin_headers):
        r = requests.get(f"{API}/ordens-servico/{TestOS.os_id}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_list_filter_tipo_disciplina(self, admin_headers):
        r = requests.get(
            f"{API}/ordens-servico",
            headers=admin_headers,
            params={"tipo": "corretiva", "disciplina": "mecanica"},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_kanban_move(self, admin_headers):
        r = requests.patch(
            f"{API}/ordens-servico/{TestOS.os_id}/status",
            headers=admin_headers,
            json={"new_status": "em_execucao"},
            timeout=30,
        )
        assert r.status_code == 200, r.text

    def test_historico(self, admin_headers):
        r = requests.get(
            f"{API}/ordens-servico/{TestOS.os_id}/historico", headers=admin_headers, timeout=30
        )
        # historico is optional; allow 200 or 404
        assert r.status_code in (200, 404), r.text


# ============================================================
# === INSPECTIONS ===
# ============================================================
class TestInspecoes:
    insp_mec = None

    def test_create_mecanica(self, admin_headers):
        assert TestAtivos.ativo_id
        payload = {
            "ativo_id": TestAtivos.ativo_id,
            "tipo": "mecanica",
            "data_prevista": "2026-02-01",
            "frequencia": "mensal",
            "responsavel_id": None,
            "titulo": f"AUDIT_INSP_MEC_{SUFFIX}",
        }
        r = requests.post(f"{API}/inspecoes", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        b = r.json()
        TestInspecoes.insp_mec = b["id"]
        # default checklist should be present
        items = b.get("checklist") or b.get("itens_checklist") or []
        assert len(items) >= 5, f"expected default mecanica checklist, got {items}"

    def test_create_lubrificacao(self, admin_headers):
        payload = {
            "ativo_id": TestAtivos.ativo_id,
            "tipo": "lubrificacao",
            "data_prevista": "2026-02-02",
            "frequencia": "semanal",
            "titulo": f"AUDIT_INSP_LUB_{SUFFIX}",
        }
        r = requests.post(f"{API}/inspecoes", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text

    def test_create_eletrica(self, admin_headers):
        payload = {
            "ativo_id": TestAtivos.ativo_id,
            "tipo": "eletrica",
            "data_prevista": "2026-02-03",
            "frequencia": "mensal",
            "titulo": f"AUDIT_INSP_ELE_{SUFFIX}",
        }
        r = requests.post(f"{API}/inspecoes", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text

    def test_list(self, admin_headers):
        r = requests.get(f"{API}/inspecoes", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_detail(self, admin_headers):
        r = requests.get(f"{API}/inspecoes/{TestInspecoes.insp_mec}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text


# ============================================================
# === CHECKLIST TEMPLATES ===
# ============================================================
class TestChecklists:
    def test_templates(self, admin_headers):
        r = requests.get(f"{API}/checklists/templates", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        # body is dict {mecanica:{itens:[...]}, eletrica:{...}, lubrificacao:{...}}
        assert isinstance(body, dict)
        assert "mecanica" in body and "eletrica" in body and "lubrificacao" in body
        mec = body["mecanica"].get("itens", [])
        ele = body["eletrica"].get("itens", [])
        lub = body["lubrificacao"].get("itens", [])
        assert len(mec) == 10, f"mecanica itens count={len(mec)} (expected 10)"
        assert len(ele) == 10, f"eletrica itens count={len(ele)} (expected 10)"
        assert len(lub) == 9, f"lubrificacao itens count={len(lub)} (expected 9)"


# ============================================================
# === DASHBOARD ===
# ============================================================
class TestDashboard:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/kpis",
            "/dashboard/stats",
            "/dashboard/trend",
            "/dashboard/os-por-setor",
            "/dashboard/os-por-disciplina",
            "/dashboard/ativos-mais-falhas",
            "/migration/report",
        ],
    )
    def test_endpoint(self, admin_headers, endpoint):
        r = requests.get(f"{API}{endpoint}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"{endpoint}: {r.status_code} {r.text[:300]}"


# ============================================================
# === USERS ===
# ============================================================
class TestUsers:
    def test_list(self, admin_headers):
        r = requests.get(f"{API}/users", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1


# ============================================================
# === PERMISSIONS (tecnico) ===
# ============================================================
class TestPermissions:
    def test_tecnico_cannot_create_sector(self, tecnico_headers):
        r = requests.post(
            f"{API}/sectors",
            headers=tecnico_headers,
            json={"codigo": f"FORB{SUFFIX}", "nome": f"FORB_{SUFFIX}"},
            timeout=30,
        )
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"

    def test_tecnico_cannot_delete_ativo(self, tecnico_headers):
        assert TestAtivos.ativo_id
        r = requests.delete(
            f"{API}/ativos/{TestAtivos.ativo_id}", headers=tecnico_headers, timeout=30
        )
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"


# ============================================================
# === Z_CLEANUP (run last alphabetically) ===
# ============================================================
class TestZCleanup:
    def test_cleanup(self, admin_headers):
        # delete ativo
        if TestAtivos.ativo_id:
            requests.delete(f"{API}/ativos/{TestAtivos.ativo_id}", headers=admin_headers, timeout=30)
        # delete sector
        if TestAtivos.sector_id:
            requests.delete(f"{API}/sectors/{TestAtivos.sector_id}", headers=admin_headers, timeout=30)
        # delete estoque
        if TestEstoque.item_id:
            requests.delete(f"{API}/estoque/{TestEstoque.item_id}", headers=admin_headers, timeout=30)
        # delete spare
        if TestSpares.sp_id:
            requests.delete(f"{API}/sobressalentes/{TestSpares.sp_id}", headers=admin_headers, timeout=30)
        # delete OS
        if TestOS.os_id:
            requests.delete(f"{API}/ordens-servico/{TestOS.os_id}", headers=admin_headers, timeout=30)
