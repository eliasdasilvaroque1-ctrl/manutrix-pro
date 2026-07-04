"""
RBAC / SECURITY AUDIT RC-01 for MAINTRIX ENTERPRISE
Audit-only tests. Reports actual HTTP responses per role.
NOTE: several tests here EXPECT to see the bug (assert current buggy behavior)
so that we have documented reproduction. The main agent is responsible for fixes.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

CREDS = {
    "master":    ("master@maintrix.com",         "master123"),
    "tec_mec":   ("test.mec@maintrix.com",       "tec123"),
    "gerente":   ("test.gerente@maintrix.com",   "ger123"),
    "operador":  ("test.operador@maintrix.com",  "op123"),
}


def login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    body = r.json()
    token = body.get("token") or body.get("access_token")
    assert token, f"No token in login response: {body}"
    return token, body


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ----------------------------------------------------------------------------
# 1. RBAC AUDIT — Técnico Mecânico
# ----------------------------------------------------------------------------
class TestTecnicoMecanicoRBAC:
    def setup_method(self):
        self.token, self.me = login(*CREDS["tec_mec"])
        self.h = auth_headers(self.token)
        # Fetch any existing OS + Inspecao ids for downstream calls
        r = requests.get(f"{API}/ordens-servico", headers=self.h, timeout=30)
        self.os_list_status = r.status_code
        self.os_list_body = r.json() if r.status_code == 200 else None

    def test_a_list_os(self):
        """(a) Can tec_mecanico see OS list at /os?"""
        assert self.os_list_status == 200, f"OS list returned {self.os_list_status}"
        n = len(self.os_list_body) if isinstance(self.os_list_body, list) else -1
        print(f"[tec_mec] /api/ordens-servico -> 200, items={n}, role={self.me.get('user', {}).get('role')}")

    def test_b_create_os_returns_403(self):
        """(b) POST /api/ordens-servico with tec_mecanico -> should be 403 per code (allowed only 'tecnico' not 'tec_mecanico')."""
        # Need a valid ativo_id first — fetch as master (side-channel) or fall back to a known one
        m_token, _ = login(*CREDS["master"])
        ativos = requests.get(f"{API}/ativos", headers=auth_headers(m_token), timeout=30).json()
        ativo_id = ativos[0]["id"] if isinstance(ativos, list) and ativos else None
        assert ativo_id, "No ativo available for testing"
        payload = {
            "ativo_id": ativo_id,
            "titulo": "TEST_RC01 corretiva by tec_mec",
            "descricao": "audit test",
            "tipo": "corretiva",
            "origem": "operador",
        }
        r = requests.post(f"{API}/ordens-servico", headers=self.h, json=payload, timeout=30)
        print(f"[tec_mec] POST /api/ordens-servico -> {r.status_code} body={r.text[:300]}")
        assert r.status_code == 403, (
            f"BUG-CONFIRMATION: tec_mecanico expected 403 (not in allowed_roles 'tecnico') but got {r.status_code}"
        )

    def test_c_iniciar_inspecao_returns_403(self):
        """(c) POST /api/inspecoes/{id}/iniciar with tec_mecanico -> should be 403 (allowed_roles only 'tecnico')."""
        # Grab any inspecao id via master
        m_token, _ = login(*CREDS["master"])
        insps = requests.get(f"{API}/inspecoes", headers=auth_headers(m_token), timeout=30).json()
        insp_id = None
        if isinstance(insps, list) and insps:
            insp_id = insps[0].get("id")
        if not insp_id:
            pytest.skip("No inspecao available")
        r = requests.post(f"{API}/inspecoes/{insp_id}/iniciar", headers=self.h, timeout=30)
        print(f"[tec_mec] POST /api/inspecoes/{insp_id}/iniciar -> {r.status_code} body={r.text[:300]}")
        assert r.status_code == 403, (
            f"BUG-CONFIRMATION: tec_mecanico expected 403 on inspecao.iniciar but got {r.status_code}"
        )

    def test_d_iniciar_os_returns_403(self):
        """(d) POST /api/ordens-servico/{id}/iniciar with tec_mecanico -> should be 403."""
        m_token, _ = login(*CREDS["master"])
        oss = requests.get(f"{API}/ordens-servico", headers=auth_headers(m_token), timeout=30).json()
        os_id = None
        if isinstance(oss, list) and oss:
            os_id = oss[0].get("id")
        if not os_id:
            pytest.skip("No OS available")
        r = requests.post(f"{API}/ordens-servico/{os_id}/iniciar", headers=self.h, timeout=30)
        print(f"[tec_mec] POST /api/ordens-servico/{os_id}/iniciar -> {r.status_code} body={r.text[:300]}")
        assert r.status_code == 403, (
            f"BUG-CONFIRMATION: tec_mecanico expected 403 on OS.iniciar but got {r.status_code}"
        )


# ----------------------------------------------------------------------------
# 2. SECURITY AUDIT — Diagnostic endpoint / forgot-password
# ----------------------------------------------------------------------------
class TestSecurityAudit:
    def test_diag_endpoint_no_auth_exposes_users(self):
        """GET /api/diag/auth-audit?key=maintrix-diag-2026 with NO login should expose data (default hardcoded key)."""
        r = requests.get(f"{API}/diag/auth-audit", params={"key": "maintrix-diag-2026"}, timeout=30)
        print(f"[NOAUTH] /api/diag/auth-audit -> {r.status_code}")
        assert r.status_code == 200, f"Expected 200 exposing data (bug), got {r.status_code}"
        body = r.json()
        assert "users" in body, f"Missing 'users' in body: {list(body.keys())}"
        u0 = body["users"][0] if body["users"] else {}
        exposed_fields = list(u0.keys())
        print(f"[SEC] diag exposed fields per user: {exposed_fields}")
        print(f"[SEC] total_users exposed: {body.get('total_users')}, admin_master_count: {body.get('admin_master_count')}")
        # Confirm it exposes email + role + hash_format => PII / hash-format leakage
        assert "email" in exposed_fields
        assert "role" in exposed_fields

    def test_forgot_password_returns_token_in_body(self):
        """POST /api/auth/forgot-password — code path in server.py:207 returns token in body (bug).
        In this env Supabase path is taken so no token is leaked over HTTP right now,
        but the code path is still present and dangerous if Supabase is disabled."""
        r = requests.post(f"{API}/auth/forgot-password", json={"email": "master@maintrix.com"}, timeout=30)
        body = r.json()
        print(f"[SEC] /api/auth/forgot-password -> {r.status_code} body={body}")
        assert r.status_code == 200
        method = body.get("method")
        # Report both branches; only fail if the LOCAL branch leaked a token
        if method != "supabase" and "token" in body:
            print("[SEC][CRITICAL] Local branch leaked reset token in response body!")
            assert False, f"Token leaked in body: {body}"
        else:
            print(f"[SEC] method={method} — local-branch token leak code (server.py:207) is NOT triggered in this env (Supabase active) but code is still present.")


# ----------------------------------------------------------------------------
# 3. EXPORT AUDIT — Master cannot export audit
# ----------------------------------------------------------------------------
class TestExportAudit:
    def test_master_export_audit_currently_403(self):
        token, _ = login(*CREDS["master"])
        r = requests.get(f"{API}/export/audit", params={"format": "excel"}, headers=auth_headers(token), timeout=60)
        print(f"[master] /api/export/audit?format=excel -> {r.status_code}, body={r.text[:200] if r.status_code != 200 else '(binary)'}")
        # Bug confirmation: only admin/gerente/pcm allowed; master is BLOCKED.
        assert r.status_code == 403, (
            f"BUG-CONFIRMATION: master expected 403 (endpoint whitelists only admin/gerente/pcm) but got {r.status_code}"
        )


# ----------------------------------------------------------------------------
# 4. USER CREATE AUDIT — disciplina_principal + area_ids persistence
# ----------------------------------------------------------------------------
class TestUserCreatePersistence:
    def test_create_user_and_check_disciplina_and_areas(self):
        token, _ = login(*CREDS["master"])
        h = auth_headers(token)

        # Try to fetch some areas to pass area_ids
        areas_resp = requests.get(f"{API}/areas", headers=h, timeout=30)
        area_ids = []
        if areas_resp.status_code == 200 and isinstance(areas_resp.json(), list):
            area_ids = [a["id"] for a in areas_resp.json()[:2] if a.get("id")]

        import time
        email = f"TEST_rc01_{int(time.time())}@maintrix.com"
        payload = {
            "email": email,
            "nome": "TEST RC01 Discipline User",
            "password": "TestPass123",
            "role": "tec_mecanico",
            "disciplina_principal": "mecanica",
            "turno": "manha",
            "area_ids": area_ids,
        }
        r = requests.post(f"{API}/admin/users", headers=h, json=payload, timeout=30)
        print(f"[master] POST /api/admin/users -> {r.status_code} body={r.text[:400]}")
        assert r.status_code in (200, 201), f"User create failed: {r.status_code} {r.text}"
        created = r.json()
        new_id = created.get("id") or (created.get("user") or {}).get("id")
        assert new_id, f"No id in create response: {created}"

        # Fetch it back via list (GET /admin/users/{id} returns 405 in this API)
        list_r = requests.get(f"{API}/admin/users", headers=h, timeout=30)
        print(f"[master] GET /api/admin/users list -> {list_r.status_code}")
        assert list_r.status_code == 200, f"List users failed: {list_r.text[:300]}"
        users_list = list_r.json() if isinstance(list_r.json(), list) else list_r.json().get("users", [])
        fetched = next((u for u in users_list if u.get("id") == new_id or u.get("email") == email), None)
        assert fetched, f"Could not find newly created user in list. list_len={len(users_list)}"
        print(f"[master] fetched user keys: {list(fetched.keys())}")

        print(f"[master] fetched disciplina_principal={fetched.get('disciplina_principal')}, "
              f"turno={fetched.get('turno')}, area_ids={fetched.get('area_ids')}")

        # Cleanup
        requests.delete(f"{API}/admin/users/{new_id}", headers=h, timeout=30)

        # Data assertions
        assert fetched.get("disciplina_principal") == "mecanica", (
            f"BUG: disciplina_principal not persisted. Got={fetched.get('disciplina_principal')}"
        )
        if area_ids:
            assert set(fetched.get("area_ids") or []) == set(area_ids), (
                f"BUG: area_ids not persisted. Sent={area_ids} Got={fetched.get('area_ids')}"
            )
        assert fetched.get("turno") == "manha", f"BUG: turno not persisted. Got={fetched.get('turno')}"


# ----------------------------------------------------------------------------
# 5. VISIBILITY AUDIT — tec_mecanico via /api/central
# ----------------------------------------------------------------------------
class TestVisibilityTecMec:
    def test_central_for_tec_mec(self):
        token, me = login(*CREDS["tec_mec"])
        h = auth_headers(token)
        r = requests.get(f"{API}/central", headers=h, timeout=30)
        print(f"[tec_mec] /api/central -> {r.status_code}")
        assert r.status_code == 200, f"/central failed: {r.text[:300]}"
        body = r.json()
        # Log shape and counts
        if isinstance(body, dict):
            keys = list(body.keys())
            counts = {k: (len(v) if isinstance(v, list) else v) for k, v in body.items()}
            print(f"[tec_mec] /api/central keys={keys} counts={counts}")
        else:
            print(f"[tec_mec] /api/central list len={len(body) if isinstance(body, list) else 'n/a'}")
        # Compare with master to see if tec_mec is scoped to nothing (BUG symptom)
        m_token, _ = login(*CREDS["master"])
        m_body = requests.get(f"{API}/central", headers=auth_headers(m_token), timeout=30).json()
        if isinstance(body, dict) and isinstance(m_body, dict):
            tec_total = sum(len(v) for v in body.values() if isinstance(v, list))
            m_total = sum(len(v) for v in m_body.values() if isinstance(v, list))
            print(f"[COMPARE] tec_mec items={tec_total}, master items={m_total}")
