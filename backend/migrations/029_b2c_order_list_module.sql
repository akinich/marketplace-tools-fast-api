-- ============================================================================
-- Migration: 029_b2c_order_list_module.sql
-- Description: Remove old B2C Orders module and register new B2C Order List
-- Author: System
-- Date: 2025-12-08
-- ============================================================================

-- ============================================================================
-- PART 1: Remove old B2C Orders module (deleted from codebase)
-- ============================================================================

-- Remove user permissions for old module
DELETE FROM user_module_permissions
WHERE module_id IN (SELECT id FROM modules WHERE module_key = 'b2c_orders');

-- Remove old B2C Orders module
DELETE FROM modules WHERE module_key = 'b2c_orders';

-- Success message for removal
DO $$
BEGIN
    RAISE NOTICE '🗑️  Removed old B2C Orders module and permissions';
END $$;


-- ============================================================================
-- PART 2: Register new B2C Order List module
-- ============================================================================

-- Register B2C Order List module
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'b2c_order_list',
    'B2C Order List',
    'Fetch and view B2C orders from WooCommerce',
    'list_alt',
    (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    true,
    6
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'B2C Order List',
    description = 'Fetch and view B2C orders from WooCommerce',
    icon = 'list_alt',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    display_order = 6,
    is_active = true;

-- Grant access to all Admin users
INSERT INTO user_module_permissions (user_id, module_id)
SELECT 
    up.id,
    m.id
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
  AND m.module_key = 'b2c_order_list'
ON CONFLICT (user_id, module_id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ B2C Order List module registered successfully';
    RAISE NOTICE '✅ Admin users granted access';
END $$;
