"""Iteration 42 - Storage migration validation (Emergent Object Storage)
Validates new uploads route to cloud (/api/storage/) and proxy serves files.
"""
import os
import io
import pytest
import requests
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASS = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def jpeg_bytes():
    """Generate a small valid JPEG in-memory."""
    img = Image.new("RGB", (32, 32), color=(120, 80, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


@pytest.fixture(scope="module")
def pdf_bytes():
    """Minimal valid PDF (1 page, empty)."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 100 100]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000098 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n150\n%%EOF\n"
    )


@pytest.fixture(scope="module")
def work_order_id(headers):
    """Pick any existing OS to upload to."""
    r = requests.get(f"{API}/ordens-servico", headers=headers, timeout=15)
    assert r.status_code == 200, f"OS list failed: {r.status_code} {r.text[:200]}"
    ws = r.json()
    if isinstance(ws, dict):
        ws = ws.get("items") or ws.get("data") or []
    assert len(ws) > 0, "No work orders available"
    return ws[0]["id"]


@pytest.fixture(scope="module")
def inspecao_id(headers):
    r = requests.get(f"{API}/inspecoes", headers=headers, timeout=15)
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0, "No inspecoes available"
    return items[0]["id"]


@pytest.fixture(scope="module")
def anomalia_id(headers):
    r = requests.get(f"{API}/anomalias", headers=headers, timeout=15)
    assert r.status_code == 200
    items = r.json()
    if not items:
        pytest.skip("No anomalias available")
    return items[0]["id"]


@pytest.fixture(scope="module")
def ativo_id(headers):
    r = requests.get(f"{API}/ativos", headers=headers, timeout=15)
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0, "No ativos available"
    return items[0]["id"]


# -------- Storage availability + basic upload --------
class TestStorageInfrastructure:
    def test_general_upload_to_cloud(self, headers, jpeg_bytes):
        """POST /api/upload returns cloud URL when objstore available."""
        files = {"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
        r = requests.post(f"{API}/upload", headers=headers, files=files, timeout=30)
        assert r.status_code == 200, f"upload failed: {r.text}"
        data = r.json()
        assert data["storage"] == "cloud", f"Storage backend not cloud: {data}"
        assert data["url"].startswith("/api/storage/"), f"URL not cloud: {data['url']}"

        # Verify proxy serves it back
        full = f"{BASE_URL}{data['url']}"
        rg = requests.get(full, timeout=30)
        assert rg.status_code == 200
        assert rg.headers.get("Content-Type", "").startswith("image/")
        assert len(rg.content) == len(jpeg_bytes)


# -------- Attachment upload tests --------
class TestAttachmentUploadCloud:
    def _upload_attach(self, headers, entity_type, entity_id, content, fname, ctype, categoria="foto"):
        data = {"entity_type": entity_type, "entity_id": entity_id, "categoria": categoria}
        files = {"file": (fname, content, ctype)}
        r = requests.post(f"{API}/attachments", headers=headers, data=data, files=files, timeout=30)
        return r

    def test_upload_work_order_photo(self, headers, work_order_id, jpeg_bytes):
        r = self._upload_attach(headers, "work_order", work_order_id, jpeg_bytes, "TEST_os_photo.jpg", "image/jpeg")
        assert r.status_code == 200, f"WO upload failed: {r.text}"
        body = r.json()
        assert "/api/storage/" in body["file_url"], f"URL not cloud: {body['file_url']}"
        # Verify retrieval via proxy
        rg = requests.get(f"{BASE_URL}{body['file_url']}", timeout=30)
        assert rg.status_code == 200

    def test_upload_inspection_photo(self, headers, inspecao_id, jpeg_bytes):
        r = self._upload_attach(headers, "inspection", inspecao_id, jpeg_bytes, "TEST_insp.jpg", "image/jpeg")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "/api/storage/" in body["file_url"]
        rg = requests.get(f"{BASE_URL}{body['file_url']}", timeout=30)
        assert rg.status_code == 200

    def test_upload_anomalia_attachment(self, headers, anomalia_id, jpeg_bytes):
        r = self._upload_attach(headers, "anomalia", anomalia_id, jpeg_bytes, "TEST_anom.jpg", "image/jpeg")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "/api/storage/" in body["file_url"]
        rg = requests.get(f"{BASE_URL}{body['file_url']}", timeout=30)
        assert rg.status_code == 200


# -------- Manual PDF upload --------
class TestManualUploadCloud:
    def test_upload_manual_pdf(self, headers, ativo_id, pdf_bytes):
        files = {"file": ("TEST_manual.pdf", pdf_bytes, "application/pdf")}
        r = requests.post(f"{API}/ativos/{ativo_id}/manual", headers=headers, files=files, timeout=60)
        assert r.status_code == 200, f"Manual upload failed: {r.text}"
        body = r.json()
        assert body.get("success") is True
        manual = body["manual"]
        assert "/api/storage/" in manual["url"], f"manual url not cloud: {manual['url']}"
        # Verify proxy retrieval
        rg = requests.get(f"{BASE_URL}{manual['url']}", timeout=30)
        assert rg.status_code == 200
        assert rg.headers.get("Content-Type", "").startswith("application/pdf")


# -------- Migrated data verification (via list endpoints) --------
class TestMigratedDataIntegrity:
    def test_existing_attachments_all_cloud(self, headers, work_order_id):
        """List attachments and verify file_url points to /api/storage/."""
        r = requests.get(f"{API}/attachments/work_order/{work_order_id}", headers=headers, timeout=15)
        assert r.status_code == 200
        attaches = r.json()
        local_count = 0
        cloud_count = 0
        for a in attaches:
            if a["file_url"].startswith("/api/storage/"):
                cloud_count += 1
            elif a["file_url"].startswith("/api/uploads/"):
                local_count += 1
        # After migration there should be 0 local
        assert local_count == 0, f"Found {local_count} attachments still on local disk for this WO"

    def test_all_existing_attachments_cloud_global(self, headers):
        """Iterate first 20 ordens-servico and verify all attachments are on cloud."""
        r = requests.get(f"{API}/ordens-servico", headers=headers, timeout=20)
        assert r.status_code == 200
        ws = r.json()
        if isinstance(ws, dict):
            ws = ws.get("items") or ws.get("data") or []
        local_urls = []
        cloud_urls = 0
        for w in ws[:30]:
            ra = requests.get(f"{API}/attachments/work_order/{w['id']}", headers=headers, timeout=15)
            if ra.status_code != 200:
                continue
            for a in ra.json():
                if a["file_url"].startswith("/api/storage/"):
                    cloud_urls += 1
                elif a["file_url"].startswith("/api/uploads/"):
                    local_urls.append(a["file_url"])
        assert not local_urls, f"Found {len(local_urls)} attachments still local: {local_urls[:5]}"
        print(f"Verified {cloud_urls} attachments on cloud across {len(ws[:30])} OS")

    def test_all_existing_manuais_cloud_global(self, headers):
        """Iterate ativos and verify all manuais use /api/storage/."""
        r = requests.get(f"{API}/ativos", headers=headers, timeout=20)
        assert r.status_code == 200
        ativos = r.json()
        local_manuais = []
        cloud_manuais = 0
        for at in ativos[:60]:
            rm = requests.get(f"{API}/ativos/{at['id']}/manuais", headers=headers, timeout=15)
            if rm.status_code != 200:
                continue
            for m in rm.json():
                url = m.get("url") or m.get("filepath", "")
                if url.startswith("/api/storage/"):
                    cloud_manuais += 1
                elif url.startswith("/api/uploads/"):
                    local_manuais.append(url)
        assert not local_manuais, f"Found {len(local_manuais)} manuais still local: {local_manuais[:5]}"
        print(f"Verified {cloud_manuais} manuais on cloud across {len(ativos[:60])} ativos")

    def test_list_manuais_for_ativo(self, headers, ativo_id):
        r = requests.get(f"{API}/ativos/{ativo_id}/manuais", headers=headers, timeout=15)
        assert r.status_code == 200
        manuais = r.json()
        for m in manuais:
            url = m.get("url") or m.get("filepath")
            assert url, f"Manual missing url: {m}"
            # After migration, should be /api/storage/
            assert "/api/storage/" in url, f"Manual url not migrated: {url}"


# -------- Proxy endpoint behavior --------
class TestStorageProxy:
    def test_unknown_path_returns_404(self):
        r = requests.get(f"{API}/storage/manutrix/nonexistent/abcd/zzzz.jpg", timeout=15)
        assert r.status_code == 404

    def test_known_migrated_attachment_returns_200(self, headers, work_order_id, jpeg_bytes):
        # Upload one to ensure at least one cloud path exists tied to this WO
        data = {"entity_type": "work_order", "entity_id": work_order_id, "categoria": "foto"}
        files = {"file": ("TEST_proxy.jpg", jpeg_bytes, "image/jpeg")}
        ru = requests.post(f"{API}/attachments", headers=headers, data=data, files=files, timeout=30)
        assert ru.status_code == 200
        url = ru.json()["file_url"]
        rg = requests.get(f"{BASE_URL}{url}", timeout=30)
        assert rg.status_code == 200


# -------- Regression: critical list endpoints --------
class TestRegressionListEndpoints:
    def test_dashboard(self, headers):
        r = requests.get(f"{API}/dashboard/stats", headers=headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_kanban_os(self, headers):
        r = requests.get(f"{API}/ordens-servico", headers=headers, timeout=15)
        assert r.status_code == 200

    def test_ativos_list(self, headers):
        r = requests.get(f"{API}/ativos", headers=headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_inspecoes_list(self, headers):
        r = requests.get(f"{API}/inspecoes", headers=headers, timeout=15)
        assert r.status_code == 200

    def test_login_tecnico(self):
        r = requests.post(f"{API}/auth/login", json={"email": "tecnico@manutrix.com", "password": "tecnico123"}, timeout=15)
        assert r.status_code == 200
        assert "access_token" in r.json()
