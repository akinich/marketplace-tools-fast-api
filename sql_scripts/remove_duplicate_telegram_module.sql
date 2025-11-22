-- ============================================================================
-- Remove Duplicate Telegram Module
-- ============================================================================
-- Purpose: Remove the top-level telegram module (keep only admin_telegram)
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- The correct telegram module is 'admin_telegram' (sub-module of admin)
-- Remove the standalone 'telegram' module if it has no parent
DELETE FROM modules
WHERE module_key = 'telegram'
AND parent_module_id IS NULL;

-- Verify only admin_telegram remains
SELECT
    module_key,
    module_name,
    icon,
    display_order,
    parent_module_id,
    CASE
        WHEN parent_module_id IS NULL THEN 'Top-level module'
        ELSE 'Sub-module of ' || (SELECT module_key FROM modules m WHERE m.id = modules.parent_module_id)
    END as module_type
FROM modules
WHERE module_key LIKE '%telegram%'
ORDER BY display_order;

COMMIT;

-- ============================================================================
-- Expected Result:
-- ============================================================================
-- Only 'admin_telegram' should remain as a sub-module of admin
-- ============================================================================
