"""Tests for Anomalia module removal and RBAC label fixes."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ORG_SLUG = "astec"

CREDS = {
    "master": ("master@maintrix.com", "master123"),
    "tec_mec": ("test.mec@maintrix.com", "tec123"),
    "gerente": ("test.gerente@maintrix.com", "ger123"),
    "operador": ("test.operador@maintrix.com", "op123"),
}


def _login(email: str, password: str) -> str:
    payload = {"email": email, "password": password}
    resp = requests.post(f"{API}/auth/login", json=payload, timeout=15)
    assert resp.status_code == 200, f"Login {email}: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in {data}"
    return token


@pytest.fixture(scope="module")
def master_token():
    return _login(*CREDS["master"])


@pytest.fixture(scope="module")
def tec_token():
    return _login(*CREDS["tec_mec"])


@pytest.fixture(scope="module")
def gerente_token():
    return _login(*CREDS["gerente"])


@pytest.fixture(scope="module")
def operador_token():
    return _login(*CREDS["operador"])


# --- Anomalia endpoints must be gone ---
class TestAnomaliaEndpointsRemoved:
    def test_get_anomalias_returns_404(self, master_token):
        r = requests.get(f"{API}/anomalias", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 404, f"Expected 404 but got {r.status_code}: {r.text[:200]}"

    def test_post_anomalias_returns_404(self, master_token):
        r = requests.post(
            f"{API}/anomalias",
            headers={"Authorization": f"Bearer {master_token}"},
            json={"titulo": "X", "descricao": "Y"},
        )
        assert r.status_code == 404, f"Expected 404 but got {r.status_code}"

    def test_get_anomalia_by_id_returns_404(self, master_token):
        r = requests.get(f"{API}/anomalias/xxx", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 404


# --- RBAC / permissions ---
class TestRoleLabels:
    def _permissions(self, token):
        r = requests.get(f"{API}/auth/permissions", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        return r.json()

    def test_tec_mec_role_label(self, tec_token):
        data = self._permissions(tec_token)
        # Role label may be role_label or user.role_label
        label = data.get("role_label") or data.get("user", {}).get("role_label")
        # Accept if label absent (label is a frontend concern) but role should be tec_mecanico
        role = data.get("role") or data.get("user", {}).get("role")
        assert role == "tec_mecanico", f"role={role}"
        if label:
            assert label == "Técnico Mecânico", f"role_label={label}"

    def test_gerente_role(self, gerente_token):
        data = self._permissions(gerente_token)
        role = data.get("role") or data.get("user", {}).get("role")
        assert role == "gerente"

    def test_tec_mec_no_anomalia_permissions(self, tec_token):
        data = self._permissions(tec_token)
        perms = data.get("permissions") or []
        assert not any("anomalia" in p.lower() for p in perms), f"Anomalia perms still exist: {perms}"

    def test_master_no_anomalia_permissions(self, master_token):
        data = self._permissions(master_token)
        perms = data.get("permissions") or []
        assert not any("anomalia" in p.lower() for p in perms), f"Anomalia perms exist: {perms}"


# --- Regression: core endpoints still work ---
class TestCoreEndpoints:
    def test_master_dashboard(self, master_token):
        r = requests.get(f"{API}/dashboard/stats", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"

    def test_master_ordens_servico(self, master_token):
        r = requests.get(f"{API}/ordens-servico", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200

    def test_master_ativos(self, master_token):
        r = requests.get(f"{API}/ativos", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200

    def test_master_inspecoes(self, master_token):
        r = requests.get(f"{API}/inspecoes", headers={"Authorization": f"Bearer {master_token}"})
        assert r.status_code == 200

    def test_operador_can_login(self, operador_token):
        assert operador_token is not None
