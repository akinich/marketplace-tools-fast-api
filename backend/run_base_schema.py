"""
================================================================================
Farm Management System - Base Schema Migration Runner
================================================================================
Version: 1.0.0
Created: 2025-11-27

Description:
  Runs the base schema migration (000_base_schema.sql) to create core tables
  including users, user_profiles, roles, sessions, and other foundational tables.

Usage:
  python run_base_schema.py

Changelog:
----------
v1.0.0 (2025-11-27):
  - Initial base schema migration runner
  - Creates users table and core authentication tables
  - Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS)

================================================================================
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_db, disconnect_db, pool


async def run_base_schema():
    """Run the base schema migration"""
    print("🚀 Starting base schema migration...")
    print("=" * 60)

    # Connect to database
    await connect_db()

    try:
        # Read migration file
        migration_file = Path(__file__).parent / "migrations" / "000_base_schema.sql"

        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        print(f"📄 Reading migration file: {migration_file.name}")
        sql_content = migration_file.read_text()

        # Execute migration
        print("⚙️  Executing base schema migration...")
        async with pool.acquire() as conn:
            # Execute the entire SQL file
            await conn.execute(sql_content)

        print("✅ Base schema migration completed successfully!")
        print()

        # Verify tables were created
        async with pool.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name IN (
                    'users', 'user_profiles', 'roles', 'modules',
                    'login_history', 'user_sessions', 'activity_logs',
                    'webhooks', 'webhook_deliveries', 'email_queue',
                    'user_module_permissions'
                )
                ORDER BY table_name
                """
            )

            print(f"📊 Created/verified {len(result)} core tables:")
            for row in result:
                print(f"   ✓ {row['table_name']}")

            # Check if users table exists and has the expected structure
            print()
            users_check = await conn.fetchrow(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'users'
                ) as exists
                """
            )

            if users_check['exists']:
                print("✅ Users table verified successfully!")

                # Show user count
                user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                print(f"   Current user count: {user_count}")
            else:
                print("❌ Users table was not created!")
                return False

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Disconnect from database
        await disconnect_db()
        print("=" * 60)


if __name__ == "__main__":
    success = asyncio.run(run_base_schema())
    if success:
        print("✨ Base schema migration completed successfully!")
    else:
        print("⚠️  Base schema migration failed. Please check the errors above.")
    sys.exit(0 if success else 1)
