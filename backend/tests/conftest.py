"""
================================================================================
Farm Management System - Test Configuration & Fixtures
================================================================================
Version: 1.2.0
Last Updated: 2025-11-25

Changelog:
----------
v1.2.0 (2025-11-25):
  - Added cleanup for Phase 2 test modules (tickets, ticket_comments)
  - Added cleanup for user_module_permissions table
  - Improved cleanup organization with comments
  - Enhanced webhook cleanup to handle created_by column

v1.1.0 (2025-11-24):
  - Updated cleanup queries to use production table names
  - Changed login_attempts → login_history
  - Changed active_sessions → user_sessions
  - Fixed cleanup order to respect foreign key constraints
  - Ensures proper test isolation and cleanup after each test

v1.0.0 (2025-11-24):
  - Initial test infrastructure
  - Created pytest fixtures for database, HTTP client, and users
  - Implemented automatic test cleanup with proper dependency ordering
  - Added test user fixtures (admin, regular, inactive)
  - Added authentication token fixtures
  - Configured async test support with pytest-asyncio

Description:
    Pytest configuration and shared fixtures for testing.
    Provides test database, test client, and user fixtures.
    Handles automatic cleanup of test data after each test run.

Features:
  - Session-scoped database connection pool
  - Test-scoped automatic cleanup with foreign key handling
  - Pre-configured admin, regular, and inactive user fixtures
  - JWT token generation for authenticated endpoint testing
  - HTTP client with proper ASGI transport setup

================================================================================
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
import asyncpg

# Set test environment before importing app
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"

from app.main import app
from app.database import pool, connect_db, disconnect_db, execute_query, fetch_one
from app.config import settings
from app.auth.password import hash_password


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    Required for pytest-asyncio to work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Setup test database connection for the entire test session.
    Runs once before all tests.
    """
    # Connect to database
    await connect_db()

    yield

    # Disconnect after all tests
    await disconnect_db()


@pytest.fixture(autouse=True)
async def cleanup_database():
    """
    Clean up database after each test.
    Rolls back any changes made during the test.
    """
    # Run test
    yield

    # Clean up test data (delete in reverse order of dependencies)
    cleanup_queries = [
        # Ticket-related cleanup
        "DELETE FROM ticket_comments WHERE ticket_id IN (SELECT id FROM tickets WHERE created_by_id IN (SELECT id FROM users WHERE email LIKE '%@test.com'))",
        "DELETE FROM tickets WHERE created_by_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        # Session and auth cleanup
        "DELETE FROM login_history WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM user_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM activity_logs WHERE user_email LIKE '%@test.com'",
        # Webhook cleanup
        "DELETE FROM webhook_deliveries",
        "DELETE FROM webhooks WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM email_queue",
        # API keys and user cleanup
        "DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM user_module_permissions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM user_profiles WHERE id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
        "DELETE FROM users WHERE email LIKE '%@test.com'",
    ]

    for query in cleanup_queries:
        try:
            await execute_query(query)
        except Exception:
            # Ignore errors if table doesn't exist or no data to clean
            pass


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# USER FIXTURES
# ============================================================================


@pytest.fixture
async def test_admin_user() -> Dict:
    """
    Create a test admin user.

    Returns:
        Dict with user_id, email, password, full_name, role
    """
    email = "admin@test.com"
    password = "AdminPass123!"
    full_name = "Test Admin"
    role_name = "Admin"

    # Hash password
    hashed_password = hash_password(password)

    # Get Admin role ID
    role = await fetch_one("SELECT id FROM roles WHERE role_name = $1", role_name)
    role_id = role["id"] if role else 1

    # Create user in users table (simulates auth.users)
    user_id = await execute_query(
        """
        INSERT INTO users (email)
        VALUES ($1)
        RETURNING id
        """,
        email,
    )

    # Create user profile with all auth data
    await execute_query(
        """
        INSERT INTO user_profiles (id, full_name, role_id, password_hash, is_active, must_change_password)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id,
        full_name,
        role_id,
        hashed_password,
        True,
        False,
    )

    return {
        "id": str(user_id),  # Convert UUID to string for JSON serialization
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": role_name,
    }


@pytest.fixture
async def test_regular_user() -> Dict:
    """
    Create a test regular user.

    Returns:
        Dict with user_id, email, password, full_name, role
    """
    email = "user@test.com"
    password = "UserPass123!"
    full_name = "Test User"
    role_name = "User"

    # Hash password
    hashed_password = hash_password(password)

    # Get User role ID
    role = await fetch_one("SELECT id FROM roles WHERE role_name = $1", role_name)
    role_id = role["id"] if role else 2

    # Create user in users table (simulates auth.users)
    user_id = await execute_query(
        """
        INSERT INTO users (email)
        VALUES ($1)
        RETURNING id
        """,
        email,
    )

    # Create user profile with all auth data
    await execute_query(
        """
        INSERT INTO user_profiles (id, full_name, role_id, password_hash, is_active, must_change_password)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id,
        full_name,
        role_id,
        hashed_password,
        True,
        False,
    )

    return {
        "id": str(user_id),  # Convert UUID to string for JSON serialization
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": role_name,
    }


@pytest.fixture
async def test_inactive_user() -> Dict:
    """
    Create a test inactive user.

    Returns:
        Dict with user_id, email, password, full_name, role
    """
    email = "inactive@test.com"
    password = "InactivePass123!"
    full_name = "Inactive User"
    role_name = "User"

    # Hash password
    hashed_password = hash_password(password)

    # Get User role ID
    role = await fetch_one("SELECT id FROM roles WHERE role_name = $1", role_name)
    role_id = role["id"] if role else 2

    # Create user in users table (simulates auth.users)
    user_id = await execute_query(
        """
        INSERT INTO users (email)
        VALUES ($1)
        RETURNING id
        """,
        email,
    )

    # Create inactive user profile
    await execute_query(
        """
        INSERT INTO user_profiles (id, full_name, role_id, password_hash, is_active, must_change_password)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id,
        full_name,
        role_id,
        hashed_password,
        False,  # is_active = False
        False,
    )

    return {
        "id": str(user_id),  # Convert UUID to string for JSON serialization
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": role_name,
    }


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================


@pytest.fixture
async def admin_token(client: AsyncClient, test_admin_user: Dict) -> str:
    """
    Get JWT access token for admin user.

    Returns:
        JWT access token string
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_admin_user["email"],
            "password": test_admin_user["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def user_token(client: AsyncClient, test_regular_user: Dict) -> str:
    """
    Get JWT access token for regular user.

    Returns:
        JWT access token string
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_regular_user["email"],
            "password": test_regular_user["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def admin_headers(admin_token: str) -> Dict[str, str]:
    """
    Get authorization headers for admin user.

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def user_headers(user_token: str) -> Dict[str, str]:
    """
    Get authorization headers for regular user.

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {user_token}"}


# ============================================================================
# HELPER FIXTURES
# ============================================================================


@pytest.fixture
def valid_user_data() -> Dict:
    """
    Get valid user registration data for testing.

    Returns:
        Dict with email, password, full_name, role
    """
    return {
        "email": "newuser@test.com",
        "password": "NewUserPass123!",
        "full_name": "New Test User",
        "role": "User",
    }


@pytest.fixture
def invalid_password_data() -> Dict:
    """
    Get various invalid password test cases.

    Returns:
        Dict with different invalid password scenarios
    """
    return {
        "too_short": "Pass1!",
        "no_uppercase": "password123!",
        "no_lowercase": "PASSWORD123!",
        "no_digit": "Password!",
        "no_special": "Password123",
    }
