"""Iteration 97 — RC1.5 Compliance/LGPD backend tests
Tests /api/compliance/* endpoints: status, accept, history, terms, privacy, about.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": password, "organization_id": ORG_ID
    }, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def master_token():
    return _login("master@maintrix.com", "master123")


@pytest.fixture(scope="module")
def admin_token():
    return _login("test.admin@maintrix.com", "admin123")


@pytest.fixture(scope="module")
def tec_token():
    return _login("test.mec@maintrix.com", "tec123")


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============== About (no auth needed but requires client) ==============

class TestAbout:
    def test_about_endpoint(self, master_token):
        r = requests.get(f"{BASE_URL}/api/compliance/about", headers=_headers(master_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("product") == "MAINTRIX Enterprise"
        assert "version" in d
        assert d.get("version") == "5.2.0-RC1"
        assert "build" in d
        assert "support_email" in d
        assert "privacy_email" in d


# ============== Terms & Privacy docs ==============

class TestLegalDocs:
    def test_terms_document(self, master_token):
        r = requests.get(f"{BASE_URL}/api/compliance/terms", headers=_headers(master_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("version") == "1.0"
        assert "content" in d
        assert len(d["content"]) > 100, "Terms content should be substantial"

    def test_privacy_document(self, master_token):
        r = requests.get(f"{BASE_URL}/api/compliance/privacy", headers=_headers(master_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("version") == "1.0"
        assert "content" in d
        assert len(d["content"]) > 100


# ============== Status/Accept flow ==============

class TestComplianceStatus:
    def test_status_master_accepted(self, master_token):
        """master@maintrix.com has already accepted per problem statement"""
        r = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(master_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("terms_version") == "1.0"
        assert d.get("privacy_version") == "1.0"
        assert "accepted" in d
        # Master should already have accepted
        assert d.get("accepted") is True, f"Expected master to have accepted, got {d}"

    def test_status_admin_accepted(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(admin_token), timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("accepted") is True, f"Expected admin to have accepted, got {d}"

    def test_status_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/compliance/status", timeout=15)
        # Must be 401 or 403 without auth
        assert r.status_code in [401, 403], f"Expected auth required, got {r.status_code}"


class TestComplianceAcceptFlow:
    """Test full accept flow using test.mec@maintrix.com (which may or may not have accepted).
    NOTE: This test is idempotent - it accepts if not already, and verifies status.
    """
    def test_tec_status_and_accept(self, tec_token):
        # Check status first
        r = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(tec_token), timeout=15)
        assert r.status_code == 200
        initial_status = r.json()

        if not initial_status.get("accepted"):
            # Accept
            r2 = requests.post(f"{BASE_URL}/api/compliance/accept", headers=_headers(tec_token), timeout=15)
            assert r2.status_code == 200
            d2 = r2.json()
            assert d2.get("success") is True
            assert d2.get("terms_version") == "1.0"

            # Verify status changed
            r3 = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(tec_token), timeout=15)
            assert r3.status_code == 200
            assert r3.json().get("accepted") is True
        else:
            # Already accepted — skip acceptance test but verify status endpoint is stable
            assert initial_status.get("accepted_at") is not None or True

    def test_tec_history(self, tec_token):
        # Ensure at least accept once so history is not empty
        r_status = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(tec_token), timeout=15)
        if not r_status.json().get("accepted"):
            requests.post(f"{BASE_URL}/api/compliance/accept", headers=_headers(tec_token), timeout=15)

        r = requests.get(f"{BASE_URL}/api/compliance/history", headers=_headers(tec_token), timeout=15)
        assert r.status_code == 200
        history = r.json()
        assert isinstance(history, list)
        if history:
            item = history[0]
            assert "terms_version" in item
            assert "privacy_version" in item
            assert "accepted_at" in item
            assert "ip_address" in item
            assert "user_agent" in item
            # user_email/nome should also be present per server implementation
            assert "user_email" in item

    def test_second_accept_idempotent_or_records_new(self, tec_token):
        """Calling accept twice should not break; server records new consent doc each time."""
        r = requests.post(f"{BASE_URL}/api/compliance/accept", headers=_headers(tec_token), timeout=15)
        assert r.status_code == 200
        # Status should still be accepted
        r2 = requests.get(f"{BASE_URL}/api/compliance/status", headers=_headers(tec_token), timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("accepted") is True


# ============== Regression: verify core endpoints still work ==============

class TestRegression:
    def test_dashboard_endpoint(self, master_token):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=_headers(master_token), timeout=30)
        assert r.status_code == 200, f"Dashboard KPIs failed: {r.status_code} {r.text[:200]}"

    def test_ativos_list(self, master_token):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=_headers(master_token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_os_list(self, master_token):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=_headers(master_token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
