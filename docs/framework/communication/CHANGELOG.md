# Communication Module - Changelog

All notable changes to the Communication Module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2025-11-22

### Fixed

#### Telegram Module Migration Correction

**Issue:**
The original migration (v1.0.0) incorrectly moved the old inactive `telegram` module (id: 54) under Communication instead of the active `admin_telegram` module (id: 61).

**Root Cause:**
Migration script targeted `telegram` module key instead of `admin_telegram` module key.

**Resolution:**
- Created patch migration file: `007_communication_module_patch.sql`
- Renamed old telegram module (id: 54) to `telegram_legacy`
- Moved correct `admin_telegram` module (id: 61) under Communication as `com_telegram`
- Preserved all module IDs and user permissions

**Result After Patch:**
- ✅ `com_telegram` (id: 61) - Active telegram module under Communication
- ✅ `telegram_legacy` (id: 54) - Old inactive module, standalone
- ✅ All permissions maintained
- ✅ No data loss

**Files Changed:**
- Added: `backend/migrations/007_communication_module_patch.sql`
- Updated: Documentation to reflect corrected module IDs

**Impact:**
- No breaking changes
- Existing permissions preserved
- Corrects module hierarchy to intended state

**Testing:**
- ✅ Patch successfully applied in production
- ✅ Verification query confirms correct structure
- ✅ All Communication modules functional

---

## [1.0.0] - 2025-11-22

### Added

#### Database Structure
- **Communication Parent Module**
  - New parent module with `module_key = 'communication'`
  - Module name: "Communication"
  - Description: "Manage all communication channels: Email, Telegram, Webhooks, API Keys, and Real-time notifications"
  - Icon: 📡 (broadcast satellite emoji)
  - Display order: 50
  - Status: Active by default

- **SMTP Email Child Module (`com_smtp`)**
  - Module key: `com_smtp`
  - Module name: "Email (SMTP)"
  - Description: "Configure SMTP email settings, manage email templates, and send notifications"
  - Icon: 📧 (email emoji)
  - Display order: 2
  - Parent: Communication module
  - Status: Active

- **Webhooks Child Module (`com_webhooks`)**
  - Module key: `com_webhooks`
  - Module name: "Webhooks"
  - Description: "Manage outgoing webhooks for event-driven integrations"
  - Icon: 🔗 (link emoji)
  - Display order: 3
  - Parent: Communication module
  - Status: Active

- **API Keys Child Module (`com_api_keys`)**
  - Module key: `com_api_keys`
  - Module name: "API Keys"
  - Description: "Manage API keys for programmatic access and automation"
  - Icon: 🔑 (key emoji)
  - Display order: 4
  - Parent: Communication module
  - Status: Active

- **WebSockets Child Module (`com_websockets`)**
  - Module key: `com_websockets`
  - Module name: "Real-time (WebSocket)"
  - Description: "Configure real-time notifications and live updates"
  - Icon: 🔔 (bell emoji)
  - Display order: 5
  - Parent: Communication module
  - Status: Active

#### Permissions
- Auto-grant permissions for all Communication modules to Admin users
- Permission entries created in `user_module_permissions` table
- Conflict-safe permission grants using `ON CONFLICT DO NOTHING`

#### Migration Files
- `backend/migrations/007_communication_module.sql`
  - Complete migration script with transaction safety
  - Includes verification query
  - Contains rollback documentation
  - Uses PL/pgSQL for complex operations

#### Documentation
- `docs/framework/communication/README.md` - Comprehensive module documentation
- `docs/framework/communication/VERSION_HISTORY.md` - Version tracking
- `docs/framework/communication/CHANGELOG.md` - Detailed change log

### Changed

#### Telegram Module Migration
- **Module Key:** `telegram` → `com_telegram`
- **Parent Module:** `NULL` → Communication module ID
- **Display Order:** Updated to `1` (first child under Communication)
- **Status:** Preserved previous state (inactive in production)
- **Permissions:** All existing permissions preserved and migrated

### Fixed

#### Schema Compatibility Issues

**Fix 1: Column Name Correction (Commit: 04072ed)**
- **Issue:** Migration used column name `name` but actual schema uses `module_name`
- **Fix:** Updated all INSERT statements to use `module_name`
- **Impact:** All module creation statements
- **Files Changed:** `007_communication_module.sql`

**Fix 2: Route Path Column Removed (Commit: 04072ed)**
- **Issue:** Migration included `route_path` column not present in current schema
- **Fix:** Removed `route_path` from all INSERT statements
- **Impact:** Simplified module creation to match actual schema
- **Files Changed:** `007_communication_module.sql`

**Fix 3: User Profiles Column Correction (Commit: fce6250)**
- **Issue:** Query referenced `user_id` column but schema uses `id`
- **Fix:** Changed `SELECT user_id FROM user_profiles` to `SELECT id FROM user_profiles`
- **Fix:** Updated all references from `admin_user.user_id` to `admin_user.id`
- **Impact:** Permission grant block (Step 3 in migration)
- **Files Changed:** `007_communication_module.sql`

**Fix 4: Icon Values Updated (Commit: 04072ed)**
- **Issue:** Used text icon names like "Email", "Webhook", "VpnKey", "Notifications"
- **Fix:** Changed to emoji icons for better UI consistency
- **Icons Updated:**
  - Communication: "Communication" → "📡"
  - SMTP: "Email" → "📧"
  - Webhooks: "Webhook" → "🔗"
  - API Keys: "VpnKey" → "🔑"
  - WebSockets: "Notifications" → "🔔"

### Security

- **Permission Safety:** Uses `ON CONFLICT DO NOTHING` to prevent duplicate permissions
- **Transaction Safety:** All operations wrapped in PL/pgSQL blocks with error handling
- **SQL Injection Prevention:** No dynamic SQL, all values are parameterized
- **Idempotency:** Migration can be run multiple times safely

### Database Impact

#### Tables Modified
- **`modules`**
  - Rows Inserted: 5 (1 parent + 4 children)
  - Rows Updated: 1 (telegram module)
  - Total Communication Modules: 6

- **`user_module_permissions`**
  - Rows Inserted: Varies (Admin users × 6 modules)
  - Example: If 3 admin users exist, 18 permission rows created

#### Performance Impact
- **Execution Time:** < 1 second (typical)
- **Lock Duration:** Minimal (uses row-level locks)
- **Index Impact:** None (no new indexes required)

### Testing

#### Test Environment
- **Database:** Supabase (Production)
- **Date:** 2025-11-22
- **Tested By:** Farm2 Development Team

#### Test Results
- ✅ Migration execution successful
- ✅ All 6 modules created correctly
- ✅ Parent-child relationships established
- ✅ Telegram module successfully migrated
- ✅ Admin permissions granted
- ✅ Verification query returns expected structure
- ✅ No errors or warnings
- ✅ Database integrity maintained

#### Test Data
**Modules Created (Production IDs):**
- Communication (ID: 67)
- com_telegram (ID: 54) - migrated
- com_smtp (ID: 68)
- com_webhooks (ID: 69)
- com_api_keys (ID: 70)
- com_websockets (ID: 71)

### Git History

```
fce6250 - fix: Correct user_profiles column from user_id to id
04072ed - fix: Update Communication module migration to match actual table schema
8003cad - feat: Add Communication parent module database migration
```

### Migration Execution Log

**Step 1: Create Communication parent module**
- Status: ✅ Success
- Notice: Communication module created with key 'communication'

**Step 2: Get Communication module ID & Create child modules**
- Status: ✅ Success
- Notice: "Communication module structure created successfully"
- Telegram module migrated: ✅
- SMTP module created: ✅
- Webhooks module created: ✅
- API Keys module created: ✅
- WebSockets module created: ✅

**Step 3: Grant admin permissions**
- Status: ✅ Success
- Notice: "Admin permissions granted for Communication modules"
- Admin users identified: Based on role 'Admin'
- Permissions created: 6 modules × N admin users

**Step 4: Verification**
- Status: ✅ Success
- Query returned: 6 modules (1 parent + 5 children)
- Structure validated: All parent-child relationships correct

### Known Issues

None identified in version 1.0.0.

### Deprecations

- **Legacy Telegram Module Key:** The module key `telegram` is deprecated
  - **Replaced By:** `com_telegram`
  - **Removal Timeline:** Not applicable (automatically migrated)
  - **Action Required:** Update frontend references from `telegram` to `com_telegram`

### Removed

None - this is the initial release.

### Backwards Compatibility

#### Breaking Changes
- **Telegram Module Key Changed**
  - **Old:** `telegram`
  - **New:** `com_telegram`
  - **Impact:** Frontend code referencing module key needs update
  - **Migration:** Automatic at database level
  - **User Impact:** None (permissions preserved)

#### Compatible Changes
- All new modules are additive
- No existing functionality removed
- Telegram module permissions preserved
- Database queries remain compatible

### Upgrade Notes

#### From: No Communication Module
**To:** Version 1.0.0

**Steps:**
1. Run migration script `007_communication_module.sql`
2. Verify modules created with verification query
3. Update frontend code to use new module keys
4. Update routing to reflect new module structure
5. Test admin user access to all Communication modules

**Estimated Time:** 5-10 minutes

**Rollback Available:** Yes (see README.md)

### Contributors

- **Developer:** Claude AI
- **Reviewer:** Farm2 Development Team
- **Tester:** Farm2 Development Team
- **Documentation:** Claude AI

### Related Issues

- Handover #1: Communication Module - Database Foundation ✅
- Handover #2: Advanced Settings (Planned)
- Handover #3: SMTP Email Service (Planned)
- Handover #4: Webhook System (Planned)
- Handover #5: API Key Management (Planned)
- Handover #6: WebSocket Real-time System (Planned)

### References

- Migration Script: `backend/migrations/007_communication_module.sql`
- Documentation: `docs/framework/communication/README.md`
- Version History: `docs/framework/communication/VERSION_HISTORY.md`

---

## [Unreleased]

### Planned for Version 1.1.0
- Advanced settings framework
- Configuration management system
- Module-level settings

### Planned for Version 1.2.0
- SMTP email backend implementation
- Email template system
- Email sending functionality

### Planned for Version 1.3.0
- Webhook management system
- Event trigger framework
- Webhook delivery tracking

### Planned for Version 1.4.0
- API key generation system
- Permission scoping
- Usage analytics

### Planned for Version 1.5.0
- WebSocket server implementation
- Real-time event system
- Connection management

---

**Changelog Version:** 1.0.0
**Last Updated:** 2025-11-22
**Format:** [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
