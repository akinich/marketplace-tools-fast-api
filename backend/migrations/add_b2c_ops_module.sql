-- ============================================================================
-- Migration: Add B2C Ops Module and Sub-modules
-- Description: Creates parent module 'b2c_ops' and child module 'order_extractor'
-- ============================================================================

-- Insert parent module: B2C Ops
INSERT INTO modules (module_key, module_name, description, icon, is_active, parent_module_id, display_order)
VALUES (
    'b2c_ops',
    'B2C Operations',
    'Business-to-consumer operations including order management, shipping, and labeling',
    '🛒',
    true,
    NULL,
    50
) ON CONFLICT (module_key) DO NOTHING;

-- Insert child module: Order Extractor
INSERT INTO modules (module_key, module_name, description, icon, is_active, parent_module_id, display_order)
VALUES (
    'order_extractor',
    'Order Extractor',
    'Extract orders from WooCommerce and export to Excel',
    '📦',
    true,
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'),
    1
) ON CONFLICT (module_key) DO NOTHING;

-- Add WooCommerce API settings to system_settings
INSERT INTO system_settings (category, setting_key, setting_value, is_public, is_encrypted, description)
VALUES
    ('woocommerce', 'api_url', '', false, false, 'WooCommerce API URL (e.g., https://your-site.com/wp-json/wc/v3)'),
    ('woocommerce', 'consumer_key', '', false, true, 'WooCommerce API Consumer Key'),
    ('woocommerce', 'consumer_secret', '', false, true, 'WooCommerce API Consumer Secret')
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
