-- ================================================================================
-- Migration 030: Add Expiry Priority for FIFO Allocation
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-12
-- Description: Adds index to optimize FIFO allocation with expiry date priority
--              Priority: Expiring (<2 days) → Repacked → Oldest → Newest
-- ================================================================================

-- Index for allocation FIFO query with expiry priority
-- This speeds up the complex ORDER BY in allocate_stock_to_order
CREATE INDEX IF NOT EXISTS idx_inventory_allocation_fifo_priority
ON inventory(item_id, location, status, expiry_date, entry_date)
WHERE status = 'available';

COMMENT ON INDEX idx_inventory_allocation_fifo_priority IS 
'Optimizes FIFO allocation query with expiry date priority. Used by allocate_stock_to_order function.';

-- Composite index for batch information joins
CREATE INDEX IF NOT EXISTS idx_inventory_batch_allocation_lookup
ON inventory(batch_id, item_id, location, status)
WHERE status IN ('available', 'allocated');

COMMENT ON INDEX idx_inventory_batch_allocation_lookup IS 
'Speeds up batch-based allocation queries and availability checks.';

-- ================================================================================
-- Verification Queries
-- ================================================================================

-- Check that indexes were created successfully:
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'inventory' 
--   AND indexname IN ('idx_inventory_allocation_fifo_priority', 'idx_inventory_batch_allocation_lookup');

-- Test allocation query performance (before/after):
-- EXPLAIN ANALYZE
-- SELECT i.id, i.batch_id, i.quantity, b.batch_number, b.is_repacked
-- FROM inventory i
-- JOIN batches b ON i.batch_id = b.id
-- WHERE i.item_id = 1
--   AND i.location = 'packed_warehouse'
--   AND i.status = 'available'
-- ORDER BY 
--     CASE 
--         WHEN i.expiry_date IS NOT NULL 
--              AND i.expiry_date <= CURRENT_DATE + INTERVAL '2 days' 
--         THEN 0
--         ELSE 1
--     END,
--     b.is_repacked DESC,
--     i.entry_date ASC;
