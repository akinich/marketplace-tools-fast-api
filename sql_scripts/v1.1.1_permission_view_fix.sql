/*
================================================================================
Permission Fix for Hierarchical Modules
================================================================================
Version: 1.1.1
Created: 2025-11-17
Description: Fixes permission view to properly handle hierarchical modules

Issue: Admin panel and inventory modules not showing in sidebar
Root cause: Permission view logic was too restrictive

Fix: Simplified view logic to properly handle hierarchical permissions
================================================================================
*/

-- Drop and recreate the view with fixed logic
DROP VIEW IF EXISTS user_accessible_modules;

CREATE OR REPLACE VIEW user_accessible_modules AS
SELECT DISTINCT
    up.id as user_id,
    m.id as module_id,
    m.module_key,
    m.module_name,
    m.description,
    m.icon,
    m.display_order,
    m.parent_module_id,
    -- Include parent module info for sub-modules
    pm.module_key as parent_module_key,
    pm.module_name as parent_module_name
FROM user_profiles up
CROSS JOIN modules m
LEFT JOIN modules pm ON pm.id = m.parent_module_id
LEFT JOIN roles r ON r.id = up.role_id
LEFT JOIN user_module_permissions ump ON ump.user_id = up.id AND ump.module_id = m.id
WHERE
    m.is_active = TRUE
    AND up.is_active = TRUE
    AND (
        -- Condition 1: Admins get access to EVERYTHING
        r.role_name = 'Admin'
        OR
        -- Condition 2: User has explicit permission to this specific module/sub-module
        (ump.can_access = TRUE)
        OR
        -- Condition 3: For SUB-modules - user has permission to parent module
        --               AND does NOT have any explicit sub-module restrictions
        (
            m.parent_module_id IS NOT NULL
            AND EXISTS (
                -- User has access to the parent module
                SELECT 1 FROM user_module_permissions parent_ump
                WHERE parent_ump.user_id = up.id
                AND parent_ump.module_id = m.parent_module_id
                AND parent_ump.can_access = TRUE
            )
            AND NOT EXISTS (
                -- User does NOT have any explicit sub-module permissions for this parent
                -- If they do, they only see the ones they have explicit access to
                SELECT 1 FROM user_module_permissions sub_ump
                JOIN modules sub_m ON sub_m.id = sub_ump.module_id
                WHERE sub_ump.user_id = up.id
                AND sub_m.parent_module_id = m.parent_module_id
                AND sub_ump.can_access = TRUE
            )
        )
    )
ORDER BY up.id, m.parent_module_id NULLS FIRST, m.display_order;

COMMENT ON VIEW user_accessible_modules IS 'Users accessible modules with hierarchical permission support (fixed v1.1.1)';

-- Verification query
DO $$
BEGIN
    RAISE NOTICE '=== Permission View Fix v1.1.1 ===';
    RAISE NOTICE 'View user_accessible_modules recreated successfully';
    RAISE NOTICE 'To verify, run: SELECT * FROM user_accessible_modules WHERE user_id = ''<your_user_id>'';';
END $$;
