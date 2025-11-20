"""
================================================================================
Farm Management System - Comprehensive Migration Runner
================================================================================
Version: 1.0.0
Created: 2025-11-20
Last Updated: 2025-11-20

Description:
  Comprehensive migration checker and runner for all Farm Management System modules.
  Intelligently detects which migrations have been applied and runs pending ones.

  Supported Migrations:
  - Biofloc Module (biofloc_tanks, biofloc_readings, etc.)
  - Biofloc Grading (biofloc_gradings)
  - Tickets Module (tickets, ticket_comments)
  - Development Planning Module (features, feature_steps, feature_comments)

Usage:
  python run_all_migrations.py

Features:
  - Automatic detection of applied migrations
  - Safe execution with error handling
  - Detailed migration summary report
  - Lists all tables and registered modules
  - Idempotent - safe to run multiple times

Changelog:
----------
v1.0.0 (2025-11-20):
  - Initial comprehensive migration runner
  - Checks for existence of key tables before running migrations
  - Runs all pending migrations in correct order
  - Provides detailed summary of database state
  - Reports all tables and active modules after completion

================================================================================
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_db, disconnect_db, pool


async def check_table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the database"""
    result = await conn.fetchrow(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = $1
        ) as exists
        """,
        table_name
    )
    return result['exists']


async def run_migration_file(conn, migration_file: Path) -> bool:
    """Run a single migration file"""
    try:
        print(f"📄 Reading migration file: {migration_file.name}")
        sql_content = migration_file.read_text()

        print(f"⚙️  Executing migration...")
        await conn.execute(sql_content)

        print(f"✅ Migration {migration_file.name} completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration {migration_file.name} failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_migrations():
    """Run all pending migrations"""
    print("🚀 Starting comprehensive migration check...")
    print("=" * 60)

    # Connect to database
    await connect_db()

    migrations_dir = Path(__file__).parent / "migrations"
    all_success = True

    try:
        async with pool.acquire() as conn:
            # Define migrations to check
            migrations = [
                {
                    "name": "Biofloc Module",
                    "file": "biofloc_module_v1.0.0.sql",
                    "check_table": "biofloc_tanks"
                },
                {
                    "name": "Biofloc Grading",
                    "file": "biofloc_grading_v1.0.1.sql",
                    "check_table": "biofloc_gradings"
                },
                {
                    "name": "Tickets Module",
                    "file": "tickets_module_v1.0.0.sql",
                    "check_table": "tickets"
                },
                {
                    "name": "Development Planning Module",
                    "file": "development_module_v1.0.0.sql",
                    "check_table": "features"
                }
            ]

            print(f"\n📋 Checking {len(migrations)} migrations...\n")

            for migration in migrations:
                print(f"🔍 Checking: {migration['name']}")
                migration_file = migrations_dir / migration["file"]

                if not migration_file.exists():
                    print(f"   ⚠️  Migration file not found: {migration['file']}")
                    continue

                # Check if already applied
                table_exists = await check_table_exists(conn, migration["check_table"])

                if table_exists:
                    print(f"   ✓ Already applied (table '{migration['check_table']}' exists)")
                else:
                    print(f"   ⏳ Running migration...")
                    success = await run_migration_file(conn, migration_file)
                    if not success:
                        all_success = False
                        print(f"   ❌ Failed to apply migration")
                    else:
                        print(f"   ✅ Successfully applied")

                print()

            # Summary
            print("=" * 60)
            print("📊 Migration Summary:")
            print()

            # List all tables
            result = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
                ORDER BY table_name
                """
            )

            print(f"Total tables in database: {len(result)}")
            for row in result:
                print(f"   - {row['table_name']}")

            # List modules
            print()
            modules = await conn.fetch(
                """
                SELECT module_key, module_name, is_active
                FROM modules
                ORDER BY display_order
                """
            )

            print(f"\nRegistered modules: {len(modules)}")
            for module in modules:
                status = "✓" if module['is_active'] else "✗"
                print(f"   {status} {module['module_name']} ({module['module_key']})")

        return all_success

    except Exception as e:
        print(f"❌ Migration process failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Disconnect from database
        await disconnect_db()
        print("\n" + "=" * 60)


if __name__ == "__main__":
    success = asyncio.run(run_all_migrations())
    if success:
        print("✨ All migrations completed successfully!")
    else:
        print("⚠️  Some migrations failed. Please check the errors above.")
    sys.exit(0 if success else 1)
