"""
Iteration 125 — HOTFIX P0 verification: procedure annex must include ALL fields.

Verifies that the PDF of an OS with a linked procedure renders a complete annex
containing every populated field of the procedure (título, código, revisão, descrição,
disciplina, EPIs, ferramentas, riscos, bloqueios/LOTO, etapas numeradas, observações,
critérios de conclusão). Also verifies that:
  - OS without procedure => exactly 1 page, no empty annex, no blank page.
  - OS with procedure    => 2+ pages, page 2 is the annex.
  - No fictitious data (CNPJ 12.345.678, MAINTRIX INT LTDA, (11) 5555-1234, Rua Integracao).
  - OS title preserved (not replaced by procedure name).
  - Procedure not duplicated as full section on page 1.
  - Ativo QR endpoint still returns 200.

Data model (as present in DB for PROC-0001):
  codigo=PROC-0001, nome='Troca de Rolamento em Motor Elétrico WEG', revisao='03',
  descricao='Procedimento padrão para substituição de rolamentos em motores elétricos WEG',
  tempo_estimado_minutos=120,
  observacoes='Utilizar EPI completo. Bloquear alimentação elétrica antes de iniciar.',
  etapas=7 titles: Desenergizar/Remover acoplamento/Remover tampa/Extrair rolamento/
                   Inspecionar eixo/Instalar rolamento novo/Remontar e testar.
  disciplina/epis/ferramentas/riscos/bloqueios/criterios: None (not rendered — correct).
"""
import os
import re
import pytest
import requests
import fitz  # pymupdf

# Load frontend/.env for backend URL
if not os.environ.get("REACT_APP_BACKEND_URL"):
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    os.environ["REACT_APP_BACKEND_URL"] = line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

OS_NO_PROC = "be9878f1-71ab-476e-b491-b1af7c402685"
OS_WITH_PROC = "ff2bb384-6d68-4f29-9584-5e5aeb9e5035"
OS_EMPTY_FIELDS = "c8f9b1ea-ab6f-41e5-b690-9a7c0c840e62"
PROC_ID = "0ef8981b-0afc-4ff2-b8ad-044a43f0f908"


# ---------------- Fixtures ----------------
@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(api_client):
    r = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test.admin@maintrix.com", "password": "admin123"},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"No token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture(scope="module")
def pdf_no_proc(auth_client):
    return _fetch_pdf(auth_client, OS_NO_PROC)


@pytest.fixture(scope="module")
def pdf_with_proc(auth_client):
    return _fetch_pdf(auth_client, OS_WITH_PROC)


@pytest.fixture(scope="module")
def pdf_empty_fields(auth_client):
    return _fetch_pdf(auth_client, OS_EMPTY_FIELDS)


# ---------------- Helpers ----------------
def _fetch_pdf(client, os_id):
    r = client.get(
        f"{BASE_URL}/api/ordens-servico/{os_id}/pdf?modo=digital", timeout=90
    )
    assert r.status_code == 200, f"PDF fetch failed for {os_id}: {r.status_code} {r.text[:300]}"
    assert r.headers.get("content-type", "").startswith("application/pdf"), (
        f"Non-PDF content-type: {r.headers.get('content-type')}"
    )
    return r.content


def _pages(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = [p.get_text() for p in doc]
    return doc, pages_text


def _norm(s):
    """Normalize text: collapse whitespace, lowercase for substring lookups."""
    return re.sub(r"\s+", " ", s or "").strip()


# ============================================================================
# 1) OS SEM procedimento — 1 página, sem seção vazia, sem anexo
# ============================================================================
class TestOSSemProcedimento1Pagina:
    def test_valid_pdf(self, pdf_no_proc):
        assert pdf_no_proc.startswith(b"%PDF")

    def test_exactly_one_page(self, pdf_no_proc):
        doc, _ = _pages(pdf_no_proc)
        assert doc.page_count == 1, (
            f"Expected EXACTLY 1 page for OS without procedure, got {doc.page_count}"
        )

    def test_no_empty_procedimento_section(self, pdf_no_proc):
        _, pages = _pages(pdf_no_proc)
        joined = "\n".join(pages)
        assert "Procedimento Aplic" not in joined, (
            "Empty 'Procedimento Aplicável' section should NOT render when OS has no procedure"
        )

    def test_no_annex_header(self, pdf_no_proc):
        _, pages = _pages(pdf_no_proc)
        joined = "\n".join(pages).upper()
        assert "ANEXO" not in joined or "PROCEDIMENTO DE MANUTEN" not in joined, (
            "Annex header should NOT appear when OS has no procedure"
        )

    def test_no_fictitious_data(self, pdf_no_proc):
        _, pages = _pages(pdf_no_proc)
        joined = "\n".join(pages)
        assert "12.345.678" not in joined
        assert "MAINTRIX INT" not in joined.upper()
        assert "5555-1234" not in joined
        assert "Rua Integracao" not in joined and "Rua Integração" not in joined


# ============================================================================
# 2) OS COM procedimento — 2+ páginas, anexo COMPLETO com todos os campos
# ============================================================================
class TestOSComProcedimentoAnexoCompleto:
    def test_valid_pdf(self, pdf_with_proc):
        assert pdf_with_proc.startswith(b"%PDF")

    def test_at_least_2_pages(self, pdf_with_proc):
        doc, _ = _pages(pdf_with_proc)
        assert doc.page_count >= 2, (
            f"OS with procedure must have 2+ pages (body + annex). Got {doc.page_count}"
        )

    def test_page1_summary_reference(self, pdf_with_proc):
        """Page 1 must have a short 'Procedimento Aplicável' reference (not full annex)."""
        _, pages = _pages(pdf_with_proc)
        page1 = pages[0]
        # section_title() renders labels in UPPERCASE — match case-insensitively
        assert re.search(r"PROCEDIMENTO\s+APLIC", page1, re.IGNORECASE), (
            "Page 1 must show a short procedure reference ('Procedimento Aplicável')"
        )
        assert "PROC-0001" in page1, "Page 1 reference must include the procedure code"
        # Body page must NOT include etapas numbered inline — those must live in the annex
        # (we assert steps live on page >=2 below)

    def test_annex_header_on_page_2plus(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex_text = "\n".join(pages[1:]).upper()
        assert "ANEXO" in annex_text and "PROCEDIMENTO DE MANUTEN" in annex_text, (
            f"Annex header 'ANEXO N — PROCEDIMENTO DE MANUTENÇÃO' not found in page 2+. "
            f"Sample: {annex_text[:400]!r}"
        )

    # ---- All annex fields ----
    def test_annex_contains_titulo(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        assert "Troca de Rolamento em Motor Elétrico WEG" in annex, (
            "Título do procedimento não aparece no anexo"
        )

    def test_annex_contains_codigo(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = "\n".join(pages[1:])
        assert "PROC-0001" in annex, "Código PROC-0001 não aparece no anexo"

    def test_annex_contains_revisao(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        # Field label 'Revisão' followed by the value '03' near it
        assert "Revisão" in annex or "Revisao" in annex, "Label 'Revisão' not in annex"
        assert re.search(r"Revis[aã]o[^0-9]{0,10}03", annex), (
            f"Revisão value '03' not found near label. Sample: {annex[:600]!r}"
        )

    def test_annex_contains_descricao(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        assert "Procedimento padrão para substituição de rolamentos" in annex, (
            f"Descrição do procedimento não aparece no anexo. Sample: {annex[:800]!r}"
        )

    def test_annex_contains_tempo_estimado(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        assert re.search(r"120\s*min", annex), (
            f"Tempo estimado '120 min' não aparece no anexo. Sample: {annex[:800]!r}"
        )

    def test_annex_contains_all_7_steps(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        expected_titles = [
            "Desenergizar e bloquear motor",
            "Remover acoplamento",
            "Remover tampa traseira",
            "Extrair rolamento danificado",
            "Inspecionar eixo",
            "Instalar rolamento novo",
            "Remontar e testar",
        ]
        missing = [t for t in expected_titles if t not in annex]
        assert not missing, f"Etapas ausentes no anexo: {missing}. Sample: {annex[:1500]!r}"

    def test_annex_steps_are_numbered(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = "\n".join(pages[1:])
        # Steps rendered with 'N.' prefix; ensure 1., 2., ..., 7. all appear
        for n in range(1, 8):
            assert re.search(rf"(^|\W){n}\.\s", annex), (
                f"Numeração '{n}.' não encontrada no anexo"
            )

    def test_annex_contains_observacoes(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        annex = _norm("\n".join(pages[1:]))
        annex_upper = annex.upper()
        # section_title() renders in UPPERCASE
        assert "OBSERVAÇÕES DO PROCEDIMENTO" in annex_upper or "OBSERVACOES DO PROCEDIMENTO" in annex_upper, (
            "Section 'Observações do Procedimento' missing in annex"
        )
        assert "Utilizar EPI completo" in annex, "Observações content missing (EPI completo)"
        assert "Bloquear alimentação elétrica" in annex or "Bloquear alimentacao" in annex, (
            "Observações content missing (Bloquear alimentação elétrica)"
        )

    # ---- Fields intentionally NOT populated in DB — must NOT appear ----
    def test_annex_does_not_include_unpopulated_sections(self, pdf_with_proc):
        """PROC-0001 has no EPIs/ferramentas/riscos/bloqueios/critérios in DB.
        These SECTIONS should not appear (procedure_annex conditionally renders)."""
        _, pages = _pages(pdf_with_proc)
        annex_upper = _norm("\n".join(pages[1:])).upper()
        # These section titles must not be rendered as their data is null in DB
        forbidden_sections = [
            "EQUIPAMENTOS DE PROTEÇÃO INDIVIDUAL",
            "EQUIPAMENTOS DE PROTECAO INDIVIDUAL",
            "RISCOS E ALERTAS DE SEGURANÇA",
            "RISCOS E ALERTAS DE SEGURANCA",
            "BLOQUEIOS / LOTO",
            "CRITÉRIOS DE CONCLUSÃO",
            "CRITERIOS DE CONCLUSAO",
        ]
        found = [s for s in forbidden_sections if s in annex_upper]
        assert not found, (
            f"Empty sections should NOT render (data is null in DB): {found}"
        )
        # 'Ferramentas' section: DB has None. Ensure the section title FERRAMENTAS
        # (as an own section, not the checklist item on page 1) is not on annex pages.
        # We check the annex text specifically — page 1 has "Ferramentas separadas" as a prep item,
        # which is unrelated.
        assert "FERRAMENTAS" not in annex_upper, (
            "Empty 'Ferramentas' section should NOT render in annex (data is null in DB)"
        )

    def test_os_title_preserved(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        page1 = pages[0]
        assert "Troca do rolamento do alimentador" in page1, (
            f"Título da OS 'Troca do rolamento do alimentador' foi substituído. "
            f"Page1 sample: {page1[:600]!r}"
        )

    def test_procedure_annex_not_duplicated(self, pdf_with_proc):
        """Ensure PROC-0001 code appears once as a reference on page 1 AND once in annex identification.
        The procedure content (steps) must NOT be duplicated on page 1."""
        doc, pages = _pages(pdf_with_proc)
        page1 = pages[0]
        # No numbered steps content on page 1 (steps should live only in annex)
        # Check any step title is absent from page 1
        assert "Desenergizar e bloquear motor" not in page1, (
            "Step content leaking into page 1 (should only be in annex)"
        )
        # Annex block header should occur exactly once across the whole PDF
        all_text = "\n".join(pages).upper()
        occurrences = len(re.findall(r"ANEXO\s+1\s+.*?PROCEDIMENTO DE MANUTEN", all_text))
        assert occurrences == 1, (
            f"Annex header expected exactly 1x, found {occurrences}. Procedure may be duplicated."
        )

    def test_no_fictitious_data(self, pdf_with_proc):
        _, pages = _pages(pdf_with_proc)
        joined = "\n".join(pages)
        assert "12.345.678" not in joined
        assert "MAINTRIX INT" not in joined.upper()
        assert "5555-1234" not in joined
        assert "Rua Integracao" not in joined and "Rua Integração" not in joined


# ============================================================================
# 3) OS com campos vazios (fabricante/série) — sem '-'
# ============================================================================
class TestOSCamposVazios:
    def test_valid_pdf_one_page(self, pdf_empty_fields):
        assert pdf_empty_fields.startswith(b"%PDF")
        doc, _ = _pages(pdf_empty_fields)
        assert doc.page_count == 1, (
            f"OS com campos vazios deve ter 1 página, tem {doc.page_count}"
        )

    def test_no_dash_only_lines(self, pdf_empty_fields):
        _, pages = _pages(pdf_empty_fields)
        txt = "\n".join(pages)
        for label in ["Fabricante", "Nº Série", "N° Série", "No Serie"]:
            m = re.search(rf"{label}\s*[:\n]?\s*-\s*(?:\n|$)", txt)
            assert m is None, f"Empty field '{label}' still rendered with dash"


# ============================================================================
# 4) QR de Ativos still works
# ============================================================================
class TestAtivoQR:
    def test_ativo_qr_png_200(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/ativos", timeout=30)
        assert r.status_code == 200
        ativos = r.json()
        assert isinstance(ativos, list) and len(ativos) > 0, "No ativos to test QR"
        ativo_id = next((a["id"] for a in ativos if a.get("id")), None)
        assert ativo_id, "No ativo with id"
        r2 = auth_client.get(f"{BASE_URL}/api/ativos/{ativo_id}/qrcode/png", timeout=30)
        assert r2.status_code == 200, f"QR PNG failed: {r2.status_code}"
        assert r2.headers.get("content-type", "").startswith("image/png"), (
            f"Wrong content-type: {r2.headers.get('content-type')}"
        )
        assert r2.content[:8] == b"\x89PNG\r\n\x1a\n", "Invalid PNG magic bytes"
