"""
Iteration 35 - Sobressalentes Export (Excel + PDF), Edit, Delete, Audit & RBAC re-verification.

Covers review_request items:
- GET /api/export/sobressalentes?format=excel returns 200, xlsx content, 10+ rows
- GET /api/export/sobressalentes?format=pdf returns 200, PDF content, >1000 bytes, %PDF- prefix
- Excel headers correct
- PUT /api/sobressalentes/{id} (edit) returns 200
- DELETE /api/sobressalentes/{id} returns 200
- Audit logs record edit + delete
- Tecnico gets 403 on PUT/DELETE
"""
import io
import os
import time
import requests
import pytest
import openpyxl

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
TECNICO = {"email": "tecnico@manutrix.com", "password": "tecnico123"}

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in {data}"
    return token


@pytest.fixture(scope="module")
def admin_h():
    return {"Authorization": f"Bearer {_login(ADMIN)}"}


@pytest.fixture(scope="module")
def tec_h():
    return {"Authorization": f"Bearer {_login(TECNICO)}"}


# ---------- Export Excel ----------
class TestExportExcel:
    def test_excel_status_and_content_type(self, admin_h):
        r = requests.get(f"{API}/export/sobressalentes", params={"format": "excel"}, headers=admin_h, timeout=30)
        assert r.status_code == 200, f"excel export status {r.status_code}: {r.text[:200]}"
        ctype = r.headers.get("content-type", "")
        assert EXCEL_MIME in ctype or "spreadsheetml" in ctype, f"unexpected content-type: {ctype}"
        # Sanity: bytes look like a zip (xlsx is zip)
        assert r.content[:2] == b"PK", "xlsx should start with PK zip magic"
        assert len(r.content) > 1000, f"excel suspiciously small: {len(r.content)} bytes"

    def test_excel_headers_and_row_count(self, admin_h):
        r = requests.get(f"{API}/export/sobressalentes", params={"format": "excel"}, headers=admin_h, timeout=30)
        assert r.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert len(rows) >= 1, "no rows in worksheet"
        header = list(rows[0])
        expected = ["Código", "Descrição", "Modelo", "Fabricante", "Série", "Status", "Localização", "Custo"]
        assert header == expected, f"headers mismatch.\n got={header}\nexp={expected}"
        data_rows = rows[1:]
        # Database should have 10+ spares per problem statement
        assert len(data_rows) >= 10, f"expected >=10 data rows, got {len(data_rows)}"


# ---------- Export PDF ----------
class TestExportPDF:
    def test_pdf_status_and_content_type(self, admin_h):
        r = requests.get(f"{API}/export/sobressalentes", params={"format": "pdf"}, headers=admin_h, timeout=30)
        assert r.status_code == 200, f"pdf export status {r.status_code}: {r.text[:200]}"
        ctype = r.headers.get("content-type", "")
        assert "application/pdf" in ctype, f"unexpected content-type: {ctype}"

    def test_pdf_magic_and_size(self, admin_h):
        r = requests.get(f"{API}/export/sobressalentes", params={"format": "pdf"}, headers=admin_h, timeout=30)
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-", f"PDF magic missing: {r.content[:20]!r}"
        assert len(r.content) > 1000, f"pdf suspiciously small: {len(r.content)} bytes"


# ---------- Edit / Delete re-verification ----------
class TestEditDelete:
    spare_id = None

    def test_create_for_edit_delete(self, admin_h):
        payload = {
            "descricao": "TEST_SPARE_iter35_edit",
            "fabricante": "SKF",
            "modelo": "6205-2RS",
            "localizacao": "Almox A1",
            "status": "estoque",
            "custo": 49.90,
        }
        r = requests.post(f"{API}/sobressalentes", json=payload, headers=admin_h, timeout=15)
        assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text}"
        sid = r.json().get("id")
        assert sid
        TestEditDelete.spare_id = sid

    def test_edit_spare(self, admin_h):
        sid = TestEditDelete.spare_id
        assert sid, "create test must run first"
        payload = {
            "descricao": "TEST_SPARE_iter35_edit_UPDATED",
            "fabricante": "SKF",
            "modelo": "6205-2RS",
            "localizacao": "Almox A2",
            "status": "estoque",
            "custo": 79.90,
        }
        r = requests.put(f"{API}/sobressalentes/{sid}", json=payload, headers=admin_h, timeout=15)
        assert r.status_code == 200, f"edit failed: {r.status_code} {r.text}"
        # Verify persisted
        r2 = requests.get(f"{API}/sobressalentes", headers=admin_h, timeout=15)
        match = next((s for s in r2.json() if s.get("id") == sid), None)
        assert match, "spare missing after update"
        assert match["descricao"] == payload["descricao"]
        assert match["localizacao"] == "Almox A2"
        assert abs(float(match["custo"]) - 79.90) < 0.001

    def test_delete_spare(self, admin_h):
        sid = TestEditDelete.spare_id
        assert sid
        r = requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)
        assert r.status_code in (200, 204), f"delete failed: {r.status_code} {r.text}"
        # Verify gone
        r2 = requests.get(f"{API}/sobressalentes", headers=admin_h, timeout=15)
        ids = [s.get("id") for s in r2.json()]
        assert sid not in ids


# ---------- Audit Logs ----------
class TestAudit:
    def test_audit_logs_for_edit_and_delete(self, admin_h):
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_AUDIT_iter35", "status": "estoque"}, headers=admin_h, timeout=15)
        assert c.status_code in (200, 201), c.text
        sid = c.json().get("id")
        assert sid

        u = requests.put(f"{API}/sobressalentes/{sid}", json={"descricao": "TEST_AUDIT_iter35_upd", "status": "estoque"}, headers=admin_h, timeout=15)
        assert u.status_code == 200, u.text

        d = requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)
        assert d.status_code in (200, 204), d.text

        time.sleep(1.0)
        r = requests.get(f"{API}/admin/audit-logs", headers=admin_h, params={"limit": 200}, timeout=15)
        assert r.status_code == 200, r.text
        logs = r.json()
        if isinstance(logs, dict):
            logs = logs.get("items") or logs.get("data") or logs.get("logs") or []
        spare_logs = [l for l in logs if l.get("entity_type") in ("sobressalentes", "sobressalente")]
        upd = [l for l in spare_logs if l.get("action") in ("update", "updated") and str(l.get("entity_id")) == str(sid)]
        dele = [l for l in spare_logs if l.get("action") in ("delete", "deleted") and str(l.get("entity_id")) == str(sid)]
        assert upd, f"No update audit log for {sid}; sample={spare_logs[:3]}"
        assert dele, f"No delete audit log for {sid}; sample={spare_logs[:3]}"


# ---------- RBAC: Tecnico forbidden write ----------
class TestTecnicoForbidden:
    def test_tecnico_put_forbidden(self, admin_h, tec_h):
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_RBAC_iter35_put", "status": "estoque"}, headers=admin_h, timeout=15)
        sid = c.json().get("id")
        try:
            r = requests.put(f"{API}/sobressalentes/{sid}", json={"descricao": "hack", "status": "estoque"}, headers=tec_h, timeout=15)
            assert r.status_code == 403, f"tecnico PUT should be 403 got {r.status_code}: {r.text}"
        finally:
            requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)

    def test_tecnico_delete_forbidden(self, admin_h, tec_h):
        c = requests.post(f"{API}/sobressalentes", json={"descricao": "TEST_RBAC_iter35_del", "status": "estoque"}, headers=admin_h, timeout=15)
        sid = c.json().get("id")
        try:
            r = requests.delete(f"{API}/sobressalentes/{sid}", headers=tec_h, timeout=15)
            assert r.status_code == 403, f"tecnico DELETE should be 403 got {r.status_code}: {r.text}"
        finally:
            requests.delete(f"{API}/sobressalentes/{sid}", headers=admin_h, timeout=15)
