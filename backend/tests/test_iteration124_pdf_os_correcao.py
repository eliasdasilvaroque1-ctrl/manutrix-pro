"""
Iteration 124 — PDF OS Correção (Modo Econômico).
Tests the immediate PDF correction: no fictitious CNPJ, no QR on OS, procedure section visible,
compacted layout, correct footer.

Test OS IDs:
- be9878f1-71ab-476e-b491-b1af7c402685 (no procedure, must be 1 page)
- ff2bb384-6d68-4f29-9584-5e5aeb9e5035 (with procedure PROC-0001)
- c8f9b1ea-ab6f-41e5-b690-9a7c0c840e62 (empty fields)
"""
import os
import io
import re
import pytest
import requests
import fitz  # pymupdf

# Load frontend/.env to get REACT_APP_BACKEND_URL
if not os.environ.get('REACT_APP_BACKEND_URL'):
    try:
        with open('/app/frontend/.env') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    os.environ['REACT_APP_BACKEND_URL'] = line.split('=', 1)[1].strip()
                    break
    except Exception:
        pass

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

OS_NO_PROC = "be9878f1-71ab-476e-b491-b1af7c402685"
OS_WITH_PROC = "ff2bb384-6d68-4f29-9584-5e5aeb9e5035"
OS_EMPTY_FIELDS = "c8f9b1ea-ab6f-41e5-b690-9a7c0c840e62"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test.admin@maintrix.com",
        "password": "admin123",
    })
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


def _fetch_pdf(client, os_id):
    r = client.get(f"{BASE_URL}/api/ordens-servico/{os_id}/pdf?modo=digital", timeout=60)
    assert r.status_code == 200, f"PDF fetch failed for {os_id}: {r.status_code} {r.text[:300]}"
    assert r.headers.get("content-type", "").startswith("application/pdf"), (
        f"Non-PDF content-type: {r.headers.get('content-type')}"
    )
    return r.content


def _pdf_text(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    txt = ""
    for p in doc:
        txt += p.get_text()
    return txt, doc


# ============================================================================
# TEST 1 — OS sem procedimento
# ============================================================================
class TestOSSemProcedimento:
    """be9878f1: header ok, no fictitious data, no QR, footer ok, 1 page"""

    def test_pdf_200_and_content_type(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        assert pdf.startswith(b"%PDF"), "Not a valid PDF header"

    def test_header_astec(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "ASTEC DO BRASIL" in txt.upper(), f"Header 'ASTEC DO BRASIL' not found. Head: {txt[:400]!r}"

    def test_header_unidade(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert re.search(r"Unidade:\s*UNIDADE\s+CEDRO", txt, re.IGNORECASE), (
            f"'Unidade: UNIDADE CEDRO' not found. Head: {txt[:600]!r}"
        )

    def test_header_os_number(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert re.search(r"ORDEM\s+DE\s+SERVI", txt, re.IGNORECASE), "OS title not found"
        # Should contain N. <numero>
        assert re.search(r"N\.\s*\S+", txt), f"OS number pattern not found. Sample: {txt[:400]!r}"

    def test_header_titulo_intervencao(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        # We don't know exact title, but must have some titulo text visible (not empty)
        assert len(txt.strip()) > 100, "PDF text too short — layout may be broken"

    def test_no_fictitious_cnpj(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "12.345.678" not in txt, f"Fictitious CNPJ still present: {txt}"

    def test_no_maintrix_int_ltda(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "MAINTRIX INT" not in txt.upper(), "Fictitious 'MAINTRIX INT LTDA' still present"

    def test_no_fictitious_phone(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "5555-1234" not in txt, "Fictitious phone (11) 5555-1234 still present"

    def test_no_fictitious_address(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "Rua Integracao" not in txt and "Rua Integração" not in txt, (
            "Fictitious address 'Rua Integração' still present"
        )

    def test_no_qr_code_image(self, auth_client):
        """QR should be removed from OS PDF. Only logo image expected."""
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        doc = fitz.open(stream=pdf, filetype="pdf")
        total_imgs = 0
        for p in doc:
            imgs = p.get_images(full=True)
            total_imgs += len(imgs)
        # Expect at most 1 image (logo). No QR.
        assert total_imgs <= 1, f"Expected <=1 image (logo only), got {total_imgs}. QR may still be present."

    def test_no_empty_procedimento_section(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        # If no procedimento_id linked, the section "Procedimento Aplicável" must NOT appear
        assert "Procedimento Aplicável" not in txt and "Procedimento Aplicavel" not in txt, (
            "Empty 'Procedimento Aplicável' section rendered when OS has no procedure"
        )

    def test_footer_maintrix_enterprise(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        txt, _ = _pdf_text(pdf)
        assert "MAINTRIX Enterprise" in txt or "Maintrix Enterprise" in txt, (
            f"Footer 'Documento gerado pelo MAINTRIX Enterprise' not found. Text sample: {txt[-500:]!r}"
        )
        assert "Documento gerado" in txt, "Footer text 'Documento gerado' not found"

    def test_fits_one_page(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        doc = fitz.open(stream=pdf, filetype="pdf")
        assert doc.page_count == 1, (
            f"OS sem procedimento deve ter 1 página, tem {doc.page_count}. "
            "Layout não está compacto o suficiente ou há página em branco."
        )


# ============================================================================
# TEST 2 — OS com procedimento
# ============================================================================
class TestOSComProcedimento:
    """ff2bb384: title preserved, procedure section visible, annex, no QR, no fictitious CNPJ"""

    def test_pdf_200(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        assert pdf.startswith(b"%PDF")

    def test_titulo_intervencao_preserved(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        txt, _ = _pdf_text(pdf)
        assert "Troca do rolamento do alimentador" in txt, (
            f"Título da OS não preservado. Deve conter 'Troca do rolamento do alimentador'. "
            f"Encontrado sample: {txt[:600]!r}"
        )

    def test_procedimento_aplicavel_section(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        txt, _ = _pdf_text(pdf)
        assert "PROCEDIMENTO APLIC" in txt.upper(), "Section 'Procedimento Aplicável' not found"
        assert "PROC-0001" in txt, f"Procedure code PROC-0001 not found. Text sample: {txt[:1500]!r}"

    def test_procedure_annex_present(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        doc = fitz.open(stream=pdf, filetype="pdf")
        assert doc.page_count >= 2, (
            f"OS com procedimento deve ter pelo menos 2 páginas (corpo + anexo), tem {doc.page_count}"
        )

    def test_no_qr_on_first_page(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        doc = fitz.open(stream=pdf, filetype="pdf")
        page1_imgs = doc[0].get_images(full=True)
        # Only logo expected on page 1
        assert len(page1_imgs) <= 1, (
            f"Page 1 has {len(page1_imgs)} images; expected <=1 (logo only). QR should not be in OS PDF."
        )

    def test_no_fictitious_cnpj(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_WITH_PROC)
        txt, _ = _pdf_text(pdf)
        assert "12.345.678" not in txt, "Fictitious CNPJ still present"
        assert "MAINTRIX INT" not in txt.upper(), "Fictitious 'MAINTRIX INT LTDA' still present"


# ============================================================================
# TEST 3 — OS com campos vazios
# ============================================================================
class TestOSCamposVazios:
    """c8f9b1ea: empty fields (fabricante, num_serie) not shown as '-'"""

    def test_pdf_200(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_EMPTY_FIELDS)
        assert pdf.startswith(b"%PDF")

    def test_no_dash_only_lines(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_EMPTY_FIELDS)
        txt, _ = _pdf_text(pdf)
        # Should NOT have "Fabricante ... -" or "Nº Série ... -" as visible fields
        # We just check that these labels do not appear followed by a dash
        # The compact layout should skip these fields entirely when null.
        for label in ["Fabricante", "Nº Série"]:
            m = re.search(rf"{label}\s*\n?\s*-\s*(?:\n|$)", txt)
            assert m is None, f"Empty field '{label}' still rendered with dash. Sample: {txt[:800]!r}"

    def test_one_page(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_EMPTY_FIELDS)
        doc = fitz.open(stream=pdf, filetype="pdf")
        # Should fit in 1 page since empty fields are hidden
        assert doc.page_count == 1, (
            f"OS com campos vazios deve ter 1 página (fields hidden), tem {doc.page_count}"
        )


# ============================================================================
# TEST 4 — OS simples em 1 página (já validado em TestOSSemProcedimento.test_fits_one_page)
# Aqui verificamos que assinaturas estão na mesma página.
# ============================================================================
class TestOSUmaPagina:
    def test_signatures_on_same_page(self, auth_client):
        pdf = _fetch_pdf(auth_client, OS_NO_PROC)
        doc = fitz.open(stream=pdf, filetype="pdf")
        assert doc.page_count == 1, f"Expected 1 page, got {doc.page_count}"
        page1_text = doc[0].get_text()
        # Signature block must be on the same page
        assert ("Executor" in page1_text) or ("Assinatura" in page1_text) or ("Supervisor" in page1_text), (
            f"Signatures not visible on page 1. Text: {page1_text[-500:]!r}"
        )


# ============================================================================
# TEST 5 — QR de Ativos still works
# ============================================================================
class TestAtivoQRUnaffected:
    def test_ativo_qrcode_png_200(self, auth_client):
        # Fetch an existing ativo
        r = auth_client.get(f"{BASE_URL}/api/ativos", timeout=30)
        assert r.status_code == 200, f"List ativos failed: {r.status_code}"
        ativos = r.json()
        assert isinstance(ativos, list) and len(ativos) > 0, "No ativos available for QR test"
        # find an ativo that has an id
        ativo_id = None
        for a in ativos:
            if a.get("id"):
                ativo_id = a["id"]
                break
        assert ativo_id, "No ativo with id found"
        r2 = auth_client.get(f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/png", timeout=30)
        assert r2.status_code == 200, f"QR PNG failed: {r2.status_code} {r2.text[:200]}"
        assert r2.headers.get("content-type", "").startswith("image/png"), (
            f"QR content-type not image/png: {r2.headers.get('content-type')}"
        )
        # PNG magic bytes
        assert r2.content[:8] == b"\x89PNG\r\n\x1a\n", "QR content is not valid PNG"
