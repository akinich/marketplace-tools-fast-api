"""
Run migration 016: Create purchase_orders placeholder table
Uses the app's existing database connection utilities
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_pool
from pathlib import Path

async def run_migration():
    """Run the migration SQL file"""
    print("🚀 Starting migration 016...")
    
    # Read migration file
    migration_file = Path(__file__).parent / 'migrations' / '016_purchase_orders_placeholder.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Get database pool
    try:
        pool = await get_pool()
        print("🔗 Connected to database")
        
        # Execute migration
        async with pool.acquire() as conn:
            await conn.execute(sql)
        
        print("✅ Migration 016 executed successfully!")
        print("✅ purchase_orders table created!")
        
        await pool.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)
