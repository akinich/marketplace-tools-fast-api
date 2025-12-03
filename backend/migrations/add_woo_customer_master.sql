-- ============================================================================
-- Migration: Add WooCommerce Customer Master Module
-- Description: Creates woo_customers table, module entry, and permissions
-- ============================================================================

BEGIN;

-- 1. Create woo_customers table
CREATE TABLE IF NOT EXISTS woo_customers (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- WooCommerce Customer ID
    customer_id INTEGER UNIQUE NOT NULL,
    
    -- Core Customer Info
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'customer',
    
    -- Billing Address
    billing_first_name VARCHAR(100),
    billing_last_name VARCHAR(100),
    billing_company VARCHAR(200),
    billing_address_1 VARCHAR(255),
    billing_address_2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_postcode VARCHAR(20),
    billing_country VARCHAR(2),
    billing_email VARCHAR(255),
    billing_phone VARCHAR(50),
    
    -- Shipping Address
    shipping_first_name VARCHAR(100),
    shipping_last_name VARCHAR(100),
    shipping_company VARCHAR(200),
    shipping_address_1 VARCHAR(255),
    shipping_address_2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postcode VARCHAR(20),
    shipping_country VARCHAR(2),
    
    -- Customer Metadata
    is_paying_customer BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    
    -- Timestamps from WooCommerce
    date_created TIMESTAMP,
    date_modified TIMESTAMP,
    
    -- Sync tracking
    last_sync_at TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    
    -- User notes
    notes TEXT
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_woo_customers_email ON woo_customers(email);
CREATE INDEX IF NOT EXISTS idx_woo_customers_customer_id ON woo_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_woo_customers_last_sync ON woo_customers(last_sync_at);
CREATE INDEX IF NOT EXISTS idx_woo_customers_billing_country ON woo_customers(billing_country);
CREATE INDEX IF NOT EXISTS idx_woo_customers_is_paying ON woo_customers(is_paying_customer);

-- 3. Add module entry (under Database Management parent)
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'woo_customer_master', 
    'Woo Customer Master', 
    'Manage WooCommerce customers, sync with WooCommerce, and view customer data', 
    'People', 
    (SELECT id FROM modules WHERE module_key = 'database_management'), 
    true, 
    20
) ON CONFLICT (module_key) DO UPDATE SET display_order = 20;

COMMIT;
