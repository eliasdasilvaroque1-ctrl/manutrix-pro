"""
RC-10 Go Live / Cliente Zero — Pedreira Alfa
Backend tests for:
  1. Login PALFA users (all 4 roles)
  2. Multi-tenant isolation (PALFA sees only PALFA ativos/os)
  3. Estoque fix (unidade string, not enum)
  4. Dossiê enrichment for PALFA OS 2026-00001
  5. Public portal ativo endpoint
  6. Master cross-org visibility (/api/admin/users)
  7. RBAC on PALFA (viewer cannot POST OS, operador can, gerente cannot create OS)
  8. Regression ASTEC (master still sees ASTEC ativos + dashboard)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")

ASTEC_ORG = "9a232bf2-fc01-4253-813f-8df356be31c1"
PALFA_ORG = "5ea998af-ee7e-4549-9fc9-11b338335793"


def _login(email, password, org_id):
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password, "organization_id": org_id},
        timeout=30,
    )
    return r


def _token(email, password, org_id):
    r = _login(email, password, org_id)
    assert r.status_code == 200, f"Login {email} failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --- Fixtures --------------------------------------------------------
@pytest.fixture(scope="module")
def pcm_palfa_token():
    return _token("pcm@palfa.com", "alfa123", PALFA_ORG)


@pytest.fixture(scope="module")
def operador_palfa_token():
    return _token("operador@palfa.com", "alfa123", PALFA_ORG)


@pytest.fixture(scope="module")
def gerente_palfa_token():
    return _token("gerente@palfa.com", "alfa123", PALFA_ORG)


@pytest.fixture(scope="module")
def viewer_palfa_token():
    return _token("viewer@palfa.com", "alfa123", PALFA_ORG)


@pytest.fixture(scope="module")
def master_astec_token():
    return _token("master@maintrix.com", "master123", ASTEC_ORG)


# --- 1. Login PALFA --------------------------------------------------
class TestLoginPalfa:
    def test_pcm_login(self):
        r = _login("pcm@palfa.com", "alfa123", PALFA_ORG)
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body or "token" in body

    def test_operador_login(self):
        r = _login("operador@palfa.com", "alfa123", PALFA_ORG)
        assert r.status_code == 200

    def test_gerente_login(self):
        r = _login("gerente@palfa.com", "alfa123", PALFA_ORG)
        assert r.status_code == 200

    def test_viewer_login(self):
        r = _login("viewer@palfa.com", "alfa123", PALFA_ORG)
        assert r.status_code == 200


# --- 2. Isolation ----------------------------------------------------
class TestIsolationPalfa:
    def test_ativos_palfa_only(self, pcm_palfa_token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_headers(pcm_palfa_token), timeout=30)
        assert r.status_code == 200
        ativos = r.json()
        tags = sorted([a.get("tag") for a in ativos])
        assert len(ativos) == 4, f"Expected 4 PALFA ativos, got {len(ativos)}: tags={tags}"
        assert set(tags) == {"BM-001", "CT-001", "PV-001", "BC-001"}, f"Unexpected tags: {tags}"
        # All must be in PALFA org
        for a in ativos:
            assert a.get("organization_id") == PALFA_ORG, f"Ativo {a.get('tag')} leaked from other org"

    def test_ordens_servico_palfa(self, pcm_palfa_token):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_headers(pcm_palfa_token), timeout=30)
        assert r.status_code == 200
        os_list = r.json()
        for os in os_list:
            assert os.get("organization_id") == PALFA_ORG, f"OS {os.get('numero_os')} leaked from other org"


# --- 3. Estoque fix (unidade string) ---------------------------------
class TestEstoqueFix:
    created_id = None

    def test_create_estoque_with_string_unidade(self, pcm_palfa_token):
        payload = {
            "sku": "TEST-PC-001",
            "nome": "TEST_Peça de teste com unidade string",
            "descricao": "TEST_Peça de teste com unidade string",
            "unidade": "PÇ",
            "quantidade": 10,
            "estoque_minimo": 2,
            "categoria": "peca",
        }
        r = requests.post(
            f"{BASE_URL}/api/estoque",
            headers=_headers(pcm_palfa_token),
            json=payload,
            timeout=30,
        )
        assert r.status_code in (200, 201), f"POST /api/estoque failed: {r.status_code} {r.text[:500]}"
        data = r.json()
        assert data.get("unidade") == "PÇ", f"unidade not persisted correctly: {data.get('unidade')}"
        TestEstoqueFix.created_id = data.get("id")

    def test_list_estoque_contains_created(self, pcm_palfa_token):
        r = requests.get(f"{BASE_URL}/api/estoque", headers=_headers(pcm_palfa_token), timeout=30)
        assert r.status_code == 200
        items = r.json()
        skus = [it.get("sku") for it in items]
        assert "TEST-PC-001" in skus, f"Created item not listed. skus={skus}"


# --- 4. Dossiê -------------------------------------------------------
class TestDossiePalfa:
    def test_pesquisa_bm001(self, pcm_palfa_token):
        # NOTE: /api/dossie/pesquisa?q=... does NOT search by ativo tag,
        # only OS.numero/titulo. Use tag=BM-001 filter for asset-scoped search.
        r = requests.get(
            f"{BASE_URL}/api/dossie/pesquisa?tag=BM-001",
            headers=_headers(pcm_palfa_token),
            timeout=30,
        )
        assert r.status_code == 200
        results = r.json()
        if isinstance(results, dict) and "resultados" in results:
            results = results["resultados"]
        assert len(results) >= 1, f"Expected >=1 dossie result for tag=BM-001, got {len(results)}"
        # Also verify q= variant with the OS numero works
        r2 = requests.get(
            f"{BASE_URL}/api/dossie/pesquisa?q=2026-00001",
            headers=_headers(pcm_palfa_token),
            timeout=30,
        )
        assert r2.status_code == 200
        assert len(r2.json()) >= 1

    def test_dossie_os_enrichment(self, pcm_palfa_token):
        # find OS 2026-00001 (field is 'numero', not 'numero_os')
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_headers(pcm_palfa_token), timeout=30)
        assert r.status_code == 200
        os_list = r.json()
        target = next((o for o in os_list if o.get("numero") == "2026-00001"), None)
        assert target is not None, f"OS #2026-00001 not found. numeros={[o.get('numero') for o in os_list]}"
        os_id = target["id"]

        r2 = requests.get(
            f"{BASE_URL}/api/dossie/os/{os_id}",
            headers=_headers(pcm_palfa_token),
            timeout=30,
        )
        assert r2.status_code == 200, f"dossie/os failed: {r2.status_code} {r2.text[:300]}"
        dossie = r2.json()
        assert dossie.get("ativo_unidade", "").strip() == "Unidade Pedreira", (
            f"Expected ativo_unidade='Unidade Pedreira', got '{dossie.get('ativo_unidade')}'"
        )
        assert dossie.get("ativo_sector", "").strip() == "Britagem Primária", (
            f"Expected ativo_sector='Britagem Primária', got '{dossie.get('ativo_sector')}'"
        )


# --- 5. Public portal ativo ------------------------------------------
class TestPublicPortal:
    def test_public_bm001(self, pcm_palfa_token):
        # get BM-001 id first
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_headers(pcm_palfa_token), timeout=30)
        ativos = r.json()
        bm = next((a for a in ativos if a.get("tag") == "BM-001"), None)
        assert bm is not None
        bm_id = bm["id"]

        r2 = requests.get(f"{BASE_URL}/api/public/ativo/{bm_id}", timeout=30)
        assert r2.status_code == 200, f"public/ativo failed: {r2.status_code} {r2.text[:300]}"
        data = r2.json()
        # tag is nested under 'ativo' object; unidade/area are at top level
        ativo = data.get("ativo") or {}
        assert ativo.get("tag") == "BM-001", f"Public tag: {ativo.get('tag')!r}"
        unidade = data.get("unidade") or data.get("unidade_nome") or ""
        area = data.get("area") or data.get("sector") or data.get("sector_nome") or ""
        assert unidade.strip() == "Unidade Pedreira", f"Public unidade: {unidade!r}"
        assert area.strip() == "Britagem Primária", f"Public area: {area!r}"


# --- 6. Master cross-org --------------------------------------------
class TestMasterCrossOrg:
    def test_master_sees_all_orgs_users(self, master_astec_token):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_headers(master_astec_token), timeout=30)
        assert r.status_code == 200, f"admin/users failed: {r.status_code} {r.text[:300]}"
        users = r.json()
        assert isinstance(users, list) and len(users) > 0
        org_ids = {u.get("organization_id") for u in users}
        assert PALFA_ORG in org_ids, f"Master doesn't see PALFA users. org_ids={org_ids}"
        assert ASTEC_ORG in org_ids, f"Master doesn't see ASTEC users. org_ids={org_ids}"
        emails = [u.get("email") for u in users]
        assert any("palfa.com" in (e or "") for e in emails), "No palfa.com emails in master list"


# --- 7. RBAC on PALFA -----------------------------------------------
class TestRbacPalfa:
    def _get_ativo_id(self, token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_headers(token), timeout=30)
        ativos = r.json()
        assert len(ativos) > 0
        return ativos[0]["id"]

    def _os_payload(self, ativo_id):
        return {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "prioridade": "media",
            "descricao": "TEST_RBAC probe",
            "titulo": "TEST_RBAC probe",
        }

    def test_viewer_cannot_post_os(self, viewer_palfa_token):
        ativo_id = self._get_ativo_id(viewer_palfa_token)
        r = requests.post(
            f"{BASE_URL}/api/ordens-servico",
            headers=_headers(viewer_palfa_token),
            json=self._os_payload(ativo_id),
            timeout=30,
        )
        assert r.status_code in (401, 403, 422), f"Viewer should not POST OS, got {r.status_code}"

    def test_operador_can_post_os(self, operador_palfa_token):
        ativo_id = self._get_ativo_id(operador_palfa_token)
        r = requests.post(
            f"{BASE_URL}/api/ordens-servico",
            headers=_headers(operador_palfa_token),
            json=self._os_payload(ativo_id),
            timeout=30,
        )
        assert r.status_code in (200, 201), f"Operador POST OS failed: {r.status_code} {r.text[:400]}"

    def test_gerente_can_access_dashboard(self, gerente_palfa_token):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=_headers(gerente_palfa_token), timeout=30)
        assert r.status_code == 200, f"Gerente dashboard failed: {r.status_code} {r.text[:300]}"

    def test_gerente_cannot_create_os(self, gerente_palfa_token):
        ativo_id = self._get_ativo_id(gerente_palfa_token)
        r = requests.post(
            f"{BASE_URL}/api/ordens-servico",
            headers=_headers(gerente_palfa_token),
            json=self._os_payload(ativo_id),
            timeout=30,
        )
        assert r.status_code in (401, 403, 422), f"Gerente should not create OS, got {r.status_code}: {r.text[:200]}"


# --- 8. Regression ASTEC --------------------------------------------
class TestRegressionAstec:
    def test_master_astec_ativos(self, master_astec_token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_headers(master_astec_token), timeout=30)
        assert r.status_code == 200
        ativos = r.json()
        assert len(ativos) >= 40, f"Expected 40+ ASTEC ativos, got {len(ativos)}"
        # ensure NOT PALFA content
        tags = [a.get("tag") for a in ativos]
        assert "BM-001" not in tags, "ASTEC listing leaked BM-001 from PALFA"
        # all should be ASTEC
        for a in ativos:
            assert a.get("organization_id") == ASTEC_ORG, f"Ativo {a.get('tag')} not ASTEC"

    def test_dashboard_stats(self, master_astec_token):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=_headers(master_astec_token), timeout=30)
        assert r.status_code == 200
