-- ================================================================================
-- Migration 018: Purchase Order Management Module - Database Tables
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-06
-- Description: Creates tables for purchase order management, vendor pricing,
--              and PO status tracking with complete audit trail.
-- ================================================================================

-- ============================================================================
-- TABLE: purchase_orders
-- ============================================================================
-- Main table for purchase orders from vendors/farms

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS po_status_history CASCADE;
DROP TABLE IF EXISTS vendor_item_price_history CASCADE;
DROP TABLE IF EXISTS purchase_order_items CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,  -- PO-001, PO-002, etc.
    
    -- Vendor Reference
    vendor_id INTEGER NOT NULL REFERENCES zoho_vendors(id) ON DELETE RESTRICT,
    
    -- Dates (CRITICAL: dispatch_date drives pricing!)
    dispatch_date DATE NOT NULL,  -- Expected dispatch/billing date
    delivery_date DATE NOT NULL,  -- Expected delivery date
    
    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Status values: draft, sent_to_farm, grn_generated, completed, exported_to_zoho, closed
    
    -- Financial
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    
    -- Notes
    notes TEXT,
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    exported_at TIMESTAMP WITH TIME ZONE,  -- When exported to Zoho
    
    -- Constraints
    CONSTRAINT check_delivery_after_dispatch CHECK (delivery_date >= dispatch_date),
    CONSTRAINT check_total_amount_positive CHECK (total_amount >= 0),
    CONSTRAINT check_status_valid CHECK (status IN (
        'draft', 'sent_to_farm', 'grn_generated', 'completed', 'exported_to_zoho', 'closed'
    ))
);

-- Indexes for purchase_orders
CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_dispatch_date ON purchase_orders(dispatch_date);
CREATE INDEX IF NOT EXISTS idx_po_delivery_date ON purchase_orders(delivery_date);
CREATE INDEX IF NOT EXISTS idx_po_created_at ON purchase_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number);

COMMENT ON TABLE purchase_orders IS 'Purchase orders from vendors/farms with status tracking';
COMMENT ON COLUMN purchase_orders.dispatch_date IS 'Expected dispatch/billing date - DRIVES PRICING';
COMMENT ON COLUMN purchase_orders.delivery_date IS 'Expected delivery date for planning/logistics';
COMMENT ON COLUMN purchase_orders.status IS 'Workflow status: draft → sent → grn_generated → completed → exported → closed';
COMMENT ON COLUMN purchase_orders.exported_at IS 'Timestamp when exported to Zoho Books (locks PO from edits)';


-- ============================================================================
-- TABLE: purchase_order_items
-- ============================================================================
-- Line items for each purchase order

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id SERIAL PRIMARY KEY,
    po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Item Reference
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE RESTRICT,
    
    -- Quantity & Pricing
    quantity DECIMAL(10, 3) NOT NULL,  -- Support decimal quantities (e.g., 10.5 kg)
    unit_price DECIMAL(10, 2) NOT NULL,
    price_source VARCHAR(20) NOT NULL,  -- 'vendor', 'zoho', 'manual'
    total_price DECIMAL(10, 2) NOT NULL,
    
    -- Notes
    notes TEXT,
    
    -- GRN Integration
    added_from_grn BOOLEAN DEFAULT FALSE,  -- TRUE if item was added from GRN (not on original PO)
    
    -- Constraints
    CONSTRAINT check_quantity_positive CHECK (quantity > 0),
    CONSTRAINT check_unit_price_positive CHECK (unit_price > 0),
    CONSTRAINT check_total_price_positive CHECK (total_price > 0),
    CONSTRAINT check_price_source_valid CHECK (price_source IN ('vendor', 'zoho', 'manual'))
);

-- Indexes for purchase_order_items
CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(po_id);
CREATE INDEX IF NOT EXISTS idx_po_items_item ON purchase_order_items(item_id);
CREATE INDEX IF NOT EXISTS idx_po_items_added_from_grn ON purchase_order_items(added_from_grn);

COMMENT ON TABLE purchase_order_items IS 'Line items for purchase orders with pricing source tracking';
COMMENT ON COLUMN purchase_order_items.price_source IS 'Source of price: vendor (tier 1), zoho (tier 2), manual (tier 3)';
COMMENT ON COLUMN purchase_order_items.added_from_grn IS 'TRUE if item was added from GRN (farm sent extra items)';


-- ============================================================================
-- TABLE: vendor_item_price_history
-- ============================================================================
-- Time-based vendor-specific pricing (admin-managed)

CREATE TABLE IF NOT EXISTS vendor_item_price_history (
    id SERIAL PRIMARY KEY,
    
    -- Vendor-Item Combination
    vendor_id INTEGER NOT NULL REFERENCES zoho_vendors(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE CASCADE,
    
    -- Pricing
    price DECIMAL(10, 2) NOT NULL,
    
    -- Effective Date Range
    effective_from DATE NOT NULL,
    effective_to DATE,  -- NULL means indefinite (until next price change)
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- Admin only
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    
    -- Constraints
    CONSTRAINT check_price_positive CHECK (price > 0),
    CONSTRAINT check_valid_date_range CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- Indexes for vendor_item_price_history
CREATE INDEX IF NOT EXISTS idx_vendor_price_vendor ON vendor_item_price_history(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_price_item ON vendor_item_price_history(item_id);
CREATE INDEX IF NOT EXISTS idx_vendor_price_dates ON vendor_item_price_history(effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_vendor_price_lookup ON vendor_item_price_history(vendor_id, item_id, effective_from, effective_to);

COMMENT ON TABLE vendor_item_price_history IS 'Time-based vendor-specific pricing with scheduled price changes';
COMMENT ON COLUMN vendor_item_price_history.effective_from IS 'Price becomes active from this date';
COMMENT ON COLUMN vendor_item_price_history.effective_to IS 'Price valid until this date (NULL = indefinite)';
COMMENT ON COLUMN vendor_item_price_history.created_by IS 'Admin user who set this price';


-- ============================================================================
-- TABLE: po_status_history
-- ============================================================================
-- Complete audit trail of PO status changes

CREATE TABLE IF NOT EXISTS po_status_history (
    id SERIAL PRIMARY KEY,
    po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Status Change
    from_status VARCHAR(50),  -- NULL for initial creation
    to_status VARCHAR(50) NOT NULL,
    
    -- Audit Trail
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Indexes for po_status_history
CREATE INDEX IF NOT EXISTS idx_po_history_po ON po_status_history(po_id);
CREATE INDEX IF NOT EXISTS idx_po_history_changed_at ON po_status_history(changed_at DESC);

COMMENT ON TABLE po_status_history IS 'Complete audit trail of all PO status changes';
COMMENT ON COLUMN po_status_history.from_status IS 'Previous status (NULL for initial creation)';
COMMENT ON COLUMN po_status_history.to_status IS 'New status after change';


-- ============================================================================
-- FUNCTION: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_po_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for purchase_orders
CREATE TRIGGER trigger_update_po_updated_at
    BEFORE UPDATE ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_po_updated_at();


-- ============================================================================
-- MODULE REGISTRATION
-- ============================================================================

-- Register Purchase Order Management module
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'purchase_orders',
    'Purchase Orders',
    'Create and manage purchase orders with vendor-specific pricing and Zoho export',
    'ShoppingCart',
    NULL,  -- Top-level module (or set parent if needed)
    true,
    10
)
ON CONFLICT (module_key) DO UPDATE SET
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    display_order = EXCLUDED.display_order;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('purchase_orders', 'purchase_order_items', 'vendor_item_price_history', 'po_status_history')
ORDER BY table_name;

-- Verify indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('purchase_orders', 'purchase_order_items', 'vendor_item_price_history', 'po_status_history')
ORDER BY tablename, indexname;

-- Verify module registered
SELECT module_key, module_name, description, icon, is_active
FROM modules
WHERE module_key = 'purchase_orders';


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 018: Purchase Order Management tables created successfully';
    RAISE NOTICE '   - 4 tables created: purchase_orders, purchase_order_items, vendor_item_price_history, po_status_history';
    RAISE NOTICE '   - 15 indexes created for performance';
    RAISE NOTICE '   - Module registered: Purchase Orders';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready for PO Management implementation!';
END $$;
