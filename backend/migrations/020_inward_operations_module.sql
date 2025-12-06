-- ============================================================================
-- Migration: Register Inward Operations Module
-- ============================================================================
-- Description: Registers the Inward Operations parent module and its sub-modules
-- Created: 2024-12-06
-- ============================================================================

-- Insert Inward Operations parent module
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

-- Insert Purchase Orders sub-module
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
    'Create and manage purchase orders with intelligent pricing',
    NULL,
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    10
) ON CONFLICT (module_key) DO NOTHING;

-- Insert Vendor Pricing sub-module
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'vendor_pricing', 
    'Vendor Pricing',
    'Manage vendor-specific item pricing (Admin only)',
    NULL,
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    20
) ON CONFLICT (module_key) DO NOTHING;
