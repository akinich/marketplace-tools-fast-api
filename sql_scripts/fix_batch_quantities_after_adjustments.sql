-- ============================================================================
-- Fix Batch Quantities After Stock Adjustments
-- ============================================================================
-- Purpose: Reconcile inventory_batches.remaining_qty with item_master.current_qty
--          This fixes the issue where old stock adjustments updated item quantities
--          but not batch quantities, causing inventory value discrepancies.
--
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- Step 1: Create a temporary table to track items needing fixes
CREATE TEMP TABLE items_to_fix AS
SELECT
    im.id,
    im.item_name,
    im.current_qty as item_qty,
    COALESCE(SUM(ib.remaining_qty), 0) as batch_total_qty,
    im.current_qty - COALESCE(SUM(ib.remaining_qty), 0) as difference
FROM item_master im
LEFT JOIN inventory_batches ib ON ib.item_master_id = im.id AND ib.is_active = TRUE
GROUP BY im.id, im.item_name, im.current_qty
HAVING im.current_qty != COALESCE(SUM(ib.remaining_qty), 0);

-- Display items that will be fixed
SELECT
    id,
    item_name,
    item_qty as "Current Item Qty",
    batch_total_qty as "Current Batch Total",
    difference as "Difference"
FROM items_to_fix
ORDER BY id;

-- Step 2: Fix items where current_qty = 0 (set all batches to 0)
UPDATE inventory_batches
SET
    remaining_qty = 0,
    updated_at = NOW()
WHERE item_master_id IN (
    SELECT id FROM items_to_fix WHERE item_qty = 0
)
AND is_active = TRUE
AND remaining_qty > 0;

-- Step 3: For items with current_qty > 0, proportionally adjust batches
-- This maintains the relative distribution across batches
WITH batch_adjustments AS (
    SELECT
        ib.id as batch_id,
        ib.item_master_id,
        ib.remaining_qty as old_qty,
        itf.item_qty,
        itf.batch_total_qty,
        -- Calculate proportional new quantity
        CASE
            WHEN itf.batch_total_qty > 0 THEN
                ROUND((ib.remaining_qty * itf.item_qty / itf.batch_total_qty)::numeric, 2)
            ELSE 0
        END as new_qty
    FROM inventory_batches ib
    JOIN items_to_fix itf ON itf.id = ib.item_master_id
    WHERE itf.item_qty > 0
      AND ib.is_active = TRUE
)
UPDATE inventory_batches
SET
    remaining_qty = ba.new_qty,
    updated_at = NOW()
FROM batch_adjustments ba
WHERE inventory_batches.id = ba.batch_id;

-- Step 4: Verify the fix - check if there are still mismatches
SELECT
    im.id,
    im.item_name,
    im.current_qty as item_qty,
    COALESCE(SUM(ib.remaining_qty), 0) as batch_total_qty,
    im.current_qty - COALESCE(SUM(ib.remaining_qty), 0) as remaining_difference
FROM item_master im
LEFT JOIN inventory_batches ib ON ib.item_master_id = im.id AND ib.is_active = TRUE
GROUP BY im.id, im.item_name, im.current_qty
HAVING ABS(im.current_qty - COALESCE(SUM(ib.remaining_qty), 0)) > 0.01
ORDER BY id;

-- Step 5: Show summary of changes
SELECT
    COUNT(*) as items_fixed,
    SUM(CASE WHEN item_qty = 0 THEN 1 ELSE 0 END) as items_zeroed,
    SUM(CASE WHEN item_qty > 0 THEN 1 ELSE 0 END) as items_adjusted
FROM items_to_fix;

-- Step 6: Show updated inventory value
SELECT
    COALESCE(SUM(remaining_qty * unit_cost), 0) as total_inventory_value,
    COUNT(DISTINCT item_master_id) as items_with_stock,
    COALESCE(SUM(remaining_qty), 0) as total_units
FROM inventory_batches
WHERE is_active = TRUE AND remaining_qty > 0;

COMMIT;

-- ============================================================================
-- Usage Instructions:
-- ============================================================================
-- 1. Review the output before committing
-- 2. If the results look correct, the transaction will commit automatically
-- 3. If you need to rollback, run: ROLLBACK;
--
-- This script:
-- - Sets all batches to 0 for items with current_qty = 0
-- - Proportionally adjusts batches for items with current_qty > 0
-- - Maintains the relative distribution of stock across batches
-- ============================================================================
