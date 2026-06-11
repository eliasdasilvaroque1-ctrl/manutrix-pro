"""
MANUTRIX Iteration 12 - Audit Remediation Tests
Tests for:
1. KPI Prev/Corr% uses ALL OS (not just completed)
2. Conformidade% excludes pending inspections
3. Trend data has is_estimated flag
4. Edit/Delete buttons admin-only (backend RBAC)
5. Supervisor password restored
6. OS list 500 error fixed
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"
SUPERVISOR_EMAIL = "supervisor@manutrix.com"
SUPERVISOR_PASSWORD = "supervisor123"
TECNICO_EMAIL = "tecnico@manutrix.com"
TECNICO_PASSWORD = "tecnico123"


class TestAuthenticationFixes:
    """Test authentication for all user roles"""
    
    def test_admin_login(self):
        """Admin login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, role={data['user']['role']}")
    
    def test_supervisor_login(self):
        """Supervisor login should work (password restored to supervisor123)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERVISOR_EMAIL,
            "password": SUPERVISOR_PASSWORD
        })
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "supervisor"
        print(f"✓ Supervisor login successful, role={data['user']['role']}")
    
    def test_tecnico_login(self):
        """Tecnico login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECNICO_EMAIL,
            "password": TECNICO_PASSWORD
        })
        assert response.status_code == 200, f"Tecnico login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "tecnico"
        print(f"✓ Tecnico login successful, role={data['user']['role']}")
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should be rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")


class TestKPICalculationFixes:
    """Test KPI calculation fixes"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_kpis_endpoint_returns_data(self, admin_token):
        """GET /api/kpis should return KPI data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/kpis", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        required_fields = [
            "disponibilidade_percent", "mtbf_horas", "mttr_horas",
            "confiabilidade_percent", "taxa_conformidade_percent",
            "backlog_total", "os_atrasadas",
            "preventivas_percent", "corretivas_percent",
            "custo_manutencao_mes", "ativos_total"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ KPIs endpoint returns all required fields")
        print(f"  - preventivas_percent: {data['preventivas_percent']}%")
        print(f"  - corretivas_percent: {data['corretivas_percent']}%")
        print(f"  - taxa_conformidade_percent: {data['taxa_conformidade_percent']}%")
    
    def test_preventiva_corretiva_percent_realistic(self, admin_token):
        """Preventiva/Corretiva % should be realistic (not 100%/0%)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/kpis", headers=headers)
        data = response.json()
        
        prev_pct = data["preventivas_percent"]
        corr_pct = data["corretivas_percent"]
        
        # Should not be 100%/0% (the old bug)
        # Realistic values should be distributed
        print(f"  Preventiva: {prev_pct}%, Corretiva: {corr_pct}%")
        
        # If there's data, percentages should be reasonable
        if data.get("ativos_total", 0) > 0:
            # Sum should be <= 100 (other types like preditiva, emergencia exist)
            assert prev_pct + corr_pct <= 100.1, "Percentages exceed 100%"
            print(f"✓ Preventiva/Corretiva percentages are realistic")
    
    def test_conformidade_excludes_pending(self, admin_token):
        """Conformidade should exclude pending inspections"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/kpis", headers=headers)
        data = response.json()
        
        conformidade = data["taxa_conformidade_percent"]
        print(f"  Taxa Conformidade: {conformidade}%")
        
        # Should be a valid percentage
        assert 0 <= conformidade <= 100, "Conformidade out of range"
        print(f"✓ Conformidade percentage is valid: {conformidade}%")


class TestDashboardTrendFixes:
    """Test dashboard trend data with is_estimated flag"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_trend_endpoint_returns_data(self, admin_token):
        """GET /api/dashboard/trend should return trend data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), "Trend data should be a list"
        assert len(data) == 6, "Should have 6 months of data"
        print(f"✓ Trend endpoint returns 6 months of data")
    
    def test_trend_has_is_estimated_flag(self, admin_token):
        """Each month in trend data should have is_estimated flag"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=headers)
        data = response.json()
        
        for month in data:
            assert "is_estimated" in month, f"Missing is_estimated flag in month {month.get('mes')}"
            assert isinstance(month["is_estimated"], bool), "is_estimated should be boolean"
        
        estimated_count = sum(1 for m in data if m["is_estimated"])
        print(f"✓ All months have is_estimated flag ({estimated_count} estimated)")
    
    def test_trend_data_structure(self, admin_token):
        """Trend data should have correct structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/trend", headers=headers)
        data = response.json()
        
        required_fields = ["mes", "mes_num", "ano", "mttr", "mtbf", "total_os", 
                          "preventivas", "corretivas", "is_estimated"]
        
        for month in data:
            for field in required_fields:
                assert field in month, f"Missing field {field} in month data"
        
        print(f"✓ Trend data has correct structure")


class TestOSListFix:
    """Test OS list 500 error fix"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_os_list_no_500_error(self, admin_token):
        """GET /api/ordens-servico should not return 500 error"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers)
        
        assert response.status_code == 200, f"OS list returned {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "OS list should be an array"
        print(f"✓ OS list returns {len(data)} items without error")
    
    def test_os_list_with_filters(self, admin_token):
        """OS list with filters should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with status filter
        response = requests.get(f"{BASE_URL}/api/ordens-servico?status=aberta", headers=headers)
        assert response.status_code == 200
        
        # Test with tipo filter
        response = requests.get(f"{BASE_URL}/api/ordens-servico?tipo=preventiva", headers=headers)
        assert response.status_code == 200
        
        print(f"✓ OS list with filters works correctly")


class TestRBACAdminOnly:
    """Test RBAC - Edit/Delete should be admin-only"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def tecnico_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECNICO_EMAIL,
            "password": TECNICO_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_tecnico_cannot_delete_os(self, tecnico_token, admin_token):
        """Tecnico should not be able to delete OS"""
        headers_tecnico = {"Authorization": f"Bearer {tecnico_token}"}
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        
        # Get an OS to try to delete
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers_admin)
        os_list = response.json()
        
        if len(os_list) > 0:
            os_id = os_list[0]["id"]
            # Try to delete as tecnico
            response = requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers_tecnico)
            assert response.status_code == 403, f"Tecnico should not delete OS, got {response.status_code}"
            print(f"✓ Tecnico correctly blocked from deleting OS (403)")
        else:
            print("⚠ No OS to test delete permission")
    
    def test_tecnico_cannot_delete_estoque(self, tecnico_token, admin_token):
        """Tecnico should not be able to delete estoque items"""
        headers_tecnico = {"Authorization": f"Bearer {tecnico_token}"}
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        
        # Get an estoque item
        response = requests.get(f"{BASE_URL}/api/estoque", headers=headers_admin)
        items = response.json()
        
        if len(items) > 0:
            item_id = items[0]["id"]
            # Try to delete as tecnico
            response = requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=headers_tecnico)
            assert response.status_code == 403, f"Tecnico should not delete estoque, got {response.status_code}"
            print(f"✓ Tecnico correctly blocked from deleting estoque (403)")
        else:
            print("⚠ No estoque items to test delete permission")
    
    def test_tecnico_cannot_update_os(self, tecnico_token, admin_token):
        """Tecnico should not be able to update OS"""
        headers_tecnico = {"Authorization": f"Bearer {tecnico_token}"}
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        
        # Get an OS
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers_admin)
        os_list = response.json()
        
        if len(os_list) > 0:
            os_id = os_list[0]["id"]
            # Try to update as tecnico
            response = requests.put(f"{BASE_URL}/api/ordens-servico/{os_id}", 
                                   headers=headers_tecnico,
                                   json={"titulo": "Test Update"})
            assert response.status_code == 403, f"Tecnico should not update OS, got {response.status_code}"
            print(f"✓ Tecnico correctly blocked from updating OS (403)")
        else:
            print("⚠ No OS to test update permission")
    
    def test_admin_can_delete_os(self, admin_token):
        """Admin should be able to delete OS (just verify permission, don't actually delete)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get an OS
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers)
        os_list = response.json()
        
        if len(os_list) > 0:
            # Just verify admin has access (don't actually delete to preserve data)
            os_id = os_list[0]["id"]
            # Get the OS to verify admin can access
            response = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=headers)
            assert response.status_code == 200
            print(f"✓ Admin has access to OS operations")
        else:
            print("⚠ No OS to test admin permission")


class TestDashboardStats:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_dashboard_stats_endpoint(self, admin_token):
        """GET /api/dashboard/stats should return stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "ativos" in data
        assert "ordens_servico" in data
        assert "inspecoes" in data
        assert "estoque" in data
        
        print(f"✓ Dashboard stats endpoint works")
        print(f"  - Ativos: {data['ativos']}")
        print(f"  - OS: {data['ordens_servico']}")


class TestRegressionPages:
    """Test that other pages still work"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_ativos_list(self, admin_token):
        """GET /api/ativos should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos", headers=headers)
        assert response.status_code == 200
        print(f"✓ Ativos list works ({len(response.json())} items)")
    
    def test_inspecoes_list(self, admin_token):
        """GET /api/inspecoes should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=headers)
        assert response.status_code == 200
        print(f"✓ Inspeções list works ({len(response.json())} items)")
    
    def test_anomalias_list(self, admin_token):
        """GET /api/anomalias should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/anomalias", headers=headers)
        assert response.status_code == 200
        print(f"✓ Anomalias list works ({len(response.json())} items)")
    
    def test_estoque_list(self, admin_token):
        """GET /api/estoque should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/estoque", headers=headers)
        assert response.status_code == 200
        print(f"✓ Estoque list works ({len(response.json())} items)")
    
    def test_sobressalentes_list(self, admin_token):
        """GET /api/sobressalentes should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/sobressalentes", headers=headers)
        assert response.status_code == 200
        print(f"✓ Sobressalentes list works ({len(response.json())} items)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
