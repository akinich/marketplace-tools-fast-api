"""
Simple migration runner for Batch Tracking module
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_db, disconnect_db, pool
import asyncpg


async def run_migration():
    """Run the batch tracking migration SQL file"""
    print("🚀 Starting Batch Tracking module migration...")

    # Connect to database
    await connect_db()

    try:
        # Read migration file
        migration_file = Path(__file__).parent / "migrations" / "014_batch_tracking_clean.sql"

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
            result = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('batches', 'batch_history', 'batch_documents', 'batch_sequence')
                ORDER BY table_name
                """
            )

            print(f"\n📊 Created {len(result)} batch tracking tables:")
            for row in result:
                print(f"   - {row['table_name']}")

            # Check batch_sequence configuration
            seq_result = await conn.fetchrow(
                """
                SELECT
                    prefix,
                    current_number,
                    financial_year,
                    fy_start_date,
                    fy_end_date,
                    CONCAT(prefix, '/', financial_year, '/', LPAD((current_number + 1)::text, 4, '0')) as next_batch_number
                FROM batch_sequence
                WHERE id = 1
                """
            )

            if seq_result:
                print(f"\n🔢 Batch sequence configuration:")
                print(f"   - Prefix: {seq_result['prefix']}")
                print(f"   - Financial Year: {seq_result['financial_year']}")
                print(f"   - FY Period: {seq_result['fy_start_date']} to {seq_result['fy_end_date']}")
                print(f"   - Current Number: {seq_result['current_number']}")
                print(f"   - Next Batch: {seq_result['next_batch_number']}")

        print("\n🎉 Batch Tracking module ready for testing!")
        print("   Start FastAPI server: uvicorn app.main:app --reload")
        print("   Open Swagger UI: http://localhost:8000/docs")

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
