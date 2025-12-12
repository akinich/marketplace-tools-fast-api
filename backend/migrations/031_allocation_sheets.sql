-- ================================================================================
-- Migration 031: Allocation Sheets System
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-12
-- Description: Creates allocation sheet system for spreadsheet-style order allocation
--              organized by delivery date with Items × Customers matrix
-- ================================================================================

-- Set timezone to IST (Indian Standard Time = Asia/Kolkata)
SET timezone = 'Asia/Kolkata';

-- Table 1: Allocation Sheets (one per delivery date)
CREATE TABLE allocation_sheets (
    id SERIAL PRIMARY KEY,
    delivery_date DATE NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_allocation_sheets_date ON allocation_sheets(delivery_date);
CREATE INDEX idx_allocation_sheets_status ON allocation_sheets(status) WHERE status = 'active';

COMMENT ON TABLE allocation_sheets IS 'Master table for allocation sheets, one record per delivery date';
COMMENT ON COLUMN allocation_sheets.delivery_date IS 'Delivery date for this allocation sheet (unique)';
COMMENT ON COLUMN allocation_sheets.status IS 'active = currently being edited, archived = historical';

-- Table 2: Allocation Sheet Cells (each (item, customer) combination)
CREATE TABLE allocation_sheet_cells (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL REFERENCES allocation_sheets(id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES zoho_items(id),
    customer_id VARCHAR(100) NOT NULL, -- Zoho customer ID
    so_id INT NOT NULL REFERENCES sales_orders(id),
    
    -- Data columns
    order_quantity DECIMAL(10,3) NOT NULL CHECK (order_quantity >= 0),
    sent_quantity DECIMAL(10,3) CHECK (sent_quantity >= 0),
    
    -- Tracking flags
    order_modified BOOLEAN DEFAULT FALSE,
    has_shortfall BOOLEAN GENERATED ALWAYS AS (COALESCE(sent_quantity, 0) < order_quantity) STORED,
    invoice_status VARCHAR(50) DEFAULT 'pending' CHECK (invoice_status IN ('pending', 'ready', 'invoiced')),
    invoice_id INT, -- Reference to invoice when generated
    invoiced_at TIMESTAMP WITH TIME ZONE,
    
    -- Batch allocation tracking (JSON)
    allocated_batches JSONB,
    
    -- Optimistic locking
    version INT DEFAULT 1,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Each (sheet, item, customer) combination must be unique
    UNIQUE(sheet_id, item_id, customer_id)
);

-- Indexes for performance
CREATE INDEX idx_allocation_cells_sheet ON allocation_sheet_cells(sheet_id);
CREATE INDEX idx_allocation_cells_so ON allocation_sheet_cells(so_id);
CREATE INDEX idx_allocation_cells_invoice_status ON allocation_sheet_cells(invoice_status) WHERE invoice_status IN ('pending', 'ready');
CREATE INDEX idx_allocation_cells_customer ON allocation_sheet_cells(sheet_id, customer_id);
CREATE INDEX idx_allocation_cells_item ON allocation_sheet_cells(sheet_id, item_id);

COMMENT ON TABLE allocation_sheet_cells IS 'Each row represents one (item, customer) cell in allocation grid';
COMMENT ON COLUMN allocation_sheet_cells.order_quantity IS 'Quantity from SO, user-editable, syncs back to SO';
COMMENT ON COLUMN allocation_sheet_cells.sent_quantity IS 'Auto-filled via FIFO, user-editable, used for invoicing';
COMMENT ON COLUMN allocation_sheet_cells.allocated_batches IS 'JSON array of {batch_id, quantity} allocations';
COMMENT ON COLUMN allocation_sheet_cells.version IS 'For optimistic locking in multi-user editing';

-- Table 3: Audit Log for Cell Changes
CREATE TABLE allocation_sheet_audit (
    id SERIAL PRIMARY KEY,
    cell_id INT NOT NULL REFERENCES allocation_sheet_cells(id) ON DELETE CASCADE,
    field_changed VARCHAR(50) NOT NULL,
    old_value DECIMAL(10,3),
    new_value DECIMAL(10,3),
    changed_by UUID NOT NULL REFERENCES auth.users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_allocation_audit_cell ON allocation_sheet_audit(cell_id);
CREATE INDEX idx_allocation_audit_date ON allocation_sheet_audit(changed_at);

COMMENT ON TABLE allocation_sheet_audit IS 'Audit trail for all changes to allocation cells';

-- Trigger: Auto-update updated_at on allocation_sheets
CREATE OR REPLACE FUNCTION update_allocation_sheet_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_allocation_sheets_updated_at
    BEFORE UPDATE ON allocation_sheets
    FOR EACH ROW
    EXECUTE FUNCTION update_allocation_sheet_updated_at();

-- Trigger: Auto-update updated_at on allocation_sheet_cells
CREATE TRIGGER trg_allocation_cells_updated_at
    BEFORE UPDATE ON allocation_sheet_cells
    FOR EACH ROW
    EXECUTE FUNCTION update_allocation_sheet_updated_at();

-- Trigger: Increment version on cell update (optimistic locking)
CREATE OR REPLACE FUNCTION increment_cell_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_allocation_cells_version
    BEFORE UPDATE ON allocation_sheet_cells
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION increment_cell_version();

-- Trigger: Log changes to audit table
CREATE OR REPLACE FUNCTION log_cell_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log order_quantity changes
    IF OLD.order_quantity IS DISTINCT FROM NEW.order_quantity THEN
        INSERT INTO allocation_sheet_audit (cell_id, field_changed, old_value, new_value, changed_by)
        VALUES (NEW.id, 'order_quantity', OLD.order_quantity, NEW.order_quantity, NEW.created_by);
    END IF;
    
    -- Log sent_quantity changes
    IF OLD.sent_quantity IS DISTINCT FROM NEW.sent_quantity THEN
        INSERT INTO allocation_sheet_audit (cell_id, field_changed, old_value, new_value, changed_by)
        VALUES (NEW.id, 'sent_quantity', OLD.sent_quantity, NEW.sent_quantity, NEW.created_by);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_allocation_cells_audit
    AFTER UPDATE ON allocation_sheet_cells
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE FUNCTION log_cell_changes();

-- ================================================================================
-- Verification Queries
-- ================================================================================

-- Check tables created:
-- SELECT tablename FROM pg_tables WHERE tablename LIKE 'allocation%' ORDER BY tablename;

-- Check indexes:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename LIKE 'allocation%' ORDER BY tablename, indexname;

-- Check triggers:
-- SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE tgrelid::regclass::text LIKE 'allocation%';
