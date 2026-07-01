"""Iteration 50 - Test:
- POST /api/planos-inspecao with/without ativo_id (now optional)
- POST /api/planos-inspecao with 10/50/100 perguntas
- POST /api/planos-inspecao missing 'nome' -> 422 with field name
- GET  /api/planos-inspecao returns 'perguntas' key
- Supervisor now has full visibility (same as PCM/Admin) → sees ALL 5 OS
- Mecânico still sees only 1 OS (mecanica)
- Operador still sees only 2 OS (producao+civil)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

CREDS = {
    "master":    ("master@manutrix.com",       "master123"),
    "sup_mec":   ("test.sup.mec@maintrix.com", "sup123"),
    "mecanico":  ("test.mec@maintrix.com",     "tec123"),
    "operador":  ("test.operador@maintrix.com","op123"),
}

_tokens = {}
_created_planos = []


def _login(key):
    if key in _tokens:
        return _tokens[key]
    email, password = CREDS[key]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"Login failed for {key}: {r.status_code} {r.text}"
    tok = r.json()["access_token"]
    _tokens[key] = tok
    return tok


def _h(key):
    return {"Authorization": f"Bearer {_login(key)}", "Content-Type": "application/json"}


# --- Ensure seed test users are present ---
@pytest.fixture(scope="module", autouse=True)
def seed_users():
    try:
        r = requests.post(f"{API}/seed/test-users", headers=_h("master"), timeout=30)
        # 200/201/409 acceptable
        assert r.status_code in (200, 201, 409), f"seed test users: {r.status_code} {r.text[:200]}"
    except Exception as e:
        pytest.skip(f"cannot seed test users: {e}")
    yield
    # Cleanup created planos
    for pid in _created_planos:
        try:
            requests.delete(f"{API}/planos-inspecao/{pid}", headers=_h("master"), timeout=15)
        except Exception:
            pass


# ============== PLANOS DE INSPEÇÃO ==============

def _mk_perguntas(n):
    return [{"texto": f"Item {i+1}", "tipo_campo": "boolean", "ordem": i} for i in range(n)]


class TestPlanosInspecao:
    def test_create_plano_without_ativo_id_generic(self):
        """ativo_id agora é Optional — plano genérico deve ser criado."""
        payload = {
            "nome": "TEST_ITER50_Plano_Generico",
            "tipo": "inspecao",
            "disciplina": "mecanica",
            "perguntas": _mk_perguntas(3),
        }
        r = requests.post(f"{API}/planos-inspecao", headers=_h("master"), json=payload, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        data = r.json()
        assert data.get("nome") == payload["nome"]
        assert data.get("ativo_id") is None
        assert len(data.get("perguntas", [])) == 3
        _created_planos.append(data["id"])

        # Verify persistence
        g = requests.get(f"{API}/planos-inspecao", headers=_h("master"), timeout=15)
        assert g.status_code == 200
        assert any(p.get("id") == data["id"] for p in g.json())

    def test_create_plano_with_ativo_id(self):
        # get a random ativo
        r = requests.get(f"{API}/ativos", headers=_h("master"), timeout=15)
        assert r.status_code == 200
        ativos = r.json()
        if not ativos:
            pytest.skip("no assets available")
        ativo_id = ativos[0]["id"]
        payload = {
            "nome": "TEST_ITER50_Plano_ComAtivo",
            "tipo": "inspecao",
            "ativo_id": ativo_id,
            "perguntas": _mk_perguntas(2),
        }
        r = requests.post(f"{API}/planos-inspecao", headers=_h("master"), json=payload, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        data = r.json()
        assert data.get("ativo_id") == ativo_id
        _created_planos.append(data["id"])

    @pytest.mark.parametrize("n", [10, 50, 100])
    def test_create_plano_bulk_perguntas(self, n):
        payload = {
            "nome": f"TEST_ITER50_Plano_{n}itens",
            "tipo": "inspecao",
            "perguntas": _mk_perguntas(n),
        }
        r = requests.post(f"{API}/planos-inspecao", headers=_h("master"), json=payload, timeout=40)
        assert r.status_code in (200, 201), f"{n} itens: {r.status_code} {r.text[:300]}"
        data = r.json()
        assert len(data.get("perguntas", [])) == n, f"expected {n} perguntas, got {len(data.get('perguntas', []))}"
        _created_planos.append(data["id"])

    def test_create_plano_missing_nome_returns_422_with_field(self):
        payload = {"tipo": "inspecao", "perguntas": []}  # missing 'nome'
        r = requests.post(f"{API}/planos-inspecao", headers=_h("master"), json=payload, timeout=15)
        assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text}"
        body = r.json()
        detail = body.get("detail") or []
        # detail is Pydantic v2 list of {loc: [...], msg, type}
        assert isinstance(detail, list) and len(detail) > 0
        # verify loc contains 'nome'
        found = False
        for err in detail:
            loc = err.get("loc") or []
            if "nome" in loc:
                found = True
                break
        assert found, f"'nome' field not in error loc: {detail}"

    def test_get_planos_returns_perguntas_key(self):
        r = requests.get(f"{API}/planos-inspecao", headers=_h("master"), timeout=15)
        assert r.status_code == 200
        planos = r.json()
        assert isinstance(planos, list)
        # Find any created test plano
        test_planos = [p for p in planos if p.get("nome", "").startswith("TEST_ITER50")]
        assert len(test_planos) > 0, "no TEST_ITER50 planos found"
        for p in test_planos:
            assert "perguntas" in p, f"plano {p.get('id')} missing 'perguntas' key"
            assert isinstance(p["perguntas"], list)


# ============== VISIBILIDADE SUPERVISOR (full access) ==============

class TestSupervisorFullVisibility:
    def _fetch_os(self, key):
        r = requests.get(f"{API}/ordens-servico", headers=_h(key), timeout=15)
        assert r.status_code == 200, f"{key}: {r.status_code} {r.text}"
        return r.json()

    def test_master_sees_5_os(self):
        os_list = self._fetch_os("master")
        # seeded test users create 5 disciplines
        assert len(os_list) >= 5, f"expected >=5 OS for master, got {len(os_list)}"

    def test_supervisor_now_sees_same_as_master(self):
        master_os = self._fetch_os("master")
        sup_os = self._fetch_os("sup_mec")
        # Same organization → supervisor sees same 5 seed OS as master (within org filter)
        # We require at least 5 (bug fix: was 1 before)
        assert len(sup_os) >= 5, f"supervisor now expected FULL visibility (>=5 OS), got {len(sup_os)}"

    def test_supervisor_dashboard_stats_shows_5_abertas(self):
        r = requests.get(f"{API}/dashboard/stats", headers=_h("sup_mec"), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # nested per prior iteration
        abertas = data.get("ordens_servico", {}).get("abertas", data.get("os_abertas"))
        assert abertas is not None, f"no 'abertas' key in stats: {data}"
        assert abertas >= 5, f"supervisor should see 5+ OS abertas, got {abertas}"

    def test_mecanico_still_scoped_to_1_os(self):
        os_list = self._fetch_os("mecanico")
        assert len(os_list) == 1, f"mecânico must see exactly 1 OS (mecanica), got {len(os_list)}"
        assert os_list[0].get("disciplina") == "mecanica"

    def test_operador_still_scoped_to_2_os(self):
        os_list = self._fetch_os("operador")
        assert len(os_list) == 2, f"operador must see 2 OS (producao+civil), got {len(os_list)}: disciplines={[o.get('disciplina') for o in os_list]}"
        disciplines = {o.get("disciplina") for o in os_list}
        assert disciplines.issubset({"producao", "civil", None, ""}), f"forbidden disciplines: {disciplines}"
        # never sees mecanica/eletrica/instrumentacao
        assert "mecanica" not in disciplines
        assert "eletrica" not in disciplines
        assert "instrumentacao" not in disciplines
