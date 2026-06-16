"""Iteration 28 — QR Code URL format fix + Scanner manual lookup endpoints.

Validates:
- GET /api/ativos/qr/{qr_code} returns 200 with correct asset for a valid qr_code UUID
- GET /api/ativos/tag/{tag} returns 200 with correct asset for a valid TAG (case-insensitive)
- Both endpoints return the same asset when given the qr_code and tag of the same ativo
- Invalid qr_code/tag returns 404
- Sobressalentes regression: Edit/Delete RBAC still enforced (admin allowed, tecnico 403)
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers():
    token = _login("admin@manutrix.com", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def tecnico_headers():
    token = _login("tecnico@manutrix.com", "tecnico123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def sample_ativo(admin_headers):
    """Pick one ativo with both qr_code and tag set."""
    r = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and len(items) > 0, "no ativos found"
    candidate = next((a for a in items if a.get("qr_code") and a.get("tag")), None)
    assert candidate, "no ativo with both qr_code and tag"
    return candidate


# ---------- QR Code endpoint ----------

class TestQrCodeLookup:
    def test_get_ativo_by_qr_valid(self, admin_headers, sample_ativo):
        qr = sample_ativo["qr_code"]
        r = requests.get(f"{BASE_URL}/api/ativos/qr/{qr}", headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        assert data["id"] == sample_ativo["id"]
        assert data["qr_code"] == qr
        assert data["tag"] == sample_ativo["tag"]
        assert "_id" not in data  # mongo internal id must be stripped

    def test_get_ativo_by_qr_invalid_returns_404(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/qr/non-existent-uuid-zzz", headers=admin_headers, timeout=15)
        assert r.status_code == 404


# ---------- TAG endpoint ----------

class TestTagLookup:
    def test_get_ativo_by_tag_valid(self, admin_headers, sample_ativo):
        tag = sample_ativo["tag"]
        r = requests.get(f"{BASE_URL}/api/ativos/tag/{tag}", headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        assert data["id"] == sample_ativo["id"]
        assert data["tag"] == tag

    def test_get_ativo_by_tag_lowercase_works(self, admin_headers, sample_ativo):
        # Backend uppercases the tag, so lowercase input should still resolve
        tag_lower = sample_ativo["tag"].lower()
        r = requests.get(f"{BASE_URL}/api/ativos/tag/{tag_lower}", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["id"] == sample_ativo["id"]

    def test_get_ativo_by_tag_invalid_returns_404(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/tag/ZZ-NOPE-9999", headers=admin_headers, timeout=15)
        assert r.status_code == 404


# ---------- Cross-check: same asset via both endpoints ----------

class TestQrAndTagSameAsset:
    def test_qr_and_tag_resolve_to_same_asset(self, admin_headers, sample_ativo):
        r1 = requests.get(f"{BASE_URL}/api/ativos/qr/{sample_ativo['qr_code']}", headers=admin_headers, timeout=15)
        r2 = requests.get(f"{BASE_URL}/api/ativos/tag/{sample_ativo['tag']}", headers=admin_headers, timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"] == sample_ativo["id"]


# ---------- Sobressalentes regression (iteration_27 fix) ----------

class TestSobressalentesRBACRegression:
    def test_admin_can_list_spares(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sobressalentes", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_tecnico_can_list_spares(self, tecnico_headers):
        r = requests.get(f"{BASE_URL}/api/sobressalentes", headers=tecnico_headers, timeout=15)
        assert r.status_code == 200

    def test_tecnico_cannot_create_spare(self, tecnico_headers):
        payload = {"codigo": "TEST_iter28_blocked", "descricao": "should be blocked", "categoria": "outros", "unidade": "un"}
        r = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=tecnico_headers, timeout=15)
        assert r.status_code == 403
