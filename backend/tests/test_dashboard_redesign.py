"""
Test Dashboard Redesign - Backend API Tests
Tests for finance APIs used by the redesigned dashboard:
- GET /api/finances/dre?year=YYYY - Monthly financial data for charts
- GET /api/finances/summary - Financial summary for dashboard widget
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@accta.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@accta.cv"
SOCIO_PASSWORD = "socio123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def socio_token():
    """Get regular socio authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": SOCIO_EMAIL, "password": SOCIO_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Socio authentication failed")


class TestDREEndpoint:
    """Tests for GET /api/finances/dre - Monthly financial data for charts"""
    
    def test_dre_returns_valid_structure(self, admin_token):
        """DRE endpoint returns correct structure for dashboard charts"""
        response = requests.get(
            f"{BASE_URL}/api/finances/dre?year=2026",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "year" in data
        assert data["year"] == 2026
        assert "monthly" in data
        assert "receitas_por_categoria" in data
        assert "despesas_por_categoria" in data
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
    
    def test_dre_monthly_has_all_months(self, admin_token):
        """DRE monthly data contains all 12 months"""
        response = requests.get(
            f"{BASE_URL}/api/finances/dre?year=2026",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        monthly = data["monthly"]
        # Check all 12 months exist (keys are strings "1" to "12")
        for month in range(1, 13):
            assert str(month) in monthly or month in monthly
            month_data = monthly.get(str(month)) or monthly.get(month)
            assert "receitas" in month_data
            assert "despesas" in month_data
    
    def test_dre_requires_year_param(self, admin_token):
        """DRE endpoint requires year parameter"""
        response = requests.get(
            f"{BASE_URL}/api/finances/dre",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 422 (validation error) without year param
        assert response.status_code == 422
    
    def test_dre_forbidden_for_regular_socio(self, socio_token):
        """DRE endpoint is forbidden for regular socio users"""
        response = requests.get(
            f"{BASE_URL}/api/finances/dre?year=2026",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        
        assert response.status_code == 403


class TestFinanceSummaryEndpoint:
    """Tests for GET /api/finances/summary - Financial summary for dashboard widget"""
    
    def test_summary_returns_valid_structure(self, admin_token):
        """Summary endpoint returns correct structure for dashboard widget"""
        response = requests.get(
            f"{BASE_URL}/api/finances/summary?year=2026",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields for dashboard widget
        assert "total_receitas" in data
        assert "total_despesas" in data
        assert "resultado_liquido" in data
        
        # Verify data types
        assert isinstance(data["total_receitas"], (int, float))
        assert isinstance(data["total_despesas"], (int, float))
        assert isinstance(data["resultado_liquido"], (int, float))
    
    def test_summary_resultado_calculation(self, admin_token):
        """Summary resultado_liquido equals receitas minus despesas"""
        response = requests.get(
            f"{BASE_URL}/api/finances/summary?year=2026",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_resultado = data["total_receitas"] - data["total_despesas"]
        assert data["resultado_liquido"] == expected_resultado
    
    def test_summary_forbidden_for_regular_socio(self, socio_token):
        """Summary endpoint is forbidden for regular socio users"""
        response = requests.get(
            f"{BASE_URL}/api/finances/summary?year=2026",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        
        assert response.status_code == 403
    
    def test_summary_includes_category_breakdown(self, admin_token):
        """Summary includes category breakdown for DRE percentages"""
        response = requests.get(
            f"{BASE_URL}/api/finances/summary?year=2026",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check category breakdowns exist
        assert "receitas_por_categoria" in data
        assert "despesas_por_categoria" in data
        assert isinstance(data["receitas_por_categoria"], dict)
        assert isinstance(data["despesas_por_categoria"], dict)


class TestStatsEndpoint:
    """Tests for GET /api/stats - Stats for dashboard stat cards"""
    
    def test_stats_returns_valid_structure(self, admin_token):
        """Stats endpoint returns correct structure for stat cards"""
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields for stat cards
        assert "total_users" in data
        assert "active_users" in data
        assert "active_events" in data
        assert "total_revenue" in data
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["active_events"], int)
        assert isinstance(data["total_revenue"], (int, float))
    
    def test_stats_forbidden_for_regular_socio(self, socio_token):
        """Stats endpoint is forbidden for regular socio users"""
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers={"Authorization": f"Bearer {socio_token}"}
        )
        
        assert response.status_code == 403


class TestAuthEndpoint:
    """Tests for authentication - verify login works"""
    
    def test_admin_login_success(self):
        """Admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
    
    def test_socio_login_success(self):
        """Regular socio can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SOCIO_EMAIL, "password": SOCIO_PASSWORD}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        # Regular socio should not be admin
        assert data["user"]["role"] != "admin"
