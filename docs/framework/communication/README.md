# Communication Module - Database Foundation

## Overview

The Communication module serves as the central hub for all communication-related features in the Farm2 application. It provides a unified parent module with five specialized child modules for different communication channels.

## Module Structure

```
Communication (Parent Module)
├── Telegram Notifications
├── Email (SMTP)
├── Webhooks
├── API Keys
└── Real-time (WebSocket)
```

## Database Schema

### Parent Module: Communication

| Field | Value |
|-------|-------|
| **module_key** | `communication` |
| **module_name** | Communication |
| **description** | Manage all communication channels: Email, Telegram, Webhooks, API Keys, and Real-time notifications |
| **icon** | 📡 |
| **display_order** | 50 |
| **is_active** | `true` |
| **parent_module_id** | `NULL` |

### Child Modules

#### 1. Telegram Notifications (`com_telegram`)

| Field | Value |
|-------|-------|
| **module_key** | `com_telegram` |
| **module_name** | Telegram Notifications |
| **description** | Send notifications via Telegram bot |
| **icon** | 📱 (existing icon) |
| **display_order** | 1 |
| **parent_module_id** | `communication` module ID |

**Migration Notes:**
- This module was migrated from the existing `admin_telegram` module
- Module key changed from `admin_telegram` to `com_telegram`
- All existing user permissions were preserved during migration
- **Note:** An initial migration error moved the wrong module; this was corrected via patch (v1.0.1)

#### 2. Email (SMTP) (`com_smtp`)

| Field | Value |
|-------|-------|
| **module_key** | `com_smtp` |
| **module_name** | Email (SMTP) |
| **description** | Configure SMTP email settings, manage email templates, and send notifications |
| **icon** | 📧 |
| **display_order** | 2 |
| **parent_module_id** | `communication` module ID |

**Purpose:**
- Configure SMTP server settings
- Create and manage email templates
- Send email notifications
- Track email delivery status

#### 3. Webhooks (`com_webhooks`)

| Field | Value |
|-------|-------|
| **module_key** | `com_webhooks` |
| **module_name** | Webhooks |
| **description** | Manage outgoing webhooks for event-driven integrations |
| **icon** | 🔗 |
| **display_order** | 3 |
| **parent_module_id** | `communication` module ID |

**Purpose:**
- Configure webhook endpoints
- Define event triggers
- Manage webhook payloads
- Monitor webhook delivery

#### 4. API Keys (`com_api_keys`)

| Field | Value |
|-------|-------|
| **module_key** | `com_api_keys` |
| **module_name** | API Keys |
| **description** | Manage API keys for programmatic access and automation |
| **icon** | 🔑 |
| **display_order** | 4 |
| **parent_module_id** | `communication` module ID |

**Purpose:**
- Generate API keys for external integrations
- Set key permissions and scopes
- Rotate and revoke API keys
- Track API key usage

#### 5. Real-time (WebSocket) (`com_websockets`)

| Field | Value |
|-------|-------|
| **module_key** | `com_websockets` |
| **module_name** | Real-time (WebSocket) |
| **description** | Configure real-time notifications and live updates |
| **icon** | 🔔 |
| **display_order** | 5 |
| **parent_module_id** | `communication` module ID |

**Purpose:**
- Configure WebSocket connections
- Manage real-time event subscriptions
- Push live updates to connected clients
- Monitor WebSocket connections

## Migration Details

### Migration File
- **File:** `backend/migrations/007_communication_module.sql`
- **Version:** 1.0.0
- **Date:** 2025-11-22

### What the Migration Does

1. **Creates Communication Parent Module**
   - Adds a new parent module with `module_key = 'communication'`
   - Sets appropriate metadata (name, description, icon, display order)

2. **Migrates Existing Telegram Module**
   - Renames `telegram` module to `com_telegram`
   - Sets `parent_module_id` to link it under Communication
   - Preserves all existing user permissions

3. **Creates Four New Child Modules**
   - SMTP Email (`com_smtp`)
   - Webhooks (`com_webhooks`)
   - API Keys (`com_api_keys`)
   - WebSockets (`com_websockets`)

4. **Grants Admin Permissions**
   - Automatically grants access to all Communication modules for Admin users
   - Uses the `roles` table to identify Admin role
   - Creates entries in `user_module_permissions` table

5. **Verification**
   - Includes a verification query to confirm successful migration
   - Returns all Communication-related modules with their structure

### Migration Patch (Version 1.0.1)

**Patch File:** `backend/migrations/007_communication_module_patch.sql`

**Issue Fixed:**
The original migration incorrectly moved the old inactive `telegram` module (id: 54) under Communication instead of the active `admin_telegram` module (id: 61).

**Patch Actions:**
1. Renamed the old inactive telegram module to `telegram_legacy`
2. Moved the active `admin_telegram` module under Communication as `com_telegram`
3. Preserved all module IDs and permissions

**Result:**
- ✅ `com_telegram` (id: 61) - Active telegram module under Communication
- ✅ `telegram_legacy` (id: 54) - Old inactive module, standalone

## Permissions Model

### Admin Users
All users with the `Admin` role automatically receive permissions for:
- Communication parent module
- All five child modules

### Custom Permissions
Future implementations can grant granular permissions:
- Access to specific child modules only
- Read-only vs. full access
- Per-module feature permissions

## Database Tables Affected

### `modules`
- **Inserted:** 1 parent module + 4 new child modules
- **Updated:** 1 module (telegram → com_telegram)

### `user_module_permissions`
- **Inserted:** Permissions for all Admin users × 6 modules
- **Conflict Resolution:** Uses `ON CONFLICT DO NOTHING` to prevent duplicates

## Testing & Verification

### Test Results (2025-11-22)

**Migration Execution:** ✅ Success

**Modules Created:**

| ID | Module Key | Module Name | Type | Parent | Active |
|----|------------|-------------|------|--------|--------|
| 67 | communication | Communication | Parent | NULL | ✅ |
| 61 | com_telegram | Telegram Notifications | Child | Communication | ✅ |
| 68 | com_smtp | Email (SMTP) | Child | Communication | ✅ |
| 69 | com_webhooks | Webhooks | Child | Communication | ✅ |
| 70 | com_api_keys | API Keys | Child | Communication | ✅ |
| 71 | com_websockets | Real-time (WebSocket) | Child | Communication | ✅ |
| 54 | telegram_legacy | Telegram Notifications | Standalone | NULL | ❌ |

**Notes:**
- **After Patch (v1.0.1):** Correct `admin_telegram` module (id: 61) moved under Communication
- `telegram_legacy` (id: 54) is the old inactive module, kept standalone for reference
- All communication modules are active except telegram_legacy

### Verification Query

```sql
SELECT
    m.id,
    m.module_key,
    m.module_name,
    CASE WHEN m.parent_module_id IS NULL THEN 'Parent' ELSE 'Child' END as type,
    p.module_name as parent_name,
    m.display_order,
    m.is_active,
    (SELECT COUNT(*) FROM user_module_permissions WHERE module_id = m.id) as users_with_access
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key LIKE 'com%' OR m.module_key = 'communication'
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;
```

## Schema Corrections Made

During implementation, the following schema corrections were made to match the actual database structure:

### Column Name Changes
- **`name`** → **`module_name`** (actual column in modules table)
- **Removed:** `route_path` column (not present in current schema)

### User Profiles Table
- **`user_id`** → **`id`** (actual column in user_profiles table)

These corrections were committed separately to ensure the migration script matches the production database schema.

## Implementation Timeline

| Date | Event | Status |
|------|-------|--------|
| 2025-11-22 | Migration script created | ✅ |
| 2025-11-22 | Schema corrections applied | ✅ |
| 2025-11-22 | Migration tested in Supabase | ✅ |
| 2025-11-22 | Documentation created | ✅ |

## Next Steps

### Immediate Next Steps
1. ✅ Database structure created
2. ⏭️ Implement frontend navigation (Handover #2)
3. ⏭️ Build SMTP configuration UI (Handover #3)
4. ⏭️ Develop Webhook management (Handover #4)
5. ⏭️ Create API Key management (Handover #5)
6. ⏭️ Implement WebSocket system (Handover #6)

### Future Enhancements
- Add module-level permissions granularity
- Implement audit logging for communication events
- Create unified communication dashboard
- Add communication analytics and reporting

## Rollback Procedure

If you need to rollback this migration:

```sql
-- WARNING: This will delete all Communication modules and their permissions
-- Backup your data before running this!

-- Step 1: Delete user permissions
DELETE FROM user_module_permissions
WHERE module_id IN (
    SELECT id FROM modules
    WHERE module_key IN ('communication', 'com_telegram', 'com_smtp', 'com_webhooks', 'com_api_keys', 'com_websockets')
);

-- Step 2: Restore original Telegram module (optional)
UPDATE modules
SET module_key = 'telegram', parent_module_id = NULL
WHERE module_key = 'com_telegram';

-- Step 3: Delete Communication modules
DELETE FROM modules
WHERE module_key IN ('communication', 'com_smtp', 'com_webhooks', 'com_api_keys', 'com_websockets');
```

## Support & Troubleshooting

### Common Issues

#### Issue: Telegram module is inactive
**Solution:** This is expected if the module was previously deactivated. To activate:
```sql
UPDATE modules SET is_active = true WHERE module_key = 'com_telegram';
```

#### Issue: Admin users don't have access
**Solution:** Run the permission grant section of the migration again:
```sql
-- Manually grant permissions (replace with actual module IDs)
INSERT INTO user_module_permissions (user_id, module_id)
SELECT up.id, m.id
FROM user_profiles up
CROSS JOIN modules m
WHERE up.role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
AND m.module_key IN ('communication', 'com_telegram', 'com_smtp', 'com_webhooks', 'com_api_keys', 'com_websockets')
ON CONFLICT DO NOTHING;
```

## References

- **Migration File:** `backend/migrations/007_communication_module.sql`
- **Handover Document:** Handover #1 - Communication Module Database Foundation
- **Related Modules:** Telegram Notifications (legacy), Inventory Management (parent module example)

## Contributors

- **Migration Author:** System
- **Documentation:** Claude AI
- **Testing:** Farm2 Development Team
- **Date:** 2025-11-22

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-22
**Status:** ✅ Completed & Tested
