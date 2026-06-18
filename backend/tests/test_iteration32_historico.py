"""
Iteration 32 - Bloco 5: Histórico do Equipamento com Filtros

Tests GET /api/ativos/{id}/historico endpoint with various filters:
- tipo: os | inspecao | anomalia | material
- status, usuario_id, data_inicio, data_fim
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": "admin@manutrix.com", "password": "admin123"}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    token = r.json().get("token") or r.json().get("access_token")
    assert token, f"No token in response: {r.json()}"
    return token


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def ativo_id(headers):
    """Find an ativo with rich history (preferring AV-01)."""
    r = requests.get(f"{API}/ativos", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    ativos = r.json()
    assert len(ativos) > 0, "No ativos found"
    # prefer AV-01
    for a in ativos:
        if a.get("tag") == "AV-01":
            return a["id"]
    return ativos[0]["id"]


# ---- Basic / unfiltered ----

def test_historico_returns_list_with_events(headers, ativo_id):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    events = r.json()
    assert isinstance(events, list)
    assert len(events) > 0, "Expected at least one event in historico"


def test_historico_event_structure(headers, ativo_id):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, timeout=30)
    assert r.status_code == 200
    events = r.json()
    required = {"tipo_evento", "data", "titulo", "descricao", "status", "usuario"}
    for ev in events:
        missing = required - set(ev.keys())
        assert not missing, f"Event missing fields {missing}: {ev}"


def test_historico_sorted_desc(headers, ativo_id):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, timeout=30)
    events = r.json()
    dates = [e.get("data") or "" for e in events]
    assert dates == sorted(dates, reverse=True), "Events not sorted descending by date"


def test_historico_has_multiple_types(headers, ativo_id):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, timeout=30)
    events = r.json()
    tipos = {e.get("tipo_evento") for e in events}
    # Expect at least 2 different event types in AV-01 seed
    assert len(tipos) >= 2, f"Expected multiple tipo_evento, got {tipos}"


# ---- Filter by tipo ----

@pytest.mark.parametrize("tipo", ["os", "inspecao", "anomalia", "material"])
def test_historico_filter_by_tipo(headers, ativo_id, tipo):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, params={"tipo": tipo}, timeout=30)
    assert r.status_code == 200, r.text
    events = r.json()
    assert isinstance(events, list)
    for ev in events:
        assert ev["tipo_evento"] == tipo, f"Expected only {tipo} events, got {ev['tipo_evento']}"


def test_historico_material_event_fields(headers, ativo_id):
    """Material events must include codigo, quantidade, and OS reference in descricao"""
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, params={"tipo": "material"}, timeout=30)
    assert r.status_code == 200
    events = r.json()
    if not events:
        pytest.skip("No material events present in seed for this ativo")
    for ev in events:
        assert ev["tipo_evento"] == "material"
        assert ev.get("codigo"), f"material event missing codigo: {ev}"
        assert ev.get("quantidade") is not None, f"material event missing quantidade: {ev}"
        desc = ev.get("descricao", "")
        assert "OS #" in desc, f"material descricao should reference OS #: {desc}"


# ---- Filter by status ----

def test_historico_filter_by_status_concluida(headers, ativo_id):
    r = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, params={"status": "concluida"}, timeout=30)
    assert r.status_code == 200, r.text
    events = r.json()
    # Material events have status=None and should not be returned; OS/Inspections with status=concluida pass through
    for ev in events:
        if ev["tipo_evento"] in ("os", "inspecao"):
            assert ev.get("status") == "concluida", f"Expected status=concluida, got {ev.get('status')} for {ev}"


# ---- Filter by date range ----

def test_historico_filter_by_date_range(headers, ativo_id):
    r = requests.get(
        f"{API}/ativos/{ativo_id}/historico",
        headers=headers,
        params={"data_inicio": "2026-01-01", "data_fim": "2026-12-31"},
        timeout=30,
    )
    assert r.status_code == 200
    events = r.json()
    for ev in events:
        d = ev.get("data") or ""
        assert d >= "2026-01-01", f"Event date {d} before data_inicio"
        assert d <= "2026-12-31T23:59:59", f"Event date {d} after data_fim"


def test_historico_date_range_excludes_outside(headers, ativo_id):
    """Filter to far past should return empty list."""
    r = requests.get(
        f"{API}/ativos/{ativo_id}/historico",
        headers=headers,
        params={"data_inicio": "1990-01-01", "data_fim": "1990-12-31"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json() == []


# ---- Filter by usuario_id ----

def test_historico_filter_by_usuario(headers, ativo_id):
    # Get a user id from /api/users
    r = requests.get(f"{API}/users", headers=headers, timeout=30)
    assert r.status_code == 200, r.text
    users = r.json()
    if not users:
        pytest.skip("No users available")
    target = users[0]["id"]
    r2 = requests.get(f"{API}/ativos/{ativo_id}/historico", headers=headers, params={"usuario_id": target}, timeout=30)
    assert r2.status_code == 200, r2.text
    assert isinstance(r2.json(), list)


# ---- Not found ----

def test_historico_404_for_invalid_ativo(headers):
    r = requests.get(f"{API}/ativos/nonexistent-id-zzz/historico", headers=headers, timeout=30)
    assert r.status_code == 404
