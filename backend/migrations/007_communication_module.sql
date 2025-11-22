-- ============================================================================
-- Migration 007: Communication Module Foundation
-- ============================================================================
-- Description: Creates Communication parent module and child modules
-- Author: System
-- Date: 2025-11-22
-- Version: 1.0.0
-- ============================================================================

-- Step 1: Create Communication parent module
INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
VALUES (
    'communication',
    'Communication',
    'Manage all communication channels: Email, Telegram, Webhooks, API Keys, and Real-time notifications',
    '📡',
    true,
    50,
    NULL
) ON CONFLICT (module_key) DO NOTHING;

-- Step 2: Get the Communication module ID
DO $$
DECLARE
    comm_module_id INT;
    telegram_module_id INT;
BEGIN
    -- Get Communication module ID
    SELECT id INTO comm_module_id FROM modules WHERE module_key = 'communication';

    -- Get existing Telegram module ID
    SELECT id INTO telegram_module_id FROM modules WHERE module_key = 'telegram';

    -- Update Telegram module to be child of Communication
    IF telegram_module_id IS NOT NULL THEN
        UPDATE modules
        SET
            module_key = 'com_telegram',
            parent_module_id = comm_module_id,
            display_order = 1
        WHERE id = telegram_module_id;

        -- Update all references to telegram module in user_module_permissions
        UPDATE user_module_permissions
        SET module_id = telegram_module_id
        WHERE module_id = telegram_module_id;
    END IF;

    -- Create SMTP Email child module
    INSERT INTO modules (module_key, module_name, description, icon, is_active, display_order, parent_module_id)
    VALUES (
        'com_smtp',
        'Email (SMTP)',
        'Configure SMTP email settings, manage email templates, and send notifications',
        '📧',
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
        '🔗',
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
        '🔑',
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
        '🔔',
        true,
        5,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Communication module structure created successfully';
END $$;

-- Step 3: Grant admin users access to all Communication modules
DO $$
DECLARE
    admin_role_id INT;
    comm_module_id INT;
    smtp_module_id INT;
    webhooks_module_id INT;
    api_keys_module_id INT;
    websockets_module_id INT;
    admin_user RECORD;
BEGIN
    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE role_name = 'Admin';

    -- Get module IDs
    SELECT id INTO comm_module_id FROM modules WHERE module_key = 'communication';
    SELECT id INTO smtp_module_id FROM modules WHERE module_key = 'com_smtp';
    SELECT id INTO webhooks_module_id FROM modules WHERE module_key = 'com_webhooks';
    SELECT id INTO api_keys_module_id FROM modules WHERE module_key = 'com_api_keys';
    SELECT id INTO websockets_module_id FROM modules WHERE module_key = 'com_websockets';

    -- Grant access to all admin users
    FOR admin_user IN SELECT id FROM user_profiles WHERE role_id = admin_role_id
    LOOP
        -- Communication parent
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.id, comm_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- SMTP
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.id, smtp_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- Webhooks
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.id, webhooks_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- API Keys
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.id, api_keys_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- WebSockets
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.id, websockets_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;
    END LOOP;

    RAISE NOTICE 'Admin permissions granted for Communication modules';
END $$;

-- Step 4: Verify the migration
SELECT
    m.id,
    m.module_key,
    m.module_name,
    CASE WHEN m.parent_module_id IS NULL THEN 'Parent' ELSE 'Child' END as type,
    p.module_name as parent_name,
    m.display_order,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key LIKE 'com%' OR m.module_key = 'communication'
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;
