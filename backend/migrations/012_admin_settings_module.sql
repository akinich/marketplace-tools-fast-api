-- ============================================================================
-- Migration 012: Admin Settings Module
-- ============================================================================
-- Version: 1.0.0
-- Purpose: Add Settings as a sub-module of Admin
-- ============================================================================

BEGIN;

-- Get the admin module ID and insert sub-module
DO $$
DECLARE
    admin_module_id INTEGER;
BEGIN
    -- Get admin module ID
    SELECT id INTO admin_module_id FROM modules WHERE module_key = 'admin';

    -- Check if admin module exists
    IF admin_module_id IS NULL THEN
        RAISE NOTICE 'Admin module not found. Skipping settings module creation.';
        RETURN;
    END IF;

    -- Insert admin settings sub-module
    INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active, parent_module_id)
    VALUES
        ('admin_settings', 'System Settings', 'Configure application settings', '⚙️', 7, true, admin_module_id)
    ON CONFLICT (module_key) DO UPDATE SET
        module_name = EXCLUDED.module_name,
        description = EXCLUDED.description,
        icon = EXCLUDED.icon,
        parent_module_id = EXCLUDED.parent_module_id,
        is_active = EXCLUDED.is_active;

    RAISE NOTICE 'Admin settings module created/updated successfully';
END $$;

COMMIT;
