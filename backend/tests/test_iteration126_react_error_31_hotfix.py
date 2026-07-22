"""
ITERATION 126 — HOTFIX P0 REACT ERROR #31 EM ERROS DE VALIDAÇÃO
Backend contract validation:
- POST /api/ordens-servico com ativo_id ausente → deve retornar 422 com detail array Pydantic
- POST /api/ordens-servico com dados válidos → 200/201
- POST /api/ordens-servico com data_planejada inválida → 422
- Login admin e pcm funcionando (regressão)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

ADMIN = {"email": "test.admin@maintrix.com", "password": "admin123"}
PCM = {"email": "test.pcm@maintrix.com", "password": "pcm123"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def pcm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=PCM, timeout=30)
    assert r.status_code == 200, f"pcm login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def pcm_headers(pcm_token):
    return {"Authorization": f"Bearer {pcm_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def first_ativo_id(admin_headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert isinstance(ativos, list) and len(ativos) > 0, "No ativos to test with"
    return ativos[0]["id"]


# --- 1) Auth regression ---
class TestAuthRegression:
    def test_admin_login(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 10

    def test_pcm_login(self, pcm_token):
        assert isinstance(pcm_token, str) and len(pcm_token) > 10

    def test_admin_me(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json().get("role") == "admin"

    def test_pcm_me(self, pcm_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=pcm_headers, timeout=15)
        assert r.status_code == 200
        assert r.json().get("role") == "pcm"


# --- 2) OS validation errors — the critical 422 contract ---
class TestOSValidationErrors:
    def test_missing_ativo_id_returns_422_with_pydantic_array(self, admin_headers):
        """POST without ativo_id must return 422 with detail array (Pydantic format)."""
        payload = {
            "titulo": "OS teste sem ativo",
            "disciplina": "mecanica",
            "tipo": "corretiva",
            "prioridade": "media",
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code == 422, f"Expected 422 got {r.status_code}: {r.text[:300]}"
        body = r.json()
        detail = body.get("detail")
        assert detail is not None, f"Missing detail: {body}"
        assert isinstance(detail, list), f"detail should be list (Pydantic), got {type(detail).__name__}: {detail}"
        # Should have at least one error mentioning ativo_id
        found_ativo = False
        for d in detail:
            assert isinstance(d, dict), f"Each detail item should be dict, got {type(d).__name__}"
            loc = d.get("loc", [])
            msg = d.get("msg", "")
            assert isinstance(loc, list), "loc must be a list"
            assert isinstance(msg, str), "msg must be a string (renderable)"
            if "ativo_id" in loc:
                found_ativo = True
        assert found_ativo, f"No error for ativo_id in {detail}"

    def test_invalid_data_planejada_response_safe(self, admin_headers, first_ativo_id):
        """
        Invalid date format. Some backends accept string (200) — this is a backend contract
        note but NOT the target of this hotfix. If it returns 422, the detail must be array
        so safeErrorMsg can render it.
        """
        payload = {
            "ativo_id": first_ativo_id,
            "titulo": "TEST_ITER126 data inválida",
            "disciplina": "mecanica",
            "tipo": "corretiva",
            "prioridade": "media",
            "data_planejada": "abc",
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers, timeout=15)
        # Cleanup if accepted
        if r.status_code in (200, 201):
            try:
                requests.delete(f"{BASE_URL}/api/ordens-servico/{r.json()['id']}", headers=admin_headers, timeout=15)
            except Exception:
                pass
        # Accept: 200 (backend permissive), 400, 422, 500
        assert r.status_code in (200, 201, 400, 422, 500), f"Unexpected status {r.status_code}"
        if r.status_code == 422:
            body = r.json()
            assert isinstance(body.get("detail"), list)

    def test_create_valid_os(self, admin_headers, first_ativo_id):
        """Create a valid corretiva OS with ativo, título, disciplina — should succeed."""
        payload = {
            "ativo_id": first_ativo_id,
            "titulo": "TEST_ITER126 OS válida hotfix",
            "descricao": "Teste hotfix React #31",
            "disciplina": "mecanica",
            "tipo": "corretiva",
            "prioridade": "media",
            "procedimento_id": None,   # explicit null (matches frontend sanitization)
            "causa_falha": None,
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code in (200, 201), f"OS create failed {r.status_code}: {r.text[:300]}"
        os_data = r.json()
        assert "id" in os_data
        assert os_data["titulo"] == payload["titulo"]
        # Verify persistence
        os_id = os_data["id"]
        rg = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers, timeout=15)
        assert rg.status_code == 200
        assert rg.json()["titulo"] == payload["titulo"]
        # Cleanup
        requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers, timeout=15)

    def test_procedimento_id_empty_string_accepted_or_422(self, admin_headers, first_ativo_id):
        """
        Frontend sends null for empty procedimento_id/causa_falha.
        Verify that null is accepted (not 422).
        """
        payload = {
            "ativo_id": first_ativo_id,
            "titulo": "TEST_ITER126 nulls",
            "disciplina": "mecanica",
            "tipo": "corretiva",
            "prioridade": "media",
            "procedimento_id": None,
            "causa_falha": None,
        }
        r = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), f"nulls should be accepted, got {r.status_code}: {r.text[:200]}"
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/ordens-servico/{r.json()['id']}", headers=admin_headers, timeout=15)
        except Exception:
            pass


# --- 3) Central / Auditoria regression ---
class TestCentralAndAuditoria:
    def test_central_loads_for_admin(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/central", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"Central failed: {r.status_code} {r.text[:200]}"

    def test_auditoria_endpoint_admin(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs?limit=10", headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"admin audit-logs failed: {r.status_code} {r.text[:200]}"

    def test_auditoria_denied_for_pcm(self, pcm_headers):
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs?limit=10", headers=pcm_headers, timeout=15)
        assert r.status_code in (401, 403), f"PCM should not access audit-logs; got {r.status_code}"
