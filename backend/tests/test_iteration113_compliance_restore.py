"""
Iteration 113 — Restoration of legal compliance docs (Privacy Policy + Terms of Use)
Verifies:
  - /api/compliance/privacy returns real content (>1000 chars, not placeholder)
  - /api/compliance/terms  returns real content (>1000 chars, not placeholder)
  - /api/compliance/about  environment == "preview"
  - /api/health healthy
  - Auth for admin, pcm, master
  - RBAC: unauth → 403 on /api/ativos, 401 on /api/storage/*
  - GET /api/ativos returns 55+ ativos and /api/ordens-servico returns 100+ OS
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or "https://procure-manutrix.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")

ORG_ID_ASTEC = "9a232bf2-fc01-4253-813f-8df356be31c1"

ADMIN = {"email": "test.admin@maintrix.com", "password": "admin123"}
PCM = {"email": "test.pcm@maintrix.com", "password": "pcm123"}
MASTER = {"email": "master@maintrix.com", "password": "master123", "organization_id": ORG_ID_ASTEC}


# ----------- Compliance / Health / About -----------

def test_health_ok():
    r = requests.get(f"{BASE_URL}/api/health", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "healthy"
    assert d["database"]["connected"] is True


def test_compliance_privacy_full_content():
    r = requests.get(f"{BASE_URL}/api/compliance/privacy", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "content" in d and "version" in d
    c = d["content"]
    assert c != "Documento em preparação."
    assert len(c) > 1000, f"privacy content too short: {len(c)} chars"
    assert "Política de Privacidade" in c
    assert "MAINTRIX Enterprise" in c
    # Count sections (## 1. ... ## 11.)
    for section in ["## 1.", "## 2.", "## 3.", "## 4.", "## 5.",
                    "## 6.", "## 7.", "## 8.", "## 9.", "## 10.", "## 11."]:
        assert section in c, f"missing section {section}"


def test_compliance_terms_full_content():
    r = requests.get(f"{BASE_URL}/api/compliance/terms", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "content" in d and "version" in d
    c = d["content"]
    assert c != "Documento em preparação."
    assert len(c) > 1000, f"terms content too short: {len(c)} chars"
    assert "Termos de Uso" in c
    assert "MAINTRIX Enterprise" in c
    for section in ["## 1.", "## 2.", "## 3.", "## 4.", "## 5.",
                    "## 6.", "## 7.", "## 8.", "## 9.", "## 10."]:
        assert section in c, f"missing section {section}"


def test_compliance_about_environment_preview():
    r = requests.get(f"{BASE_URL}/api/compliance/about", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["environment"] == "preview"
    assert d["product"] == "MAINTRIX Enterprise"
    assert d["terms_version"]
    assert d["privacy_version"]


# ----------- Auth -----------

def _login(payload):
    return requests.post(f"{BASE_URL}/api/auth/login", json=payload, timeout=30)


def test_login_admin():
    r = _login(ADMIN)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("access_token")
    assert d.get("user", {}).get("email") == ADMIN["email"]


def test_login_pcm():
    r = _login(PCM)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("access_token")
    assert d.get("user", {}).get("email") == PCM["email"]


def test_login_master_requires_org():
    r = _login(MASTER)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("access_token")


# ----------- RBAC / Security -----------

def test_ativos_unauth_403():
    r = requests.get(f"{BASE_URL}/api/ativos", timeout=30)
    # FastAPI HTTPBearer returns 403 for missing creds
    assert r.status_code in (401, 403), r.status_code


def test_storage_unauth_401_or_403():
    r = requests.get(f"{BASE_URL}/api/storage/some-private-file.pdf", timeout=30)
    assert r.status_code in (401, 403), r.status_code


# ----------- Data checks with auth -----------

@pytest.fixture(scope="module")
def admin_token():
    r = _login(ADMIN)
    if r.status_code != 200:
        pytest.skip("Admin login failed")
    return r.json()["access_token"]


def test_get_ativos_auth_returns_min_55(admin_token):
    r = requests.get(f"{BASE_URL}/api/ativos", headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    items = data if isinstance(data, list) else data.get("items") or data.get("data") or []
    assert len(items) >= 55, f"expected >=55 ativos, got {len(items)}"


def test_get_ordens_servico_auth_returns_min_100(admin_token):
    r = requests.get(f"{BASE_URL}/api/ordens-servico", headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    items = data if isinstance(data, list) else data.get("items") or data.get("data") or []
    assert len(items) >= 100, f"expected >=100 OS, got {len(items)}"
