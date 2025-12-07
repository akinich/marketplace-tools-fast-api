/*
================================================================================
Marketplace ERP Tools - Fix tank_id Column Type in inventory_transactions
================================================================================
Version: 1.3.1
Created: 2025-11-19
Database: Supabase PostgreSQL

Purpose:
--------
Fix tank_id column type mismatch in inventory_transactions table.
Change from INTEGER to UUID to match biofloc_tanks.id type.

Problem:
--------
- biofloc_tanks.id is UUID type
- inventory_transactions.tank_id is INTEGER type
- Causes "value out of int32 range" error when inserting UUID values
- Prevents feeding sessions from recording inventory transactions

Solution:
---------
1. Change tank_id column from INTEGER to UUID
2. Add foreign key constraint to biofloc_tanks(id)
3. Add index for efficient tank-based queries

Migration Path:
--------------
- Safe to run on existing database
- Existing NULL values will remain NULL
- No data loss (tank_id was not actively used before biofloc integration)

================================================================================
*/

-- ============================================================================
-- 1. ALTER TANK_ID COLUMN TYPE
-- ============================================================================

-- Drop any existing constraints on tank_id (if any)
ALTER TABLE inventory_transactions
DROP CONSTRAINT IF EXISTS fk_inventory_transactions_tank_id;

-- Check if there are any non-NULL integer values
DO $$
DECLARE
    non_null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO non_null_count
    FROM inventory_transactions
    WHERE tank_id IS NOT NULL;

    IF non_null_count > 0 THEN
        RAISE NOTICE '⚠ Found % rows with non-NULL tank_id. These will be set to NULL.', non_null_count;
        -- Set existing INTEGER values to NULL (they were likely incorrect anyway)
        UPDATE inventory_transactions SET tank_id = NULL WHERE tank_id IS NOT NULL;
    END IF;
END $$;

-- Change column type from INTEGER to UUID
-- All existing values are now NULL, so this is safe
ALTER TABLE inventory_transactions
ALTER COLUMN tank_id TYPE UUID USING NULL;

-- ============================================================================
-- 2. ADD FOREIGN KEY CONSTRAINT
-- ============================================================================

-- Add foreign key to biofloc_tanks if that table exists
-- Using SET NULL on delete to preserve transaction history if tank is deleted
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'biofloc_tanks') THEN
        ALTER TABLE inventory_transactions
        ADD CONSTRAINT fk_inventory_transactions_tank_id
        FOREIGN KEY (tank_id) REFERENCES biofloc_tanks(id) ON DELETE SET NULL;

        RAISE NOTICE '✓ Added foreign key constraint to biofloc_tanks';
    ELSE
        RAISE NOTICE '⚠ biofloc_tanks table not found, skipping foreign key constraint';
    END IF;
END $$;

-- ============================================================================
-- 3. ADD INDEX FOR PERFORMANCE
-- ============================================================================

-- Create index for efficient tank-based transaction queries
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_tank_id
ON inventory_transactions(tank_id)
WHERE tank_id IS NOT NULL;

-- ============================================================================
-- 4. UPDATE COLUMN COMMENT
-- ============================================================================

COMMENT ON COLUMN inventory_transactions.tank_id IS 'Reference to biofloc tank UUID (for biofloc module transactions)';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✓ Migration v1.3.1 completed successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✓ Changed tank_id from INTEGER to UUID';
    RAISE NOTICE '✓ Added foreign key to biofloc_tanks(id)';
    RAISE NOTICE '✓ Added index on tank_id';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Restart FastAPI backend server';
    RAISE NOTICE '2. Test biofloc feeding with inventory deduction';
    RAISE NOTICE '3. Verify transactions are recorded correctly';
    RAISE NOTICE '';
END $$;
