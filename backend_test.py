#!/usr/bin/env python3
"""
MANUTRIX Backend API Testing
Tests all critical endpoints for industrial CMMS system
"""

import requests
import json
import sys
from datetime import datetime, timezone

class ManutrixAPITester:
    def __init__(self):
        self.base_url = "https://procure-manutrix.preview.emergentagent.com/api"
        self.token = None
        self.user_id = None
        self.org_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_credentials = {
            "email": "admin@manutrix.com",
            "password": "admin123"
        }
        self.tecnico_credentials = {
            "email": "tecnico@manutrix.com", 
            "password": "tecnico123"
        }

    def log_test(self, name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}: {message}")
        if success:
            self.tests_passed += 1
        return success

    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            default_headers.update(headers)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"

    def test_seed_data(self):
        """Test seed data creation"""
        print("\n🌱 Testing seed data creation...")
        response, error = self.make_request('POST', '/seed')
        
        if error:
            return self.log_test("Seed Data Creation", False, error)
        
        success = response.status_code in [200, 201]
        message = f"Status: {response.status_code}"
        if success and response.status_code == 200:
            try:
                data = response.json()
                if "message" in data:
                    message += f" - {data['message']}"
            except:
                pass
        
        return self.log_test("Seed Data Creation", success, message)

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔐 Testing admin authentication...")
        response, error = self.make_request('POST', '/auth/login', self.admin_credentials)
        
        if error:
            return self.log_test("Admin Login", False, error)
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data['access_token']
                self.user_id = data['user']['id']
                self.org_id = data['user']['organization_id']
                return self.log_test("Admin Login", True, f"Token received, role: {data['user']['role']}")
            except KeyError as e:
                return self.log_test("Admin Login", False, f"Missing field in response: {e}")
        else:
            return self.log_test("Admin Login", False, f"Status: {response.status_code}")

    def test_tecnico_login(self):
        """Test tecnico login"""
        print("\n👨‍🔧 Testing tecnico authentication...")
        response, error = self.make_request('POST', '/auth/login', self.tecnico_credentials)
        
        if error:
            return self.log_test("Tecnico Login", False, error)
        
        success = response.status_code == 200
        message = f"Status: {response.status_code}"
        if success:
            try:
                data = response.json()
                message += f" - Role: {data['user']['role']}"
            except:
                pass
        
        return self.log_test("Tecnico Login", success, message)

    def test_kpis_endpoint(self):
        """Test KPIs endpoint"""
        print("\n📊 Testing KPIs endpoint...")
        response, error = self.make_request('GET', '/kpis')
        
        if error:
            return self.log_test("KPIs Endpoint", False, error)
        
        if response.status_code == 200:
            try:
                data = response.json()
                required_fields = ['mttr_horas', 'mtbf_horas', 'disponibilidade_percent', 
                                 'taxa_conformidade_percent', 'backlog_total', 'os_abertas', 
                                 'inspecoes_pendentes']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return self.log_test("KPIs Endpoint", False, f"Missing fields: {missing_fields}")
                
                return self.log_test("KPIs Endpoint", True, 
                    f"Disponibilidade: {data.get('disponibilidade_percent', 0)}%, "
                    f"MTTR: {data.get('mttr_horas', 0)}h, "
                    f"Backlog: {data.get('backlog_total', 0)}")
            except Exception as e:
                return self.log_test("KPIs Endpoint", False, f"JSON parse error: {e}")
        else:
            return self.log_test("KPIs Endpoint", False, f"Status: {response.status_code}")

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        print("\n📈 Testing dashboard stats...")
        response, error = self.make_request('GET', '/dashboard/stats')
        
        if error:
            return self.log_test("Dashboard Stats", False, error)
        
        if response.status_code == 200:
            try:
                data = response.json()
                required_sections = ['ativos', 'ordens_servico']
                missing = [section for section in required_sections if section not in data]
                
                if missing:
                    return self.log_test("Dashboard Stats", False, f"Missing sections: {missing}")
                
                ativos = data.get('ativos', {})
                os_data = data.get('ordens_servico', {})
                
                return self.log_test("Dashboard Stats", True,
                    f"Ativos: {ativos.get('total', 0)} total, "
                    f"OS: {os_data.get('abertas', 0)} abertas")
            except Exception as e:
                return self.log_test("Dashboard Stats", False, f"Parse error: {e}")
        else:
            return self.log_test("Dashboard Stats", False, f"Status: {response.status_code}")

    def test_ativos_endpoint(self):
        """Test ativos (assets) endpoint"""
        print("\n🏭 Testing ativos endpoint...")
        response, error = self.make_request('GET', '/ativos')
        
        if error:
            return self.log_test("Ativos List", False, error)
        
        if response.status_code == 200:
            try:
                ativos = response.json()
                if not isinstance(ativos, list):
                    return self.log_test("Ativos List", False, "Response is not a list")
                
                if len(ativos) == 0:
                    return self.log_test("Ativos List", False, "No ativos found (expected 7 demo assets)")
                
                # Check first asset structure
                if ativos:
                    ativo = ativos[0]
                    required_fields = ['id', 'tag', 'nome', 'status', 'criticidade']
                    missing = [field for field in required_fields if field not in ativo]
                    
                    if missing:
                        return self.log_test("Ativos List", False, f"Missing fields in ativo: {missing}")
                
                return self.log_test("Ativos List", True, f"{len(ativos)} ativos found")
            except Exception as e:
                return self.log_test("Ativos List", False, f"Parse error: {e}")
        else:
            return self.log_test("Ativos List", False, f"Status: {response.status_code}")

    def test_inspecoes_endpoint(self):
        """Test inspecoes endpoint"""
        print("\n🔍 Testing inspecoes endpoint...")
        response, error = self.make_request('GET', '/inspecoes')
        
        if error:
            return self.log_test("Inspecoes List", False, error)
        
        success = response.status_code == 200
        message = f"Status: {response.status_code}"
        
        if success:
            try:
                inspecoes = response.json()
                message += f" - {len(inspecoes)} inspeções found"
            except:
                message += " - Could not parse response"
        
        return self.log_test("Inspecoes List", success, message)

    def test_ordens_servico_endpoint(self):
        """Test ordens-servico endpoint"""
        print("\n🔧 Testing ordens-servico endpoint...")
        response, error = self.make_request('GET', '/ordens-servico')
        
        if error:
            return self.log_test("OS List", False, error)
        
        success = response.status_code == 200
        message = f"Status: {response.status_code}"
        
        if success:
            try:
                os_list = response.json()
                message += f" - {len(os_list)} ordens de serviço found"
                if os_list:
                    primeiro_os = os_list[0]
                    if 'status' in primeiro_os and 'numero' in primeiro_os:
                        message += f", first OS: {primeiro_os['numero']} ({primeiro_os['status']})"
            except:
                message += " - Could not parse response"
        
        return self.log_test("OS List", success, message)

    def test_rotas_inspecao_endpoint(self):
        """Test rotas-inspecao endpoint"""
        print("\n📋 Testing rotas-inspecao endpoint...")
        response, error = self.make_request('GET', '/rotas-inspecao')
        
        if error:
            return self.log_test("Rotas Inspecao", False, error)
        
        success = response.status_code == 200
        message = f"Status: {response.status_code}"
        
        if success:
            try:
                rotas = response.json()
                message += f" - {len(rotas)} rotas found"
            except:
                message += " - Could not parse response"
        
        return self.log_test("Rotas Inspecao", success, message)

    def test_api_root(self):
        """Test API root endpoint"""
        print("\n🏠 Testing API root...")
        response, error = self.make_request('GET', '/')
        
        if error:
            return self.log_test("API Root", False, error)
        
        success = response.status_code == 200
        message = f"Status: {response.status_code}"
        
        if success:
            try:
                data = response.json()
                if 'message' in data and 'MANUTRIX' in data['message']:
                    message += f" - {data['message']}"
                else:
                    message += " - Response received but unexpected format"
            except:
                message += " - Could not parse response"
        
        return self.log_test("API Root", success, message)

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 60)
        print("MANUTRIX Backend API Testing")
        print("=" * 60)
        
        # Test API availability first
        self.test_api_root()
        
        # Test seed data (optional, may already exist)
        self.test_seed_data()
        
        # Test authentication
        admin_login_success = self.test_admin_login()
        
        if not admin_login_success:
            print("\n❌ Cannot proceed without admin login. Stopping tests.")
            return self.print_summary()
        
        # Test secondary authentication
        self.test_tecnico_login()
        
        # Test all API endpoints
        self.test_kpis_endpoint()
        self.test_dashboard_stats()
        self.test_ativos_endpoint()
        self.test_inspecoes_endpoint()
        self.test_ordens_servico_endpoint()
        self.test_rotas_inspecao_endpoint()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary and return success status"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 Backend tests PASSED! System is ready for frontend testing.")
            return True
        else:
            print("\n⚠️  Backend tests show issues. Frontend testing may be impacted.")
            return False


def main():
    """Main test execution"""
    tester = ManutrixAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())