#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta

class ACCTAAPITester:
    def __init__(self, base_url="https://controladores-cv.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user_id = None
        self.admin_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        elif self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            print(f"   Status: {response.status_code}")
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_register_users(self):
        """Register test users"""
        print("\n📝 Registering test users...")
        
        # Regular user
        user_data = {
            "name": "Sócio Teste",
            "email": "socio1@accta.cv",
            "password": "socio123",
            "role": "socio",
            "status": "ativo",
            "member_id": "ACCTA001",
            "license_number": "LIC001",
            "phone_number": "+238 999 1234",
            "consent_data": True
        }
        
        success1, response1 = self.run_test(
            "Register Regular User",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        # Admin user
        admin_data = {
            "name": "Admin ACCTA",
            "email": "admin@accta.cv",
            "password": "admin123",
            "role": "admin",
            "status": "ativo",
            "member_id": "ACCTA-ADMIN",
            "phone_number": "+238 999 0000",
            "consent_data": True
        }
        
        success2, response2 = self.run_test(
            "Register Admin User",
            "POST",
            "auth/register",
            200,
            data=admin_data
        )
        
        # Inactive user
        inactive_data = {
            "name": "Sócio Inadimplente",
            "email": "inadimplente@accta.cv",
            "password": "socio123",
            "role": "socio",
            "status": "inadimplente",
            "member_id": "ACCTA002",
            "consent_data": True
        }
        
        success3, response3 = self.run_test(
            "Register Inactive User",
            "POST",
            "auth/register",
            200,
            data=inactive_data
        )
        
        return success1 and success2 and success3

    def test_login(self):
        """Test login with different users"""
        print("\n🔐 Testing login...")
        
        # Regular user login
        success1, response1 = self.run_test(
            "Login Regular User",
            "POST",
            "auth/login",
            200,
            data={"email": "socio1@accta.cv", "password": "socio123"}
        )
        
        if success1 and 'access_token' in response1:
            self.token = response1['access_token']
            self.current_user_id = response1['user']['id']
            print(f"   Regular user token: {self.token[:20]}...")
        
        # Admin login
        success2, response2 = self.run_test(
            "Login Admin User",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@accta.cv", "password": "admin123"}
        )
        
        if success2 and 'access_token' in response2:
            self.admin_token = response2['access_token']
            self.admin_user_id = response2['user']['id']
            print(f"   Admin token: {self.admin_token[:20]}...")
        
        return success1 and success2

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_demo_data(self):
        """Create demo data for testing"""
        print("\n📊 Creating demo data...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Create demo poll
        poll_data = {
            "title": "Aprovação do Novo Estatuto",
            "description": "Votação sobre as alterações propostas no estatuto da associação",
            "options": [
                {"id": 1, "label": "Aprovar"},
                {"id": 2, "label": "Rejeitar"},
                {"id": 3, "label": "Abstinência"}
            ],
            "start_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "result_visibility": "socios"
        }
        
        success1, poll_response = self.run_test(
            "Create Demo Poll",
            "POST",
            "polls",
            200,
            data=poll_data,
            token=self.admin_token
        )
        
        # Update poll status to open
        if success1:
            poll_id = poll_response.get('id')
            # Note: We need to manually update poll status in DB as there's no API endpoint for this
            print(f"   Created poll with ID: {poll_id}")
        
        # Create demo invoice
        if self.current_user_id:
            invoice_data = {
                "user_id": self.current_user_id,
                "type": "quota",
                "amount": 500.0,
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "source": "folha_salarial",
                "payroll_reference": "REF-2024-01",
                "notes": "Quota mensal"
            }
            
            success2, invoice_response = self.run_test(
                "Create Demo Invoice",
                "POST",
                "invoices",
                200,
                data=invoice_data,
                token=self.admin_token
            )
        else:
            success2 = False
        
        # Create demo benefit
        benefit_data = {
            "name": "Desconto Academia Fitness",
            "description": "20% de desconto em mensalidades da academia local",
            "discount_percent": 20.0,
            "logo_url": "https://example.com/logo.png"
        }
        
        success3, benefit_response = self.run_test(
            "Create Demo Benefit",
            "POST",
            "benefits",
            200,
            data=benefit_data,
            token=self.admin_token
        )
        
        # Create demo document
        doc_data = {
            "title": "Estatuto ACCTA 2024",
            "file_url": "https://example.com/estatuto.pdf",
            "type": "estatuto",
            "visibility": "socios",
            "tags": ["legal", "governança"]
        }
        
        success4, doc_response = self.run_test(
            "Create Demo Document",
            "POST",
            "documents",
            200,
            data=doc_data,
            token=self.admin_token
        )
        
        return success1 and success2 and success3 and success4

    def test_poll_operations(self):
        """Test poll operations"""
        print("\n🗳️ Testing poll operations...")
        
        # Get polls
        success1, polls_response = self.run_test(
            "Get Polls",
            "GET",
            "polls",
            200
        )
        
        if not success1 or not polls_response.get('data'):
            print("   No polls found, skipping voting test")
            return success1
        
        # Try to vote (should work for active user)
        polls = polls_response.get('data', [])
        if polls:
            poll_id = polls[0]['id']
            vote_data = {
                "poll_id": poll_id,
                "vote_option": 1
            }
            
            success2, vote_response = self.run_test(
                "Cast Vote",
                "POST",
                "polls/vote",
                200,
                data=vote_data
            )
            
            # Get poll results
            success3, results_response = self.run_test(
                f"Get Poll Results",
                "GET",
                f"polls/{poll_id}/results",
                200
            )
        else:
            success2 = success3 = False
        
        return success1 and success2 and success3

    def test_invoice_operations(self):
        """Test invoice operations"""
        print("\n💰 Testing invoice operations...")
        
        success1, response1 = self.run_test(
            "Get User Invoices",
            "GET",
            "invoices",
            200
        )
        
        # Test admin access to all invoices
        success2, response2 = self.run_test(
            "Get All Invoices (Admin)",
            "GET",
            "invoices",
            200,
            token=self.admin_token
        )
        
        return success1 and success2

    def test_user_management(self):
        """Test user management (admin only)"""
        print("\n👥 Testing user management...")
        
        success1, response1 = self.run_test(
            "Get All Users (Admin)",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        
        # Test regular user can't access users endpoint
        success2, response2 = self.run_test(
            "Get Users (Regular User - Should Fail)",
            "GET",
            "users",
            403
        )
        
        # success2 should be True because we expect 403 (access denied)
        return success1 and success2

    def test_benefits_and_documents(self):
        """Test benefits and documents"""
        print("\n📄 Testing benefits and documents...")
        
        success1, response1 = self.run_test(
            "Get Benefits",
            "GET",
            "benefits",
            200
        )
        
        success2, response2 = self.run_test(
            "Get Documents",
            "GET",
            "documents",
            200
        )
        
        return success1 and success2

    def test_wall_operations(self):
        """Test wall (mural) operations"""
        print("\n📝 Testing wall operations...")
        
        # Create wall post
        post_data = {
            "content": "Teste de post no mural da associação"
        }
        
        success1, response1 = self.run_test(
            "Create Wall Post",
            "POST",
            "wall",
            200,
            data=post_data
        )
        
        # Get wall posts
        success2, response2 = self.run_test(
            "Get Wall Posts",
            "GET",
            "wall",
            200
        )
        
        return success1 and success2

    def test_public_endpoints(self):
        """Test public endpoints"""
        print("\n🌐 Testing public endpoints...")
        
        # Test QR validator (this is public, no auth needed)
        success1, response1 = self.run_test(
            "QR Validator (Invalid Hash)",
            "GET",
            "validate/invalid-hash",
            404,
            token=None
        )
        
        # Test public posts
        success2, response2 = self.run_test(
            "Get Public Posts",
            "GET",
            "posts?visibility=publico",
            200,
            token=None
        )
        
        return success1 and success2

    def test_statistics(self):
        """Test admin statistics"""
        print("\n📊 Testing statistics...")
        
        success, response = self.run_test(
            "Get Statistics (Admin)",
            "GET",
            "stats",
            200,
            token=self.admin_token
        )
        
        if success:
            stats = response
            print(f"   Total users: {stats.get('total_users', 0)}")
            print(f"   Active users: {stats.get('active_users', 0)}")
            print(f"   Pending invoices: {stats.get('pending_invoices', 0)}")
            print(f"   Total revenue: {stats.get('total_revenue', 0)} CVE")
        
        return success

    def test_audit_logs(self):
        """Test audit logs"""
        print("\n📋 Testing audit logs...")
        
        success, response = self.run_test(
            "Get Audit Logs (Admin)",
            "GET",
            "audit-logs",
            200,
            token=self.admin_token
        )
        
        return success

def main():
    print("🚀 Starting ACCTA Portal API Testing...")
    print("=" * 50)
    
    tester = ACCTAAPITester()
    
    # Run all tests in sequence
    tests = [
        ("API Root", tester.test_api_root),
        ("User Registration", tester.test_register_users),
        ("Authentication", tester.test_login),
        ("Auth Me", tester.test_auth_me),
        ("Demo Data Creation", tester.test_create_demo_data),
        ("Poll Operations", tester.test_poll_operations),
        ("Invoice Operations", tester.test_invoice_operations),
        ("User Management", tester.test_user_management),
        ("Benefits & Documents", tester.test_benefits_and_documents),
        ("Wall Operations", tester.test_wall_operations),
        ("Public Endpoints", tester.test_public_endpoints),
        ("Statistics", tester.test_statistics),
        ("Audit Logs", tester.test_audit_logs)
    ]
    
    passed_tests = []
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result:
                passed_tests.append(test_name)
                print(f"✅ {test_name} - PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} - ERROR: {str(e)}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"🏁 TESTING COMPLETE")
    print(f"{'='*50}")
    print(f"📊 Total Tests: {tester.tests_run}")
    print(f"✅ Passed: {tester.tests_passed}")
    print(f"❌ Failed: {tester.tests_run - tester.tests_passed}")
    print(f"📈 Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    print(f"\n📋 Test Categories:")
    print(f"✅ Passed: {', '.join(passed_tests) if passed_tests else 'None'}")
    print(f"❌ Failed: {', '.join(failed_tests) if failed_tests else 'None'}")
    
    if tester.tests_passed == tester.tests_run:
        print(f"\n🎉 All tests passed! API is fully functional.")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())