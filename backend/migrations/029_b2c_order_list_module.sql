-- ============================================================================
-- Migration: 029_b2c_order_list_module.sql
-- Description: Register B2C Order List module under B2C Management
-- Author: System
-- Date: 2025-12-08
-- ============================================================================

-- Register B2C Order List module
INSERT INTO modules (
    name,
    module_key,
    description,
    icon,
    route_path,
    parent_key,
    display_order,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'B2C Order List',
    'b2c_order_list',
    'Fetch and view B2C orders from WooCommerce',
    'list_alt',
    '/b2c-ops/b2c-order-list',
    'b2c_management',
    6,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (module_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    route_path = EXCLUDED.route_path,
    parent_key = EXCLUDED.parent_key,
    display_order = EXCLUDED.display_order,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Grant access to ALL roles (no restrictions)
-- This ensures everyone who has access to B2C Management can see B2C Order List
INSERT INTO role_module_permissions (role_id, module_id, created_at)
SELECT 
    r.id,
    m.id,
    NOW()
FROM roles r
CROSS JOIN modules m
WHERE m.module_key = 'b2c_order_list'
ON CONFLICT (role_id, module_id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ B2C Order List module registered successfully';
    RAISE NOTICE '✅ All roles granted access';
END $$;
