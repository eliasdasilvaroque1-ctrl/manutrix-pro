"""RC-12 Dossiê Permanente do Equipamento — backend tests
Covers:
- GET /api/ativos/{id}/historico
- GET /api/dossie/os/{os_id}
- GET /api/dossie/inspecao/{insp_id}
- GET /api/dossie/pesquisa (with q, tipo filters)
- RBAC: tec_mecanico blocked from dossie endpoints
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope="module")
def org_id():
    r = requests.get(f"{BASE_URL}/api/public/organizations", timeout=30)
    assert r.status_code == 200, r.text
    orgs = r.json()
    assert orgs, "no organizations"
    return orgs[0]['id']


def _login(email, password, org_id):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password, "organization_id": org_id},
                      timeout=30)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def master_token(org_id):
    return _login("master@maintrix.com", "master123", org_id)


@pytest.fixture(scope="module")
def tec_token(org_id):
    return _login("test.mec@maintrix.com", "tec123", org_id)


@pytest.fixture(scope="module")
def master_headers(master_token):
    return {"Authorization": f"Bearer {master_token}"}


@pytest.fixture(scope="module")
def tec_headers(tec_token):
    return {"Authorization": f"Bearer {tec_token}"}


@pytest.fixture(scope="module")
def first_ativo_id(master_headers):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=master_headers, timeout=30)
    assert r.status_code == 200, r.text
    ativos = r.json()
    assert ativos, "no ativos"
    return ativos[0]['id']


@pytest.fixture(scope="module")
def concluida_os_id(master_headers):
    r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=master_headers, timeout=30)
    assert r.status_code == 200, r.text
    oss = r.json()
    concluidas = [o for o in oss if o.get('status') == 'concluida']
    if not concluidas:
        pytest.skip("no concluida OS available")
    return concluidas[0]['id']


@pytest.fixture(scope="module")
def any_inspecao_id(master_headers):
    r = requests.get(f"{BASE_URL}/api/inspecoes", headers=master_headers, timeout=30)
    assert r.status_code == 200, r.text
    insps = r.json()
    if not insps:
        pytest.skip("no inspecoes")
    return insps[0]['id']


# ============== HISTORICO ==============

class TestHistorico:
    def test_historico_returns_events(self, master_headers, first_ativo_id):
        r = requests.get(f"{BASE_URL}/api/ativos/{first_ativo_id}/historico",
                         headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list), "historico should be array"
        # If events exist, check required fields
        if data:
            ev = data[0]
            assert 'tipo_evento' in ev
            assert 'titulo' in ev
            assert 'status' in ev
            assert 'data' in ev
            print(f"[historico] {len(data)} events, sample: tipo={ev.get('tipo_evento')} titulo={ev.get('titulo')}")


# ============== DOSSIE OS ==============

class TestDossieOS:
    def test_dossie_os_enriched(self, master_headers, concluida_os_id):
        r = requests.get(f"{BASE_URL}/api/dossie/os/{concluida_os_id}",
                         headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert (d.get('ativo_unidade') or '').strip() == 'UNIDADE CEDRO', f"got {d.get('ativo_unidade')!r}"
        assert 'ativo_sector' in d
        assert isinstance(d.get('executantes'), list), "executantes must be list"
        assert isinstance(d.get('materiais'), list), "materiais must be list"
        assert isinstance(d.get('fotos'), list), "fotos must be list"
        assert isinstance(d.get('auditoria'), list), "auditoria must be list"
        assert 'aprovacao' in d
        print(f"[dossie/os] unidade={d.get('ativo_unidade')} sector={d.get('ativo_sector')} "
              f"executantes={len(d.get('executantes',[]))} materiais={len(d.get('materiais',[]))} "
              f"fotos={len(d.get('fotos',[]))} audit={len(d.get('auditoria',[]))}")

    def test_dossie_os_404(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/dossie/os/nonexistent-id-xxx",
                         headers=master_headers, timeout=30)
        assert r.status_code == 404


# ============== DOSSIE INSPECAO ==============

class TestDossieInspecao:
    def test_dossie_inspecao_enriched(self, master_headers, any_inspecao_id):
        r = requests.get(f"{BASE_URL}/api/dossie/inspecao/{any_inspecao_id}",
                         headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert 'ativo' in d
        assert (d.get('ativo_unidade') or '').strip() == 'UNIDADE CEDRO', f"got {d.get('ativo_unidade')!r}"
        assert 'ativo_sector' in d
        # plano may or may not be present
        assert 'checklist' in d
        assert isinstance(d.get('nao_conformidades'), list)
        assert isinstance(d.get('fotos'), list)
        print(f"[dossie/inspecao] unidade={d.get('ativo_unidade')} "
              f"nc={len(d.get('nao_conformidades',[]))} fotos={len(d.get('fotos',[]))}")


# ============== PESQUISA ==============

class TestPesquisa:
    def test_pesquisa_q_bomba(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/dossie/pesquisa",
                         params={"q": "bomba"}, headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            for k in ['tipo_registro', 'tag', 'equipamento', 'area', 'status']:
                assert k in item, f"missing key {k}"
        print(f"[pesquisa q=bomba] {len(data)} results")

    def test_pesquisa_tipo_inspecao(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/dossie/pesquisa",
                         params={"tipo": "inspecao"}, headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        for item in data:
            assert item.get('tipo_registro') == 'inspecao', f"filter broken: {item.get('tipo_registro')}"
        print(f"[pesquisa tipo=inspecao] {len(data)} results, all inspecao")

    def test_pesquisa_no_params(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/dossie/pesquisa",
                         headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        print(f"[pesquisa noargs] {len(data)} results")


# ============== RBAC ==============

class TestRBAC:
    def test_tec_blocked_dossie_os(self, tec_headers, concluida_os_id):
        r = requests.get(f"{BASE_URL}/api/dossie/os/{concluida_os_id}",
                         headers=tec_headers, timeout=30)
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"

    def test_tec_blocked_dossie_inspecao(self, tec_headers, any_inspecao_id):
        r = requests.get(f"{BASE_URL}/api/dossie/inspecao/{any_inspecao_id}",
                         headers=tec_headers, timeout=30)
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"


# ============== REGRESSION ==============

class TestRegression:
    def test_master_dashboard(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_os_list(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/ordens-servico", headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text

    def test_inspecoes_list(self, master_headers):
        r = requests.get(f"{BASE_URL}/api/inspecoes", headers=master_headers, timeout=30)
        assert r.status_code == 200, r.text
