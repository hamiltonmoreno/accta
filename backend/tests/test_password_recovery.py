"""
Password Recovery Feature Tests
Tests for forgot-password and reset-password endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPasswordRecovery:
    """Password recovery flow tests"""
    
    # Test credentials
    TEST_EMAIL = "socio1@accta.cv"
    ORIGINAL_PASSWORD = "socio123"
    NEW_PASSWORD = "newpass123"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    # ===== FORGOT PASSWORD TESTS =====
    
    def test_forgot_password_valid_email(self):
        """POST /api/auth/forgot-password with valid email returns demo_token"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "demo_token" in data, "Response should contain demo_token"
        assert "message" in data, "Response should contain message"
        assert "expires_in" in data, "Response should contain expires_in"
        assert len(data["demo_token"]) > 0, "Token should not be empty"
        print(f"✓ Forgot password returned token: {data['demo_token'][:8]}...")
    
    def test_forgot_password_invalid_email(self):
        """POST /api/auth/forgot-password with invalid email returns 404"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"✓ Invalid email correctly returns 404: {data['detail']}")
    
    def test_forgot_password_invalid_email_format(self):
        """POST /api/auth/forgot-password with invalid email format returns 422"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "not-an-email"}
        )
        assert response.status_code == 422, f"Expected 422 for invalid email format, got {response.status_code}"
        print("✓ Invalid email format correctly returns 422")
    
    # ===== RESET PASSWORD TESTS =====
    
    def test_reset_password_valid_token(self):
        """POST /api/auth/reset-password with valid token succeeds"""
        # First get a token
        forgot_response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert forgot_response.status_code == 200
        token = forgot_response.json()["demo_token"]
        
        # Reset password
        reset_response = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": self.NEW_PASSWORD}
        )
        assert reset_response.status_code == 200, f"Expected 200, got {reset_response.status_code}: {reset_response.text}"
        
        data = reset_response.json()
        assert "message" in data, "Response should contain success message"
        print(f"✓ Password reset successful: {data['message']}")
    
    def test_reset_password_used_token(self):
        """POST /api/auth/reset-password with used token returns 400"""
        # Get a token
        forgot_response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert forgot_response.status_code == 200
        token = forgot_response.json()["demo_token"]
        
        # Use the token
        first_reset = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": "temppass123"}
        )
        assert first_reset.status_code == 200
        
        # Try to use the same token again
        second_reset = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": "anotherpass123"}
        )
        assert second_reset.status_code == 400, f"Expected 400 for used token, got {second_reset.status_code}"
        
        data = second_reset.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"✓ Used token correctly returns 400: {data['detail']}")
    
    def test_reset_password_invalid_token(self):
        """POST /api/auth/reset-password with invalid token returns 400"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "invalid-token-12345", "new_password": "newpass123"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"✓ Invalid token correctly returns 400: {data['detail']}")
    
    def test_reset_password_short_password(self):
        """POST /api/auth/reset-password with short password returns 400"""
        # Get a token
        forgot_response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert forgot_response.status_code == 200
        token = forgot_response.json()["demo_token"]
        
        # Try to reset with short password
        reset_response = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": "12345"}  # Only 5 chars
        )
        assert reset_response.status_code == 400, f"Expected 400 for short password, got {reset_response.status_code}"
        
        data = reset_response.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"✓ Short password correctly returns 400: {data['detail']}")
    
    # ===== E2E FLOW TEST =====
    
    def test_full_password_recovery_flow(self):
        """Full E2E: forgot password -> get token -> reset -> login with new password"""
        # Step 1: Request password reset
        forgot_response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert forgot_response.status_code == 200
        token = forgot_response.json()["demo_token"]
        print(f"✓ Step 1: Got reset token")
        
        # Step 2: Reset password
        reset_response = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": self.NEW_PASSWORD}
        )
        assert reset_response.status_code == 200
        print(f"✓ Step 2: Password reset successful")
        
        # Step 3: Login with new password
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.TEST_EMAIL, "password": self.NEW_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login with new password failed: {login_response.text}"
        
        data = login_response.json()
        assert "access_token" in data, "Login should return access_token"
        assert "user" in data, "Login should return user"
        assert data["user"]["email"] == self.TEST_EMAIL
        print(f"✓ Step 3: Login with new password successful")
        
        # Step 4: Verify old password no longer works
        old_login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.TEST_EMAIL, "password": self.ORIGINAL_PASSWORD}
        )
        assert old_login_response.status_code == 401, "Old password should not work"
        print(f"✓ Step 4: Old password correctly rejected")
    
    def test_restore_original_password(self):
        """Restore test user password back to original (socio123)"""
        # Get a new token
        forgot_response = self.session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": self.TEST_EMAIL}
        )
        assert forgot_response.status_code == 200
        token = forgot_response.json()["demo_token"]
        
        # Reset to original password
        reset_response = self.session.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": token, "new_password": self.ORIGINAL_PASSWORD}
        )
        assert reset_response.status_code == 200
        
        # Verify login with original password works
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.TEST_EMAIL, "password": self.ORIGINAL_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login with restored password failed: {login_response.text}"
        print(f"✓ Password restored to original: {self.ORIGINAL_PASSWORD}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
