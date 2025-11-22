# HANDOVER MESSAGE #1: Communication Module - Database Foundation

## 📋 MISSION
Create the **Communication** parent module and its database structure. This is the foundation for all communication features: Telegram, SMTP Email, Webhooks, API Keys, and WebSockets.

## 🎯 WHAT YOU NEED TO BUILD

### 1. Database Schema Changes

You need to create a SQL migration script that:

1. **Creates Communication parent module**
2. **Creates 5 child modules** under Communication
3. **Updates existing Telegram module** to be under Communication parent

### 2. SQL Migration Script

Create file: `backend/migrations/007_communication_module.sql`

```sql
-- ============================================================================
-- Migration 007: Communication Module Foundation
-- ============================================================================
-- Description: Creates Communication parent module and child modules
-- Author: System
-- Date: 2025-11-22
-- ============================================================================

-- Step 1: Create Communication parent module
INSERT INTO modules (module_key, name, description, icon, route_path, is_active, display_order, parent_module_id)
VALUES (
    'communication',
    'Communication',
    'Manage all communication channels: Email, Telegram, Webhooks, API Keys, and Real-time notifications',
    'Communication',
    '/communication',
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
    INSERT INTO modules (module_key, name, description, icon, route_path, is_active, display_order, parent_module_id)
    VALUES (
        'com_smtp',
        'Email (SMTP)',
        'Configure SMTP email settings, manage email templates, and send notifications',
        'Email',
        '/communication/smtp',
        true,
        2,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create Webhooks child module
    INSERT INTO modules (module_key, name, description, icon, route_path, is_active, display_order, parent_module_id)
    VALUES (
        'com_webhooks',
        'Webhooks',
        'Manage outgoing webhooks for event-driven integrations',
        'Webhook',
        '/communication/webhooks',
        true,
        3,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create API Keys child module
    INSERT INTO modules (module_key, name, description, icon, route_path, is_active, display_order, parent_module_id)
    VALUES (
        'com_api_keys',
        'API Keys',
        'Manage API keys for programmatic access and automation',
        'VpnKey',
        '/communication/api-keys',
        true,
        4,
        comm_module_id
    ) ON CONFLICT (module_key) DO NOTHING;

    -- Create WebSockets child module
    INSERT INTO modules (module_key, name, description, icon, route_path, is_active, display_order, parent_module_id)
    VALUES (
        'com_websockets',
        'Real-time (WebSocket)',
        'Configure real-time notifications and live updates',
        'Notifications',
        '/communication/websockets',
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
    FOR admin_user IN SELECT user_id FROM user_profiles WHERE role_id = admin_role_id
    LOOP
        -- Communication parent
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.user_id, comm_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- SMTP
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.user_id, smtp_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- Webhooks
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.user_id, webhooks_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- API Keys
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.user_id, api_keys_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;

        -- WebSockets
        INSERT INTO user_module_permissions (user_id, module_id)
        VALUES (admin_user.user_id, websockets_module_id)
        ON CONFLICT (user_id, module_id) DO NOTHING;
    END LOOP;

    RAISE NOTICE 'Admin permissions granted for Communication modules';
END $$;

-- Step 4: Verify the migration
SELECT
    m.id,
    m.module_key,
    m.name,
    CASE WHEN m.parent_module_id IS NULL THEN 'Parent' ELSE 'Child' END as type,
    p.name as parent_name,
    m.display_order,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key LIKE 'com%' OR m.module_key = 'communication'
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;
```

## 🚀 DEPLOYMENT STEPS

### Step 1: Create Migration File

```bash
# Create migrations directory if it doesn't exist
mkdir -p backend/migrations

# Create the migration file
cat > backend/migrations/007_communication_module.sql << 'EOF'
[paste the SQL above]
EOF
```

### Step 2: Run Migration in Supabase

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Copy the entire SQL script above
4. Paste into SQL Editor
5. Click "Run"
6. Check for success messages

### Step 3: Verify Migration

Run this verification query:

```sql
-- Verify Communication module structure
SELECT
    m.id,
    m.module_key,
    m.name,
    CASE WHEN m.parent_module_id IS NULL THEN 'Parent' ELSE 'Child' END as type,
    p.name as parent_name,
    m.display_order,
    m.is_active,
    (SELECT COUNT(*) FROM user_module_permissions WHERE module_id = m.id) as users_with_access
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key LIKE 'com%' OR m.module_key = 'communication'
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;
```

Expected output:
```
communication | Communication | Parent | - | 50 | true | [admin_count]
com_telegram | Email (Telegram) | Child | Communication | 1 | true | [admin_count]
com_smtp | Email (SMTP) | Child | Communication | 2 | true | [admin_count]
com_webhooks | Webhooks | Child | Communication | 3 | true | [admin_count]
com_api_keys | API Keys | Child | Communication | 4 | true | [admin_count]
com_websockets | Real-time (WebSocket) | Child | Communication | 5 | true | [admin_count]
```

## ✅ VERIFICATION CHECKLIST

After running the migration, verify:

- [ ] Communication parent module exists in `modules` table
- [ ] 5 child modules exist: `com_telegram`, `com_smtp`, `com_webhooks`, `com_api_keys`, `com_websockets`
- [ ] Old `telegram` module has been renamed to `com_telegram`
- [ ] `com_telegram` has `parent_module_id` pointing to Communication
- [ ] All admin users have permissions for all Communication modules
- [ ] No errors in migration output
- [ ] Verification query shows correct structure

## 📊 EXPECTED DATABASE STATE

After this migration, your `modules` table should include:

| module_key | name | parent | display_order |
|------------|------|--------|---------------|
| communication | Communication | NULL | 50 |
| com_telegram | Email (Telegram) | communication | 1 |
| com_smtp | Email (SMTP) | communication | 2 |
| com_webhooks | Webhooks | communication | 3 |
| com_api_keys | API Keys | communication | 4 |
| com_websockets | Real-time (WebSocket) | communication | 5 |

## 🐛 TROUBLESHOOTING

### Issue: "telegram module not found"
**Solution:** The migration handles this gracefully. If telegram module doesn't exist, it will skip the update.

### Issue: "duplicate key value violates unique constraint"
**Solution:** Modules already exist. Safe to ignore or use `ON CONFLICT DO NOTHING`.

### Issue: "No admin users found"
**Solution:** Run this to manually grant permissions:
```sql
INSERT INTO user_module_permissions (user_id, module_id)
SELECT up.user_id, m.id
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
AND m.module_key IN ('communication', 'com_telegram', 'com_smtp', 'com_webhooks', 'com_api_keys', 'com_websockets')
ON CONFLICT DO NOTHING;
```

## 📝 COMMIT MESSAGE

After verifying the migration works:

```bash
git add backend/migrations/007_communication_module.sql
git commit -m "feat: Add Communication parent module with 5 child modules

- Create Communication parent module
- Create child modules: SMTP, Webhooks, API Keys, WebSockets
- Migrate Telegram module under Communication parent (com_telegram)
- Grant admin permissions for all Communication modules
- Migration script: 007_communication_module.sql"
```

## 🎯 SUCCESS CRITERIA

This handover is complete when:

1. ✅ Migration file created at `backend/migrations/007_communication_module.sql`
2. ✅ Migration executed successfully in Supabase
3. ✅ Verification query returns expected structure
4. ✅ All admin users have access to Communication modules
5. ✅ Changes committed to git

## 📋 NEXT STEPS

After completing this handover, the database foundation is ready for:
- **Handover #2:** Advanced Settings & Configuration Management
- **Handover #3:** SMTP Email Service
- **Handover #4:** Webhook System
- **Handover #5:** API Key Management
- **Handover #6:** WebSocket Real-time System

---

**IMPORTANT:** Share the migration output with the main chat so we can verify success before proceeding to the next handover.
