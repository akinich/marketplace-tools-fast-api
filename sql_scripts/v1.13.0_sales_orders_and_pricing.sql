/*
================================================================================
Sales Order & Pricing Module Schema
================================================================================
Version: 1.13.0
Created: 2025-12-07
Database: Supabase PostgreSQL

Description:
  - Adds customer_price_history for time-based customer-specific pricing.
  - Adds sales_orders table for managing sales orders with full workflow.
  - Adds sales_order_items table for line items.
  - Adds so_status_history for complete audit trail.
  - Registers the 'sales_orders' module.

Reference: Mirrors structure of Purchase Order (PO) module (Migration 018).
================================================================================
*/

-- ============================================================================
-- 1. CUSTOMER PRICING TABLE (Time-Based)
-- ============================================================================
-- Similar to vendor_item_price_history in PO module

CREATE TABLE IF NOT EXISTS customer_price_history (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES zoho_customers(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE CASCADE,
    
    -- Pricing
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    
    -- Effective Date Range
    effective_from DATE NOT NULL,
    effective_to DATE, -- NULL means indefinite
    
    -- Audit Trail
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    
    -- Ensure unique active price per customer/item (handled by app logic usually, but index helps)
    CONSTRAINT check_customer_price_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cust_price_lookup ON customer_price_history(customer_id, item_id, effective_from);
CREATE INDEX IF NOT EXISTS idx_cust_price_dates ON customer_price_history(effective_from, effective_to);

COMMENT ON TABLE customer_price_history IS 'Time-based customer-specific item pricing';

-- ============================================================================
-- 2. SALES ORDER HEADER TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_orders (
    id SERIAL PRIMARY KEY,
    so_number VARCHAR(50) UNIQUE NOT NULL, -- Format: SO/YY-YY/XXXX
    
    -- Customer & Dates
    customer_id INTEGER NOT NULL REFERENCES zoho_customers(id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE, -- Date of order placement
    delivery_date DATE, -- Expected delivery
    
    -- Status & Source
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    order_source VARCHAR(50) DEFAULT 'manual', -- manual, whatsapp, email, website
    
    -- Financials
    subtotal NUMERIC(12, 2) DEFAULT 0,
    tax_total NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    
    -- Meta
    notes TEXT,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    exported_at TIMESTAMP WITH TIME ZONE, -- For Zoho sync
    
    -- Constraints
    CONSTRAINT check_so_status_valid CHECK (status IN (
        'draft', 'confirmed', 'packing', 'shipped', 'completed', 'cancelled', 'exported_to_zoho'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_so_customer ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_so_status ON sales_orders(status);
CREATE INDEX IF NOT EXISTS idx_so_date ON sales_orders(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_so_number ON sales_orders(so_number);

COMMENT ON COLUMN sales_orders.status IS 'Workflow: draft -> confirmed -> packing -> shipped -> completed';

-- ============================================================================
-- 3. SALES ORDER ITEMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_order_items (
    id SERIAL PRIMARY KEY,
    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES zoho_items(id),
    
    -- Quantities
    quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),
    
    -- Pricing
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    price_source VARCHAR(20) NOT NULL DEFAULT 'manual', -- customer, manual, item_rate
    tax_percentage NUMERIC(5, 2) DEFAULT 0,
    
    -- Computed
    line_total NUMERIC(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_so_items_order ON sales_order_items(sales_order_id);
CREATE INDEX IF NOT EXISTS idx_so_items_item ON sales_order_items(item_id);

COMMENT ON COLUMN sales_order_items.price_source IS 'Source: customer (tier 1), item_rate (tier 2), manual (tier 3)';

-- ============================================================================
-- 4. SALES ORDER STATUS HISTORY (Audit Trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS so_status_history (
    id SERIAL PRIMARY KEY,
    sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_so_history_order ON so_status_history(sales_order_id);
CREATE INDEX IF NOT EXISTS idx_so_history_date ON so_status_history(changed_at DESC);

-- ============================================================================
-- 5. TRIGGERS
-- ============================================================================

-- Function to update sales_orders.updated_at
CREATE OR REPLACE FUNCTION update_sales_order_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_sales_order_timestamp ON sales_orders;
CREATE TRIGGER trigger_update_sales_order_timestamp
BEFORE UPDATE ON sales_orders
FOR EACH ROW
EXECUTE FUNCTION update_sales_order_timestamp();

-- Function to calculate SO totals
CREATE OR REPLACE FUNCTION update_sales_order_totals()
RETURNS TRIGGER AS $$
DECLARE
    order_id INTEGER;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        order_id := OLD.sales_order_id;
    ELSE
        order_id := NEW.sales_order_id;
    END IF;

    UPDATE sales_orders
    SET 
        subtotal = (SELECT COALESCE(SUM(line_total), 0) FROM sales_order_items WHERE sales_order_id = order_id),
        total_amount = (SELECT COALESCE(SUM(line_total), 0) FROM sales_order_items WHERE sales_order_id = order_id), -- Tax logic can be added later
        updated_at = NOW()
    WHERE id = order_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calc_so_totals ON sales_order_items;
CREATE TRIGGER trigger_calc_so_totals
AFTER INSERT OR UPDATE OR DELETE ON sales_order_items
FOR EACH ROW
EXECUTE FUNCTION update_sales_order_totals();

-- ============================================================================
-- 6. MODULE REGISTRATION
-- ============================================================================

INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'sales_orders',
    'Sales Orders',
    'Manage customer orders, custom pricing, and outbound logistics',
    'ShoppingBag',
    NULL,
    true,
    11 -- After Purchase Orders (10)
)
ON CONFLICT (module_key) DO UPDATE SET
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    display_order = EXCLUDED.display_order;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
