"""Iteration 55 — Prontuário do Ativo (Asset Health Record)
Backend tests:
- GET /api/ativos/{id}/saude returns full health payload
- GET /api/ativos/{id} returns KPIs (total_os, total_falhas, disponibilidade_percent, mtbf_horas, mttr_horas)
- BR-01 has approved plans, open OS, and pending inspection
"""
import os
import pytest
import requests

# Load REACT_APP_BACKEND_URL from frontend/.env when not present in environment
if not os.environ.get("REACT_APP_BACKEND_URL"):
    try:
        with open("/app/frontend/.env") as _f:
            for _line in _f:
                if _line.startswith("REACT_APP_BACKEND_URL="):
                    os.environ["REACT_APP_BACKEND_URL"] = _line.strip().split("=", 1)[1]
                    break
    except Exception:
        pass
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
BR01_ATIVO_ID = "025260b9-e541-4745-9100-e5110efb8155"


@pytest.fixture(scope="module")
def master_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "master@manutrix.com", "password": "master123"},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(master_token):
    return {"Authorization": f"Bearer {master_token}"}


class TestAtivoDetail:
    """GET /api/ativos/{id} — returns identification + KPIs + related"""

    def test_get_br01_returns_full_identification(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("tag") == "BR-01", f"expected tag BR-01, got {d.get('tag')}"
        assert "BRITADOR" in (d.get("nome") or "").upper()
        # Fabricante ASTEC per problem statement
        assert (d.get("fabricante") or "").upper() == "ASTEC"
        # Sector should be present
        sector = d.get("sector") or {}
        assert "Britagem Primária" in (sector.get("nome") or "") or "PRIMARIA" in (sector.get("nome") or "").upper()

    def test_get_br01_returns_kpis(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        kpis = r.json().get("kpis")
        assert kpis is not None, "kpis key missing"
        for k in ("total_os", "total_falhas", "disponibilidade_percent", "mtbf_horas", "mttr_horas"):
            assert k in kpis, f"missing kpi field {k} — got keys {list(kpis.keys())}"
        # Types & ranges
        assert isinstance(kpis["total_os"], int) and kpis["total_os"] >= 0
        assert isinstance(kpis["total_falhas"], int) and kpis["total_falhas"] >= 0
        assert 0 <= float(kpis["disponibilidade_percent"]) <= 100
        assert float(kpis["mtbf_horas"]) >= 0
        assert float(kpis["mttr_horas"]) >= 0

    def test_get_br01_returns_related_lists(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("ordens_servico", "inspecoes", "materiais"):
            assert isinstance(d.get(k), list), f"{k} should be a list"


class TestAtivoSaude:
    """GET /api/ativos/{id}/saude — Prontuário health summary"""

    def test_saude_returns_all_expected_fields(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}/saude", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        expected = {
            "ultima_inspecao", "proxima_inspecao",
            "ultima_preventiva", "proxima_preventiva",
            "ultima_lubrificacao", "ultima_os", "ultima_anomalia",
        }
        missing = expected - set(d.keys())
        assert not missing, f"saude missing keys: {missing}"

    def test_saude_br01_has_pending_next_inspecao(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}/saude", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        prox = r.json().get("proxima_inspecao")
        assert prox is not None, "BR-01 should have a pending next inspection per requirements"
        assert prox.get("data") is not None, f"proxima_inspecao.data missing: {prox}"

    def test_saude_404_for_unknown_ativo(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/ativos/does-not-exist-xyz/saude", headers=auth_headers, timeout=15)
        assert r.status_code == 404

    def test_saude_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/ativos/{BR01_ATIVO_ID}/saude", timeout=15)
        assert r.status_code in (401, 403), f"expected auth challenge, got {r.status_code}"


class TestBR01ProntuarioContext:
    """Sanity checks that the surrounding context on BR-01 matches the spec"""

    def test_br01_has_3_approved_plans(self, auth_headers):
        # Endpoint uses ativo_id (UUID), not TAG
        r = requests.get(
            f"{BASE_URL}/api/planos-inspecao/por-ativo/{BR01_ATIVO_ID}",
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        planos = r.json()
        if isinstance(planos, dict):
            planos = planos.get("items") or planos.get("planos") or []
        aprovados = [p for p in planos if (p.get("status") or "").lower() == "aprovado"]
        assert len(aprovados) >= 3, f"expected >=3 aprovado plans for BR-01, got {len(aprovados)}"

    def test_br01_has_open_os(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/ordens-servico?ativo_id={BR01_ATIVO_ID}",
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        os_list = r.json()
        if isinstance(os_list, dict):
            os_list = os_list.get("items") or []
        abertas = [o for o in os_list if (o.get("status") or "").lower() in ("aberta", "em_execucao", "planejada")]
        assert len(abertas) >= 1, f"expected at least 1 open OS for BR-01, got {len(abertas)} of {len(os_list)}"
