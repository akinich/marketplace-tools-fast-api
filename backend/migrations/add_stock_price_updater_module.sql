-- ============================================================================
-- Stock & Price Updater Module Migration
-- ============================================================================
-- Created: 2025-12-03
-- Purpose: Create tables and register module for stock/price management
-- Also restructures modules: Creates B2C Management parent and moves 
-- woo_to_zoho_export from b2c_ops to b2c_management
-- ============================================================================

-- ============================================================================
-- STEP 1: Create B2C Management Parent Module
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
    'b2c_management',
    'B2C Management',
    'Manage B2C operations including exports and stock/price updates',
    'ManageAccounts',
    NULL,
    true,
    50
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'B2C Management',
    description = 'Manage B2C operations including exports and stock/price updates',
    icon = 'ManageAccounts';

-- ============================================================================
-- STEP 2: Move woo_to_zoho_export to B2C Management
-- ============================================================================

UPDATE modules
SET parent_module_id = (SELECT id FROM modules WHERE module_key = 'b2c_management')
WHERE module_key = 'woo_to_zoho_export';

-- ============================================================================
-- STEP 3: Create product_update_settings Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS product_update_settings (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    variation_id BIGINT,
    is_updatable BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    notes TEXT,
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique constraint on product_id + variation_id combination
    UNIQUE (product_id, variation_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_product_update_settings_product_id 
    ON product_update_settings(product_id);
CREATE INDEX IF NOT EXISTS idx_product_update_settings_variation_id 
    ON product_update_settings(variation_id);
CREATE INDEX IF NOT EXISTS idx_product_update_settings_updatable 
    ON product_update_settings(is_updatable) WHERE is_updatable = true;
CREATE INDEX IF NOT EXISTS idx_product_update_settings_deleted 
    ON product_update_settings(is_deleted) WHERE is_deleted = true;

-- ============================================================================
-- STEP 4: Create stock_price_history Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_price_history (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    variation_id BIGINT,
    field_changed VARCHAR(50) NOT NULL, -- 'stock_quantity', 'regular_price', 'sale_price'
    old_value TEXT,
    new_value TEXT,
    changed_by UUID REFERENCES auth.users(id),
    batch_id UUID NOT NULL,
    change_source VARCHAR(50) DEFAULT 'manual', -- 'manual', 'excel_upload', 'sync'
    sync_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'success', 'failed'
    sync_error TEXT,
    sync_attempted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_stock_price_history_product_id 
    ON stock_price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_price_history_variation_id 
    ON stock_price_history(variation_id);
CREATE INDEX IF NOT EXISTS idx_stock_price_history_batch_id 
    ON stock_price_history(batch_id);
CREATE INDEX IF NOT EXISTS idx_stock_price_history_changed_by 
    ON stock_price_history(changed_by);
CREATE INDEX IF NOT EXISTS idx_stock_price_history_created_at 
    ON stock_price_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_price_history_sync_status 
    ON stock_price_history(sync_status);

-- ============================================================================
-- STEP 5: Register stock_price_updater Module
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
    'stock_price_updater',
    'Stock & Price Updater',
    'Update WooCommerce product stock and prices with list management and bulk upload',
    'PriceChange',
    (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    true,
    10
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Stock & Price Updater',
    description = 'Update WooCommerce product stock and prices with list management and bulk upload',
    icon = 'PriceChange',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    display_order = 10;

-- ============================================================================
-- STEP 6: Grant Permissions to Admin Role
-- ============================================================================

-- Grant access to admin role for stock_price_updater module
INSERT INTO user_module_permissions (user_id, module_id, can_access, can_edit, can_delete)
SELECT 
    up.id,
    m.id,
    true,
    true,
    true
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
  AND m.module_key = 'stock_price_updater'
ON CONFLICT (user_id, module_id) DO UPDATE SET
    can_access = true,
    can_edit = true,
    can_delete = true;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. product_update_settings: Controls which products can be updated
--    - Default: All products are updatable (is_updatable = true)
--    - Admin can lock products (is_updatable = false)
--    - Products deleted from WooCommerce are marked (is_deleted = true)
--
-- 2. stock_price_history: Audit log for all changes
--    - Tracks every change with old/new values
--    - Groups changes by batch_id for bulk operations
--    - Tracks sync status to WooCommerce
--    - Kept indefinitely for audit purposes
--
-- 3. Module Restructuring:
--    - Created b2c_management parent module
--    - Moved woo_to_zoho_export under b2c_management
--    - Registered stock_price_updater under b2c_management
-- ============================================================================
