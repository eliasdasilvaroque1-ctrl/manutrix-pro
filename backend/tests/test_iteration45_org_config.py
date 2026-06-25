"""
Iteration 45 - MANUTRIX ENTERPRISE consolidation tests
- org_config CRUD per section (identidade, tema, terminologia, numeracao, preferencias)
- unidades CRUD (replaces plantas_v2)
- /api/plantas backward compatibility
- Numbering preview
- RBAC: tecnico cannot update org config
- Regression: login, dashboard, ativos, OS, inspecoes
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN = ("admin@manutrix.com", "admin123")
TECNICO = ("tecnico@manutrix.com", "tecnico123")
MASTER = ("master@manutrix.com", "master123")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers():
    return {"Authorization": f"Bearer {_login(*ADMIN)}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def tecnico_headers():
    return {"Authorization": f"Bearer {_login(*TECNICO)}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def master_headers():
    return {"Authorization": f"Bearer {_login(*MASTER)}", "Content-Type": "application/json"}


# =============== ORG CONFIG ===============

class TestOrgConfig:
    def test_get_org_config_autocreates(self, admin_headers):
        r = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        for key in ("identidade", "tema", "terminologia", "numeracao", "preferencias", "organization_id"):
            assert key in data, f"missing {key} in org_config"
        # spot-checks
        assert "cor_primaria" in data["tema"]
        assert "ordens_servico" in data["numeracao"]
        assert "horario_trabalho" in data["preferencias"]
        assert "ativo" in data["terminologia"]

    def test_update_identidade(self, admin_headers):
        body = {"nome_sistema": "TEST_Portal", "subtitulo": "TEST_Subtitulo", "rodape": "TEST rodape"}
        r = requests.put(f"{API}/org/config/identidade", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        # verify persistence
        r2 = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20)
        ident = r2.json()["identidade"]
        assert ident["nome_sistema"] == "TEST_Portal"
        assert ident["subtitulo"] == "TEST_Subtitulo"
        assert ident["rodape"] == "TEST rodape"

    def test_update_tema_all_colors(self, admin_headers):
        body = {
            "cor_primaria": "#111111", "cor_secundaria": "#222222",
            "cor_fundo": "#333333", "cor_texto": "#444444",
            "cor_destaque": "#555555", "cor_sucesso": "#666666",
            "cor_alerta": "#777777", "cor_erro": "#888888",
        }
        r = requests.put(f"{API}/org/config/tema", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        r2 = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20)
        tema = r2.json()["tema"]
        for k, v in body.items():
            assert tema[k] == v, f"{k} != {v} got {tema[k]}"

    def test_update_terminologia(self, admin_headers):
        body = {"ativo": "Equipamento Teste", "tecnico": "Operador"}
        r = requests.put(f"{API}/org/config/terminologia", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        term = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20).json()["terminologia"]
        assert term["ativo"] == "Equipamento Teste"
        assert term["tecnico"] == "Operador"

    def test_update_numeracao(self, admin_headers):
        body = {"ordens_servico": {"prefixo": "TEST-{ano}-", "digitos": 4}}
        r = requests.put(f"{API}/org/config/numeracao", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        num = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20).json()["numeracao"]
        assert num["ordens_servico"]["prefixo"] == "TEST-{ano}-"
        assert num["ordens_servico"]["digitos"] == 4

    def test_update_preferencias(self, admin_headers):
        body = {
            "horario_trabalho": {"inicio": "08:00", "fim": "18:00"},
            "fuso_horario": "America/Sao_Paulo",
            "formato_data": "DD/MM/YYYY",
            "moeda": "BRL",
            "prefixo_empresa": "TST",
        }
        r = requests.put(f"{API}/org/config/preferencias", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        prefs = requests.get(f"{API}/org/config", headers=admin_headers, timeout=20).json()["preferencias"]
        assert prefs["horario_trabalho"]["inicio"] == "08:00"
        assert prefs["prefixo_empresa"] == "TST"

    def test_numeracao_preview(self, admin_headers):
        r = requests.get(f"{API}/org/config/numeracao/preview?entidade=ordens_servico&tipo=corretiva",
                         headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "preview" in data
        assert "prefixo_empresa" in data
        assert "digitos" in data
        assert isinstance(data["preview"], str)
        assert len(data["preview"]) > 0

    def test_tecnico_cannot_update_config(self, tecnico_headers):
        # All section updates should be admin-only
        for section, body in [
            ("identidade", {"nome_sistema": "HACK"}),
            ("tema", {"cor_primaria": "#000"}),
            ("terminologia", {"ativo": "Hack"}),
            ("numeracao", {"ordens_servico": {"prefixo": "X-", "digitos": 3}}),
            ("preferencias", {"prefixo_empresa": "HX"}),
        ]:
            r = requests.put(f"{API}/org/config/{section}", headers=tecnico_headers, json=body, timeout=20)
            assert r.status_code == 403, f"{section} tecnico should be 403 got {r.status_code} {r.text}"


# =============== UNIDADES ===============

class TestUnidades:
    created_id = None

    def test_list_unidades(self, admin_headers):
        r = requests.get(f"{API}/unidades", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)
        # ensure no _id leakage
        for u in r.json():
            assert "_id" not in u

    def test_create_unidade(self, admin_headers):
        body = {"codigo": "TEST_UN1", "nome": "TEST_Unidade_Iter45", "descricao": "test", "endereco": "rua x"}
        r = requests.post(f"{API}/unidades", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["nome"] == "TEST_Unidade_Iter45"
        assert d["codigo"] == "TEST_UN1"
        assert "id" in d
        assert "_id" not in d
        TestUnidades.created_id = d["id"]
        # verify via list
        lst = requests.get(f"{API}/unidades", headers=admin_headers, timeout=20).json()
        assert any(u["id"] == d["id"] for u in lst)

    def test_update_unidade(self, admin_headers):
        assert TestUnidades.created_id
        body = {"nome": "TEST_Unidade_Updated", "descricao": "updated"}
        r = requests.put(f"{API}/unidades/{TestUnidades.created_id}", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["nome"] == "TEST_Unidade_Updated"

    def test_delete_unidade_soft(self, admin_headers):
        assert TestUnidades.created_id
        r = requests.delete(f"{API}/unidades/{TestUnidades.created_id}", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        # ensure it no longer appears in list
        lst = requests.get(f"{API}/unidades", headers=admin_headers, timeout=20).json()
        assert not any(u["id"] == TestUnidades.created_id for u in lst)


# =============== PLANTAS BACKWARD COMPAT ===============

class TestPlantasCompat:
    created_id = None

    def test_list_plantas_compat(self, admin_headers):
        r = requests.get(f"{API}/plantas", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_create_planta_compat(self, admin_headers):
        body = {"codigo": "TEST_PL", "nome": "TEST_Planta_BackCompat", "descricao": "back-compat"}
        r = requests.post(f"{API}/plantas", headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        TestPlantasCompat.created_id = d.get("id")
        assert d.get("nome") == "TEST_Planta_BackCompat"
        # Verify it shows in /api/unidades too (same collection)
        lst = requests.get(f"{API}/unidades", headers=admin_headers, timeout=20).json()
        assert any(u["id"] == TestPlantasCompat.created_id for u in lst)

    def test_update_planta_compat(self, admin_headers):
        assert TestPlantasCompat.created_id
        r = requests.put(f"{API}/plantas/{TestPlantasCompat.created_id}",
                         headers=admin_headers, json={"nome": "TEST_Planta_Updated"}, timeout=20)
        assert r.status_code == 200, r.text

    def test_delete_planta_compat(self, admin_headers):
        assert TestPlantasCompat.created_id
        r = requests.delete(f"{API}/plantas/{TestPlantasCompat.created_id}",
                            headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text


# =============== REGRESSION ===============

class TestRegression:
    def test_login_three_roles(self):
        for email, pwd in [ADMIN, TECNICO, MASTER]:
            r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=20)
            assert r.status_code == 200, f"{email} -> {r.status_code} {r.text}"

    def test_dashboard_stats(self, admin_headers):
        r = requests.get(f"{API}/dashboard/stats", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text

    def test_ativos(self, admin_headers):
        r = requests.get(f"{API}/ativos", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_ordens_servico(self, admin_headers):
        r = requests.get(f"{API}/ordens-servico", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text

    def test_inspecoes(self, admin_headers):
        r = requests.get(f"{API}/inspecoes", headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
