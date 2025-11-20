"""
================================================================================
Farm Management System - Development Planning Module Migration Runner
================================================================================
Version: 1.0.0
Created: 2025-11-20
Last Updated: 2025-11-20

Description:
  Runs the development planning module database migration to create:
  - features table (for tracking development features)
  - feature_steps table (for breaking down features into steps)
  - feature_comments table (for discussion and collaboration)
  - Development module registration in modules table

Usage:
  python run_development_migration.py

Changelog:
----------
v1.0.0 (2025-11-20):
  - Initial migration runner for development planning module
  - Executes development_module_v1.0.0.sql migration script
  - Verifies table creation and module registration
  - Provides detailed output of migration results

================================================================================
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_db, disconnect_db, pool
import asyncpg


async def run_migration():
    """Run the development module migration SQL file"""
    print("🚀 Starting development planning module migration...")

    # Connect to database
    await connect_db()

    try:
        # Read migration file
        migration_file = Path(__file__).parent / "migrations" / "development_module_v1.0.0.sql"

        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        print(f"📄 Reading migration file: {migration_file}")
        sql_content = migration_file.read_text()

        # Execute migration
        print("⚙️  Executing migration...")
        async with pool.acquire() as conn:
            # Execute the entire SQL file
            await conn.execute(sql_content)

        print("✅ Migration completed successfully!")

        # Verify tables were created
        async with pool.acquire() as conn:
            # Check for features table
            result = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('features', 'feature_steps', 'feature_comments')
                ORDER BY table_name
                """
            )

            print(f"\n📊 Created {len(result)} development tables:")
            for row in result:
                print(f"   - {row['table_name']}")

            # Check if module was added
            module = await conn.fetchrow(
                """
                SELECT module_key, module_name, is_active
                FROM modules
                WHERE module_key = 'development'
                """
            )

            if module:
                print(f"\n📦 Module registered:")
                print(f"   - {module['module_name']} ({module['module_key']})")
                print(f"   - Active: {module['is_active']}")
            else:
                print("\n⚠️  Warning: Development module not found in modules table")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Disconnect from database
        await disconnect_db()


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
