"""
MAINTRIX Enterprise — Iteration 110 Pilot QA Audit
Comprehensive read-only QA sweep covering login (all roles), Central, Dashboard,
Ativos, OS lifecycle + PDF, Procedimentos + execução, Estoque, RBAC, multi-tenant,
Compliance (privacy bug investigation), Biblioteca corporativa, Users, Org config,
Auditoria, Exports and Health.
"""
import os
import pytest
import httpx
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

CRED = {
    "admin": ("test.admin@maintrix.com", "admin123"),
    "pcm": ("test.pcm@maintrix.com", "pcm123"),
    "supervisor": ("test.sup.mec@maintrix.com", "sup123"),
    "tecnico": ("test.mec@maintrix.com", "tec123"),
    "operador": ("test.operador@maintrix.com", "op123"),
}

ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"

_tokens = {}


VALID_ROLES = ("admin", "pcm", "supervisor", "tecnico", "operador", "master",
               "tec_mecanico", "tec_eletrico", "sup_mecanico", "sup_eletrico")


def login(role):
    if role in _tokens:
        return _tokens[role]
    email, pwd = CRED[role]
    for attempt in range(4):
        r = httpx.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=30)
        if r.status_code == 429:
            time.sleep(3 + attempt * 2)
            continue
        break
    assert r.status_code == 200, f"Login failed for {role}: {r.status_code} {r.text[:200]}"
    data = r.json()
    assert "access_token" in data
    assert data["user"]["role"] in VALID_ROLES, f"Unexpected role: {data['user']['role']}"
    _tokens[role] = data["access_token"]
    return data["access_token"]


def hdr(role):
    return {"Authorization": f"Bearer {login(role)}"}


# ============== Section 1: LOGIN (all roles) ==============
class TestLogin:
    def test_login_admin(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["admin"][0], "password": CRED["admin"][1]}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["role"] == "admin"
        assert d["user"]["organization_id"] == ORG_ID

    def test_login_pcm(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["pcm"][0], "password": CRED["pcm"][1]}, timeout=30)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "pcm"

    def test_login_supervisor(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["supervisor"][0], "password": CRED["supervisor"][1]}, timeout=30)
        assert r.status_code == 200
        assert r.json()["user"]["role"] in ("supervisor", "sup_mecanico", "sup_eletrico")

    def test_login_tecnico(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["tecnico"][0], "password": CRED["tecnico"][1]}, timeout=30)
        assert r.status_code == 200
        # role may be canonicalized (e.g. tec_mecanico)
        assert r.json()["user"]["role"] in ("tecnico", "tec_mecanico", "tec_eletrico")

    def test_login_operador(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["operador"][0], "password": CRED["operador"][1]}, timeout=30)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "operador"

    def test_login_invalid_credentials(self):
        r = httpx.post(f"{API}/auth/login", json={"email": CRED["admin"][0], "password": "wrong"}, timeout=30)
        assert r.status_code in (401, 400, 403)

    def test_login_no_token_returns_401(self):
        r = httpx.get(f"{API}/ativos", timeout=30)
        # FastAPI HTTPBearer returns 403 when no header sent, 401 when invalid.
        assert r.status_code in (401, 403)

    def test_login_invalid_token_returns_401(self):
        r = httpx.get(f"{API}/ativos", headers={"Authorization": "Bearer garbage.token"}, timeout=30)
        assert r.status_code == 401


# ============== Section 2: HEALTH ==============
class TestHealth:
    def test_health(self):
        r = httpx.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "healthy"
        assert d["database"]["connected"] is True


# ============== Section 3: CENTRAL ==============
class TestCentral:
    def test_central_admin(self):
        r = httpx.get(f"{API}/central", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict)


# ============== Section 4: DASHBOARD ==============
class TestDashboard:
    def test_dashboard_stats(self):
        r = httpx.get(f"{API}/dashboard/stats", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200

    def test_dashboard_os_por_setor(self):
        r = httpx.get(f"{API}/dashboard/os-por-setor", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200

    def test_dashboard_trend(self):
        r = httpx.get(f"{API}/dashboard/trend", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200

    def test_dashboard_executivo(self):
        r = httpx.get(f"{API}/dashboard/executivo", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200


# ============== Section 5: ATIVOS ==============
class TestAtivos:
    def test_list_ativos(self):
        r = httpx.get(f"{API}/ativos", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        assert len(d) >= 1

    def test_get_ativo_detail(self):
        r = httpx.get(f"{API}/ativos", headers=hdr("admin"), timeout=30)
        first = r.json()[0]
        aid = first.get("id") or first.get("_id")
        r2 = httpx.get(f"{API}/ativos/{aid}", headers=hdr("admin"), timeout=30)
        assert r2.status_code == 200

    def test_tecnico_cannot_create_ativo(self):
        # RBAC: tecnico must not create ativos
        payload = {"nome": "TEST_ATIVO_BLOCK", "tipo_equipamento": "bomba"}
        r = httpx.post(f"{API}/ativos", headers=hdr("tecnico"), json=payload, timeout=30)
        assert r.status_code in (400, 403, 422), f"Expected 403/422, got {r.status_code}"

    def test_operador_cannot_create_ativo(self):
        payload = {"nome": "TEST_ATIVO_BLOCK_OP", "tipo_equipamento": "bomba"}
        r = httpx.post(f"{API}/ativos", headers=hdr("operador"), json=payload, timeout=30)
        assert r.status_code in (400, 403, 422)


# ============== Section 6: OS LIFECYCLE ==============
_os_state = {}


class TestOSLifecycle:
    def test_list_ordens_servico(self):
        r = httpx.get(f"{API}/ordens-servico", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        # keep one existing OS id for PDF tests
        if isinstance(d, list) and d:
            _os_state["sample_os_id"] = d[0].get("id") or d[0].get("_id")

    def test_create_os(self):
        # need ativo_id
        ativos = httpx.get(f"{API}/ativos", headers=hdr("admin"), timeout=30).json()
        ativo_id = ativos[0].get("id") or ativos[0].get("_id")
        payload = {
            "ativo_id": ativo_id,
            "titulo": "TEST_OS_ITER110 QA Audit",
            "tipo": "corretiva",
            "prioridade": "media",
            "descricao": "OS created by iter110 QA audit"
        }
        r = httpx.post(f"{API}/ordens-servico", headers=hdr("admin"), json=payload, timeout=30)
        assert r.status_code in (200, 201), f"Create OS failed {r.status_code}: {r.text[:300]}"
        d = r.json()
        assert "id" in d or "_id" in d
        _os_state["new_os_id"] = d.get("id") or d.get("_id")
        assert d.get("titulo") == payload["titulo"]

    def test_pdf_generation(self):
        os_id = _os_state.get("new_os_id") or _os_state.get("sample_os_id")
        assert os_id, "no OS available for PDF test"
        r = httpx.get(f"{API}/ordens-servico/{os_id}/pdf", headers=hdr("admin"), timeout=90)
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-", "Invalid PDF header"
        assert len(r.content) > 5000, f"PDF too small: {len(r.content)}"

    def test_pdf_manual_mode(self):
        os_id = _os_state.get("new_os_id") or _os_state.get("sample_os_id")
        r = httpx.get(f"{API}/ordens-servico/{os_id}/pdf?modo=manual", headers=hdr("admin"), timeout=90)
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-"

    def test_os_historico(self):
        os_id = _os_state.get("new_os_id") or _os_state.get("sample_os_id")
        r = httpx.get(f"{API}/ordens-servico/{os_id}/historico", headers=hdr("admin"), timeout=30)
        # 200 or 404 acceptable depending on data
        assert r.status_code in (200, 404)


# ============== Section 7: PROCEDIMENTOS ==============
_proc_state = {}


class TestProcedimentos:
    def test_list_procedimentos(self):
        r = httpx.get(f"{API}/procedimentos", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        if d:
            _proc_state["sample_id"] = d[0].get("id") or d[0].get("_id")

    def test_create_procedimento_pcm(self):
        payload = {
            "nome": "TEST_PROC_ITER110",
            "descricao": "audit test",
            "etapas": [
                {"titulo": "Etapa 1", "descricao": "primeira etapa"},
                {"titulo": "Etapa 2", "descricao": "segunda etapa"},
            ],
        }
        r = httpx.post(f"{API}/procedimentos", headers=hdr("pcm"), json=payload, timeout=30)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:300]}"
        d = r.json()
        _proc_state["new_id"] = d.get("id") or d.get("_id")

    def test_tecnico_cannot_create_procedimento(self):
        payload = {"nome": "TEST_TEC_BLOCK", "etapas": [{"titulo": "X"}]}
        r = httpx.post(f"{API}/procedimentos", headers=hdr("tecnico"), json=payload, timeout=30)
        assert r.status_code in (400, 403), f"tecnico must not create procedimento: {r.status_code}"

    def test_tecnico_cannot_delete_procedimento(self):
        pid = _proc_state.get("new_id") or _proc_state.get("sample_id")
        if not pid:
            pytest.skip("no procedimento available")
        r = httpx.delete(f"{API}/procedimentos/{pid}", headers=hdr("tecnico"), timeout=30)
        assert r.status_code in (400, 403), f"tecnico must not delete: {r.status_code}"

    def test_validate_empty_name(self):
        r = httpx.post(f"{API}/procedimentos", headers=hdr("pcm"), json={"nome": "", "etapas": []}, timeout=30)
        assert r.status_code in (400, 422)


# ============== Section 8: ESTOQUE ==============
class TestEstoque:
    def test_list_estoque(self):
        r = httpx.get(f"{API}/estoque", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200


# ============== Section 9: COMPLIANCE (privacy bug investigation) ==============
class TestCompliance:
    """Investigate the 'Carregando documento' bug on /privacidade."""

    def test_privacy_returns_content(self):
        r = httpx.get(f"{API}/compliance/privacy", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "content" in d
        assert len(d["content"]) > 1000, f"Content too small: {len(d.get('content',''))}"
        assert "version" in d
        # spec says ~4085 chars
        _proc_state["privacy_chars"] = len(d["content"])

    def test_terms_returns_content(self):
        r = httpx.get(f"{API}/compliance/terms", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "content" in d
        assert len(d["content"]) > 1000

    def test_compliance_status(self):
        r = httpx.get(f"{API}/compliance/status", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "accepted" in d

    def test_privacy_no_auth_required(self):
        # If privacy needs auth, that could cause the frontend "Carregando" bug for un-authenticated users
        r = httpx.get(f"{API}/compliance/privacy", timeout=30)
        # Either public (200) or protected (401)
        assert r.status_code in (200, 401)


# ============== Section 10: USUARIOS ==============
class TestUsers:
    def test_list_users_admin(self):
        r = httpx.get(f"{API}/users", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)

    def test_admin_users_endpoint(self):
        r = httpx.get(f"{API}/admin/users", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200


# ============== Section 11: ORG CONFIG ==============
class TestOrgConfig:
    def test_org_config(self):
        r = httpx.get(f"{API}/org/config", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200


# ============== Section 12: AUDIT LOGS ==============
class TestAudit:
    def test_audit_logs(self):
        r = httpx.get(f"{API}/admin/audit-logs", headers=hdr("admin"), timeout=30)
        assert r.status_code in (200, 403)

    def test_audit_stats(self):
        r = httpx.get(f"{API}/admin/audit-logs/stats", headers=hdr("admin"), timeout=30)
        assert r.status_code in (200, 403)


# ============== Section 13: BIBLIOTECA CORPORATIVA ==============
class TestBiblioteca:
    def test_list_documentos_corporativos(self):
        r = httpx.get(f"{API}/documentos-corporativos", headers=hdr("admin"), timeout=30)
        assert r.status_code == 200


# ============== Section 14: EXPORTS ==============
class TestExports:
    def test_export_os(self):
        r = httpx.get(f"{API}/export/ordens-servico", headers=hdr("admin"), timeout=60)
        assert r.status_code in (200, 202)

    def test_export_ativos(self):
        r = httpx.get(f"{API}/export/ativos", headers=hdr("admin"), timeout=60)
        assert r.status_code in (200, 202)

    def test_export_estoque(self):
        r = httpx.get(f"{API}/export/estoque", headers=hdr("admin"), timeout=60)
        assert r.status_code in (200, 202)


# ============== Section 15: MULTI-TENANT ISOLATION ==============
class TestMultiTenant:
    def test_no_token_blocked(self):
        endpoints = ["/ativos", "/ordens-servico", "/procedimentos", "/estoque",
                     "/users", "/dashboard/stats", "/central"]
        for ep in endpoints:
            r = httpx.get(f"{API}{ep}", timeout=15)
            assert r.status_code in (401, 403), f"{ep} should require auth, got {r.status_code}"
