-- ============================================================================
-- Migration: Add Zoho Item Master Module
-- Description: Creates zoho_items table, Zoho Books API settings, and module
-- ============================================================================

BEGIN;

-- 1. Create zoho_items table
CREATE TABLE IF NOT EXISTS zoho_items (
    id SERIAL PRIMARY KEY,
    item_id BIGINT UNIQUE NOT NULL, -- Zoho's unique item ID
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    description TEXT,
    
    -- Pricing
    rate DECIMAL(10, 2), -- Selling price
    purchase_rate DECIMAL(10, 2), -- Purchase price
    
    -- Classification
    item_type VARCHAR(50), -- sales, purchases, sales_and_purchases, inventory
    product_type VARCHAR(50), -- goods, service
    status VARCHAR(50) DEFAULT 'active', -- active, inactive
    
    -- Tax Information
    hsn_or_sac VARCHAR(50), -- HSN/SAC code for GST
    tax_id VARCHAR(100),
    tax_name VARCHAR(100),
    tax_percentage DECIMAL(5, 2),
    is_taxable BOOLEAN DEFAULT TRUE,
    
    -- Other Details
    unit VARCHAR(50), -- Unit of measurement
    account_id VARCHAR(100), -- Income/Expense account ID
    
    -- Timestamps from Zoho
    created_time TIMESTAMP WITH TIME ZONE,
    last_modified_time TIMESTAMP WITH TIME ZONE,
    
    -- Our Timestamps
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Store full Zoho response for reference
    raw_json JSONB
);

-- Create indexes for faster search
CREATE INDEX IF NOT EXISTS idx_zoho_items_item_id ON zoho_items(item_id);
CREATE INDEX IF NOT EXISTS idx_zoho_items_name ON zoho_items(name);
CREATE INDEX IF NOT EXISTS idx_zoho_items_sku ON zoho_items(sku);
CREATE INDEX IF NOT EXISTS idx_zoho_items_status ON zoho_items(status);

-- 2. Add Zoho Books API settings to system_settings
INSERT INTO system_settings (category, setting_key, setting_value, data_type, is_public, is_encrypted, description)
VALUES
    ('zoho', 'zoho.client_id', '""', 'string', false, false, 'Zoho Books OAuth Client ID'),
    ('zoho', 'zoho.client_secret', '""', 'string', false, true, 'Zoho Books OAuth Client Secret'),
    ('zoho', 'zoho.refresh_token', '""', 'string', false, true, 'Zoho Books OAuth Refresh Token'),
    ('zoho', 'zoho.organization_id', '""', 'string', false, false, 'Zoho Books Organization ID'),
    ('zoho', 'zoho.base_url', '"https://books.zoho.com/api/v3"', 'string', false, false, 'Zoho Books API Base URL')
ON CONFLICT (setting_key) DO NOTHING;

-- 3. Register Zoho Item Master module under Database Management
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'zoho_item_master',
    'Zoho Item Master',
    'Manage items from Zoho Books, sync and view master data',
    'Inventory',
    (SELECT id FROM modules WHERE module_key = 'database_management'),
    true,
    20
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Zoho Item Master',
    description = 'Manage items from Zoho Books, sync and view master data',
    icon = 'Inventory',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'database_management'),
    display_order = 20;

COMMIT;
