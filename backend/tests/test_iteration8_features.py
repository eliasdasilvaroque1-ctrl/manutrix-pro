"""
MANUTRIX Iteration 8 - PDF Manuals & AI Assistant Testing
Tests:
- PDF manual upload in ativo creation/edit modal
- PDF view/download/delete on ativo detail page
- AI Assistant page showing available manuals
- Power BI endpoints (regression)
- Dashboard and CRUD regression
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        return data["access_token"]


class TestPDFManuals:
    """PDF Manual upload, view, download, delete tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def ativo_id(self, admin_token):
        """Get first ativo ID for testing"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos", headers=headers)
        assert response.status_code == 200
        ativos = response.json()
        assert len(ativos) > 0, "No ativos found for testing"
        return ativos[0]["id"]
    
    def test_list_manuais_endpoint(self, admin_token, ativo_id):
        """GET /api/ativos/{id}/manuais returns list of manuals"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}/manuais", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # Check structure if manuals exist
        if len(data) > 0:
            manual = data[0]
            assert "id" in manual
            assert "filename" in manual
            assert "url" in manual
            assert "size_bytes" in manual
            print(f"Found {len(data)} manual(s) for ativo {ativo_id}")
    
    def test_upload_pdf_manual(self, admin_token, ativo_id):
        """POST /api/ativos/{id}/manual uploads PDF successfully"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Use test PDF file
        test_pdf_path = "/tmp/test_manual.pdf"
        if not os.path.exists(test_pdf_path):
            pytest.skip("Test PDF not found at /tmp/test_manual.pdf")
        
        with open(test_pdf_path, "rb") as f:
            files = {"file": ("test_upload.pdf", f, "application/pdf")}
            response = requests.post(
                f"{BASE_URL}/api/ativos/{ativo_id}/manual",
                headers=headers,
                files=files
            )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "manual" in data
        assert data["manual"]["filename"] == "test_upload.pdf"
        print(f"Uploaded manual: {data['manual']['filename']}")
        return data["manual"]["id"]
    
    def test_get_manual_file_no_auth(self, admin_token, ativo_id):
        """GET /api/uploads/manuals/{filename} returns PDF without auth"""
        # First get a manual URL
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}/manuais", headers=headers)
        manuais = response.json()
        
        if len(manuais) == 0:
            pytest.skip("No manuals to test file download")
        
        manual = manuais[0]
        url = manual["url"]
        
        # Access without auth
        response = requests.get(f"{BASE_URL}{url}")
        assert response.status_code == 200, f"File access failed: {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PDF file accessible at {url}")
    
    def test_reject_non_pdf_upload(self, admin_token, ativo_id):
        """POST /api/ativos/{id}/manual rejects non-PDF files"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try uploading a text file
        files = {"file": ("test.txt", b"This is not a PDF", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/ativos/{ativo_id}/manual",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 400, f"Should reject non-PDF: {response.text}"
        print("Non-PDF file correctly rejected")
    
    def test_delete_manual_admin_only(self, admin_token, ativo_id):
        """DELETE /api/manuais/{id} works for admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First upload a manual to delete
        test_pdf_path = "/tmp/test_manual.pdf"
        if not os.path.exists(test_pdf_path):
            pytest.skip("Test PDF not found")
        
        with open(test_pdf_path, "rb") as f:
            files = {"file": ("to_delete.pdf", f, "application/pdf")}
            upload_response = requests.post(
                f"{BASE_URL}/api/ativos/{ativo_id}/manual",
                headers=headers,
                files=files
            )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test manual")
        
        manual_id = upload_response.json()["manual"]["id"]
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/manuais/{manual_id}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Manual {manual_id} deleted successfully")


class TestAIAssistant:
    """AI Assistant page tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_assistente_chat_endpoint(self, admin_token):
        """POST /api/assistente/chat works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/assistente/chat",
            headers=headers,
            json={"message": "Olá, como verificar vibração?"}
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        print(f"AI response received: {data['response'][:100]}...")


class TestPowerBIEndpoints:
    """Power BI endpoints regression tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_powerbi_ativos(self, admin_token):
        """GET /api/powerbi/ativos returns flat JSON"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/ativos", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Power BI ativos: {len(data)} records")
    
    def test_powerbi_ordens_servico(self, admin_token):
        """GET /api/powerbi/ordens-servico returns flat JSON"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/ordens-servico", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Power BI OS: {len(data)} records")
    
    def test_powerbi_inspecoes(self, admin_token):
        """GET /api/powerbi/inspecoes returns flat JSON"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/inspecoes", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Power BI inspecoes: {len(data)} records")
    
    def test_powerbi_kpis_historico(self, admin_token):
        """GET /api/powerbi/kpis-historico returns KPI snapshot"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/kpis-historico", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "data_snapshot" in data
        print(f"Power BI KPIs snapshot: {data.get('data_snapshot')}")


class TestDashboardRegression:
    """Dashboard and CRUD regression tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_dashboard_stats(self, admin_token):
        """GET /api/dashboard/stats works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_ativos" in data or "ativos" in data
        print(f"Dashboard stats loaded")
    
    def test_ativos_list(self, admin_token):
        """GET /api/ativos works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Ativos list: {len(data)} items")
    
    def test_os_list(self, admin_token):
        """GET /api/ordens-servico works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"OS list: {len(data)} items")
    
    def test_inspecoes_list(self, admin_token):
        """GET /api/inspecoes works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Inspecoes list: {len(data)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
