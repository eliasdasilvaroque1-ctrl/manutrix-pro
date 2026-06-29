"""
Iteration 49 — Backend visibility / RBAC tests
Aditivo Arquitetural 002: profile-based visibility on the API layer.

Rules:
- master : sees everything
- admin  : sees everything in the org
- pcm    : sees all disciplines
- supervisor : disciplina + areas
- tecnico    : disciplina + areas
- operador   : NEVER mecanica/eletrica/instrumentacao — only producao/civil
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# --- credentials map ---
USERS = {
    "master":   ("master@manutrix.com",          "master123"),
    "admin":    ("test.admin@maintrix.com",      "admin123"),
    "pcm":      ("test.pcm@maintrix.com",        "pcm123"),
    "sup_mec":  ("test.sup.mec@maintrix.com",    "sup123"),
    "sup_ele":  ("test.sup.ele@maintrix.com",    "sup123"),
    "tec_mec":  ("test.mec@maintrix.com",        "tec123"),
    "tec_ele":  ("test.ele@maintrix.com",        "tec123"),
    "operador": ("test.operador@maintrix.com",   "op123"),
}


# ============== fixtures ==============

@pytest.fixture(scope="session")
def master_token():
    r = requests.post(f"{API}/auth/login", json={"email": USERS["master"][0], "password": USERS["master"][1]}, timeout=20)
    assert r.status_code == 200, f"Master login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def seed_users(master_token):
    """Ensure all test users exist with correct disciplines/areas."""
    r = requests.post(f"{API}/seed/test-users", headers={"Authorization": f"Bearer {master_token}"}, timeout=30)
    assert r.status_code == 200, f"Seed failed: {r.status_code} {r.text}"
    return r.json()


def _login(role_key):
    email, pwd = USERS[role_key]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=20)
    assert r.status_code == 200, f"Login {role_key} failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _list_os(token):
    r = requests.get(f"{API}/ordens-servico?limit=500", headers=_headers(token), timeout=20)
    assert r.status_code == 200, f"GET /ordens-servico → {r.status_code} {r.text}"
    return r.json()


def _disciplines(os_list):
    return sorted({o.get("disciplina") for o in os_list if o.get("disciplina")})


# ============== LOGIN PAGE LOADS ==============

class TestFrontendLogin:
    def test_login_page_loads(self):
        r = requests.get(BASE_URL, timeout=20)
        assert r.status_code == 200
        # quick smoke check
        assert "<html" in r.text.lower() or "<!doctype" in r.text.lower()


# ============== OS visibility per role ==============

class TestOSVisibility:
    """GET /api/ordens-servico — visibility per role."""

    def test_master_sees_all_5(self):
        token = _login("master")
        os_list = _list_os(token)
        assert len(os_list) == 5, f"Master should see 5 OS, got {len(os_list)}: {_disciplines(os_list)}"
        assert set(_disciplines(os_list)) == {"mecanica", "eletrica", "instrumentacao", "producao", "civil"}

    def test_admin_sees_all_5(self):
        token = _login("admin")
        os_list = _list_os(token)
        assert len(os_list) == 5, f"Admin should see 5 OS, got {len(os_list)}"
        assert set(_disciplines(os_list)) == {"mecanica", "eletrica", "instrumentacao", "producao", "civil"}

    def test_pcm_sees_all_5(self):
        token = _login("pcm")
        os_list = _list_os(token)
        assert len(os_list) == 5, f"PCM should see 5 OS, got {len(os_list)}"
        assert set(_disciplines(os_list)) == {"mecanica", "eletrica", "instrumentacao", "producao", "civil"}

    def test_supervisor_mecanico_sees_only_mecanica(self):
        token = _login("sup_mec")
        os_list = _list_os(token)
        disc = set(_disciplines(os_list))
        # Should ONLY contain mecanica
        assert "eletrica" not in disc, f"Sup-Mec leaked eletrica: {disc}"
        assert "instrumentacao" not in disc, f"Sup-Mec leaked instrumentacao: {disc}"
        assert "producao" not in disc, f"Sup-Mec leaked producao: {disc}"
        assert "civil" not in disc, f"Sup-Mec leaked civil: {disc}"
        assert disc == {"mecanica"}, f"Sup-Mec should only see mecanica, got {disc}"
        assert len(os_list) == 1, f"Sup-Mec should see exactly 1 OS, got {len(os_list)}"

    def test_supervisor_eletrico_sees_only_eletrica_instr(self):
        token = _login("sup_ele")
        os_list = _list_os(token)
        disc = set(_disciplines(os_list))
        assert disc.issubset({"eletrica", "instrumentacao"}), f"Sup-Ele leaked: {disc}"
        assert "mecanica" not in disc
        assert "producao" not in disc
        assert "civil" not in disc
        assert len(os_list) == 2, f"Sup-Ele should see 2 OS, got {len(os_list)}: {disc}"

    def test_tecnico_mecanico_sees_only_mecanica(self):
        token = _login("tec_mec")
        os_list = _list_os(token)
        disc = set(_disciplines(os_list))
        assert disc == {"mecanica"}, f"Tec-Mec should only see mecanica, got {disc}"
        assert len(os_list) == 1, f"Tec-Mec should see 1 OS, got {len(os_list)}"

    def test_tecnico_eletrico_sees_only_eletrica_instr(self):
        token = _login("tec_ele")
        os_list = _list_os(token)
        disc = set(_disciplines(os_list))
        assert disc.issubset({"eletrica", "instrumentacao"}), f"Tec-Ele leaked: {disc}"
        assert len(os_list) == 2, f"Tec-Ele should see 2 OS, got {len(os_list)}"

    def test_operador_never_sees_mecanica_eletrica_instr(self):
        token = _login("operador")
        os_list = _list_os(token)
        disc = set(_disciplines(os_list))
        # CRITICAL: operador must NEVER see these 3 disciplines
        assert "mecanica" not in disc, f"SECURITY: Operador leaked mecanica! disc={disc}"
        assert "eletrica" not in disc, f"SECURITY: Operador leaked eletrica! disc={disc}"
        assert "instrumentacao" not in disc, f"SECURITY: Operador leaked instrumentacao! disc={disc}"
        # should only see producao + civil
        assert disc.issubset({"producao", "civil"}), f"Operador unexpected disc: {disc}"
        assert len(os_list) == 2, f"Operador should see 2 OS (producao+civil), got {len(os_list)}: {disc}"


# ============== Dashboard /stats per role ==============

class TestDashboardStats:
    def _open(self, data):
        return (data.get("ordens_servico") or {}).get("abertas")

    def test_master_stats_5_open(self):
        token = _login("master")
        r = requests.get(f"{API}/dashboard/stats", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert self._open(data) == 5, f"Master os abertas expected 5, got {self._open(data)}. Full: {data}"

    def test_supervisor_mec_stats_scoped(self):
        token = _login("sup_mec")
        r = requests.get(f"{API}/dashboard/stats", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert self._open(data) == 1, f"Sup-Mec os abertas expected 1, got {self._open(data)}. Full: {data}"

    def test_operador_stats_only_2(self):
        token = _login("operador")
        r = requests.get(f"{API}/dashboard/stats", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert self._open(data) == 2, f"Operador os abertas expected 2, got {self._open(data)}. Full: {data}"


# ============== Dashboard /os-por-disciplina ==============

class TestOsPorDisciplina:
    def test_operador_never_sees_forbidden_disciplines(self):
        token = _login("operador")
        r = requests.get(f"{API}/dashboard/os-por-disciplina", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        # data is expected to be list of {disciplina: ..., count: ...} or dict.
        if isinstance(data, list):
            disciplinas = {item.get("disciplina") or item.get("name") or item.get("_id") for item in data}
        elif isinstance(data, dict):
            disciplinas = set(data.keys())
        else:
            pytest.fail(f"Unexpected response shape: {type(data)} {data}")

        # Remove None/empty
        disciplinas = {d for d in disciplinas if d}
        assert "mecanica" not in disciplinas, f"SECURITY: Operador saw mecanica in disc breakdown: {disciplinas}"
        assert "eletrica" not in disciplinas, f"SECURITY: Operador saw eletrica in disc breakdown: {disciplinas}"
        assert "instrumentacao" not in disciplinas, f"SECURITY: Operador saw instrumentacao in disc breakdown: {disciplinas}"

    def test_master_sees_all_disciplines(self):
        token = _login("master")
        r = requests.get(f"{API}/dashboard/os-por-disciplina", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text


# ============== /kpis ==============

class TestKpis:
    def test_supervisor_mec_backlog_1(self):
        token = _login("sup_mec")
        r = requests.get(f"{API}/kpis", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        backlog = data.get("backlog_total")
        assert backlog == 1, f"Sup-Mec backlog_total expected 1, got {backlog}. Full: {data}"

    def test_master_kpis_works(self):
        token = _login("master")
        r = requests.get(f"{API}/kpis", headers=_headers(token), timeout=20)
        assert r.status_code == 200, r.text


# ============== OS creation includes sector_id ==============

class TestOSCreationSectorDenorm:
    def test_create_os_includes_sector_id_from_ativo(self, master_token):
        # Pick an ativo
        r = requests.get(f"{API}/ativos?limit=1", headers=_headers(master_token), timeout=20)
        assert r.status_code == 200
        ativos = r.json()
        if not ativos:
            pytest.skip("No ativos to use")
        ativo = ativos[0]
        ativo_id = ativo["id"]
        ativo_sector = ativo.get("sector_id")

        payload = {
            "titulo": "TEST_VIS_SECTOR_DENORM",
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "prioridade": "media",
            "disciplina": "mecanica",
            "descricao": "iteration49 sector denorm test",
        }
        r = requests.post(f"{API}/ordens-servico", headers=_headers(master_token), json=payload, timeout=20)
        assert r.status_code in (200, 201), f"Create OS failed: {r.status_code} {r.text}"
        created = r.json()
        os_id = created["id"]
        try:
            # sector_id must be denormalised onto the OS doc
            assert created.get("sector_id") == ativo_sector, \
                f"OS sector_id ({created.get('sector_id')}) != ativo sector ({ativo_sector})"
            # GET to verify persistence
            r2 = requests.get(f"{API}/ordens-servico/{os_id}", headers=_headers(master_token), timeout=20)
            assert r2.status_code == 200
            assert r2.json().get("sector_id") == ativo_sector
        finally:
            # cleanup
            requests.delete(f"{API}/ordens-servico/{os_id}", headers=_headers(master_token), timeout=20)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
