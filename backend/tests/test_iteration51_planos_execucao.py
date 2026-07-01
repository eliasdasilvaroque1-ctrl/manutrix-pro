"""Iteration 51 — Test enforcement of Plano Aprovado for Inspecao Execução.

Validates:
  1. Plans created with status='rascunho' by default
  2. POST /api/inspecoes rejects rascunho plans (400)
  3. PATCH /aprovar transitions status to 'aprovado'
  4. POST /api/inspecoes with approved plan creates execution copying checklist
  5. Execution preserves plano_id, plano_nome, plano_versao
  6. Bulk (5 and 100) questions -> exactly N items
  7. Missing plano_id in InspecaoCreate returns 422
  8. GET /por-ativo returns only 'aprovado' plans
  9. Aprovar without perguntas returns 400
  10. Ronda mode (checklist with 'conforme') auto-concludes
"""
import os
import time
import pytest
import requests

def _load_frontend_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        for line in open(p):
            if line.strip().startswith("REACT_APP_BACKEND_URL="):
                os.environ.setdefault("REACT_APP_BACKEND_URL", line.split("=", 1)[1].strip())
                break
_load_frontend_env()
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
MASTER = {"email": "master@manutrix.com", "password": "master123"}
PREFIX = "TEST_ITER51_"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login", json=MASTER, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def ativo_id(headers):
    r = requests.get(f"{API}/ativos", headers=headers, timeout=30)
    assert r.status_code == 200
    ativos = r.json()
    assert len(ativos) > 0, "No ativos in DB; cannot run test"
    return ativos[0]["id"]


def _get_plan(headers, plan_id):
    """Fetch a single plan via list endpoint (no GET-by-id endpoint exists)."""
    r = requests.get(f"{API}/planos-inspecao", headers=headers, timeout=15)
    r.raise_for_status()
    for p in r.json():
        if p["id"] == plan_id:
            return p
    return None


def _mk_plan(headers, ativo_id, nome_suffix, n_perguntas=3):
    perguntas = [
        {"texto": f"Pergunta {i}", "tipo_campo": "boolean", "obrigatoria": True, "ordem": i}
        for i in range(n_perguntas)
    ]
    payload = {
        "nome": f"{PREFIX}{nome_suffix}",
        "tipo": "inspecao",
        "ativo_id": ativo_id,
        "disciplina": "mecanica",
        "perguntas": perguntas,
    }
    r = requests.post(f"{API}/planos-inspecao", json=payload, headers=headers, timeout=30)
    assert r.status_code in (200, 201), f"Plan create failed: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def created_plans(headers, ativo_id):
    """Track created plans for teardown."""
    created = []
    yield created
    for pid in created:
        try:
            requests.delete(f"{API}/planos-inspecao/{pid}", headers=headers, timeout=15)
        except Exception:
            pass


# ============== TESTS ==============

def test_1_plan_defaults_to_rascunho(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"rascunho_default_{int(time.time())}")
    created_plans.append(plan["id"])
    assert plan.get("status") == "rascunho", f"Expected rascunho, got {plan.get('status')}"


def test_2_inspecao_rejects_rascunho_plan(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"reject_rascunho_{int(time.time())}")
    created_plans.append(plan["id"])
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"]},
        headers=headers, timeout=30,
    )
    assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
    detail = r.json().get("detail", "")
    assert "não está aprovado" in detail or "aprovad" in detail.lower()


def test_3_aprovar_transitions_to_aprovado(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"aprovar_ok_{int(time.time())}")
    created_plans.append(plan["id"])
    r = requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    assert r.status_code == 200, f"Approve failed: {r.status_code} {r.text}"
    assert r.json().get("success") is True
    # Re-fetch and verify
    got = _get_plan(headers, plan["id"])
    assert got is not None
    assert got.get("status") == "aprovado"


def test_4_inspecao_from_approved_plan_copies_checklist(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"exec_copy_{int(time.time())}", n_perguntas=3)
    created_plans.append(plan["id"])
    requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"]},
        headers=headers, timeout=30,
    )
    assert r.status_code in (200, 201), f"Inspecao create failed: {r.status_code} {r.text}"
    insp = r.json()
    assert len(insp.get("checklist", [])) == 3
    # Verify persistence via GET
    got = requests.get(f"{API}/inspecoes/{insp['id']}", headers=headers, timeout=15)
    assert got.status_code == 200
    assert len(got.json().get("checklist", [])) == 3


def test_5_execution_preserves_plano_metadata(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"metadata_{int(time.time())}")
    created_plans.append(plan["id"])
    requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"]},
        headers=headers, timeout=30,
    )
    assert r.status_code in (200, 201)
    insp = r.json()
    assert insp.get("plano_id") == plan["id"]
    assert insp.get("plano_nome") == plan["nome"]
    assert insp.get("plano_versao") == plan.get("versao", 1)


def test_6a_plan_with_5_questions_creates_5_items(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"n5_{int(time.time())}", n_perguntas=5)
    created_plans.append(plan["id"])
    requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"]},
        headers=headers, timeout=30,
    )
    assert r.status_code in (200, 201)
    assert len(r.json()["checklist"]) == 5


def test_6b_plan_with_100_questions_creates_100_items(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"n100_{int(time.time())}", n_perguntas=100)
    created_plans.append(plan["id"])
    requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"]},
        headers=headers, timeout=60,
    )
    assert r.status_code in (200, 201)
    assert len(r.json()["checklist"]) == 100


def test_7_inspecao_without_plano_id_returns_422(headers, ativo_id):
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id},  # missing plano_id
        headers=headers, timeout=30,
    )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    detail = r.json().get("detail", [])
    fields = []
    if isinstance(detail, list):
        for d in detail:
            loc = d.get("loc", [])
            fields.extend(loc)
    assert "plano_id" in fields, f"plano_id not flagged as missing: {detail}"


def test_8_por_ativo_returns_only_aprovado(headers, ativo_id, created_plans):
    """Create one rascunho + one aprovado; GET por-ativo returns only aprovado."""
    ts = int(time.time())
    rascunho = _mk_plan(headers, ativo_id, f"rasc_visibility_{ts}")
    aprovado = _mk_plan(headers, ativo_id, f"apr_visibility_{ts}")
    created_plans.extend([rascunho["id"], aprovado["id"]])
    requests.patch(f"{API}/planos-inspecao/{aprovado['id']}/aprovar", headers=headers, timeout=30)

    r = requests.get(f"{API}/planos-inspecao/por-ativo/{ativo_id}", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    plans = r.json()
    ids = {p["id"] for p in plans}
    statuses = {p.get("status") for p in plans}
    assert aprovado["id"] in ids, "Approved plan missing from por-ativo"
    assert rascunho["id"] not in ids, "Rascunho plan should NOT appear in por-ativo"
    assert statuses == {"aprovado"} or statuses.issubset({"aprovado"}), f"Non-aprovado statuses present: {statuses}"


def test_9_aprovar_plan_without_perguntas_returns_400(headers, ativo_id, created_plans):
    payload = {
        "nome": f"{PREFIX}empty_{int(time.time())}",
        "tipo": "inspecao",
        "ativo_id": ativo_id,
        "disciplina": "mecanica",
        "perguntas": [],
    }
    r = requests.post(f"{API}/planos-inspecao", json=payload, headers=headers, timeout=30)
    assert r.status_code in (200, 201), r.text
    pid = r.json()["id"]
    created_plans.append(pid)
    ra = requests.patch(f"{API}/planos-inspecao/{pid}/aprovar", headers=headers, timeout=30)
    assert ra.status_code == 400, f"Expected 400, got {ra.status_code}: {ra.text}"
    assert "pergunta" in ra.json().get("detail", "").lower()


def test_10_ronda_mode_auto_concludes(headers, ativo_id, created_plans):
    plan = _mk_plan(headers, ativo_id, f"ronda_{int(time.time())}", n_perguntas=3)
    created_plans.append(plan["id"])
    requests.patch(f"{API}/planos-inspecao/{plan['id']}/aprovar", headers=headers, timeout=30)
    # Fetch plan to reuse question ids/order
    plan_full = _get_plan(headers, plan["id"])
    assert plan_full is not None
    # Build filled checklist with 'conforme' responses
    checklist = []
    for p in plan_full["perguntas"]:
        checklist.append({
            "id": p.get("id", ""),
            "descricao": p.get("texto") or p.get("descricao", ""),
            "tipo": "boolean",
            "conforme": True,
            "obrigatorio": True,
        })
    r = requests.post(
        f"{API}/inspecoes",
        json={"ativo_id": ativo_id, "plano_id": plan["id"], "checklist": checklist},
        headers=headers, timeout=30,
    )
    assert r.status_code in (200, 201), r.text
    insp = r.json()
    assert insp.get("status") == "concluida", f"Expected concluida, got {insp.get('status')}"
    assert insp.get("resultado") == "conforme"
    assert insp.get("data_conclusao") is not None
