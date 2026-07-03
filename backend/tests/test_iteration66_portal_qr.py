"""FASE 3/4/5 — QR Label + Portal Público + Portal do Técnico

Backend focus: GET /api/public/ativo/{id} enrichment (kpis, ultimas_*, branding, manuais).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
ATIVO_ID = "5af42d90-4654-4067-b67d-92d7e7f6f78d"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Public Portal endpoint ----------

class TestPublicAtivoEndpoint:
    def test_endpoint_reachable(self, session):
        r = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}")
        assert r.status_code == 200, r.text

    def test_returns_ativo_core_fields(self, session):
        r = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}")
        d = r.json()
        assert "ativo" in d
        a = d["ativo"]
        for k in ("id", "tag", "nome", "tipo_equipamento", "status"):
            assert k in a, f"missing ativo.{k}"
        assert a["id"] == ATIVO_ID
        assert a["tag"], "tag should be present"
        assert a["nome"], "nome should be present"

    def test_returns_area(self, session):
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        assert "area" in d
        assert isinstance(d["area"], str)

    def test_returns_kpis_block(self, session):
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        assert "kpis" in d, "kpis block missing"
        kpis = d["kpis"]
        for k in ("total_os", "total_inspecoes", "os_concluidas", "insp_conformes", "disponibilidade"):
            assert k in kpis, f"kpis.{k} missing"
        assert isinstance(kpis["total_os"], int)
        assert isinstance(kpis["disponibilidade"], (int, float))

    def test_returns_ultimas_lists(self, session):
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        for k in ("ultimas_inspecoes", "ultimas_os", "ultimas_manutencoes", "manuais"):
            assert k in d, f"{k} missing"
            assert isinstance(d[k], list), f"{k} should be list"

    def test_returns_branding_block(self, session):
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        assert "branding" in d
        b = d["branding"]
        for k in ("nome_empresa", "cor_primaria", "cor_secundaria", "cor_fundo",
                  "cor_texto", "cor_menu", "mostrar_powered_by"):
            assert k in b, f"branding.{k} missing"
        # logo_url may be None but key must exist
        assert "logo_url" in b
        assert "logo_branca_url" in b

    def test_no_mongo_id_leak(self, session):
        """MongoDB _id must never be exposed."""
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        assert "_id" not in d
        assert "_id" not in d["ativo"]
        for item in d.get("ultimas_os", []):
            assert "_id" not in item
        for item in d.get("ultimas_inspecoes", []):
            assert "_id" not in item
        for item in d.get("manuais", []):
            assert "_id" not in item

    def test_public_no_auth_required(self, session):
        """Endpoint must be reachable with NO Authorization header."""
        s = requests.Session()  # brand new, no cookies/tokens
        r = s.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}")
        assert r.status_code == 200

    def test_invalid_id_returns_404(self, session):
        r = session.get(f"{BASE_URL}/api/public/ativo/invalid-id-does-not-exist")
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text}"

    def test_ultimas_os_limit_5(self, session):
        d = session.get(f"{BASE_URL}/api/public/ativo/{ATIVO_ID}").json()
        assert len(d["ultimas_os"]) <= 5
        assert len(d["ultimas_inspecoes"]) <= 5
        assert len(d["ultimas_manutencoes"]) <= 5


# ---------- Auth for other tests ----------

class TestMasterLogin:
    def test_master_login_works(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": "master@maintrix.com", "password": "master123"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "access_token" in d
        assert d["user"]["role"] == "master"

    def test_ativo_detail_requires_auth(self, session):
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/ativos/{ATIVO_ID}")
        # 401 or 403 both acceptable to signify auth required
        assert r.status_code in (401, 403)
