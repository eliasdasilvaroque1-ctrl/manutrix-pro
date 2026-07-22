"""
RC P1 Dossiê Digital v1.0 — FASE 3
Tests for the public dossier endpoint (no auth) — /api/public/equipment/{slug}/{token}
"""
import os
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")

VALID_SLUG_WITH_DOSSIER = "av-01-alimentador"
VALID_TOKEN_WITH_DOSSIER = "Wb2xZ_y_eeAWO8Q8iLzjQJkH4sa_TuIu"

VALID_SLUG_MINIMAL = "bb-03-bomba-aspersao-patio"
VALID_TOKEN_MINIMAL = "P4wbjMQ3JxqWXFxOWsnYIYBtkOi1ewNf"

INVALID_SLUG = "slug-invalido"
INVALID_TOKEN = "token-invalido"


@pytest.fixture(scope="module")
def av01_data():
    r = requests.get(f"{BASE_URL}/api/public/equipment/{VALID_SLUG_WITH_DOSSIER}/{VALID_TOKEN_WITH_DOSSIER}", timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    return r.json()


@pytest.fixture(scope="module")
def bb03_data():
    r = requests.get(f"{BASE_URL}/api/public/equipment/{VALID_SLUG_MINIMAL}/{VALID_TOKEN_MINIMAL}", timeout=15)
    assert r.status_code == 200
    return r.json()


class TestPublicEndpointAccess:
    """Test that the public endpoint requires NO auth and behaves correctly."""

    def test_valid_qr_returns_200_without_auth(self):
        last_err = None
        for _ in range(3):
            try:
                r = requests.get(f"{BASE_URL}/api/public/equipment/{VALID_SLUG_WITH_DOSSIER}/{VALID_TOKEN_WITH_DOSSIER}", timeout=30)
                assert r.status_code == 200
                body = r.json()
                assert body.get("available") is True
                return
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                last_err = e
        raise last_err

    def test_invalid_qr_returns_404_or_available_false(self):
        r = requests.get(f"{BASE_URL}/api/public/equipment/{INVALID_SLUG}/{INVALID_TOKEN}", timeout=15)
        # Backend returns 404 with detail — this is friendly enough for frontend to handle
        assert r.status_code in (404, 200)
        if r.status_code == 200:
            assert r.json().get("available") is False

    def test_no_auth_header_needed(self):
        # explicitly send no Authorization header
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/public/equipment/{VALID_SLUG_WITH_DOSSIER}/{VALID_TOKEN_WITH_DOSSIER}", timeout=15)
        assert r.status_code == 200


class TestPublicDossierContent:
    """Test that the JSON payload has all the fields the frontend needs."""

    def test_basic_identification_present(self, av01_data):
        eq = av01_data["equipment"]
        assert eq.get("tag") == "AV-01"
        assert eq.get("nome") == "ALIMENTADOR"

    def test_status_publico_and_color(self, av01_data):
        eq = av01_data["equipment"]
        assert eq.get("status_publico") == "Operando"
        assert eq.get("status_color") == "green"

    def test_branding_present(self, av01_data):
        eq = av01_data["equipment"]
        b = eq.get("branding", {})
        assert b.get("nome_empresa") == "ASTEC Cedro"
        assert b.get("logo_url"), "logo_url must be present in branding"

    def test_location_complete(self, av01_data):
        loc = av01_data["equipment"].get("location", {})
        assert loc.get("area") == "PLANTA-03"
        assert loc.get("linha") == "Linha 1"
        assert loc.get("ponto_instalacao") == "Entrada Britagem"

    def test_info_blocks_present(self, av01_data):
        eq = av01_data["equipment"]
        assert eq.get("curiosity"), "curiosity block should be present"
        assert eq.get("warning"), "warning block should be present"
        assert eq.get("safety"), "safety block should be present"
        assert eq.get("best_practices"), "best_practices block should be present"
        assert eq.get("description"), "description should be present"

    def test_technical_data_present(self, av01_data):
        td = av01_data["equipment"].get("technical_data", {})
        assert td.get("modelo")
        assert td.get("corrente")
        assert td.get("frequencia")

    def test_inspections_max_3_items(self, av01_data):
        insps = av01_data["equipment"].get("inspections", [])
        assert isinstance(insps, list)
        assert len(insps) <= 3

    def test_history_summary_present(self, av01_data):
        h = av01_data["equipment"].get("history_summary", {})
        assert h, "history_summary must be present"
        assert h.get("total_inspecoes") is not None or h.get("total_manutencoes") is not None


class TestSensitiveDataFiltered:
    """CRITICAL: The public endpoint must NEVER leak sensitive fields."""

    SENSITIVE_KEYS = ["_id", "organization_id", "responsavel", "responsavel_email",
                       "custo", "custo_hora", "created_by", "updated_by"]

    def test_no_mongo_objectid(self, av01_data):
        eq_str = json.dumps(av01_data)
        assert '"_id"' not in eq_str, f"MongoDB _id leaked in response"

    def test_no_organization_id(self, av01_data):
        eq = av01_data["equipment"]
        # organization_id may appear inside branding URL path, but should not be a top-level field
        assert "organization_id" not in eq

    def test_no_sensitive_fields_in_equipment(self, av01_data):
        eq = av01_data["equipment"]
        for k in ["responsavel", "responsavel_email", "created_by", "updated_by", "custo", "custo_hora"]:
            assert k not in eq, f"Sensitive key '{k}' leaked in equipment"

    def test_no_email_addresses(self, av01_data):
        # Very simple regex check for @something. in the body
        import re
        body_str = json.dumps(av01_data)
        emails = re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+", body_str)
        # allow no matches
        assert len(emails) == 0, f"Email(s) leaked in public response: {emails}"


class TestMinimalEquipment:
    """BB-03: equipment potentially without full dossier — conditional rendering."""

    def test_available_true_even_without_dossier(self, bb03_data):
        assert bb03_data.get("available") is True

    def test_optional_blocks_may_be_absent(self, bb03_data):
        eq = bb03_data["equipment"]
        # tag/nome must always exist
        assert eq.get("tag")
        assert eq.get("nome")
        # info blocks are optional
        # Frontend must handle their absence — we simply assert that if they exist, they are strings
        for k in ["curiosity", "warning", "safety", "best_practices", "description"]:
            v = eq.get(k)
            if v is not None:
                assert isinstance(v, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
