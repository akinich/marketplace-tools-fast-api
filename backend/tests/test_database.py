"""
================================================================================
Farm Management System - Database Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-24

Description:
    Tests for database connection, query helpers, and transaction management.

================================================================================
"""

import pytest
from app import database
from app.database import (
    fetch_one,
    fetch_all,
    execute_query,
    execute_many,
    check_database_health,
    build_where_clause,
    paginate_query,
    DatabaseTransaction,
    fetch_one_tx,
    fetch_all_tx,
    execute_query_tx,
)


# ============================================================================
# DATABASE CONNECTION TESTS
# ============================================================================


@pytest.mark.database
class TestDatabaseConnection:
    """Test database connection and health checks."""

    async def test_database_pool_is_connected(self):
        """Test that database pool is initialized and connected."""
        assert database.pool is not None
        assert not database.pool._closed

    async def test_database_health_check(self):
        """Test database health check returns True."""
        is_healthy = await check_database_health()
        assert is_healthy is True

    async def test_can_acquire_connection(self):
        """Test that we can acquire a connection from the pool."""
        async with database.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1


# ============================================================================
# QUERY HELPER TESTS
# ============================================================================


@pytest.mark.database
class TestQueryHelpers:
    """Test database query helper functions."""

    async def test_fetch_one_returns_dict(self):
        """Test fetch_one returns a single row as dict."""
        result = await fetch_one("SELECT 1 as number, 'test' as text")

        assert isinstance(result, dict)
        assert result["number"] == 1
        assert result["text"] == "test"

    async def test_fetch_one_returns_none_when_no_results(self):
        """Test fetch_one returns None when no results."""
        result = await fetch_one("SELECT 1 WHERE 1 = 0")

        assert result is None

    async def test_fetch_all_returns_list_of_dicts(self):
        """Test fetch_all returns list of dicts."""
        result = await fetch_all(
            """
            SELECT * FROM (
                VALUES (1, 'first'), (2, 'second'), (3, 'third')
            ) AS t(id, name)
            """
        )

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[0]["name"] == "first"
        assert result[2]["id"] == 3
        assert result[2]["name"] == "third"

    async def test_fetch_all_returns_empty_list_when_no_results(self):
        """Test fetch_all returns empty list when no results."""
        result = await fetch_all("SELECT 1 WHERE 1 = 0")

        assert isinstance(result, list)
        assert len(result) == 0

    async def test_fetch_with_parameters(self):
        """Test query with parameters using $1, $2 placeholders."""
        result = await fetch_one(
            "SELECT $1::int as num, $2::text as text", 42, "hello"
        )

        assert result["num"] == 42
        assert result["text"] == "hello"


# ============================================================================
# INSERT/UPDATE/DELETE TESTS
# ============================================================================


@pytest.mark.database
class TestExecuteQuery:
    """Test execute_query for INSERT, UPDATE, DELETE operations."""

    async def test_insert_with_returning_single_column(self, test_admin_user):
        """Test INSERT with RETURNING single column."""
        # Insert a test API key
        api_key_id = await execute_query(
            """
            INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
            VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
            RETURNING id
            """,
            test_admin_user["id"],
            "Test Key",
            "test_key_hash_123",
            "farm_test...",
            ["read"],
        )

        # Should return the ID directly
        assert api_key_id is not None
        assert isinstance(api_key_id, int)

    async def test_insert_with_returning_multiple_columns(self, test_admin_user):
        """Test INSERT with RETURNING multiple columns."""
        # Insert a test API key
        result = await execute_query(
            """
            INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
            VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
            RETURNING id, name, key_hash
            """,
            test_admin_user["id"],
            "Multi Return Key",
            "test_key_hash_456",
            "farm_multi...",
            ["read", "write"],
        )

        # Should return a dict
        assert isinstance(result, dict)
        assert result["id"] is not None
        assert result["name"] == "Multi Return Key"
        assert result["key_hash"] == "test_key_hash_456"

    async def test_update_query(self, test_regular_user):
        """Test UPDATE query."""
        # Update user's full name
        await execute_query(
            "UPDATE user_profiles SET full_name = $1 WHERE id = $2",
            "Updated Name",
            test_regular_user["id"],
        )

        # Verify update
        user = await fetch_one(
            "SELECT full_name FROM user_profiles WHERE id = $1",
            test_regular_user["id"],
        )

        assert user["full_name"] == "Updated Name"

    async def test_delete_query(self, test_admin_user):
        """Test DELETE query."""
        # Insert a test API key
        key_id = await execute_query(
            """
            INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
            VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
            RETURNING id
            """,
            test_admin_user["id"],
            "Delete Test Key",
            "test_key_hash_delete",
            "farm_delete...",
            ["read"],
        )

        # Delete the key
        await execute_query("DELETE FROM api_keys WHERE id = $1", key_id)

        # Verify deletion
        result = await fetch_one("SELECT * FROM api_keys WHERE id = $1", key_id)
        assert result is None

    async def test_execute_many(self, test_admin_user):
        """Test bulk insert with execute_many."""
        # Insert multiple API keys
        values = [
            (test_admin_user["id"], f"Key {i}", f"key_hash_{i}", f"farm_{i}...", ["read"])
            for i in range(3)
        ]

        await execute_many(
            """
            INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
            VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
            """,
            values,
        )

        # Verify insertions
        keys = await fetch_all(
            "SELECT name FROM api_keys WHERE user_id = $1 ORDER BY name",
            test_admin_user["id"],
        )

        assert len(keys) >= 3


# ============================================================================
# TRANSACTION TESTS
# ============================================================================


@pytest.mark.database
class TestTransactions:
    """Test database transaction handling."""

    async def test_transaction_commit_on_success(self, test_admin_user):
        """Test transaction commits when no exception occurs."""
        async with DatabaseTransaction() as conn:
            # Insert API key within transaction
            key_id = await execute_query_tx(
                """
                INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
                VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
                RETURNING id
                """,
                test_admin_user["id"],
                "Transaction Test",
                "test_key_hash_trans",
                "farm_trans...",
                ["read"],
                conn=conn,
            )

        # Verify data was committed
        result = await fetch_one(
            "SELECT * FROM api_keys WHERE id = $1", key_id
        )
        assert result is not None
        assert result["name"] == "Transaction Test"

    async def test_transaction_rollback_on_exception(self, test_admin_user):
        """Test transaction rolls back when exception occurs."""
        key_id = None

        try:
            async with DatabaseTransaction() as conn:
                # Insert API key
                key_id = await execute_query_tx(
                    """
                    INSERT INTO api_keys (user_id, name, key_hash, key_prefix, scopes, expires_at)
                    VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '1 day')
                    RETURNING id
                    """,
                    test_admin_user["id"],
                    "Rollback Test",
                    "rollback_key",
                    ["read"],
                    conn=conn,
                )

                # Raise exception to trigger rollback
                raise Exception("Test exception")
        except Exception:
            pass

        # Verify data was rolled back (should not exist)
        if key_id:
            result = await fetch_one(
                "SELECT * FROM api_keys WHERE id = $1", key_id
            )
            assert result is None

    async def test_transaction_aware_fetch_one(self, test_admin_user):
        """Test fetch_one_tx works within transaction."""
        async with DatabaseTransaction() as conn:
            result = await fetch_one_tx(
                "SELECT $1 as value",
                "test",
                conn=conn,
            )

            assert result["value"] == "test"

    async def test_transaction_aware_fetch_all(self, test_admin_user):
        """Test fetch_all_tx works within transaction."""
        async with DatabaseTransaction() as conn:
            results = await fetch_all_tx(
                "SELECT * FROM (VALUES (1), (2), (3)) AS t(num)",
                conn=conn,
            )

            assert len(results) == 3
            assert results[0]["num"] == 1


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================


@pytest.mark.database
class TestUtilityFunctions:
    """Test database utility functions."""

    def test_build_where_clause_with_filters(self):
        """Test build_where_clause generates correct SQL."""
        filters = {"status": "active", "role": "Admin"}

        where_clause, values = build_where_clause(filters)

        assert "WHERE" in where_clause
        assert "status = $1" in where_clause
        assert "role = $2" in where_clause
        assert "AND" in where_clause
        assert values == ["active", "Admin"]

    def test_build_where_clause_empty_filters(self):
        """Test build_where_clause with no filters."""
        where_clause, values = build_where_clause({})

        assert where_clause == ""
        assert values == []

    def test_build_where_clause_with_none_values(self):
        """Test build_where_clause skips None values."""
        filters = {"status": "active", "role": None}

        where_clause, values = build_where_clause(filters)

        assert "status = $1" in where_clause
        assert "role" not in where_clause
        assert values == ["active"]

    def test_paginate_query(self):
        """Test paginate_query adds LIMIT and OFFSET."""
        base_query = "SELECT * FROM users"

        # Page 1, page_size 20
        query, offset = paginate_query(base_query, page=1, page_size=20)
        assert "LIMIT 20 OFFSET 0" in query
        assert offset == 0

        # Page 2, page_size 20
        query, offset = paginate_query(base_query, page=2, page_size=20)
        assert "LIMIT 20 OFFSET 20" in query
        assert offset == 20

        # Page 3, page_size 50
        query, offset = paginate_query(base_query, page=3, page_size=50)
        assert "LIMIT 50 OFFSET 100" in query
        assert offset == 100
