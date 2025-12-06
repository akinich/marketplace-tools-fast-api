-- ============================================================================
-- Migration 016: Create Purchase Orders Placeholder Table
-- ============================================================================
-- Description: Creates a basic purchase_orders table to support batch tracking
--              This is a placeholder until the full PO module is implemented
-- Created: 2025-12-06
-- ============================================================================

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    po_number VARCHAR(50) UNIQUE NOT NULL,
    farm_name VARCHAR(255),  -- Farm/Vendor name
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Audit
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_purchase_orders_po_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_farm_name ON purchase_orders(farm_name);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);

-- Comments
COMMENT ON TABLE purchase_orders IS 'Placeholder table for purchase orders - to be expanded when PO module is implemented';
COMMENT ON COLUMN purchase_orders.farm_name IS 'Name of the farm/vendor - temporary field until vendor master is linked';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Purchase Orders placeholder table created successfully!';
    RAISE NOTICE 'ℹ️  This is a basic table to support batch tracking. Full PO module will be implemented later.';
END $$;
