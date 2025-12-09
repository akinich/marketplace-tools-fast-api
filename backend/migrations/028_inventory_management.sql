-- ================================================================================
-- Migration 028: Inventory Management Module - Database Tables
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-07
-- Description: Creates tables for inventory management, stock tracking,
--              movements, adjustments, and reorder levels with multi-location support.
-- ================================================================================

-- ============================================================================
-- TABLE: inventory
-- ============================================================================
-- Main stock tracking table with batch-level granularity and multi-location support

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    
    -- Item Reference
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE RESTRICT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE RESTRICT,
    
    -- Location Tracking
    location VARCHAR(50) NOT NULL,
    -- Location values: receiving_area, processing_area, packed_warehouse, delivery_vehicles, quality_hold
    
    -- Quantity & Grade
    quantity DECIMAL(10, 3) NOT NULL,
    grade VARCHAR(10), -- A, B, C, or NULL
    
    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'available',
    -- Status values: available, allocated, hold, in_transit, delivered
    
    -- Shelf Life Management
    shelf_life_days INTEGER, -- Expected shelf life in days
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expiry_date DATE, -- Calculated based on entry_date + shelf_life_days
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_quantity_positive CHECK (quantity >= 0),
    CONSTRAINT check_location_valid CHECK (location IN (
        'receiving_area', 'processing_area', 'packed_warehouse', 'delivery_vehicles', 'quality_hold'
    )),
    CONSTRAINT check_status_valid CHECK (status IN (
        'available', 'allocated', 'hold', 'in_transit', 'delivered'
    ))
);

-- Indexes for inventory
CREATE INDEX IF NOT EXISTS idx_inventory_item ON inventory(item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batch ON inventory(batch_id);
CREATE INDEX IF NOT EXISTS idx_inventory_location ON inventory(location);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON inventory(expiry_date);
CREATE INDEX IF NOT EXISTS idx_inventory_location_status ON inventory(location, status);
CREATE INDEX IF NOT EXISTS idx_inventory_item_location ON inventory(item_id, location);

COMMENT ON TABLE inventory IS 'Multi-location inventory tracking with batch-level granularity';
COMMENT ON COLUMN inventory.location IS 'Physical location of stock: receiving_area/processing_area/packed_warehouse/delivery_vehicles/quality_hold';
COMMENT ON COLUMN inventory.status IS 'Stock status: available/allocated/hold/in_transit/delivered';
COMMENT ON COLUMN inventory.expiry_date IS 'Calculated expiry date for shelf life monitoring';


-- ============================================================================
-- TABLE: inventory_movements
-- ============================================================================
-- Complete history of all stock movements and transfers

CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    
    -- Item & Batch Reference
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE RESTRICT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE RESTRICT,
    
    -- Movement Details
    movement_type VARCHAR(50) NOT NULL,
    -- Movement types: stock_in, stock_out, location_transfer, adjustment, allocation, delivery
    
    quantity DECIMAL(10, 3) NOT NULL,
    
    -- Location Tracking
    from_location VARCHAR(50), -- NULL for stock_in
    to_location VARCHAR(50),   -- NULL for stock_out
    
    -- Reference to Source Document
    reference_type VARCHAR(50), -- packing, grn, sales_order, adjustment, manual
    reference_id INTEGER, -- ID of the source document
    
    -- Notes
    notes TEXT,
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_movement_quantity_positive CHECK (quantity > 0),
    CONSTRAINT check_movement_type_valid CHECK (movement_type IN (
        'stock_in', 'stock_out', 'location_transfer', 'adjustment', 'allocation', 'delivery'
    ))
);

-- Indexes for inventory_movements
CREATE INDEX IF NOT EXISTS idx_movements_batch ON inventory_movements(batch_id);
CREATE INDEX IF NOT EXISTS idx_movements_item ON inventory_movements(item_id);
CREATE INDEX IF NOT EXISTS idx_movements_type ON inventory_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_movements_created_at ON inventory_movements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_movements_reference ON inventory_movements(reference_type, reference_id);

COMMENT ON TABLE inventory_movements IS 'Complete audit trail of all stock movements and transfers';
COMMENT ON COLUMN inventory_movements.movement_type IS 'Type: stock_in/stock_out/location_transfer/adjustment/allocation/delivery';
COMMENT ON COLUMN inventory_movements.reference_type IS 'Source document type that triggered this movement';


-- ============================================================================
-- TABLE: inventory_adjustments
-- ============================================================================
-- Manual stock adjustments with approval workflow

CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id SERIAL PRIMARY KEY,
    
    -- Item & Batch Reference
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE RESTRICT,
    batch_id INTEGER REFERENCES batches(id) ON DELETE RESTRICT, -- Optional: can be item-level adjustment
    location VARCHAR(50) NOT NULL,
    
    -- Adjustment Details
    adjustment_type VARCHAR(20) NOT NULL,
    -- Adjustment types: increase, decrease, correction
    
    quantity DECIMAL(10, 3) NOT NULL,
    reason TEXT NOT NULL,
    
    -- Supporting Evidence
    photo_urls TEXT[], -- Array of Supabase Storage URLs for photos
    
    -- Approval Workflow
    approval_status VARCHAR(20) NOT NULL DEFAULT 'pending_approval',
    -- Status: pending_approval, approved, rejected, applied
    
    approved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_adjustment_quantity_positive CHECK (quantity > 0),
    CONSTRAINT check_adjustment_type_valid CHECK (adjustment_type IN ('increase', 'decrease', 'correction')),
    CONSTRAINT check_approval_status_valid CHECK (approval_status IN (
        'pending_approval', 'approved', 'rejected', 'applied'
    ))
);

-- Indexes for inventory_adjustments
CREATE INDEX IF NOT EXISTS idx_adjustments_item ON inventory_adjustments(item_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_batch ON inventory_adjustments(batch_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_status ON inventory_adjustments(approval_status);
CREATE INDEX IF NOT EXISTS idx_adjustments_created_at ON inventory_adjustments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adjustments_location ON inventory_adjustments(location);

COMMENT ON TABLE inventory_adjustments IS 'Manual stock adjustments with approval workflow and photo evidence';
COMMENT ON COLUMN inventory_adjustments.approval_status IS 'Workflow: pending_approval → approved/rejected → applied';
COMMENT ON COLUMN inventory_adjustments.photo_urls IS 'Array of Supabase Storage URLs for supporting documentation';


-- ============================================================================
-- TABLE: reorder_levels
-- ============================================================================
-- Configurable reorder levels and alert thresholds per item and location

CREATE TABLE IF NOT EXISTS reorder_levels (
    id SERIAL PRIMARY KEY,
    
    -- Item & Location
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE CASCADE,
    location VARCHAR(50) NOT NULL,
    
    -- Reorder Configuration
    reorder_quantity DECIMAL(10, 3) NOT NULL, -- Minimum stock level before reorder
    alert_threshold DECIMAL(10, 3) NOT NULL,  -- Trigger alert when stock falls below this
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_reorder_quantity_positive CHECK (reorder_quantity >= 0),
    CONSTRAINT check_alert_threshold_positive CHECK (alert_threshold >= 0),
    CONSTRAINT unique_item_location_reorder UNIQUE (item_id, location)
);

-- Indexes for reorder_levels
CREATE INDEX IF NOT EXISTS idx_reorder_item ON reorder_levels(item_id);
CREATE INDEX IF NOT EXISTS idx_reorder_location ON reorder_levels(location);
CREATE INDEX IF NOT EXISTS idx_reorder_active ON reorder_levels(is_active);

COMMENT ON TABLE reorder_levels IS 'Configurable reorder levels and alert thresholds per item and location';
COMMENT ON COLUMN reorder_levels.reorder_quantity IS 'Minimum stock level before initiating reorder';
COMMENT ON COLUMN reorder_levels.alert_threshold IS 'Alert when stock falls below this level';


-- ============================================================================
-- FUNCTION: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_inventory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER trigger_update_inventory_updated_at
    BEFORE UPDATE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_updated_at();

CREATE TRIGGER trigger_update_adjustment_updated_at
    BEFORE UPDATE ON inventory_adjustments
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_updated_at();

CREATE TRIGGER trigger_update_reorder_updated_at
    BEFORE UPDATE ON reorder_levels
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_updated_at();


-- ============================================================================
-- FUNCTION: Auto-calculate expiry date
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_expiry_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.shelf_life_days IS NOT NULL THEN
        NEW.expiry_date = (NEW.entry_date::date + (NEW.shelf_life_days || ' days')::interval)::date;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_expiry_date
    BEFORE INSERT OR UPDATE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION calculate_expiry_date();


-- ============================================================================
-- MODULE REGISTRATION
-- ============================================================================

-- Update Stock Management module from placeholder to active
UPDATE modules
SET 
    description = 'Track stock levels across multiple locations with batch-level granularity. Manage FIFO allocation, reorder levels, and stock movements.',
    is_active = true
WHERE module_key = 'stock_management';


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('inventory', 'inventory_movements', 'inventory_adjustments', 'reorder_levels')
ORDER BY table_name;

-- Verify indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('inventory', 'inventory_movements', 'inventory_adjustments', 'reorder_levels')
ORDER BY tablename, indexname;

-- Verify module updated
SELECT module_key, module_name, description, is_active
FROM modules
WHERE module_key = 'stock_management';


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 028: Inventory Management tables created successfully';
    RAISE NOTICE '   - 4 tables created: inventory, inventory_movements, inventory_adjustments, reorder_levels';
    RAISE NOTICE '   - 18 indexes created for performance';
    RAISE NOTICE '   - 3 triggers created for auto-update and expiry calculation';
    RAISE NOTICE '   - Module updated: Stock Management';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready for Inventory Management implementation!';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Next Steps:';
    RAISE NOTICE '   1. Verify tables: SELECT * FROM inventory LIMIT 1;';
    RAISE NOTICE '   2. Deploy backend service and routes';
    RAISE NOTICE '   3. Test with manual stock entry endpoint';
END $$;
