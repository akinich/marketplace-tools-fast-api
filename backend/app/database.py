"""
================================================================================
Farm Management System - Database Connection Manager
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial database setup
  - Async PostgreSQL connection using databases library
  - Connection pool management
  - Supabase client initialization
  - Helper functions for queries

================================================================================
"""

from databases import Database
from supabase import create_client, Client
from typing import Optional, Dict, List, Any
import logging

from app.config import settings

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE INSTANCES
# ============================================================================

# Async PostgreSQL database connection
database: Optional[Database] = None

# Supabase client (for Auth and convenience methods)
supabase: Optional[Client] = None


# ============================================================================
# DATABASE LIFECYCLE
# ============================================================================


async def connect_db():
    """
    Initialize database connections on application startup.
    Called from main.py startup event.
    """
    global database, supabase

    try:
        # Initialize async PostgreSQL connection
        database = Database(
            settings.DATABASE_URL,
            min_size=settings.DATABASE_POOL_MIN,
            max_size=settings.DATABASE_POOL_MAX,
        )
        await database.connect()
        logger.info(
            f"✅ Database connected (Pool: {settings.DATABASE_POOL_MIN}-{settings.DATABASE_POOL_MAX})"
        )

        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase client initialized")

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


async def disconnect_db():
    """
    Close database connections on application shutdown.
    Called from main.py shutdown event.
    """
    global database

    try:
        if database:
            await database.disconnect()
            logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error(f"❌ Database disconnection error: {e}")


# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================


def get_db() -> Database:
    """
    Get database instance for dependency injection.

    Usage:
        @router.get("/items")
        async def get_items(db: Database = Depends(get_db)):
            results = await db.fetch_all("SELECT * FROM items")
    """
    return database


def get_supabase() -> Client:
    """
    Get Supabase client for dependency injection.

    Usage:
        @router.post("/auth/login")
        async def login(sb: Client = Depends(get_supabase)):
            result = sb.auth.sign_in_with_password(...)
    """
    return supabase


# ============================================================================
# QUERY HELPERS
# ============================================================================


async def fetch_one(query: str, *values) -> Optional[Dict]:
    """
    Execute query and return single row as dict.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        *values: Values to bind to placeholders

    Returns:
        Dict with column names as keys, or None if no results
    """
    try:
        result = await database.fetch_one(query=query, values=values)
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Query error (fetch_one): {e}")
        raise


async def fetch_all(query: str, *values) -> List[Dict]:
    """
    Execute query and return all rows as list of dicts.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        *values: Values to bind to placeholders

    Returns:
        List of dicts, empty list if no results
    """
    try:
        results = await database.fetch_all(query=query, values=values)
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Query error (fetch_all): {e}")
        raise


async def execute(query: str, *values) -> Any:
    """
    Execute INSERT, UPDATE, DELETE query.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        *values: Values to bind to placeholders

    Returns:
        Result of the query execution
    """
    try:
        result = await database.execute(query=query, values=values)
        return result
    except Exception as e:
        logger.error(f"Query error (execute): {e}")
        raise


async def execute_many(query: str, values: List[Dict]) -> None:
    """
    Execute query multiple times with different values (bulk insert).

    Args:
        query: SQL query with :key placeholders
        values: List of dicts with values

    Example:
        await execute_many(
            "INSERT INTO items (name, price) VALUES (:name, :price)",
            [{"name": "Item1", "price": 10}, {"name": "Item2", "price": 20}]
        )
    """
    try:
        await database.execute_many(query=query, values=values)
    except Exception as e:
        logger.error(f"Query error (execute_many): {e}")
        raise


# ============================================================================
# TRANSACTION HELPERS
# ============================================================================


class DatabaseTransaction:
    """
    Context manager for database transactions.

    Usage:
        async with DatabaseTransaction():
            await execute("INSERT INTO items ...")
            await execute("UPDATE stock ...")
            # Commits if no exception, rolls back otherwise
    """

    def __init__(self):
        self.transaction = None

    async def __aenter__(self):
        self.transaction = await database.transaction()
        await self.transaction.__aenter__()
        return self.transaction

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            await self.transaction.__aexit__(exc_type, exc_val, exc_tb)


# ============================================================================
# HEALTH CHECK
# ============================================================================


async def check_database_health() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if healthy, False otherwise
    """
    try:
        await database.fetch_one("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def build_where_clause(filters: Dict[str, Any]) -> tuple[str, List]:
    """
    Build WHERE clause from filters dict.

    Args:
        filters: Dict of column: value pairs

    Returns:
        Tuple of (WHERE clause string, list of values)

    Example:
        filters = {"status": "active", "role": "admin"}
        -> ("WHERE status = $1 AND role = $2", ["active", "admin"])
    """
    if not filters:
        return "", []

    conditions = []
    values = []
    param_count = 1

    for key, value in filters.items():
        if value is not None:
            conditions.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_clause, values


def paginate_query(
    base_query: str, page: int = 1, page_size: int = 20
) -> tuple[str, int]:
    """
    Add pagination to a query.

    Args:
        base_query: Original SQL query
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Tuple of (query with LIMIT/OFFSET, offset value)
    """
    offset = (page - 1) * page_size
    paginated_query = f"{base_query} LIMIT {page_size} OFFSET {offset}"
    return paginated_query, offset
