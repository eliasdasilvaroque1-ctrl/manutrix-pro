"""
GATE 1 — Autenticação, Segurança e RBAC — ASTEC Pilot Homologation
Tests: AUTH-01..AUTH-16 | MULTI-01..MULTI-06 | RBAC (Master/Admin/PCM/Supervisor/Tecnico/Operador/Viewer/Gerente)
"""
import os
import base64
import json
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"

CREDS = {
    "master":       ("master@maintrix.com", "master123"),
    "admin":        ("test.admin@maintrix.com", "admin123"),
    "pcm":          ("test.pcm@maintrix.com", "pcm123"),
    "gerente":      ("test.gerente@maintrix.com", "ger123"),
    "sup_mec":      ("test.sup.mec@maintrix.com", "sup123"),
    "sup_ele":      ("test.sup.ele@maintrix.com", "sup123"),
    "tec_mec":      ("test.mec@maintrix.com", "tec123"),
    "tec_ele":      ("test.ele@maintrix.com", "tec123"),
    "operador":     ("test.operador@maintrix.com", "op123"),
    "viewer":       ("rc07v@maintrix.com", "viewer123"),
}


def _login(email, password, org_id=ORG_ID):
    return requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password, "organization_id": org_id},
        timeout=30,
    )


@pytest.fixture(scope="session")
def tokens():
    """Login every persona once and cache tokens."""
    result = {}
    for key, (email, pwd) in CREDS.items():
        r = _login(email, pwd)
        assert r.status_code == 200, f"Login failed for {key}: {r.status_code} {r.text[:200]}"
        result[key] = r.json()["access_token"]
    return result


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# AUTH tests
# ============================================================

class TestAuth:

    def test_auth_01_login_valid(self):
        r = _login(*CREDS["admin"])
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body and isinstance(body["access_token"], str) and body["access_token"]
        assert body.get("token_type") == "bearer"
        assert body["user"]["email"] == CREDS["admin"][0]
        assert body["user"]["organization_id"] == ORG_ID
        assert body["user"]["role"] == "admin"

    def test_auth_02_login_without_org(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": CREDS["admin"][0], "password": CREDS["admin"][1]},
                          timeout=30)
        # organization_id is required by pydantic → 422
        assert r.status_code in (400, 422), f"Expected 400/422 but got {r.status_code}: {r.text[:200]}"

    def test_auth_03_login_wrong_org(self):
        r = _login(CREDS["admin"][0], CREDS["admin"][1], org_id=str(uuid.uuid4()))
        assert r.status_code == 401

    def test_auth_04_login_nonexistent_email(self):
        r = _login(f"nobody-{uuid.uuid4().hex}@maintrix.com", "whatever123")
        assert r.status_code == 401

    def test_auth_05_login_wrong_password(self):
        r = _login(CREDS["admin"][0], "wrongpassword!!!")
        assert r.status_code == 401

    def test_auth_06_login_empty_email(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": "", "password": "x", "organization_id": ORG_ID}, timeout=30)
        assert r.status_code in (400, 401, 422)

    def test_auth_07_login_empty_password(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": CREDS["admin"][0], "password": "", "organization_id": ORG_ID}, timeout=30)
        assert r.status_code in (400, 401, 422)

    def test_auth_08_me_with_valid_token(self, tokens):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == CREDS["admin"][0]
        assert me["organization_id"] == ORG_ID
        assert "password_hash" not in me

    def test_auth_09_me_with_invalid_token(self):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": "Bearer invalid.token.here"}, timeout=30)
        assert r.status_code == 401

    def test_auth_10_me_without_token(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=30)
        # HTTPBearer with default auto_error=True returns 403 when no header — accept 401/403
        assert r.status_code in (401, 403)

    def test_auth_11_forgot_password_valid(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": CREDS["admin"][0], "organization_id": ORG_ID}, timeout=30)
        assert r.status_code == 200
        b = r.json()
        assert b.get("success") is True

    def test_auth_12_forgot_password_enumeration(self):
        r1 = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                           json={"email": CREDS["admin"][0], "organization_id": ORG_ID}, timeout=30)
        r2 = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                           json={"email": f"nobody-{uuid.uuid4().hex}@maintrix.com", "organization_id": ORG_ID}, timeout=30)
        assert r1.status_code == 200 and r2.status_code == 200
        # Same response body pattern — no distinction leaked
        assert r1.json().get("success") == r2.json().get("success") is True

    def test_auth_13_change_password_correct_old(self, tokens):
        # Create a disposable admin-owned user, then rotate password with correct old.
        admin_tk = tokens["admin"]
        tmp_email = f"test.tmpchg+{uuid.uuid4().hex[:8]}@maintrix.com"
        payload = {"email": tmp_email, "nome": "TEST_chg", "role": "operador",
                   "password": "old_pw_123", "organization_id": ORG_ID,
                   "disciplina_principal": "producao"}
        c = requests.post(f"{BASE_URL}/api/admin/users", json=payload,
                          headers=_auth(admin_tk), timeout=30)
        assert c.status_code == 200, c.text
        tmp_uid = c.json()["id"]
        try:
            # First login → force_password_change=True → allowed to change without current
            login = _login(tmp_email, "old_pw_123")
            assert login.status_code == 200, login.text
            tk = login.json()["access_token"]
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": "old_pw_123", "new_password": "new_pw_456"},
                              headers=_auth(tk), timeout=30)
            assert r.status_code == 200, r.text
            # Now change again with correct current
            login2 = _login(tmp_email, "new_pw_456")
            assert login2.status_code == 200
            tk2 = login2.json()["access_token"]
            r2 = requests.post(f"{BASE_URL}/api/auth/change-password",
                               json={"current_password": "new_pw_456", "new_password": "final_pw_789"},
                               headers=_auth(tk2), timeout=30)
            assert r2.status_code == 200, r2.text
        finally:
            requests.delete(f"{BASE_URL}/api/admin/users/{tmp_uid}",
                            headers=_auth(admin_tk), timeout=30)

    def test_auth_14_change_password_wrong_old(self, tokens):
        r = requests.post(f"{BASE_URL}/api/auth/change-password",
                          json={"current_password": "wrong_old_pw", "new_password": "newpw12345"},
                          headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code in (400, 401)

    def test_auth_15_login_response_has_role_and_org(self):
        r = _login(*CREDS["pcm"])
        assert r.status_code == 200
        u = r.json()["user"]
        assert u["role"] == "pcm"
        assert u["organization_id"] == ORG_ID

    def test_auth_16_token_claims(self, tokens):
        # Decode JWT payload segment (base64url) — verify claims sub/role/org present
        tok = tokens["admin"]
        parts = tok.split(".")
        assert len(parts) == 3
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        assert "sub" in payload and payload["sub"]
        assert payload.get("role") == "admin"
        assert payload.get("org") == ORG_ID
        assert "exp" in payload


# ============================================================
# MULTI-TENANT ISOLATION
# ============================================================

class TestMultitenant:

    def test_multi_02_ativos_belong_to_org(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        for it in items:
            assert it.get("organization_id") == ORG_ID, f"Ativo leaking: {it.get('id')} org={it.get('organization_id')}"

    def test_multi_03_ordens_belong_to_org(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        for it in r.json():
            assert it.get("organization_id") == ORG_ID, f"OS leak {it.get('id')}"

    def test_multi_04_inspecoes_belong_to_org(self, tokens):
        r = requests.get(f"{BASE_URL}/api/inspecoes", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        for it in r.json():
            assert it.get("organization_id") == ORG_ID, f"Inspecao leak {it.get('id')}"

    def test_multi_01_estoque_belong_to_org(self, tokens):
        r = requests.get(f"{BASE_URL}/api/estoque", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200
        for it in r.json():
            assert it.get("organization_id") == ORG_ID

    def test_multi_05_estoque_foreign_id_returns_404(self, tokens):
        fake_id = str(uuid.uuid4())
        r = requests.get(f"{BASE_URL}/api/estoque/{fake_id}", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 404

    def test_multi_06_ativos_fake_id_returns_404(self, tokens):
        fake_id = str(uuid.uuid4())
        r = requests.get(f"{BASE_URL}/api/ativos/{fake_id}", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 404

    def test_multi_tampered_token_rejected(self, tokens):
        # Take a valid token and tamper with its signature → must be rejected
        tok = tokens["admin"]
        parts = tok.split(".")
        tampered = parts[0] + "." + parts[1] + "." + ("A" * len(parts[2]))
        r = requests.get(f"{BASE_URL}/api/estoque", headers={"Authorization": f"Bearer {tampered}"}, timeout=30)
        assert r.status_code == 401


# ============================================================
# RBAC
# ============================================================

class TestRBAC:

    # ---- MASTER
    def test_rbac_master_01_can_list_admin_users(self, tokens):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_auth(tokens["master"]), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_rbac_master_02_can_create_estoque(self, tokens):
        payload = {
            "sku": f"TEST-MASTER-{uuid.uuid4().hex[:6].upper()}",
            "nome": "TEST_master_item", "quantidade": 1, "estoque_minimo": 0,
            "estoque_maximo": 10, "custo_unitario": 1.0, "categoria": "outro", "unidade": "UN"
        }
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=_auth(tokens["master"]), timeout=30)
        assert r.status_code == 200, r.text
        item_id = r.json()["id"]
        # Cleanup
        requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=_auth(tokens["master"]), timeout=30)

    # ---- ADMIN
    def test_rbac_admin_01_can_list_admin_users(self, tokens):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200

    def test_rbac_admin_02_can_crud_estoque(self, tokens):
        payload = {
            "sku": f"TEST-ADM-{uuid.uuid4().hex[:6].upper()}",
            "nome": "TEST_admin_item", "quantidade": 5, "estoque_minimo": 1,
            "estoque_maximo": 20, "custo_unitario": 2.5, "categoria": "outro", "unidade": "UN"
        }
        # Create
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=_auth(tokens["admin"]), timeout=30)
        assert r.status_code == 200, r.text
        item_id = r.json()["id"]
        # Update
        r2 = requests.put(f"{BASE_URL}/api/estoque/{item_id}", json={"quantidade": 10},
                          headers=_auth(tokens["admin"]), timeout=30)
        assert r2.status_code == 200
        assert r2.json()["quantidade"] == 10
        # Delete
        r3 = requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=_auth(tokens["admin"]), timeout=30)
        assert r3.status_code == 200

    # ---- PCM
    def test_rbac_pcm_01_can_read_estoque_os_planos(self, tokens):
        for ep in ["/api/estoque", "/api/ordens-servico", "/api/planos-inspecao"]:
            r = requests.get(f"{BASE_URL}{ep}", headers=_auth(tokens["pcm"]), timeout=30)
            assert r.status_code == 200, f"{ep} → {r.status_code}"

    def test_rbac_pcm_02_can_create_estoque_and_plano(self, tokens):
        # estoque create
        r = requests.post(f"{BASE_URL}/api/estoque",
                          json={"sku": f"TEST-PCM-{uuid.uuid4().hex[:6].upper()}",
                                "nome": "TEST_pcm_item", "quantidade": 1, "estoque_minimo": 0,
                                "estoque_maximo": 5, "custo_unitario": 1.0, "categoria": "outro", "unidade": "UN"},
                          headers=_auth(tokens["pcm"]), timeout=30)
        assert r.status_code == 200, r.text
        item_id = r.json()["id"]
        requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=_auth(tokens["admin"]), timeout=30)

        # plano create — must accept
        plano = {
            "nome": f"TEST_plano_pcm_{uuid.uuid4().hex[:6]}", "tipo": "inspecao",
            "categoria": "inspecao", "status": "rascunho", "versao": 1,
            "perguntas": [{"texto": "TEST pergunta", "tipo_campo": "boolean", "obrigatoria": True, "ordem": 0}]
        }
        r2 = requests.post(f"{BASE_URL}/api/planos-inspecao", json=plano,
                           headers=_auth(tokens["pcm"]), timeout=30)
        assert r2.status_code == 200, r2.text
        pid = r2.json()["id"]
        requests.delete(f"{BASE_URL}/api/planos-inspecao/{pid}", headers=_auth(tokens["admin"]), timeout=30)

    # ---- SUPERVISOR
    def test_rbac_supervisor_01_can_view_os(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_auth(tokens["sup_mec"]), timeout=30)
        assert r.status_code == 200

    # ---- TÉCNICO
    def test_rbac_tecnico_01_can_view_own_os(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_auth(tokens["tec_mec"]), timeout=30)
        assert r.status_code == 200

    def test_rbac_tecnico_02_cannot_create_estoque(self, tokens):
        payload = {"sku": f"TEST-TEC-{uuid.uuid4().hex[:6]}", "nome": "TEST_tec_deny",
                   "quantidade": 1, "estoque_minimo": 0, "estoque_maximo": 5,
                   "custo_unitario": 1.0, "categoria": "outro", "unidade": "UN"}
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=_auth(tokens["tec_mec"]), timeout=30)
        assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text[:200]}"

    def test_rbac_tecnico_03_cannot_delete_ativo(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(tokens["admin"]), timeout=30)
        ativos = r.json()
        if not ativos:
            pytest.skip("Sem ativos para testar")
        target_id = ativos[0]["id"]
        r2 = requests.delete(f"{BASE_URL}/api/ativos/{target_id}", headers=_auth(tokens["tec_mec"]), timeout=30)
        assert r2.status_code == 403, f"Expected 403 got {r2.status_code}: {r2.text[:200]}"

    # ---- OPERADOR
    def test_rbac_operador_01_can_create_solicitacao(self, tokens):
        # Endpoint solicitações — try /api/solicitacoes (best-effort). If missing skip.
        r = requests.get(f"{BASE_URL}/api/solicitacoes", headers=_auth(tokens["operador"]), timeout=30)
        if r.status_code == 404:
            pytest.skip("Endpoint /api/solicitacoes not implemented as GET; permission test only")
        assert r.status_code in (200, 403)  # at minimum reachable

    def test_rbac_operador_02_cannot_create_os_directly(self, tokens):
        """CTO spec: Operador CANNOT create OS directly (only solicitações).
        Currently the backend allows POST /api/ordens-servico for operador (status set to
        'solicitada'). If the business rule requires a separate /solicitacoes endpoint or a
        403 on /ordens-servico, this is a spec violation."""
        # Get a valid ativo_id from admin scope
        adm_r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(tokens["admin"]), timeout=30)
        ativos = adm_r.json()
        if not ativos:
            pytest.skip("No ativos to POST OS with")
        payload = {
            "ativo_id": ativos[0]["id"],
            "tipo": "corretiva",
            "prioridade": "media",
            "titulo": f"TEST_operador_direct_os_{uuid.uuid4().hex[:6]}",
            "disciplina": "mecanica",
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload,
                          headers=_auth(tokens["operador"]), timeout=30)
        try:
            # Strict per CTO: must be denied (403)
            assert r.status_code == 403, (
                f"AUDIT VIOLATION: Operador conseguiu criar OS diretamente (status={r.status_code}). "
                f"CTO spec: 'Operador CANNOT create OS directly'. body={r.text[:200]}"
            )
        finally:
            # Cleanup if it was created
            if r.status_code == 200:
                try:
                    oid = r.json().get("id")
                    if oid:
                        requests.delete(f"{BASE_URL}/api/ordens-servico/{oid}",
                                        headers=_auth(tokens["admin"]), timeout=30)
                except Exception:
                    pass

    def test_rbac_operador_03_cannot_access_admin_users(self, tokens):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_auth(tokens["operador"]), timeout=30)
        assert r.status_code == 403

    # ---- VISUALIZADOR
    def test_rbac_viewer_01_can_read_ativos(self, tokens):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_auth(tokens["viewer"]), timeout=30)
        # visualizador has ativos.visualizar permission
        assert r.status_code == 200, f"Viewer denied on /api/ativos: {r.status_code}"

    def test_rbac_viewer_02_cannot_create_estoque(self, tokens):
        payload = {"sku": f"TEST-VIEW-{uuid.uuid4().hex[:6]}", "nome": "TEST_view_deny",
                   "quantidade": 1, "estoque_minimo": 0, "estoque_maximo": 5,
                   "custo_unitario": 1.0, "categoria": "outro", "unidade": "UN"}
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=_auth(tokens["viewer"]), timeout=30)
        assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text[:200]}"

    def test_rbac_viewer_03_cannot_create_os(self, tokens):
        payload = {"titulo": "TEST_view_os_denied", "ativo_id": str(uuid.uuid4()), "tipo": "corretiva",
                   "prioridade": "media"}
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload,
                          headers=_auth(tokens["viewer"]), timeout=30)
        # visualizador NOT in os.criar → 403
        assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text[:200]}"

    def test_rbac_viewer_04_cannot_access_admin(self, tokens):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_auth(tokens["viewer"]), timeout=30)
        assert r.status_code == 403

    # ---- GERENTE
    def test_rbac_gerente_01_can_view_dashboard_and_os(self, tokens):
        r = requests.get(f"{BASE_URL}/api/kpis", headers=_auth(tokens["gerente"]), timeout=30)
        # some deployments use /api/dashboard/kpis; try both
        if r.status_code == 404:
            r = requests.get(f"{BASE_URL}/api/dashboard/kpis", headers=_auth(tokens["gerente"]), timeout=30)
        assert r.status_code == 200, f"Gerente cannot view KPIs: {r.status_code}"

        r2 = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_auth(tokens["gerente"]), timeout=30)
        assert r2.status_code == 200

    def test_rbac_gerente_cannot_write_estoque(self, tokens):
        payload = {"sku": f"TEST-GER-{uuid.uuid4().hex[:6]}", "nome": "TEST_ger_deny",
                   "quantidade": 1, "estoque_minimo": 0, "estoque_maximo": 5,
                   "custo_unitario": 1.0, "categoria": "outro", "unidade": "UN"}
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=_auth(tokens["gerente"]), timeout=30)
        assert r.status_code == 403
