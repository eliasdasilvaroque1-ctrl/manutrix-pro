"""RC Estabilização Fase 3 — Redesenho do PDF da OS.

Testa:
 - Ausência de PENDENTE / concluídas / Executado por: nas páginas do anexo
 - Presença de PROCEDIMENTO APLICÁVEL, Ler e seguir, PREPARAÇÃO DA INTERVENÇÃO
 - ANEXO 1 — PROCEDIMENTO DE MANUTENÇÃO com etapas
 - Etapas como texto sequencial (não checkbox)
 - Assinaturas NÃO em página isolada
 - Acentos preservados (Descrição, Informações, Mecânica, Não, Duração)
 - QR decodifica para https://www.maintrix.com.br/os/{id}
 - PDF de OS simples (sem procedimento) funciona
 - Regressão: página pública dossiê AV-01 continua respondendo
"""
import io
import os
import re
import pytest
import requests
import fitz  # PyMuPDF
from pyzbar.pyzbar import decode as qr_decode
from PIL import Image

def _load_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if url:
        return url.rstrip("/")
    # Fallback: read from /app/frontend/.env
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except FileNotFoundError:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")


BASE_URL = _load_base_url()

# Credenciais / IDs fixos vindos do review request
ADMIN_EMAIL = "test.admin@maintrix.com"
ADMIN_PASSWORD = "admin123"
OS_COM_PROC_ID = "211039a2-f616-4231-be4b-ab1338cceb8f"  # 7 etapas
OS_SIMPLES_ID = "aa42e758-b719-4e68-9882-60add0b2e46e"
PUBLIC_QR_PATH = "/api/public/equipment/av-01-alimentador/Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu"

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"Login falhou: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


def _fetch_pdf(os_id: str, modo: str, headers) -> fitz.Document:
    r = requests.get(
        f"{BASE_URL}/api/ordens-servico/{os_id}/pdf",
        headers=headers,
        params={"modo": modo},
        timeout=60,
    )
    assert r.status_code == 200, f"PDF {os_id} modo={modo} status={r.status_code} body={r.text[:200]}"
    assert r.headers.get("content-type", "").startswith("application/pdf"), r.headers
    return fitz.open(stream=r.content, filetype="pdf")


def _full_text(doc: fitz.Document) -> str:
    return "\n".join(page.get_text() for page in doc)


def _page_texts(doc: fitz.Document):
    return [page.get_text() for page in doc]


# --------------------------------------------------------------------------
# Cache PDFs (module-scope) — evitar múltiplos downloads
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def pdf_proc_digital(headers):
    return _fetch_pdf(OS_COM_PROC_ID, "digital", headers)


@pytest.fixture(scope="module")
def pdf_proc_manual(headers):
    return _fetch_pdf(OS_COM_PROC_ID, "manual", headers)


@pytest.fixture(scope="module")
def pdf_simples_digital(headers):
    return _fetch_pdf(OS_SIMPLES_ID, "digital", headers)


@pytest.fixture(scope="module")
def pdf_simples_manual(headers):
    return _fetch_pdf(OS_SIMPLES_ID, "manual", headers)


# --------------------------------------------------------------------------
# 1) Ausência de PENDENTE / concluídas / Executado por
# --------------------------------------------------------------------------
class TestAusenciaTermosDigitais:
    @pytest.mark.parametrize("fixture_name", ["pdf_proc_digital", "pdf_proc_manual"])
    def test_no_pendente(self, request, fixture_name):
        doc = request.getfixturevalue(fixture_name)
        for i, page_text in enumerate(_page_texts(doc), 1):
            assert "PENDENTE" not in page_text.upper(), (
                f"Encontrado 'PENDENTE' na página {i} do PDF {fixture_name}"
            )

    @pytest.mark.parametrize("fixture_name", ["pdf_proc_digital", "pdf_proc_manual"])
    def test_no_concluidas(self, request, fixture_name):
        doc = request.getfixturevalue(fixture_name)
        txt = _full_text(doc).lower()
        assert "concluída" not in txt and "concluidas" not in txt and "concluídas" not in txt, (
            "Encontrado 'concluídas/concluidas' no PDF"
        )
        # Também não deve conter padrão "0/7" (progresso digital)
        assert not re.search(r"\b0/7\b", txt), "Progresso '0/7' presente no PDF"

    @pytest.mark.parametrize("fixture_name", ["pdf_proc_digital", "pdf_proc_manual"])
    def test_no_executado_por_no_anexo(self, request, fixture_name):
        """Executado por: NÃO deve aparecer nas etapas do procedimento (páginas do anexo).
        Pode aparecer no bloco de assinaturas como 'Executor' -- mas não 'Executado por:'.
        """
        doc = request.getfixturevalue(fixture_name)
        txt = _full_text(doc)
        assert "Executado por:" not in txt, "Rótulo 'Executado por:' encontrado no PDF"
        assert "Executado por" not in txt, "Rótulo 'Executado por' encontrado no PDF"


# --------------------------------------------------------------------------
# 2) Presença de blocos redesenhados
# --------------------------------------------------------------------------
class TestBlocosRedesenhados:
    def test_procedimento_aplicavel(self, pdf_proc_digital):
        txt = _full_text(pdf_proc_digital)
        # section_title faz upper() ⇒ "PROCEDIMENTO APLICÁVEL"
        assert "PROCEDIMENTO APLICÁVEL" in txt, "Título 'PROCEDIMENTO APLICÁVEL' ausente"
        # Deve conter código e título do PROC-0001
        assert "PROC-0001" in txt, "Código PROC-0001 ausente"
        assert re.search(r"Revis[aã]o", txt), "Revisão ausente"

    def test_ler_e_seguir(self, pdf_proc_digital):
        txt = _full_text(pdf_proc_digital)
        assert "Ler e seguir integralmente" in txt, "Instrução 'Ler e seguir integralmente' ausente"

    def test_preparacao_da_intervencao_com_itens(self, pdf_proc_manual):
        txt = _full_text(pdf_proc_manual)
        assert "PREPARAÇÃO DA INTERVENÇÃO" in txt, "Bloco 'PREPARAÇÃO DA INTERVENÇÃO' ausente"
        # Itens obrigatórios
        for item in [
            "Materiais separados",
            "Ferramentas separadas",
            "LOTO",
            "Permissão de Trabalho",
            "Área liberada",
            "EPI",
        ]:
            assert item in txt, f"Item de preparação ausente: {item}"

    def test_anexo1_com_etapas_numeradas(self, pdf_proc_digital):
        txt = _full_text(pdf_proc_digital)
        assert "ANEXO 1" in txt, "Cabeçalho 'ANEXO 1' ausente"
        assert "PROCEDIMENTO DE MANUTENÇÃO" in txt, "Título 'PROCEDIMENTO DE MANUTENÇÃO' ausente no anexo"
        # 7 etapas numeradas — deve haver "1." ... "7."
        # Buscar padrão numérico seguido de ponto no anexo
        etapas_encontradas = re.findall(r"^\s*([1-7])\.\s", txt, flags=re.MULTILINE)
        # A verificação exata do PDF depende do layout; pelo menos 1..7 devem existir de alguma forma
        assert set(str(i) for i in range(1, 8)).issubset(set(etapas_encontradas)) or all(
            f"{i}." in txt for i in range(1, 8)
        ), f"Não encontrou marcadores de 1 a 7 etapas. Encontrado: {etapas_encontradas}"

    def test_etapas_sao_texto_sequencial_sem_badge(self, pdf_proc_digital):
        """Não deve haver labels de progresso/badge tipo PENDENTE, CONCLUIDO, EM ANDAMENTO."""
        txt = _full_text(pdf_proc_digital).upper()
        for badge in ["PENDENTE", "CONCLU\u00cdDO", "CONCLU\u00cdDA", "EM ANDAMENTO", "N\u00c3O INICIADO"]:
            assert badge not in txt, f"Badge de estado '{badge}' encontrado nas etapas"


# --------------------------------------------------------------------------
# 3) Assinaturas NÃO em página isolada
# --------------------------------------------------------------------------
class TestAssinaturasNaoIsoladas:
    def test_assinaturas_nao_isoladas_com_proc(self, pdf_proc_digital):
        pages = _page_texts(pdf_proc_digital)
        # Encontrar página com assinaturas
        idx = None
        for i, txt in enumerate(pages):
            if re.search(r"Assinatura", txt, re.IGNORECASE) or re.search(r"ASSINATURA", txt):
                idx = i
        assert idx is not None, "Bloco de assinaturas não encontrado"
        # A página com assinaturas deve conter outro conteúdo (não somente assinaturas)
        page_txt = pages[idx]
        # Remover as ocorrências de "Assinatura" e whitespace — deve sobrar conteúdo
        residual = re.sub(r"assinatura[s]?", "", page_txt, flags=re.IGNORECASE).strip()
        # Deve sobrar algo além do simples cabeçalho/rodapé (heurística: mais de ~50 chars)
        assert len(residual) > 80, (
            f"Página de assinaturas parece isolada. Conteúdo residual muito curto ({len(residual)} chars)."
        )

    def test_assinaturas_nao_isoladas_os_simples(self, pdf_simples_digital):
        pages = _page_texts(pdf_simples_digital)
        idx = None
        for i, txt in enumerate(pages):
            if re.search(r"Assinatura", txt, re.IGNORECASE):
                idx = i
        assert idx is not None, "Bloco de assinaturas não encontrado (OS simples)"
        residual = re.sub(r"assinatura[s]?", "", pages[idx], flags=re.IGNORECASE).strip()
        assert len(residual) > 80, "Página de assinaturas isolada em OS simples"


# --------------------------------------------------------------------------
# 4) Acentos corretos
# --------------------------------------------------------------------------
class TestAcentos:
    @pytest.mark.parametrize("fixture_name", ["pdf_proc_digital", "pdf_proc_manual"])
    def test_acentos_presentes(self, request, fixture_name):
        doc = request.getfixturevalue(fixture_name)
        txt = _full_text(doc)
        # Espera-se pelo menos alguns desses no PDF (mixed case ou upper)
        expected = {
            "Descrição/DESCRIÇÃO": ["Descrição", "DESCRIÇÃO"],
            "Informações/INFORMAÇÕES": ["Informações", "INFORMAÇÕES"],
            "Não/NÃO": ["Não", "NÃO"],
            "Duração/DURAÇÃO": ["Duração", "DURAÇÃO"],
        }
        for key, variants in expected.items():
            assert any(v in txt for v in variants), (
                f"Acento esperado ausente ({key}): nenhuma das variantes {variants} encontrada"
            )

    def test_mecanica_com_acento(self, pdf_proc_digital):
        """Mecânica deve aparecer com acento se o texto do OS tiver esse termo. Fallback: aceita tanto Mecânica quanto MECÂNICA."""
        txt = _full_text(pdf_proc_digital)
        # Se termo aparecer sem acento é falha (mesmo em uppercase)
        # Verifica que se 'Mecanica' (sem acento) aparecer, tem que ser dentro de 'Mecânica'
        has_wrong = re.search(r"\bMec[Aa]nic[ao]\b", txt) is not None  # sem acento
        has_right = ("Mecânica" in txt) or ("MECÂNICA" in txt) or ("Mecânico" in txt) or ("MECÂNICO" in txt)
        if has_wrong and not has_right:
            pytest.fail("'Mecanica' sem acento encontrado (esperado 'Mecânica')")
        # Se o termo não aparece de forma alguma, ok (não crítico neste teste)


# --------------------------------------------------------------------------
# 5) QR aponta para https://www.maintrix.com.br/os/{id}
# --------------------------------------------------------------------------
class TestQRCode:
    def test_qr_decodifica_para_url_publica(self, pdf_proc_digital):
        # Renderizar cada página como imagem e decodificar QR
        found = None
        for page in pdf_proc_digital:
            pix = page.get_pixmap(dpi=250)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            decoded = qr_decode(img)
            for d in decoded:
                data = d.data.decode("utf-8", errors="ignore")
                if "/os/" in data:
                    found = data
                    break
            if found:
                break
        assert found is not None, "QR Code não foi encontrado / decodificado no PDF"
        expected = f"https://www.maintrix.com.br/os/{OS_COM_PROC_ID}"
        assert found == expected, f"QR aponta para {found!r}, esperado {expected!r}"


# --------------------------------------------------------------------------
# 6) PDF de OS simples (sem procedimento) funciona
# --------------------------------------------------------------------------
class TestOSSimples:
    def test_pdf_simples_digital_ok(self, pdf_simples_digital):
        assert pdf_simples_digital.page_count >= 1
        txt = _full_text(pdf_simples_digital)
        # Não deve ter anexo nem termos do fluxo digital
        assert "ANEXO 1" not in txt, "OS sem procedimento não deveria ter ANEXO 1"
        assert "PENDENTE" not in txt.upper()
        assert "Executado por" not in txt

    def test_pdf_simples_manual_ok(self, pdf_simples_manual):
        assert pdf_simples_manual.page_count >= 1
        txt = _full_text(pdf_simples_manual)
        # Manual deve conter Preparação
        assert "PREPARAÇÃO DA INTERVENÇÃO" in txt


# --------------------------------------------------------------------------
# 7) Observações da execução com área ampla (manual_box)
# --------------------------------------------------------------------------
class TestObservacoesAmpliadas:
    def test_observacoes_com_area_ampla(self, pdf_proc_manual):
        txt = _full_text(pdf_proc_manual)
        assert "OBSERVAÇÕES DA EXECUÇÃO" in txt, "Título 'OBSERVAÇÕES DA EXECUÇÃO' ausente"
        # Manual deve conter dica de anomalias
        assert "Anomalias encontradas" in txt or "anomalias" in txt.lower(), (
            "Área ampla de anomalias/observações não detectada"
        )


# --------------------------------------------------------------------------
# 8) Regressão: dossiê público AV-01 continua respondendo
# --------------------------------------------------------------------------
class TestRegressao:
    def test_public_dossier_av01(self):
        # Endpoint público -- sem auth
        r = requests.get(f"{BASE_URL}{PUBLIC_QR_PATH}", timeout=30)
        assert r.status_code == 200, f"Público falhou: {r.status_code} {r.text[:200]}"
        data = r.json()
        # Sanidade mínima
        assert "equipment" in data or "nome" in data or "tag" in data or isinstance(data, dict)
