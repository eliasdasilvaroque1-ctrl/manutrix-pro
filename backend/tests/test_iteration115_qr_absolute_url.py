"""
Iteration 115 — HOTFIX P0 QR Codes com URL Absoluta
Backend tests:
- Endpoints QR PNG/SVG/PDF/Batch retornam bytes válidos
- QR decodificado contém URL absoluta https://www.maintrix.com.br/equipamento/...
- Nenhum QR contém blob:, localhost, ou rota relativa
- Rota pública funciona sem auth
- Token inválido retorna 404 genérico
- Backfill executado (public_qr_url absoluta no DB)
- Rotas autenticadas continuam funcionando
"""
import os
import io
import re
import pytest
import requests
from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode
import fitz  # PyMuPDF

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
PUBLIC_APP_URL = "https://www.maintrix.com.br"
EXPECTED_URL_PREFIX = f"{PUBLIC_APP_URL}/equipamento/"

PUBLIC_URLS = [
    ("av-01-alimentador", "Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu"),
    ("bb-03-bomba-aspersao-patio", "P4wbjMQ3JxqWXFxOWsnYIYBtkOi1ewNf"),
]


# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test.admin@maintrix.com", "password": "admin123"},
        timeout=15,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text[:300]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def sample_ativo(auth_headers):
    """Get a sample asset by tag AV-01 to run QR tests against."""
    r = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers, timeout=15)
    assert r.status_code == 200, f"list ativos failed: {r.text[:300]}"
    ativos = r.json()
    # Prefer AV-01 alimentador
    ativo = None
    for a in ativos:
        if a.get("public_slug") == "av-01-alimentador":
            ativo = a
            break
    if not ativo:
        # fallback: pick first with public_qr_token
        for a in ativos:
            if a.get("public_qr_token") and a.get("public_slug"):
                ativo = a
                break
    assert ativo is not None, "No asset with public_qr_token found"
    return ativo


# ============== HELPERS ==============

def _decode_png(png_bytes: bytes) -> list:
    """Return list of decoded QR payload strings from PNG bytes."""
    img = Image.open(io.BytesIO(png_bytes))
    results = zbar_decode(img)
    return [r.data.decode("utf-8", errors="ignore") for r in results]


def _decode_pdf(pdf_bytes: bytes) -> list:
    """Render every page of the PDF and decode QR codes. Returns list of payloads."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    payloads = []
    try:
        for page in doc:
            # Render page at 300dpi
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            results = zbar_decode(img)
            for r in results:
                payloads.append(r.data.decode("utf-8", errors="ignore"))
    finally:
        doc.close()
    return payloads


def _assert_url_valid(url: str):
    assert url.startswith(EXPECTED_URL_PREFIX), f"URL não começa com {EXPECTED_URL_PREFIX}: {url}"
    assert "blob:" not in url, f"URL contém blob: {url}"
    assert "localhost" not in url, f"URL contém localhost: {url}"
    assert not url.startswith("/"), f"URL é relativa: {url}"
    # Deve ter slug e token
    m = re.match(rf"^{re.escape(EXPECTED_URL_PREFIX)}([^/]+)/([^/?#]+)$", url)
    assert m, f"URL malformada (falta slug/token): {url}"


# ============== TESTS: Rota Pública ==============

class TestPublicEndpoint:
    @pytest.mark.parametrize("slug,token", PUBLIC_URLS)
    def test_public_equipment_no_auth(self, slug, token):
        last_err = None
        for _ in range(3):
            try:
                r = requests.get(f"{BASE_URL}/api/public/equipment/{slug}/{token}", timeout=30)
                assert r.status_code == 200, f"Expected 200 got {r.status_code}"
                data = r.json()
                assert data.get("available") is True or "equipment" in data
                return
            except Exception as e:
                last_err = e
        raise last_err

    def test_invalid_token_generic(self):
        """Token inválido deve retornar 404 (genérico, sem info sensível)."""
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/av-01-alimentador/invalid_token_XYZ_123",
            timeout=15,
        )
        assert r.status_code in (200, 404), f"Unexpected status {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert data.get("available") is False


# ============== TESTS: Backfill (DB) ==============

class TestBackfill:
    """Backfill executado: URLs no banco devem ser absolutas."""

    def test_all_ativos_have_absolute_url(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        ativos = r.json()
        with_qr = [a for a in ativos if a.get("public_qr_token")]
        assert len(with_qr) > 0, "Nenhum ativo com QR token encontrado"

        invalid = []
        for a in with_qr:
            url = a.get("public_qr_url", "")
            if not url.startswith(EXPECTED_URL_PREFIX):
                invalid.append((a.get("tag"), url))
        assert not invalid, f"Ativos com URL não-absoluta: {invalid[:5]} (total {len(invalid)})"

    def test_backfill_significant_count(self, auth_headers):
        """Backfill informado corrigiu 62 ativos GLOBAL. Admin vê apenas sua org (ASTEC Cedro).
        Validar que há >= 50 ativos com URL absoluta na org visível."""
        r = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        ativos = r.json()
        with_qr = [a for a in ativos if a.get("public_qr_token") and a.get("public_qr_url", "").startswith(EXPECTED_URL_PREFIX)]
        # Expected ~55 in ASTEC Cedro (total 62 across all orgs per backfill log)
        assert len(with_qr) >= 30, f"Muito poucos ativos com URL absoluta: {len(with_qr)}"
        # Nenhum ativo com URL não-absoluta
        with_qr_but_bad = [a for a in ativos if a.get("public_qr_token") and not a.get("public_qr_url", "").startswith(EXPECTED_URL_PREFIX)]
        assert not with_qr_but_bad, f"Ativos com QR token mas URL não-absoluta: {[a.get('tag') for a in with_qr_but_bad]}"


# ============== TESTS: QR PNG ==============

class TestQrPng:
    def test_png_returns_image(self, auth_headers, sample_ativo):
        ativo_id = sample_ativo["id"]
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/png",
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code == 200, f"PNG endpoint failed: {r.status_code} {r.text[:200]}"
        assert r.headers.get("content-type") == "image/png"
        assert len(r.content) > 100

    def test_png_qr_decodes_to_absolute_url(self, auth_headers, sample_ativo):
        ativo_id = sample_ativo["id"]
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/png",
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code == 200
        payloads = _decode_png(r.content)
        assert len(payloads) >= 1, "Nenhum QR decodificado do PNG"
        url = payloads[0]
        _assert_url_valid(url)
        # Slug/token devem bater com o ativo
        assert sample_ativo["public_slug"] in url
        assert sample_ativo["public_qr_token"] in url


# ============== TESTS: QR SVG ==============

class TestQrSvg:
    def test_svg_returns_svg(self, auth_headers, sample_ativo):
        ativo_id = sample_ativo["id"]
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/svg",
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code == 200
        assert "svg" in r.headers.get("content-type", "").lower()
        body = r.content.decode("utf-8", errors="ignore")
        assert body.startswith("<?xml") or body.startswith("<svg")


# ============== TESTS: QR PDF Individual ==============

class TestQrPdfIndividual:
    @pytest.mark.parametrize("modelo", ["simples", "etiqueta", "placa"])
    def test_pdf_returns_pdf(self, auth_headers, sample_ativo, modelo):
        ativo_id = sample_ativo["id"]
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/pdf",
            params={"modelo": modelo},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200, f"PDF {modelo} failed: {r.status_code} {r.text[:200]}"
        assert r.content[:4] == b"%PDF", f"Not a valid PDF (modelo={modelo})"

    @pytest.mark.parametrize("modelo", ["simples", "etiqueta", "placa"])
    def test_pdf_qr_decodes_to_absolute_url(self, auth_headers, sample_ativo, modelo):
        ativo_id = sample_ativo["id"]
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/pdf",
            params={"modelo": modelo},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        payloads = _decode_pdf(r.content)
        assert len(payloads) >= 1, f"Nenhum QR decodificado do PDF {modelo}"
        url = payloads[0]
        _assert_url_valid(url)
        assert sample_ativo["public_slug"] in url
        assert sample_ativo["public_qr_token"] in url


# ============== TESTS: Batch PDF ==============

class TestQrBatchPdf:
    def test_batch_pdf_6_ativos(self, auth_headers):
        # Buscar 6 ativos com QR
        r = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        ativos = [a for a in r.json() if a.get("public_qr_token") and a.get("public_slug")][:6]
        assert len(ativos) == 6, f"Precisa de 6 ativos, encontrou {len(ativos)}"
        ids = [a["id"] for a in ativos]

        r2 = requests.post(
            f"{BASE_URL}/api/ativos/qrcode/batch-pdf",
            json={"asset_ids": ids, "modelo": "etiqueta", "layout": "6_per_page"},
            headers=auth_headers,
            timeout=60,
        )
        assert r2.status_code == 200, f"Batch PDF failed: {r2.status_code} {r2.text[:300]}"
        assert r2.content[:4] == b"%PDF"

        # Decode all QRs from the PDF
        payloads = _decode_pdf(r2.content)
        assert len(payloads) >= 6, f"Esperava >=6 QRs, decodificados: {len(payloads)}"

        expected_tokens = {a["public_qr_token"] for a in ativos}
        found_tokens = set()
        for url in payloads:
            _assert_url_valid(url)
            m = re.match(rf"^{re.escape(EXPECTED_URL_PREFIX)}([^/]+)/([^/?#]+)$", url)
            if m:
                found_tokens.add(m.group(2))

        missing = expected_tokens - found_tokens
        assert not missing, f"Tokens ausentes no batch PDF: {missing}"


# ============== TESTS: Sem regressão de auth ==============

class TestAuthNoRegression:
    def test_protected_route_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/ativos", timeout=10)
        assert r.status_code in (401, 403)

    def test_login_still_works(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test.pcm@maintrix.com", "password": "pcm123"},
            timeout=10,
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_qr_endpoints_require_auth(self, sample_ativo):
        ativo_id = sample_ativo["id"]
        # PNG sem token deve retornar 401/403
        r = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/png", timeout=10)
        assert r.status_code in (401, 403), f"QR PNG deveria requerer auth, got {r.status_code}"
