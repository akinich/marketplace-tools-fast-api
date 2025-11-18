/*
================================================================================
Farm Management System - Database Migration v1.1.0
================================================================================
Version: 1.1.0
Created: 2025-11-17
Description: Adds hierarchical module support and user creation functionality

Changes:
--------
1. Add parent_module_id to modules table for hierarchical structure
2. Add password_hash to user_profiles for password-based authentication
3. Create inventory sub-modules
4. Update user_accessible_modules view to support hierarchy
5. Add helper function for checking sub-module access

Migration Path: v1.0.0 → v1.1.0
================================================================================
*/

-- ============================================================================
-- STEP 1: Add parent_module_id to modules table
-- ============================================================================

-- Add parent_module_id column
ALTER TABLE modules ADD COLUMN IF NOT EXISTS parent_module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_modules_parent_id ON modules(parent_module_id);

COMMENT ON COLUMN modules.parent_module_id IS 'Parent module ID for hierarchical structure (NULL = top-level module)';


-- ============================================================================
-- STEP 2: Add password_hash to user_profiles
-- ============================================================================

-- Add password_hash column
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS password_hash TEXT;

COMMENT ON COLUMN user_profiles.password_hash IS 'Hashed password for authentication (bcrypt)';


-- ============================================================================
-- STEP 3: Create inventory sub-modules
-- ============================================================================

-- First, get the inventory module ID
DO $$
DECLARE
    inventory_module_id INTEGER;
BEGIN
    -- Get inventory module ID
    SELECT id INTO inventory_module_id FROM modules WHERE module_key = 'inventory';

    -- Insert inventory sub-modules
    INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active, parent_module_id)
    VALUES
        -- Dashboard
        ('inventory_dashboard', 'Dashboard', 'Inventory overview and key metrics', '📊', 1, true, inventory_module_id),

        -- Current Stock
        ('inventory_current_stock', 'Current Stock', 'View current stock levels and availability', '📦', 2, true, inventory_module_id),

        -- Add Stock
        ('inventory_add_stock', 'Add Stock', 'Add new stock to inventory', '➕', 3, true, inventory_module_id),

        -- Adjustments
        ('inventory_adjustments', 'Adjustments', 'Stock adjustments and corrections', '⚖️', 4, true, inventory_module_id),

        -- Purchase Orders
        ('inventory_purchase_orders', 'Purchase Orders', 'Manage purchase orders', '📝', 5, true, inventory_module_id),

        -- Alerts
        ('inventory_alerts', 'Alerts', 'Low stock and expiry alerts', '🔔', 6, true, inventory_module_id),

        -- History
        ('inventory_history', 'History', 'Transaction history and audit trail', '📜', 7, true, inventory_module_id),

        -- Item Master
        ('inventory_items', 'Item Master', 'Manage inventory items', '📋', 8, true, inventory_module_id),

        -- Categories
        ('inventory_categories', 'Categories', 'Manage item categories', '🏷️', 9, true, inventory_module_id),

        -- Suppliers
        ('inventory_suppliers', 'Suppliers', 'Manage suppliers and vendors', '🏢', 10, true, inventory_module_id),

        -- Analytics
        ('inventory_analytics', 'Analytics', 'Reports and analytics', '📈', 11, true, inventory_module_id)
    ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Inventory sub-modules created successfully';
END $$;


-- ============================================================================
-- STEP 4: Drop and recreate user_accessible_modules view with hierarchy support
-- ============================================================================

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
        -- Admins get access to everything
        r.role_name = 'Admin'
        OR
        -- User has explicit permission to this module/sub-module
        (ump.can_access = TRUE)
        OR
        -- User has permission to parent module AND no sub-module-specific permissions exist
        (
            m.parent_module_id IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM user_module_permissions parent_ump
                WHERE parent_ump.user_id = up.id
                AND parent_ump.module_id = m.parent_module_id
                AND parent_ump.can_access = TRUE
            )
            -- Check if user has ANY sub-module permissions for this parent
            AND NOT EXISTS (
                SELECT 1 FROM user_module_permissions sub_ump
                JOIN modules sub_m ON sub_m.id = sub_ump.module_id
                WHERE sub_ump.user_id = up.id
                AND sub_m.parent_module_id = m.parent_module_id
                AND sub_ump.can_access = TRUE
            )
        )
    )
ORDER BY up.id, m.display_order;

COMMENT ON VIEW user_accessible_modules IS 'Users accessible modules with hierarchical permission support';


-- ============================================================================
-- STEP 5: Create helper function for permission checking
-- ============================================================================

CREATE OR REPLACE FUNCTION user_can_access_module(
    p_user_id UUID,
    p_module_key VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    v_user_role VARCHAR(50);
    v_module_id INTEGER;
    v_parent_module_id INTEGER;
    v_has_permission BOOLEAN;
    v_has_submodule_restrictions BOOLEAN;
BEGIN
    -- Get user role
    SELECT r.role_name INTO v_user_role
    FROM user_profiles up
    JOIN roles r ON r.id = up.role_id
    WHERE up.id = p_user_id AND up.is_active = TRUE;

    -- Admins have full access
    IF v_user_role = 'Admin' THEN
        RETURN TRUE;
    END IF;

    -- Get module info
    SELECT id, parent_module_id INTO v_module_id, v_parent_module_id
    FROM modules
    WHERE module_key = p_module_key AND is_active = TRUE;

    -- Module doesn't exist or inactive
    IF v_module_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check direct permission
    SELECT EXISTS (
        SELECT 1 FROM user_module_permissions
        WHERE user_id = p_user_id
        AND module_id = v_module_id
        AND can_access = TRUE
    ) INTO v_has_permission;

    IF v_has_permission THEN
        RETURN TRUE;
    END IF;

    -- If this is a sub-module, check parent permission
    IF v_parent_module_id IS NOT NULL THEN
        -- Check if user has parent permission
        SELECT EXISTS (
            SELECT 1 FROM user_module_permissions
            WHERE user_id = p_user_id
            AND module_id = v_parent_module_id
            AND can_access = TRUE
        ) INTO v_has_permission;

        IF v_has_permission THEN
            -- Check if user has any sub-module-specific permissions
            SELECT EXISTS (
                SELECT 1 FROM user_module_permissions ump
                JOIN modules m ON m.id = ump.module_id
                WHERE ump.user_id = p_user_id
                AND m.parent_module_id = v_parent_module_id
                AND ump.can_access = TRUE
            ) INTO v_has_submodule_restrictions;

            -- If no sub-module restrictions, grant access
            IF NOT v_has_submodule_restrictions THEN
                RETURN TRUE;
            END IF;
        END IF;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION user_can_access_module IS 'Check if user has access to a module considering hierarchical permissions';


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify schema changes
DO $$
BEGIN
    RAISE NOTICE '=== Migration v1.1.0 Verification ===';

    RAISE NOTICE 'Modules table: parent_module_id column exists = %',
        (SELECT column_name IS NOT NULL FROM information_schema.columns
         WHERE table_name = 'modules' AND column_name = 'parent_module_id');

    RAISE NOTICE 'User_profiles table: password_hash column exists = %',
        (SELECT column_name IS NOT NULL FROM information_schema.columns
         WHERE table_name = 'user_profiles' AND column_name = 'password_hash');

    RAISE NOTICE 'Total modules count = %',
        (SELECT COUNT(*) FROM modules);

    RAISE NOTICE 'Inventory sub-modules count = %',
        (SELECT COUNT(*) FROM modules WHERE parent_module_id = (SELECT id FROM modules WHERE module_key = 'inventory'));

    RAISE NOTICE 'View user_accessible_modules exists = %',
        (SELECT COUNT(*) > 0 FROM information_schema.views WHERE table_name = 'user_accessible_modules');

    RAISE NOTICE 'Function user_can_access_module exists = %',
        (SELECT COUNT(*) > 0 FROM information_schema.routines WHERE routine_name = 'user_can_access_module');

    RAISE NOTICE '=== Migration v1.1.0 Complete ===';
END $$;
