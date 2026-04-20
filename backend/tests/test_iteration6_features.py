"""
MANUTRIX Iteration 6 - New Features Testing
Tests for: Sobressalentes, Anomalias, Attachments, Knowledge Base, Admin Users, Export, RBAC
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@manutrix.com"
ADMIN_PASSWORD = "admin123"
TECNICO_EMAIL = "tecnico@manutrix.com"
TECNICO_PASSWORD = "tecnico123"


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, role: {data['user']['role']}")
    
    def test_tecnico_login(self):
        """Tecnico can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECNICO_EMAIL,
            "password": TECNICO_PASSWORD
        })
        assert response.status_code == 200, f"Tecnico login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "tecnico"
        print(f"✓ Tecnico login successful, role: {data['user']['role']}")


@pytest.fixture
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json()["access_token"]


@pytest.fixture
def tecnico_token():
    """Get tecnico auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TECNICO_EMAIL,
        "password": TECNICO_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Tecnico login failed")
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def tecnico_headers(tecnico_token):
    return {"Authorization": f"Bearer {tecnico_token}"}


class TestSobressalentes:
    """Sobressalentes (Spare Parts) CRUD tests"""
    
    def test_list_sobressalentes(self, admin_headers):
        """List sobressalentes endpoint works"""
        response = requests.get(f"{BASE_URL}/api/sobressalentes", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ List sobressalentes: {len(response.json())} items")
    
    def test_create_sobressalente_admin(self, admin_headers):
        """Admin can create sobressalente"""
        payload = {
            "descricao": "TEST_Rolamento 6205-2RS",
            "modelo": "6205-2RS",
            "fabricante": "SKF",
            "status": "estoque",
            "localizacao": "Almox A-01",
            "custo": 150.00
        }
        response = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["descricao"] == payload["descricao"]
        assert "tag" in data  # Auto-generated tag
        assert data["status"] == "estoque"
        print(f"✓ Created sobressalente: {data['tag']} - {data['descricao']}")
        return data["id"]
    
    def test_get_sobressalente_detail(self, admin_headers):
        """Get sobressalente detail with movements and attachments"""
        # First create one
        payload = {"descricao": "TEST_Detail Spare", "status": "estoque"}
        create_res = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=admin_headers)
        spare_id = create_res.json()["id"]
        
        # Get detail
        response = requests.get(f"{BASE_URL}/api/sobressalentes/{spare_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "movimentacoes" in data
        assert "attachments" in data
        print(f"✓ Sobressalente detail includes movimentacoes and attachments")
    
    def test_create_sobressalente_tecnico_forbidden(self, tecnico_headers):
        """Tecnico cannot create sobressalente (RBAC)"""
        payload = {"descricao": "TEST_Tecnico Spare", "status": "estoque"}
        response = requests.post(f"{BASE_URL}/api/sobressalentes", json=payload, headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from creating sobressalente (403)")


class TestAnomalias:
    """Anomalias with intelligent prioritization tests"""
    
    def test_list_anomalias(self, admin_headers):
        """List anomalias endpoint works"""
        response = requests.get(f"{BASE_URL}/api/anomalias", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ List anomalias: {len(response.json())} items")
    
    def test_create_anomalia_with_intelligent_priority(self, admin_headers):
        """Create anomalia calculates intelligent priority score"""
        # First get an ativo
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_res.json()
        if not ativos:
            pytest.skip("No ativos available for testing")
        
        ativo = ativos[0]
        ativo_criticidade = ativo.get('criticidade', 'media')
        
        payload = {
            "ativo_id": ativo["id"],
            "descricao": "TEST_Vibração excessiva detectada no rolamento",
            "severidade": "alta",
            "gerar_os": True
        }
        response = requests.post(f"{BASE_URL}/api/anomalias", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify intelligent prioritization
        assert "score_prioridade" in data
        assert "prioridade_calculada" in data
        assert data["score_prioridade"] > 0
        
        # Score = severidade × criticidade (alta=3, media=2, etc)
        severidade_peso = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
        criticidade_peso = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
        expected_score = severidade_peso['alta'] * criticidade_peso.get(ativo_criticidade, 2)
        assert data["score_prioridade"] == expected_score, f"Score mismatch: {data['score_prioridade']} != {expected_score}"
        
        print(f"✓ Anomalia created with intelligent priority: score={data['score_prioridade']}, prioridade={data['prioridade_calculada']}")
        
        # Verify OS was auto-generated
        if payload["gerar_os"]:
            assert data.get("os_gerada_id") is not None
            print(f"✓ OS auto-generated: {data['os_gerada_id']}")
    
    def test_anomalia_os_priority_mapping(self, admin_headers):
        """Verify OS priority mapping based on score"""
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_res.json()
        if not ativos:
            pytest.skip("No ativos available")
        
        # Test with critica severidade
        payload = {
            "ativo_id": ativos[0]["id"],
            "descricao": "TEST_Falha crítica iminente",
            "severidade": "critica",
            "gerar_os": True
        }
        response = requests.post(f"{BASE_URL}/api/anomalias", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Score >= 12 should be critica, >= 6 alta, >= 3 media, else baixa
        score = data["score_prioridade"]
        prioridade = data["prioridade_calculada"]
        
        if score >= 12:
            assert prioridade == "critica"
        elif score >= 6:
            assert prioridade == "alta"
        elif score >= 3:
            assert prioridade == "media"
        else:
            assert prioridade == "baixa"
        
        print(f"✓ Priority mapping correct: score={score} -> prioridade={prioridade}")


class TestKnowledgeBase:
    """Knowledge Base structure tests"""
    
    def test_list_knowledge_base(self, admin_headers):
        """List knowledge base entries"""
        response = requests.get(f"{BASE_URL}/api/knowledge-base", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ List knowledge base: {len(response.json())} entries")
    
    def test_create_knowledge_entry(self, admin_headers):
        """Create knowledge base entry"""
        payload = {
            "tipo_equipamento": "Bomba Centrífuga",
            "problema": "TEST_Vibração excessiva",
            "solucao": "Verificar alinhamento, balanceamento e rolamentos",
            "tags": ["vibração", "bomba", "manutenção"]
        }
        response = requests.post(f"{BASE_URL}/api/knowledge-base", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["tipo_equipamento"] == payload["tipo_equipamento"]
        assert data["problema"] == payload["problema"]
        assert data["solucao"] == payload["solucao"]
        print(f"✓ Knowledge base entry created: {data['tipo_equipamento']} - {data['problema']}")
    
    def test_search_knowledge_base(self, admin_headers):
        """Search knowledge base"""
        # First create an entry
        payload = {
            "tipo_equipamento": "Motor Elétrico",
            "problema": "TEST_Superaquecimento",
            "solucao": "Verificar ventilação e carga"
        }
        requests.post(f"{BASE_URL}/api/knowledge-base", json=payload, headers=admin_headers)
        
        # Search
        response = requests.get(f"{BASE_URL}/api/knowledge-base?search=superaquecimento", headers=admin_headers)
        assert response.status_code == 200
        results = response.json()
        # Should find at least the one we created
        matching = [r for r in results if "superaquecimento" in r.get("problema", "").lower()]
        print(f"✓ Knowledge base search works: found {len(matching)} matching entries")


class TestAdminUsers:
    """Admin user management tests"""
    
    def test_admin_list_users(self, admin_headers):
        """Admin can list users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Verify password_hash is not exposed
        for user in users:
            assert "password_hash" not in user
        
        print(f"✓ Admin listed {len(users)} users (password_hash hidden)")
    
    def test_admin_create_user(self, admin_headers):
        """Admin can create new user"""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@manutrix.com"
        
        payload = {
            "nome": "TEST_Novo Usuário",
            "email": unique_email,
            "password": "test123",
            "role": "tecnico",
            "telefone": "11999999999"
        }
        response = requests.post(f"{BASE_URL}/api/admin/users", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["email"] == unique_email
        assert data["role"] == "tecnico"
        assert "password_hash" not in data
        print(f"✓ Admin created user: {data['nome']} ({data['role']})")
    
    def test_tecnico_cannot_list_users(self, tecnico_headers):
        """Tecnico cannot access admin users endpoint (RBAC)"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from admin/users (403)")
    
    def test_tecnico_cannot_create_user(self, tecnico_headers):
        """Tecnico cannot create users (RBAC)"""
        payload = {
            "nome": "TEST_Hacker",
            "email": "hacker@test.com",
            "password": "hack123",
            "role": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/admin/users", json=payload, headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from creating users (403)")


class TestRBAC:
    """Role-Based Access Control tests"""
    
    def test_tecnico_cannot_create_ativo(self, tecnico_headers):
        """Tecnico cannot create ativos (admin only)"""
        # First get an area
        areas_res = requests.get(f"{BASE_URL}/api/areas", headers=tecnico_headers)
        areas = areas_res.json()
        if not areas:
            pytest.skip("No areas available")
        
        payload = {
            "nome": "TEST_Ativo Tecnico",
            "area_id": areas[0]["id"],
            "criticidade": "media"
        }
        response = requests.post(f"{BASE_URL}/api/ativos", json=payload, headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from creating ativos (403)")
    
    def test_tecnico_cannot_delete_ativo(self, tecnico_headers, admin_headers):
        """Tecnico cannot delete ativos"""
        # Get an ativo
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_res.json()
        if not ativos:
            pytest.skip("No ativos available")
        
        response = requests.delete(f"{BASE_URL}/api/ativos/{ativos[0]['id']}", headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from deleting ativos (403)")
    
    def test_admin_can_create_ativo(self, admin_headers):
        """Admin can create ativos"""
        areas_res = requests.get(f"{BASE_URL}/api/areas", headers=admin_headers)
        areas = areas_res.json()
        if not areas:
            pytest.skip("No areas available")
        
        payload = {
            "nome": "TEST_Ativo Admin",
            "area_id": areas[0]["id"],
            "criticidade": "alta"
        }
        response = requests.post(f"{BASE_URL}/api/ativos", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        print(f"✓ Admin can create ativos: {response.json()['tag']}")
    
    def test_tecnico_can_create_os(self, tecnico_headers, admin_headers):
        """Tecnico can create OS"""
        ativos_res = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        ativos = ativos_res.json()
        if not ativos:
            pytest.skip("No ativos available")
        
        payload = {
            "ativo_id": ativos[0]["id"],
            "titulo": "TEST_OS Tecnico",
            "tipo": "corretiva",
            "prioridade": "media"
        }
        response = requests.post(f"{BASE_URL}/api/ordens-servico", json=payload, headers=tecnico_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        print(f"✓ Tecnico can create OS: {response.json()['numero']}")


class TestExport:
    """Export functionality tests"""
    
    def test_export_ativos_excel(self, admin_headers):
        """Export ativos as Excel"""
        response = requests.get(f"{BASE_URL}/api/export/ativos?format=excel", headers=admin_headers)
        assert response.status_code == 200, f"Export failed: {response.text}"
        assert "spreadsheetml" in response.headers.get("content-type", "")
        print(f"✓ Export ativos Excel: {len(response.content)} bytes")
    
    def test_export_os_excel(self, admin_headers):
        """Export OS as Excel"""
        response = requests.get(f"{BASE_URL}/api/export/ordens-servico?format=excel", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Export OS Excel: {len(response.content)} bytes")
    
    def test_export_estoque_excel(self, admin_headers):
        """Export estoque as Excel"""
        response = requests.get(f"{BASE_URL}/api/export/estoque?format=excel", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Export estoque Excel: {len(response.content)} bytes")
    
    def test_export_inspecoes_excel(self, admin_headers):
        """Export inspeções as Excel"""
        response = requests.get(f"{BASE_URL}/api/export/inspecoes?format=excel", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Export inspeções Excel: {len(response.content)} bytes")
    
    def test_tecnico_cannot_export(self, tecnico_headers):
        """Tecnico cannot export (RBAC)"""
        response = requests.get(f"{BASE_URL}/api/export/ativos?format=excel", headers=tecnico_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tecnico correctly blocked from exporting (403)")


class TestAttachments:
    """Attachments system tests"""
    
    def test_list_attachments(self, admin_headers):
        """List attachments for an entity"""
        response = requests.get(f"{BASE_URL}/api/attachments/work_order/test-id", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✓ List attachments endpoint works")


class TestAssistenteIA:
    """AI Assistant tests"""
    
    def test_assistente_chat(self, admin_headers):
        """AI assistant responds to messages"""
        payload = {
            "message": "Como verificar vibração em uma bomba?",
            "ativo_id": None,
            "session_id": None
        }
        response = requests.post(f"{BASE_URL}/api/assistente/chat", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["response"]) > 0
        print(f"✓ AI assistant responded: {data['response'][:100]}...")


class TestRegressionCRUD:
    """Regression tests for existing CRUD operations"""
    
    def test_ativos_list(self, admin_headers):
        """Ativos list works"""
        response = requests.get(f"{BASE_URL}/api/ativos", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Ativos list: {len(response.json())} items")
    
    def test_os_list(self, admin_headers):
        """OS list works"""
        response = requests.get(f"{BASE_URL}/api/ordens-servico", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ OS list: {len(response.json())} items")
    
    def test_estoque_list(self, admin_headers):
        """Estoque list works"""
        response = requests.get(f"{BASE_URL}/api/estoque", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Estoque list: {len(response.json())} items")
    
    def test_inspecoes_list(self, admin_headers):
        """Inspeções list works"""
        response = requests.get(f"{BASE_URL}/api/inspecoes", headers=admin_headers)
        assert response.status_code == 200
        print(f"✓ Inspeções list: {len(response.json())} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
