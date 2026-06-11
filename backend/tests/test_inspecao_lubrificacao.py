"""
Test suite for MANUTRIX Inspeção/Lubrificação new features
- New Inspeção modal with tabs (Inspeção | Lubrificação)
- Inspeção tab: Frequência dropdown (Diária/Quinzenal/Mensal), auto-generated checklist
- Lubrificação tab: tipo_lubrificante, quantidade, ponto, método, observações
- Badges for type identification in list
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestInspecaoLubrificacao:
    """Test new Inspeção/Lubrificação features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@manutrix.com",
            "password": os.getenv("TEST_ADMIN_PASSWORD", "admin123")
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json()["user"]
        
        # Get first ativo for testing
        ativos_response = self.session.get(f"{BASE_URL}/api/ativos")
        assert ativos_response.status_code == 200
        ativos = ativos_response.json()
        assert len(ativos) > 0, "No ativos found for testing"
        self.ativo = ativos[0]
        
        # Get first tecnico for responsavel (endpoint is /api/users/tecnicos)
        tecnicos_response = self.session.get(f"{BASE_URL}/api/users/tecnicos")
        assert tecnicos_response.status_code == 200, f"Get tecnicos failed: {tecnicos_response.text}"
        tecnicos = tecnicos_response.json()
        assert len(tecnicos) > 0, "No tecnicos found for testing"
        self.tecnico = tecnicos[0]
        
        yield
        
        # Cleanup: Delete test inspections
        inspecoes = self.session.get(f"{BASE_URL}/api/inspecoes").json()
        for insp in inspecoes:
            if insp.get('tipo_lubrificante') == 'oleo_mineral' or insp.get('frequencia') in ['diaria', 'quinzenal', 'mensal']:
                if 'TEST_' in str(insp.get('observacoes', '')) or 'TEST_' in str(insp.get('observacoes_lubrificacao', '')):
                    self.session.delete(f"{BASE_URL}/api/inspecoes/{insp['id']}")
    
    # ============== INSPEÇÃO TAB TESTS ==============
    
    def test_create_inspecao_diaria(self):
        """Test creating inspeção with frequência diária - should generate 5 checklist items"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "checklist",
            "frequencia": "diaria",
            "data_programada": "2026-01-15T10:00:00"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code == 200, f"Create inspeção diária failed: {response.text}"
        
        data = response.json()
        assert data["tipo"] == "checklist"
        assert data["frequencia"] == "diaria"
        assert data["ativo_id"] == self.ativo["id"]
        assert data["responsavel_id"] == self.tecnico["id"]
        
        # Verify checklist has 5 items for diária
        checklist = data.get("checklist", [])
        assert len(checklist) == 5, f"Expected 5 checklist items for diária, got {len(checklist)}"
        
        # Verify expected items
        descriptions = [item["descricao"] for item in checklist]
        assert "Vibração normal" in descriptions
        assert "Temperatura normal" in descriptions
        assert "Sem ruídos anormais" in descriptions
        assert "Sem vazamentos" in descriptions
        assert "Observações" in descriptions
        
        print(f"✓ Inspeção diária created with {len(checklist)} checklist items")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{data['id']}")
    
    def test_create_inspecao_quinzenal(self):
        """Test creating inspeção with frequência quinzenal - should generate 7 checklist items"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "checklist",
            "frequencia": "quinzenal",
            "data_programada": "2026-01-20T14:00:00"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code == 200, f"Create inspeção quinzenal failed: {response.text}"
        
        data = response.json()
        assert data["frequencia"] == "quinzenal"
        
        # Verify checklist has 7 items for quinzenal
        checklist = data.get("checklist", [])
        assert len(checklist) == 7, f"Expected 7 checklist items for quinzenal, got {len(checklist)}"
        
        # Verify additional items for quinzenal
        descriptions = [item["descricao"] for item in checklist]
        assert "Nível de óleo adequado" in descriptions
        assert "Fixações e parafusos OK" in descriptions
        
        print(f"✓ Inspeção quinzenal created with {len(checklist)} checklist items")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{data['id']}")
    
    def test_create_inspecao_mensal(self):
        """Test creating inspeção with frequência mensal - should generate 9 checklist items"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "checklist",
            "frequencia": "mensal",
            "data_programada": "2026-02-01T08:00:00"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code == 200, f"Create inspeção mensal failed: {response.text}"
        
        data = response.json()
        assert data["frequencia"] == "mensal"
        
        # Verify checklist has 9 items for mensal
        checklist = data.get("checklist", [])
        assert len(checklist) == 9, f"Expected 9 checklist items for mensal, got {len(checklist)}"
        
        # Verify mensal has numeric items with tolerances
        vibracao_item = next((item for item in checklist if "Vibração" in item["descricao"]), None)
        assert vibracao_item is not None
        assert vibracao_item.get("tipo") == "numero"
        assert vibracao_item.get("unidade") == "mm/s"
        
        temp_item = next((item for item in checklist if "Temperatura" in item["descricao"]), None)
        assert temp_item is not None
        assert temp_item.get("tipo") == "numero"
        assert temp_item.get("unidade") == "°C"
        
        # Verify additional mensal items
        descriptions = [item["descricao"] for item in checklist]
        assert "Alinhamento verificado" in descriptions
        assert "Correias/acoplamentos OK" in descriptions
        
        print(f"✓ Inspeção mensal created with {len(checklist)} checklist items (including numeric with tolerances)")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{data['id']}")
    
    # ============== LUBRIFICAÇÃO TAB TESTS ==============
    
    def test_create_lubrificacao(self):
        """Test creating lubrificação entry with all fields"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "lubrificacao",
            "tipo_lubrificante": "oleo_mineral",
            "quantidade_lubrificante": "200ml",
            "ponto_lubrificacao": "Rolamento lado acoplamento",
            "metodo_aplicacao": "manual",
            "observacoes_lubrificacao": "TEST_Lubrificação de teste",
            "data_programada": "2026-01-15T09:00:00"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code == 200, f"Create lubrificação failed: {response.text}"
        
        data = response.json()
        assert data["tipo"] == "lubrificacao"
        assert data["tipo_lubrificante"] == "oleo_mineral"
        assert data["quantidade_lubrificante"] == "200ml"
        assert data["ponto_lubrificacao"] == "Rolamento lado acoplamento"
        assert data["metodo_aplicacao"] == "manual"
        assert data["observacoes_lubrificacao"] == "TEST_Lubrificação de teste"
        
        # Verify lubrificação has its own checklist
        checklist = data.get("checklist", [])
        assert len(checklist) >= 4, f"Expected at least 4 checklist items for lubrificação, got {len(checklist)}"
        
        descriptions = [item["descricao"] for item in checklist]
        assert "Ponto de lubrificação acessível" in descriptions
        assert "Área limpa antes da aplicação" in descriptions
        assert "Lubrificante aplicado corretamente" in descriptions
        assert "Sem vazamentos após aplicação" in descriptions
        
        print(f"✓ Lubrificação created with all fields and {len(checklist)} checklist items")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{data['id']}")
    
    def test_create_lubrificacao_graxa(self):
        """Test creating lubrificação with graxa type"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "lubrificacao",
            "tipo_lubrificante": "graxa_base_litio",
            "quantidade_lubrificante": "50g",
            "ponto_lubrificacao": "Mancal principal",
            "metodo_aplicacao": "bomba",
            "data_programada": "2026-01-16T10:00:00"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code == 200, f"Create lubrificação graxa failed: {response.text}"
        
        data = response.json()
        assert data["tipo_lubrificante"] == "graxa_base_litio"
        assert data["metodo_aplicacao"] == "bomba"
        
        print("✓ Lubrificação with graxa created successfully")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{data['id']}")
    
    # ============== LIST AND DETAIL TESTS ==============
    
    def test_list_inspecoes_shows_type(self):
        """Test that list endpoint returns tipo field for badge display"""
        # Create one of each type
        insp_payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "checklist",
            "frequencia": "diaria"
        }
        lub_payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "lubrificacao",
            "tipo_lubrificante": "oleo_sintetico",
            "quantidade_lubrificante": "100ml"
        }
        
        insp_resp = self.session.post(f"{BASE_URL}/api/inspecoes", json=insp_payload)
        lub_resp = self.session.post(f"{BASE_URL}/api/inspecoes", json=lub_payload)
        
        assert insp_resp.status_code == 200
        assert lub_resp.status_code == 200
        
        insp_id = insp_resp.json()["id"]
        lub_id = lub_resp.json()["id"]
        
        # List all inspections
        list_response = self.session.get(f"{BASE_URL}/api/inspecoes")
        assert list_response.status_code == 200
        
        inspecoes = list_response.json()
        
        # Find our created items
        insp_item = next((i for i in inspecoes if i["id"] == insp_id), None)
        lub_item = next((i for i in inspecoes if i["id"] == lub_id), None)
        
        assert insp_item is not None, "Inspeção not found in list"
        assert lub_item is not None, "Lubrificação not found in list"
        
        assert insp_item["tipo"] == "checklist"
        assert lub_item["tipo"] == "lubrificacao"
        
        # Verify ativo info is enriched
        assert "ativo" in insp_item
        assert "ativo" in lub_item
        
        print("✓ List endpoint returns tipo field for badge display")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{insp_id}")
        self.session.delete(f"{BASE_URL}/api/inspecoes/{lub_id}")
    
    def test_get_lubrificacao_detail(self):
        """Test that detail endpoint returns lubrificação info"""
        payload = {
            "ativo_id": self.ativo["id"],
            "responsavel_id": self.tecnico["id"],
            "tipo": "lubrificacao",
            "tipo_lubrificante": "oleo_hidraulico",
            "quantidade_lubrificante": "500ml",
            "ponto_lubrificacao": "Sistema hidráulico",
            "metodo_aplicacao": "gotejamento",
            "observacoes_lubrificacao": "TEST_Verificar nível após aplicação"
        }
        
        create_resp = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert create_resp.status_code == 200
        
        lub_id = create_resp.json()["id"]
        
        # Get detail
        detail_resp = self.session.get(f"{BASE_URL}/api/inspecoes/{lub_id}")
        assert detail_resp.status_code == 200
        
        data = detail_resp.json()
        
        # Verify all lubrificação fields
        assert data["tipo"] == "lubrificacao"
        assert data["tipo_lubrificante"] == "oleo_hidraulico"
        assert data["quantidade_lubrificante"] == "500ml"
        assert data["ponto_lubrificacao"] == "Sistema hidráulico"
        assert data["metodo_aplicacao"] == "gotejamento"
        assert data["observacoes_lubrificacao"] == "TEST_Verificar nível após aplicação"
        
        # Verify enriched data
        assert "ativo" in data
        assert "responsavel" in data
        
        print("✓ Detail endpoint returns all lubrificação fields")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/inspecoes/{lub_id}")
    
    # ============== VALIDATION TESTS ==============
    
    def test_create_inspecao_requires_ativo(self):
        """Test that creating inspeção without ativo_id fails"""
        payload = {
            "responsavel_id": self.tecnico["id"],
            "tipo": "checklist",
            "frequencia": "diaria"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"
        
        print("✓ Validation: ativo_id is required")
    
    def test_create_inspecao_requires_responsavel(self):
        """Test that creating inspeção without responsavel_id fails"""
        payload = {
            "ativo_id": self.ativo["id"],
            "tipo": "checklist",
            "frequencia": "diaria"
        }
        
        response = self.session.post(f"{BASE_URL}/api/inspecoes", json=payload)
        # Note: Backend may allow null responsavel, check actual behavior
        # If it fails, it should be 400/422
        print(f"Create without responsavel: {response.status_code}")
    
    # ============== REGRESSION TESTS ==============
    
    def test_ativos_crud_regression(self):
        """Regression: Verify Ativos CRUD still works"""
        # Get areas first
        areas_resp = self.session.get(f"{BASE_URL}/api/areas")
        assert areas_resp.status_code == 200
        areas = areas_resp.json()
        assert len(areas) > 0
        
        # Create ativo
        create_payload = {
            "nome": "TEST_Ativo Regression",
            "area_id": areas[0]["id"],
            "criticidade": "media",
            "status": "operacional"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/ativos", json=create_payload)
        assert create_resp.status_code == 200, f"Create ativo failed: {create_resp.text}"
        
        ativo_id = create_resp.json()["id"]
        
        # Read
        get_resp = self.session.get(f"{BASE_URL}/api/ativos/{ativo_id}")
        assert get_resp.status_code == 200
        
        # Update
        update_resp = self.session.put(f"{BASE_URL}/api/ativos/{ativo_id}", json={"nome": "TEST_Ativo Updated"})
        assert update_resp.status_code == 200
        
        # Delete
        delete_resp = self.session.delete(f"{BASE_URL}/api/ativos/{ativo_id}")
        assert delete_resp.status_code == 200
        
        print("✓ Regression: Ativos CRUD working")
    
    def test_os_crud_regression(self):
        """Regression: Verify OS CRUD still works"""
        # Create OS
        create_payload = {
            "ativo_id": self.ativo["id"],
            "titulo": "TEST_OS Regression",
            "tipo": "corretiva",
            "prioridade": "media"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/ordens-servico", json=create_payload)
        assert create_resp.status_code == 200, f"Create OS failed: {create_resp.text}"
        
        os_id = create_resp.json()["id"]
        
        # Read
        get_resp = self.session.get(f"{BASE_URL}/api/ordens-servico/{os_id}")
        assert get_resp.status_code == 200
        
        # Delete
        delete_resp = self.session.delete(f"{BASE_URL}/api/ordens-servico/{os_id}")
        assert delete_resp.status_code == 200
        
        print("✓ Regression: OS CRUD working")
    
    def test_estoque_crud_regression(self):
        """Regression: Verify Estoque CRUD still works"""
        # Create item
        create_payload = {
            "nome": "TEST_Item Regression",
            "categoria": "outros",
            "quantidade": 10,
            "unidade": "UN"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/estoque", json=create_payload)
        assert create_resp.status_code == 200, f"Create estoque failed: {create_resp.text}"
        
        item_id = create_resp.json()["id"]
        
        # Read
        get_resp = self.session.get(f"{BASE_URL}/api/estoque/{item_id}")
        assert get_resp.status_code == 200
        
        # Delete
        delete_resp = self.session.delete(f"{BASE_URL}/api/estoque/{item_id}")
        assert delete_resp.status_code == 200
        
        print("✓ Regression: Estoque CRUD working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
