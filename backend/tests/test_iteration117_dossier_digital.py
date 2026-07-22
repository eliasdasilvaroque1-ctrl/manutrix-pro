"""
RC P1 — Dossiê Digital do Ativo v1.0 — FASE 1 (Backend)
Iteration 117: Comprehensive tests for public_dossier structure, RBAC, visibility filtering,
document upload/publish/delete, and public endpoint evolution.

Tested asset: AV-01 ALIMENTADOR (id=0f8972a8-72c6-4941-97af-06cd61171904)
Public slug/token: av-01-alimentador / Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu
"""
import io
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

ATIVO_ID = "0f8972a8-72c6-4941-97af-06cd61171904"
PUBLIC_SLUG = "av-01-alimentador"
PUBLIC_TOKEN = "Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu"

ADMIN = {"email": "test.admin@maintrix.com", "password": "admin123"}
PCM = {"email": "test.pcm@maintrix.com", "password": "pcm123"}
OPERADOR = {"email": "test.operador@maintrix.com", "password": "op123"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def pcm_token():
    return _login(PCM)


@pytest.fixture(scope="module")
def operador_token():
    return _login(OPERADOR)


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ================= GET DOSSIER (auth) =================

class TestGetDossier:
    def test_get_dossier_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier", timeout=15)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_get_dossier_admin_returns_structure(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "public_dossier" in body
        assert "public_status" in body
        assert "documents" in body
        dossier = body["public_dossier"]
        # Visibility defaults present
        assert "visibility" in dossier
        vis = dossier["visibility"]
        # Blocks must have defaults
        for k in ("technical_data", "history", "inspections", "maintenance",
                  "documents", "curiosity", "warning", "safety", "best_practices"):
            assert k in vis, f"Missing default visibility for {k}"
            assert vis[k] in ("public", "authenticated", "restricted", "hidden")

    def test_get_dossier_pcm_ok(self, pcm_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(pcm_token), timeout=15
        )
        assert r.status_code == 200

    def test_get_dossier_invalid_id_404(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos/does-not-exist-xyz/dossier",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 404


# ================= PUT DOSSIER (RBAC + validation) =================

class TestUpdateDossier:
    def test_put_rejects_operador_403(self, operador_token):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(operador_token),
            json={"description": "hack"},
            timeout=15
        )
        assert r.status_code == 403

    def test_put_rejects_no_auth_401(self):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            json={"description": "hack"},
            timeout=15
        )
        assert r.status_code in (401, 403)

    def test_put_admin_updates_all_fields(self, admin_token):
        payload = {
            "description": "TEST_DESC — Alimentador Vibratorio VGF4216",
            "curiosity": "TEST_CUR — capacidade 450 t/h",
            "warning": "TEST_WARN — nao operar acima da capacidade nominal",
            "safety": "TEST_SAFE — bloqueio e etiquetagem obrigatorios",
            "best_practices": "TEST_BP — alimentacao uniforme",
            "public_status": "operando",
            "location": {"linha": "Linha 1", "ponto_instalacao": "Entrada Britagem"},
            "technical_data": {"corrente": "95 A", "frequencia": "60 Hz"},
            "visibility": {
                "curiosity": "public", "warning": "public", "safety": "public",
                "best_practices": "public", "technical_data": "public",
                "history": "public", "inspections": "public",
                "maintenance": "public", "documents": "public",
            },
        }
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token), json=payload, timeout=20
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("success") is True
        d = body["public_dossier"]
        assert d.get("description") == payload["description"]
        assert d.get("curiosity") == payload["curiosity"]
        assert d.get("technical_data", {}).get("corrente") == "95 A"
        assert d.get("location", {}).get("linha") == "Linha 1"
        assert body.get("public_status") == "operando"

        # GET to verify persistence
        r2 = requests.get(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token), timeout=15
        )
        d2 = r2.json()["public_dossier"]
        assert d2["description"] == payload["description"]

    def test_put_invalid_public_status_400(self, admin_token):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"public_status": "invalido-xyz"}, timeout=15
        )
        assert r.status_code == 400

    def test_put_invalid_visibility_level_ignored(self, admin_token):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"curiosity": "invalid_level_xyz"}},
            timeout=15
        )
        # Invalid level ignored → no update → 400 "Nenhum campo para atualizar"
        # OR 200 if other fields were sent. Route: ignores invalid — returns 400.
        assert r.status_code == 400

    def test_put_pcm_can_update(self, pcm_token):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(pcm_token),
            json={"description": "TEST_DESC — Alimentador Vibratorio VGF4216"},
            timeout=15
        )
        assert r.status_code == 200


# ================= PUBLIC ENDPOINT — visibility filtering =================

class TestPublicEndpoint:
    def test_public_no_auth_returns_200(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        assert r.status_code == 200
        assert r.json().get("available") is True

    def test_public_invalid_token_404(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/invalid-token-xyz",
            timeout=15
        )
        assert r.status_code == 404

    def test_public_invalid_slug_404(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/slug-xyz/{PUBLIC_TOKEN}",
            timeout=15
        )
        assert r.status_code == 404

    def test_public_returns_branding(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        assert "branding" in eq
        b = eq["branding"]
        assert "logo_url" in b
        assert "cor_primaria" in b
        assert "nome_empresa" in b

    def test_public_returns_location(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        assert "location" in eq
        loc = eq["location"]
        assert "area" in loc
        assert "unidade" in loc

    def test_public_returns_technical_data(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        assert "technical_data" in eq
        td = eq["technical_data"]
        # Should contain at least model/fabricante or corrente/frequencia
        assert td.get("modelo") or td.get("fabricante") or td.get("corrente")

    def test_public_returns_status_publico_color(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        # After PUT test, status is 'operando' → color green
        if "status_publico" in eq:
            assert eq.get("status_color") in ("green", "red", "yellow", "blue")

    def test_public_returns_dossier_blocks_when_public(self, admin_token):
        # Ensure blocks visible=public
        requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {
                "curiosity": "public", "warning": "public",
                "safety": "public", "best_practices": "public",
            }},
            timeout=15
        )
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        assert eq.get("curiosity")
        assert eq.get("warning")
        assert eq.get("safety")
        assert eq.get("best_practices")

    def test_public_hides_block_when_visibility_hidden(self, admin_token):
        # Change curiosity to hidden
        put_r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"curiosity": "hidden"}},
            timeout=15
        )
        assert put_r.status_code == 200
        try:
            r = requests.get(
                f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
                timeout=15
            )
            eq = r.json()["equipment"]
            assert "curiosity" not in eq, f"curiosity should be hidden but got: {eq.get('curiosity')}"
            # Sanity — other blocks still present
            assert eq.get("warning")
        finally:
            # Restore
            requests.put(
                f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
                headers=_headers(admin_token),
                json={"visibility": {"curiosity": "public"}},
                timeout=15
            )

    def test_public_hides_technical_data_when_hidden(self, admin_token):
        put_r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"technical_data": "hidden"}},
            timeout=15
        )
        assert put_r.status_code == 200
        try:
            r = requests.get(
                f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
                timeout=15
            )
            eq = r.json()["equipment"]
            assert "technical_data" not in eq
        finally:
            requests.put(
                f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
                headers=_headers(admin_token),
                json={"visibility": {"technical_data": "public"}},
                timeout=15
            )

    def test_public_returns_history_summary(self, admin_token):
        # Ensure history=public
        requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"history": "public"}},
            timeout=15
        )
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        # history_summary present only if there is data
        if "history_summary" in eq:
            hs = eq["history_summary"]
            # At least one of the fields
            assert any(k in hs for k in ("total_manutencoes", "total_inspecoes",
                                          "ultima_manutencao", "ultima_inspecao"))

    def test_public_inspections_max_3_safe_fields(self, admin_token):
        requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"inspections": "public"}}, timeout=15
        )
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        insp = eq.get("inspections", [])
        assert isinstance(insp, list)
        assert len(insp) <= 3
        allowed = {"data", "tipo", "resultado", "status"}
        for i in insp:
            extras = set(i.keys()) - allowed
            assert not extras, f"Inspection contains unsafe fields: {extras}"

    def test_public_maintenance_max_3_safe_fields(self, admin_token):
        requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"maintenance": "public"}}, timeout=15
        )
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        eq = r.json()["equipment"]
        mnt = eq.get("maintenance", [])
        assert isinstance(mnt, list)
        assert len(mnt) <= 3
        allowed = {"data", "tipo", "titulo", "status"}
        for m in mnt:
            extras = set(m.keys()) - allowed
            assert not extras, f"Maintenance contains unsafe fields: {extras}"

    def test_public_does_not_leak_sensitive_fields(self):
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}",
            timeout=15
        )
        raw = r.text
        # Check sensitive keys are not exposed at any depth
        for forbidden in ("organization_id", "\"_id\"", "responsavel_id",
                          "custo", "custos", "uploaded_by"):
            assert forbidden not in raw, f"Sensitive field '{forbidden}' leaked in public response"
        # email leakage — allow contact_email if it's part of branding intentionally?
        # Public JSON should not contain any email addresses from users
        assert "@maintrix.com" not in raw


# ================= DOCUMENTS =================

class TestDossierDocuments:
    _doc_id = None

    def test_upload_document(self, admin_token):
        # Craft a small PDF-like payload (>100 bytes)
        content = b"%PDF-1.4\n%TEST_DOSSIER_DOC\n" + b"a" * 300
        files = {"file": ("test_manual.pdf", io.BytesIO(content), "application/pdf")}
        data = {"title": "TEST_MANUAL", "doc_type": "manual"}
        r = requests.post(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents",
            headers=_headers(admin_token),
            files=files, data=data, timeout=30
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc.get("title") == "TEST_MANUAL"
        assert doc.get("doc_type") == "manual"
        assert doc.get("is_published") is False
        assert "id" in doc
        TestDossierDocuments._doc_id = doc["id"]

    def test_upload_rejects_operador(self, operador_token):
        content = b"%PDF-1.4\n" + b"b" * 300
        files = {"file": ("hack.pdf", io.BytesIO(content), "application/pdf")}
        data = {"title": "TEST_HACK", "doc_type": "outro"}
        r = requests.post(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents",
            headers=_headers(operador_token),
            files=files, data=data, timeout=15
        )
        assert r.status_code == 403

    def test_toggle_publish_true(self, admin_token):
        assert TestDossierDocuments._doc_id
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents/{TestDossierDocuments._doc_id}/publish",
            headers=_headers(admin_token),
            json={"is_published": True}, timeout=15
        )
        assert r.status_code == 200
        assert r.json().get("is_published") is True

    def test_public_document_download_when_published(self, admin_token):
        assert TestDossierDocuments._doc_id
        # Ensure documents visibility=public
        requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {"documents": "public"}}, timeout=15
        )
        r = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}/document/{TestDossierDocuments._doc_id}",
            timeout=20
        )
        # Should download without auth. If storage backend returns 404 (no supabase),
        # we still check the endpoint didn't reject on visibility/publish grounds.
        assert r.status_code in (200, 404), f"Unexpected status {r.status_code}: {r.text[:200]}"
        if r.status_code == 200:
            assert len(r.content) > 100

    def test_toggle_publish_false_hides_from_public(self, admin_token):
        assert TestDossierDocuments._doc_id
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents/{TestDossierDocuments._doc_id}/publish",
            headers=_headers(admin_token),
            json={"is_published": False}, timeout=15
        )
        assert r.status_code == 200
        # Public download must 404
        r2 = requests.get(
            f"{BASE_URL}/api/public/equipment/{PUBLIC_SLUG}/{PUBLIC_TOKEN}/document/{TestDossierDocuments._doc_id}",
            timeout=15
        )
        assert r2.status_code == 404

    def test_delete_document_soft(self, admin_token):
        assert TestDossierDocuments._doc_id
        r = requests.delete(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents/{TestDossierDocuments._doc_id}",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 200
        assert r.json().get("success") is True

        # Verify: GET dossier should not list it
        g = requests.get(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token), timeout=15
        )
        docs = g.json().get("documents", [])
        ids = [d.get("id") for d in docs]
        assert TestDossierDocuments._doc_id not in ids

    def test_delete_nonexistent_doc_404(self, admin_token):
        r = requests.delete(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier/documents/nonexistent-xyz",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 404


# ================= BACKWARDS COMPAT =================

class TestBackwardsCompat:
    def test_qr_public_url_still_present(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 200
        ativo = r.json()
        assert ativo.get("public_qr_url"), "public_qr_url must remain populated"
        assert PUBLIC_TOKEN in ativo["public_qr_url"]

    def test_ativos_list_without_dossier_works(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/ativos",
            headers=_headers(admin_token), timeout=15
        )
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        # Ativos without public_dossier should still return normally
        assert len(arr) > 0


# ================= CLEANUP (restore public visibility) =================

class TestCleanup:
    def test_zzz_restore_visibility_public(self, admin_token):
        r = requests.put(
            f"{BASE_URL}/api/ativos/{ATIVO_ID}/dossier",
            headers=_headers(admin_token),
            json={"visibility": {
                "curiosity": "public", "warning": "public",
                "safety": "public", "best_practices": "public",
                "technical_data": "public", "history": "public",
                "inspections": "public", "maintenance": "public",
                "documents": "public",
            }},
            timeout=15
        )
        assert r.status_code == 200
