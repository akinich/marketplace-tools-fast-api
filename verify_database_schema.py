"""
Database Schema Verification Script
Checks if the database schema matches the code at commit 3fb0a16
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import connect_db, disconnect_db, fetch_all, fetch_one


async def verify_schema():
    """Verify that all required tables exist in the database"""

    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    print()

    # Required tables based on migrations at commit 3fb0a16
    required_tables = {
        'system_settings': 'Migration 008 - System Settings',
        'settings_audit_log': 'Migration 008 - Settings Audit',
        'email_templates': 'Migration 009 - Email Templates',
        'email_queue': 'Migration 009 - Email Queue',
        'email_recipients': 'Migration 009 - Email Recipients',
        'email_send_log': 'Migration 009 - Email Send Log',
        'webhooks': 'Migration 010 - Webhooks',
        'webhook_deliveries': 'Migration 010 - Webhook Deliveries',
        'api_keys': 'Migration 011 - API Keys',
        'api_key_usage': 'Migration 011 - API Key Usage'
    }

    try:
        # Connect to database
        await connect_db()
        print("✅ Connected to database\n")

        # Get all tables in public schema
        all_tables = await fetch_all("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        existing_table_names = {t['table_name'] for t in all_tables}

        print(f"Found {len(existing_table_names)} tables in database\n")

        # Check required tables
        print("CHECKING REQUIRED TABLES:")
        print("-" * 80)

        missing_tables = []
        present_tables = []

        for table, description in required_tables.items():
            if table in existing_table_names:
                print(f"✅ {table:<25} - {description}")
                present_tables.append(table)
            else:
                print(f"❌ {table:<25} - {description} (MISSING)")
                missing_tables.append(table)

        print()
        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"✅ Present: {len(present_tables)}/{len(required_tables)} tables")
        print(f"❌ Missing: {len(missing_tables)}/{len(required_tables)} tables")
        print()

        if missing_tables:
            print("⚠️  DATABASE NEEDS MIGRATION!")
            print()
            print("Missing tables:")
            for table in missing_tables:
                print(f"  - {table}")
            print()
            print("ACTIONS REQUIRED:")
            print("-" * 80)
            print("Run the following migration files in order:")

            # Map missing tables to migration files
            migration_map = {
                'system_settings': '008_system_settings.sql',
                'settings_audit_log': '008_system_settings.sql',
                'email_templates': '009_smtp_email.sql',
                'email_queue': '009_smtp_email.sql',
                'email_recipients': '009_smtp_email.sql',
                'email_send_log': '009_smtp_email.sql',
                'webhooks': '010_webhooks.sql',
                'webhook_deliveries': '010_webhooks.sql',
                'api_keys': '011_api_keys.sql',
                'api_key_usage': '011_api_keys.sql'
            }

            migrations_needed = set()
            for table in missing_tables:
                if table in migration_map:
                    migrations_needed.add(migration_map[table])

            for i, migration in enumerate(sorted(migrations_needed), 1):
                print(f"{i}. backend/migrations/{migration}")

            print()
            print("Run migrations using:")
            print("  psql <your_database_url> -f backend/migrations/<migration_file>")
            print()
            return False

        else:
            print("✅ DATABASE SCHEMA IS UP TO DATE!")
            print()
            print("All required tables are present. The rolled-back code matches")
            print("the current database schema.")
            print()

            # Additional validation - check key columns
            print("PERFORMING DETAILED VALIDATION:")
            print("-" * 80)

            # Check webhooks table structure
            webhooks_cols = await fetch_all("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'webhooks'
                ORDER BY ordinal_position
            """)

            expected_webhook_cols = ['id', 'name', 'url', 'secret', 'events', 'custom_headers',
                                      'is_active', 'timeout_seconds', 'retry_attempts',
                                      'retry_delay_seconds', 'description', 'created_by',
                                      'updated_by', 'created_at', 'updated_at']

            webhook_col_names = [col['column_name'] for col in webhooks_cols]

            all_present = all(col in webhook_col_names for col in expected_webhook_cols)

            if all_present:
                print("✅ Webhooks table structure verified")
            else:
                print("⚠️  Webhooks table structure may need updates")
                missing = [col for col in expected_webhook_cols if col not in webhook_col_names]
                if missing:
                    print(f"   Missing columns: {', '.join(missing)}")

            # Check api_keys table structure
            api_keys_cols = await fetch_all("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'api_keys'
                ORDER BY ordinal_position
            """)

            expected_api_key_cols = ['id', 'user_id', 'key_hash', 'key_prefix', 'name',
                                      'description', 'scopes', 'is_active', 'expires_at',
                                      'last_used_at', 'created_at', 'revoked_at']

            api_key_col_names = [col['column_name'] for col in api_keys_cols]

            all_present = all(col in api_key_col_names for col in expected_api_key_cols)

            if all_present:
                print("✅ API Keys table structure verified")
            else:
                print("⚠️  API Keys table structure may need updates")
                missing = [col for col in expected_api_key_cols if col not in api_key_col_names]
                if missing:
                    print(f"   Missing columns: {', '.join(missing)}")

            print()
            return True

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await disconnect_db()
        print("Disconnected from database")


if __name__ == "__main__":
    result = asyncio.run(verify_schema())
    sys.exit(0 if result else 1)
