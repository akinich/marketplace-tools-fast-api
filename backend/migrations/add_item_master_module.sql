-- Add B2C Item Master Module
-- Created: 2025-12-01

-- 1. Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id BIGINT UNIQUE, -- WooCommerce Product ID
    variation_id BIGINT, -- WooCommerce Variation ID (nullable for simple products)
    sku VARCHAR(100),
    product_name VARCHAR(255) NOT NULL,
    parent_product VARCHAR(255), -- Name of parent product for variations
    
    -- Pricing & Stock (Synced from WC)
    stock_quantity INTEGER DEFAULT 0,
    regular_price DECIMAL(10, 2),
    sale_price DECIMAL(10, 2),
    
    -- Editable Fields (B2C Ops)
    hsn VARCHAR(50),
    zoho_name VARCHAR(255),
    usage_units VARCHAR(50),
    
    -- Metadata
    categories TEXT, -- Comma separated categories
    attribute TEXT, -- Variation attributes
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    product_status VARCHAR(50) DEFAULT 'publish', -- publish, draft, private
    
    -- Timestamps
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster search
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);

-- 2. Register module
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'b2c_item_master',
    'Item Master',
    'Manage B2C products, sync with WooCommerce, and edit master data',
    'Inventory',
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'),
    true,
    20
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Item Master',
    description = 'Manage B2C products, sync with WooCommerce, and edit master data',
    icon = 'Inventory',
    display_order = 20;

-- 3. Grant permissions (assuming role-based access control exists)
-- This part depends on how permissions are handled, usually handled by admin UI
-- But we can ensure the module exists for role assignment
