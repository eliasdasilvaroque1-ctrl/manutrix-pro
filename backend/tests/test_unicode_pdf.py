"""MAINTRIX Unicode PDF Validation Tests — RC4.1 P0
Validates that pdf_engine.py correctly renders Unicode characters across
all PDF types: OS digital/manual, Inspection digital/manual.
Uses pdfplumber for text extraction to confirm characters are preserved.

Run: cd /app/backend && python -m pytest tests/test_unicode_pdf.py -v
"""
import pytest
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pdf_engine import MaintrixPDF, _safe, _safe_long, register_unicode_fonts

# ---- Character Sets ----
PORTUGUESE = "ação inspeção manutenção não conformidade São João"
SPANISH = "señal inspección operación"
FRENCH = "sécurité équipement contrôle"
GERMAN = "Überprüfung Größe Straße"
TECH_SYMBOLS = "µm °C Ω Ø ± ≥ ≤ Δ α β ² ³ →"
ALL_CHARS = f"{PORTUGUESE} {SPANISH} {FRENCH} {GERMAN} {TECH_SYMBOLS}"


class TestSafeFunctions:
    """Ensure _safe/_safe_long preserve ALL Unicode characters."""

    def test_safe_portuguese(self):
        assert _safe(PORTUGUESE, 100) == PORTUGUESE

    def test_safe_spanish(self):
        assert _safe(SPANISH, 100) == SPANISH

    def test_safe_french(self):
        assert _safe(FRENCH, 100) == FRENCH

    def test_safe_german(self):
        assert _safe(GERMAN, 100) == GERMAN

    def test_safe_tech_symbols(self):
        assert _safe(TECH_SYMBOLS, 100) == TECH_SYMBOLS

    def test_safe_no_question_marks(self):
        result = _safe(ALL_CHARS, 200)
        assert '?' not in result, f"Found '?' in result: {result}"

    def test_safe_long_preserves_all(self):
        result = _safe_long(ALL_CHARS, 500)
        assert '?' not in result
        for char in ['µ', '°', 'Ω', 'Ø', '±', '≥', '≤', 'Δ', 'α', 'β', '²', '³', '→']:
            assert char in result, f"Missing symbol: {char}"

    def test_safe_empty(self):
        assert _safe(None) == '-'
        assert _safe('') == '-'
        assert _safe_long(None) == ''
        assert _safe_long('') == ''

    def test_safe_truncation(self):
        assert len(_safe("x" * 100, 60)) == 60


class TestFontRegistration:
    """Ensure DejaVu fonts are properly bundled and registered."""

    def test_font_files_exist(self):
        font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
        for fname in ['DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf', 'DejaVuSans-BoldOblique.ttf']:
            path = os.path.join(font_dir, fname)
            assert os.path.exists(path), f"Font not found: {path}"
            assert os.path.getsize(path) > 100_000, f"Font file too small: {fname}"

    def test_font_registration_on_maintrix_pdf(self):
        pdf = MaintrixPDF(empresa='Test')
        # DejaVu should be registered - set_font should not raise
        pdf.add_page()
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(100, 10, 'µm °C Ω')
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(100, 10, 'Bold µm °C Ω')
        pdf.set_font('DejaVu', 'I', 10)
        pdf.cell(100, 10, 'Italic µm °C Ω')

    def test_font_registration_on_raw_fpdf(self):
        from fpdf import FPDF
        pdf = FPDF()
        register_unicode_fonts(pdf)
        pdf.add_page()
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(100, 10, 'µm °C Ω')


class TestUnicodePDFGeneration:
    """Generate PDFs with Unicode content and validate no errors."""

    def _make_pdf_with_unicode(self, modo_manual=False):
        pdf = MaintrixPDF(
            empresa='ASTEC Engenharia',
            doc_title=f'OS Teste Unicode µm °C',
            doc_code='OS-UC-001',
            cor_primaria='#6366f1',
            modo_manual=modo_manual,
        )
        pdf.alias_nb_pages()
        pdf.add_page()
        return pdf

    def test_header_unicode(self):
        pdf = self._make_pdf_with_unicode()
        buf = pdf.output_bytes()
        assert buf.read(4) == b'%PDF'

    def test_footer_unicode(self):
        pdf = self._make_pdf_with_unicode()
        # Footer is rendered automatically; just verify PDF is valid
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_section_title_unicode(self):
        pdf = self._make_pdf_with_unicode()
        pdf.section_title('Inspeção de Segurança — µm °C Ω Ø ±')
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_field_pair_unicode(self):
        pdf = self._make_pdf_with_unicode()
        pdf.field_pair('Medição', '25.3 µm ± 0.1', 10, 30)
        pdf.field_pair('Temperatura', '150 °C', 105, 30)
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_text_block_unicode(self):
        pdf = self._make_pdf_with_unicode()
        pdf.text_block(f'{PORTUGUESE}\n{SPANISH}\n{FRENCH}\n{GERMAN}\n{TECH_SYMBOLS}')
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_procedure_section_unicode(self):
        proc = {
            'objetivo': 'Verificação de tolerância ± 0.5 µm em Ø 50mm',
            'pre_requisitos': 'Medidor calibrado (°C compensado)',
            'etapas': [
                {'numero': 1, 'descricao': 'Medir resistência Ω do circuito α-β'},
                {'numero': 2, 'descricao': 'Verificar temperatura ≥ 20 °C e ≤ 30 °C'},
                {'numero': 3, 'descricao': 'Registrar variação Δ = ² + ³'},
            ],
            'ferramentas': ['Multímetro Ω', 'Termômetro °C'],
            'materiais': ['Peça Ø 50mm', 'Resistência α'],
            'observacoes': 'Não conformidade → ação corretiva imediata',
        }
        pdf = self._make_pdf_with_unicode()
        pdf.procedure_section(proc, manual=False)
        data = pdf.output_bytes().read()
        assert len(data) > 1000

    def test_procedure_manual_unicode(self):
        proc = {
            'objetivo': 'Inspeção señal sécurité',
            'etapas': [{'numero': 1, 'descricao': 'Überprüfung Größe Straße'}],
        }
        pdf = self._make_pdf_with_unicode(modo_manual=True)
        pdf.procedure_section(proc, manual=True)
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_safety_section_unicode(self):
        seg = {
            'riscos': [
                {'descricao': 'Risco elétrico: corrente ≥ 30 mA → parada cardíaca'},
                {'descricao': 'Temperatura ≥ 200 °C na superfície'},
            ],
            'medidas_controle': ['Desligar Ω antes de medir', 'Usar luva térmica (Δ proteção)'],
            'epis': ['Luva isolante (Ω)', 'Óculos α-proteção'],
            'epcs': ['Barreira Ø 1m'],
            'loto': {'necessario': True},
            'apr': {'necessaria': True, 'numero': 'APR-µ001'},
            'bloqueios': [{'tipo': 'Elétrico', 'descricao': 'Disjuntor ≤ 500V'}],
            'observacoes': 'Não realizar trabalho se T° ≥ 40 °C',
        }
        pdf = self._make_pdf_with_unicode()
        pdf.safety_section(seg, manual=False)
        data = pdf.output_bytes().read()
        assert len(data) > 1000

    def test_safety_manual_unicode(self):
        seg = {
            'riscos': [{'descricao': 'Risco térmico ≥ 100 °C'}],
            'epis': ['Luva Ø especial'],
        }
        pdf = self._make_pdf_with_unicode(modo_manual=True)
        pdf.safety_section(seg, manual=True)
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_photo_legend_unicode(self):
        attachments = [
            {'legenda': 'Medição µm no eixo Ø principal', '_local_path': None},
            {'legenda': 'Temperatura °C ≥ limite → não conformidade', '_local_path': None},
            {'categoria': 'Überprüfung foto α', '_local_path': None},
        ]
        pdf = self._make_pdf_with_unicode()
        pdf.photo_grid(attachments, {'grid_colunas': 2, 'max_por_pagina': 4})
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_signature_unicode(self):
        pdf = self._make_pdf_with_unicode()
        pdf.signature_block([('Executor', 'José María García'), ('Supervisor', 'François Müller')])
        data = pdf.output_bytes().read()
        assert len(data) > 500

    def test_manual_box_unicode(self):
        pdf = self._make_pdf_with_unicode(modo_manual=True)
        pdf.manual_box('Registrar medições µm, °C, Ω:', 20)
        data = pdf.output_bytes().read()
        assert len(data) > 500


class TestUnicodePDFContentExtraction:
    """Extract text from generated PDFs to confirm characters survive encoding."""

    @pytest.fixture
    def unicode_pdf_bytes(self):
        pdf = MaintrixPDF(empresa='ASTEC Engenharia ²³', doc_title='OS Unicode µm °C Ω', doc_code='OS-UC-001')
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.section_title('Português: ação inspeção manutenção não conformidade São João')
        pdf.text_block(PORTUGUESE)
        pdf.section_title('Español: señal inspección operación')
        pdf.text_block(SPANISH)
        pdf.section_title('Français: sécurité équipement contrôle')
        pdf.text_block(FRENCH)
        pdf.section_title('Deutsch: Überprüfung Größe Straße')
        pdf.text_block(GERMAN)
        pdf.section_title('Símbolos Técnicos')
        pdf.text_block(f'Temperatura: 25 °C, Medição: 10 µm, Resistência: 5 Ω')
        pdf.text_block(f'Tolerância: ± 0.1, Mínimo: ≥ 10, Máximo: ≤ 100')
        pdf.text_block(f'Variação: Δ = 5, Coef: α = 0.3, β = 0.7')
        pdf.text_block(f'Diâmetro: Ø 50mm, Potência: 10², Volume: 5³')
        pdf.text_block(f'Fluxo → saída')
        return pdf.output_bytes().read()

    def test_pdf_valid_header(self, unicode_pdf_bytes):
        assert unicode_pdf_bytes[:4] == b'%PDF'

    def test_pdf_not_corrupted(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            assert len(p.pages) >= 1

    def test_extract_portuguese(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for word in ['ação', 'inspeção', 'manutenção', 'não', 'conformidade', 'São', 'João']:
            assert word in text, f"Missing Portuguese: '{word}'"

    def test_extract_spanish(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for word in ['señal', 'inspección', 'operación']:
            assert word in text, f"Missing Spanish: '{word}'"

    def test_extract_french(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for word in ['sécurité', 'équipement', 'contrôle']:
            assert word in text, f"Missing French: '{word}'"

    def test_extract_german(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for word in ['Überprüfung', 'Größe', 'Straße']:
            assert word in text, f"Missing German: '{word}'"

    def test_extract_tech_symbols(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for sym in ['µm', '°C', 'Ω', 'Ø', '±', '≥', '≤', 'Δ', 'α', 'β', '²', '³', '→']:
            assert sym in text, f"Missing tech symbol: '{sym}'"

    def test_no_question_marks_in_extracted_text(self, unicode_pdf_bytes):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(unicode_pdf_bytes)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        # Only allow ? if it appears in actual content (which we didn't put)
        if '?' in text:
            # Find context of the ?
            idx = text.index('?')
            ctx = text[max(0, idx-20):idx+20]
            pytest.fail(f"Found '?' in extracted PDF text near: ...{ctx}...")

    def test_pdf_size_reasonable(self, unicode_pdf_bytes):
        size_kb = len(unicode_pdf_bytes) / 1024
        assert size_kb < 500, f"PDF too large: {size_kb:.1f}KB (expected < 500KB)"
        assert size_kb > 5, f"PDF too small: {size_kb:.1f}KB (expected > 5KB)"


class TestFullOSPDFUnicode:
    """Simulate a complete OS PDF with all Unicode sections."""

    def _generate_full_os_pdf(self, manual=False):
        pdf = MaintrixPDF(
            empresa='ASTEC Engenharia & Manutenção',
            doc_title='Ordem de Serviço OS-2026-001',
            doc_code='OS-2026-001',
            cor_primaria='#6366f1',
            modo_manual=manual,
        )
        pdf.alias_nb_pages()
        pdf.add_page()

        # Equipment
        pdf.section_title('Equipamento', 28)
        cy = pdf.get_y()
        pdf.field_pair('TAG', 'BBA-001-Ø50', 10, cy)
        pdf.field_pair('Equipamento', 'Bomba Centrífuga Überprüfung', 105, cy)
        cy += 11
        pdf.field_pair('Tipo', 'Bomba Centrífuga', 10, cy)
        pdf.field_pair('Local', 'Sala de Manutenção α', 105, cy)
        pdf.set_y(cy + 13); pdf.line_sep()

        # OS Info
        pdf.section_title('Informações da OS')
        cy = pdf.get_y()
        pdf.field_pair('Tipo', 'Corretiva', 10, cy)
        pdf.field_pair('Prioridade', 'CRÍTICA', 105, cy)
        cy += 11
        pdf.field_pair('Disciplina', 'Mecânica', 10, cy)
        pdf.field_pair('Status', 'Em Execução', 105, cy)
        pdf.set_y(cy + 13); pdf.line_sep()

        # Description
        pdf.section_title('Descrição')
        pdf.text_block('Manutenção corretiva: substituição do rolamento com tolerância ± 0.01 µm. '
                       'Temperatura máxima: 85 °C. Resistência elétrica: ≥ 100 Ω. '
                       'Diâmetro do eixo: Ø 75mm. Variação Δ aceitável: ≤ 2%.')
        pdf.line_sep()

        # Procedure
        proc = {
            'objetivo': 'Substituição do rolamento — tolerância ± 0.01 µm',
            'pre_requisitos': 'Área limpa, T° ≤ 30 °C',
            'etapas': [
                {'numero': 1, 'descricao': 'Desmontar proteção — verificar Ω isolamento'},
                {'numero': 2, 'descricao': 'Aquecer rolamento a 80 °C (Δ ≤ 5 °C/min)'},
                {'numero': 3, 'descricao': 'Instalar rolamento Ø 75mm — tolerância ± µm'},
                {'numero': 4, 'descricao': 'Medir folga axial: ≥ 0.05mm e ≤ 0.15mm'},
                {'numero': 5, 'descricao': 'Testar rotação → vibração ≤ 2.5 mm/s² (α = 0.95)'},
            ],
            'ferramentas': ['Aquecedor indutivo', 'Multímetro Ω', 'Micrômetro µm'],
            'materiais': ['Rolamento SKF Ø 75mm', 'Graxa β especial'],
            'observacoes': 'Se vibração > limite → repetir alinhamento',
        }
        pdf.procedure_section(proc, manual=manual)

        # Safety
        seg = {
            'riscos': [
                {'descricao': 'Risco térmico: peça a 80 °C → queimadura'},
                {'descricao': 'Risco elétrico: tensão ≥ 380V — resistência Ω baixa'},
            ],
            'medidas_controle': ['Usar luva térmica (T° ≤ 200 °C)', 'Medir Ω antes de tocar'],
            'epis': ['Luva isolante Ω', 'Óculos proteção α', 'Máscara FFP²'],
            'epcs': ['Barreira Ø 2m', 'Extintor classe C³'],
            'loto': {'necessario': True},
            'apr': {'necessaria': True, 'numero': 'APR-2026-µ001'},
            'bloqueios': [{'tipo': 'Elétrico', 'descricao': 'Disjuntor ≤ 500V — posição Ø'}],
            'observacoes': 'Não realizar se T° ambiente ≥ 40 °C',
        }
        pdf.safety_section(seg, manual=manual)

        # Photos
        attachments = [
            {'legenda': 'Vista geral — medição Ø 75mm', '_local_path': None},
            {'legenda': 'Rolamento: T° = 25 °C (± 2 °C)', '_local_path': None},
        ]
        pdf.photo_grid(attachments, {'grid_colunas': 2, 'max_por_pagina': 4})

        # Signatures
        pdf.signature_block([
            ('Executor', 'José María García Überprüfung'),
            ('Supervisor', 'François Müller'),
        ])

        return pdf.output_bytes().read()

    def test_os_digital_generates(self):
        data = self._generate_full_os_pdf(manual=False)
        assert data[:4] == b'%PDF'
        assert len(data) > 5000

    def test_os_manual_generates(self):
        data = self._generate_full_os_pdf(manual=True)
        assert data[:4] == b'%PDF'
        assert len(data) > 5000

    def test_os_digital_content_extraction(self):
        import pdfplumber
        data = self._generate_full_os_pdf(manual=False)
        with pdfplumber.open(io.BytesIO(data)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        # Portuguese
        for w in ['Manutenção', 'tolerância', 'Descrição', 'Mecânica']:
            assert w.lower() in text.lower(), f"Missing: {w}"
        # Tech symbols
        for s in ['µm', '°C', 'Ω', 'Ø', '±', '≥', '≤', 'Δ', 'α', 'β']:
            assert s in text, f"Missing: {s}"
        # No corruption
        assert '?' not in text or text.count('?') == 0

    def test_os_manual_content_extraction(self):
        import pdfplumber
        data = self._generate_full_os_pdf(manual=True)
        with pdfplumber.open(io.BytesIO(data)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        assert 'µm' in text
        assert '°C' in text
        assert '?' not in text

    def test_os_size_comparison(self):
        digital = self._generate_full_os_pdf(manual=False)
        manual = self._generate_full_os_pdf(manual=True)
        # Both should be reasonable size
        for label, data in [('digital', digital), ('manual', manual)]:
            kb = len(data) / 1024
            assert kb < 500, f"{label} PDF too large: {kb:.1f}KB"
            assert kb > 5, f"{label} PDF too small: {kb:.1f}KB"


class TestFullInspectionPDFUnicode:
    """Simulate inspection PDFs with Unicode."""

    def _generate_inspection_pdf(self, manual=False):
        pdf = MaintrixPDF(
            empresa='ASTEC Engenharia',
            doc_title='Inspeção Visual µm',
            doc_code='INSP-2026-001',
            cor_primaria='#6366f1',
            modo_manual=manual,
        )
        pdf.alias_nb_pages()
        pdf.add_page()

        # Equipment
        pdf.section_title('Equipamento', 28)
        cy = pdf.get_y()
        pdf.field_pair('TAG', 'MOT-Ø100-α', 10, cy)
        pdf.field_pair('Equipamento', 'Motor Überprüfung ²', 105, cy)
        pdf.set_y(cy + 13); pdf.line_sep()

        # Info
        pdf.section_title('Informações da Inspeção')
        cy = pdf.get_y()
        pdf.field_pair('Tipo', 'Visual — sécurité', 10, cy)
        pdf.field_pair('Resultado', 'Não Conforme → ação', 105, cy)
        pdf.set_y(cy + 13); pdf.line_sep()

        # Checklist simulation
        pdf.section_title('Checklist de Inspeção')
        items = [
            f'Verificar temperatura ≤ 80 °C',
            f'Medir resistência ≥ 100 Ω',
            f'Folga axial: ± 0.05 µm',
            f'Diâmetro Ø correto — Δ ≤ 1%',
            f'Coeficiente α = 0.95, β = 0.05',
        ]
        cy = pdf.get_y()
        for i, item in enumerate(items):
            pdf.set_font('DejaVu', 'B', 7.5)
            pdf.set_text_color(99, 102, 241)
            pdf.set_xy(10, cy); pdf.cell(8, 5, str(i + 1))
            pdf.set_font('DejaVu', '', 8)
            pdf.set_text_color(30, 41, 59)
            pdf.set_xy(18, cy); pdf.cell(120, 5, item)
            cy += 6
        pdf.set_y(cy + 2); pdf.line_sep()

        # Observations
        pdf.section_title('Observações')
        pdf.text_block('señal de alarme → parar operación. sécurité équipement contrôle. Größe Straße.')
        pdf.line_sep()

        # Signatures
        pdf.signature_block([('Inspetor', 'José García µ'), ('Supervisor', 'Hans Überprüfung')])

        return pdf.output_bytes().read()

    def test_inspection_digital_generates(self):
        data = self._generate_inspection_pdf(manual=False)
        assert data[:4] == b'%PDF'
        assert len(data) > 3000

    def test_inspection_manual_generates(self):
        data = self._generate_inspection_pdf(manual=True)
        assert data[:4] == b'%PDF'
        assert len(data) > 3000

    def test_inspection_digital_content(self):
        import pdfplumber
        data = self._generate_inspection_pdf(manual=False)
        with pdfplumber.open(io.BytesIO(data)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        for sym in ['°C', 'Ω', 'µm', 'Ø', '±', 'Δ', 'α', 'β']:
            assert sym in text, f"Missing in inspection: {sym}"
        assert '?' not in text

    def test_inspection_manual_content(self):
        import pdfplumber
        data = self._generate_inspection_pdf(manual=True)
        with pdfplumber.open(io.BytesIO(data)) as p:
            text = '\n'.join(page.extract_text() or '' for page in p.pages)
        assert '°C' in text
        assert '?' not in text
