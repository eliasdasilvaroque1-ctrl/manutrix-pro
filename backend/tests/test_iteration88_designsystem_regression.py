"""
Iteration 88 - Design System Phase 1 - Backend regression tests.

Design System changes are CSS/UI ONLY - no backend changes.
This suite verifies critical read/list endpoints continue to work after the frontend changes,
ensuring no accidental regressions to auth, dashboards, estoque, sobressalentes, OS,
inspecoes, ativos, or whitelabel.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "test.admin@maintrix.com"
ADMIN_PASSWORD = "admin123"
ASTEC_ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    """Login as admin — API uses access_token, not token."""
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "organization_id": ASTEC_ORG_ID,
        },
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tk = data.get("access_token") or data.get("token")
    assert tk, f"No access_token in login response: {data}"
    return tk


@pytest.fixture(scope="module")
def auth_client(session, token):
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


# ------------------------ Sanity ------------------------
def test_root_reachable(session):
    r = session.get(f"{BASE_URL}/api/")
    assert r.status_code in (200, 404)  # tolerate no root handler


def test_public_organizations_list(session):
    r = session.get(f"{BASE_URL}/api/public/organizations")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(o.get("id") == ASTEC_ORG_ID for o in data), "ASTEC org missing"


def test_public_branding_astec(session):
    r = session.get(f"{BASE_URL}/api/public/branding/{ASTEC_ORG_ID}")
    assert r.status_code == 200
    data = r.json()
    assert data.get("organization_id") == ASTEC_ORG_ID
    # Should expose tema block with cor_menu / cor_header etc used by design tokens
    tema = data.get("tema") or {}
    assert isinstance(tema, dict)
    # These keys drive --brand-surface / --brand-border in branding.js
    for k in ("cor_primaria", "cor_menu", "cor_header", "cor_texto"):
        assert k in tema, f"Missing branding key '{k}' — token injection will use defaults"


# ------------------------ Auth ------------------------
def test_login_bad_password(session):
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": "wrongwrongwrong",
            "organization_id": ASTEC_ORG_ID,
        },
    )
    assert r.status_code in (400, 401, 403)


def test_auth_me(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data.get("email") == ADMIN_EMAIL


# ------------------------ Regression: page-backing APIs ------------------------
def test_dashboard_kpis(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/kpis")
    assert r.status_code == 200, r.text[:300]


def test_estoque_list(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/estoque")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_sobressalentes_list(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/sobressalentes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_os_list(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/ordens-servico")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_inspecoes_list(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/inspecoes")
    assert r.status_code == 200


def test_ativos_list(auth_client):
    r = auth_client.get(f"{BASE_URL}/api/ativos")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_org_config_reachable(auth_client):
    """Org branding config drives the white-label / design tokens."""
    r = auth_client.get(f"{BASE_URL}/api/org/config")
    assert r.status_code in (200, 403), r.text[:300]
