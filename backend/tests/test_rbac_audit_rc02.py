"""
RBAC / SECURITY VERIFICATION — RC-02 (verifies P0 fixes applied on top of RC-01)

Verifies that the P0/P1 bugs found in iteration_75.json are now fixed:
 - P0-01  tec_mecanico can create/iniciar OS  (expected 200/201)
 - P0-02  tec_mecanico can iniciar Inspecao   (expected 200)
 - P0-03  /api/central for tec_mecanico returns items > 0 (visibility engine fixed)
 - P0-04  /api/diag/auth-audit removed        (expected 404)
 - P0-05  /api/auth/forgot-password body has NO 'token' key
 - P0-06  POST /api/admin/users persists disciplina_principal/turno/area_ids
 - P1-03  Master can GET /api/export/audit    (expected 200)
 - Regressions for master/gerente/operador ordens-servico + solicitations
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get(
    'REACT_APP_BACKEND_URL',
    'https://procure-manutrix.preview.emergentagent.com',
).rstrip('/')
API = f"{BASE_URL}/api"

CREDS = {
    "master":    ("master@maintrix.com",         "master123"),
    "tec_mec":   ("test.mec@maintrix.com",       "tec123"),
    "gerente":   ("test.gerente@maintrix.com",   "ger123"),
    "operador":  ("test.operador@maintrix.com",  "op123"),
}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    body = r.json()
    token = body.get("token") or body.get("access_token")
    assert token, f"No token: {body}"
    return token, body


def _h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# P0-04  DIAG endpoint removed
# ---------------------------------------------------------------------------
class TestP0_04_DiagRemoved:
    def test_diag_endpoint_returns_404(self):
        r = requests.get(f"{API}/diag/auth-audit", params={"key": "maintrix-diag-2026"}, timeout=30)
        print(f"[P0-04] /api/diag/auth-audit -> {r.status_code}")
        assert r.status_code == 404, (
            f"Expected 404 (endpoint removed) but got {r.status_code}. Body: {r.text[:300]}"
        )


# ---------------------------------------------------------------------------
# P0-05  forgot-password no longer leaks token
# ---------------------------------------------------------------------------
class TestP0_05_ForgotPasswordNoToken:
    def test_no_token_in_response(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": "master@maintrix.com"}, timeout=30)
        print(f"[P0-05] /api/auth/forgot-password -> {r.status_code} body={r.text[:300]}")
        assert r.status_code == 200
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        assert "token" not in body, f"BUG NOT FIXED: 'token' still present in response body: {body}"


# ---------------------------------------------------------------------------
# P0-01  tec_mecanico can create + iniciar OS
# P0-02  tec_mecanico can iniciar Inspecao
# ---------------------------------------------------------------------------
class TestP0_01_02_TecMecCanExecute:
    @pytest.fixture(scope="class")
    def tec_token(self):
        token, _ = _login(*CREDS["tec_mec"])
        return token

    @pytest.fixture(scope="class")
    def master_token(self):
        token, _ = _login(*CREDS["master"])
        return token

    def test_tec_mec_can_create_os(self, tec_token, master_token):
        # Pull a valid ativo via master (side-channel — same tenant)
        ativos = requests.get(f"{API}/ativos", headers=_h(master_token), timeout=30).json()
        assert isinstance(ativos, list) and ativos, "No ativos available for test"
        ativo_id = ativos[0]["id"]

        payload = {
            "ativo_id": ativo_id,
            "titulo": f"TEST_RC02 corretiva by tec_mec {int(time.time())}",
            "descricao": "P0-01 fix verification",
            "tipo": "corretiva",
            "origem": "operador",
        }
        r = requests.post(f"{API}/ordens-servico", headers=_h(tec_token), json=payload, timeout=30)
        print(f"[P0-01] tec_mec POST /api/ordens-servico -> {r.status_code} body={r.text[:200]}")
        assert r.status_code in (200, 201), (
            f"BUG NOT FIXED: tec_mecanico still blocked from creating OS. status={r.status_code} body={r.text[:300]}"
        )
        # Save id for cleanup + iniciar test
        created = r.json()
        self.__class__._created_os_id = created.get("id") or created.get("ordem_servico", {}).get("id")

    def test_tec_mec_can_iniciar_os(self, tec_token):
        os_id = getattr(self.__class__, "_created_os_id", None)
        if not os_id:
            pytest.skip("No OS was created by previous test")
        r = requests.post(f"{API}/ordens-servico/{os_id}/iniciar", headers=_h(tec_token), timeout=30)
        print(f"[P0-01] tec_mec POST /api/ordens-servico/{os_id}/iniciar -> {r.status_code} body={r.text[:200]}")
        assert r.status_code in (200, 201), (
            f"BUG NOT FIXED: tec_mecanico still 403 on OS.iniciar. status={r.status_code} body={r.text[:300]}"
        )

    def test_tec_mec_can_iniciar_inspecao(self, tec_token, master_token):
        # Find a pending inspecao via master
        insps = requests.get(f"{API}/inspecoes", headers=_h(master_token), timeout=30).json()
        if not isinstance(insps, list) or not insps:
            pytest.skip("No inspecoes to test")
        # prefer a pendente/agendada one
        candidates = [i for i in insps if (i.get("status") or "").lower() in ("pendente", "agendada", "programada", "aberta")]
        target = candidates[0] if candidates else insps[0]
        insp_id = target.get("id")
        if not insp_id:
            pytest.skip("No valid inspection id")
        r = requests.post(f"{API}/inspecoes/{insp_id}/iniciar", headers=_h(tec_token), timeout=30)
        print(f"[P0-02] tec_mec POST /api/inspecoes/{insp_id}/iniciar (status={target.get('status')}) -> {r.status_code} body={r.text[:200]}")
        # Accept 200/201 (fix works) OR 400 (already iniciada is a business-state failure, not RBAC)
        assert r.status_code != 403, (
            f"BUG NOT FIXED: tec_mecanico still 403 on inspecao.iniciar. body={r.text[:300]}"
        )


# ---------------------------------------------------------------------------
# P0-03  /api/central visibility for tec_mecanico
# ---------------------------------------------------------------------------
class TestP0_03_CentralVisibility:
    def test_central_returns_items_for_tec_mec(self):
        token, _ = _login(*CREDS["tec_mec"])
        r = requests.get(f"{API}/central", headers=_h(token), timeout=30)
        print(f"[P0-03] tec_mec /api/central -> {r.status_code}")
        assert r.status_code == 200
        body = r.json()

        # Central returns nested buckets: {vencidas:{os:[],inspecoes:[],total:N}, hoje:{...}, ...}
        def _bucket_count(b):
            if isinstance(b, dict):
                if isinstance(b.get("total"), int):
                    return b["total"]
                return sum(len(v) for v in b.values() if isinstance(v, list))
            if isinstance(b, list):
                return len(b)
            if isinstance(b, int):
                return b
            return 0

        if isinstance(body, dict):
            print(f"[P0-03] central summary: vencidas={_bucket_count(body.get('vencidas'))}, "
                  f"hoje={_bucket_count(body.get('hoje'))}, semana={_bucket_count(body.get('semana'))}, "
                  f"total_atividades={body.get('total_atividades')}")
            vencidas_count = _bucket_count(body.get("vencidas"))
        else:
            vencidas_count = len(body) if isinstance(body, list) else 0

        # Compare with master for sanity
        m_token, _ = _login(*CREDS["master"])
        m_body = requests.get(f"{API}/central", headers=_h(m_token), timeout=30).json()
        if isinstance(m_body, dict):
            m_total = _bucket_count(m_body.get("vencidas"))
        else:
            m_total = len(m_body) if isinstance(m_body, list) else 0
        print(f"[P0-03] tec_mec vencidas/total_visible={vencidas_count}, master total={m_total}")

        assert vencidas_count > 0, (
            f"BUG NOT FIXED: tec_mecanico /api/central still returns 0 items (visibility engine). master sees {m_total}."
        )


# ---------------------------------------------------------------------------
# P0-06  admin_create_user persists disciplina_principal/turno/area_ids
# ---------------------------------------------------------------------------
class TestP0_06_AdminCreateUserPersistence:
    def test_disciplina_turno_area_persist(self):
        token, _ = _login(*CREDS["master"])
        h = _h(token)

        areas_resp = requests.get(f"{API}/areas", headers=h, timeout=30)
        area_ids = []
        if areas_resp.status_code == 200 and isinstance(areas_resp.json(), list):
            area_ids = [a["id"] for a in areas_resp.json()[:1] if a.get("id")]

        email = f"test.rc02_{int(time.time())}@maintrix.com"
        payload = {
            "email": email,
            "nome": "TEST RC02 Disc User",
            "password": "TestPass123",
            "role": "tec_mecanico",
            "disciplina_principal": "mecanica",
            "turno": "A",
            "area_ids": area_ids,
        }
        r = requests.post(f"{API}/admin/users", headers=h, json=payload, timeout=30)
        print(f"[P0-06] POST /api/admin/users -> {r.status_code} body={r.text[:400]}")
        assert r.status_code in (200, 201), f"Create failed: {r.status_code} {r.text}"
        created = r.json()
        new_id = created.get("id") or (created.get("user") or {}).get("id")
        assert new_id, f"No id in response: {created}"

        # Check response body directly (per E1 task: "verify by reading the response")
        # Some backends return nested {'user': {...}}
        user_dict = created.get("user") if isinstance(created.get("user"), dict) else created
        print(f"[P0-06] created keys={list(user_dict.keys())}")
        resp_disciplina = user_dict.get("disciplina_principal")
        resp_turno = user_dict.get("turno")
        resp_area_ids = user_dict.get("area_ids")

        # Also verify via GET (list)
        list_r = requests.get(f"{API}/admin/users", headers=h, timeout=30)
        assert list_r.status_code == 200
        users_list = list_r.json() if isinstance(list_r.json(), list) else list_r.json().get("users", [])
        fetched = next((u for u in users_list if u.get("id") == new_id or u.get("email") == email), None)
        assert fetched, f"Newly created user not found in list (len={len(users_list)})"
        print(f"[P0-06] fetched user disc={fetched.get('disciplina_principal')} turno={fetched.get('turno')} areas={fetched.get('area_ids')}")

        # Cleanup FIRST so a later assertion failure still deletes the user
        try:
            requests.delete(f"{API}/admin/users/{new_id}", headers=h, timeout=30)
        except Exception:
            pass

        # Assertions on the fetched (persisted) record
        assert fetched.get("disciplina_principal") == "mecanica", (
            f"BUG NOT FIXED: disciplina_principal not persisted. Response={resp_disciplina} Fetched={fetched.get('disciplina_principal')}"
        )
        assert fetched.get("turno") == "A", (
            f"BUG NOT FIXED: turno not persisted. Response={resp_turno} Fetched={fetched.get('turno')}"
        )
        if area_ids:
            assert set(fetched.get("area_ids") or []) == set(area_ids), (
                f"BUG NOT FIXED: area_ids not persisted. Sent={area_ids} Response={resp_area_ids} Fetched={fetched.get('area_ids')}"
            )


# ---------------------------------------------------------------------------
# P1-03  Master can export audit
# ---------------------------------------------------------------------------
class TestP1_03_MasterCanExportAudit:
    def test_master_export_audit_excel(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/export/audit", params={"format": "excel"}, headers=_h(token), timeout=60)
        print(f"[P1-03] master /api/export/audit?format=excel -> {r.status_code} ct={r.headers.get('content-type')}")
        assert r.status_code == 200, (
            f"BUG NOT FIXED: master still blocked from export audit. status={r.status_code} body={r.text[:300]}"
        )


# ---------------------------------------------------------------------------
# REGRESSION tests
# ---------------------------------------------------------------------------
class TestRegressionMaster:
    def test_master_dashboard_stats(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/dashboard/stats", headers=_h(token), timeout=30)
        print(f"[REG] master /api/dashboard/stats -> {r.status_code}")
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json(), (dict, list))

    def test_master_ordens_servico_list(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/ordens-servico", headers=_h(token), timeout=30)
        print(f"[REG] master /api/ordens-servico -> {r.status_code} len={len(r.json()) if r.status_code==200 and isinstance(r.json(), list) else 'n/a'}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_master_inspecoes_list(self):
        token, _ = _login(*CREDS["master"])
        r = requests.get(f"{API}/inspecoes", headers=_h(token), timeout=30)
        print(f"[REG] master /api/inspecoes -> {r.status_code}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestRegressionGerente:
    def test_gerente_can_read_os(self):
        token, _ = _login(*CREDS["gerente"])
        r = requests.get(f"{API}/ordens-servico", headers=_h(token), timeout=30)
        print(f"[REG] gerente GET /api/ordens-servico -> {r.status_code}")
        assert r.status_code == 200, r.text[:300]

    def test_gerente_cannot_create_os(self):
        token_g, _ = _login(*CREDS["gerente"])
        m_token, _ = _login(*CREDS["master"])
        ativos = requests.get(f"{API}/ativos", headers=_h(m_token), timeout=30).json()
        ativo_id = ativos[0]["id"] if isinstance(ativos, list) and ativos else None
        assert ativo_id
        payload = {
            "ativo_id": ativo_id,
            "titulo": "TEST_RC02 gerente attempt",
            "descricao": "should be blocked",
            "tipo": "corretiva",
            "origem": "operador",
        }
        r = requests.post(f"{API}/ordens-servico", headers=_h(token_g), json=payload, timeout=30)
        print(f"[REG] gerente POST /api/ordens-servico -> {r.status_code}")
        assert r.status_code == 403, f"Gerente should be blocked (read-only). Got {r.status_code}: {r.text[:300]}"


class TestRegressionOperador:
    def test_operador_can_create_solicitation(self):
        token, _ = _login(*CREDS["operador"])
        m_token, _ = _login(*CREDS["master"])
        ativos = requests.get(f"{API}/ativos", headers=_h(m_token), timeout=30).json()
        ativo_id = ativos[0]["id"] if isinstance(ativos, list) and ativos else None
        assert ativo_id
        payload = {
            "ativo_id": ativo_id,
            "titulo": f"TEST_RC02 solicitacao operador {int(time.time())}",
            "descricao": "operador can create solicitations",
            "tipo": "corretiva",
            "origem": "operador",
        }
        r = requests.post(f"{API}/ordens-servico", headers=_h(token), json=payload, timeout=30)
        print(f"[REG] operador POST /api/ordens-servico -> {r.status_code} body={r.text[:200]}")
        assert r.status_code in (200, 201), f"Operador solicitation blocked: {r.status_code} {r.text[:300]}"
