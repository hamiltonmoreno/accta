"""
Finance Module Tests - ACTACV Association Portal
Tests for: Transactions CRUD, DRE Reports, Settings, Quota Generation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@accta.cv", "password": "admin123"}
SOCIO_CREDS = {"email": "socio1@accta.cv", "password": "socio123"}


class TestAuthSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def socio_token(self):
        """Get socio (regular member) authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SOCIO_CREDS)
        if response.status_code != 200:
            pytest.skip(f"Socio login failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"Admin login successful: {data['user']['email']}")
    
    def test_socio_login(self):
        """Test socio can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SOCIO_CREDS)
        assert response.status_code == 200, f"Socio login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "socio"
        print(f"Socio login successful: {data['user']['email']}")


class TestTransactionsCRUD:
    """Transaction CRUD operations tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Create authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def socio_session(self):
        """Create authenticated socio session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=SOCIO_CREDS)
        if response.status_code != 200:
            pytest.skip("Socio login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_list_transactions(self, admin_session):
        """GET /api/finances/transactions - list all transactions"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Listed {len(data)} transactions")
    
    def test_list_transactions_filter_receita(self, admin_session):
        """GET /api/finances/transactions?type=receita - filter by income"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"type": "receita"})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        for tx in data:
            assert tx["type"] == "receita", f"Expected receita, got {tx['type']}"
        print(f"Listed {len(data)} receita transactions")
    
    def test_list_transactions_filter_despesa(self, admin_session):
        """GET /api/finances/transactions?type=despesa - filter by expense"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"type": "despesa"})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        for tx in data:
            assert tx["type"] == "despesa", f"Expected despesa, got {tx['type']}"
        print(f"Listed {len(data)} despesa transactions")
    
    def test_create_income_transaction(self, admin_session):
        """POST /api/finances/transactions - create income (receita)"""
        payload = {
            "type": "receita",
            "category": "patrocinios",
            "description": "TEST_Patrocinio Empresa XYZ",
            "amount": 50000.0,
            "date": "2026-01-20T10:00:00",
            "reference": "TEST-PAT-001"
        }
        response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["type"] == "receita"
        assert data["category"] == "patrocinios"
        assert data["amount"] == 50000.0
        assert "id" in data
        print(f"Created income transaction: {data['id']}")
        return data["id"]
    
    def test_create_expense_transaction(self, admin_session):
        """POST /api/finances/transactions - create expense (despesa)"""
        payload = {
            "type": "despesa",
            "category": "operacional",
            "description": "TEST_Despesa Operacional Escritorio",
            "amount": 15000.0,
            "date": "2026-01-22T14:00:00",
            "reference": "TEST-OP-001"
        }
        response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["type"] == "despesa"
        assert data["category"] == "operacional"
        assert data["amount"] == 15000.0
        print(f"Created expense transaction: {data['id']}")
        return data["id"]
    
    def test_create_transaction_invalid_type(self, admin_session):
        """POST /api/finances/transactions - reject invalid type"""
        payload = {
            "type": "invalid_type",
            "category": "quotas",
            "description": "TEST_Invalid",
            "amount": 1000.0,
            "date": "2026-01-20T10:00:00"
        }
        response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"Correctly rejected invalid type: {response.json()}")
    
    def test_create_transaction_invalid_category(self, admin_session):
        """POST /api/finances/transactions - reject invalid category for type"""
        payload = {
            "type": "receita",
            "category": "operacional",  # operacional is expense category, not income
            "description": "TEST_Invalid Category",
            "amount": 1000.0,
            "date": "2026-01-20T10:00:00"
        }
        response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"Correctly rejected invalid category: {response.json()}")
    
    def test_create_transaction_invalid_amount(self, admin_session):
        """POST /api/finances/transactions - reject negative/zero amount"""
        payload = {
            "type": "receita",
            "category": "quotas",
            "description": "TEST_Invalid Amount",
            "amount": -100.0,
            "date": "2026-01-20T10:00:00"
        }
        response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"Correctly rejected negative amount: {response.json()}")
    
    def test_update_transaction(self, admin_session):
        """PATCH /api/finances/transactions/{id} - update transaction"""
        # First create a transaction
        create_payload = {
            "type": "receita",
            "category": "doacoes",
            "description": "TEST_Doacao para Update",
            "amount": 5000.0,
            "date": "2026-01-25T10:00:00"
        }
        create_response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=create_payload)
        assert create_response.status_code == 200
        tx_id = create_response.json()["id"]
        
        # Update the transaction
        update_payload = {
            "description": "TEST_Doacao Atualizada",
            "amount": 7500.0
        }
        update_response = admin_session.patch(f"{BASE_URL}/api/finances/transactions/{tx_id}", json=update_payload)
        assert update_response.status_code == 200, f"Failed: {update_response.text}"
        updated = update_response.json()
        assert updated["description"] == "TEST_Doacao Atualizada"
        assert updated["amount"] == 7500.0
        print(f"Updated transaction {tx_id}")
    
    def test_delete_transaction(self, admin_session):
        """DELETE /api/finances/transactions/{id} - delete transaction"""
        # First create a transaction
        create_payload = {
            "type": "despesa",
            "category": "viagens",
            "description": "TEST_Despesa para Delete",
            "amount": 3000.0,
            "date": "2026-01-26T10:00:00"
        }
        create_response = admin_session.post(f"{BASE_URL}/api/finances/transactions", json=create_payload)
        assert create_response.status_code == 200
        tx_id = create_response.json()["id"]
        
        # Delete the transaction
        delete_response = admin_session.delete(f"{BASE_URL}/api/finances/transactions/{tx_id}")
        assert delete_response.status_code == 200, f"Failed: {delete_response.text}"
        print(f"Deleted transaction {tx_id}")
        
        # Verify it's gone - should get 404 on update attempt
        verify_response = admin_session.patch(f"{BASE_URL}/api/finances/transactions/{tx_id}", json={"amount": 100})
        assert verify_response.status_code == 404
    
    def test_socio_cannot_access_transactions(self, socio_session):
        """Non-admin/financeiro users should get 403 on finance endpoints"""
        response = socio_session.get(f"{BASE_URL}/api/finances/transactions")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"Correctly denied socio access: {response.json()}")


class TestFinancialSummary:
    """Financial summary endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_summary_current_year(self, admin_session):
        """GET /api/finances/summary - get financial summary for current year"""
        response = admin_session.get(f"{BASE_URL}/api/finances/summary", params={"year": 2026})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        assert "receitas_por_categoria" in data
        assert "despesas_por_categoria" in data
        assert data["resultado_liquido"] == data["total_receitas"] - data["total_despesas"]
        print(f"Summary: Receitas={data['total_receitas']}, Despesas={data['total_despesas']}, Resultado={data['resultado_liquido']}")
    
    def test_get_summary_with_month(self, admin_session):
        """GET /api/finances/summary - get summary for specific month"""
        response = admin_session.get(f"{BASE_URL}/api/finances/summary", params={"year": 2026, "month": 1})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_receitas" in data
        print(f"January 2026 Summary: {data['total_transacoes']} transactions")


class TestDREReport:
    """DRE (Demonstracao do Resultado do Exercicio) report tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_dre_report(self, admin_session):
        """GET /api/finances/dre - get DRE report with monthly breakdown"""
        response = admin_session.get(f"{BASE_URL}/api/finances/dre", params={"year": 2026})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert data["year"] == 2026
        assert "monthly" in data
        assert "receitas_por_categoria" in data
        assert "despesas_por_categoria" in data
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        
        # Verify monthly breakdown has all 12 months
        assert len(data["monthly"]) == 12
        for month in range(1, 13):
            assert str(month) in data["monthly"]
            assert "receitas" in data["monthly"][str(month)]
            assert "despesas" in data["monthly"][str(month)]
        
        print(f"DRE 2026: Total Receitas={data['total_receitas']}, Total Despesas={data['total_despesas']}")
    
    def test_dre_requires_year_param(self, admin_session):
        """GET /api/finances/dre - year parameter is required"""
        response = admin_session.get(f"{BASE_URL}/api/finances/dre")
        assert response.status_code == 422, f"Expected 422 for missing year, got {response.status_code}"
        print("Correctly requires year parameter")


class TestFinanceSettings:
    """Finance settings endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def socio_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=SOCIO_CREDS)
        if response.status_code != 200:
            pytest.skip("Socio login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_settings(self, admin_session):
        """GET /api/finances/settings - get finance settings"""
        response = admin_session.get(f"{BASE_URL}/api/finances/settings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "quota_amount" in data
        assert "quota_description" in data
        assert data["quota_amount"] > 0
        print(f"Settings: quota_amount={data['quota_amount']}, description={data['quota_description']}")
    
    def test_update_settings_admin_only(self, admin_session):
        """PATCH /api/finances/settings - admin can update settings"""
        # Get current settings
        get_response = admin_session.get(f"{BASE_URL}/api/finances/settings")
        original_amount = get_response.json()["quota_amount"]
        
        # Update settings
        new_amount = 2500.0
        update_response = admin_session.patch(f"{BASE_URL}/api/finances/settings", json={
            "quota_amount": new_amount,
            "quota_description": "Quota Mensal Atualizada"
        })
        assert update_response.status_code == 200, f"Failed: {update_response.text}"
        
        # Verify update
        verify_response = admin_session.get(f"{BASE_URL}/api/finances/settings")
        assert verify_response.json()["quota_amount"] == new_amount
        
        # Restore original
        admin_session.patch(f"{BASE_URL}/api/finances/settings", json={"quota_amount": original_amount})
        print("Settings update successful")
    
    def test_socio_cannot_update_settings(self, socio_session):
        """PATCH /api/finances/settings - socio cannot update (403)"""
        response = socio_session.patch(f"{BASE_URL}/api/finances/settings", json={"quota_amount": 1000})
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Correctly denied socio from updating settings")
    
    def test_socio_cannot_get_settings(self, socio_session):
        """GET /api/finances/settings - socio cannot access (403)"""
        response = socio_session.get(f"{BASE_URL}/api/finances/settings")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Correctly denied socio from viewing settings")


class TestQuotaGeneration:
    """Bulk quota generation tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_generate_quotas(self, admin_session):
        """POST /api/finances/generate-quotas - bulk generate monthly quotas"""
        # Use a future month to avoid conflicts with existing data
        response = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 12,
            "year": 2026
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "created" in data
        assert "skipped" in data
        assert "total_value" in data
        print(f"Generated quotas: created={data['created']}, skipped={data['skipped']}, total={data['total_value']}")
    
    def test_generate_quotas_idempotent(self, admin_session):
        """POST /api/finances/generate-quotas - running twice skips existing"""
        # First run
        response1 = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 11,
            "year": 2026
        })
        assert response1.status_code == 200
        created1 = response1.json()["created"]
        
        # Second run - should skip all
        response2 = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 11,
            "year": 2026
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["created"] == 0, "Should not create duplicates"
        assert data2["skipped"] >= created1
        print(f"Idempotent check passed: second run created 0, skipped {data2['skipped']}")


class TestCategoriesMetadata:
    """Categories metadata endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_categories(self, admin_session):
        """GET /api/finances/meta/categories - get categories metadata"""
        response = admin_session.get(f"{BASE_URL}/api/finances/meta/categories")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "income" in data
        assert "expense" in data
        assert "types" in data
        
        # Verify expected categories
        assert "quotas" in data["income"]
        assert "patrocinios" in data["income"]
        assert "operacional" in data["expense"]
        assert "receita" in data["types"]
        assert "despesa" in data["types"]
        
        print(f"Categories: income={data['income']}, expense={data['expense']}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_cleanup_test_transactions(self, admin_session):
        """Clean up TEST_ prefixed transactions"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"limit": 200})
        if response.status_code == 200:
            transactions = response.json()
            deleted = 0
            for tx in transactions:
                if tx.get("description", "").startswith("TEST_"):
                    del_response = admin_session.delete(f"{BASE_URL}/api/finances/transactions/{tx['id']}")
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"Cleaned up {deleted} test transactions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
