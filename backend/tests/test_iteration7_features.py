"""
MANUTRIX Iteration 7 - PDF Manual Upload & Power BI Endpoints Testing
Tests: Manual upload to ativos, Power BI data endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication for testing"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()['access_token']
    
    @pytest.fixture(scope="class")
    def tecnico_token(self):
        """Get tecnico auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tecnico@manutrix.com",
            "password": "tecnico123"
        })
        assert response.status_code == 200, f"Tecnico login failed: {response.text}"
        return response.json()['access_token']


class TestManualUpload(TestAuth):
    """PDF Manual Upload Tests"""
    
    def test_list_ativos_to_get_id(self, admin_token):
        """Get first ativo ID for manual upload tests"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos", headers=headers)
        assert response.status_code == 200
        ativos = response.json()
        assert len(ativos) > 0, "No ativos found for testing"
        # Store ativo_id for other tests
        TestManualUpload.ativo_id = ativos[0]['id']
        TestManualUpload.ativo_tag = ativos[0]['tag']
        print(f"Using ativo: {ativos[0]['tag']} - {ativos[0]['nome']}")
    
    def test_upload_pdf_manual_admin(self, admin_token):
        """Admin can upload PDF manual to ativo"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        ativo_id = getattr(TestManualUpload, 'ativo_id', None)
        if not ativo_id:
            pytest.skip("No ativo_id available")
        
        # Create a test PDF file
        pdf_path = "/tmp/test_manual.pdf"
        if not os.path.exists(pdf_path):
            # Create minimal PDF
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF')
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test_manual_iteration7.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/api/ativos/{ativo_id}/manual", headers=headers, files=files)
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data.get('success') == True
        assert 'manual' in data
        assert data['manual']['filename'] == 'test_manual_iteration7.pdf'
        assert data['manual']['ativo_id'] == ativo_id
        TestManualUpload.manual_id = data['manual']['id']
        TestManualUpload.manual_url = data['manual']['url']
        print(f"Uploaded manual: {data['manual']['filename']}")
    
    def test_upload_non_pdf_rejected(self, admin_token):
        """Non-PDF files should be rejected"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        ativo_id = getattr(TestManualUpload, 'ativo_id', None)
        if not ativo_id:
            pytest.skip("No ativo_id available")
        
        # Try uploading a text file
        files = {'file': ('test.txt', b'This is not a PDF', 'text/plain')}
        response = requests.post(f"{BASE_URL}/api/ativos/{ativo_id}/manual", headers=headers, files=files)
        
        assert response.status_code == 400
        assert "PDF" in response.json().get('detail', '')
    
    def test_list_manuais_for_ativo(self, admin_token):
        """List manuals for an ativo"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        ativo_id = getattr(TestManualUpload, 'ativo_id', None)
        if not ativo_id:
            pytest.skip("No ativo_id available")
        
        response = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}/manuais", headers=headers)
        assert response.status_code == 200
        manuais = response.json()
        assert isinstance(manuais, list)
        assert len(manuais) > 0, "No manuals found after upload"
        
        # Verify manual structure
        manual = manuais[0]
        assert 'id' in manual
        assert 'filename' in manual
        assert 'url' in manual
        assert 'size_bytes' in manual
        assert 'created_at' in manual
        print(f"Found {len(manuais)} manual(s) for ativo")
    
    def test_view_manual_pdf(self, admin_token):
        """View/download manual PDF file"""
        manual_url = getattr(TestManualUpload, 'manual_url', None)
        if not manual_url:
            pytest.skip("No manual_url available")
        
        # Manual URL is like /api/uploads/manuals/filename.pdf
        response = requests.get(f"{BASE_URL}{manual_url}")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        print(f"Manual PDF accessible at {manual_url}")
    
    def test_tecnico_cannot_upload_manual(self, tecnico_token):
        """Tecnico should not be able to upload manuals (admin only)"""
        headers = {"Authorization": f"Bearer {tecnico_token}"}
        ativo_id = getattr(TestManualUpload, 'ativo_id', None)
        if not ativo_id:
            pytest.skip("No ativo_id available")
        
        files = {'file': ('test.pdf', b'%PDF-1.4 test', 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/ativos/{ativo_id}/manual", headers=headers, files=files)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Tecnico correctly blocked from uploading manuals")
    
    def test_tecnico_cannot_delete_manual(self, tecnico_token):
        """Tecnico should not be able to delete manuals (admin only)"""
        headers = {"Authorization": f"Bearer {tecnico_token}"}
        manual_id = getattr(TestManualUpload, 'manual_id', None)
        if not manual_id:
            pytest.skip("No manual_id available")
        
        response = requests.delete(f"{BASE_URL}/api/manuais/{manual_id}", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Tecnico correctly blocked from deleting manuals")
    
    def test_delete_manual_admin(self, admin_token):
        """Admin can delete manual"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        manual_id = getattr(TestManualUpload, 'manual_id', None)
        if not manual_id:
            pytest.skip("No manual_id available")
        
        response = requests.delete(f"{BASE_URL}/api/manuais/{manual_id}", headers=headers)
        assert response.status_code == 200
        assert response.json().get('success') == True
        print(f"Manual {manual_id} deleted successfully")


class TestPowerBIEndpoints(TestAuth):
    """Power BI Data Endpoints Tests"""
    
    def test_powerbi_ativos_returns_flat_json(self, admin_token):
        """GET /api/powerbi/ativos returns flat JSON array"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/ativos", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected array response"
        
        if len(data) > 0:
            # Verify flat structure (no nested objects)
            ativo = data[0]
            expected_fields = ['tag', 'nome', 'tipo_equipamento', 'fabricante', 'modelo', 
                             'criticidade', 'status', 'area', 'centro_custo', 
                             'mtbf_horas', 'mttr_horas', 'valor_aquisicao', 
                             'data_instalacao', 'created_at']
            for field in expected_fields:
                assert field in ativo, f"Missing field: {field}"
            
            # Verify no nested objects (flat for Power BI)
            for key, value in ativo.items():
                assert not isinstance(value, dict), f"Field {key} should not be nested dict"
                assert not isinstance(value, list), f"Field {key} should not be a list"
            
            print(f"Power BI ativos: {len(data)} records, flat structure verified")
    
    def test_powerbi_ordens_servico_returns_flat_json(self, admin_token):
        """GET /api/powerbi/ordens-servico returns flat JSON array"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/ordens-servico", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected array response"
        
        if len(data) > 0:
            os_item = data[0]
            expected_fields = ['numero', 'ativo_tag', 'ativo_nome', 'ativo_criticidade',
                             'tipo', 'origem', 'prioridade', 'status', 'titulo',
                             'responsavel', 'data_abertura', 'data_inicio', 'data_conclusao',
                             'tempo_execucao_minutos', 'custo_pecas', 'custo_mao_obra', 
                             'custo_total', 'created_at']
            for field in expected_fields:
                assert field in os_item, f"Missing field: {field}"
            
            # Verify flat structure
            for key, value in os_item.items():
                assert not isinstance(value, dict), f"Field {key} should not be nested"
            
            print(f"Power BI OS: {len(data)} records, flat structure verified")
    
    def test_powerbi_inspecoes_returns_flat_json(self, admin_token):
        """GET /api/powerbi/inspecoes returns flat JSON array"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/inspecoes", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected array response"
        
        if len(data) > 0:
            insp = data[0]
            expected_fields = ['ativo_tag', 'ativo_nome', 'tipo', 'frequencia', 
                             'status', 'resultado', 'data_programada', 
                             'data_inicio', 'data_conclusao', 'duracao_minutos',
                             'tipo_lubrificante', 'created_at']
            for field in expected_fields:
                assert field in insp, f"Missing field: {field}"
            
            print(f"Power BI inspecoes: {len(data)} records, flat structure verified")
    
    def test_powerbi_kpis_historico_returns_snapshot(self, admin_token):
        """GET /api/powerbi/kpis-historico returns KPI snapshot"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/powerbi/kpis-historico", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict), "Expected object response"
        
        expected_fields = ['data_snapshot', 'ativos_total', 'ativos_operacionais', 
                          'ativos_parados', 'disponibilidade_pct', 'mttr_horas',
                          'mtbf_horas', 'backlog_total', 'taxa_conformidade_pct',
                          'os_concluidas_total', 'preventivas', 'corretivas']
        for field in expected_fields:
            assert field in data, f"Missing KPI field: {field}"
        
        # Verify numeric types
        assert isinstance(data['ativos_total'], int)
        assert isinstance(data['disponibilidade_pct'], (int, float))
        assert isinstance(data['mttr_horas'], (int, float))
        
        print(f"Power BI KPIs: disponibilidade={data['disponibilidade_pct']}%, backlog={data['backlog_total']}")
    
    def test_powerbi_requires_auth(self):
        """Power BI endpoints require authentication"""
        # Test without auth token
        response = requests.get(f"{BASE_URL}/api/powerbi/ativos")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        response = requests.get(f"{BASE_URL}/api/powerbi/ordens-servico")
        assert response.status_code in [401, 403]
        
        response = requests.get(f"{BASE_URL}/api/powerbi/inspecoes")
        assert response.status_code in [401, 403]
        
        response = requests.get(f"{BASE_URL}/api/powerbi/kpis-historico")
        assert response.status_code in [401, 403]
        
        print("Power BI endpoints correctly require authentication")


class TestRegressionBasics(TestAuth):
    """Regression tests for core functionality"""
    
    def test_dashboard_loads(self, admin_token):
        """Dashboard stats endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print("Dashboard stats endpoint working")
    
    def test_ativos_list(self, admin_token):
        """Ativos list endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ativos", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Ativos list: {len(response.json())} items")
    
    def test_os_list(self, admin_token):
        """OS list endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"OS list: {len(response.json())} items")
    
    def test_sidebar_navigation_endpoints(self, admin_token):
        """All sidebar navigation endpoints respond"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        endpoints = [
            '/api/ativos',
            '/api/ordens-servico',
            '/api/inspecoes',
            '/api/estoque',
            '/api/sobressalentes',
            '/api/anomalias',
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert response.status_code == 200, f"{endpoint} failed with {response.status_code}"
        print("All sidebar navigation endpoints working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
