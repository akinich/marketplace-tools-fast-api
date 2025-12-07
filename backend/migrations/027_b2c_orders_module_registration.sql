-- ============================================================================
-- Migration: Register B2C Orders Module
-- ============================================================================
-- Description: Register the B2C Orders module under B2C Management parent
-- Created: 2025-12-07
-- Note: The tables (orders, order_items) were already created in 026_orders_module.sql
--       This migration only registers the module in the modules table
-- ============================================================================

-- Register B2C Orders as a child module under B2C Management
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'b2c_orders',
    'B2C Orders',
    'Manage WooCommerce B2C orders synced via webhooks and API',
    'ShoppingCart',
    (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    true,
    20
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'B2C Orders',
    description = 'Manage WooCommerce B2C orders synced via webhooks and API',
    icon = 'ShoppingCart',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    display_order = 20,
    is_active = true;

-- ============================================================================
-- Grant Permissions to Admin Role
-- ============================================================================

-- Grant access to admin role for b2c_orders module
INSERT INTO user_module_permissions (user_id, module_id)
SELECT 
    up.id,
    m.id
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
  AND m.module_key = 'b2c_orders'
ON CONFLICT (user_id, module_id) DO NOTHING;

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Verify the module was registered correctly
SELECT 
    m.id,
    m.module_key,
    m.module_name,
    p.module_name as parent_module,
    m.is_active,
    m.display_order
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key = 'b2c_orders';

-- ============================================================================
-- Expected Result
-- ============================================================================
-- module_key: b2c_orders
-- module_name: B2C Orders
-- parent_module: B2C Management
-- is_active: true
-- display_order: 20
-- ============================================================================
