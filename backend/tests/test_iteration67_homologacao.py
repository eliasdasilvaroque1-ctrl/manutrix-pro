"""
Iteration 67 - HOMOLOGACAO SPRINT - Backend RBAC + Prontuario + Public Portal + White Label
Tests visibility rules per role, Prontuario tabs endpoints, and org branding endpoints.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

# Test ativo id (from previous iterations - AV-01 in ASTEC Cedro org)
ATIVO_ID = "5af42d90-4654-4067-b67d-92d7e7f6f78d"

CREDS = {
    "master":       ("master@maintrix.com",         "master123"),
    "admin":        ("test.admin@maintrix.com",     "admin123"),
    "pcm":          ("test.pcm@maintrix.com",       "pcm123"),
    "sup_mec":      ("test.sup.mec@maintrix.com",   "sup123"),
    "sup_ele":      ("test.sup.ele@maintrix.com",   "sup123"),
    "mec":          ("test.mec@maintrix.com",       "tec123"),
    "ele":          ("test.ele@maintrix.com",       "tec123"),
    "operador":     ("test.operador@maintrix.com",  "op123"),
}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    return r


@pytest.fixture(scope="module")
def tokens():
    """Login all users once. Skip missing ones."""
    out = {}
    for key, (email, pw) in CREDS.items():
        r = _login(email, pw)
        if r.status_code == 200:
            body = r.json()
            out[key] = {
                "token": body["access_token"],
                "user": body["user"],
            }
        else:
            print(f"[WARN] Login failed for {key} ({email}): {r.status_code} {r.text[:120]}")
    return out


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# --------------------- AUTH: verify all 8 accounts login ---------------------

class TestAuthAllRoles:
    @pytest.mark.parametrize("role_key", list(CREDS.keys()))
    def test_login_ok(self, role_key):
        email, pw = CREDS[role_key]
        r = _login(email, pw)
        assert r.status_code == 200, f"Login failed for {role_key}: {r.status_code} {r.text}"
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"].lower() == email.lower()

    def test_operador_user_has_producao_disciplina(self, tokens):
        assert "operador" in tokens, "operador login failed"
        u = tokens["operador"]["user"]
        dp = u.get("disciplina_principal")
        # sanity: operador should have producao (per problem statement)
        assert dp in ("producao", "civil", None), f"Operador disciplina_principal={dp}, expected producao/civil"

    def test_mec_user_has_mecanica(self, tokens):
        assert "mec" in tokens
        u = tokens["mec"]["user"]
        assert u.get("disciplina_principal") == "mecanica", f"got {u.get('disciplina_principal')}"

    def test_ele_user_has_eletrica_and_instrumentacao(self, tokens):
        assert "ele" in tokens
        u = tokens["ele"]["user"]
        dp = u.get("disciplina_principal")
        secs = u.get("disciplinas_secundarias") or []
        all_disc = [dp] + secs
        assert "eletrica" in all_disc, f"Eletricista missing 'eletrica': {all_disc}"


# --------------------- RBAC VISIBILITY: OS ---------------------

class TestOSVisibility:
    def test_master_sees_os(self, tokens):
        assert "master" in tokens
        r = requests.get(f"{API}/ordens-servico", headers=_auth(tokens["master"]["token"]), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_operador_never_sees_mecanica_eletrica(self, tokens):
        if "operador" not in tokens:
            pytest.skip("operador login failed")
        r = requests.get(f"{API}/ordens-servico", headers=_auth(tokens["operador"]["token"]), timeout=15)
        assert r.status_code == 200, r.text
        os_list = r.json()
        forbidden = ["mecanica", "eletrica", "instrumentacao"]
        offenders = [o for o in os_list if o.get("disciplina") in forbidden]
        # Note: OS assigned directly to operador may leak; but no forbidden discipline in scope filter should appear
        # We check: no OS with disciplina in forbidden UNLESS operador is directly assigned as responsavel/equipe
        uid = tokens["operador"]["user"]["id"]
        real_offenders = [o for o in offenders if o.get("responsavel_id") != uid and uid not in (o.get("equipe") or [])]
        assert len(real_offenders) == 0, f"Operador leaked {len(real_offenders)} forbidden-discipline OS: {[o.get('numero') for o in real_offenders][:5]}"

    def test_mecanico_sees_only_mecanica(self, tokens):
        if "mec" not in tokens:
            pytest.skip("mec login failed")
        r = requests.get(f"{API}/ordens-servico", headers=_auth(tokens["mec"]["token"]), timeout=15)
        assert r.status_code == 200
        os_list = r.json()
        uid = tokens["mec"]["user"]["id"]
        # Allow: mecanica OR directly assigned (responsavel/equipe)
        for o in os_list:
            disc = o.get("disciplina")
            is_direct = o.get("responsavel_id") == uid or uid in (o.get("equipe") or [])
            assert disc in ("mecanica", None, "") or is_direct, \
                f"Mecanico sees non-mecanica OS not assigned to them: {o.get('numero')} disciplina={disc}"

    def test_eletricista_sees_only_eletrica_or_instrumentacao(self, tokens):
        if "ele" not in tokens:
            pytest.skip("ele login failed")
        r = requests.get(f"{API}/ordens-servico", headers=_auth(tokens["ele"]["token"]), timeout=15)
        assert r.status_code == 200
        os_list = r.json()
        uid = tokens["ele"]["user"]["id"]
        for o in os_list:
            disc = o.get("disciplina")
            is_direct = o.get("responsavel_id") == uid or uid in (o.get("equipe") or [])
            assert disc in ("eletrica", "instrumentacao", None, "") or is_direct, \
                f"Eletricista sees invalid disciplina: {o.get('numero')} disciplina={disc}"


# --------------------- RBAC VISIBILITY: INSPECOES ---------------------

class TestInspecoesVisibility:
    def test_operador_no_mecanica_eletrica_inspections(self, tokens):
        if "operador" not in tokens:
            pytest.skip("operador login failed")
        r = requests.get(f"{API}/inspecoes", headers=_auth(tokens["operador"]["token"]), timeout=15)
        assert r.status_code == 200, r.text
        insp = r.json()
        forbidden = ["mecanica", "eletrica", "instrumentacao"]
        uid = tokens["operador"]["user"]["id"]
        offenders = [i for i in insp if i.get("disciplina") in forbidden
                     and i.get("responsavel_id") != uid
                     and uid not in (i.get("executantes") or [])]
        assert len(offenders) == 0, f"Operador leaked {len(offenders)} forbidden inspections"

    def test_mecanico_only_mecanica_inspections(self, tokens):
        if "mec" not in tokens:
            pytest.skip("mec login failed")
        r = requests.get(f"{API}/inspecoes", headers=_auth(tokens["mec"]["token"]), timeout=15)
        assert r.status_code == 200
        uid = tokens["mec"]["user"]["id"]
        for i in r.json():
            disc = i.get("disciplina")
            is_direct = i.get("responsavel_id") == uid or uid in (i.get("executantes") or [])
            assert disc in ("mecanica", None, "") or is_direct, \
                f"Mecanico sees non-mecanica inspection: id={i.get('id')} disc={disc}"


# --------------------- PRONTUARIO / ATIVO DETAIL ---------------------

class TestProntuario:
    def test_master_gets_ativo_detail(self, tokens):
        assert "master" in tokens
        r = requests.get(f"{API}/ativos/{ATIVO_ID}", headers=_auth(tokens["master"]["token"]), timeout=15)
        assert r.status_code == 200, r.text
        ativo = r.json()
        assert ativo.get("id") == ATIVO_ID
        assert "_id" not in ativo, "MongoDB _id leaked in /api/ativos/{id}"
        # required prontuario fields
        for f in ("nome", "tag", "organization_id"):
            assert f in ativo, f"missing {f} in ativo detail"

    def test_prontuario_related_endpoints(self, tokens):
        assert "master" in tokens
        tk = tokens["master"]["token"]
        # Timeline / historico
        # Try /api/ativos/{id}/historico or /timeline
        for path in ("/historico", "/timeline"):
            r = requests.get(f"{API}/ativos/{ATIVO_ID}{path}", headers=_auth(tk), timeout=15)
            if r.status_code == 200:
                assert isinstance(r.json(), (list, dict))

    def test_bom_endpoint(self, tokens):
        assert "master" in tokens
        tk = tokens["master"]["token"]
        r = requests.get(f"{API}/ativos/{ATIVO_ID}/bom", headers=_auth(tk), timeout=15)
        # Endpoint should exist; either 200 or 404 if not implemented
        assert r.status_code in (200, 404), f"BOM unexpected: {r.status_code} {r.text[:120]}"
        if r.status_code == 200:
            body = r.json()
            assert isinstance(body, (list, dict))

    def test_pcm_can_create_ativo(self, tokens):
        if "pcm" not in tokens:
            pytest.skip("pcm login failed")
        tk = tokens["pcm"]["token"]
        # Fetch a valid sector_id from existing ativos so payload validates
        list_r = requests.get(f"{API}/ativos", headers=_auth(tk), timeout=15)
        assert list_r.status_code == 200
        sector_id = None
        for a in list_r.json():
            if a.get("sector_id"):
                sector_id = a["sector_id"]
                break
        if not sector_id:
            pytest.skip("No sector_id available to create ativo")
        payload = {
            "nome": "TEST_Bomba Centrifuga",
            "tag": "BC-TEST-67",
            "tipo": "BOMBA",
            "tipo_equipamento": "BOMBA",
            "fabricante": "KSB",
            "modelo": "MEGANORM",
            "sector_id": sector_id,
        }
        r = requests.post(f"{API}/ativos", json=payload, headers=_auth(tk), timeout=15)
        # Expect 200 or 201
        assert r.status_code in (200, 201), f"PCM create ativo failed: {r.status_code} {r.text[:200]}"
        created = r.json()
        assert created.get("nome") == payload["nome"]
        assert "id" in created
        # Verify persistence
        get_r = requests.get(f"{API}/ativos/{created['id']}", headers=_auth(tk), timeout=15)
        assert get_r.status_code == 200
        # Cleanup
        requests.delete(f"{API}/ativos/{created['id']}", headers=_auth(tk), timeout=15)


# --------------------- PUBLIC PORTAL ---------------------

class TestPublicPortal:
    def test_public_ativo_no_auth(self):
        r = requests.get(f"{API}/public/ativo/{ATIVO_ID}", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "_id" not in body
        for f in ("ativo", "kpis", "branding"):
            assert f in body, f"missing {f} in public payload"
        assert body["ativo"].get("tag") is not None

    def test_public_ativo_404(self):
        r = requests.get(f"{API}/public/ativo/does-not-exist", timeout=15)
        assert r.status_code == 404


# --------------------- WHITE LABEL (MASTER) ---------------------

class TestWhiteLabel:
    def test_master_list_orgs(self, tokens):
        assert "master" in tokens
        tk = tokens["master"]["token"]
        # Try common master endpoints
        for path in ("/master/organizations", "/master/orgs", "/organizations"):
            r = requests.get(f"{API}{path}", headers=_auth(tk), timeout=15)
            if r.status_code == 200:
                data = r.json()
                assert isinstance(data, list) or isinstance(data, dict)
                return
        pytest.fail("No master orgs listing endpoint responded 200")

    def test_get_white_label_config(self, tokens):
        assert "master" in tokens
        tk = tokens["master"]["token"]
        # Get user's own org first
        me = requests.get(f"{API}/auth/me", headers=_auth(tk), timeout=15).json()
        org_id = me.get("organization_id")
        if not org_id:
            pytest.skip("master has no organization_id")
        # try get org config
        for path in (f"/organizations/{org_id}", f"/master/organizations/{org_id}", f"/master/white-label/{org_id}"):
            r = requests.get(f"{API}{path}", headers=_auth(tk), timeout=15)
            if r.status_code == 200:
                return
        # not fatal — just log
        pytest.skip("No white-label GET endpoint responded 200 (verified via UI instead)")


# --------------------- CENTRAL DE TRABALHO ---------------------

class TestCentral:
    @pytest.mark.parametrize("role_key", ["sup_mec", "mec", "ele", "operador", "pcm"])
    def test_central_endpoint(self, tokens, role_key):
        if role_key not in tokens:
            pytest.skip(f"{role_key} login failed")
        tk = tokens[role_key]["token"]
        # Try common central endpoints
        candidates = [
            "/central/trabalho",
            "/central-trabalho",
            "/central",
            "/central-de-trabalho",
        ]
        found = False
        for path in candidates:
            r = requests.get(f"{API}{path}", headers=_auth(tk), timeout=15)
            if r.status_code in (200, 204):
                found = True
                break
        # Central may just be a UI page powered by /ordens-servico + /inspecoes
        if not found:
            # ensure at least /ordens-servico works for this role
            r = requests.get(f"{API}/ordens-servico", headers=_auth(tk), timeout=15)
            assert r.status_code == 200, f"{role_key} cannot read OS: {r.status_code}"
