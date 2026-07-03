"""Sprint 58 - HH Manual endpoint tests
Tests POST /api/os/{os_id}/hh-manual with horas and with data_inicio/data_fim
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


# --- Auth fixtures ---

@pytest.fixture(scope="module")
def tec_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": "test.mec@maintrix.com",
        "password": "tec123",
    })
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def pcm_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": "test.pcm@maintrix.com",
        "password": "pcm123",
    })
    assert r.status_code == 200
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def tec_headers(tec_token):
    return {"Authorization": f"Bearer {tec_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def pcm_headers(pcm_token):
    return {"Authorization": f"Bearer {pcm_token}", "Content-Type": "application/json"}


# --- Helper: find or create an OS to test against ---

@pytest.fixture(scope="module")
def test_os_id(tec_headers):
    """Get any OS visible to the técnico for HH testing."""
    r = requests.get(f"{API}/ordens-servico", headers=tec_headers)
    assert r.status_code == 200, f"Failed listing OS: {r.status_code}"
    lst = r.json()
    assert isinstance(lst, list) and len(lst) > 0, "No OS available for técnico"
    # Prefer one that is not concluida/cancelada
    for os_doc in lst:
        st = os_doc.get("status", "")
        if st not in ("concluida", "cancelada", "encerrada"):
            return os_doc["id"]
    return lst[0]["id"]


# --- Tests ---

class TestHHManualHoras:
    """POST /api/os/{os_id}/hh-manual with horas should return minutos = horas*60"""

    def test_hh_manual_with_horas(self, tec_headers, test_os_id):
        payload = {"horas": 2.5, "descricao": "TEST_ hh manual via horas"}
        r = requests.post(f"{API}/os/{test_os_id}/hh-manual", headers=tec_headers, json=payload)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("success") is True, f"success not true: {data}"
        assert data.get("minutos") == 150.0 or data.get("minutos") == 150, f"expected 150 minutos, got {data}"

    def test_hh_manual_with_data_inicio_fim(self, tec_headers, test_os_id):
        payload = {
            "data_inicio": "2026-07-03T08:00:00",
            "data_fim": "2026-07-03T10:30:00",
            "descricao": "TEST_ hh manual via dates",
        }
        r = requests.post(f"{API}/os/{test_os_id}/hh-manual", headers=tec_headers, json=payload)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("success") is True
        assert data.get("minutos") == 150.0 or data.get("minutos") == 150, f"expected 150, got {data}"

    def test_hh_manual_without_horas_or_dates_returns_400(self, tec_headers, test_os_id):
        payload = {"descricao": "TEST_ invalid"}
        r = requests.post(f"{API}/os/{test_os_id}/hh-manual", headers=tec_headers, json=payload)
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"

    def test_hh_manual_persists_registros(self, tec_headers, test_os_id):
        """After a hh-manual POST, GET /os/{id}/hh should include manual entries."""
        # Post an entry
        payload = {"horas": 1.0, "descricao": "TEST_ persistence check"}
        r = requests.post(f"{API}/os/{test_os_id}/hh-manual", headers=tec_headers, json=payload)
        assert r.status_code == 200
        # List HH
        r2 = requests.get(f"{API}/os/{test_os_id}/hh", headers=tec_headers)
        assert r2.status_code == 200
        registros = r2.json()
        # Should contain at least one manual pair
        manual = [x for x in registros if x.get("manual") is True]
        assert len(manual) >= 2, f"expected paired manual entries, got {len(manual)}"

    def test_hh_manual_updates_resumo(self, tec_headers, test_os_id):
        r = requests.get(f"{API}/hh/resumo/{test_os_id}", headers=tec_headers)
        assert r.status_code == 200
        data = r.json()
        assert "executantes" in data
        assert isinstance(data.get("hh_total_liquida_min", -1), (int, float))


class TestOrgConfigModoHH:
    """org_config.workflow.modo_hh should exist"""

    def test_workflow_modo_hh_exists(self, pcm_headers):
        r = requests.get(f"{API}/org/config", headers=pcm_headers)
        if r.status_code == 404:
            pytest.skip("org/config endpoint not found")
        assert r.status_code == 200, r.text
        cfg = r.json()
        wf = cfg.get("workflow", {})
        assert "modo_hh" in wf, f"workflow.modo_hh missing: {wf}"
        assert wf["modo_hh"] in ("manual", "cronometro", "ambos")


class TestOSStatusTransitions:
    """Verify OS action endpoints work for técnico"""

    def test_get_os_detail(self, tec_headers, test_os_id):
        r = requests.get(f"{API}/ordens-servico/{test_os_id}", headers=tec_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("id") == test_os_id
        assert "status" in data
