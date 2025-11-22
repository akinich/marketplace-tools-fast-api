-- ============================================================================
-- Safely Remove Duplicate Telegram Module
-- ============================================================================
-- Purpose: Remove the top-level telegram module after checking dependencies
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- First, check if there are any user permissions tied to this module
DO $$
DECLARE
    telegram_module_id INTEGER;
    permission_count INTEGER;
BEGIN
    -- Get the ID of the standalone telegram module
    SELECT id INTO telegram_module_id
    FROM modules
    WHERE module_key = 'telegram' AND parent_module_id IS NULL;

    IF telegram_module_id IS NOT NULL THEN
        -- Check for user permissions
        SELECT COUNT(*) INTO permission_count
        FROM user_module_permissions
        WHERE module_id = telegram_module_id;

        RAISE NOTICE 'Found % user permissions for standalone telegram module', permission_count;

        -- Remove user permissions first
        IF permission_count > 0 THEN
            DELETE FROM user_module_permissions WHERE module_id = telegram_module_id;
            RAISE NOTICE 'Deleted % user permissions', permission_count;
        END IF;

        -- Now delete the module
        DELETE FROM modules WHERE id = telegram_module_id;
        RAISE NOTICE 'Deleted standalone telegram module (ID: %)', telegram_module_id;
    ELSE
        RAISE NOTICE 'No standalone telegram module found - already clean!';
    END IF;
END $$;

-- Verify the cleanup
SELECT
    module_key,
    module_name,
    icon,
    display_order,
    CASE
        WHEN parent_module_id IS NULL THEN 'Top-level'
        ELSE 'Sub-module'
    END as type
FROM modules
WHERE module_key LIKE '%telegram%'
ORDER BY display_order;

COMMIT;

-- ============================================================================
-- Expected Result: Only 'admin_telegram' should remain
-- ============================================================================
