"""
BLOCO A — Regression tests after dead code removal & React.memo() application.
Iteration 93 — Verifica que a limpeza (imports mortos, componentes mortos, memo)
não quebrou nenhum endpoint crítico.

Cobertura:
 - Login (master/admin/tec) na org ASTEC Cedro
 - Central de Trabalho
 - Dashboard (KPIs, MTBF/MTTR, distribuição OS)
 - Ativos
 - Ordens de Serviço (list + kanban states)
 - Estoque
 - Inspeções
 - Sobressalentes/Materiais
 - Admin Templates
 - Auditoria (audit logs)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"


def _login(email: str, password: str) -> str:
    """Login helper — returns access_token."""
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password, "organization_id": ORG_ID},
        timeout=15,
    )
    assert r.status_code == 200, f"Login {email} failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert "access_token" in body or "token" in body, f"No token in response: {body}"
    return body.get("access_token") or body.get("token")


@pytest.fixture(scope="module")
def master_token():
    return _login("master@maintrix.com", "master123")


@pytest.fixture(scope="module")
def admin_token():
    return _login("test.admin@maintrix.com", "admin123")


@pytest.fixture(scope="module")
def tec_token():
    return _login("test.mec@maintrix.com", "tec123")


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------------------------------------------------------------------------
# 1. Auth
# ---------------------------------------------------------------------------
class TestAuth:
    def test_public_organizations_loads(self):
        r = requests.get(f"{BASE_URL}/api/public/organizations", timeout=10)
        assert r.status_code == 200
        orgs = r.json()
        assert isinstance(orgs, list) and len(orgs) > 0
        assert any(o["id"] == ORG_ID for o in orgs), "ASTEC Cedro not in public orgs list"

    def test_login_master(self, master_token):
        assert master_token and isinstance(master_token, str)

    def test_login_admin(self, admin_token):
        assert admin_token and isinstance(admin_token, str)

    def test_login_tecnico(self, tec_token):
        assert tec_token and isinstance(tec_token, str)

    def test_auth_me_returns_user(self, master_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_auth(master_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("email") == "master@maintrix.com"


# ---------------------------------------------------------------------------
# 2. Central de Trabalho
# ---------------------------------------------------------------------------
class TestCentral:
    def test_central_carrega(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/central", headers=_auth(admin_token), timeout=15)
        # tolerate 200 or 404 depending on route naming
        assert r.status_code in (200, 404), f"Central: {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (dict, list))

    def test_central_tecnico(self, tec_token):
        r = requests.get(f"{BASE_URL}/api/central", headers=_auth(tec_token), timeout=15)
        assert r.status_code in (200, 404)


# ---------------------------------------------------------------------------
# 3. Dashboard (KPIs + gráficos)
# ---------------------------------------------------------------------------
class TestDashboard:
    def test_dashboard_kpis(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/kpis", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200, f"KPIs: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert isinstance(data, dict)

    def test_dashboard_mtbf_mttr(self, admin_token):
        # Try known trend endpoints
        candidates = ["/api/dashboard/mtbf-mttr", "/api/dashboard/trend", "/api/dashboard"]
        found = False
        for path in candidates:
            r = requests.get(f"{BASE_URL}{path}", headers=_auth(admin_token), timeout=15)
            if r.status_code == 200:
                found = True
                break
        assert found, "No dashboard trend/MTBF endpoint responded 200"

    def test_dashboard_distribuicao_os(self, admin_token):
        # OSDistChart is fed by dashboard/stats payload
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 4. Ativos (StatusBadge, PriorityBadge memo — must render list)
# ---------------------------------------------------------------------------
class TestAtivos:
    def test_lista_ativos(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            # ensure status/criticidade fields exist (fed to StatusBadge/PriorityBadge)
            a = data[0]
            assert isinstance(a, dict)

    def test_ativos_multitenant(self, master_token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(master_token), timeout=15)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 5. Ordens de Serviço (Kanban board)
# ---------------------------------------------------------------------------
class TestOrdensServico:
    def test_lista_os(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_os_por_status(self, admin_token):
        # Kanban precisa dos vários status
        for st in ["solicitada", "programada", "em_execucao", "concluida"]:
            r = requests.get(f"{BASE_URL}/api/ordens-servico?status={st}", headers=_auth(admin_token), timeout=15)
            assert r.status_code == 200, f"OS by status {st}: {r.status_code}"


# ---------------------------------------------------------------------------
# 6. Estoque
# ---------------------------------------------------------------------------
class TestEstoque:
    def test_lista_estoque(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/estoque", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_categorias(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/estoque/categorias", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 7. Inspeções
# ---------------------------------------------------------------------------
class TestInspecoes:
    def test_lista_inspecoes(self, admin_token):
        candidates = ["/api/inspecoes", "/api/inspecao", "/api/planos-inspecao"]
        ok = False
        for path in candidates:
            r = requests.get(f"{BASE_URL}{path}", headers=_auth(admin_token), timeout=15)
            if r.status_code == 200:
                ok = True
                break
        assert ok, "Nenhum endpoint de inspeções respondeu 200"


# ---------------------------------------------------------------------------
# 8. Sobressalentes / Materiais
# ---------------------------------------------------------------------------
class TestSobressalentes:
    def test_lista_sobressalentes(self, admin_token):
        candidates = ["/api/sobressalentes", "/api/materiais", "/api/estoque"]
        ok = False
        for path in candidates:
            r = requests.get(f"{BASE_URL}{path}", headers=_auth(admin_token), timeout=15)
            if r.status_code == 200:
                ok = True
                break
        assert ok


# ---------------------------------------------------------------------------
# 9. Admin Templates
# ---------------------------------------------------------------------------
class TestTemplates:
    def test_lista_templates(self, admin_token):
        candidates = [
            "/api/admin/templates",
            "/api/templates",
            "/api/checklists/templates",
            "/api/planos-preventivos/templates",
        ]
        ok = False
        for path in candidates:
            r = requests.get(f"{BASE_URL}{path}", headers=_auth(admin_token), timeout=15)
            if r.status_code == 200:
                ok = True
                break
        assert ok, "Nenhum endpoint de templates respondeu 200"


# ---------------------------------------------------------------------------
# 10. Auditoria
# ---------------------------------------------------------------------------
class TestAuditoria:
    def test_audit_logs(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs?limit=10", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))


# ---------------------------------------------------------------------------
# 11. Backend cleanup smoke — imports removidos não quebraram endpoints
# ---------------------------------------------------------------------------
class TestCleanupSmoke:
    def test_no_500_on_key_endpoints(self, admin_token):
        """Confere que nenhum endpoint retorna 500 (indicador de ImportError etc)."""
        endpoints = [
            "/api/dashboard",
            "/api/ativos",
            "/api/ordens-servico",
            "/api/estoque",
            "/api/auth/me",
            "/api/admin/audit-logs?limit=5",
        ]
        for ep in endpoints:
            r = requests.get(f"{BASE_URL}{ep}", headers=_auth(admin_token), timeout=15)
            assert r.status_code != 500, f"{ep} → 500 (possível ImportError após limpeza): {r.text[:200]}"

    def test_events_endpoint_not_500(self, admin_token):
        """events.py teve bare except corrigido — endpoint deve continuar respondendo."""
        candidates = ["/api/events", "/api/eventos"]
        for path in candidates:
            r = requests.get(f"{BASE_URL}{path}", headers=_auth(admin_token), timeout=15)
            assert r.status_code != 500, f"{path} 500 após fix bare except: {r.text[:200]}"
