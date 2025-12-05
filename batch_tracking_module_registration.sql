-- ============================================================================
-- Module Registration SQL for Batch Tracking
-- ============================================================================
-- Description: SQL to register Inventory parent module and Batch Tracking sub-module
-- Note: This SQL is already in backend/migrations/015_batch_tracking_module.sql
--       Run this if the module is not yet registered in your database
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

-- Register Batch Tracking sub-module
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
    m.is_active,
    m.display_order
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key IN ('inventory', 'batch_tracking')
ORDER BY m.display_order;

-- Grant access to admin users (optional - adjust as needed)
-- INSERT INTO user_module_access (user_id, module_id)
-- SELECT u.id, m.id
-- FROM users u
-- CROSS JOIN modules m
-- WHERE u.role = 'admin'
--   AND m.module_key IN ('inventory', 'batch_tracking')
-- ON CONFLICT DO NOTHING;
