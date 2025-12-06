-- ============================================================================
-- Migration: Fix Inward Operations Module Nesting
-- ============================================================================
-- Description: Fixes parent-child relationship for Inward Operations modules
-- Created: 2024-12-06
-- ============================================================================

-- Ensure the parent module exists
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'inward', 
    'Inward Operations',
    'Purchase orders, GRN, grading, and packing operations',
    'LocalShipping',
    NULL,
    true,
    25
) ON CONFLICT (module_key) DO NOTHING;

-- Force update the parent_module_id for Purchase Orders
UPDATE modules 
SET parent_module_id = (SELECT id FROM modules WHERE module_key = 'inward')
WHERE module_key = 'purchase_orders';

-- Force update the parent_module_id for Vendor Pricing
UPDATE modules 
SET parent_module_id = (SELECT id FROM modules WHERE module_key = 'inward')
WHERE module_key = 'vendor_pricing';
