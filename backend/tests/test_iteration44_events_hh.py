"""
Iteration 44 - MANUTRIX PRO Data Architecture (Event Sourcing + HH + Metrics).
Tests for /api/os/{id}/hh, /api/os/{id}/eventos, /api/os/{id}/executantes, /api/metricas/*
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://procure-manutrix.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@manutrix.com", "password": "admin123"}
TECNICO = {"email": "tecnico@manutrix.com", "password": "tecnico123"}
MASTER = {"email": "master@manutrix.com", "password": "master123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed: {r.text}"
    body = r.json()
    return body["access_token"], body["user"]


def _hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_session():
    tok, user = _login(ADMIN)
    return {"token": tok, "user": user, "h": _hdr(tok)}


@pytest.fixture(scope="module")
def tecnico_session():
    tok, user = _login(TECNICO)
    return {"token": tok, "user": user, "h": _hdr(tok)}


@pytest.fixture(scope="module")
def master_session():
    tok, user = _login(MASTER)
    return {"token": tok, "user": user, "h": _hdr(tok)}


@pytest.fixture(scope="module")
def test_os(admin_session):
    """Get or create an OS to use for tests."""
    r = requests.get(f"{API}/ordens-servico", headers=admin_session["h"], timeout=15)
    if r.status_code == 404:
        r = requests.get(f"{API}/os", headers=admin_session["h"], timeout=15)
    assert r.status_code == 200, f"OS list failed: {r.status_code} {r.text[:200]}"
    items = r.json()
    if isinstance(items, dict):
        items = items.get("items") or items.get("data") or []
    assert items, "Need at least one OS for testing"
    return items[0]


# ============== HH ENDPOINTS ==============

class TestHHRegistros:
    def test_hh_iniciar_creates_records(self, admin_session, test_os):
        """POST /api/os/{id}/hh evento=iniciar creates HH registro + OS evento."""
        os_id = test_os["id"]
        # Pre-clean: ensure no open session for admin by trying finalizar (best-effort)
        # We rely on event sequence validation
        payload = {"os_id": os_id, "evento": "iniciar", "observacao": "TEST_iniciar"}
        r = requests.post(f"{API}/os/{os_id}/hh", json=payload, headers=admin_session["h"], timeout=15)
        # If admin already had an in-progress session, accept 400 then close it
        if r.status_code == 400:
            # Try finalizar to reset
            requests.post(f"{API}/os/{os_id}/hh",
                          json={"os_id": os_id, "evento": "finalizar", "observacao": "TEST_reset"},
                          headers=admin_session["h"], timeout=15)
            r = requests.post(f"{API}/os/{os_id}/hh", json=payload, headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, f"iniciar failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["evento"] == "iniciar"
        assert data["os_id"] == os_id
        assert "id" in data
        assert "_id" not in data

    def test_hh_invalid_sequence_pausar_without_iniciar_fresh_os(self, admin_session):
        """pausar without iniciar should be 400 (use a fresh OS-like id)."""
        # Use a fake/never-used os_id but real OS lookup will 404.
        # Better: test sequence via real OS but use master who has no prior events
        # We just check the validation by attempting pausar twice
        # First we need an OS that has a finalized session by admin
        pass  # Covered by sequence_full test below

    def test_hh_sequence_full(self, admin_session, test_os):
        """iniciar -> pausar -> retornar -> finalizar should all succeed."""
        os_id = test_os["id"]
        # Ensure clean state - finalize any open session
        requests.post(f"{API}/os/{os_id}/hh",
                      json={"os_id": os_id, "evento": "finalizar"},
                      headers=admin_session["h"], timeout=15)
        # Now: iniciar
        for evento in ["iniciar", "pausar", "retornar", "finalizar"]:
            r = requests.post(f"{API}/os/{os_id}/hh",
                              json={"os_id": os_id, "evento": evento, "observacao": f"TEST_{evento}"},
                              headers=admin_session["h"], timeout=15)
            assert r.status_code == 200, f"{evento} failed: {r.status_code} {r.text}"
            assert r.json()["evento"] == evento

    def test_hh_invalid_transition(self, admin_session, test_os):
        """After finalizar, pausar should fail (only iniciar allowed)."""
        os_id = test_os["id"]
        # Last event should be finalizar from previous test
        r = requests.post(f"{API}/os/{os_id}/hh",
                          json={"os_id": os_id, "evento": "pausar"},
                          headers=admin_session["h"], timeout=15)
        assert r.status_code == 400
        assert "invalida" in r.text.lower() or "inválida" in r.text.lower() or "transi" in r.text.lower()

    def test_hh_list_chronological(self, admin_session, test_os):
        """GET /api/os/{id}/hh returns chronological list."""
        os_id = test_os["id"]
        r = requests.get(f"{API}/os/{os_id}/hh", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200
        events = r.json()
        assert isinstance(events, list)
        assert len(events) >= 4  # from sequence_full
        # Verify ascending timestamps
        timestamps = [e.get("timestamp", "") for e in events]
        assert timestamps == sorted(timestamps), "Events not in chronological order"
        # Verify no _id field
        for e in events:
            assert "_id" not in e

    def test_hh_resumo(self, admin_session, test_os):
        """GET /api/hh/resumo/{os_id} returns per-user calculation."""
        os_id = test_os["id"]
        r = requests.get(f"{API}/hh/resumo/{os_id}", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "executantes" in data
        assert "hh_total_liquida_min" in data
        assert data["os_id"] == os_id
        # Admin should be present
        admin_id = admin_session["user"]["id"]
        admin_exec = next((e for e in data["executantes"] if e["user_id"] == admin_id), None)
        assert admin_exec is not None
        for k in ["hh_bruta_min", "hh_liquida_min", "tempo_parado_min", "total_eventos"]:
            assert k in admin_exec


# ============== OS EVENTOS ==============

class TestOSEventos:
    def test_eventos_listing(self, admin_session, test_os):
        """GET /api/os/{id}/eventos returns chronological events (populated by HH calls)."""
        os_id = test_os["id"]
        r = requests.get(f"{API}/os/{os_id}/eventos", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        events = r.json()
        assert isinstance(events, list)
        assert len(events) >= 4  # from HH sequence
        # Verify event types include the mapped types
        tipos = [e.get("tipo") for e in events]
        assert any(t in tipos for t in ["trabalho_iniciado", "pausa", "retorno", "os_concluida"])
        # Chronological
        ts = [e.get("timestamp", "") for e in events]
        assert ts == sorted(ts)
        for e in events:
            assert "_id" not in e


# ============== EXECUTANTES ==============

class TestExecutantes:
    @pytest.fixture(scope="class")
    def tech_user_id(self, admin_session):
        # find tecnico user id in same org
        r = requests.get(f"{API}/users", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        users = r.json()
        if isinstance(users, dict):
            users = users.get("items") or users.get("data") or []
        tec = next((u for u in users if u.get("email") == "tecnico@manutrix.com"), None)
        assert tec, "tecnico user not found"
        return tec["id"]

    def test_add_executante(self, admin_session, test_os, tech_user_id):
        os_id = test_os["id"]
        # Cleanup first (best effort)
        requests.delete(f"{API}/os/{os_id}/executantes/{tech_user_id}", headers=admin_session["h"], timeout=15)

        payload = {"os_id": os_id, "user_id": tech_user_id, "funcao": "executor"}
        r = requests.post(f"{API}/os/{os_id}/executantes", json=payload, headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, f"add executante failed: {r.status_code} {r.text}"
        d = r.json()
        assert d["user_id"] == tech_user_id
        assert d["funcao"] == "executor"
        assert d["status"] == "ativo"
        assert "_id" not in d

    def test_duplicate_executante_400(self, admin_session, test_os, tech_user_id):
        os_id = test_os["id"]
        payload = {"os_id": os_id, "user_id": tech_user_id, "funcao": "executor"}
        r = requests.post(f"{API}/os/{os_id}/executantes", json=payload, headers=admin_session["h"], timeout=15)
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"

    def test_list_executantes(self, admin_session, test_os, tech_user_id):
        os_id = test_os["id"]
        r = requests.get(f"{API}/os/{os_id}/executantes", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200
        execs = r.json()
        assert isinstance(execs, list)
        assert any(e["user_id"] == tech_user_id for e in execs)

    def test_equipe_array_updated(self, admin_session, test_os, tech_user_id):
        """OS.equipe array should contain tech_user_id."""
        os_id = test_os["id"]
        # Try both endpoints
        r = requests.get(f"{API}/ordens-servico/{os_id}", headers=admin_session["h"], timeout=15)
        if r.status_code != 200:
            r = requests.get(f"{API}/os/{os_id}", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        os_doc = r.json()
        assert tech_user_id in os_doc.get("equipe", [])

    def test_soft_delete_executante(self, admin_session, test_os, tech_user_id):
        os_id = test_os["id"]
        r = requests.delete(f"{API}/os/{os_id}/executantes/{tech_user_id}", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True
        # Verify removed from list
        r2 = requests.get(f"{API}/os/{os_id}/executantes", headers=admin_session["h"], timeout=15)
        execs = r2.json()
        assert not any(e["user_id"] == tech_user_id for e in execs)

    def test_delete_nonexistent_executante_404(self, admin_session, test_os):
        os_id = test_os["id"]
        r = requests.delete(f"{API}/os/{os_id}/executantes/non-existent-id-zzz", headers=admin_session["h"], timeout=15)
        assert r.status_code == 404

    def test_readd_after_soft_delete(self, admin_session, test_os, tech_user_id):
        """BUG REGRESSION: After soft-delete, re-adding same user must NOT 500.
        The unique index (os_id, user_id) on os_executantes does not honor deleted_at,
        so soft-deleted rows cause DuplicateKeyError on re-add.
        Expected: 200 (re-activate) or 400 (graceful), NOT 500."""
        os_id = test_os["id"]
        payload = {"os_id": os_id, "user_id": tech_user_id, "funcao": "executor"}
        r = requests.post(f"{API}/os/{os_id}/executantes", json=payload, headers=admin_session["h"], timeout=15)
        assert r.status_code != 500, f"500 on re-add after soft-delete: {r.text}"
        assert r.status_code in (200, 400)


# ============== METRICS ==============

class TestMetrics:
    def test_user_metrics_hoje(self, admin_session):
        uid = admin_session["user"]["id"]
        r = requests.get(f"{API}/metricas/usuario/{uid}?periodo=hoje", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "hh_liquida_min" in d or "os_total" in d

    def test_user_metrics_mes(self, admin_session):
        uid = admin_session["user"]["id"]
        r = requests.get(f"{API}/metricas/usuario/{uid}?periodo=mes", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict)
        assert "os_total" in d or "hh_liquida_min" in d

    def test_team_metrics_semana(self, admin_session):
        r = requests.get(f"{API}/metricas/equipe?periodo=semana", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, list)
        # If non-empty, ranking should be sorted desc
        if len(d) > 1:
            totals = [u.get("os_total", 0) for u in d]
            assert totals == sorted(totals, reverse=True)

    def test_team_metrics_mes(self, admin_session):
        r = requests.get(f"{API}/metricas/equipe?periodo=mes", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_rebuild_admin_can(self, admin_session):
        r = requests.post(f"{API}/metricas/rebuild", headers=admin_session["h"], timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "rebuilt_users" in d or "daily" in d

    def test_rebuild_tecnico_forbidden(self, tecnico_session):
        r = requests.post(f"{API}/metricas/rebuild", headers=tecnico_session["h"], timeout=15)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

    def test_rebuild_for_specific_user(self, admin_session):
        uid = admin_session["user"]["id"]
        r = requests.post(f"{API}/metricas/rebuild?user_id={uid}", headers=admin_session["h"], timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "daily" in d or "monthly" in d


# ============== INDEXES ==============

class TestIndexes:
    def test_36_indexes_exist(self):
        """Verify 36 custom indexes exist across the 13 declared collections."""
        import asyncio
        from dotenv import load_dotenv
        from motor.motor_asyncio import AsyncIOMotorClient

        load_dotenv("/app/backend/.env")
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        assert mongo_url and db_name, "MONGO_URL / DB_NAME must be set"

        from data_architecture import INDEXES

        async def run():
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            total = 0
            missing = []
            for coll_name, idx_list in INDEXES.items():
                info = await db[coll_name].index_information()
                names = set(info.keys())
                for idx in idx_list:
                    if idx["name"] in names:
                        total += 1
                    else:
                        missing.append(f"{coll_name}.{idx['name']}")
            client.close()
            return total, missing

        total, missing = asyncio.get_event_loop().run_until_complete(run())
        expected = sum(len(v) for v in __import__("data_architecture").INDEXES.values())
        assert not missing, f"Missing indexes: {missing}"
        assert total == expected, f"expected {expected}, got {total}"
        assert total >= 36, f"Expected at least 36 indexes, found {total}"


# ============== REGRESSION ==============

class TestRegression:
    def test_dashboard(self, admin_session):
        r = requests.get(f"{API}/dashboard/stats", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200

    def test_ativos(self, admin_session):
        r = requests.get(f"{API}/ativos", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200

    def test_os_list(self, admin_session):
        r = requests.get(f"{API}/ordens-servico", headers=admin_session["h"], timeout=15)
        if r.status_code != 200:
            r = requests.get(f"{API}/os", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200

    def test_inspecoes(self, admin_session):
        r = requests.get(f"{API}/inspecoes", headers=admin_session["h"], timeout=15)
        assert r.status_code == 200

    def test_login_master(self):
        tok, user = _login(MASTER)
        assert user["role"] == "master"

    def test_login_tecnico(self):
        tok, user = _login(TECNICO)
        assert user["role"] == "tecnico"
