-- ============================================================================
-- Migration: 026_orders_module.sql
-- Description: Create orders and order_items tables for B2C WooCommerce orders
-- Created: 2025-12-07
-- ============================================================================

-- Drop existing tables (for clean migration)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

-- ============================================================================
-- Main Orders Table
-- ============================================================================

CREATE TABLE orders (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- WooCommerce Identifiers
    woo_order_id INTEGER UNIQUE NOT NULL,
    order_number VARCHAR(100) NOT NULL,

    -- Customer Reference
    customer_id INTEGER REFERENCES woo_customers(customer_id) ON DELETE SET NULL,

    -- Order Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Possible values: pending, processing, on-hold, completed, cancelled, refunded, failed

    -- Order Dates
    date_created TIMESTAMP WITH TIME ZONE NOT NULL,
    date_modified TIMESTAMP WITH TIME ZONE,
    date_completed TIMESTAMP WITH TIME ZONE,
    date_paid TIMESTAMP WITH TIME ZONE,

    -- Financial Information
    currency VARCHAR(10) DEFAULT 'INR',
    subtotal DECIMAL(10, 2) DEFAULT 0.00,
    total_tax DECIMAL(10, 2) DEFAULT 0.00,
    shipping_total DECIMAL(10, 2) DEFAULT 0.00,
    discount_total DECIMAL(10, 2) DEFAULT 0.00,
    total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Payment Information
    payment_method VARCHAR(100),
    payment_method_title VARCHAR(200),
    transaction_id VARCHAR(200),

    -- Customer Notes & Order Source
    customer_note TEXT,
    created_via VARCHAR(50),  -- web, mobile, admin, rest-api, etc.

    -- Billing Address (JSONB for flexibility)
    billing JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Structure: {first_name, last_name, company, address_1, address_2, city, state, postcode, country, email, phone}

    -- Shipping Address (JSONB for flexibility)
    shipping JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Structure: {first_name, last_name, company, address_1, address_2, city, state, postcode, country}

    -- Sync Metadata
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_source VARCHAR(20) DEFAULT 'webhook',  -- webhook, api, manual

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_status CHECK (status IN ('pending', 'processing', 'on-hold', 'completed', 'cancelled', 'refunded', 'failed')),
    CONSTRAINT check_sync_source CHECK (sync_source IN ('webhook', 'api', 'manual'))
);

-- ============================================================================
-- Order Items Table
-- ============================================================================

CREATE TABLE order_items (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER,  -- Reference to WooCommerce product_id
    variation_id INTEGER,  -- For product variations

    -- Item Details
    name VARCHAR(500) NOT NULL,
    sku VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,

    -- Pricing
    price DECIMAL(10, 2) DEFAULT 0.00,  -- Unit price
    subtotal DECIMAL(10, 2) DEFAULT 0.00,  -- Before tax
    total DECIMAL(10, 2) DEFAULT 0.00,  -- After tax
    tax DECIMAL(10, 2) DEFAULT 0.00,

    -- Additional Metadata (for custom fields, attributes, etc.)
    meta_data JSONB DEFAULT '{}'::jsonb,

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Orders Table Indexes
CREATE INDEX idx_orders_woo_order_id ON orders(woo_order_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date_created ON orders(date_created DESC);
CREATE INDEX idx_orders_date_modified ON orders(date_modified DESC);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_payment_method ON orders(payment_method);
CREATE INDEX idx_orders_last_synced_at ON orders(last_synced_at);

-- JSONB Indexes for faster queries on billing/shipping
CREATE INDEX idx_orders_billing_email ON orders USING GIN ((billing->'email'));
CREATE INDEX idx_orders_billing_phone ON orders USING GIN ((billing->'phone'));
CREATE INDEX idx_orders_shipping_city ON orders USING GIN ((shipping->'city'));

-- Order Items Table Indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_variation_id ON order_items(variation_id);
CREATE INDEX idx_order_items_sku ON order_items(sku);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE orders IS 'WooCommerce B2C orders with full order details, synced via webhooks and API';
COMMENT ON TABLE order_items IS 'Line items for each order with product references';

COMMENT ON COLUMN orders.woo_order_id IS 'WooCommerce order ID (unique identifier from WooCommerce)';
COMMENT ON COLUMN orders.customer_id IS 'Foreign key to woo_customers table';
COMMENT ON COLUMN orders.billing IS 'JSONB containing full billing address and contact info';
COMMENT ON COLUMN orders.shipping IS 'JSONB containing full shipping address';
COMMENT ON COLUMN orders.last_synced_at IS 'Last time this order was synced from WooCommerce';
COMMENT ON COLUMN orders.sync_source IS 'Source of last sync: webhook, api, or manual';

COMMENT ON COLUMN order_items.product_id IS 'WooCommerce product ID (not FK to maintain flexibility)';
COMMENT ON COLUMN order_items.variation_id IS 'WooCommerce variation ID for product variants';
COMMENT ON COLUMN order_items.meta_data IS 'JSONB for storing custom fields, attributes, etc.';

-- ============================================================================
-- Update Trigger for updated_at
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_orders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for orders table
CREATE TRIGGER trigger_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();

-- Trigger for order_items table
CREATE TRIGGER trigger_order_items_updated_at
    BEFORE UPDATE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();

-- ============================================================================
-- Success Message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 026_orders_module.sql completed successfully!';
    RAISE NOTICE 'Created tables: orders, order_items';
    RAISE NOTICE 'Created indexes for optimized queries';
END $$;
