-- ================================================================================
-- Module Registration: Purchase Order Management
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-06
-- Description: Register Purchase Order Management module in modules table
-- ================================================================================

-- Insert or update module registration
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'purchase_orders',
    'Purchase Orders',
    'Create and manage purchase orders with vendor-specific pricing and Zoho export',
    'ShoppingCart',
    NULL,  -- Top-level module (or set parent if needed)
    true,
    10
)
ON CONFLICT (module_key) DO UPDATE SET
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    display_order = EXCLUDED.display_order;

-- Verify module registered
SELECT module_key, module_name, description, icon, is_active
FROM modules
WHERE module_key = 'purchase_orders';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Purchase Order Management module registered successfully';
END $$;
