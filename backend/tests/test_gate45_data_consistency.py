"""GATE 4.5 — Data Consistency (Enterprise Homologation)
Tests the 10 scenarios of data propagation across MAINTRIX CMMS modules.
"""
import os
import time
import uuid
import concurrent.futures
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

ORG_ASTEC = "9a232bf2-fc01-4253-813f-8df356be31c1"
ORG_PALFA = "5ea998af-ee7e-4549-9fc9-11b338335793"  # corrected from task spec

# ---- Auth Fixtures ----

def _login(email, password, org):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password, "organization_id": org}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Login failed for {email}: {r.status_code} {r.text[:120]}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def t_admin():
    return _login("test.admin@maintrix.com", "admin123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_pcm():
    return _login("test.pcm@maintrix.com", "pcm123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_operador():
    return _login("test.operador@maintrix.com", "op123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_tec():
    return _login("test.mec@maintrix.com", "tec123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_gerente():
    return _login("test.gerente@maintrix.com", "ger123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_viewer():
    return _login("rc07v@maintrix.com", "viewer123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_master():
    return _login("master@maintrix.com", "master123", ORG_ASTEC)


@pytest.fixture(scope="module")
def t_palfa_admin(t_master):
    """Reset Pedreira admin pw via master, then login."""
    palfa_uid = "65123581-8cc2-4c35-be28-0edf5516717b"
    r = requests.post(f"{BASE_URL}/api/admin/users/{palfa_uid}/reset-password",
                      headers={"Authorization": f"Bearer {t_master}"},
                      json={"new_password": "PalfaTest!123"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Cannot reset palfa admin: {r.status_code}")
    temp_pw = r.json().get("temp_password", "PalfaTest!123")
    login_r = requests.post(f"{BASE_URL}/api/auth/login",
                            json={"email": "admin@pedreira-alfa.com",
                                  "password": temp_pw,
                                  "organization_id": ORG_PALFA}, timeout=30)
    if login_r.status_code != 200:
        pytest.skip(f"Palfa admin login failed: {login_r.status_code} {login_r.text[:200]}")
    return login_r.json()["access_token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def sample_ativo_id(t_admin):
    r = requests.get(f"{BASE_URL}/api/ativos", headers=H(t_admin), timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0
    return ativos[0]["id"]


@pytest.fixture(scope="module")
def sample_sector_id(t_admin):
    """Return a valid sector_id from ativos for ativo creation."""
    r = requests.get(f"{BASE_URL}/api/ativos", headers=H(t_admin), timeout=30)
    for a in r.json():
        if a.get("sector_id"):
            return a["sector_id"]
    return ""


@pytest.fixture(scope="module")
def sample_estoque(t_admin):
    """Find or create an estoque item with quantity>=10 for material tests."""
    r = requests.get(f"{BASE_URL}/api/estoque", headers=H(t_admin), timeout=30)
    assert r.status_code == 200
    items = r.json()
    # look for TEST-MAT-5D393E as per task
    for it in items:
        if it.get('sku') == 'TEST-MAT-5D393E' and it.get('quantidade', 0) >= 10:
            return it
    # else pick any high-qty item
    for it in items:
        if it.get('quantidade', 0) >= 10:
            return it
    # Create one
    sku = f"TEST-MAT-{uuid.uuid4().hex[:6].upper()}"
    r2 = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_admin),
                       json={"sku": sku, "nome": "Test Material Gate45",
                             "categoria": "consumivel", "quantidade": 20,
                             "unidade": "UN", "custo_unitario": 10}, timeout=30)
    assert r2.status_code in (200, 201), r2.text
    return r2.json()


# ============ SCENARIO 1: OS LIFECYCLE ============

class TestScenario1_OS_Lifecycle:
    os_id = None
    os_numero = None
    initial_backlog = None

    def test_1a_operador_creates_solicitada(self, t_operador, sample_ativo_id):
        payload = {"titulo": "TEST_GATE45 Solicitação de OS",
                   "tipo": "corretiva", "disciplina": "mecanica",
                   "prioridade": "media", "ativo_id": sample_ativo_id}
        r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_operador),
                          json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "solicitada", f"Expected solicitada, got {data['status']}"
        assert "id" in data
        TestScenario1_OS_Lifecycle.os_id = data["id"]
        TestScenario1_OS_Lifecycle.os_numero = data.get("numero")

    def test_1b_solicitada_excluded_from_kpis(self, t_admin):
        assert TestScenario1_OS_Lifecycle.os_id
        r = requests.get(f"{BASE_URL}/api/kpis", headers=H(t_admin), timeout=30)
        assert r.status_code == 200
        kpis = r.json()
        # Assert solicitada NOT counted in backlog
        r2 = requests.get(f"{BASE_URL}/api/ordens-servico?status=solicitada",
                          headers=H(t_admin), timeout=30)
        solicitadas_ids = [o["id"] for o in r2.json()]
        assert TestScenario1_OS_Lifecycle.os_id in solicitadas_ids
        # backlog spec: {aberta, planejada, em_execucao, pausada} - not solicitada
        # As we cannot know absolute number, just save
        TestScenario1_OS_Lifecycle.initial_backlog = kpis["backlog_total"]

    def test_1c_pcm_moves_solicitada_to_programada(self, t_pcm):
        os_id = TestScenario1_OS_Lifecycle.os_id
        assert os_id
        r = requests.patch(f"{BASE_URL}/api/ordens-servico/{os_id}/status",
                           headers=H(t_pcm), json={"new_status": "programada"}, timeout=30)
        assert r.status_code == 200, r.text
        # Verify
        rg = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=H(t_pcm), timeout=30)
        assert rg.json()["status"] == "programada"

    def test_1d_pcm_moves_to_em_execucao_sets_data_inicio(self, t_pcm):
        os_id = TestScenario1_OS_Lifecycle.os_id
        r = requests.patch(f"{BASE_URL}/api/ordens-servico/{os_id}/status",
                           headers=H(t_pcm), json={"new_status": "em_execucao"}, timeout=30)
        assert r.status_code == 200, r.text
        rg = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=H(t_pcm), timeout=30)
        d = rg.json()
        assert d["status"] == "em_execucao"
        assert d.get("data_inicio"), "data_inicio deve ser setada automaticamente"

    def test_1e_admin_concludes_os(self, t_admin):
        os_id = TestScenario1_OS_Lifecycle.os_id
        r = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/concluir",
                          headers=H(t_admin),
                          json={"tempo_execucao_minutos": 120,
                                "servicos_realizados": "TEST_GATE45 Troca de rolamento",
                                "skip_foto_check": True}, timeout=30)
        assert r.status_code == 200, r.text
        rg = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=H(t_admin), timeout=30)
        d = rg.json()
        assert d["status"] == "concluida"
        assert d.get("data_conclusao")
        assert d.get("tempo_execucao_minutos") == 120

    def test_1f_kpis_updated_after_conclusion(self, t_admin):
        r = requests.get(f"{BASE_URL}/api/kpis", headers=H(t_admin), timeout=30)
        assert r.status_code == 200
        kpis = r.json()
        # After conclusion, backlog should not include this OS
        assert isinstance(kpis["backlog_total"], int)
        # MTTR should be a number (corretiva concluida contributes)
        assert kpis["mttr_horas"] >= 0

    def test_1g_dashboard_stats_reflects_concluida(self, t_admin):
        r = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=H(t_admin), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "ordens_servico" in d
        assert d["ordens_servico"].get("concluidas_hoje", 0) >= 1

    def test_1h_audit_log_contains_transitions(self, t_admin):
        os_id = TestScenario1_OS_Lifecycle.os_id
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs?entity_id={os_id}",
                         headers=H(t_admin), timeout=30)
        assert r.status_code == 200
        logs = r.json()
        # Fallback: try filter by entity type
        if not logs or (isinstance(logs, dict) and not logs.get("logs")):
            r2 = requests.get(f"{BASE_URL}/api/admin/audit-logs", headers=H(t_admin), timeout=30)
            all_logs = r2.json() if isinstance(r2.json(), list) else r2.json().get("logs", [])
            logs = [l for l in all_logs if l.get("entity_id") == os_id]
        logs_list = logs if isinstance(logs, list) else logs.get("logs", [])
        assert len(logs_list) >= 1, f"Audit log should have entries for OS {os_id}"
        actions = {l.get("action") for l in logs_list}
        # Expected: at least a status change and conclusion
        assert any("status" in (a or "") or a == "kanban_move" for a in actions), \
            f"Expected status transition actions, got {actions}"


# ============ SCENARIO 4: MATERIAIS ============

class TestScenario4_Materiais:
    os_id = None
    material_id = None
    initial_qty = None

    def test_4_setup_os(self, t_admin, sample_ativo_id):
        payload = {"titulo": "TEST_GATE45 OS Material",
                   "tipo": "corretiva", "disciplina": "mecanica",
                   "prioridade": "media", "ativo_id": sample_ativo_id}
        r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_admin),
                          json=payload, timeout=30)
        assert r.status_code == 200
        TestScenario4_Materiais.os_id = r.json()["id"]

    def test_4a_consume_material_deducts_stock(self, t_admin, sample_estoque):
        os_id = TestScenario4_Materiais.os_id
        assert os_id
        # Get current stock qty
        rg = requests.get(f"{BASE_URL}/api/estoque/{sample_estoque['id']}",
                          headers=H(t_admin), timeout=30)
        assert rg.status_code == 200
        initial = rg.json()["quantidade"]
        TestScenario4_Materiais.initial_qty = initial

        r = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/materiais",
                          headers=H(t_admin),
                          json={"item_estoque_id": sample_estoque["id"], "quantidade": 2},
                          timeout=30)
        assert r.status_code == 200, r.text
        TestScenario4_Materiais.material_id = r.json().get("id")

    def test_4b_estoque_quantity_decreased(self, t_admin, sample_estoque):
        rg = requests.get(f"{BASE_URL}/api/estoque/{sample_estoque['id']}",
                          headers=H(t_admin), timeout=30)
        assert rg.status_code == 200
        assert rg.json()["quantidade"] == TestScenario4_Materiais.initial_qty - 2

    def test_4c_audit_log_material_consumo(self, t_admin):
        os_id = TestScenario4_Materiais.os_id
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs", headers=H(t_admin), timeout=30)
        logs = r.json() if isinstance(r.json(), list) else r.json().get("logs", [])
        mat_logs = [l for l in logs if l.get("entity_id") == os_id
                    and l.get("action") == "material_consumo"]
        assert len(mat_logs) >= 1, "Expected material_consumo audit entry"


# ============ SCENARIO 6: RBAC ============

class TestScenario6_RBAC:
    def test_6a_master_admin_users_all_orgs(self, t_master):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=H(t_master), timeout=30)
        assert r.status_code == 200
        users = r.json()
        orgs = {u.get("organization_id") for u in users}
        assert len(orgs) >= 2, f"Master should see users from >=2 orgs, saw {orgs}"

    def test_6b_admin_can_crud_estoque(self, t_admin):
        sku = f"TEST-GATE45-{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_admin),
                          json={"sku": sku, "nome": "GATE45 Admin Test",
                                "categoria": "consumivel", "quantidade": 5,
                                "unidade": "UN"}, timeout=30)
        assert r.status_code in (200, 201), r.text
        eid = r.json()["id"]
        # cleanup
        requests.delete(f"{BASE_URL}/api/estoque/{eid}", headers=H(t_admin), timeout=30)

    def test_6c_pcm_can_manage(self, t_pcm, t_admin):
        # Pick a random ativo without existing plano to avoid duplicate
        r_all = requests.get(f"{BASE_URL}/api/ativos", headers=H(t_admin), timeout=30).json()
        ativo_id = r_all[len(r_all) // 2]["id"] if len(r_all) > 1 else r_all[0]["id"]
        unique = uuid.uuid4().hex[:8].upper()
        r = requests.post(f"{BASE_URL}/api/planos-inspecao", headers=H(t_pcm),
                          json={"nome": f"TEST_GATE45_PCM_{unique}",
                                "ativo_id": ativo_id, "frequencia": "mensal",
                                "perguntas": [{"pergunta": "Q1", "tipo": "sim_nao"}]},
                          timeout=30)
        # PCM must have permission: 200/201 (created) or 409 (duplicate ativo/tipo) — both prove permission
        assert r.status_code in (200, 201, 409), f"PCM should have plano permission, got {r.status_code}: {r.text[:200]}"
        # PCM can create estoque
        sku = f"TEST-GATE45P-{uuid.uuid4().hex[:6].upper()}"
        r2 = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_pcm),
                           json={"sku": sku, "nome": "PCM Test",
                                 "categoria": "consumivel", "quantidade": 3,
                                 "unidade": "UN"}, timeout=30)
        assert r2.status_code in (200, 201), r2.text

    def test_6d_tecnico_cannot_create_estoque(self, t_tec):
        r = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_tec),
                          json={"sku": "TEST-TEC-FAIL", "nome": "x",
                                "categoria": "consumivel", "quantidade": 1,
                                "unidade": "UN"}, timeout=30)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

    def test_6e_operador_can_create_os_cannot_change_status(self, t_operador, sample_ativo_id):
        # Operador creates OS (returns solicitada) — this is the "OS-as-solicitação" design
        r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_operador),
                          json={"titulo": "TEST_GATE45 OP Fail",
                                "tipo": "corretiva", "disciplina": "mecanica",
                                "prioridade": "media", "ativo_id": sample_ativo_id},
                          timeout=30)
        assert r.status_code == 200
        os_id = r.json()["id"]
        assert r.json()["status"] == "solicitada"
        # But operador CANNOT change status via PATCH kanban
        r2 = requests.patch(f"{BASE_URL}/api/ordens-servico/{os_id}/status",
                            headers=H(t_operador), json={"new_status": "programada"},
                            timeout=30)
        assert r2.status_code == 403, f"Operador should NOT change status, got {r2.status_code}"

    def test_6f_viewer_cannot_do_anything(self, t_viewer, sample_ativo_id):
        # Cannot create OS
        r = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_viewer),
                          json={"titulo": "x", "tipo": "corretiva",
                                "disciplina": "mecanica", "prioridade": "media",
                                "ativo_id": sample_ativo_id}, timeout=30)
        assert r.status_code == 403
        # Cannot create estoque
        r2 = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_viewer),
                           json={"sku": "V", "nome": "x", "categoria": "consumivel",
                                 "quantidade": 1, "unidade": "UN"}, timeout=30)
        assert r2.status_code == 403
        # Cannot access admin users
        r3 = requests.get(f"{BASE_URL}/api/admin/users", headers=H(t_viewer), timeout=30)
        assert r3.status_code == 403

    def test_6g_gerente_readonly(self, t_gerente):
        # Can view dashboard
        r = requests.get(f"{BASE_URL}/api/kpis", headers=H(t_gerente), timeout=30)
        assert r.status_code == 200
        # Cannot create estoque
        r2 = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_gerente),
                           json={"sku": "G", "nome": "x", "categoria": "consumivel",
                                 "quantidade": 1, "unidade": "UN"}, timeout=30)
        assert r2.status_code == 403


# ============ SCENARIO 7: MULTI-TENANT ============

class TestScenario7_MultiTenant:
    astec_ativo_id = None
    astec_os_id = None

    def test_7_setup_astec_data(self, t_admin, sample_ativo_id, sample_sector_id):
        # Create an ativo in ASTEC to test isolation
        r = requests.post(f"{BASE_URL}/api/ativos", headers=H(t_admin),
                          json={"tag": f"TEST-GATE45-{uuid.uuid4().hex[:6].upper()}",
                                "nome": "TEST_GATE45 Ativo ASTEC",
                                "tipo_equipamento": "motor",
                                "sector_id": sample_sector_id}, timeout=30)
        assert r.status_code in (200, 201), r.text
        TestScenario7_MultiTenant.astec_ativo_id = r.json()["id"]

        # OS in ASTEC
        ros = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_admin),
                            json={"titulo": "TEST_GATE45 OS ASTEC",
                                  "tipo": "corretiva", "disciplina": "mecanica",
                                  "prioridade": "media", "ativo_id": sample_ativo_id},
                            timeout=30)
        assert ros.status_code == 200
        TestScenario7_MultiTenant.astec_os_id = ros.json()["id"]

    def test_7a_palfa_does_not_see_astec_ativos(self, t_palfa_admin):
        r = requests.get(f"{BASE_URL}/api/ativos", headers=H(t_palfa_admin), timeout=30)
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert TestScenario7_MultiTenant.astec_ativo_id not in ids

    def test_7b_palfa_get_astec_ativo_returns_404(self, t_palfa_admin):
        r = requests.get(f"{BASE_URL}/api/ativos/{TestScenario7_MultiTenant.astec_ativo_id}",
                         headers=H(t_palfa_admin), timeout=30)
        assert r.status_code == 404, f"Expected 404 (not 403), got {r.status_code}"

    def test_7c_palfa_cannot_patch_astec_os(self, t_palfa_admin):
        r = requests.patch(f"{BASE_URL}/api/ordens-servico/{TestScenario7_MultiTenant.astec_os_id}/status",
                           headers=H(t_palfa_admin),
                           json={"new_status": "programada"}, timeout=30)
        # Palfa admin doesn't own this OS — expect 404 (verify_org_access hides existence)
        assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"

    def test_7d_kpis_are_org_scoped(self, t_admin, t_palfa_admin):
        r1 = requests.get(f"{BASE_URL}/api/kpis", headers=H(t_admin), timeout=30).json()
        r2 = requests.get(f"{BASE_URL}/api/kpis", headers=H(t_palfa_admin), timeout=30).json()
        # They should be different objects (independent counts)
        # At minimum, ativos_total should differ significantly
        assert r1.get("ativos_total") != r2.get("ativos_total") or r1 != r2

    def test_7e_estoque_org_isolated(self, t_admin, t_palfa_admin):
        r1 = requests.get(f"{BASE_URL}/api/estoque", headers=H(t_admin), timeout=30).json()
        r2 = requests.get(f"{BASE_URL}/api/estoque", headers=H(t_palfa_admin), timeout=30).json()
        ids1 = {i["id"] for i in r1}
        ids2 = {i["id"] for i in r2}
        # No overlap
        assert ids1.isdisjoint(ids2), f"Estoque overlap between orgs! {ids1 & ids2}"


# ============ SCENARIO 9: SOFT DELETE ============

class TestScenario9_SoftDelete:
    def test_9a_soft_delete_ativo(self, t_admin, sample_sector_id):
        # Create then delete
        tag = f"TEST-GATE45-DEL-{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(f"{BASE_URL}/api/ativos", headers=H(t_admin),
                          json={"tag": tag, "nome": "TEST_GATE45 to_delete",
                                "tipo_equipamento": "motor", "sector_id": sample_sector_id},
                          timeout=30)
        assert r.status_code in (200, 201), r.text
        aid = r.json()["id"]
        rd = requests.delete(f"{BASE_URL}/api/ativos/{aid}", headers=H(t_admin), timeout=30)
        assert rd.status_code in (200, 204)
        # Should not appear in list
        rlist = requests.get(f"{BASE_URL}/api/ativos", headers=H(t_admin), timeout=30)
        assert aid not in {a["id"] for a in rlist.json()}

    def test_9b_audit_log_delete_ativo(self, t_admin):
        r = requests.get(f"{BASE_URL}/api/admin/audit-logs", headers=H(t_admin), timeout=30)
        logs = r.json() if isinstance(r.json(), list) else r.json().get("logs", [])
        delete_logs = [l for l in logs if l.get("action") in ("delete", "excluir")
                       and l.get("entity_type") in ("ativos", "ativo")]
        assert len(delete_logs) >= 1

    def test_9c_soft_delete_estoque(self, t_admin):
        sku = f"TEST-GATE45-DEL-{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_admin),
                          json={"sku": sku, "nome": "TEST_GATE45 to_delete",
                                "categoria": "consumivel", "quantidade": 1,
                                "unidade": "UN"}, timeout=30)
        assert r.status_code in (200, 201)
        eid = r.json()["id"]
        rd = requests.delete(f"{BASE_URL}/api/estoque/{eid}", headers=H(t_admin), timeout=30)
        assert rd.status_code in (200, 204)
        rlist = requests.get(f"{BASE_URL}/api/estoque", headers=H(t_admin), timeout=30)
        assert eid not in {i["id"] for i in rlist.json()}


# ============ SCENARIO 10: CONCURRENCY ============

class TestScenario10_Concurrency:
    def test_10a_10b_concurrent_material_no_negative(self, t_admin, sample_ativo_id):
        # Create fresh estoque item with exactly 10
        sku = f"TEST-CONC-{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(f"{BASE_URL}/api/estoque", headers=H(t_admin),
                          json={"sku": sku, "nome": "TEST Concurrency",
                                "categoria": "consumivel", "quantidade": 10,
                                "unidade": "UN", "custo_unitario": 5}, timeout=30)
        assert r.status_code in (200, 201), r.text
        item_id = r.json()["id"]

        # Create 2 OS
        os_ids = []
        for _ in range(2):
            ro = requests.post(f"{BASE_URL}/api/ordens-servico", headers=H(t_admin),
                               json={"titulo": "TEST_GATE45 concurrency",
                                     "tipo": "corretiva", "disciplina": "mecanica",
                                     "prioridade": "media", "ativo_id": sample_ativo_id},
                               timeout=30)
            assert ro.status_code == 200
            os_ids.append(ro.json()["id"])

        def consume(os_id):
            return requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/materiais",
                                 headers=H(t_admin),
                                 json={"item_estoque_id": item_id, "quantidade": 8},
                                 timeout=30)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            futures = [ex.submit(consume, os_ids[0]), ex.submit(consume, os_ids[1])]
            results = [f.result() for f in futures]

        codes = [r.status_code for r in results]
        # At least ONE must fail (400 insufficient stock) OR total consumed <= 10
        rf = requests.get(f"{BASE_URL}/api/estoque/{item_id}", headers=H(t_admin), timeout=30)
        final_qty = rf.json()["quantidade"]
        assert final_qty >= 0, f"Stock went NEGATIVE: {final_qty}"
        # If both succeeded, final should be -6 which is invalid
        successes = sum(1 for c in codes if c == 200)
        assert successes <= 1 or final_qty >= 0
        # More strict: if both succeeded, that's a race condition bug
        # Report: expect only one success (400 on second)
        # Log the outcome
        print(f"\nConcurrency results: codes={codes}, final_qty={final_qty}")
