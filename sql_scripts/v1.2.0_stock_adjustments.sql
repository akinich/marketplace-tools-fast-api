/*
================================================================================
Marketplace ERP Tools - Stock Adjustments Table Migration
================================================================================
Version: 1.2.0
Created: 2025-11-18
Database: Supabase PostgreSQL

Changelog:
----------
v1.2.0 (2025-11-18):
  - Added stock_adjustments table for tracking manual stock adjustments
  - Added index for performance
  - Added view for stock adjustment history with item names
  - Part of Inventory Sub-Module Phase B implementation

================================================================================
*/

-- Stock Adjustments Table
CREATE TABLE IF NOT EXISTS stock_adjustments (
    id BIGSERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL CHECK (adjustment_type IN ('increase', 'decrease', 'recount')),
    quantity_change NUMERIC(10,2) NOT NULL,
    previous_qty NUMERIC(10,2) NOT NULL,
    new_qty NUMERIC(10,2) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    notes TEXT,
    adjusted_by UUID NOT NULL REFERENCES user_profiles(id),
    adjustment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_item ON stock_adjustments(item_master_id, adjustment_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_date ON stock_adjustments(adjustment_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_adjustments_user ON stock_adjustments(adjusted_by, adjustment_date DESC);

-- View for stock adjustment history
CREATE OR REPLACE VIEW stock_adjustment_history AS
SELECT
    sa.id,
    sa.item_master_id,
    im.item_name,
    im.sku,
    im.unit,
    sa.adjustment_type,
    sa.quantity_change,
    sa.previous_qty,
    sa.new_qty,
    sa.reason,
    sa.notes,
    sa.adjusted_by,
    up.full_name as adjusted_by_name,
    sa.adjustment_date,
    sa.created_at
FROM stock_adjustments sa
JOIN item_master im ON im.id = sa.item_master_id
LEFT JOIN user_profiles up ON up.id = sa.adjusted_by
ORDER BY sa.adjustment_date DESC;

-- ============================================================================
-- END OF MIGRATION v1.1.0
-- ============================================================================
