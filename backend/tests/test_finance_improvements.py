"""
Finance Module Improvements Tests - ACTACV Association Portal
Tests for 7 new improvements:
1. Date range filters on Cash Flow
2. Text search for transactions
3. Real pagination (paginated response format)
4. CSV export of transactions
5. DRE category percentages (already in DRE endpoint)
6. Financial summary widget on Dashboard (uses /api/finances/summary)
7. Detailed quota generation results
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@controlador.cv", "password": "admin123"}
SOCIO_CREDS = {"email": "socio1@controlador.cv", "password": "socio123"}


@pytest.fixture(scope="module")
def admin_session():
    """Create authenticated admin session"""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


class TestPaginatedTransactions:
    """Test paginated response format for transactions"""
    
    def test_transactions_returns_paginated_format(self, admin_session):
        """GET /api/finances/transactions returns {items, total, skip, limit}"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify paginated response structure
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert "skip" in data, "Response should have 'skip' field"
        assert "limit" in data, "Response should have 'limit' field"
        
        assert isinstance(data["items"], list), "'items' should be a list"
        assert isinstance(data["total"], int), "'total' should be an integer"
        assert isinstance(data["skip"], int), "'skip' should be an integer"
        assert isinstance(data["limit"], int), "'limit' should be an integer"
        
        print(f"Paginated response: total={data['total']}, items_returned={len(data['items'])}, skip={data['skip']}, limit={data['limit']}")
    
    def test_pagination_skip_limit(self, admin_session):
        """Test skip and limit parameters work correctly"""
        # Get first page
        response1 = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"skip": 0, "limit": 10})
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"skip": 10, "limit": 10})
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Total should be same across pages
        assert data1["total"] == data2["total"], "Total should be consistent across pages"
        
        # Skip should reflect the parameter
        assert data1["skip"] == 0
        assert data2["skip"] == 10
        
        # If there are enough items, pages should have different items
        if data1["total"] > 20:
            first_page_ids = set(tx["id"] for tx in data1["items"])
            second_page_ids = set(tx["id"] for tx in data2["items"])
            # Pages should be mostly different (allow some overlap due to concurrent changes)
            # Just verify we got different data
            assert first_page_ids != second_page_ids, "Pages should return different items"
        
        print(f"Pagination test passed: page1={len(data1['items'])} items, page2={len(data2['items'])} items")
    
    def test_pagination_with_20_limit(self, admin_session):
        """Test default PAGE_SIZE of 20"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"limit": 20})
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 20 items
        assert len(data["items"]) <= 20, f"Should return at most 20 items, got {len(data['items'])}"
        assert data["limit"] == 20
        
        print(f"PAGE_SIZE=20 test: returned {len(data['items'])} items, total={data['total']}")


class TestSearchFilter:
    """Test text search filter for transactions"""
    
    def test_search_by_description(self, admin_session):
        """GET /api/finances/transactions?search=TAP filters by description"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"search": "TAP"})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned items should contain 'TAP' in description (case-insensitive)
        for tx in data["items"]:
            assert "tap" in tx["description"].lower(), f"Transaction {tx['id']} doesn't match search: {tx['description']}"
        
        print(f"Search 'TAP' returned {len(data['items'])} transactions (total matching: {data['total']})")
    
    def test_search_case_insensitive(self, admin_session):
        """Search should be case-insensitive"""
        response_upper = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"search": "QUOTA"})
        response_lower = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"search": "quota"})
        
        assert response_upper.status_code == 200
        assert response_lower.status_code == 200
        
        # Both should return same total
        assert response_upper.json()["total"] == response_lower.json()["total"], "Search should be case-insensitive"
        
        print(f"Case-insensitive search verified: QUOTA={response_upper.json()['total']}, quota={response_lower.json()['total']}")
    
    def test_search_with_pagination(self, admin_session):
        """Search should work with pagination"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={
            "search": "Mensal",
            "skip": 0,
            "limit": 5
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should have paginated structure
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 5
        
        print(f"Search with pagination: {len(data['items'])} items returned, total matching: {data['total']}")


class TestDateRangeFilter:
    """Test date range filters for transactions"""
    
    def test_start_date_filter(self, admin_session):
        """GET /api/finances/transactions?start_date=... filters from date"""
        start_date = "2026-01-01T00:00:00"
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"start_date": start_date})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned items should have date >= start_date
        for tx in data["items"]:
            assert tx["date"] >= start_date, f"Transaction date {tx['date']} is before start_date {start_date}"
        
        print(f"Start date filter: {len(data['items'])} transactions from {start_date}")
    
    def test_end_date_filter(self, admin_session):
        """GET /api/finances/transactions?end_date=... filters until date"""
        end_date = "2025-12-31T23:59:59"
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={"end_date": end_date})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned items should have date <= end_date
        for tx in data["items"]:
            assert tx["date"] <= end_date, f"Transaction date {tx['date']} is after end_date {end_date}"
        
        print(f"End date filter: {len(data['items'])} transactions until {end_date}")
    
    def test_date_range_filter(self, admin_session):
        """GET /api/finances/transactions with both start_date and end_date"""
        start_date = "2025-01-01T00:00:00"
        end_date = "2025-12-31T23:59:59"
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={
            "start_date": start_date,
            "end_date": end_date
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned items should be within range
        for tx in data["items"]:
            assert start_date <= tx["date"] <= end_date, f"Transaction date {tx['date']} is outside range"
        
        print(f"Date range filter: {len(data['items'])} transactions in 2025")
    
    def test_date_filter_with_type(self, admin_session):
        """Date filter should work with type filter"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions", params={
            "type": "receita",
            "start_date": "2025-01-01T00:00:00"
        })
        assert response.status_code == 200
        data = response.json()
        
        for tx in data["items"]:
            assert tx["type"] == "receita"
            assert tx["date"] >= "2025-01-01T00:00:00"
        
        print(f"Combined type+date filter: {len(data['items'])} receitas from 2025")


class TestCSVExport:
    """Test CSV export endpoint"""
    
    def test_csv_export_returns_csv(self, admin_session):
        """GET /api/finances/transactions/csv returns CSV file"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions/csv")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        
        # Check content disposition
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, f"Expected attachment, got {content_disp}"
        assert "Fluxo_Caixa_ACCTA.csv" in content_disp, f"Expected filename in disposition: {content_disp}"
        
        print(f"CSV export successful, Content-Type: {content_type}")
    
    def test_csv_uses_semicolon_delimiter(self, admin_session):
        """CSV should use semicolon (;) as delimiter"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions/csv")
        assert response.status_code == 200
        
        # Decode content (UTF-8 BOM)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        # Check header row uses semicolons
        header = lines[0]
        assert ";" in header, f"Header should use semicolon delimiter: {header}"
        
        # Verify expected columns (strip whitespace/carriage returns)
        columns = [c.strip() for c in header.split(";")]
        expected_columns = ["Data", "Tipo", "Categoria", "Descricao", "Valor (CVE)", "Referencia"]
        assert columns == expected_columns, f"Expected columns {expected_columns}, got {columns}"
        
        print(f"CSV delimiter verified: {len(lines)} rows, columns: {columns}")
    
    def test_csv_respects_type_filter(self, admin_session):
        """CSV export should respect type filter"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions/csv", params={"type": "receita"})
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        # Skip header, check all rows are Receita
        for line in lines[1:]:
            if line.strip():
                columns = line.split(";")
                assert columns[1] == "Receita", f"Expected Receita, got {columns[1]}"
        
        print(f"CSV type filter verified: {len(lines)-1} receita rows")
    
    def test_csv_respects_search_filter(self, admin_session):
        """CSV export should respect search filter"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions/csv", params={"search": "Quota"})
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        # Skip header, check all rows contain 'Quota' in description
        for line in lines[1:]:
            if line.strip():
                columns = line.split(";")
                description = columns[3]
                assert "quota" in description.lower(), f"Description should contain 'quota': {description}"
        
        print(f"CSV search filter verified: {len(lines)-1} rows matching 'Quota'")
    
    def test_csv_respects_date_filter(self, admin_session):
        """CSV export should respect date filters"""
        response = admin_session.get(f"{BASE_URL}/api/finances/transactions/csv", params={
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-12-31T23:59:59"
        })
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\n')
        
        # Skip header, check all dates are in 2025
        for line in lines[1:]:
            if line.strip():
                columns = line.split(";")
                date_str = columns[0]
                if date_str:
                    assert date_str.startswith("2025-"), f"Date should be in 2025: {date_str}"
        
        print(f"CSV date filter verified: {len(lines)-1} rows in 2025")


class TestQuotaGenerationDetails:
    """Test detailed quota generation results"""
    
    def test_generate_quotas_returns_details(self, admin_session):
        """POST /api/finances/generate-quotas returns created, skipped, total_value"""
        # Use a future month to test
        response = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 10,
            "year": 2027
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify detailed response structure
        assert "message" in data, "Response should have 'message'"
        assert "created" in data, "Response should have 'created'"
        assert "skipped" in data, "Response should have 'skipped'"
        assert "total_value" in data, "Response should have 'total_value'"
        
        assert isinstance(data["created"], int)
        assert isinstance(data["skipped"], int)
        assert isinstance(data["total_value"], (int, float))
        
        print(f"Quota generation details: created={data['created']}, skipped={data['skipped']}, total_value={data['total_value']}")
    
    def test_generate_quotas_idempotent_with_details(self, admin_session):
        """Running generate-quotas twice shows skipped count"""
        # First run
        response1 = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 9,
            "year": 2027
        })
        assert response1.status_code == 200
        data1 = response1.json()
        created_first = data1["created"]
        
        # Second run - should skip all
        response2 = admin_session.post(f"{BASE_URL}/api/finances/generate-quotas", params={
            "month": 9,
            "year": 2027
        })
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["created"] == 0, "Second run should create 0"
        assert data2["skipped"] >= created_first, "Second run should skip at least what was created"
        assert data2["total_value"] == 0, "Second run should have 0 total_value"
        
        print(f"Idempotent check: first created={created_first}, second skipped={data2['skipped']}")


class TestFinancialSummaryForDashboard:
    """Test financial summary endpoint used by Dashboard widget"""
    
    def test_summary_returns_required_fields(self, admin_session):
        """GET /api/finances/summary returns fields needed for Dashboard widget"""
        response = admin_session.get(f"{BASE_URL}/api/finances/summary", params={"year": 2026})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Dashboard widget needs these fields
        assert "total_receitas" in data, "Should have total_receitas"
        assert "total_despesas" in data, "Should have total_despesas"
        assert "resultado_liquido" in data, "Should have resultado_liquido"
        
        # Verify calculation
        assert data["resultado_liquido"] == data["total_receitas"] - data["total_despesas"]
        
        print(f"Summary for Dashboard: Receitas={data['total_receitas']}, Despesas={data['total_despesas']}, Saldo={data['resultado_liquido']}")


class TestDRECategoryPercentages:
    """Test DRE endpoint returns data for percentage calculations"""
    
    def test_dre_has_category_breakdown(self, admin_session):
        """GET /api/finances/dre returns category breakdown for percentage bars"""
        response = admin_session.get(f"{BASE_URL}/api/finances/dre", params={"year": 2025})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify category breakdown exists
        assert "receitas_por_categoria" in data, "Should have receitas_por_categoria"
        assert "despesas_por_categoria" in data, "Should have despesas_por_categoria"
        assert "total_receitas" in data, "Should have total_receitas for percentage calculation"
        assert "total_despesas" in data, "Should have total_despesas for percentage calculation"
        
        # Verify category values are numbers (for percentage calculation)
        for cat, val in data["receitas_por_categoria"].items():
            assert isinstance(val, (int, float)), f"Category {cat} value should be numeric"
        
        for cat, val in data["despesas_por_categoria"].items():
            assert isinstance(val, (int, float)), f"Category {cat} value should be numeric"
        
        print(f"DRE categories: {len(data['receitas_por_categoria'])} income, {len(data['despesas_por_categoria'])} expense")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
