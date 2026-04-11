"""
MANUTRIX CMMS - Comprehensive Backend API Tests
Tests all CRUD operations for Ativos, Estoque, OS, and Inspeções
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://procure-manutrix.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"
TECNICO_EMAIL = "tecnico@manutrix.com"
TECNICO_PASSWORD = "tecnico123"


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful - role: {data['user']['role']}")
    
    def test_tecnico_login_success(self):
        """Test tecnico login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECNICO_EMAIL,
            "password": TECNICO_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "tecnico"
        print(f"✓ Tecnico login successful - role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture
def tecnico_token():
    """Get tecnico authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TECNICO_EMAIL,
        "password": TECNICO_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Tecnico authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def tecnico_headers(tecnico_token):
    """Headers with tecnico auth"""
    return {
        "Authorization": f"Bearer {tecnico_token}",
        "Content-Type": "application/json"
    }


class TestAtivosCRUD:
    """Ativos (Assets) CRUD tests"""
    
    def test_list_ativos(self, admin_headers):
        """Test listing all ativos"""
        response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} ativos")
    
    def test_list_areas(self, admin_headers):
        """Test listing areas (required for creating ativos)"""
        response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No areas found - seed data may be missing"
        print(f"✓ Listed {len(data)} areas")
        return data
    
    def test_create_ativo_admin(self, admin_headers):
        """Test creating a new ativo as admin"""
        # First get an area
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_response.json()
        assert len(areas) > 0, "No areas available"
        area_id = areas[0]["id"]
        
        # Create ativo
        payload = {
            "nome": "TEST_Bomba Teste",
            "area_id": area_id,
            "tipo_equipamento": "Bomba",
            "fabricante": "Test Fabricante",
            "criticidade": "media",
            "status": "operacional"
        }
        response = requests.post(f"{BASE_URL}/api/ativos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data
        assert data["nome"] == payload["nome"]
        assert "tag" in data  # Auto-generated TAG
        assert "_id" not in data, "MongoDB _id should not be in response"
        
        print(f"✓ Created ativo: {data['tag']} - {data['nome']}")
        return data
    
    def test_get_ativo_by_id(self, admin_headers):
        """Test getting ativo by ID"""
        # First create an ativo
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_response.json()
        area_id = areas[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ativos", json={
            "nome": "TEST_Ativo Get Test",
            "area_id": area_id,
            "criticidade": "alta"
        }, headers=admin_headers)
        created = create_response.json()
        ativo_id = created["id"]
        
        # Get the ativo
        response = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ativo_id
        assert data["nome"] == "TEST_Ativo Get Test"
        assert "_id" not in data
        print(f"✓ Retrieved ativo by ID: {data['tag']}")
    
    def test_update_ativo(self, admin_headers):
        """Test updating an ativo"""
        # Create ativo first
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_response.json()
        area_id = areas[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ativos", json={
            "nome": "TEST_Ativo Update Test",
            "area_id": area_id
        }, headers=admin_headers)
        created = create_response.json()
        ativo_id = created["id"]
        
        # Update the ativo
        update_payload = {
            "nome": "TEST_Ativo Updated Name",
            "status": "manutencao"
        }
        response = requests.put(f"{BASE_URL}/api/ativos/{ativo_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "TEST_Ativo Updated Name"
        assert data["status"] == "manutencao"
        print(f"✓ Updated ativo: {data['tag']} - status: {data['status']}")
    
    def test_delete_ativo_admin(self, admin_headers):
        """Test deleting an ativo as admin"""
        # Create ativo first
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_response.json()
        area_id = areas[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ativos", json={
            "nome": "TEST_Ativo Delete Test",
            "area_id": area_id
        }, headers=admin_headers)
        created = create_response.json()
        ativo_id = created["id"]
        
        # Delete the ativo
        response = requests.delete(f"{BASE_URL}/api/ativos/{ativo_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify deletion (should return 404)
        get_response = requests.get(f"{BASE_URL}/api/ativos/{ativo_id}", headers=admin_headers)
        assert get_response.status_code == 404
        print("✓ Deleted ativo and verified removal")


class TestEstoqueCRUD:
    """Estoque (Inventory) CRUD tests"""
    
    def test_list_estoque(self, admin_headers):
        """Test listing all estoque items"""
        response = requests.get(f"{BASE_URL}/api/estoque", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} estoque items")
    
    def test_create_estoque_item(self, admin_headers):
        """Test creating a new estoque item"""
        payload = {
            "nome": "TEST_Rolamento 6205",
            "categoria": "rolamento",
            "quantidade": 10,
            "estoque_minimo": 5,
            "unidade": "UN",
            "custo_unitario": 45.50,
            "fornecedor": "Test Fornecedor"
        }
        response = requests.post(f"{BASE_URL}/api/estoque", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "sku" in data  # Auto-generated SKU
        assert data["nome"] == payload["nome"]
        assert data["quantidade"] == payload["quantidade"]
        assert "_id" not in data, "MongoDB _id should not be in response"
        
        print(f"✓ Created estoque item: {data['sku']} - {data['nome']}")
        return data
    
    def test_get_estoque_item(self, admin_headers):
        """Test getting estoque item by ID"""
        # Create item first
        create_response = requests.post(f"{BASE_URL}/api/estoque", json={
            "nome": "TEST_Item Get Test",
            "categoria": "mecanica",
            "quantidade": 5
        }, headers=admin_headers)
        created = create_response.json()
        item_id = created["id"]
        
        # Get the item
        response = requests.get(f"{BASE_URL}/api/estoque/{item_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert "_id" not in data
        print(f"✓ Retrieved estoque item: {data['sku']}")
    
    def test_update_estoque_item(self, admin_headers):
        """Test updating an estoque item"""
        # Create item first
        create_response = requests.post(f"{BASE_URL}/api/estoque", json={
            "nome": "TEST_Item Update Test",
            "quantidade": 10
        }, headers=admin_headers)
        created = create_response.json()
        item_id = created["id"]
        
        # Update the item
        update_payload = {
            "quantidade": 25,
            "custo_unitario": 100.00
        }
        response = requests.put(f"{BASE_URL}/api/estoque/{item_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["quantidade"] == 25
        assert data["custo_unitario"] == 100.00
        print(f"✓ Updated estoque item: qty={data['quantidade']}, cost={data['custo_unitario']}")
    
    def test_delete_estoque_item(self, admin_headers):
        """Test deleting an estoque item"""
        # Create item first
        create_response = requests.post(f"{BASE_URL}/api/estoque", json={
            "nome": "TEST_Item Delete Test",
            "quantidade": 5
        }, headers=admin_headers)
        created = create_response.json()
        item_id = created["id"]
        
        # Delete the item
        response = requests.delete(f"{BASE_URL}/api/estoque/{item_id}", headers=admin_headers)
        assert response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/estoque/{item_id}", headers=admin_headers)
        assert get_response.status_code == 404
        print("✓ Deleted estoque item and verified removal")


class TestOSCRUD:
    """Ordens de Serviço (Work Orders) CRUD tests"""
    
    def test_list_os(self, admin_headers):
        """Test listing all OS"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} ordens de serviço")
    
    def test_create_os_with_falha_tipo(self, admin_headers):
        """Test creating OS with 'falha' tipo (P0 requirement)"""
        # Get an ativo first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        assert len(ativos) > 0, "No ativos available"
        ativo_id = ativos[0]["id"]
        
        # Create OS with tipo='falha'
        payload = {
            "ativo_id": ativo_id,
            "titulo": "TEST_OS Falha Test",
            "tipo": "falha",  # P0 requirement - FALHA enum
            "prioridade": "alta",
            "descricao": "Teste de OS com tipo falha"
        }
        response = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "numero" in data  # Auto-generated OS number
        assert data["tipo"] == "falha"
        assert data["titulo"] == payload["titulo"]
        assert "_id" not in data, "MongoDB _id should not be in response"
        
        print(f"✓ Created OS with tipo='falha': {data['numero']} - {data['titulo']}")
        return data
    
    def test_create_os_all_tipos(self, admin_headers):
        """Test creating OS with all tipo options"""
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        tipos = ["preventiva", "corretiva", "preditiva", "emergencia", "falha"]
        
        for tipo in tipos:
            payload = {
                "ativo_id": ativo_id,
                "titulo": f"TEST_OS {tipo.capitalize()} Test",
                "tipo": tipo,
                "prioridade": "media"
            }
            response = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=admin_headers)
            assert response.status_code == 200, f"Create failed for tipo={tipo}: {response.text}"
            data = response.json()
            assert data["tipo"] == tipo
            print(f"  ✓ Created OS with tipo='{tipo}'")
        
        print(f"✓ All {len(tipos)} OS tipos working correctly")
    
    def test_get_os_by_id(self, admin_headers):
        """Test getting OS by ID"""
        # Create OS first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ordens-servico", json={
            "ativo_id": ativo_id,
            "titulo": "TEST_OS Get Test",
            "tipo": "corretiva"
        }, headers=admin_headers)
        created = create_response.json()
        os_id = created["id"]
        
        # Get the OS
        response = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == os_id
        assert "_id" not in data
        print(f"✓ Retrieved OS: {data['numero']}")
    
    def test_update_os(self, admin_headers):
        """Test updating an OS"""
        # Create OS first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ordens-servico", json={
            "ativo_id": ativo_id,
            "titulo": "TEST_OS Update Test",
            "tipo": "corretiva"
        }, headers=admin_headers)
        created = create_response.json()
        os_id = created["id"]
        
        # Update the OS
        update_payload = {
            "titulo": "TEST_OS Updated Title",
            "prioridade": "critica",
            "status": "planejada"
        }
        response = requests.put(f"{BASE_URL}/api/ordens-servico/{os_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == "TEST_OS Updated Title"
        assert data["prioridade"] == "critica"
        print(f"✓ Updated OS: {data['numero']} - prioridade: {data['prioridade']}")
    
    def test_os_workflow(self, admin_headers):
        """Test OS workflow: create -> iniciar -> concluir"""
        # Create OS
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ordens-servico", json={
            "ativo_id": ativo_id,
            "titulo": "TEST_OS Workflow Test",
            "tipo": "corretiva"
        }, headers=admin_headers)
        created = create_response.json()
        os_id = created["id"]
        assert created["status"] == "aberta"
        print(f"  ✓ Created OS: {created['numero']} - status: aberta")
        
        # Iniciar OS
        iniciar_response = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/iniciar", headers=admin_headers)
        assert iniciar_response.status_code == 200
        print("  ✓ Iniciou OS - status: em_execucao")
        
        # Concluir OS
        concluir_response = requests.post(f"{BASE_URL}/api/ordens-servico/{os_id}/concluir", 
            json={"observacoes": "Teste concluído"},
            headers=admin_headers)
        assert concluir_response.status_code == 200
        print("  ✓ Concluiu OS - status: concluida")
        
        # Verify final status
        get_response = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        final_data = get_response.json()
        assert final_data["status"] == "concluida"
        print(f"✓ OS workflow completed: {final_data['numero']}")
    
    def test_delete_os_admin(self, admin_headers):
        """Test deleting an OS as admin"""
        # Create OS first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ordens-servico", json={
            "ativo_id": ativo_id,
            "titulo": "TEST_OS Delete Test",
            "tipo": "corretiva"
        }, headers=admin_headers)
        created = create_response.json()
        os_id = created["id"]
        
        # Delete the OS
        response = requests.delete(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        assert response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/ordens-servico/{os_id}", headers=admin_headers)
        assert get_response.status_code == 404
        print("✓ Deleted OS and verified removal")


class TestInspecoesCRUD:
    """Inspeções (Inspections) CRUD tests"""
    
    def test_list_inspecoes(self, admin_headers):
        """Test listing all inspeções"""
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} inspeções")
    
    def test_list_tecnicos(self, admin_headers):
        """Test listing tecnicos (required for creating inspeções)"""
        response = requests.get(f"{BASE_URL}/api/users/tecnicos", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} tecnicos")
        return data
    
    def test_create_inspecao(self, admin_headers):
        """Test creating a new inspeção"""
        # Get ativo and tecnico
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        assert len(ativos) > 0, "No ativos available"
        ativo_id = ativos[0]["id"]
        
        tecnicos_response = requests.get(f"{BASE_URL}/api/users/tecnicos", headers=admin_headers)
        tecnicos = tecnicos_response.json()
        assert len(tecnicos) > 0, "No tecnicos available"
        responsavel_id = tecnicos[0]["id"]
        
        # Create inspeção
        payload = {
            "ativo_id": ativo_id,
            "responsavel_id": responsavel_id,
            "tipo": "checklist"
        }
        response = requests.post(f"{BASE_URL}/api/inspecoes", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["ativo_id"] == ativo_id
        assert data["responsavel_id"] == responsavel_id
        assert data["status"] == "pendente"
        assert "checklist" in data
        assert "_id" not in data, "MongoDB _id should not be in response"
        
        print(f"✓ Created inspeção: {data['id'][:8]}... - status: {data['status']}")
        return data
    
    def test_get_inspecao_by_id(self, admin_headers):
        """Test getting inspeção by ID"""
        # Create inspeção first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        tecnicos_response = requests.get(f"{BASE_URL}/api/users/tecnicos", headers=admin_headers)
        tecnicos = tecnicos_response.json()
        responsavel_id = tecnicos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/inspecoes", json={
            "ativo_id": ativo_id,
            "responsavel_id": responsavel_id
        }, headers=admin_headers)
        created = create_response.json()
        inspecao_id = created["id"]
        
        # Get the inspeção
        response = requests.get(f"{BASE_URL}/api/inspecoes/{inspecao_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inspecao_id
        assert "_id" not in data
        print(f"✓ Retrieved inspeção: {data['id'][:8]}...")
    
    def test_inspecao_workflow(self, admin_headers):
        """Test inspeção workflow: create -> iniciar -> concluir"""
        # Create inspeção
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        tecnicos_response = requests.get(f"{BASE_URL}/api/users/tecnicos", headers=admin_headers)
        tecnicos = tecnicos_response.json()
        responsavel_id = tecnicos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/inspecoes", json={
            "ativo_id": ativo_id,
            "responsavel_id": responsavel_id
        }, headers=admin_headers)
        created = create_response.json()
        inspecao_id = created["id"]
        assert created["status"] == "pendente"
        print(f"  ✓ Created inspeção - status: pendente")
        
        # Iniciar inspeção
        iniciar_response = requests.post(f"{BASE_URL}/api/inspecoes/{inspecao_id}/iniciar", headers=admin_headers)
        assert iniciar_response.status_code == 200
        print("  ✓ Iniciou inspeção - status: em_andamento")
        
        # Concluir inspeção with checklist
        checklist = [
            {"id": "1", "descricao": "Vibração OK", "tipo": "boolean", "conforme": True},
            {"id": "2", "descricao": "Temperatura OK", "tipo": "boolean", "conforme": True},
            {"id": "3", "descricao": "Ruído OK", "tipo": "boolean", "conforme": True}
        ]
        concluir_response = requests.post(f"{BASE_URL}/api/inspecoes/{inspecao_id}/concluir", 
            json={"checklist": checklist, "observacoes": "Teste concluído"},
            headers=admin_headers)
        assert concluir_response.status_code == 200, f"Concluir failed: {concluir_response.text}"
        concluir_data = concluir_response.json()
        assert concluir_data["resultado"] == "conforme"
        print(f"  ✓ Concluiu inspeção - resultado: {concluir_data['resultado']}")
        
        print(f"✓ Inspeção workflow completed")
    
    def test_delete_inspecao(self, admin_headers):
        """Test deleting an inspeção"""
        # Create inspeção first
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        tecnicos_response = requests.get(f"{BASE_URL}/api/users/tecnicos", headers=admin_headers)
        tecnicos = tecnicos_response.json()
        responsavel_id = tecnicos[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/inspecoes", json={
            "ativo_id": ativo_id,
            "responsavel_id": responsavel_id
        }, headers=admin_headers)
        created = create_response.json()
        inspecao_id = created["id"]
        
        # Delete the inspeção
        response = requests.delete(f"{BASE_URL}/api/inspecoes/{inspecao_id}", headers=admin_headers)
        assert response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/inspecoes/{inspecao_id}", headers=admin_headers)
        assert get_response.status_code == 404
        print("✓ Deleted inspeção and verified removal")


class TestRBACPermissions:
    """Role-Based Access Control tests"""
    
    def test_tecnico_cannot_delete_ativo(self, tecnico_headers, admin_headers):
        """Test that tecnico cannot delete ativos (admin only)"""
        # Create ativo as admin
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_response.json()
        area_id = areas[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/api/ativos", json={
            "nome": "TEST_RBAC Delete Test",
            "area_id": area_id
        }, headers=admin_headers)
        created = create_response.json()
        ativo_id = created["id"]
        
        # Try to delete as tecnico
        response = requests.delete(f"{BASE_URL}/api/ativos/{ativo_id}", headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly denied delete permission on ativos")
        
        # Cleanup as admin
        requests.delete(f"{BASE_URL}/api/ativos/{ativo_id}", headers=admin_headers)
    
    def test_tecnico_can_create_os(self, tecnico_headers, admin_headers):
        """Test that tecnico can create OS"""
        ativos_response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_response.json()
        ativo_id = ativos[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/ordens-servico", json={
            "ativo_id": ativo_id,
            "titulo": "TEST_Tecnico OS Test",
            "tipo": "corretiva"
        }, headers=tecnico_headers)
        assert response.status_code == 200, f"Tecnico should be able to create OS: {response.text}"
        print("✓ Tecnico can create OS")
    
    def test_admin_full_access(self, admin_headers):
        """Test that admin has full access to all operations"""
        # Get areas
        areas_response = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        assert areas_response.status_code == 200
        areas = areas_response.json()
        area_id = areas[0]["id"]
        
        # Create ativo
        create_response = requests.post(f"{BASE_URL}/api/ativos", json={
            "nome": "TEST_Admin Full Access",
            "area_id": area_id
        }, headers=admin_headers)
        assert create_response.status_code == 200
        ativo_id = create_response.json()["id"]
        
        # Update ativo
        update_response = requests.put(f"{BASE_URL}/api/ativos/{ativo_id}", json={
            "status": "parado"
        }, headers=admin_headers)
        assert update_response.status_code == 200
        
        # Delete ativo
        delete_response = requests.delete(f"{BASE_URL}/api/ativos/{ativo_id}", headers=admin_headers)
        assert delete_response.status_code == 200
        
        print("✓ Admin has full CRUD access")


class TestDashboardKPIs:
    """Dashboard and KPIs tests"""
    
    def test_kpis_endpoint(self, admin_headers):
        """Test KPIs endpoint"""
        response = requests.get(f"{BASE_URL}/api/kpis", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify KPI fields
        assert "disponibilidade_percent" in data
        assert "mtbf_horas" in data
        assert "mttr_horas" in data
        assert "backlog_total" in data
        
        print(f"✓ KPIs: Disponibilidade={data['disponibilidade_percent']}%, MTTR={data['mttr_horas']}h, Backlog={data['backlog_total']}")
    
    def test_dashboard_stats(self, admin_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "ativos" in data
        assert "ordens_servico" in data
        assert "inspecoes" in data
        
        # Get total from ativos dict
        ativos_total = data['ativos'].get('total', sum(data['ativos'].values()) if isinstance(data['ativos'], dict) else 0)
        os_info = data['ordens_servico']
        print(f"✓ Dashboard stats: ativos={data['ativos']}, OS={os_info}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
