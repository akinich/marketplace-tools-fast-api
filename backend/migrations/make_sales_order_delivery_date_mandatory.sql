-- ============================================================================
-- Migration: Make Sales Order delivery_date Mandatory
-- Description: Changes delivery_date column from nullable to NOT NULL
-- Date: 2025-12-12
-- ============================================================================

BEGIN;

-- Step 1: First, update any existing NULL delivery_date values to order_date
-- This ensures we don't violate the NOT NULL constraint
UPDATE sales_orders
SET delivery_date = order_date
WHERE delivery_date IS NULL;

-- Step 2: Alter the column to NOT NULL
ALTER TABLE sales_orders
ALTER COLUMN delivery_date SET NOT NULL;

-- Add a comment explaining the change
COMMENT ON COLUMN sales_orders.delivery_date IS 'Expected delivery date (REQUIRED - cannot be null)';

COMMIT;

-- ============================================================================
-- Verification query (optional - run separately after migration)
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'sales_orders'
--   AND column_name = 'delivery_date';
