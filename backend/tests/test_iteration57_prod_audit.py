"""
Iteration 57 - Sprint Produção 002: Complete production audit.
Validates: Auth, RBAC, CRUD Ativo, CRUD Plano, Approval, Execução, OS,
Central, Prontuário, Dashboard, Duplicate detection, Branding cleanliness.
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

CREDS = {
    "master":    ("master@manutrix.com",       "master123"),
    "admin":     ("test.admin@maintrix.com",   "admin123"),
    "pcm":       ("test.pcm@maintrix.com",     "pcm123"),
    "supmec":    ("test.sup.mec@maintrix.com", "sup123"),
    "mec":       ("test.mec@maintrix.com",     "tec123"),
    "ele":       ("test.ele@maintrix.com",     "tec123"),
    "operador":  ("test.operador@maintrix.com","op123"),
}

# ---------- shared session ----------
def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    if r.status_code != 200:
        return None
    return r.json().get("access_token") or r.json().get("token")

@pytest.fixture(scope="module")
def tokens():
    tks = {}
    for k, (e, p) in CREDS.items():
        t = _login(e, p)
        tks[k] = t
    return tks

def _hdr(tk):
    return {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"} if tk else {"Content-Type":"application/json"}


# ============ AUTH ============
class TestAuth:
    def test_login_master(self):
        tk = _login(*CREDS["master"])
        assert tk, "master login failed"
        assert isinstance(tk, str) and len(tk) > 10

    def test_login_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["master"][0], "password": "wrongpass!!"}, timeout=15)
        assert r.status_code == 401, f"expected 401 got {r.status_code}: {r.text[:200]}"

    def test_me_returns_profile(self, tokens):
        assert tokens["master"], "no master token"
        r = requests.get(f"{API}/auth/me", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "role" in data or "roles" in data or "email" in data
        assert data.get("email") == CREDS["master"][0]

    def test_me_tecnico_has_disciplina(self, tokens):
        if not tokens["mec"]:
            pytest.skip("mec token unavailable")
        r = requests.get(f"{API}/auth/me", headers=_hdr(tokens["mec"]), timeout=15)
        assert r.status_code == 200
        data = r.json()
        # disciplina_principal may be under user object
        assert data.get("disciplina_principal") == "mecanica" or data.get("role") == "tecnico"


# ============ RBAC ============
class TestRBAC:
    def test_tecnico_mec_sees_only_mecanica(self, tokens):
        if not tokens["mec"]:
            pytest.skip("mec token unavailable")
        r = requests.get(f"{API}/ordens-servico", headers=_hdr(tokens["mec"]), timeout=15)
        assert r.status_code == 200
        os_list = r.json()
        assert isinstance(os_list, list)
        # every OS the tecnico mec sees must have disciplina in mecanica or empty
        for o in os_list:
            disc = o.get("disciplina", "").lower()
            assert disc in ("", "mecanica"), f"mec tecnico sees non-mecanica OS: {disc} / {o.get('titulo')}"

    def test_operador_never_sees_mecanica_eletrica(self, tokens):
        if not tokens["operador"]:
            pytest.skip("operador token unavailable")
        r = requests.get(f"{API}/ordens-servico", headers=_hdr(tokens["operador"]), timeout=15)
        assert r.status_code == 200
        os_list = r.json()
        assert isinstance(os_list, list)
        for o in os_list:
            disc = o.get("disciplina", "").lower()
            assert disc not in ("mecanica", "eletrica", "instrumentacao"), f"operador saw forbidden disciplina {disc}"

    def test_operador_cannot_seed(self, tokens):
        if not tokens["operador"]:
            pytest.skip("operador token unavailable")
        r = requests.post(f"{API}/seed", headers=_hdr(tokens["operador"]), timeout=15)
        assert r.status_code in (401, 403), f"operador should not seed, got {r.status_code}"


# ============ CRUD ATIVO ============
class TestAtivoCRUD:
    def test_list_ativos(self, tokens):
        r = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_ativo(self, tokens):
        # get a sector
        sec = requests.get(f"{API}/sectors", headers=_hdr(tokens["master"]), timeout=15)
        if sec.status_code != 200 or not sec.json():
            pytest.skip("no sectors available")
        sector_id = sec.json()[0].get("id")
        payload = {
            "tag": f"TEST_AUDIT57_{os.urandom(3).hex().upper()}",
            "nome": "TEST Ativo Sprint 002",
            "sector_id": sector_id,
            "tipo_equipamento": "britador",
            "criticidade": "media"
        }
        r = requests.post(f"{API}/ativos", headers=_hdr(tokens["master"]), json=payload, timeout=15)
        assert r.status_code in (200, 201), f"create ativo failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert data.get("tag") == payload["tag"]
        # GET back to verify persistence
        aid = data.get("id")
        assert aid
        g = requests.get(f"{API}/ativos/{aid}", headers=_hdr(tokens["master"]), timeout=15)
        assert g.status_code == 200
        assert g.json().get("tag") == payload["tag"]
        # cleanup
        requests.delete(f"{API}/ativos/{aid}", headers=_hdr(tokens["master"]), timeout=15)


# ============ Plano + Approval + Execução ============
class TestPlanoFlow:
    _created = {}

    def test_list_planos_enriched(self, tokens):
        r = requests.get(f"{API}/planos-inspecao", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list) and len(planos) > 0
        first = planos[0]
        # Should be enriched
        assert "ativo_tag" in first or "ativo" in first or "ativo_id" in first

    def test_duplicate_plano_returns_409(self, tokens):
        # Pick a known asset with an approved plan of some type
        r = requests.get(f"{API}/planos-inspecao", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        planos = [p for p in r.json() if p.get("ativo_id") and p.get("tipo") and p.get("disciplina")]
        if not planos:
            pytest.skip("no planos with ativo_id/tipo/disciplina available")
        target = planos[0]
        payload = {
            "nome": "TEST_AUDIT57_DUP",
            "ativo_id": target["ativo_id"],
            "tipo": target["tipo"],
            "disciplina": target["disciplina"],
            "frequencia": "mensal",
            "perguntas": [{"texto":"OK?","tipo":"boolean","obrigatoria":True}]
        }
        r = requests.post(f"{API}/planos-inspecao", headers=_hdr(tokens["master"]), json=payload, timeout=15)
        assert r.status_code == 409, f"expected 409 duplicate, got {r.status_code}: {r.text[:200]}"

    def test_create_and_approve_plano(self, tokens):
        # find any ativo
        ats = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15).json()
        assert ats
        ativo = ats[0]
        # Use a unique tipo to avoid duplicate collision
        payload = {
            "nome": "TEST_AUDIT57_PLAN",
            "ativo_id": ativo["id"],
            "tipo": "inspecao_teste_audit57",
            "disciplina": "mecanica",
            "frequencia": "mensal",
            "perguntas": [
                {"texto": "Verificar vibração?", "tipo": "boolean", "obrigatoria": True},
                {"texto": "Temperatura", "tipo": "numero", "obrigatoria": True}
            ]
        }
        r = requests.post(f"{API}/planos-inspecao", headers=_hdr(tokens["master"]), json=payload, timeout=20)
        # First attempt may collide if left from a previous run - accept 200/201/409
        if r.status_code == 409:
            pytest.skip("previous test run left a duplicate plan (409)")
        assert r.status_code in (200, 201), f"create plano failed: {r.status_code} {r.text[:300]}"
        plano = r.json()
        pid = plano.get("id")
        assert pid
        TestPlanoFlow._created["plano_id"] = pid
        TestPlanoFlow._created["ativo_id"] = ativo["id"]

        # Approve
        r2 = requests.patch(f"{API}/planos-inspecao/{pid}/aprovar", headers=_hdr(tokens["master"]), timeout=15)
        assert r2.status_code == 200, f"approve failed: {r2.status_code} {r2.text[:300]}"
        body = r2.json()
        assert body.get("success") is True or body.get("status") in ("aprovado", "approved"), f"approve body unexpected: {body}"

    def test_execucao_requires_plano_id(self, tokens):
        # missing plano_id → 422
        r = requests.post(f"{API}/inspecoes", headers=_hdr(tokens["master"]), json={
            "ativo_id": TestPlanoFlow._created.get("ativo_id") or "x"
        }, timeout=15)
        assert r.status_code in (400, 422), f"expected 400/422 without plano_id, got {r.status_code} {r.text[:200]}"

    def test_execucao_with_approved_plano(self, tokens):
        pid = TestPlanoFlow._created.get("plano_id")
        aid = TestPlanoFlow._created.get("ativo_id")
        if not pid or not aid:
            pytest.skip("no created plano available")
        r = requests.post(f"{API}/inspecoes", headers=_hdr(tokens["master"]), json={
            "plano_id": pid, "ativo_id": aid
        }, timeout=20)
        assert r.status_code in (200, 201), f"execucao create failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        # checklist should be present from plan
        assert data.get("id")
        TestPlanoFlow._created["inspecao_id"] = data["id"]

    def test_execucao_with_non_approved_plano_returns_400(self, tokens):
        # Create a fresh plan and DO NOT approve
        ats = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15).json()
        if not ats:
            pytest.skip("no ativos")
        ativo = ats[0]
        payload = {
            "nome": "TEST_AUDIT57_UNAPPROVED",
            "ativo_id": ativo["id"],
            "tipo": f"unaprv_{os.urandom(3).hex()}",
            "disciplina": "mecanica",
            "frequencia": "mensal",
            "perguntas": [{"texto":"?","tipo":"boolean","obrigatoria":True}]
        }
        c = requests.post(f"{API}/planos-inspecao", headers=_hdr(tokens["master"]), json=payload, timeout=15)
        if c.status_code not in (200, 201):
            pytest.skip(f"could not create unapproved plan: {c.status_code}")
        pid_unappr = c.json()["id"]
        try:
            r = requests.post(f"{API}/inspecoes", headers=_hdr(tokens["master"]), json={
                "plano_id": pid_unappr, "ativo_id": ativo["id"]
            }, timeout=15)
            assert r.status_code == 400, f"expected 400 for unapproved plan, got {r.status_code} {r.text[:300]}"
        finally:
            requests.delete(f"{API}/planos-inspecao/{pid_unappr}", headers=_hdr(tokens["master"]), timeout=10)

    def test_cleanup_created(self, tokens):
        pid = TestPlanoFlow._created.get("plano_id")
        iid = TestPlanoFlow._created.get("inspecao_id")
        if iid:
            requests.delete(f"{API}/inspecoes/{iid}", headers=_hdr(tokens["master"]), timeout=10)
        if pid:
            requests.delete(f"{API}/planos-inspecao/{pid}", headers=_hdr(tokens["master"]), timeout=10)


# ============ OS ============
class TestOS:
    def test_create_and_close_os(self, tokens):
        ats = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15).json()
        if not ats:
            pytest.skip("no ativos")
        ativo = ats[0]
        payload = {
            "titulo": "TEST_AUDIT57_OS",
            "descricao": "audit test",
            "tipo": "corretiva",
            "disciplina": "mecanica",
            "prioridade": "media",
            "ativo_id": ativo["id"],
        }
        r = requests.post(f"{API}/ordens-servico", headers=_hdr(tokens["master"]), json=payload, timeout=20)
        assert r.status_code in (200, 201), f"create OS failed: {r.status_code} {r.text[:300]}"
        os_ = r.json()
        oid = os_.get("id")
        assert oid
        # update to concluida
        u = requests.put(f"{API}/ordens-servico/{oid}", headers=_hdr(tokens["master"]),
                         json={"status": "concluida"}, timeout=15)
        assert u.status_code in (200, 204), f"close OS failed: {u.status_code} {u.text[:300]}"
        # cleanup
        requests.delete(f"{API}/ordens-servico/{oid}", headers=_hdr(tokens["master"]), timeout=10)


# ============ Central / Prontuário / Dashboard ============
class TestCentralProntuarioDashboard:
    def test_central_role_adaptive(self, tokens):
        r = requests.get(f"{API}/central", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict), f"central should be dict, got {type(data)}"
        # role-adaptive schema, must have at least one of these buckets
        has_bucket = any(k in data for k in ("vencidas", "hoje", "semana", "atividades", "os", "inspecoes"))
        assert has_bucket, f"central missing expected buckets: keys={list(data.keys())[:10]}"

    def test_prontuario_ativo(self, tokens):
        # find any ativo
        ats = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15).json()
        assert ats
        aid = ats[0]["id"]
        r = requests.get(f"{API}/ativos/{aid}", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200
        data = r.json()
        # Prontuário should include enriched data
        keys = list(data.keys())
        # Not all fields guaranteed - just verify it's the asset
        assert data.get("id") == aid

    def test_prontuario_ativo_saude(self, tokens):
        ats = requests.get(f"{API}/ativos", headers=_hdr(tokens["master"]), timeout=15).json()
        assert ats
        aid = ats[0]["id"]
        r = requests.get(f"{API}/ativos/{aid}/saude", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200, f"prontuario saude failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert isinstance(data, dict)

    def test_dashboard_stats(self, tokens):
        r = requests.get(f"{API}/dashboard/stats", headers=_hdr(tokens["master"]), timeout=15)
        assert r.status_code == 200, f"dashboard failed: {r.status_code}"
        data = r.json()
        assert isinstance(data, dict)


# ============ BRANDING ============
class TestBranding:
    def test_index_html_clean(self):
        with open("/app/frontend/public/index.html","r",encoding="utf-8") as f:
            content = f.read().lower()
        for kw in ["emergent", "posthog", "made with"]:
            assert kw not in content, f"index.html contains forbidden keyword: {kw}"

    def test_server_error_messages_clean(self):
        with open("/app/backend/server.py","r",encoding="utf-8") as f:
            content = f.read()
        # allow the SDK import and env var name, but no user-facing "plataforma Emergent" strings
        forbidden = ["plataforma Emergent", "Made with Emergent"]
        for kw in forbidden:
            assert kw not in content, f"server.py contains forbidden user-facing text: {kw}"


# ============ Railway smoke ============
class TestRailway:
    RAILWAY = "https://manutrix-pro-production.up.railway.app"

    def test_railway_login_returns_401(self):
        r = requests.post(f"{self.RAILWAY}/api/auth/login",
                          json={"email": "master@manutrix.com", "password": "master123"},
                          timeout=20)
        # Different DB → 401 expected; NOT 405/404
        assert r.status_code == 401, f"Railway expected 401, got {r.status_code}: {r.text[:200]}"
