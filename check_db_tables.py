"""
Quick script to check what tables exist in the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

async def check_tables():
    """Check what tables exist in the database"""
    database_url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)

        # Get all tables in public schema
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"\n✅ Found {len(tables)} tables in database:\n")
        for table in tables:
            print(f"  - {table['table_name']}")

        # Check for specific tables related to the migrations
        expected_tables = [
            'system_settings',
            'settings_audit_log',
            'email_templates',
            'email_queue',
            'email_recipients',
            'email_send_log',
            'webhooks',
            'webhook_deliveries',
            'api_keys',
            'api_key_usage'
        ]

        existing_table_names = [t['table_name'] for t in tables]

        print("\n📊 Migration Tables Status:\n")
        for table in expected_tables:
            status = "✅" if table in existing_table_names else "❌"
            print(f"  {status} {table}")

        # Check for columns in key tables
        if 'webhooks' in existing_table_names:
            print("\n🔍 Webhooks table columns:")
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'webhooks'
                ORDER BY ordinal_position
            """)
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")

        if 'api_keys' in existing_table_names:
            print("\n🔍 API Keys table columns:")
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'api_keys'
                ORDER BY ordinal_position
            """)
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")

        await conn.close()

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())
