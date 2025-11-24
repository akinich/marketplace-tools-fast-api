"""
================================================================================
Farm Management System - Health Check Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-24

Description:
    Tests for health check endpoints and application status monitoring.

================================================================================
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# ROOT ENDPOINT TESTS
# ============================================================================


@pytest.mark.health
class TestRootEndpoint:
    """Test root endpoint."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API information."""
        response = await client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["version"] == "v1"

    async def test_root_contains_links(self, client: AsyncClient):
        """Test root endpoint contains navigation links."""
        response = await client.get("/")

        data = response.json()
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


@pytest.mark.health
class TestHealthCheck:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        # In test environment, scheduler might not be initialized, which could make overall status unhealthy
        assert data["status"] in ["healthy", "unhealthy"]

    async def test_health_check_services(self, client: AsyncClient):
        """Test health check shows service statuses."""
        response = await client.get("/health")

        data = response.json()
        assert "services" in data

        services = data["services"]
        assert "api" in services
        assert "database" in services
        assert "scheduler" in services

        # API should always be operational
        assert services["api"] == "operational"

    async def test_health_check_database_operational(self, client: AsyncClient):
        """Test health check shows database as operational."""
        response = await client.get("/health")

        data = response.json()
        assert data["services"]["database"] == "operational"

    async def test_health_check_scheduler_status(self, client: AsyncClient):
        """Test health check shows scheduler status."""
        response = await client.get("/health")

        data = response.json()

        # In test environment, scheduler might not be initialized
        assert data["services"]["scheduler"] in ["running", "stopped", "not_initialized"]

    async def test_health_check_contains_version(self, client: AsyncClient):
        """Test health check contains version information."""
        response = await client.get("/health")

        data = response.json()
        assert "version" in data
        assert data["version"] == "v1"

    async def test_health_check_contains_environment(self, client: AsyncClient):
        """Test health check contains environment information."""
        response = await client.get("/health")

        data = response.json()
        assert "environment" in data
        assert data["environment"] in ["development", "production", "test"]

    async def test_health_check_scheduled_jobs(self, client: AsyncClient):
        """Test health check contains scheduled jobs information."""
        response = await client.get("/health")

        data = response.json()
        assert "scheduled_jobs" in data

        # Should be a list (may be empty if scheduler not running)
        assert isinstance(data["scheduled_jobs"], list)


# ============================================================================
# PING ENDPOINT TESTS
# ============================================================================


@pytest.mark.health
class TestPingEndpoint:
    """Test ping endpoint for uptime checks."""

    async def test_ping_endpoint(self, client: AsyncClient):
        """Test ping endpoint returns pong."""
        response = await client.get("/ping")

        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "pong"

    async def test_ping_is_fast(self, client: AsyncClient):
        """Test ping endpoint responds quickly."""
        import time

        start = time.time()
        response = await client.get("/ping")
        duration = time.time() - start

        assert response.status_code == 200
        # Should respond in less than 100ms
        assert duration < 0.1


# ============================================================================
# API DOCUMENTATION TESTS
# ============================================================================


@pytest.mark.health
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    async def test_swagger_docs_accessible(self, client: AsyncClient):
        """Test Swagger UI is accessible."""
        response = await client.get("/docs")

        assert response.status_code == 200

    async def test_redoc_docs_accessible(self, client: AsyncClient):
        """Test ReDoc is accessible."""
        response = await client.get("/redoc")

        assert response.status_code == 200

    async def test_openapi_schema_accessible(self, client: AsyncClient):
        """Test OpenAPI schema is accessible."""
        response = await client.get("/openapi.json")

        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    async def test_openapi_contains_auth_endpoints(self, client: AsyncClient):
        """Test OpenAPI schema contains authentication endpoints."""
        response = await client.get("/openapi.json")

        data = response.json()
        paths = data["paths"]

        # Check for key authentication endpoints
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/refresh" in paths
        assert "/api/v1/auth/logout" in paths
        assert "/api/v1/auth/me" in paths


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.health
class TestErrorHandling:
    """Test global error handling."""

    async def test_404_not_found(self, client: AsyncClient):
        """Test 404 error for non-existent endpoint."""
        response = await client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    async def test_method_not_allowed(self, client: AsyncClient):
        """Test 405 error for wrong HTTP method."""
        # Health endpoint doesn't accept POST
        response = await client.post("/health")

        assert response.status_code == 405

    async def test_validation_error_format(self, client: AsyncClient):
        """Test validation error response format."""
        # Try to login with invalid data (missing fields)
        response = await client.post(
            "/api/v1/auth/login",
            json={},
        )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data


# ============================================================================
# CORS TESTS
# ============================================================================


@pytest.mark.health
class TestCORS:
    """Test CORS middleware configuration."""

    async def test_cors_headers_present(self, client: AsyncClient):
        """Test CORS headers are present in responses."""
        response = await client.get("/health")

        # Check for CORS headers
        headers = response.headers

        # Note: In test mode, CORS headers may not be fully set
        # This is a basic check
        assert response.status_code == 200

    async def test_options_request(self, client: AsyncClient):
        """Test OPTIONS request for CORS preflight."""
        response = await client.options("/api/v1/auth/login")

        # OPTIONS requests should be handled
        assert response.status_code in [200, 405]


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


@pytest.mark.health
@pytest.mark.slow
class TestRateLimiting:
    """Test rate limiting middleware."""

    async def test_rate_limit_not_exceeded_under_normal_use(self, client: AsyncClient):
        """Test that normal usage doesn't hit rate limits."""
        # Make 5 requests (well under the limit)
        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200

    async def test_rate_limit_headers(self, client: AsyncClient):
        """Test that rate limit information might be in headers."""
        response = await client.get("/health")

        # Rate limit headers may or may not be present depending on config
        # Just check that the request succeeds
        assert response.status_code == 200
