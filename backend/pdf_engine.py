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
    """Download a file to temp. Returns path or None. Uses StorageManager for cloud files."""
    if not url:
        return None
    try:
        # Direct local file access (no HTTP needed)
        if url.startswith('/api/uploads/manuals/'):
            fname = url.split('/api/uploads/manuals/')[-1]
            local = os.path.join(os.path.dirname(__file__), 'uploads', 'manuals', fname)
            if os.path.exists(local):
                return local
        elif url.startswith('/api/uploads/'):
            fname = url.split('/api/uploads/')[-1]
            local = os.path.join(os.path.dirname(__file__), 'uploads', fname)
            if os.path.exists(local):
                return local
        # Cloud storage via StorageManager (Supabase primary + Emergent fallback)
        if url.startswith('/api/storage/'):
            spath = url.replace('/api/storage/', '', 1)
            try:
                import storage as objstore
                # Check file_registry for migrated Supabase path
                try:
                    import pymongo
                    from dotenv import load_dotenv
                    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
                    mongo_url = os.environ.get('MONGO_URL', '')
                    db_name = os.environ.get('DB_NAME', 'maintrix')
                    if mongo_url:
                        client = pymongo.MongoClient(mongo_url)
                        db_sync = client[db_name]
                        record = db_sync.file_registry.find_one(
                            {"url": f"/api/storage/{spath}", "storage_provider": "supabase", "migration_status": "completed"},
                            {"_id": 0, "storage_path": 1}
                        )
                        if record and record.get("storage_path"):
                            spath = record["storage_path"]
                except Exception:
                    pass  # Use original spath as fallback

                data, ct = objstore.get_file(spath)
                if data and len(data) > 100:
                    ext = '.png' if '.png' in spath or 'png' in (ct or '') else '.jpg'
                    path = os.path.join(tempfile.gettempdir(), f"{prefix}_{uuid.uuid4().hex[:8]}{ext}")
                    with open(path, 'wb') as f:
                        f.write(data)
                    return path
            except Exception:
                pass
        # Fallback to HTTP for external URLs only
        if not httpx_lib:
            return None
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

    def __init__(self, empresa='MAINTRIX', doc_title='', doc_code='', logo_path=None, qr_path=None, cor_primaria='#6366f1', modo_manual=False, emissor_nome='', versao='v5.2.0', local_trabalho=''):
        super().__init__('P', 'mm', 'A4')
        register_unicode_fonts(self)
        self.set_auto_page_break(auto=True, margin=22)
        self.empresa = _safe(empresa, 40)
        self.local_trabalho = _safe(local_trabalho, 50)
        self.doc_title = _safe(doc_title, 60)
        self.doc_code = _safe(doc_code, 30)
        self.logo_path = logo_path
        self.qr_path = qr_path
        self.modo_manual = modo_manual
        self.emissor_nome = emissor_nome
        self.versao = versao
        self._temp_files = []
        # Parse cor
        try:
            c = cor_primaria.lstrip('#')
            self.cor_r, self.cor_g, self.cor_b = int(c[:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        except Exception:
            self.cor_r, self.cor_g, self.cor_b = 99, 102, 241

    def section_title(self, title, y=None):
        if y is None:
            y = self.get_y()
        # Ensure at least 20mm of space after title (avoid orphan titles)
        if y > 258:
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
        self.set_y(y + 10)
        return y + 10

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
        self.multi_cell(190, 4.5, _safe_long(text, 5000))
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
        # Signature block needs ~50mm; move to new page if not enough
        if y > 230:
            self.add_page()
            y = 30
        y = self.section_title('Assinaturas e Aprovacoes', y)

        cols = names or [('Executor', '-'), ('Supervisor', '-')]
        col_w = 180 / len(cols)
        sig_top = y + 16  # Space above signature line

        for i, (role_label, name) in enumerate(cols):
            x = 15 + i * col_w

            # Signature line
            self.set_draw_color(80, 90, 100)
            self.line(x, sig_top, x + col_w - 12, sig_top)

            # Role label (bold, primary color)
            self.set_font('DejaVu', 'B', 8)
            self.set_text_color(self.cor_r, self.cor_g, self.cor_b)
            self.set_xy(x, sig_top + 1.5)
            self.cell(col_w - 12, 4, _safe(role_label, 25))

            # Name
            self.set_font('DejaVu', '', 7.5)
            self.set_text_color(30, 41, 59)
            self.set_xy(x, sig_top + 6)
            self.cell(col_w - 12, 4, f'Nome: {_safe(name, 30)}')

            # Date line
            self.set_xy(x, sig_top + 11)
            self.cell(col_w - 12, 4, 'Data: ____/____/________')

        self.set_y(sig_top + 20)

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

    # ===== PROCEDURE ANNEX (full document) =====
    async def procedure_annex(self, proc, proc_index=1, execution_data=None):
        """Render a complete procedure as a full-page annex.
        Fase 3: Texto sequencial de orientação — sem checkboxes, sem PENDENTE, sem progresso digital.
        """
        if not proc:
            return

        # New page for each procedure annex
        self.add_page()

        # Annex header
        self.set_fill_color(self.cor_r, self.cor_g, self.cor_b)
        self.rect(8, 15, 194, 10, 'F')
        self.set_font('DejaVu', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 16.5)
        self.cell(0, 7, f'ANEXO {proc_index} \u2014 PROCEDIMENTO DE MANUTEN\u00c7\u00c3O')
        self.set_y(30)

        # Identification block
        self.section_title('Identifica\u00e7\u00e3o do Procedimento')
        cy = self.get_y()
        self.field_pair('T\u00edtulo', proc.get('nome', proc.get('titulo', '')), 10, cy, w=190)
        cy += 11
        self.field_pair('C\u00f3digo', proc.get('codigo', ''), 10, cy)
        self.field_pair('Revis\u00e3o', proc.get('revisao', '01'), 105, cy)
        cy += 11
        self.field_pair('Vers\u00e3o', str(proc.get('versao', 1)), 10, cy)
        data_rev = (proc.get('updated_at') or proc.get('created_at') or '')[:10]
        self.field_pair('Data da Revis\u00e3o', data_rev, 105, cy)
        cy += 11
        self.field_pair('Respons\u00e1vel Aprova\u00e7\u00e3o', proc.get('aprovador', proc.get('responsavel', '-')), 10, cy)
        self.set_y(cy + 13)
        self.line_sep()

        # Objective
        objetivo = proc.get('objetivo', '')
        if objetivo:
            self.section_title('Objetivo')
            self.text_block(objetivo)
            self.line_sep()

        # Description
        descricao = proc.get('descricao', '')
        if descricao:
            self.section_title('Descri\u00e7\u00e3o')
            self.text_block(descricao)
            self.line_sep()

        # Prerequisites
        prereqs = proc.get('pre_requisitos', proc.get('prerequisitos', ''))
        if prereqs:
            self.section_title('Pr\u00e9-Requisitos')
            if isinstance(prereqs, list):
                for p in prereqs:
                    self._bullet_item(str(p))
            else:
                self.text_block(str(prereqs))
            self.line_sep()

        # Safety alerts from procedure
        alertas = proc.get('alertas_seguranca', proc.get('seguranca', ''))
        if alertas:
            self.section_title('Alertas de Seguran\u00e7a')
            if isinstance(alertas, str):
                self.text_block(alertas)
            elif isinstance(alertas, list):
                for a in alertas:
                    self._bullet_item(str(a) if isinstance(a, str) else a.get('descricao', str(a)))
            self.line_sep()

        # EPIs
        epis = proc.get('epis', proc.get('epi', []))
        if epis:
            self.section_title('Equipamentos de Prote\u00e7\u00e3o Individual (EPI)')
            if isinstance(epis, list):
                for e in epis:
                    name = e.get('nome', str(e)) if isinstance(e, dict) else str(e)
                    self._bullet_item(name)
            else:
                self.text_block(str(epis))
            self.line_sep()

        # Tools
        ferramentas = proc.get('ferramentas', [])
        if ferramentas:
            self.section_title('Ferramentas')
            if isinstance(ferramentas, list):
                for f in ferramentas:
                    name = f.get('nome', str(f)) if isinstance(f, dict) else str(f)
                    self._bullet_item(name)
            else:
                self.text_block(str(ferramentas))
            self.line_sep()

        # Steps — TEXTO SEQUENCIAL FIXO (sem checkbox, sem PENDENTE, sem executado por)
        etapas = proc.get('etapas', [])
        if etapas:
            self.section_title('Etapas de Execu\u00e7\u00e3o')
            sorted_etapas = sorted(etapas, key=lambda e: e.get('ordem', 0))
            for etapa in sorted_etapas:
                cy = self.get_y()
                # Ensure title + description stay together (min 20mm)
                if cy > 255:
                    self.add_page()
                    cy = 30

                ordem = etapa.get('ordem', '')

                # Step number (large, highlighted)
                self.set_font('DejaVu', 'B', 11)
                self.set_text_color(self.cor_r, self.cor_g, self.cor_b)
                self.set_xy(10, cy)
                self.cell(12, 6, f'{ordem}.')

                # Step title (bold)
                self.set_font('DejaVu', 'B', 9)
                self.set_text_color(15, 23, 42)
                self.set_xy(22, cy)
                self.cell(0, 6, _safe(etapa.get('titulo', ''), 90))
                cy += 8

                # Step description
                desc = etapa.get('descricao', '')
                if desc:
                    self.set_font('DejaVu', '', 8.5)
                    self.set_text_color(50, 50, 50)
                    self.set_xy(22, cy)
                    self.multi_cell(175, 4.5, _safe_long(desc, 2000))
                    cy = self.get_y() + 1

                # Step image (if any)
                img_url = etapa.get('imagem_url', etapa.get('foto_url', ''))
                if img_url:
                    img_path = await fetch_file(img_url, f'proc_step_{ordem}')
                    if img_path:
                        if cy > 210:
                            self.add_page()
                            cy = 30
                        try:
                            self.image(img_path, 22, cy, 60, 40)
                            cy += 43
                        except Exception:
                            pass
                        try:
                            os.remove(img_path)
                        except Exception:
                            pass

                self.set_y(cy + 1)
                # Subtle separator between steps
                self.set_draw_color(220, 220, 220)
                self.line(22, self.get_y(), 200, self.get_y())
                self.set_y(self.get_y() + 3)

        # Observations from procedure
        obs = proc.get('observacoes', proc.get('notas', ''))
        if obs:
            self.section_title('Observa\u00e7\u00f5es do Procedimento')
            self.text_block(str(obs))
            self.line_sep()

        # Fim do anexo — obs e assinaturas ficam no corpo principal da OS

    def _bullet_item(self, text):
        """Render a bullet-pointed item."""
        cy = self.get_y()
        if cy > 270:
            self.add_page()
            cy = 30
        self.set_font('DejaVu', '', 8)
        self.set_text_color(30, 41, 59)
        self.set_xy(14, cy)
        self.cell(4, 4, '•')
        self.set_xy(19, cy)
        self.multi_cell(178, 4, _safe_long(text, 300))
        if self.get_y() == cy:
            self.set_y(cy + 5)

    # ===== PROCEDURE SECTION (inline summary — kept for backward compat) =====
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

    # ===== CUSTOM FIELDS SECTION =====
    def custom_fields_section(self, campos_defs, campos_valores, manual=False):
        """Render custom fields from layout snapshot.
        - Hides empty fields (unless manual mode)
        - Hides technical names (TEST_C_*, FIELD_*, TMP_*)
        - Hides entire section if nothing to show
        """
        if not campos_defs:
            return

        TECHNICAL_PREFIXES = ('TEST_C_', 'FIELD_', 'TMP_', 'test_c_', 'field_', 'tmp_')

        # Filter: only fields with values (or all in manual mode)
        visible_campos = []
        for campo in campos_defs:
            ident = campo.get('identificador_tecnico', '')
            nome = campo.get('nome', '')
            # Skip fields with technical names and no friendly name
            if not nome or nome.startswith(TECHNICAL_PREFIXES):
                if ident.startswith(TECHNICAL_PREFIXES):
                    continue
                nome = ident  # fallback to ident if nome is empty
            valor = (campos_valores or {}).get(ident, '')
            if manual or (valor is not None and str(valor).strip() != ''):
                visible_campos.append((campo, nome, valor))

        if not visible_campos:
            return

        y = self.section_title('Campos Personalizados')
        col1_x, col2_x = 10, 105
        row_h = 10
        col_idx = 0

        for campo, nome, valor in visible_campos:
            cy = self.get_y()
            if cy > 268:
                self.add_page()
                cy = 30
                col_idx = 0

            x = col1_x if col_idx == 0 else col2_x
            tipo = campo.get('tipo', 'texto_curto')
            unidade = campo.get('unidade_medida', '')

            if manual and not valor:
                self.field_pair(nome, None, x, cy)
            else:
                display = str(valor) if valor else '-'
                if unidade and valor:
                    display = f"{valor} {unidade}"
                if tipo == 'sim_nao' and valor:
                    display = 'Sim' if str(valor).lower() in ('true', 'sim', '1', 'yes') else 'Nao'
                if tipo == 'checkbox' and valor:
                    display = 'Sim' if str(valor).lower() in ('true', 'sim', '1', 'yes') else 'Nao'
                self.field_pair(nome, display, x, cy)

            col_idx += 1
            if col_idx >= 2:
                col_idx = 0
                self.set_y(cy + row_h)

        if col_idx == 1:
            self.set_y(self.get_y() + row_h)
        self.line_sep()

    # ===== CUSTOM HEADER FROM LAYOUT =====
    def custom_header_from_layout(self, cab_snapshot):
        """Override header rendering with custom cabecalho from layout snapshot."""
        if not cab_snapshot:
            return
        self._custom_cabecalho = cab_snapshot

    def header(self):
        cab = getattr(self, '_custom_cabecalho', None)
        if cab:
            self._render_custom_header(cab)
        else:
            self._render_default_header()

    def _render_default_header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 26, 'F')
        x = 8
        if self.logo_path:
            try:
                self.image(self.logo_path, 8, 2, 20, 20)
                x = 30
            except Exception:
                pass
        # Nome da empresa (primário)
        self.set_font('DejaVu', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, 2)
        self.cell(120, 6, self.empresa)
        # Unidade (secundário)
        if self.local_trabalho and self.local_trabalho != '-':
            self.set_font('DejaVu', '', 8)
            self.set_text_color(200, 210, 220)
            self.set_xy(x, 9)
            self.cell(120, 4, f"Unidade: {self.local_trabalho}")
        # Título do documento (OS nº)
        self.set_font('DejaVu', 'B', 9)
        self.set_text_color(self.cor_r, self.cor_g, self.cor_b)
        y_title = 15 if (self.local_trabalho and self.local_trabalho != '-') else 10
        self.set_xy(x, y_title)
        self.cell(120, 5, self.doc_title)
        # Barra de cor primária
        self.set_fill_color(self.cor_r, self.cor_g, self.cor_b)
        self.rect(0, 26, 210, 1.5, 'F')

    def _render_custom_header(self, cab):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 28, 'F')
        x = 8
        if self.logo_path:
            try:
                self.image(self.logo_path, 8, 2, 22, 22)
                x = 33
            except Exception:
                pass
        # Company info
        nome = cab.get('nome_fantasia') or cab.get('razao_social') or self.empresa
        self.set_font('DejaVu', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, 3)
        self.cell(120, 6, _safe(nome, 40))
        # Sub-info line
        sub_parts = []
        if cab.get('cnpj'):
            sub_parts.append(f"CNPJ: {cab['cnpj']}")
        if cab.get('telefone'):
            sub_parts.append(cab['telefone'])
        if cab.get('email'):
            sub_parts.append(cab['email'])
        if sub_parts:
            self.set_font('DejaVu', '', 7)
            self.set_xy(x, 10)
            self.cell(120, 4, _safe(' | '.join(sub_parts), 70))
        # Address
        if cab.get('endereco'):
            self.set_font('DejaVu', '', 6.5)
            self.set_xy(x, 15)
            self.cell(120, 4, _safe(cab['endereco'], 60))
        # Doc title
        self.set_font('DejaVu', '', 8)
        self.set_xy(x, 20)
        self.cell(120, 5, self.doc_title)
        # QR
        if self.qr_path:
            try:
                self.image(self.qr_path, 178, 2, 24, 24)
            except Exception:
                pass
        self.set_fill_color(self.cor_r, self.cor_g, self.cor_b)
        self.rect(0, 28, 210, 1.5, 'F')

    # ===== CUSTOM FOOTER FROM LAYOUT =====
    def custom_footer_from_layout(self, rod_snapshot):
        if not rod_snapshot:
            return
        self._custom_rodape = rod_snapshot

    def footer(self):
        rod = getattr(self, '_custom_rodape', None)
        if rod:
            self._render_custom_footer(rod)
        else:
            self._render_default_footer()

    def _render_default_footer(self):
        self.set_y(-15)
        self.set_draw_color(226, 232, 240)
        self.line(8, self.get_y(), 202, self.get_y())
        self.set_y(-12)
        self.set_font('DejaVu', '', 6.5)
        self.set_text_color(148, 163, 184)
        parts = ["Documento gerado pelo MAINTRIX Enterprise"]
        parts.append(datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M") + " UTC")
        if self.emissor_nome:
            parts.append(f"Emitido por: {self.emissor_nome}")
        parts.append(f"Pagina {self.page_no()}/{{nb}}")
        self.cell(0, 4, ' | '.join(parts), align='C')

    def _render_custom_footer(self, rod):
        self.set_y(-14)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_y(-12)
        parts = []
        if rod.get('texto_personalizado'):
            parts.append(rod['texto_personalizado'])
        if rod.get('mostrar_identificacao_doc') and self.doc_code:
            parts.append(self.doc_code)
        if rod.get('mostrar_data_emissao'):
            parts.append(datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M") + " UTC")
        if rod.get('mostrar_paginacao'):
            parts.append(f"Página {self.page_no()}/{{nb}}")
        self.set_font('DejaVu', 'I', 6.5)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, ' | '.join(parts), align='C')

    # ===== SIGNATURE BLOCKS =====
    def custom_signature_blocks(self, assinaturas_dados=None, blocos_config=None):
        """Render signature blocks from layout or OS data."""
        data = assinaturas_dados or []
        if not data and not blocos_config:
            self.signature_block()
            return
        y = self.get_y()
        # Estimate total height needed: ~22mm per signature entry
        entries = data if data else [{"nome": "-", "papel": b.get("papel", "Executor")} for b in (blocos_config or [])]
        needed_h = 12 + len(entries) * 22
        if y + needed_h > 270:
            self.add_page()
            y = 30
        y = self.section_title('Assinaturas e Aprovacoes', y)
        y += 2

        for entry in entries:
            if y > 250:
                self.add_page()
                y = 30
            papel = entry.get('papel', 'Executor').capitalize()
            nome = entry.get('nome', '-')
            cargo = entry.get('cargo', '')
            matricula = entry.get('matricula', '')
            status = entry.get('status', 'pendente')
            img_url = entry.get('imagem_url', '')

            self.set_font('DejaVu', 'B', 8)
            self.set_text_color(self.cor_r, self.cor_g, self.cor_b)
            self.set_xy(10, y)
            self.cell(40, 5, papel)

            status_color = {'assinado': (16, 185, 129), 'recusado': (239, 68, 68), 'pendente': (234, 179, 8)}.get(status, (148, 163, 184))
            self.set_text_color(*status_color)
            self.set_font('DejaVu', 'B', 7)
            self.set_xy(50, y)
            self.cell(30, 5, status.upper())

            self.set_font('DejaVu', '', 8)
            self.set_text_color(30, 41, 59)
            y += 6
            self.set_xy(10, y)
            info_parts = [f"Nome: {nome}"]
            if cargo:
                info_parts.append(f"Cargo: {cargo}")
            if matricula:
                info_parts.append(f"Matricula: {matricula}")
            self.cell(190, 4, _safe(' | '.join(info_parts), 90))
            y += 5

            if entry.get('data'):
                self.set_font('DejaVu', '', 7)
                self.set_text_color(100, 116, 139)
                self.set_xy(10, y)
                self.cell(90, 4, f"Data: {str(entry['data'])[:19]}")
                y += 5

            # Signature image
            if img_url and hasattr(self, '_sig_paths'):
                sig_path = self._sig_paths.get(img_url)
                if sig_path:
                    try:
                        self.image(sig_path, 10, y, 50, 15)
                        y += 17
                    except Exception:
                        pass

            # Signature line for manual
            self.set_draw_color(80, 90, 100)
            self.line(10, y + 2, 80, y + 2)
            y += 8
        self.set_y(y + 2)



# ============== QR CODE PDF GENERATION ==============

def generate_qr_label_pdf(ativos, empresa="MAINTRIX", modelo="etiqueta"):
    """Generate QR Code PDF for one or more assets. Returns BytesIO."""
    from io import BytesIO
    import qrcode
    import tempfile
    from routes.assets import build_public_equipment_url

    pdf = FPDF('P', 'mm', 'A4')
    register_unicode_fonts(pdf)

    for ativo in ativos:
        pdf.add_page()
        tag = _safe(ativo.get('tag', ''), 30)
        nome = _safe(ativo.get('nome', ''), 60)
        # URL recalculada via build_public_equipment_url — nunca confia no campo salvo
        full_url = build_public_equipment_url(ativo)
        area = _safe(ativo.get('sector', {}).get('nome', '') if isinstance(ativo.get('sector'), dict) else '', 40)
        fab = _safe(ativo.get('fabricante', '') or '', 30)
        mod = _safe(ativo.get('modelo', '') or '', 30)

        # Generate QR image
        qr_path = None
        if full_url:
            try:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=20, border=3)
                qr.add_data(full_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_path = os.path.join(tempfile.gettempdir(), f"qr_{uuid.uuid4().hex[:8]}.png")
                img.save(qr_path)
            except Exception:
                qr_path = None

        if modelo == "simples":
            # MODEL 1: Simple QR
            pdf.set_font('DejaVu', 'B', 24)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(10, 30)
            pdf.cell(190, 12, tag, align='C')
            if qr_path:
                pdf.image(qr_path, 55, 55, 100, 100)
            pdf.set_font('DejaVu', '', 11)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(10, 165)
            pdf.cell(190, 6, 'Aponte a camera para conhecer este equipamento', align='C')

        elif modelo == "placa":
            # MODEL 3: Technical Plate A4
            pdf.set_fill_color(15, 23, 42)
            pdf.rect(0, 0, 210, 35, 'F')
            pdf.set_font('DejaVu', 'B', 20)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(10, 8)
            pdf.cell(190, 10, _safe(empresa, 40), align='C')
            pdf.set_font('DejaVu', '', 11)
            pdf.set_xy(10, 20)
            pdf.cell(190, 7, 'Placa de Identificacao do Equipamento', align='C')

            y = 45
            pdf.set_font('DejaVu', 'B', 28)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(10, y)
            pdf.cell(190, 14, tag, align='C')
            y += 18
            pdf.set_font('DejaVu', '', 14)
            pdf.set_xy(10, y)
            pdf.cell(190, 8, nome, align='C')
            y += 14

            # Technical info
            pdf.set_font('DejaVu', '', 10)
            pdf.set_text_color(80, 80, 80)
            info_lines = []
            if fab: info_lines.append(f"Fabricante: {fab}")
            if mod: info_lines.append(f"Modelo: {mod}")
            if area: info_lines.append(f"Area: {area}")
            for line in info_lines:
                pdf.set_xy(10, y)
                pdf.cell(190, 6, line, align='C')
                y += 8

            if qr_path:
                pdf.image(qr_path, 55, y + 5, 100, 100)
                y += 110

            pdf.set_font('DejaVu', '', 9)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(10, y + 5)
            pdf.cell(190, 5, 'Aponte a camera do celular para conhecer este equipamento', align='C')

            # Footer
            pdf.set_y(-20)
            pdf.set_font('DejaVu', '', 7)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(190, 4, f'Monitorado pelo MAINTRIX Enterprise', align='C')

        else:
            # MODEL 2: Equipment Label (default)
            pdf.set_fill_color(15, 23, 42)
            pdf.rect(0, 0, 210, 20, 'F')
            pdf.set_font('DejaVu', 'B', 12)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(10, 5)
            pdf.cell(190, 10, _safe(empresa, 40), align='C')

            pdf.set_font('DejaVu', 'B', 22)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(10, 28)
            pdf.cell(190, 10, tag, align='C')
            pdf.set_font('DejaVu', '', 12)
            pdf.set_xy(10, 42)
            pdf.cell(190, 7, nome, align='C')

            if qr_path:
                pdf.image(qr_path, 65, 58, 80, 80)

            y = 145
            pdf.set_font('DejaVu', '', 9)
            pdf.set_text_color(80, 80, 80)
            if area:
                pdf.set_xy(10, y); pdf.cell(190, 5, f"Area: {area}", align='C'); y += 7
            if fab or mod:
                pdf.set_xy(10, y); pdf.cell(190, 5, f"{fab} {mod}".strip(), align='C'); y += 7

            pdf.set_font('DejaVu', 'I', 8)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(10, y + 5)
            pdf.cell(190, 5, 'Aponte a camera para conhecer este equipamento', align='C')

            pdf.set_y(-15)
            pdf.set_font('DejaVu', '', 6.5)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(190, 4, 'Monitorado pelo MAINTRIX Enterprise', align='C')

        if qr_path:
            try: os.remove(qr_path)
            except Exception: pass

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


def generate_qr_batch_pdf(ativos, empresa="MAINTRIX", modelo="etiqueta", layout="6_per_page"):
    """Generate batch QR labels. Returns BytesIO."""
    from io import BytesIO
    import qrcode
    import tempfile
    from routes.assets import build_public_equipment_url

    cols_rows = {"6_per_page": (2, 3), "8_per_page": (2, 4), "12_per_page": (3, 4)}
    cols, rows = cols_rows.get(layout, (2, 3))
    per_page = cols * rows

    pdf = FPDF('P', 'mm', 'A4')
    register_unicode_fonts(pdf)

    margin_x, margin_y = 8, 10
    usable_w = 210 - 2 * margin_x
    usable_h = 280 - 2 * margin_y
    cell_w = usable_w / cols
    cell_h = usable_h / rows
    qr_size = min(cell_w * 0.55, cell_h * 0.45)

    for i, ativo in enumerate(ativos):
        if i % per_page == 0:
            pdf.add_page()

        pos = i % per_page
        col = pos % cols
        row = pos // cols
        x = margin_x + col * cell_w
        y = margin_y + row * cell_h

        tag = _safe(ativo.get('tag', ''), 20)
        nome = _safe(ativo.get('nome', ''), 25)
        # URL recalculada via build_public_equipment_url — nunca confia no campo salvo
        full_url = build_public_equipment_url(ativo)

        # Draw cell border
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x, y, cell_w, cell_h)

        # TAG
        pdf.set_font('DejaVu', 'B', 8 if cols >= 3 else 10)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(x + 2, y + 2)
        pdf.cell(cell_w - 4, 5, tag, align='C')

        # Nome
        pdf.set_font('DejaVu', '', 6 if cols >= 3 else 7)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(x + 2, y + 8)
        pdf.cell(cell_w - 4, 4, nome, align='C')

        # QR Code
        qr_path = None
        if full_url:
            try:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
                qr.add_data(full_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_path = os.path.join(tempfile.gettempdir(), f"qrbatch_{uuid.uuid4().hex[:6]}.png")
                img.save(qr_path)
                qr_x = x + (cell_w - qr_size) / 2
                qr_y = y + 14
                pdf.image(qr_path, qr_x, qr_y, qr_size, qr_size)
            except Exception:
                pass

        # Footer text
        pdf.set_font('DejaVu', '', 5)
        pdf.set_text_color(148, 163, 184)
        pdf.set_xy(x + 2, y + cell_h - 6)
        pdf.cell(cell_w - 4, 4, 'Aponte a camera', align='C')

        if qr_path:
            try: os.remove(qr_path)
            except Exception: pass

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf
