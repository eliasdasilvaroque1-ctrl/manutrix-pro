"""MAINTRIX Professional PDF Engine — v2.0
Generates configurable, multi-tenant A4 documents for OS and Inspections.
Supports: company branding, procedures, safety, photos with legends, manual forms.
"""
from fpdf import FPDF
import io, os, uuid, tempfile
from datetime import datetime, timezone

import qrcode
try:
    import httpx as httpx_lib
except ImportError:
    httpx_lib = None

import logging
logger = logging.getLogger(__name__)

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')


def register_unicode_fonts(pdf):
    """Register DejaVu Sans Unicode font family on any FPDF instance."""
    pdf.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.add_font("DejaVu", "I", os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"))
    pdf.add_font("DejaVu", "BI", os.path.join(FONT_DIR, "DejaVuSans-BoldOblique.ttf"))


APP_URL = os.environ.get("APP_URL", "") or os.environ.get("REACT_APP_BACKEND_URL", "")


def _safe(text, max_len=60):
    """Truncate text for PDF cells. Unicode handled natively by DejaVu font."""
    if not text:
        return '-'
    return str(text)[:max_len]


def _safe_long(text, max_len=500):
    if not text:
        return ''
    return str(text)[:max_len]


def make_qr(data_str, size=4):
    path = os.path.join(tempfile.gettempdir(), f"qr_{uuid.uuid4().hex[:8]}.png")
    q = qrcode.make(data_str, box_size=size, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.save(path)
    return path


async def fetch_file(url, prefix="dl"):
    """Download a file to temp. Returns path or None."""
    if not url or not httpx_lib:
        return None
    try:
        full_url = f"{APP_URL}{url}" if url.startswith('/') else url
        async with httpx_lib.AsyncClient() as hc:
            r = await hc.get(full_url, timeout=8, follow_redirects=True)
            if r.status_code == 200 and len(r.content) > 100:
                ext = '.png' if 'png' in (r.headers.get('content-type', '')) else '.jpg'
                path = os.path.join(tempfile.gettempdir(), f"{prefix}_{uuid.uuid4().hex[:8]}{ext}")
                with open(path, 'wb') as f:
                    f.write(r.content)
                return path
    except Exception:
        pass
    return None


def cleanup_files(*paths):
    for p in paths:
        if p:
            try:
                os.remove(p)
            except Exception:
                pass


class MaintrixPDF(FPDF):
    """Extended FPDF with MAINTRIX document helpers."""

    def __init__(self, empresa='MAINTRIX', doc_title='', doc_code='', logo_path=None, qr_path=None, cor_primaria='#6366f1', modo_manual=False):
        super().__init__('P', 'mm', 'A4')
        register_unicode_fonts(self)
        self.set_auto_page_break(auto=True, margin=22)
        self.empresa = _safe(empresa, 40)
        self.doc_title = _safe(doc_title, 60)
        self.doc_code = _safe(doc_code, 30)
        self.logo_path = logo_path
        self.qr_path = qr_path
        self.modo_manual = modo_manual
        self._temp_files = []
        # Parse cor
        try:
            c = cor_primaria.lstrip('#')
            self.cor_r, self.cor_g, self.cor_b = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        except Exception:
            self.cor_r, self.cor_g, self.cor_b = 99, 102, 241

    def header(self):
        # Dark header bar
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 24, 'F')
        x = 8
        if self.logo_path:
            try:
                self.image(self.logo_path, 8, 2, 20, 20)
                x = 30
            except Exception:
                pass
        self.set_font('DejaVu', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, 4)
        self.cell(100, 7, self.empresa)
        self.set_font('DejaVu', '', 8)
        self.set_xy(x, 12)
        self.cell(100, 5, self.doc_title)
        if self.qr_path:
            try:
                self.image(self.qr_path, 178, 1, 22, 22)
            except Exception:
                pass
        # Color bar
        self.set_fill_color(self.cor_r, self.cor_g, self.cor_b)
        self.rect(0, 24, 210, 1.5, 'F')

    def footer(self):
        self.set_y(-12)
        self.set_font('DejaVu', 'I', 7)
        self.set_text_color(148, 163, 184)
        code_str = f" | {self.doc_code}" if self.doc_code else ""
        self.cell(0, 5, f'{self.empresa}{code_str} | {datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")} UTC | Pagina {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title, y=None):
        if y is None:
            y = self.get_y()
        if y > 268:
            self.add_page()
            y = 30
        self.set_fill_color(241, 245, 249)
        self.rect(8, y, 194, 7, 'F')
        self.set_fill_color(self.cor_r, self.cor_g, self.cor_b)
        self.rect(8, y, 2, 7, 'F')
        self.set_font('DejaVu', 'B', 8)
        self.set_text_color(30, 41, 59)
        self.set_xy(12, y + 1.5)
        self.cell(0, 4, _safe(title.upper(), 80))
        self.set_y(y + 9)
        return y + 9

    def field_pair(self, label, value, x, y, w=88):
        self.set_font('DejaVu', '', 6.5)
        self.set_text_color(100, 116, 139)
        self.set_xy(x, y)
        self.cell(w, 3.5, _safe(label, 30))
        if self.modo_manual and not value:
            # Draw line for manual fill
            self.set_draw_color(180, 180, 180)
            self.line(x, y + 8, x + w - 2, y + 8)
        else:
            self.set_font('DejaVu', 'B', 8.5)
            self.set_text_color(15, 23, 42)
            self.set_xy(x, y + 3.5)
            self.cell(w, 5, _safe(value, 55))

    def line_sep(self, y=None):
        if y is None:
            y = self.get_y()
        self.set_draw_color(226, 232, 240)
        self.line(8, y, 202, y)
        self.set_y(y + 1)
        return y + 1

    def text_block(self, text, y=None):
        if y is None:
            y = self.get_y()
        if y > 270:
            self.add_page()
            y = 30
        self.set_font('DejaVu', '', 8.5)
        self.set_text_color(30, 41, 59)
        self.set_xy(10, y)
        self.multi_cell(190, 4.5, _safe_long(text, 800))
        return self.get_y() + 2

    def manual_box(self, label='', height=20, y=None):
        """Draw a box for manual handwriting."""
        if y is None:
            y = self.get_y()
        if y + height > 275:
            self.add_page()
            y = 30
        if label:
            self.set_font('DejaVu', 'I', 7)
            self.set_text_color(140, 140, 140)
            self.set_xy(10, y)
            self.cell(190, 4, _safe(label, 60))
            y += 4
        self.set_draw_color(200, 200, 200)
        self.rect(10, y, 190, height)
        # Draw lines inside
        line_y = y + 5
        while line_y < y + height - 2:
            self.set_draw_color(230, 230, 230)
            self.line(12, line_y, 198, line_y)
            line_y += 5
        self.set_y(y + height + 2)
        return y + height + 2

    def signature_block(self, names=None):
        y = self.get_y()
        if y > 245:
            self.add_page()
            y = 30
        y = self.section_title('Assinaturas e Aprovacoes', y)
        y += 18
        cols = names or [('Executor', '-'), ('Supervisor', '-')]
        col_w = 180 / len(cols)
        for i, (role_label, name) in enumerate(cols):
            x = 15 + i * col_w
            self.set_draw_color(100, 116, 139)
            self.line(x, y, x + col_w - 10, y)
            self.set_font('DejaVu', '', 7.5)
            self.set_text_color(100, 116, 139)
            self.set_xy(x, y + 1)
            self.cell(col_w - 10, 4, _safe(role_label, 25))
            self.set_xy(x, y + 5)
            self.cell(col_w - 10, 4, f'Nome: {_safe(name, 25)}')
            self.set_xy(x, y + 10)
            self.cell(col_w - 10, 4, 'Data: ____/____/________')
        self.set_y(y + 18)

    # ===== PHOTO GRID (professional, no filenames) =====
    def photo_grid(self, attachments, foto_config=None):
        """Render photos in a professional grid with legends, no filenames."""
        if not attachments:
            return
        cols = (foto_config or {}).get('grid_colunas', 2)
        max_pp = (foto_config or {}).get('max_por_pagina', 4)

        y = self.section_title('Evidencias Fotograficas')
        img_w = 85 if cols == 2 else 58
        img_h = 55 if cols == 2 else 40
        col_idx = 0
        count = 0

        for att in attachments:
            if count >= max_pp * 3:
                break
            if y + img_h + 12 > 275:
                self.add_page()
                y = 30
                col_idx = 0
            x = 10 + col_idx * (img_w + 5)

            # Try to embed actual image
            img_path = att.get('_local_path')
            if img_path:
                try:
                    self.image(img_path, x, y, img_w, img_h)
                except Exception:
                    self.set_draw_color(200, 200, 200)
                    self.rect(x, y, img_w, img_h)
                    self.set_font('DejaVu', 'I', 8)
                    self.set_text_color(150, 150, 150)
                    self.set_xy(x + 5, y + img_h / 2 - 3)
                    self.cell(img_w - 10, 6, '[Imagem indisponivel]')
            else:
                self.set_draw_color(200, 200, 200)
                self.rect(x, y, img_w, img_h)
                self.set_font('DejaVu', 'I', 8)
                self.set_text_color(150, 150, 150)
                self.set_xy(x + 5, y + img_h / 2 - 3)
                self.cell(img_w - 10, 6, '[Imagem indisponivel]')

            # Legend (NEVER filename)
            legend = att.get('legenda') or att.get('categoria', '')
            if legend:
                legend = legend.capitalize()
            else:
                legend = f"Foto {count + 1:02d}"
            self.set_font('DejaVu', '', 7)
            self.set_text_color(80, 80, 80)
            self.set_xy(x, y + img_h + 1)
            date_str = ''
            created = att.get('created_at', '')
            if created:
                date_str = f" - {str(created)[:10]}"
            self.cell(img_w, 4, _safe(f"{legend}{date_str}", 45))

            col_idx += 1
            count += 1
            if col_idx >= cols:
                col_idx = 0
                y += img_h + 10
        if col_idx > 0:
            y += img_h + 10
        self.set_y(y)

    # ===== PROCEDURE SECTION =====
    def procedure_section(self, proc, manual=False):
        """Render structured procedure: steps, tools, materials."""
        if not proc:
            if manual:
                y = self.section_title('Procedimento de Execucao')
                self.manual_box('Descreva o procedimento realizado:', 30)
            return
        y = self.section_title('Procedimento de Execucao')
        # Objective
        obj = proc.get('objetivo', '')
        if obj:
            self.set_font('DejaVu', 'B', 7.5)
            self.set_text_color(80, 80, 80)
            self.set_xy(10, self.get_y())
            self.cell(20, 4, 'Objetivo:')
            self.set_font('DejaVu', '', 8)
            self.set_text_color(30, 41, 59)
            self.set_xy(30, self.get_y())
            self.cell(170, 4, _safe(obj, 80))
            self.set_y(self.get_y() + 5)
        # Pre-requisites
        pre = proc.get('pre_requisitos', '')
        if pre:
            self.set_font('DejaVu', 'I', 7.5)
            self.set_text_color(100, 100, 100)
            self.set_xy(10, self.get_y())
            self.cell(190, 4, _safe(f"Pre-requisitos: {pre}", 100))
            self.set_y(self.get_y() + 5)
        # Steps table
        etapas = proc.get('etapas', [])
        if etapas:
            self.set_font('DejaVu', 'B', 7)
            self.set_text_color(100, 116, 139)
            cy = self.get_y()
            self.set_xy(10, cy); self.cell(8, 4, '#')
            self.set_xy(18, cy); self.cell(120, 4, 'Descricao da Etapa')
            if manual:
                self.set_xy(140, cy); self.cell(30, 4, 'Executado')
                self.set_xy(170, cy); self.cell(30, 4, 'Obs')
            self.set_y(cy + 5)
            for et in etapas[:20]:
                cy = self.get_y()
                if cy > 270:
                    self.add_page(); cy = 30
                num = et.get('numero', '')
                desc = et.get('descricao', '')
                self.set_font('DejaVu', 'B', 8)
                self.set_text_color(self.cor_r, self.cor_g, self.cor_b)
                self.set_xy(10, cy); self.cell(8, 5, _safe(str(num), 3))
                self.set_font('DejaVu', '', 8)
                self.set_text_color(30, 41, 59)
                self.set_xy(18, cy); self.cell(120, 5, _safe(desc, 65))
                if manual:
                    self.set_draw_color(200, 200, 200)
                    self.rect(140, cy, 28, 5)  # checkbox area
                    self.rect(170, cy, 30, 5)  # obs area
                self.set_y(cy + 6)
            self.set_y(self.get_y() + 2)
        # Tools & Materials
        tools = proc.get('ferramentas', [])
        mats = proc.get('materiais', [])
        if tools or mats:
            cy = self.get_y()
            if tools:
                self.set_font('DejaVu', 'B', 7)
                self.set_text_color(100, 100, 100)
                self.set_xy(10, cy); self.cell(30, 4, 'Ferramentas:')
                self.set_font('DejaVu', '', 7.5)
                self.set_text_color(30, 41, 59)
                self.set_xy(35, cy); self.cell(70, 4, _safe(', '.join(tools), 70))
            if mats:
                self.set_font('DejaVu', 'B', 7)
                self.set_text_color(100, 100, 100)
                self.set_xy(110, cy); self.cell(25, 4, 'Materiais:')
                self.set_font('DejaVu', '', 7.5)
                self.set_text_color(30, 41, 59)
                self.set_xy(135, cy); self.cell(65, 4, _safe(', '.join(mats), 65))
            self.set_y(cy + 6)
        # Manual obs box
        if manual:
            self.manual_box('Observacoes do procedimento:', 15)
        obs = proc.get('observacoes', '')
        if obs and not manual:
            self.text_block(f"Obs: {obs}")
        self.line_sep()

    # ===== SAFETY SECTION =====
    def safety_section(self, seg, manual=False):
        """Render structured safety: risks, EPIs, LOTO, APR."""
        if not seg:
            if manual:
                y = self.section_title('Seguranca do Trabalho')
                self.manual_box('Riscos e medidas de controle:', 20)
            return
        y = self.section_title('Seguranca do Trabalho')
        cy = self.get_y()
        # Risks
        riscos = seg.get('riscos', [])
        if riscos:
            self.set_font('DejaVu', 'B', 7.5)
            self.set_text_color(239, 68, 68)
            self.set_xy(10, cy); self.cell(30, 4, 'RISCOS:')
            cy += 5
            for r in riscos[:10]:
                if cy > 270: self.add_page(); cy = 30
                desc = r if isinstance(r, str) else r.get('descricao', '')
                self.set_font('DejaVu', '', 8)
                self.set_text_color(30, 41, 59)
                self.set_xy(12, cy); self.cell(186, 4, _safe(f"- {desc}", 90))
                cy += 4.5
            self.set_y(cy + 2)
        # Medidas
        medidas = seg.get('medidas_controle', [])
        if medidas:
            cy = self.get_y()
            self.set_font('DejaVu', 'B', 7.5)
            self.set_text_color(16, 185, 129)
            self.set_xy(10, cy); self.cell(40, 4, 'MEDIDAS DE CONTROLE:')
            cy += 5
            for m in medidas[:10]:
                self.set_font('DejaVu', '', 8)
                self.set_text_color(30, 41, 59)
                self.set_xy(12, cy); self.cell(186, 4, _safe(f"- {m}", 90))
                cy += 4.5
            self.set_y(cy + 2)
        # EPIs + EPCs side by side
        epis = seg.get('epis', [])
        epcs = seg.get('epcs', [])
        if epis or epcs:
            cy = self.get_y()
            if epis:
                self.set_font('DejaVu', 'B', 7.5)
                self.set_text_color(99, 102, 241)
                self.set_xy(10, cy); self.cell(20, 4, 'EPIs:')
                self.set_font('DejaVu', '', 7.5)
                self.set_text_color(30, 41, 59)
                self.set_xy(10, cy + 4); self.cell(90, 4, _safe(', '.join(epis), 80))
            if epcs:
                self.set_font('DejaVu', 'B', 7.5)
                self.set_text_color(99, 102, 241)
                self.set_xy(105, cy); self.cell(20, 4, 'EPCs:')
                self.set_font('DejaVu', '', 7.5)
                self.set_text_color(30, 41, 59)
                self.set_xy(105, cy + 4); self.cell(90, 4, _safe(', '.join(epcs), 80))
            self.set_y(cy + 10)
        # LOTO / APR / PT
        loto = seg.get('loto') or {}
        apr = seg.get('apr') or {}
        pt = seg.get('pt') or {}
        flags = []
        if loto.get('necessario'): flags.append('LOTO/Bloqueio')
        if apr.get('necessaria'): flags.append(f"APR {apr.get('numero', '')}")
        if pt.get('necessaria'): flags.append(f"PT ({pt.get('tipo', '')})")
        if flags:
            cy = self.get_y()
            self.set_font('DejaVu', 'B', 8)
            self.set_text_color(239, 68, 68)
            self.set_xy(10, cy); self.cell(190, 5, _safe('REQUER: ' + ' | '.join(flags), 90))
            self.set_y(cy + 6)
        # Bloqueios
        bloqueios = seg.get('bloqueios', [])
        if bloqueios:
            cy = self.get_y()
            self.set_font('DejaVu', 'B', 7.5)
            self.set_text_color(100, 100, 100)
            self.set_xy(10, cy); self.cell(40, 4, 'BLOQUEIOS:')
            cy += 5
            for b in bloqueios[:8]:
                desc = b if isinstance(b, str) else f"{b.get('tipo','')}: {b.get('descricao','')}"
                self.set_font('DejaVu', '', 7.5)
                self.set_text_color(30, 41, 59)
                self.set_xy(12, cy); self.cell(186, 4, _safe(f"- {desc}", 90))
                cy += 4.5
            self.set_y(cy + 2)
        # Obs
        obs = seg.get('observacoes', '')
        if obs:
            self.text_block(f"Obs Seguranca: {obs}")
        if manual:
            self.manual_box('Observacoes de seguranca do executor:', 12)
        self.line_sep()

    def output_bytes(self):
        buf = io.BytesIO()
        buf.write(self.output())
        buf.seek(0)
        return buf
