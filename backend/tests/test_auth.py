"""
================================================================================
Farm Management System - Authentication Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-24

Description:
    Tests for authentication endpoints including login, token refresh,
    logout, password reset, and JWT token validation.

================================================================================
"""

import pytest
from httpx import AsyncClient
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    is_token_expired,
)
from app.auth.password import verify_password
from app.database import fetch_one, execute_query


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


@pytest.mark.auth
class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self, test_admin_user):
        """Test access token creation."""
        token = create_access_token(
            user_id=test_admin_user["id"],
            email=test_admin_user["email"],
            full_name=test_admin_user["full_name"],
            role=test_admin_user["role"],
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, test_admin_user):
        """Test refresh token creation."""
        token = create_refresh_token(user_id=test_admin_user["id"])

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self, test_admin_user):
        """Test access token verification."""
        token = create_access_token(
            user_id=test_admin_user["id"],
            email=test_admin_user["email"],
            full_name=test_admin_user["full_name"],
            role=test_admin_user["role"],
        )

        payload = verify_access_token(token)

        assert payload is not None
        assert payload["sub"] == test_admin_user["id"]
        assert payload["email"] == test_admin_user["email"]
        assert payload["role"] == test_admin_user["role"]
        assert payload["type"] == "access"

    def test_verify_refresh_token(self, test_admin_user):
        """Test refresh token verification."""
        token = create_refresh_token(user_id=test_admin_user["id"])

        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload["sub"] == test_admin_user["id"]
        assert payload["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        """Test that invalid token returns None."""
        payload = verify_access_token("invalid.token.here")

        assert payload is None

    def test_access_token_not_expired(self, test_admin_user):
        """Test that newly created token is not expired."""
        token = create_access_token(
            user_id=test_admin_user["id"],
            email=test_admin_user["email"],
            full_name=test_admin_user["full_name"],
            role=test_admin_user["role"],
        )

        assert not is_token_expired(token)


# ============================================================================
# LOGIN TESTS
# ============================================================================


@pytest.mark.auth
class TestLogin:
    """Test login endpoint."""

    async def test_login_with_valid_credentials(self, client: AsyncClient, test_admin_user):
        """Test login with correct email and password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"],
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"

        # Check user info
        assert "user" in data
        assert data["user"]["email"] == test_admin_user["email"]
        assert data["user"]["role"] == test_admin_user["role"]
        assert data["user"]["full_name"] == test_admin_user["full_name"]

    async def test_login_with_wrong_password(self, client: AsyncClient, test_admin_user):
        """Test login with incorrect password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_with_nonexistent_email(self, client: AsyncClient):
        """Test login with email that doesn't exist."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_with_inactive_user(self, client: AsyncClient, test_inactive_user):
        """Test login with inactive user account."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_inactive_user["email"],
                "password": test_inactive_user["password"],
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert "inactive" in data["detail"].lower()

    async def test_login_creates_session(self, client: AsyncClient, test_admin_user):
        """Test that login creates an active session."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"],
            },
        )

        assert response.status_code == 200

        # Check that session was created
        session = await fetch_one(
            "SELECT * FROM user_sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
            test_admin_user["id"],
        )

        assert session is not None
        assert str(session["user_id"]) == test_admin_user["id"]

    async def test_login_records_login_attempt(self, client: AsyncClient, test_admin_user):
        """Test that login records login attempt."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"],
            },
        )

        assert response.status_code == 200

        # Check that login attempt was recorded
        attempt = await fetch_one(
            "SELECT * FROM login_history WHERE user_id = $1 ORDER BY login_at DESC LIMIT 1",
            test_admin_user["id"],
        )

        assert attempt is not None
        assert attempt["login_status"] == "success"


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================


@pytest.mark.auth
class TestTokenRefresh:
    """Test token refresh endpoint."""

    async def test_refresh_access_token(self, client: AsyncClient, test_admin_user):
        """Test refreshing access token with valid refresh token."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"],
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_refresh_with_access_token_instead_of_refresh(
        self, client: AsyncClient, test_admin_user
    ):
        """Test that using access token for refresh fails."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"],
            },
        )

        access_token = login_response.json()["access_token"]

        # Try to refresh with access token (should fail)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401


# ============================================================================
# LOGOUT TESTS
# ============================================================================


@pytest.mark.auth
class TestLogout:
    """Test logout endpoint."""

    async def test_logout_revokes_sessions(
        self, client: AsyncClient, test_admin_user, admin_headers
    ):
        """Test that logout revokes all user sessions."""
        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers=admin_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data

        # Check that sessions were revoked
        sessions = await fetch_one(
            "SELECT COUNT(*) as count FROM user_sessions WHERE user_id = $1 AND is_active = true",
            test_admin_user["id"],
        )

        assert sessions["count"] == 0

    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout without authentication token."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 403


# ============================================================================
# GET CURRENT USER TESTS
# ============================================================================


@pytest.mark.auth
class TestGetCurrentUser:
    """Test get current user endpoint."""

    async def test_get_me_with_valid_token(
        self, client: AsyncClient, test_admin_user, admin_headers
    ):
        """Test getting current user info with valid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=admin_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_admin_user["email"]
        assert data["role"] == test_admin_user["role"]
        assert data["full_name"] == test_admin_user["full_name"]

    async def test_get_me_without_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403

    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


# ============================================================================
# PASSWORD CHANGE TESTS
# ============================================================================


@pytest.mark.auth
class TestChangePassword:
    """Test change password endpoint."""

    async def test_change_password_success(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test changing password with correct current password."""
        new_password = "NewPassword123!"

        response = await client.post(
            "/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "current_password": test_regular_user["password"],
                "new_password": new_password,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data

        # Verify password was changed by trying to login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_regular_user["email"],
                "password": new_password,
            },
        )

        assert login_response.status_code == 200

    async def test_change_password_wrong_current_password(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test changing password with wrong current password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == 401

    async def test_change_password_weak_new_password(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test changing password with weak new password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=user_headers,
            json={
                "current_password": test_regular_user["password"],
                "new_password": "weak",
            },
        )

        assert response.status_code == 422  # Pydantic validation error

    async def test_change_password_without_token(self, client: AsyncClient):
        """Test changing password without authentication."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == 403


# ============================================================================
# PROFILE TESTS
# ============================================================================


@pytest.mark.auth
class TestProfile:
    """Test user profile endpoints."""

    async def test_get_profile(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test getting user profile."""
        response = await client.get(
            "/api/v1/auth/profile",
            headers=user_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_regular_user["email"]
        assert data["full_name"] == test_regular_user["full_name"]
        assert data["role"] == test_regular_user["role"]
        assert "created_at" in data

    async def test_update_profile(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test updating user profile."""
        new_name = "Updated Test Name"

        response = await client.put(
            "/api/v1/auth/profile",
            headers=user_headers,
            json={"full_name": new_name},
        )

        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Profile updated successfully"

        # Verify update
        user = await fetch_one(
            "SELECT full_name FROM user_profiles WHERE id = $1",
            test_regular_user["id"],
        )

        assert user["full_name"] == new_name

    async def test_update_profile_without_token(self, client: AsyncClient):
        """Test updating profile without authentication."""
        response = await client.put(
            "/api/v1/auth/profile",
            json={"full_name": "New Name"},
        )

        assert response.status_code == 403


# ============================================================================
# PASSWORD RESET TESTS
# ============================================================================


@pytest.mark.auth
class TestPasswordReset:
    """Test password reset flow."""

    async def test_forgot_password_always_returns_success(
        self, client: AsyncClient, test_regular_user
    ):
        """Test forgot password returns success (prevents email enumeration)."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_regular_user["email"]},
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    async def test_forgot_password_with_nonexistent_email(self, client: AsyncClient):
        """Test forgot password with non-existent email still returns success."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@test.com"},
        )

        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
