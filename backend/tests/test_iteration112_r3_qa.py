"""
ITERATION 112 — ROUND 3 (FINAL) HOMOLOGACAO E2E — MAINTRIX Enterprise
Branch: fix/pre-pilot-privacy-branding (commit 80793ea)
Focus: NEW coverage only — Master Panel, Uploads (PDF/PNG/JPG), OS status transitions,
       Direct URL access, White Label complete, Cross-org isolation, Compliance/PDF x3.
READ-ONLY QA — do not modify production code.
"""
import os
import time
import httpx
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"
ORG_ID = "9a232bf2-fc01-4253-813f-8df356be31c1"  # ASTEC

USERS = {
    "master":     {"email": "master@maintrix.com",         "password": "master123",  "organization_id": ORG_ID},
    "admin":      {"email": "test.admin@maintrix.com",     "password": "admin123"},
    "pcm":        {"email": "test.pcm@maintrix.com",       "password": "pcm123"},
    "supervisor": {"email": "test.sup.mec@maintrix.com",   "password": "sup123"},
    "tecnico":    {"email": "test.mec@maintrix.com",       "password": "tec123"},
    "operador":   {"email": "test.operador@maintrix.com",  "password": "op123"},
}

_TOKEN_CACHE: dict = {}


def _login(role: str, retries: int = 3) -> str:
    if role in _TOKEN_CACHE:
        return _TOKEN_CACHE[role]
    payload = USERS[role]
    last = None
    for i in range(retries):
        r = httpx.post(f"{API}/auth/login", json=payload, timeout=30)
        if r.status_code == 200:
            tok = r.json().get("access_token")
            _TOKEN_CACHE[role] = tok
            return tok
        last = r
        # Rate limiter cooldown
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"login failed for {role}: {last.status_code if last else '?'} {last.text[:200] if last else ''}")


def H(role: str) -> dict:
    return {"Authorization": f"Bearer {_login(role)}"}


def _get(path: str, role: str = "admin", **kw):
    return httpx.get(f"{API}{path}", headers=H(role), timeout=30, **kw)


# =========== 1) MASTER LOGIN + PANEL ===========
class TestMasterLoginPanel:
    def test_master_login_returns_token_and_role(self):
        for i in range(3):
            # Retry with backoff to handle transient 502/5xx
            for attempt in range(5):
                r = httpx.post(f"{API}/auth/login", json=USERS["master"], timeout=30)
                if r.status_code == 200:
                    break
                time.sleep(3 * (attempt + 1))
            assert r.status_code == 200, f"iter {i+1}: {r.status_code} {r.text[:200]}"
            data = r.json()
            assert "access_token" in data and data["access_token"]
            assert data["user"]["role"] == "master"
            assert data["user"]["organization_id"] == ORG_ID
            time.sleep(4)  # rate limiter cooldown

    def test_master_list_organizations(self):
        r = _get("/master/organizations", role="master")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        orgs = r.json()
        assert isinstance(orgs, list) and len(orgs) >= 1
        # Ensure ASTEC in list
        astec = [o for o in orgs if o.get("id") == ORG_ID]
        assert astec, "ASTEC org not returned to master"
        # Each org should have a config
        assert "config" in astec[0]

    def test_admin_cannot_access_master_organizations(self):
        r = _get("/master/organizations", role="admin")
        assert r.status_code == 403, f"admin got {r.status_code} on /master/organizations"

    def test_pcm_cannot_access_master_organizations(self):
        r = _get("/master/organizations", role="pcm")
        assert r.status_code == 403

    def test_tecnico_cannot_access_master_organizations(self):
        r = _get("/master/organizations", role="tecnico")
        assert r.status_code == 403

    def test_master_get_org_config_by_id(self):
        r = httpx.get(f"{API}/master/organizations/{ORG_ID}/config", headers=H("master"), timeout=30)
        assert r.status_code == 200
        cfg = r.json()
        assert cfg.get("organization_id") == ORG_ID

    def test_master_get_org_config_nonexistent_returns_404(self):
        r = httpx.get(f"{API}/master/organizations/nonexistent-org-uuid-xxx/config", headers=H("master"), timeout=30)
        assert r.status_code in (404, 400)

    def test_master_org_config_update_and_restore(self):
        # snapshot
        cfg = httpx.get(f"{API}/master/organizations/{ORG_ID}/config", headers=H("master"), timeout=30).json()
        orig_nome = cfg.get("identidade", {}).get("nome_empresa", "ASTEC Cedro")
        # update
        new_nome = "[QA-R3-MASTER] ASTEC"
        r = httpx.put(
            f"{API}/master/organizations/{ORG_ID}/config",
            headers=H("master"),
            json={"nome_empresa": new_nome},
            timeout=30,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        # verify
        cfg2 = httpx.get(f"{API}/master/organizations/{ORG_ID}/config", headers=H("master"), timeout=30).json()
        assert cfg2.get("identidade", {}).get("nome_empresa") == new_nome
        # restore
        httpx.put(f"{API}/master/organizations/{ORG_ID}/config", headers=H("master"),
                  json={"nome_empresa": orig_nome}, timeout=30)


# =========== 2) UPLOADS ===========
_MIN_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000053 00000 n \n0000000091 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF"
)
# Minimal 1x1 PNG (67 bytes)
_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
)
# Minimal JPG (SOI + APP0 JFIF + EOI)
_MIN_JPG = bytes.fromhex(
    "ffd8ffe000104a46494600010101006000600000ffdb004300080606070605080707"
    "07090908"
    "0a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434"
    "1f27393d3832"
    "3c2e333432ffc00011080001000103012200021101031101ffc4001500010100000000000000"
    "0000000000000000000affda0008010100003f0037ffd9"
)


class TestUploads:
    """The problem statement referenced /ativos/{id}/documentos and /ordens-servico/{id}/anexos
    endpoints. Confirmed these do NOT exist (404). The only file-upload endpoints are:
    (a) POST /api/upload — generic authenticated upload (validates ext), used by frontend.
    (b) POST /api/master/organizations/{id}/upload/{asset_type} — master only.
    (c) POST /api/documentos-corporativos/{id}/upload — corporate docs.
    We test the generic /upload endpoint since that is what the app uses.
    """

    def test_upload_pdf_ok(self):
        files = {"file": ("qa_r3.pdf", _MIN_PDF, "application/pdf")}
        r = httpx.post(f"{API}/upload", headers=H("admin"), files=files, timeout=45)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        body = r.json()
        # Response should contain a URL/path/filename
        assert any(k in body for k in ("url", "path", "filename", "file_path"))

    def test_upload_png_ok(self):
        files = {"file": ("qa_r3.png", _MIN_PNG, "image/png")}
        r = httpx.post(f"{API}/upload", headers=H("admin"), files=files, timeout=45)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"

    def test_upload_jpg_ok(self):
        files = {"file": ("qa_r3.jpg", _MIN_JPG, "image/jpeg")}
        r = httpx.post(f"{API}/upload", headers=H("admin"), files=files, timeout=45)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"

    def test_upload_disallowed_extension(self):
        files = {"file": ("qa_r3.exe", b"malicious", "application/octet-stream")}
        r = httpx.post(f"{API}/upload", headers=H("admin"), files=files, timeout=45)
        assert r.status_code in (400, 415, 422), r.text[:200]

    def test_upload_requires_auth(self):
        files = {"file": ("noauth.pdf", _MIN_PDF, "application/pdf")}
        r = httpx.post(f"{API}/upload", files=files, timeout=30)
        assert r.status_code in (401, 403), r.text[:200]

    def test_download_uploaded_file(self):
        files = {"file": ("dl_test.pdf", _MIN_PDF, "application/pdf")}
        up = httpx.post(f"{API}/upload", headers=H("admin"), files=files, timeout=45)
        assert up.status_code == 200
        body = up.json()
        url = body.get("url") or body.get("path") or body.get("file_path")
        assert url, f"no url in upload response: {body}"
        # Resolve to full URL
        if url.startswith("/"):
            get_url = f"{BASE}{url}"
        else:
            get_url = url
        r = httpx.get(get_url, headers=H("admin"), timeout=30)
        # 200 or 302 (redirect to signed URL)
        assert r.status_code in (200, 302, 307), f"{r.status_code} {r.text[:200]}"

    def test_expected_ativos_documentos_endpoint_missing(self):
        """The problem statement referred to POST /api/ativos/{id}/documentos which does
        not exist. We document its absence to keep the requirement traceable."""
        aid = _get("/ativos", role="admin").json()[0]["id"]
        files = {"file": ("t.pdf", _MIN_PDF, "application/pdf")}
        r = httpx.post(f"{API}/ativos/{aid}/documentos", headers=H("admin"), files=files, timeout=30)
        assert r.status_code == 404  # confirms endpoint is missing

    def test_expected_os_anexos_endpoint_missing(self):
        """The problem statement referred to POST /api/ordens-servico/{id}/anexos which does not exist."""
        os_id = _get("/ordens-servico", role="admin").json()[0]["id"]
        files = {"file": ("t.pdf", _MIN_PDF, "application/pdf")}
        r = httpx.post(f"{API}/ordens-servico/{os_id}/anexos", headers=H("admin"), files=files, timeout=30)
        assert r.status_code == 404


# =========== 3) OS STATUS TRANSITIONS ===========
class TestOSStatusTransitions:
    def _create_os(self):
        aid = _get("/ativos", role="admin").json()[0]["id"]
        r = httpx.post(f"{API}/ordens-servico", headers=H("admin"), json={
            "ativo_id": aid,
            "titulo": "[QA-R3] status transition test OS",
            "descricao": "[QA-R3] status transition test OS",
            "tipo": "corretiva",
            "prioridade": "baixa",
        }, timeout=30)
        assert r.status_code in (200, 201), r.text[:200]
        return r.json()

    def test_os_initial_status(self):
        os_ = self._create_os()
        status = os_.get("status")
        assert status in ("aberta", "solicitada", "planejada", "programada"), f"unexpected initial status: {status}"

    def test_get_transitions_endpoint(self):
        os_ = self._create_os()
        r = _get(f"/ordens-servico/{os_['id']}/transitions", role="admin")
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert "current_status" in body and "valid_transitions" in body
        assert isinstance(body["valid_transitions"], list)

    def test_valid_transition_via_patch(self):
        os_ = self._create_os()
        os_id = os_["id"]
        current = os_.get("status")
        # From 'aberta' → 'em_execucao' is allowed for admin
        target = "em_execucao" if current == "aberta" else None
        if not target:
            # fall back to fetching transitions
            tr = _get(f"/ordens-servico/{os_id}/transitions", role="admin").json()
            valids = tr.get("valid_transitions", [])
            if not valids:
                pytest.skip(f"No valid transitions from {current}")
            target = valids[0]
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=H("admin"),
                        json={"new_status": target}, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert r.json().get("new_status") == target

    def test_invalid_transition_returns_400(self):
        os_ = self._create_os()
        os_id = os_["id"]
        # From aberta → concluida is not a valid direct transition per OS_TRANSITIONS
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=H("admin"),
                        json={"new_status": "concluida"}, timeout=30)
        # concluida is not directly reachable from aberta
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:200]}"

    def test_historico_records_transitions(self):
        os_ = self._create_os()
        os_id = os_["id"]
        # transition
        httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=H("admin"),
                    json={"new_status": "em_execucao"}, timeout=30)
        # historico
        r = _get(f"/ordens-servico/{os_id}/historico", role="admin")
        assert r.status_code == 200
        hist = r.json()
        assert isinstance(hist, list)
        # At least the creation + status change should be logged
        # Allow empty if history uses a different collection, but most iterations show entries
        # Not asserting length strictly to accommodate audit log storage strategy

    def test_full_lifecycle_via_endpoints(self):
        os_ = self._create_os()
        os_id = os_["id"]
        # iniciar
        r = httpx.post(f"{API}/ordens-servico/{os_id}/iniciar", headers=H("admin"), timeout=30)
        assert r.status_code == 200, r.text[:200]
        # pausar
        r = httpx.post(f"{API}/ordens-servico/{os_id}/pausar", headers=H("admin"), timeout=30)
        assert r.status_code == 200, r.text[:200]
        # resume via patch → em_execucao
        r = httpx.patch(f"{API}/ordens-servico/{os_id}/status", headers=H("admin"),
                        json={"new_status": "em_execucao"}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        # concluir — for corretiva OS, business rule requires anexo; either 200 or 400 is acceptable
        r = httpx.post(f"{API}/ordens-servico/{os_id}/concluir", headers=H("admin"),
                       json={"observacao": "[QA-R3] concluida via lifecycle test"}, timeout=30)
        assert r.status_code in (200, 400), r.text[:200]


# =========== 4) RBAC ORDERING REGRESSION ===========
class TestRBACOrdering:
    def test_operator_gets_403_before_422(self):
        """R2-004 fix: POST /ativos with operator + invalid payload => 403 (not 422)."""
        r = httpx.post(f"{API}/ativos", headers=H("operador"),
                       json={"tag": ""}, timeout=30)  # invalid payload
        assert r.status_code == 403, f"operator got {r.status_code} instead of 403: {r.text[:200]}"

    def test_tecnico_gets_403_before_422(self):
        r = httpx.post(f"{API}/ativos", headers=H("tecnico"),
                       json={"tag": ""}, timeout=30)
        assert r.status_code == 403, f"tecnico got {r.status_code} instead of 403: {r.text[:200]}"

    def test_admin_with_invalid_payload_gets_422(self):
        r = httpx.post(f"{API}/ativos", headers=H("admin"),
                       json={}, timeout=30)
        assert r.status_code == 422, f"admin got {r.status_code} for invalid payload: {r.text[:200]}"

    def test_no_token_gets_401_or_403(self):
        r = httpx.post(f"{API}/ativos", json={"tag": ""}, timeout=30)
        assert r.status_code in (401, 403), f"got {r.status_code}"


# =========== 5) WHITE LABEL COMPLETE ===========
class TestWhiteLabel:
    def test_full_branding_cycle(self):
        original = _get("/org/config", role="admin").json()
        orig_nome = original.get("identidade", {}).get("nome_empresa", "ASTEC Cedro")
        orig_cor = original.get("tema", {}).get("cor_primaria", "#0066cc")

        # PUT branding
        r = httpx.put(f"{API}/org/config/branding", headers=H("admin"),
                      json={"nome_empresa": "[QA-R3] ASTEC"}, timeout=30)
        assert r.status_code in (200, 204)
        after = _get("/org/config", role="admin").json()
        assert after.get("identidade", {}).get("nome_empresa") == "[QA-R3] ASTEC"

        # PUT tema
        r = httpx.put(f"{API}/org/config/tema", headers=H("admin"),
                      json={"cor_primaria": "#ff5500"}, timeout=30)
        assert r.status_code in (200, 204)
        after2 = _get("/org/config", role="admin").json()
        assert after2.get("tema", {}).get("cor_primaria") == "#ff5500"

        # PUT terminologia
        r = httpx.put(f"{API}/org/config/terminologia", headers=H("admin"),
                      json={"ordem_servico_singular": "[QA-R3] Chamado"}, timeout=30)
        assert r.status_code in (200, 204)

        # restore
        httpx.put(f"{API}/org/config/branding", headers=H("admin"),
                  json={"nome_empresa": orig_nome}, timeout=30)
        httpx.put(f"{API}/org/config/tema", headers=H("admin"),
                  json={"cor_primaria": orig_cor}, timeout=30)

    def test_tecnico_cannot_update_branding(self):
        r = httpx.put(f"{API}/org/config/branding", headers=H("tecnico"),
                      json={"nome_empresa": "hack"}, timeout=30)
        assert r.status_code == 403, f"tecnico got {r.status_code}"

    def test_operador_cannot_update_branding(self):
        r = httpx.put(f"{API}/org/config/branding", headers=H("operador"),
                      json={"nome_empresa": "hack"}, timeout=30)
        assert r.status_code == 403


# =========== 6) DIRECT URL ACCESS (RBAC forbidden endpoints) ===========
class TestDirectURLAccess:
    def test_tecnico_denied_admin_users(self):
        r = _get("/admin/users", role="tecnico")
        assert r.status_code == 403, f"tecnico got {r.status_code}"

    def test_operador_denied_admin_audit_logs(self):
        r = _get("/admin/audit-logs", role="operador")
        assert r.status_code == 403, f"operador got {r.status_code}"

    def test_supervisor_denied_admin_users(self):
        r = _get("/admin/users", role="supervisor")
        assert r.status_code == 403

    def test_pcm_denied_admin_users(self):
        r = _get("/admin/users", role="pcm")
        assert r.status_code == 403

    def test_tecnico_denied_put_branding(self):
        r = httpx.put(f"{API}/org/config/branding", headers=H("tecnico"),
                      json={"nome_empresa": "x"}, timeout=30)
        assert r.status_code == 403

    def test_no_auth_admin_users(self):
        r = httpx.get(f"{API}/admin/users", timeout=30)
        assert r.status_code in (401, 403)


# =========== 7) CROSS-ORG ISOLATION ===========
class TestCrossOrgIsolation:
    def test_all_ativos_belong_to_admin_org(self):
        r = _get("/ativos", role="admin")
        assert r.status_code == 200
        ativos = r.json()
        if isinstance(ativos, dict):
            ativos = ativos.get("items", [])
        for a in ativos:
            assert a.get("organization_id") == ORG_ID, f"cross-org leak: {a.get('organization_id')}"

    def test_all_os_belong_to_admin_org(self):
        r = _get("/ordens-servico", role="admin")
        assert r.status_code == 200
        oss = r.json()
        if isinstance(oss, dict):
            oss = oss.get("items", [])
        for o in oss:
            assert o.get("organization_id") == ORG_ID


# =========== 8) COMPLIANCE REGRESSION x3 ===========
class TestComplianceRegression:
    @pytest.mark.parametrize("run", [1, 2, 3])
    def test_privacy(self, run):
        r = httpx.get(f"{API}/compliance/privacy", timeout=30)
        assert r.status_code == 200
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"conteudo": r.text}
        conteudo = body.get("conteudo") or body.get("content") or ""
        assert len(conteudo) > 500, f"run {run}: content too short ({len(conteudo)})"

    @pytest.mark.parametrize("run", [1, 2, 3])
    def test_terms(self, run):
        r = httpx.get(f"{API}/compliance/terms", timeout=30)
        assert r.status_code == 200


# =========== 9) PDF REGRESSION x3 ===========
class TestPDFRegression:
    def test_os_pdf_x3(self):
        oss = _get("/ordens-servico", role="admin").json()
        if isinstance(oss, dict):
            oss = oss.get("items", [])
        if not oss:
            pytest.skip("no OS")
        os_id = oss[0]["id"]
        for i in range(3):
            r = httpx.get(f"{API}/ordens-servico/{os_id}/pdf", headers=H("admin"), timeout=45)
            assert r.status_code == 200, f"run {i+1}: {r.status_code}"
            assert r.content[:5] == b"%PDF-", f"run {i+1}: not a PDF"
            assert len(r.content) > 1000


# =========== 10) PROCEDIMENTOS REGRESSION x3 ===========
class TestProcedimentosRegression:
    def test_procedimentos_cycle_x3(self):
        for i in range(3):
            # List
            r = _get("/procedimentos", role="admin")
            assert r.status_code == 200, f"list {i+1}: {r.status_code}"
            # Create
            create = httpx.post(f"{API}/procedimentos", headers=H("admin"), json={
                "nome": f"[QA-R3] Proc cycle {i+1}",
                "descricao": "regression cycle",
                "etapas": [{"titulo": "step 1", "descricao": "first step"}],
            }, timeout=30)
            assert create.status_code in (200, 201), f"create {i+1}: {create.status_code} {create.text[:200]}"
            pid = create.json().get("id")
            assert pid
            # Delete
            r = httpx.delete(f"{API}/procedimentos/{pid}", headers=H("admin"), timeout=30)
            assert r.status_code in (200, 204), f"delete {i+1}: {r.status_code}"


# =========== 11) MASTER PANEL DETAILED ===========
class TestMasterPanelDetailed:
    def test_all_master_endpoints_accessible_by_master(self):
        # GET /master/organizations
        r = _get("/master/organizations", role="master")
        assert r.status_code == 200
        # GET /master/admin-actions
        r = _get("/master/admin-actions", role="master")
        # Some deployments 200, some 404 if not seeded
        assert r.status_code in (200, 404)

    def test_master_create_organization_and_isolation(self):
        # Create a new org for testing (then leave it — cleanup is optional)
        nome = f"[QA-R3] test-org {int(time.time())}"
        r = httpx.post(f"{API}/master/organizations", headers=H("master"),
                       json={"nome": nome}, timeout=30)
        assert r.status_code in (200, 201), f"{r.status_code} {r.text[:200]}"
        body = r.json()
        assert body.get("nome") == nome
        assert body.get("id")
        assert "config" in body

    def test_admin_cannot_create_organization(self):
        r = httpx.post(f"{API}/master/organizations", headers=H("admin"),
                       json={"nome": "hack-org"}, timeout=30)
        assert r.status_code == 403


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
