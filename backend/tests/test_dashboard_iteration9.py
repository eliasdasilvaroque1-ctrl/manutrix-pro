"""
MANUTRIX Dashboard Tests - Iteration 9
Tests for the new executive dashboard with KPIs, charts, and drill-down functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardBackend:
    """Dashboard API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": os.getenv("TEST_ADMIN_PASSWORD", "admin123")
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # === KPIs Endpoint ===
    def test_kpis_endpoint_returns_200(self):
        """GET /api/kpis returns 200"""
        response = requests.get(f"{BASE_URL}/api/kpis", headers=self.headers)
        assert response.status_code == 200
        print("✓ GET /api/kpis returns 200")
    
    def test_kpis_has_required_fields(self):
        """KPIs response has all required fields for dashboard"""
        response = requests.get(f"{BASE_URL}/api/kpis", headers=self.headers)
        data = response.json()
        
        required_fields = [
            'disponibilidade_percent',  # Block 1 - Visão Executiva
            'backlog_total',
            'mtbf_horas',               # Block 2 - Performance
            'mttr_horas',
            'preventivas_percent',
            'corretivas_percent',
            'ativos_total',
            'ativos_operacionais'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ KPIs has all required fields: {list(data.keys())}")
    
    # === Dashboard Stats Endpoint ===
    def test_dashboard_stats_returns_200(self):
        """GET /api/dashboard/stats returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        print("✓ GET /api/dashboard/stats returns 200")
    
    def test_dashboard_stats_has_os_data(self):
        """Dashboard stats has OS data for Block 1 and charts"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        data = response.json()
        
        assert 'ordens_servico' in data
        os_data = data['ordens_servico']
        
        # Required for OS Abertas KPI
        assert 'abertas' in os_data
        assert 'em_execucao' in os_data
        assert 'pausadas' in os_data
        
        # Required for OS distribution chart
        assert 'por_tipo' in os_data
        assert 'corretiva' in os_data['por_tipo']
        assert 'preventiva' in os_data['por_tipo']
        
        # Required for Ordens Críticas KPI
        assert 'por_prioridade' in os_data
        assert 'critica' in os_data['por_prioridade']
        
        print(f"✓ Dashboard stats has OS data: abertas={os_data['abertas']}, criticas={os_data['por_prioridade']['critica']}")
    
    def test_dashboard_stats_has_inspecoes_data(self):
        """Dashboard stats has inspeções data for Block 3"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        data = response.json()
        
        assert 'inspecoes' in data
        insp_data = data['inspecoes']
        
        # Required for Inspeções Pendentes KPI
        assert 'pendentes' in insp_data
        # Required for Não Conformidades KPI
        assert 'nao_conformes_mes' in insp_data
        
        print(f"✓ Dashboard stats has inspeções data: pendentes={insp_data['pendentes']}, nao_conformes={insp_data['nao_conformes_mes']}")
    
    def test_dashboard_stats_has_estoque_data(self):
        """Dashboard stats has estoque data for Block 3"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        data = response.json()
        
        assert 'estoque' in data
        est_data = data['estoque']
        
        # Required for Estoque Crítico KPI
        assert 'criticos' in est_data
        
        print(f"✓ Dashboard stats has estoque data: criticos={est_data['criticos']}")
    
    # === Dashboard Trend Endpoint ===
    def test_dashboard_trend_returns_200(self):
        """GET /api/dashboard/trend returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=self.headers)
        assert response.status_code == 200
        print("✓ GET /api/dashboard/trend returns 200")
    
    def test_dashboard_trend_returns_6_months(self):
        """Dashboard trend returns 6 months of data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=self.headers)
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 6, f"Expected 6 months, got {len(data)}"
        print(f"✓ Dashboard trend returns 6 months of data")
    
    def test_dashboard_trend_has_mtbf_mttr(self):
        """Dashboard trend has MTBF and MTTR for line chart"""
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=self.headers)
        data = response.json()
        
        for month in data:
            assert 'mes' in month, "Missing 'mes' field"
            assert 'mtbf' in month, "Missing 'mtbf' field"
            assert 'mttr' in month, "Missing 'mttr' field"
        
        print(f"✓ Dashboard trend has MTBF/MTTR data for all months")
    
    def test_dashboard_trend_has_os_breakdown(self):
        """Dashboard trend has OS breakdown by type"""
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=self.headers)
        data = response.json()
        
        for month in data:
            assert 'total_os' in month
            assert 'preventivas' in month
            assert 'corretivas' in month
        
        print(f"✓ Dashboard trend has OS breakdown by type")
    
    # === Drill-down Data Endpoints ===
    def test_backlog_drilldown_endpoint(self):
        """GET /api/ordens-servico/backlog returns backlog data"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico/backlog", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Backlog drill-down returns {len(data)} items")
    
    def test_os_list_for_drilldown(self):
        """GET /api/ordens-servico returns OS list for drill-down"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check that we can filter by status for drill-down
        abertas = [o for o in data if o.get('status') in ['aberta', 'planejada', 'em_execucao', 'pausada']]
        criticas = [o for o in data if o.get('prioridade') == 'critica' and o.get('status') not in ['concluida', 'cancelada']]
        
        print(f"✓ OS list for drill-down: {len(abertas)} abertas, {len(criticas)} críticas")
    
    def test_estoque_list_for_drilldown(self):
        """GET /api/estoque returns estoque list for drill-down"""
        response = requests.get(f"{BASE_URL}/api/estoque", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check that we can filter critical items
        criticos = [i for i in data if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
        print(f"✓ Estoque list for drill-down: {len(criticos)} critical items")
    
    def test_inspecoes_list_for_drilldown(self):
        """GET /api/inspecoes returns inspeções list for drill-down"""
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check that we can filter by status
        pendentes = [i for i in data if i.get('status') == 'pendente']
        nao_conformes = [i for i in data if i.get('resultado') == 'nao_conforme']
        
        print(f"✓ Inspeções list for drill-down: {len(pendentes)} pendentes, {len(nao_conformes)} não conformes")
    
    # === Export Endpoints ===
    def test_export_os_excel(self):
        """GET /api/export/ordens-servico?format=excel returns file"""
        response = requests.get(f"{BASE_URL}/api/export/ordens-servico?format=excel", headers=self.headers)
        assert response.status_code == 200
        assert 'application' in response.headers.get('content-type', '')
        print("✓ Export OS Excel works")
    
    def test_export_ativos_excel(self):
        """GET /api/export/ativos?format=excel returns file"""
        response = requests.get(f"{BASE_URL}/api/export/ativos?format=excel", headers=self.headers)
        assert response.status_code == 200
        print("✓ Export Ativos Excel works")


class TestRegressionSidebarNavigation:
    """Regression tests for sidebar navigation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": os.getenv("TEST_ADMIN_PASSWORD", "admin123")
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_ativos_endpoint(self):
        """GET /api/ativos works (Ativos page)"""
        response = requests.get(f"{BASE_URL}/api/ativos", headers=self.headers)
        assert response.status_code == 200
        print("✓ Ativos endpoint works")
    
    def test_os_endpoint(self):
        """GET /api/ordens-servico works (OS page)"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=self.headers)
        assert response.status_code == 200
        print("✓ OS endpoint works")
    
    def test_inspecoes_endpoint(self):
        """GET /api/inspecoes works (Inspeções page)"""
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=self.headers)
        assert response.status_code == 200
        print("✓ Inspeções endpoint works")
    
    def test_estoque_endpoint(self):
        """GET /api/estoque works (Estoque page)"""
        response = requests.get(f"{BASE_URL}/api/estoque", headers=self.headers)
        assert response.status_code == 200
        print("✓ Estoque endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
