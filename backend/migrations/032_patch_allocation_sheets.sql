-- ================================================================================
-- Migration 032: Patch for Migration 031 (Add Missing Columns)
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-12
-- Description: Adds columns that were missing from original migration 031
--              - has_shortfall (computed column for tracking shortfalls)
--              - invoiced_at (timestamp for invoice generation)
-- ================================================================================

-- Add has_shortfall computed column (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'allocation_sheet_cells' 
        AND column_name = 'has_shortfall'
    ) THEN
        ALTER TABLE allocation_sheet_cells 
        ADD COLUMN has_shortfall BOOLEAN 
        GENERATED ALWAYS AS (COALESCE(sent_quantity, 0) < order_quantity) STORED;
        
        RAISE NOTICE 'Added has_shortfall column';
    ELSE
        RAISE NOTICE 'Column has_shortfall already exists, skipping';
    END IF;
END $$;

-- Add invoiced_at timestamp column (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'allocation_sheet_cells' 
        AND column_name = 'invoiced_at'
    ) THEN
        ALTER TABLE allocation_sheet_cells 
        ADD COLUMN invoiced_at TIMESTAMP WITH TIME ZONE;
        
        RAISE NOTICE 'Added invoiced_at column';
    ELSE
        RAISE NOTICE 'Column invoiced_at already exists, skipping';
    END IF;
END $$;

-- Add comments for new columns
COMMENT ON COLUMN allocation_sheet_cells.has_shortfall IS 'Auto-computed: TRUE if sent_quantity < order_quantity';
COMMENT ON COLUMN allocation_sheet_cells.invoiced_at IS 'Timestamp when invoice was generated for this cell';

-- ================================================================================
-- Verification
-- ================================================================================

-- Verify new columns exist:
SELECT 
    column_name, 
    data_type,
    is_generated,
    generation_expression
FROM information_schema.columns 
WHERE table_name = 'allocation_sheet_cells'
AND column_name IN ('has_shortfall', 'invoiced_at')
ORDER BY ordinal_position;

-- Expected output:
-- has_shortfall   | boolean   | ALWAYS | (COALESCE(sent_quantity, 0::numeric) < order_quantity)
-- invoiced_at     | timestamp | NEVER  | NULL
