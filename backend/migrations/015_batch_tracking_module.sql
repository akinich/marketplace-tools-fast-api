-- ============================================================================
-- Migration 015: Register Batch Tracking Module
-- Description: Registers the Batch Tracking module in the modules table
-- Author: Claude
-- Date: 2024-12-04
-- ============================================================================

-- Register Inventory parent module (if not exists)
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'inventory',
    'Inventory',
    'Inventory management, batch tracking, and wastage analytics',
    'Inventory2',
    NULL,
    true,
    20
) ON CONFLICT (module_key) DO NOTHING;

-- Register Batch Tracking Module
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'batch_tracking',
    'Batch Tracking',
    'Complete batch traceability from farm to customer with audit trail',
    'Timeline',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    10
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Batch Tracking',
    description = 'Complete batch traceability from farm to customer with audit trail',
    icon = 'Timeline',
    display_order = 10;

-- Verify module registration
SELECT
    m.id,
    m.module_key,
    m.module_name,
    m.description,
    p.module_name as parent_module,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key IN ('inventory', 'batch_tracking')
ORDER BY m.display_order;
