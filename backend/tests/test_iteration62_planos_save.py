"""Iteration 62 — Planos de Inspeção: force_override boolean validation, duplicate 409, save flow.

Bug context: onClick={handleSave} was passing React SyntheticEvent as forceOverride arg into the
payload as force_override:<Event>, causing 'Converting circular structure to JSON' on the client.
Fix on line 7117 of App.js: onClick={() => handleSave(false)}.

These backend tests verify:
1) POST /api/planos-inspecao with valid boolean force_override works
2) POST with duplicate (same tipo+disciplina+ativo) returns 409 when force_override=false
3) POST with force_override=true bypasses duplicate check
4) POST with non-boolean force_override (e.g. object/dict) is rejected by Pydantic (422)
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
MASTER_EMAIL = "master@manutrix.com"
MASTER_PASSWORD = "master123"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": MASTER_EMAIL, "password": MASTER_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def ativo_id(client):
    """Pick or create an ativo for duplicate-check tests."""
    r = client.get(f"{BASE_URL}/api/ativos", timeout=15)
    assert r.status_code == 200
    ativos = r.json()
    if isinstance(ativos, dict) and "items" in ativos:
        ativos = ativos["items"]
    if ativos:
        return ativos[0]["id"]
    pytest.skip("No ativos in the org — skipping duplicate-check tests")


@pytest.fixture(scope="module")
def created_ids():
    return []


def _make_payload(nome, ativo_id=None, force_override=False, tipo="inspecao", disciplina="mecanica"):
    return {
        "nome": nome,
        "tipo": tipo,
        "tipo_equipamento": None,
        "categoria": tipo,
        "disciplina": disciplina,
        "ativo_id": ativo_id,
        "force_override": force_override,
        "perguntas": [
            {"descricao": "Pergunta 1", "tipo": "boolean", "obrigatorio": True, "ordem": 0},
            {"descricao": "Pergunta 2", "tipo": "boolean", "obrigatorio": True, "ordem": 1},
            {"descricao": "Pergunta 3 - medida", "tipo": "numero", "obrigatorio": False, "ordem": 2},
        ],
    }


def test_01_create_plano_with_boolean_force_override_false(client, created_ids):
    """Baseline: valid payload with force_override=false → 200 and plan persisted."""
    nome = f"TEST_Plano_{uuid.uuid4().hex[:8]}"
    payload = _make_payload(nome, ativo_id=None, force_override=False)
    r = client.post(f"{BASE_URL}/api/planos-inspecao", json=payload, timeout=15)
    assert r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("nome") == nome
    assert data.get("tipo") == "inspecao"
    assert isinstance(data.get("perguntas"), list) and len(data["perguntas"]) == 3
    assert data.get("status") == "rascunho"
    created_ids.append(data["id"])

    # Verify persisted via GET
    r2 = client.get(f"{BASE_URL}/api/planos-inspecao", timeout=15)
    assert r2.status_code == 200
    rows = r2.json()
    if isinstance(rows, dict) and "items" in rows:
        rows = rows["items"]
    assert any(p["id"] == data["id"] for p in rows), "Created plan not returned in list"


def test_02_duplicate_returns_409(client, ativo_id, created_ids):
    """Same tipo+disciplina+ativo second creation → 409 conflict.

    We use a rare disciplina (e.g. instrumentacao) and force_override=true on the FIRST
    call to guarantee we can seed, then attempt a plain duplicate to trigger the 409.
    """
    unique_disciplina = f"instrumentacao_test_{uuid.uuid4().hex[:6]}"
    payload_a = _make_payload(
        f"TEST_DupA_{uuid.uuid4().hex[:8]}",
        ativo_id=ativo_id,
        force_override=True,  # seed even if something similar exists
        tipo="inspecao",
        disciplina=unique_disciplina,
    )
    r_a = client.post(f"{BASE_URL}/api/planos-inspecao", json=payload_a, timeout=15)
    assert r_a.status_code in (200, 201), r_a.text
    created_ids.append(r_a.json()["id"])

    # Try a duplicate — should 409
    payload_b = _make_payload(
        f"TEST_DupB_{uuid.uuid4().hex[:8]}",
        ativo_id=ativo_id,
        force_override=False,
        tipo="inspecao",
        disciplina=unique_disciplina,
    )
    r_b = client.post(f"{BASE_URL}/api/planos-inspecao", json=payload_b, timeout=15)
    assert r_b.status_code == 409, f"Expected 409, got {r_b.status_code}: {r_b.text}"
    detail = r_b.json().get("detail", {})
    assert detail.get("action_required") == "duplicate_conflict"
    assert "existing_plan_id" in detail


def test_03_force_override_true_bypasses_duplicate(client, ativo_id, created_ids):
    """force_override=true should bypass the duplicate check and create the plan."""
    payload = _make_payload(f"TEST_Override_{uuid.uuid4().hex[:8]}", ativo_id=ativo_id, force_override=True, tipo="inspecao", disciplina="mecanica")
    r = client.post(f"{BASE_URL}/api/planos-inspecao", json=payload, timeout=15)
    assert r.status_code in (200, 201), f"Expected 200/201 with force_override=true, got {r.status_code}: {r.text}"
    created_ids.append(r.json()["id"])


def test_04_force_override_non_boolean_rejected(client):
    """If someone passes an object (e.g. the old React Event bug) as force_override → 422.

    This proves the backend refuses non-boolean force_override values.
    """
    nome = f"TEST_BadOverride_{uuid.uuid4().hex[:8]}"
    payload = _make_payload(nome, ativo_id=None, force_override=False)
    # Simulate the old buggy payload — Event-shaped object
    payload["force_override"] = {
        "type": "click",
        "nativeEvent": {"isTrusted": True},
        "target": {"tagName": "BUTTON"},
    }
    r = client.post(f"{BASE_URL}/api/planos-inspecao", json=payload, timeout=15)
    # Pydantic 2 will coerce dict → bool? no, it should 422. Accept either 422 or 400.
    assert r.status_code in (422, 400), f"Expected 422/400 for non-bool force_override, got {r.status_code}: {r.text[:300]}"


def test_05_update_plano(client, created_ids):
    """PUT /planos-inspecao/{id} should update nome without needing force_override."""
    if not created_ids:
        pytest.skip("No plan created earlier")
    plano_id = created_ids[0]
    new_nome = f"TEST_Updated_{uuid.uuid4().hex[:8]}"
    r = client.put(f"{BASE_URL}/api/planos-inspecao/{plano_id}", json={"nome": new_nome}, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json().get("nome") == new_nome


def test_06_approve_plano(client, created_ids):
    """PATCH /planos-inspecao/{id}/aprovar should set status=aprovado."""
    if not created_ids:
        pytest.skip("No plan created earlier")
    plano_id = created_ids[0]
    r = client.patch(f"{BASE_URL}/api/planos-inspecao/{plano_id}/aprovar", timeout=15)
    assert r.status_code == 200, r.text

    # Verify status
    r2 = client.get(f"{BASE_URL}/api/planos-inspecao", timeout=15)
    rows = r2.json()
    if isinstance(rows, dict) and "items" in rows:
        rows = rows["items"]
    plano = next((p for p in rows if p["id"] == plano_id), None)
    assert plano is not None
    assert plano.get("status") == "aprovado"


def test_99_cleanup(client, created_ids):
    """Soft-delete all TEST_ created plans."""
    for pid in created_ids:
        try:
            client.delete(f"{BASE_URL}/api/planos-inspecao/{pid}", timeout=10)
        except Exception:
            pass
