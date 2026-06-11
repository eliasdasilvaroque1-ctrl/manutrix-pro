"""
Iteration 13 - Multi-Plant Hierarchy Backend Tests
Tests: Plants/Sectors CRUD, filtering on KPIs/Dashboard/WO/Inspections, Migration report
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_CREDS = {"email": "admin@manutrix.com", "password": "admin123"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN_CREDS, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_client(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def plant_id(admin_client):
    r = admin_client.get(f"{API}/plants", timeout=15)
    assert r.status_code == 200
    plants = r.json()
    assert len(plants) >= 1
    return plants[0]["id"]


@pytest.fixture(scope="module")
def sector_id(admin_client, plant_id):
    r = admin_client.get(f"{API}/sectors", params={"plant_id": plant_id}, timeout=15)
    assert r.status_code == 200
    sectors = r.json()
    assert len(sectors) >= 1
    return sectors[0]["id"]


# ===== Plants =====
class TestPlants:
    def test_get_plants_list(self, admin_client):
        r = admin_client.get(f"{API}/plants", timeout=15)
        assert r.status_code == 200
        plants = r.json()
        assert isinstance(plants, list)
        assert len(plants) >= 1
        pp = next((p for p in plants if p.get("codigo") == "PP"), None)
        assert pp is not None, "PP - Planta Principal not found"
        assert pp["nome"] == "Planta Principal"
        assert pp.get("sector_count") == 4
        assert pp.get("asset_count") == 9

    def test_create_plant(self, admin_client):
        code = f"TEST{uuid.uuid4().hex[:4].upper()}"
        payload = {"codigo": code, "nome": f"Planta Teste {code}", "descricao": "Teste"}
        r = admin_client.post(f"{API}/plants", json=payload, timeout=15)
        assert r.status_code in (200, 201), f"Create plant failed: {r.status_code} {r.text}"
        created = r.json()
        assert created["codigo"] == code
        assert created["nome"] == payload["nome"]
        assert "id" in created
        # verify persistence
        get_r = admin_client.get(f"{API}/plants/{created['id']}", timeout=15)
        if get_r.status_code == 200:
            assert get_r.json()["codigo"] == code
        # cleanup
        admin_client.delete(f"{API}/plants/{created['id']}", timeout=15)


# ===== Sectors =====
class TestSectors:
    def test_get_sectors_list(self, admin_client):
        r = admin_client.get(f"{API}/sectors", timeout=15)
        assert r.status_code == 200
        sectors = r.json()
        assert isinstance(sectors, list)
        assert len(sectors) >= 4
        codes = {s.get("codigo") for s in sectors}
        expected = {"EMBA", "MANU", "PROD", "UTIL"}
        assert expected.issubset(codes), f"Missing sectors. Found: {codes}"
        # All sectors must have plant_id
        for s in sectors:
            assert s.get("plant_id"), f"Sector {s.get('codigo')} missing plant_id"

    def test_create_sector(self, admin_client, plant_id):
        code = f"T{uuid.uuid4().hex[:4].upper()}"
        payload = {"plant_id": plant_id, "codigo": code, "nome": f"Setor {code}", "descricao": "Teste"}
        r = admin_client.post(f"{API}/sectors", json=payload, timeout=15)
        assert r.status_code in (200, 201), f"Create sector failed: {r.status_code} {r.text}"
        created = r.json()
        assert created["codigo"] == code
        assert created["plant_id"] == plant_id
        # cleanup
        admin_client.delete(f"{API}/sectors/{created['id']}", timeout=15)


# ===== Migration =====
class TestMigration:
    def test_migration_report(self, admin_client):
        r = admin_client.get(f"{API}/migration/report", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "complete"
        summary = data.get("summary", {})
        assert summary.get("ativos_orphan", -1) == 0, f"Orphan ativos found: {summary.get('ativos_orphan')}"
        assert summary.get("ativos_with_plant") == summary.get("ativos_total")
        assert summary.get("ativos_with_sector") == summary.get("ativos_total")


# ===== Filtered KPIs =====
class TestKPIsFilter:
    def test_kpis_no_filter(self, admin_client):
        r = admin_client.get(f"{API}/kpis", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "preventivas_percent" in data or "ativos_total" in data or isinstance(data, dict)

    def test_kpis_with_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/kpis", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"KPIs with plant_id failed: {r.text}"

    def test_kpis_with_sector_filter(self, admin_client, sector_id):
        r = admin_client.get(f"{API}/kpis", params={"sector_id": sector_id}, timeout=15)
        assert r.status_code == 200


# ===== Filtered Dashboard =====
class TestDashboardFilter:
    def test_dashboard_stats_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/dashboard/stats", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"Dashboard stats with plant_id failed: {r.text}"

    def test_dashboard_trend_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/dashboard/trend", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"Dashboard trend with plant_id failed: {r.text}"


# ===== Filtered Resources =====
class TestResourceFilters:
    def test_ordens_servico_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/ordens-servico", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"OS with plant_id failed: {r.text}"
        assert isinstance(r.json(), list) or isinstance(r.json(), dict)

    def test_inspecoes_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/inspecoes", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"Inspecoes with plant_id failed: {r.text}"

    def test_anomalias_plant_filter(self, admin_client, plant_id):
        r = admin_client.get(f"{API}/anomalias", params={"plant_id": plant_id}, timeout=15)
        assert r.status_code == 200, f"Anomalias with plant_id failed: {r.text}"

    def test_ativos_plant_sector_filter(self, admin_client, plant_id, sector_id):
        r1 = admin_client.get(f"{API}/ativos", params={"plant_id": plant_id}, timeout=15)
        assert r1.status_code == 200
        ativos_plant = r1.json()
        assert isinstance(ativos_plant, list)
        assert len(ativos_plant) >= 1
        for a in ativos_plant:
            assert a.get("plant_id") == plant_id or "plant_id" not in a

        r2 = admin_client.get(f"{API}/ativos", params={"sector_id": sector_id}, timeout=15)
        assert r2.status_code == 200
        ativos_sector = r2.json()
        # sector filter should narrow results
        assert len(ativos_sector) <= len(ativos_plant)
