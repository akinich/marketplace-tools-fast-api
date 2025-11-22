-- ============================================================================
-- Fix Admin Sub-Modules Display Order
-- ============================================================================
-- Purpose: Correct the display order of admin sub-modules
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- Update display order for admin sub-modules
UPDATE modules SET display_order = 1 WHERE module_key = 'admin_users';
UPDATE modules SET display_order = 2 WHERE module_key = 'admin_modules';
UPDATE modules SET display_order = 3 WHERE module_key = 'admin_activity';
UPDATE modules SET display_order = 4 WHERE module_key = 'admin_security';
UPDATE modules SET display_order = 5 WHERE module_key = 'admin_units';
UPDATE modules SET display_order = 6 WHERE module_key = 'admin_telegram';

-- Verify the updated order
SELECT
    module_key,
    module_name,
    icon,
    display_order,
    is_active
FROM modules
WHERE parent_module_id = (SELECT id FROM modules WHERE module_key = 'admin')
ORDER BY display_order;

COMMIT;

-- ============================================================================
-- Expected Result:
-- ============================================================================
-- 1. User Management
-- 2. Module Management
-- 3. Activity Logs
-- 4. Security
-- 5. Units of Measurement
-- 6. Telegram Notifications
-- ============================================================================
