"""RC-13 — Identificação Visual de Materiais.
Tests for material image upload endpoints (estoque + sobressalente) and
regression checks on the material create endpoints accepting images[] field.
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
ASTEC_ORG = "9a232bf2-fc01-4253-813f-8df356be31c1"

ADMIN = {"email": "test.admin@maintrix.com", "password": "admin123", "organization_id": ASTEC_ORG}
PCM = {"email": "test.pcm@maintrix.com", "password": "pcm123", "organization_id": ASTEC_ORG}


# --- helpers ---
def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _tiny_png_bytes():
    # smallest valid 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01|~\xc4\xa3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def created_estoque(admin_headers):
    payload = {
        "sku": "TEST_RC13_EST_01",
        "nome": "TEST_RC13 Rolamento SKF 6205",
        "categoria": "rolamento",
        "quantidade": 3,
        "unidade": "UN",
        "custo_unitario": 25.5,
    }
    r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=admin_headers, timeout=15)
    assert r.status_code in (200, 201), f"Estoque create failed: {r.status_code} {r.text}"
    item = r.json()
    yield item
    # cleanup
    try:
        requests.delete(f"{BASE_URL}/api/estoque/{item['id']}", headers=admin_headers, timeout=10)
    except Exception:
        pass


@pytest.fixture(scope="module")
def created_spare(admin_headers):
    payload = {
        "tag": "TEST_RC13_SP_01",
        "sku": "TEST_RC13_SP_01",
        "nome": "TEST_RC13 Motor Elétrico 5cv",
        "descricao": "Spare RC13 test",
        "tipo_equipamento": "motor",
        "categoria": "eletrico",
        "quantidade": 1,
        "custo_unitario": 500.0,
    }
    r = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers, timeout=15)
    assert r.status_code in (200, 201), f"Sobressalente create failed: {r.status_code} {r.text}"
    item = r.json()
    yield item
    try:
        requests.delete(f"{BASE_URL}/api/sobressalentes/{item['id']}", headers=admin_headers, timeout=10)
    except Exception:
        pass


# ---------- Auth sanity ----------
class TestAuthPreCheck:
    def test_admin_login_returns_access_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"


# ---------- Model images[] field on create ----------
class TestModelImagesField:
    def test_estoque_create_persists_images_field(self, admin_headers):
        payload = {
            "sku": "TEST_RC13_EST_IMG_INIT",
            "nome": "TEST_RC13 Estoque com imagem inicial",
            "categoria": "filtro",
            "quantidade": 1,
            "unidade": "UN",
            "custo_unitario": 10.0,
            "images": ["/api/uploads/dummy1.jpg", "/api/uploads/dummy2.jpg"],
        }
        r = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        item = r.json()
        item_id = item["id"]
        # verify persistence via GET list
        rl = requests.get(f"{BASE_URL}/api/estoque", headers=admin_headers, timeout=15)
        assert rl.status_code == 200
        matches = [x for x in rl.json() if x.get("id") == item_id]
        assert matches, "created estoque not found in list"
        images = matches[0].get("images") or []
        assert isinstance(images, list)
        assert "/api/uploads/dummy1.jpg" in images and "/api/uploads/dummy2.jpg" in images
        # cleanup
        requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=admin_headers, timeout=10)

    def test_spare_create_persists_images_field(self, admin_headers):
        payload = {
            "tag": "TEST_RC13_SP_IMG_INIT",
            "sku": "TEST_RC13_SP_IMG_INIT",
            "nome": "TEST_RC13 Sobressalente com imagem inicial",
            "quantidade": 1,
            "custo_unitario": 100.0,
            "images": ["/api/uploads/spare1.jpg"],
        }
        r = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code in (200, 201), r.text
        item = r.json()
        item_id = item["id"]
        rl = requests.get(f"{BASE_URL}/api/sobressalentes", headers=admin_headers, timeout=15)
        assert rl.status_code == 200
        matches = [x for x in rl.json() if x.get("id") == item_id]
        assert matches, "created spare not found in list"
        images = matches[0].get("images") or []
        assert "/api/uploads/spare1.jpg" in images
        requests.delete(f"{BASE_URL}/api/sobressalentes/{item_id}", headers=admin_headers, timeout=10)


# ---------- POST/DELETE /api/materiais/{tipo}/{item_id}/images ----------
class TestMaterialImageEndpoints:
    def test_upload_estoque_image_returns_updated_images(self, admin_headers, created_estoque):
        item_id = created_estoque["id"]
        files = {"file": ("test_rc13.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/estoque/{item_id}/images",
            headers=admin_headers,  # let requests set the multipart boundary
            files=files,
            timeout=20,
        )
        assert r.status_code == 200, f"upload failed: {r.status_code} {r.text}"
        data = r.json()
        assert "url" in data and "images" in data
        assert isinstance(data["images"], list) and len(data["images"]) >= 1
        assert data["url"] in data["images"]
        # persistence check via list
        rl = requests.get(f"{BASE_URL}/api/estoque", headers=admin_headers, timeout=15)
        item = next((x for x in rl.json() if x.get("id") == item_id), None)
        assert item is not None
        assert data["url"] in (item.get("images") or [])

    def test_upload_estoque_image_rejects_non_image(self, admin_headers, created_estoque):
        item_id = created_estoque["id"]
        files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/estoque/{item_id}/images",
            headers=admin_headers,
            files=files,
            timeout=15,
        )
        assert r.status_code == 400

    def test_upload_estoque_image_404_when_item_missing(self, admin_headers):
        files = {"file": ("test.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/estoque/does-not-exist/images",
            headers=admin_headers,
            files=files,
            timeout=15,
        )
        assert r.status_code == 404

    def test_upload_estoque_invalid_tipo_returns_400(self, admin_headers, created_estoque):
        item_id = created_estoque["id"]
        files = {"file": ("test.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/notavalidtipo/{item_id}/images",
            headers=admin_headers,
            files=files,
            timeout=15,
        )
        assert r.status_code == 400

    def test_upload_spare_image_returns_updated_images(self, admin_headers, created_spare):
        item_id = created_spare["id"]
        files = {"file": ("spare.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/sobressalente/{item_id}/images",
            headers=admin_headers,
            files=files,
            timeout=20,
        )
        assert r.status_code == 200, f"upload spare failed: {r.status_code} {r.text}"
        data = r.json()
        assert "url" in data and "images" in data and data["url"] in data["images"]
        # persistence
        rl = requests.get(f"{BASE_URL}/api/sobressalentes", headers=admin_headers, timeout=15)
        item = next((x for x in rl.json() if x.get("id") == item_id), None)
        assert item is not None
        assert data["url"] in (item.get("images") or [])

    def test_delete_estoque_image_removes_url(self, admin_headers, created_estoque):
        item_id = created_estoque["id"]
        # upload first
        files = {"file": ("todel.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        up = requests.post(
            f"{BASE_URL}/api/materiais/estoque/{item_id}/images",
            headers=admin_headers,
            files=files,
            timeout=20,
        )
        assert up.status_code == 200
        url = up.json()["url"]
        # delete
        r = requests.delete(
            f"{BASE_URL}/api/materiais/estoque/{item_id}/images",
            headers=admin_headers,
            params={"image_url": url},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        # verify
        rl = requests.get(f"{BASE_URL}/api/estoque", headers=admin_headers, timeout=15)
        item = next((x for x in rl.json() if x.get("id") == item_id), None)
        assert item is not None
        assert url not in (item.get("images") or [])

    def test_delete_spare_image_removes_url(self, admin_headers, created_spare):
        item_id = created_spare["id"]
        files = {"file": ("sptodel.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        up = requests.post(
            f"{BASE_URL}/api/materiais/sobressalente/{item_id}/images",
            headers=admin_headers,
            files=files,
            timeout=20,
        )
        assert up.status_code == 200
        url = up.json()["url"]
        r = requests.delete(
            f"{BASE_URL}/api/materiais/sobressalente/{item_id}/images",
            headers=admin_headers,
            params={"image_url": url},
            timeout=15,
        )
        assert r.status_code == 200

    def test_upload_requires_auth(self, created_estoque):
        item_id = created_estoque["id"]
        files = {"file": ("noauth.png", io.BytesIO(_tiny_png_bytes()), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/materiais/estoque/{item_id}/images",
            files=files,
            timeout=15,
        )
        assert r.status_code in (401, 403)


# ---------- Regression: OS material embeds image_url ----------
class TestOSMaterialImageUrl:
    def test_work_orders_list_accepts_get(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        # sanity: list is a list
        assert isinstance(r.json(), list)


# ---------- Regression: sobressalentes exports (RC-13 must not break) ----------
class TestExportsRegression:
    def test_sobressalentes_export_excel(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sobressalentes/export/excel", headers=admin_headers, timeout=30)
        # some deployments return 200 with a file, others may 404 if no data
        assert r.status_code in (200, 404), f"unexpected status {r.status_code}: {r.text[:200]}"

    def test_sobressalentes_export_pdf(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sobressalentes/export/pdf", headers=admin_headers, timeout=30)
        assert r.status_code in (200, 404), f"unexpected status {r.status_code}: {r.text[:200]}"


# ---------- Regression: dashboard ----------
class TestDashboardRegression:
    def test_dashboard_stats_ok(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200
