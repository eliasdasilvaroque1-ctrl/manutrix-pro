"""
MANUTRIX Iteration 11 - Photo System & Login Page Tests
Tests:
1. Login page - no credentials visible, 'Acessar ambiente de demonstração' button
2. Attachments API - POST, GET, DELETE
3. Photo upload for work orders (Foto Antes/Depois)
4. Photo upload for inspections (Registro Fotográfico)
5. Photo upload for anomalies (Fotos do Problema)
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthAndLogin:
    """Test login functionality"""
    
    def test_admin_login_success(self):
        """Admin login should work with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@manutrix.com"
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, token received")
        return data["access_token"]
    
    def test_tecnico_login_success(self):
        """Tecnico login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tecnico@manutrix.com",
            "password": "tecnico123"
        })
        assert response.status_code == 200, f"Tecnico login failed: {response.text}"
        print(f"✓ Tecnico login successful")
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should be rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print(f"✓ Invalid credentials correctly rejected")


class TestAttachmentsAPI:
    """Test attachments endpoints for photo system"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_os_id(self, auth_headers):
        """Get or create a test work order"""
        # First get an ativo
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers)
        if ativos_res.status_code != 200 or not ativos_res.json():
            pytest.skip("No ativos available for testing")
        ativo_id = ativos_res.json()[0]["id"]
        
        # Create a test OS
        os_data = {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "prioridade": "media",
            "titulo": "TEST_OS_Photo_Test"
        }
        os_res = requests.post(f"{BASE_URL}/api/ordens-servico", json=os_data, headers=auth_headers)
        if os_res.status_code == 200:
            return os_res.json()["id"]
        
        # If creation failed, try to get existing OS
        os_list = requests.get(f"{BASE_URL}/api/ordens-servico", headers=auth_headers)
        if os_list.status_code == 200 and os_list.json():
            return os_list.json()[0]["id"]
        pytest.skip("Could not get or create OS for testing")
    
    @pytest.fixture
    def test_inspecao_id(self, auth_headers):
        """Get or create a test inspection"""
        insp_list = requests.get(f"{BASE_URL}/api/inspecoes", headers=auth_headers)
        if insp_list.status_code == 200 and insp_list.json():
            return insp_list.json()[0]["id"]
        pytest.skip("No inspections available for testing")
    
    @pytest.fixture
    def test_anomalia_id(self, auth_headers):
        """Get or create a test anomaly"""
        anom_list = requests.get(f"{BASE_URL}/api/anomalias", headers=auth_headers)
        if anom_list.status_code == 200 and anom_list.json():
            return anom_list.json()[0]["id"]
        pytest.skip("No anomalies available for testing")
    
    def test_upload_attachment_work_order_foto_antes(self, auth_headers, test_os_id):
        """POST /api/attachments - upload foto_antes for work order"""
        # Create a simple test image (1x1 pixel PNG)
        test_image = io.BytesIO()
        # Minimal PNG file
        test_image.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        test_image.seek(0)
        
        files = {'file': ('test_foto_antes.png', test_image, 'image/png')}
        data = {
            'entity_type': 'work_order',
            'entity_id': test_os_id,
            'categoria': 'foto_antes'
        }
        
        response = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        result = response.json()
        assert result["entity_type"] == "work_order"
        assert result["entity_id"] == test_os_id
        assert result["categoria"] == "foto_antes"
        assert "file_url" in result
        assert "id" in result
        print(f"✓ Foto Antes uploaded successfully: {result['id']}")
        return result["id"]
    
    def test_upload_attachment_work_order_foto_depois(self, auth_headers, test_os_id):
        """POST /api/attachments - upload foto_depois for work order"""
        test_image = io.BytesIO()
        test_image.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        test_image.seek(0)
        
        files = {'file': ('test_foto_depois.png', test_image, 'image/png')}
        data = {
            'entity_type': 'work_order',
            'entity_id': test_os_id,
            'categoria': 'foto_depois'
        }
        
        response = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        result = response.json()
        assert result["categoria"] == "foto_depois"
        print(f"✓ Foto Depois uploaded successfully: {result['id']}")
        return result["id"]
    
    def test_list_attachments_work_order(self, auth_headers, test_os_id):
        """GET /api/attachments/{entity_type}/{entity_id} - list work order attachments"""
        response = requests.get(f"{BASE_URL}/api/attachments/work_order/{test_os_id}", headers=auth_headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        
        attachments = response.json()
        assert isinstance(attachments, list)
        print(f"✓ Listed {len(attachments)} attachments for work order")
        return attachments
    
    def test_upload_attachment_inspection(self, auth_headers, test_inspecao_id):
        """POST /api/attachments - upload photo for inspection"""
        test_image = io.BytesIO()
        test_image.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        test_image.seek(0)
        
        files = {'file': ('test_inspecao.png', test_image, 'image/png')}
        data = {
            'entity_type': 'inspection',
            'entity_id': test_inspecao_id,
            'categoria': 'foto'
        }
        
        response = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        result = response.json()
        assert result["entity_type"] == "inspection"
        print(f"✓ Inspection photo uploaded successfully")
    
    def test_list_attachments_inspection(self, auth_headers, test_inspecao_id):
        """GET /api/attachments/inspection/{id} - list inspection attachments"""
        response = requests.get(f"{BASE_URL}/api/attachments/inspection/{test_inspecao_id}", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Listed inspection attachments")
    
    def test_upload_attachment_anomaly(self, auth_headers, test_anomalia_id):
        """POST /api/attachments - upload photo for anomaly"""
        test_image = io.BytesIO()
        test_image.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        test_image.seek(0)
        
        files = {'file': ('test_anomalia.png', test_image, 'image/png')}
        data = {
            'entity_type': 'anomaly',
            'entity_id': test_anomalia_id,
            'categoria': 'foto'
        }
        
        response = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        result = response.json()
        assert result["entity_type"] == "anomaly"
        print(f"✓ Anomaly photo uploaded successfully")
    
    def test_list_attachments_anomaly(self, auth_headers, test_anomalia_id):
        """GET /api/attachments/anomaly/{id} - list anomaly attachments"""
        response = requests.get(f"{BASE_URL}/api/attachments/anomaly/{test_anomalia_id}", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Listed anomaly attachments")
    
    def test_delete_attachment(self, auth_headers, test_os_id):
        """DELETE /api/attachments/{id} - delete attachment"""
        # First upload a test attachment
        test_image = io.BytesIO()
        test_image.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        test_image.seek(0)
        
        files = {'file': ('test_delete.png', test_image, 'image/png')}
        data = {
            'entity_type': 'work_order',
            'entity_id': test_os_id,
            'categoria': 'foto'
        }
        
        upload_res = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert upload_res.status_code == 200
        attach_id = upload_res.json()["id"]
        
        # Now delete it
        delete_res = requests.delete(f"{BASE_URL}/api/attachments/{attach_id}", headers=auth_headers)
        assert delete_res.status_code == 200, f"Delete failed: {delete_res.text}"
        
        result = delete_res.json()
        assert result["success"] == True
        print(f"✓ Attachment deleted successfully")
    
    def test_invalid_file_type_rejected(self, auth_headers, test_os_id):
        """POST /api/attachments - invalid file type should be rejected"""
        test_file = io.BytesIO(b"This is not an image")
        
        files = {'file': ('test.exe', test_file, 'application/octet-stream')}
        data = {
            'entity_type': 'work_order',
            'entity_id': test_os_id,
            'categoria': 'foto'
        }
        
        response = requests.post(f"{BASE_URL}/api/attachments", files=files, data=data, headers=auth_headers)
        assert response.status_code == 400, f"Should reject invalid file type"
        print(f"✓ Invalid file type correctly rejected")


class TestOSPhotoRequirements:
    """Test OS photo requirements for corretiva type"""
    
    @pytest.fixture
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_corretiva_os_requires_photo_to_close(self, auth_headers):
        """Corretiva OS should require photo attachment to close"""
        # Get an ativo
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers)
        if ativos_res.status_code != 200 or not ativos_res.json():
            pytest.skip("No ativos available")
        ativo_id = ativos_res.json()[0]["id"]
        
        # Create corretiva OS
        os_data = {
            "ativo_id": ativo_id,
            "tipo": "corretiva",
            "prioridade": "media",
            "titulo": "TEST_Corretiva_Photo_Required"
        }
        os_res = requests.post(f"{BASE_URL}/api/ordens-servico", json=os_data, headers=auth_headers)
        if os_res.status_code != 200:
            pytest.skip("Could not create OS")
        os_id = os_res.json()["id"]
        
        # Start the OS
        requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/iniciar", headers=auth_headers)
        
        # Try to close without photo - should fail
        close_res = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/concluir", 
            json={"descricao_servico": "Test service", "tempo_gasto_minutos": 30},
            headers=auth_headers)
        
        # Should fail because no photo attached
        assert close_res.status_code == 400, f"Should require photo for corretiva OS"
        assert "foto" in close_res.json().get("detail", "").lower() or "evidência" in close_res.json().get("detail", "").lower()
        print(f"✓ Corretiva OS correctly requires photo to close")


class TestDashboardRegression:
    """Regression tests for dashboard and navigation"""
    
    @pytest.fixture
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_dashboard_kpis(self, auth_headers):
        """Dashboard KPIs should load"""
        response = requests.get(f"{BASE_URL}/api/kpis", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Dashboard KPIs loaded")
    
    def test_dashboard_stats(self, auth_headers):
        """Dashboard stats should load"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Dashboard stats loaded")
    
    def test_ativos_list(self, auth_headers):
        """Ativos list should load"""
        response = requests.get(f"{BASE_URL}/api/ativos", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Ativos list loaded")
    
    def test_os_list(self, auth_headers):
        """OS list should load"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ OS list loaded")
    
    def test_inspecoes_list(self, auth_headers):
        """Inspecoes list should load"""
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Inspecoes list loaded")
    
    def test_anomalias_list(self, auth_headers):
        """Anomalias list should load"""
        response = requests.get(f"{BASE_URL}/api/anomalias", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Anomalias list loaded")
    
    def test_estoque_list(self, auth_headers):
        """Estoque list should load"""
        response = requests.get(f"{BASE_URL}/api/estoque", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Estoque list loaded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
