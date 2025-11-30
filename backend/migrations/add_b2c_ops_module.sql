-- ============================================================================
-- Migration: Add B2C Ops Module and Sub-modules
-- Description: Creates parent module 'b2c_ops' and child module 'order_extractor'
-- ============================================================================

-- 1. Create Parent Module (B2C Ops)
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'b2c_ops', 
    'B2C Operations', 
    'Business to Consumer Operations Management', 
    'ShoppingCart', 
    NULL, 
    true, 
    40
) ON CONFLICT (module_key) DO NOTHING;

-- 2. Create Sub-Module (Order Extractor)
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'order_extractor', 
    'Order Extractor', 
    'Extract and export WooCommerce orders', 
    'GetApp', 
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'), 
    true, 
    10
) ON CONFLICT (module_key) DO NOTHING;

-- Add WooCommerce API settings to system_settings
INSERT INTO system_settings (category, setting_key, setting_value, data_type, is_public, is_encrypted, description)
VALUES
    ('woocommerce', 'api_url', '""', 'string', false, false, 'WooCommerce API URL (e.g., https://your-site.com/wp-json/wc/v3)'),
    ('woocommerce', 'consumer_key', '""', 'string', false, true, 'WooCommerce API Consumer Key'),
    ('woocommerce', 'consumer_secret', '""', 'string', false, true, 'WooCommerce API Consumer Secret')
ON CONFLICT (setting_key) DO NOTHING;

-- Grant admin access to B2C Ops modules
INSERT INTO user_module_permissions (user_id, module_id, can_access)
SELECT 
    up.id,
    m.id,
    true
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = 1  -- Admin role
  AND m.module_key IN ('b2c_ops', 'order_extractor')
ON CONFLICT (user_id, module_id) DO UPDATE SET can_access = true;
