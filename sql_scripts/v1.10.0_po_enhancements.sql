-- ============================================================================
-- Farm Management System - Purchase Order Enhancements
-- Version: 1.10.0
-- Date: 2025-11-21
--
-- Description:
--   Adds enhanced PO functionality including:
--   - PO receiving with partial receiving support
--   - PO audit/history tracking
--   - Status workflow management
-- ============================================================================

-- ============================================================================
-- 1. PO RECEIVING TABLE
-- ============================================================================
-- Tracks actual received quantities and prices for each PO line item

CREATE TABLE IF NOT EXISTS po_receiving (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    po_item_id INTEGER NOT NULL REFERENCES purchase_order_items(id) ON DELETE CASCADE,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),

    -- Ordered vs Actual
    ordered_qty NUMERIC(10, 2) NOT NULL,
    received_qty NUMERIC(10, 2) NOT NULL DEFAULT 0,

    -- Price comparison
    po_unit_cost NUMERIC(10, 2) NOT NULL,
    actual_unit_cost NUMERIC(10, 2) NOT NULL,

    -- Line totals
    po_line_total NUMERIC(12, 2) GENERATED ALWAYS AS (ordered_qty * po_unit_cost) STORED,
    actual_line_total NUMERIC(12, 2) GENERATED ALWAYS AS (received_qty * actual_unit_cost) STORED,

    -- Receipt details
    batch_id INTEGER REFERENCES inventory_batches(id),  -- Created inventory batch
    batch_number VARCHAR(100),
    receipt_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date DATE,
    notes TEXT,

    -- Audit
    received_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for po_receiving
CREATE INDEX idx_po_receiving_po ON po_receiving(purchase_order_id);
CREATE INDEX idx_po_receiving_item ON po_receiving(item_master_id);
CREATE INDEX idx_po_receiving_date ON po_receiving(receipt_date DESC);

-- ============================================================================
-- 2. PO HISTORY/AUDIT TABLE
-- ============================================================================
-- Tracks all changes to purchase orders for audit trail

CREATE TABLE IF NOT EXISTS po_history (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,

    -- Change tracking
    action VARCHAR(50) NOT NULL,  -- created, status_changed, items_added, items_updated, items_deleted, received, duplicated, deleted
    previous_status VARCHAR(50),
    new_status VARCHAR(50),

    -- Change details
    change_details JSONB,  -- Stores detailed change information

    -- Audit
    changed_by UUID REFERENCES user_profiles(id),
    changed_by_name VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for po_history
CREATE INDEX idx_po_history_po ON po_history(purchase_order_id);
CREATE INDEX idx_po_history_action ON po_history(action);
CREATE INDEX idx_po_history_date ON po_history(changed_at DESC);

-- ============================================================================
-- 3. UPDATE PURCHASE_ORDERS STATUS OPTIONS
-- ============================================================================
-- Add comment to document valid statuses including partially_received

COMMENT ON COLUMN purchase_orders.status IS
'Valid statuses: pending, approved, ordered, partially_received, received, closed, cancelled';

-- ============================================================================
-- 4. TRIGGER FOR PO HISTORY AUTO-UPDATE TIMESTAMP
-- ============================================================================

CREATE OR REPLACE FUNCTION update_po_receiving_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_po_receiving_timestamp
    BEFORE UPDATE ON po_receiving
    FOR EACH ROW
    EXECUTE FUNCTION update_po_receiving_timestamp();

-- ============================================================================
-- 5. FUNCTION TO CALCULATE PO RECEIVING SUMMARY
-- ============================================================================
-- Returns summary of received items for a PO

CREATE OR REPLACE FUNCTION get_po_receiving_summary(p_po_id INTEGER)
RETURNS TABLE (
    total_items INTEGER,
    fully_received INTEGER,
    partially_received INTEGER,
    not_received INTEGER,
    total_ordered_value NUMERIC,
    total_received_value NUMERIC,
    variance NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH item_status AS (
        SELECT
            poi.id,
            poi.ordered_qty,
            COALESCE(SUM(pr.received_qty), 0) as total_received,
            poi.ordered_qty * poi.unit_cost as ordered_value,
            COALESCE(SUM(pr.received_qty * pr.actual_unit_cost), 0) as received_value
        FROM purchase_order_items poi
        LEFT JOIN po_receiving pr ON pr.po_item_id = poi.id
        WHERE poi.purchase_order_id = p_po_id
        GROUP BY poi.id, poi.ordered_qty, poi.unit_cost
    )
    SELECT
        COUNT(*)::INTEGER as total_items,
        COUNT(CASE WHEN total_received >= ordered_qty THEN 1 END)::INTEGER as fully_received,
        COUNT(CASE WHEN total_received > 0 AND total_received < ordered_qty THEN 1 END)::INTEGER as partially_received,
        COUNT(CASE WHEN total_received = 0 THEN 1 END)::INTEGER as not_received,
        SUM(ordered_value)::NUMERIC as total_ordered_value,
        SUM(received_value)::NUMERIC as total_received_value,
        (SUM(received_value) - SUM(ordered_value))::NUMERIC as variance
    FROM item_status;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. GRANT PERMISSIONS
-- ============================================================================

GRANT ALL ON po_receiving TO farm2_app;
GRANT ALL ON po_history TO farm2_app;
GRANT USAGE, SELECT ON SEQUENCE po_receiving_id_seq TO farm2_app;
GRANT USAGE, SELECT ON SEQUENCE po_history_id_seq TO farm2_app;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
