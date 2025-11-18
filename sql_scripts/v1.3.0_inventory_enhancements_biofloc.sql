/*
================================================================================
Farm Management System - Inventory Enhancements for Biofloc Integration
================================================================================
Version: 1.3.0
Created: 2025-11-18
Database: Supabase PostgreSQL

Purpose:
--------
Enhanced inventory module to support better cross-module integration,
particularly for biofloc module. Adds batch operations, bulk fetch,
and stock reservation capabilities.

Changes:
--------
1. Add batch_id and session_number to inventory_transactions
2. Create inventory_reservations table for stock reservation system
3. Create item_module_mapping table for module-specific item tracking

Migration Path:
--------------
- Safe to run on existing database (uses IF NOT EXISTS)
- Backward compatible with existing inventory operations
- No data loss or modification to existing records

================================================================================
*/

-- ============================================================================
-- 1. ENHANCE INVENTORY_TRANSACTIONS TABLE
-- ============================================================================

-- Note: batch_id already exists in inventory_transactions (references inventory_batches)
-- We add module_batch_id for biofloc/other module batch tracking
ALTER TABLE inventory_transactions
ADD COLUMN IF NOT EXISTS module_batch_id UUID;

-- Add session_number for grouping related transactions (e.g., feeding session)
ALTER TABLE inventory_transactions
ADD COLUMN IF NOT EXISTS session_number INTEGER;

-- Add index for efficient module batch queries
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_module_batch
ON inventory_transactions(module_batch_id);

-- Add index for session queries
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_session
ON inventory_transactions(session_number);

-- Add comment for documentation
COMMENT ON COLUMN inventory_transactions.module_batch_id IS 'Reference to biofloc batch or other module batch identifier (UUID)';
COMMENT ON COLUMN inventory_transactions.session_number IS 'Groups related transactions (e.g., daily feeding session #1, #2)';


-- ============================================================================
-- 2. CREATE INVENTORY_RESERVATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    quantity DECIMAL(10,2) NOT NULL CHECK (quantity > 0),
    module_reference VARCHAR(50) NOT NULL,  -- 'biofloc', 'hatchery', etc.
    reference_id UUID,  -- Tank ID, batch ID, or other module-specific reference
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'expired')),
    reserved_until TIMESTAMP WITH TIME ZONE NOT NULL,
    notes TEXT,
    created_by UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure reservations don't exceed reasonable timeframes
    CONSTRAINT reasonable_duration CHECK (reserved_until > created_at AND reserved_until < created_at + INTERVAL '30 days')
);

-- Indexes for efficient reservation queries
CREATE INDEX IF NOT EXISTS idx_reservations_item_status
ON inventory_reservations(item_id, status);

CREATE INDEX IF NOT EXISTS idx_reservations_module
ON inventory_reservations(module_reference, status);

CREATE INDEX IF NOT EXISTS idx_reservations_expiry
ON inventory_reservations(reserved_until, status)
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_reservations_reference
ON inventory_reservations(reference_id);

-- Add comments
COMMENT ON TABLE inventory_reservations IS 'Soft reservations for planned inventory usage across modules';
COMMENT ON COLUMN inventory_reservations.module_reference IS 'Module that created this reservation (biofloc, hatchery, growout, nursery, general)';
COMMENT ON COLUMN inventory_reservations.reference_id IS 'Module-specific reference (tank_id, batch_id, etc.)';
COMMENT ON COLUMN inventory_reservations.status IS 'pending: reserved, confirmed: converted to actual use, cancelled: manually cancelled, expired: auto-expired';


-- ============================================================================
-- 3. CREATE ITEM_MODULE_MAPPING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS item_module_mapping (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    module_name VARCHAR(50) NOT NULL,  -- 'biofloc', 'hatchery', 'growout', 'nursery', 'general'
    custom_settings JSONB DEFAULT '{}',  -- Module-specific configuration
    is_primary BOOLEAN DEFAULT FALSE,  -- Primary module for this item
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique mapping per item-module pair
    UNIQUE(item_id, module_name)
);

-- Indexes for module filtering
CREATE INDEX IF NOT EXISTS idx_item_module_mapping_module
ON item_module_mapping(module_name);

CREATE INDEX IF NOT EXISTS idx_item_module_mapping_item
ON item_module_mapping(item_id);

CREATE INDEX IF NOT EXISTS idx_item_module_mapping_primary
ON item_module_mapping(module_name, is_primary)
WHERE is_primary = TRUE;

-- Add comments
COMMENT ON TABLE item_module_mapping IS 'Maps inventory items to modules with custom settings';
COMMENT ON COLUMN item_module_mapping.module_name IS 'Module that uses this item (biofloc, hatchery, growout, nursery, general)';
COMMENT ON COLUMN item_module_mapping.custom_settings IS 'Module-specific configuration (e.g., {"feeding_schedule": "3x daily", "default_qty": 5.0})';
COMMENT ON COLUMN item_module_mapping.is_primary IS 'Indicates if this is the primary module for this item';


-- ============================================================================
-- 4. CREATE VIEW FOR AVAILABLE QUANTITIES (current - reserved)
-- ============================================================================

CREATE OR REPLACE VIEW inventory_available_stock AS
SELECT
    im.id,
    im.item_name,
    im.sku,
    im.category,
    im.unit,
    im.current_qty,
    COALESCE(SUM(
        CASE
            WHEN ir.status = 'pending' AND ir.reserved_until > NOW()
            THEN ir.quantity
            ELSE 0
        END
    ), 0) as reserved_qty,
    im.current_qty - COALESCE(SUM(
        CASE
            WHEN ir.status = 'pending' AND ir.reserved_until > NOW()
            THEN ir.quantity
            ELSE 0
        END
    ), 0) as available_qty,
    im.reorder_threshold,
    im.is_active
FROM item_master im
LEFT JOIN inventory_reservations ir ON im.id = ir.item_id
GROUP BY im.id, im.item_name, im.sku, im.category, im.unit, im.current_qty, im.reorder_threshold, im.is_active;

COMMENT ON VIEW inventory_available_stock IS 'Shows current stock minus pending reservations for each item';


-- ============================================================================
-- 5. CREATE FUNCTION TO AUTO-EXPIRE RESERVATIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION expire_old_reservations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- Log expired reservations before updating
    INSERT INTO activity_logs (
        user_id,
        user_email,
        user_role,
        action_type,
        module_key,
        description,
        metadata
    )
    SELECT
        created_by,
        'system',
        'System',
        'Reservation Expired',
        'inventory',
        'Auto-expired reservation: ' || id::TEXT,
        jsonb_build_object(
            'reservation_id', id,
            'item_id', item_id,
            'quantity', quantity,
            'module_reference', module_reference,
            'reserved_until', reserved_until
        )
    FROM inventory_reservations
    WHERE status = 'pending' AND reserved_until < NOW();

    -- Update expired reservations
    UPDATE inventory_reservations
    SET
        status = 'expired',
        updated_at = NOW()
    WHERE status = 'pending' AND reserved_until < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;

    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_old_reservations() IS 'Auto-expires pending reservations past their reserved_until time. Returns count of expired reservations.';


-- ============================================================================
-- 6. GRANT PERMISSIONS (if needed for RLS policies)
-- ============================================================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_reservations TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON item_module_mapping TO authenticated;
GRANT SELECT ON inventory_available_stock TO authenticated;
GRANT EXECUTE ON FUNCTION expire_old_reservations() TO authenticated;


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verification query
DO $$
BEGIN
    RAISE NOTICE '✓ Migration v1.3.0 completed successfully';
    RAISE NOTICE '✓ Added module_batch_id and session_number to inventory_transactions';
    RAISE NOTICE '✓ Created inventory_reservations table';
    RAISE NOTICE '✓ Created item_module_mapping table';
    RAISE NOTICE '✓ Created inventory_available_stock view';
    RAISE NOTICE '✓ Created expire_old_reservations() function';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Run migration: psql -f v1.3.0_inventory_enhancements_biofloc.sql';
    RAISE NOTICE '2. Install APScheduler: pip install APScheduler==3.10.4';
    RAISE NOTICE '3. Restart FastAPI server to activate background scheduler';
    RAISE NOTICE '4. Test endpoints:';
    RAISE NOTICE '   - POST /api/v1/inventory/stock/use-batch (batch deduction)';
    RAISE NOTICE '   - POST /api/v1/inventory/items/bulk-fetch (bulk fetch)';
    RAISE NOTICE '   - POST /api/v1/inventory/stock/reserve (create reservation)';
    RAISE NOTICE '   - GET /health (verify scheduler is running)';
END $$;
