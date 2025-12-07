-- ============================================================================
-- Marketplace ERP Tools - Admin Sub-Modules
-- ============================================================================
-- Version: 1.12.0
-- Purpose: Add admin panel sub-modules for better navigation
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- Get the admin module ID and insert sub-modules
DO $$
DECLARE
    admin_module_id INTEGER;
BEGIN
    -- Get admin module ID
    SELECT id INTO admin_module_id FROM modules WHERE module_key = 'admin';

    -- Check if admin module exists
    IF admin_module_id IS NULL THEN
        RAISE EXCEPTION 'Admin module not found. Please ensure base modules are installed.';
    END IF;

    -- Insert admin sub-modules
    INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active, parent_module_id)
    VALUES
        -- User Management
        ('admin_users', 'User Management', 'Manage users, roles, and permissions', '👥', 1, true, admin_module_id),

        -- Module Management
        ('admin_modules', 'Module Management', 'Enable/disable system modules', '⚙️', 2, true, admin_module_id),

        -- Activity Logs
        ('admin_activity', 'Activity Logs', 'View system activity and audit trail', '📜', 3, true, admin_module_id),

        -- Security Dashboard
        ('admin_security', 'Security Dashboard', 'Sessions, login history, and security stats', '🔒', 4, true, admin_module_id),

        -- Units of Measurement
        ('admin_units', 'Units of Measurement', 'Manage standardized measurement units', '📏', 5, true, admin_module_id),

        -- Telegram Notifications
        ('admin_telegram', 'Telegram Notifications', 'Configure Telegram bot notifications', '📱', 6, true, admin_module_id)
    ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Admin sub-modules created successfully';
END $$;

-- Display created admin sub-modules
SELECT
    module_key,
    module_name,
    icon,
    display_order
FROM modules
WHERE parent_module_id = (SELECT id FROM modules WHERE module_key = 'admin')
ORDER BY display_order;

COMMIT;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Admin users automatically have access to all sub-modules
-- 2. Sub-module access is inherited from parent admin module permission
-- 3. Navigation is dynamically loaded based on user permissions
-- ============================================================================
