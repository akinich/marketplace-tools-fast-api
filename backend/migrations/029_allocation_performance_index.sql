-- ================================================================================
-- Migration 029: Add Performance Index for Inventory Allocation
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-12
-- Description: Adds composite index on inventory_movements for faster allocation lookups
-- ================================================================================

-- Index for finding allocations by order
-- Speeds up deallocate and confirm_allocation queries
CREATE INDEX IF NOT EXISTS idx_inventory_movements_allocation_lookup
ON inventory_movements(reference_type, reference_id, movement_type)
WHERE reference_type = 'sales_order';

COMMENT ON INDEX idx_inventory_movements_allocation_lookup IS 
'Performance index for allocation/deallocation lookups by order ID';

-- ================================================================================
-- Verification
-- ================================================================================
-- Check that index was created successfully:
-- SELECT indexname, indexdef FROM pg_indexes 
-- WHERE tablename = 'inventory_movements' AND indexname = 'idx_inventory_movements_allocation_lookup';
