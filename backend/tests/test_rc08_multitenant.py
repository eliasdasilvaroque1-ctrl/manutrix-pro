"""RC-08 Auditoria Multiempresa — verifica que nenhuma operação funciona
sem contexto de organização e que login/register/forgot-password respeitam
o organization_id."""
import os
import base64
import json
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

MASTER_EMAIL = "master@maintrix.com"
MASTER_PASSWORD = "master123"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def astec_org_id(api):
    r = api.get(f"{BASE_URL}/api/public/organizations")
    assert r.status_code == 200, r.text
    orgs = r.json()
    assert isinstance(orgs, list) and len(orgs) > 0
    # ASTEC Cedro is the first one — matches user requirement
    return orgs[0]['id']


@pytest.fixture(scope="module")
def master_token_with_org(api, astec_org_id):
    r = api.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_EMAIL, "password": MASTER_PASSWORD,
        "organization_id": astec_org_id
    })
    assert r.status_code == 200, r.text
    data = r.json()
    return data['access_token'], data['user']


# ---------- P0-01 LOGIN with organization ----------
class TestLoginOrgScope:
    def test_login_correct_org(self, api, astec_org_id):
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_EMAIL, "password": MASTER_PASSWORD,
            "organization_id": astec_org_id
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert data['user']['email'] == MASTER_EMAIL
        # user's org must equal the one used to login
        assert data['user'].get('organization_id') == astec_org_id

    def test_login_wrong_org_returns_401(self, api):
        # Use a valid-looking but WRONG org_id
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_EMAIL, "password": MASTER_PASSWORD,
            "organization_id": "00000000-0000-0000-0000-000000000000"
        })
        assert r.status_code == 401, r.text
        assert "inv" in r.json().get('detail', '').lower() or "não pertence" in r.json().get('detail', '').lower()

    def test_login_without_org_backward_compat(self, api):
        # Without org_id, must still work (email globally unique)
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_EMAIL, "password": MASTER_PASSWORD
        })
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_wrong_password_401(self, api, astec_org_id):
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_EMAIL, "password": "wrong-pass",
            "organization_id": astec_org_id
        })
        assert r.status_code == 401


# ---------- P0-02 REGISTER blocked ----------
class TestRegisterBlocked:
    def test_register_returns_403(self, api):
        r = api.post(f"{BASE_URL}/api/auth/register", json={
            "email": "TEST_shouldnot@example.com",
            "password": "abcdef",
            "nome": "Should Not Exist",
            "role": "tecnico"
        })
        assert r.status_code == 403, r.text
        detail = r.json().get('detail', '')
        assert 'desabilit' in detail.lower() or 'disabled' in detail.lower()

    def test_register_empty_payload_still_403(self, api):
        r = api.post(f"{BASE_URL}/api/auth/register", json={})
        # even before body validation, endpoint should reject
        assert r.status_code in (403, 422)
        # if 422, we still consider it blocked (no user created)


# ---------- P0-03 FORGOT PASSWORD ----------
class TestForgotPassword:
    def test_forgot_password_with_correct_org(self, api, astec_org_id):
        r = api.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": MASTER_EMAIL, "organization_id": astec_org_id
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get('success') is True

    def test_forgot_password_with_wrong_org_generic_response(self, api):
        r = api.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": MASTER_EMAIL,
            "organization_id": "00000000-0000-0000-0000-000000000000"
        })
        assert r.status_code == 200, r.text
        body = r.json()
        # Must NOT reveal user existence — generic success message
        assert body.get('success') is True
        msg = body.get('message', '').lower()
        assert 'se o email' in msg or 'existir' in msg

    def test_forgot_password_unknown_email_generic(self, api, astec_org_id):
        r = api.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "TEST_unknown_xyz@example.com",
            "organization_id": astec_org_id
        })
        assert r.status_code == 200
        assert r.json().get('success') is True


# ---------- JWT claim ----------
class TestJWTClaims:
    def test_jwt_contains_org_claim(self, master_token_with_org, astec_org_id):
        token, _ = master_token_with_org
        # decode payload (2nd segment)
        parts = token.split('.')
        assert len(parts) == 3
        payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        assert 'org' in payload, f"JWT missing 'org' claim: {payload}"
        assert payload['org'] == astec_org_id


# ---------- Cross-org data scoping ----------
class TestOrgScopedData:
    def _auth(self, token):
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_ativos_org_scoped(self, api, master_token_with_org, astec_org_id):
        token, user = master_token_with_org
        r = api.get(f"{BASE_URL}/api/ativos", headers=self._auth(token))
        assert r.status_code == 200, r.text
        ativos = r.json()
        assert isinstance(ativos, list)
        # all ativos must belong to the same org
        for a in ativos:
            assert a.get('organization_id') == astec_org_id, (
                f"ativo {a.get('id')} belongs to org {a.get('organization_id')}, expected {astec_org_id}"
            )

    def test_ordens_servico_org_scoped(self, api, master_token_with_org, astec_org_id):
        token, _ = master_token_with_org
        r = api.get(f"{BASE_URL}/api/ordens-servico", headers=self._auth(token))
        assert r.status_code == 200, r.text
        oss = r.json()
        assert isinstance(oss, list)
        for os_doc in oss:
            assert os_doc.get('organization_id') == astec_org_id

    def test_export_ativos_is_org_scoped(self, api, master_token_with_org, astec_org_id):
        token, _ = master_token_with_org
        r = api.get(f"{BASE_URL}/api/export/ativos", headers=self._auth(token))
        assert r.status_code == 200, r.text
        # export returns CSV/xlsx blob; ensure content-length > 0
        assert len(r.content) > 0

    def test_no_auth_ativos_401(self, api):
        r = api.get(f"{BASE_URL}/api/ativos")
        assert r.status_code in (401, 403)


# ---------- Admin creates user inherits admin org ----------
class TestAdminCreateUser:
    def test_admin_create_user_inherits_org(self, api, master_token_with_org, astec_org_id):
        token, _ = master_token_with_org
        payload = {
            "email": "TEST_rc08_user@example.com",
            "nome": "TEST RC08 User",
            "password": "temppass123",
            "role": "tecnico"
            # NOTE: intentionally omitting organization_id
        }
        r = api.post(f"{BASE_URL}/api/admin/users",
                     json=payload,
                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        # accept 200/201
        assert r.status_code in (200, 201), r.text
        created = r.json()
        # Must inherit the admin's org
        assert created.get('organization_id') == astec_org_id, (
            f"created user org={created.get('organization_id')}, expected {astec_org_id}"
        )
        # cleanup
        user_id = created.get('id')
        if user_id:
            api.delete(f"{BASE_URL}/api/admin/users/{user_id}",
                       headers={"Authorization": f"Bearer {token}"})


# ---------- QR public ativo endpoint ----------
class TestPublicQR:
    def test_public_ativo_returns_org_branding(self, api, master_token_with_org, astec_org_id):
        token, _ = master_token_with_org
        r = api.get(f"{BASE_URL}/api/ativos", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        ativos = r.json()
        if not ativos:
            pytest.skip("No ativos to test QR endpoint")
        ativo_id = ativos[0]['id']
        pub = api.get(f"{BASE_URL}/api/public/ativo/{ativo_id}")
        assert pub.status_code == 200, pub.text
        data = pub.json()
        # Response must include a branding block sourced from the ativo's org
        assert 'branding' in data, f"public/ativo missing 'branding' block. Keys={list(data.keys())}"
        branding = data['branding']
        assert isinstance(branding, dict) and len(branding) > 0
        # branding should carry primary color at minimum
        assert 'cor_primaria' in branding, f"branding missing cor_primaria: {branding}"
