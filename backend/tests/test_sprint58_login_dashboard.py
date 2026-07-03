"""Sprint 58 — Estabilidade e Experiência de Login (backend tests)

Coverage:
- GET /api/public/organizations — used by empresa autocomplete
- POST /api/auth/login — direct login without prior org selector
- GET /api/ordens-servico/estatisticas — new fields: por_origem, aguardando_aprovacao, aguardando_material
- POST /api/auth/forgot-password — token response
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def master_token():
    r = requests.post(
        f"{API}/auth/login",
        json={"email": "master@maintrix.com", "password": "master123"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def pcm_token():
    r = requests.post(
        f"{API}/auth/login",
        json={"email": "test.pcm@maintrix.com", "password": "pcm123"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# Public organizations used by empresa autocomplete
class TestPublicOrganizations:
    def test_list_is_public(self):
        r = requests.get(f"{API}/public/organizations", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Required fields for autocomplete rendering
        first = data[0]
        assert "id" in first
        assert "nome" in first

    def test_astec_is_findable(self):
        r = requests.get(f"{API}/public/organizations", timeout=15)
        assert r.status_code == 200
        names = [(o.get("nome") or "").lower() for o in r.json()]
        assert any("astec" in n for n in names), (
            "ASTEC not found in public organizations — autocomplete will fail"
        )


# Login endpoint (no separate org-select step required by the API)
class TestAuthLogin:
    def test_login_master_success(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "master@maintrix.com", "password": "master123"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "master@maintrix.com"

    def test_login_pcm_success(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "test.pcm@maintrix.com", "password": "pcm123"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_invalid(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "nobody@maintrix.com", "password": "wrong"},
            timeout=15,
        )
        assert r.status_code in (400, 401, 403), r.text


# Sprint 58 — new dashboard KPI fields
class TestEstatisticasSprint58:
    def test_estatisticas_shape(self, pcm_token):
        r = requests.get(
            f"{API}/ordens-servico/estatisticas",
            headers=_headers(pcm_token),
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()

        # Sprint 58 required fields
        assert "por_origem" in data, "por_origem missing from estatisticas"
        assert isinstance(data["por_origem"], dict)

        assert "aguardando_aprovacao" in data
        assert isinstance(data["aguardando_aprovacao"], int)

        assert "aguardando_material" in data
        assert isinstance(data["aguardando_material"], int)

        # Pre-existing fields still present
        assert "por_status" in data
        assert "por_tipo" in data
        assert "por_disciplina" in data
        assert "total_abertas" in data

    def test_estatisticas_master_access(self, master_token):
        r = requests.get(
            f"{API}/ordens-servico/estatisticas",
            headers=_headers(master_token),
            timeout=30,
        )
        assert r.status_code == 200
        assert "por_origem" in r.json()


# Forgot password flow
class TestForgotPassword:
    def test_forgot_password_returns_message(self):
        r = requests.post(
            f"{API}/auth/forgot-password",
            json={"email": "master@maintrix.com"},
            timeout=15,
        )
        # Endpoint should exist and not 404
        assert r.status_code in (200, 202), r.text
        data = r.json()
        # Either a token or a friendly message is acceptable
        assert "token" in data or "message" in data
