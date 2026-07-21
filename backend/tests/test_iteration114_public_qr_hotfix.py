"""
Iteration 114 — HOTFIX P0 white-screen QR public page
Backend regression tests: public equipment endpoint + auth endpoints unchanged
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")

PUBLIC_URLS = [
    ("av-01-alimentador", "Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu"),
    ("bb-03-bomba-aspersao-patio", "P4wbjMQ3JxqWXFxOWsnYIYBtkOi1ewNf"),
]


class TestPublicEquipmentEndpoint:
    """Backend endpoint used by the public QR page must remain public and fast."""

    @pytest.mark.parametrize("slug,token", PUBLIC_URLS)
    def test_public_equipment_returns_200_no_auth(self, slug, token):
        r = requests.get(f"{BASE_URL}/api/public/equipment/{slug}/{token}", timeout=10)
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert data.get("available") is True, f"available flag not True: {data}"
        assert "equipment" in data
        eq = data["equipment"]
        assert eq.get("nome"), "equipment.nome missing"
        # tag can be nested slug -> validate at least it exists
        assert eq.get("tag"), "equipment.tag missing"

    @pytest.mark.parametrize("slug,token", PUBLIC_URLS)
    def test_public_equipment_response_time_under_3s(self, slug, token):
        r = requests.get(f"{BASE_URL}/api/public/equipment/{slug}/{token}", timeout=10)
        assert r.elapsed.total_seconds() < 3.0, f"Slow response: {r.elapsed.total_seconds():.2f}s"

    def test_public_equipment_invalid_token_returns_error_payload(self):
        r = requests.get(f"{BASE_URL}/api/public/equipment/av-01-alimentador/invalid_token_xyz", timeout=10)
        # Backend should not 500; either 404 or 200 with available=false
        assert r.status_code in (200, 404), f"Unexpected status: {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert data.get("available") is False or "message" in data

    def test_public_equipment_invalid_slug_returns_error_payload(self):
        r = requests.get(f"{BASE_URL}/api/public/equipment/nonexistent-slug/Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu", timeout=10)
        assert r.status_code in (200, 404)


class TestAuthNoRegression:
    """Ensure standard login flows still work — no regression from HOTFIX."""

    def test_admin_login(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test.admin@maintrix.com", "password": "admin123"},
            timeout=10,
        )
        assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text[:200]}"
        d = r.json()
        assert "access_token" in d
        assert d["user"]["email"] == "test.admin@maintrix.com"

    def test_pcm_login(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test.pcm@maintrix.com", "password": "pcm123"},
            timeout=10,
        )
        assert r.status_code == 200, f"PCM login failed: {r.status_code} {r.text[:200]}"
        assert "access_token" in r.json()

    def test_protected_route_still_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/ativos", timeout=10)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
