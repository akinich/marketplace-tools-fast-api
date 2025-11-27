-- ============================================================================
-- Farm Management System - Add Missing Modules
-- ============================================================================
-- Purpose: Add all missing modules that should exist in production
-- Date: 2025-11-27
-- Run this on your production database via Supabase SQL Editor
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add Documentation Module
-- ============================================================================
INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
VALUES (
    'docs',
    'Documentation',
    'System documentation and guides',
    'book',
    true,
    90,
    NULL
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- STEP 2: Add Admin Sub-Modules
-- ============================================================================
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
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES
        -- User Management
        ('admin_users', 'User Management', 'Manage users, roles, and permissions', 'users', true, 1, admin_module_id),

        -- Module Management
        ('admin_modules', 'Module Management', 'Enable/disable system modules', 'settings', true, 2, admin_module_id),

        -- Activity Logs
        ('admin_activity', 'Activity Logs', 'View system activity and audit trail', 'list', true, 3, admin_module_id),

        -- Security Dashboard
        ('admin_security', 'Security Dashboard', 'Sessions, login history, and security stats', 'lock', true, 4, admin_module_id),

        -- Units of Measurement
        ('admin_units', 'Units of Measurement', 'Manage standardized measurement units', 'ruler', true, 5, admin_module_id),

        -- Settings
        ('admin_settings', 'Settings', 'System settings and configuration', 'settings', true, 6, admin_module_id)
    ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Admin sub-modules created successfully';
END $$;

-- ============================================================================
-- STEP 3: Add Communication Parent Module
-- ============================================================================
INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
VALUES (
    'communication',
    'Communication',
    'Manage all communication channels: Email, Telegram, Webhooks, API Keys, and Real-time notifications',
    'radio',
    true,
    50,
    NULL
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- STEP 4: Add Communication Sub-Modules
-- ============================================================================
DO $$
DECLARE
    comm_module_id INT;
    telegram_module_id INT;
BEGIN
    -- Get Communication module ID
    SELECT id INTO comm_module_id FROM modules WHERE module_key = 'communication';

    -- Check if standalone Telegram module exists and update it
    SELECT id INTO telegram_module_id FROM modules WHERE module_key = 'telegram';

    IF telegram_module_id IS NOT NULL THEN
        -- Update existing Telegram module to be child of Communication
        UPDATE modules
        SET
            module_key = 'com_telegram',
            parent_module_id = comm_module_id,
            display_order = 1,
            module_name = 'Telegram Notifications',
            description = 'Configure Telegram bot notifications and alerts'
        WHERE id = telegram_module_id;
    ELSE
        -- Create new Telegram module as child of Communication
        INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
        VALUES (
            'com_telegram',
            'Telegram Notifications',
            'Configure Telegram bot notifications and alerts',
            'message',
            true,
            1,
            comm_module_id
        ) ON CONFLICT (module_key) DO NOTHING;
    END IF;

    -- Create SMTP Email child module
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES (
        'com_smtp',
        'Email (SMTP)',
        'Configure SMTP email settings, manage email templates, and send notifications',
        'mail',
        true,
        2,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create Webhooks child module
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES (
        'com_webhooks',
        'Webhooks',
        'Manage outgoing webhooks for event-driven integrations',
        'link',
        true,
        3,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create API Keys child module
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES (
        'com_api_keys',
        'API Keys',
        'Manage API keys for programmatic access and automation',
        'key',
        true,
        4,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create WebSockets child module
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES (
        'com_websockets',
        'Real-time (WebSocket)',
        'Configure real-time notifications and live updates',
        'bell',
        true,
        5,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Communication module structure created successfully';
END $$;

-- ============================================================================
-- STEP 5: Verify All Modules
-- ============================================================================
SELECT
    m.module_key,
    m.module_name,
    CASE
        WHEN m.parent_module_id IS NULL THEN 'Parent Module'
        ELSE p.module_name || ' > Sub-module'
    END as type,
    m.display_order,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
ORDER BY
    COALESCE(m.parent_module_id, m.id),
    m.display_order;

COMMIT;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- After running this migration:
-- 1. Admin users will automatically have access to ALL modules (no manual permissions needed)
-- 2. Regular users need explicit permissions via user_module_permissions table
-- 3. Restart your backend service to see the changes
-- ============================================================================
