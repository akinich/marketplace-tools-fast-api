# Database Migration Reference

**Last Updated:** 2025-11-23
**Current Schema Version:** v1.13.0

---

## 📋 Table of Contents

- [Overview](#overview)
- [Migration History](#migration-history)
- [Migration Status](#migration-status)
- [Migration Files](#migration-files)
- [Migration Dependencies](#migration-dependencies)
- [How to Run Migrations](#how-to-run-migrations)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This document provides a complete reference for all database migrations in the Marketplace ERP Tools. Each migration is tracked, documented, and includes rollback procedures.

### Migration Locations

- **Production Migrations**: `sql_scripts/v*.sql`
- **Backend Migrations**: `backend/migrations/*.sql`
- **Fix/Utility Scripts**: `sql_scripts/fix_*.sql`, `sql_scripts/verify_*.sql`

### Migration Strategy

- **Sequential Versioning**: Migrations are numbered (v1.0.0, v1.1.0, etc.)
- **Idempotent**: Can be run multiple times safely (use `IF NOT EXISTS`, `ON CONFLICT`, etc.)
- **Documented**: Each migration includes description, date, and rollback instructions
- **Tested**: All migrations tested on development before production

---

## 📊 Migration History

### Production Migrations (sql_scripts/)

| Version | File | Date | Description | Status |
|---------|------|------|-------------|--------|
| v1.0.0 | `v1.0.0_initial_schema.sql` | 2025-11-17 | Initial database schema | ✅ Applied |
| v1.1.0 | `v1.1.0_hierarchical_modules_and_user_creation.sql` | 2025-11-17 | Hierarchical modules and user creation | ✅ Applied |
| v1.1.1 | `v1.1.1_permission_view_fix.sql` | 2025-11-17 | Permission view fix | ✅ Applied |
| v1.1.2 | `v1.1.2_password_reset_tokens.sql` | 2025-11-17 | Password reset tokens | ✅ Applied |
| v1.2.0 | `v1.2.0_account_security.sql` | 2025-11-18 | Account security enhancements | ✅ Applied |
| v1.2.0 | `v1.2.0_stock_adjustments.sql` | 2025-11-18 | Stock adjustments table | ✅ Applied |
| v1.3.0 | `v1.3.0_inventory_enhancements_biofloc.sql` | 2025-11-19 | Inventory enhancements and biofloc | ✅ Applied |
| v1.3.0 | `v1.3.0_sessions_and_login_history.sql` | 2025-11-19 | Sessions and login history | ✅ Applied |
| v1.3.1 | `v1.3.1_fix_tank_id_uuid.sql` | 2025-11-19 | Fix tank ID UUID | ✅ Applied |
| v1.3.2 | `v1.3.2_fix_unconfirmed_users.sql` | 2025-11-19 | Fix unconfirmed users | ✅ Applied |
| v1.9.0 | `v1.9.0_item_master_updates.sql` | 2025-11-20 | Item master updates | ✅ Applied |
| v1.10.0 | `v1.10.0_po_enhancements.sql` | 2025-11-20 | Purchase order enhancements | ✅ Applied |
| v1.11.0 | `v1.11.0_unit_of_measurements.sql` | 2025-11-22 | Unit of measurements system | ✅ Applied |
| v1.12.0 | `v1.12.0_admin_submodules.sql` | 2025-11-22 | Admin sub-modules | ✅ Applied |

### Backend Migrations (backend/migrations/)

| Migration | File | Date | Description | Status |
|-----------|------|------|-------------|--------|
| 007 | `007_communication_module.sql` | 2025-11-22 | Communication parent module | ✅ Applied |
| 007 | `007_communication_module_patch.sql` | 2025-11-22 | Communication module patch | ✅ Applied |
| 008 | `008_system_settings.sql` | 2025-11-22 | System settings infrastructure | ✅ Applied |
| 009 | `009_telegram_supabase_settings.sql` | 2025-11-23 | Telegram & Supabase settings migration | ✅ Applied |
| 009 | `009_check_and_fix.sql` | 2025-11-23 | Migration 009 diagnostic script | 🔧 Utility |

### Module-Specific Migrations (backend/migrations/)

| Module | File | Date | Description | Status |
|--------|------|------|-------------|--------|
| Biofloc | `biofloc_module_v1.0.0.sql` | 2025-11-17 | Biofloc module initial | ✅ Applied |
| Biofloc | `biofloc_grading_v1.0.1.sql` | 2025-11-18 | Biofloc grading feature | ✅ Applied |
| Biofloc | `biofloc_cleanup.sql` | 2025-11-19 | Biofloc cleanup | 🔧 Utility |
| Tickets | `tickets_module_v1.0.0.sql` | 2025-11-17 | Tickets module initial | ✅ Applied |
| Development | `development_module_v1.0.0.sql` | 2025-11-17 | Development module | ✅ Applied |
| Telegram | `telegram_notifications_v1.0.0.sql` | 2025-11-17 | Telegram notifications | ✅ Applied |
| Telegram | `telegram_notifications_v1.0.1_patch.sql` | 2025-11-17 | Telegram patch | ✅ Applied |
| Telegram | `telegram_notifications_v1.1.0_granular_settings.sql` | 2025-11-18 | Granular settings | ✅ Applied |

### Utility Scripts (sql_scripts/)

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `fix_admin_submodules_order.sql` | Fix admin sub-modules display order | Fix | 🔧 Available |
| `fix_batch_quantities_after_adjustments.sql` | Reconcile batch quantities | Fix | 🔧 Available |
| `remove_duplicate_telegram_module.sql` | Remove duplicate telegram module | Fix | 🔧 Available |
| `safe_remove_duplicate_telegram.sql` | Safe removal of duplicate telegram | Fix | 🔧 Available |
| `verify_and_fix_permissions.sql` | Verify and fix permissions | Verification | 🔧 Available |
| `verify_password_reset_setup.sql` | Verify password reset setup | Verification | 🔧 Available |

---

## ✅ Migration Status

### Currently Applied (v1.13.0)

**Core Schema:**
- ✅ Initial schema (users, roles, modules, permissions, activity logs)
- ✅ Hierarchical module system with parent-child relationships
- ✅ Session management and login history
- ✅ Password reset tokens

**Inventory Module:**
- ✅ Inventory categories, suppliers, items
- ✅ Inventory batches with FIFO tracking
- ✅ Inventory transactions and audit trail
- ✅ Purchase orders with multi-item support
- ✅ Stock adjustments with reason tracking
- ✅ Unit of measurements system

**Biofloc Module:**
- ✅ Tank management
- ✅ Water quality testing
- ✅ Growth records and grading
- ✅ Feed logs

**Communication Module:**
- ✅ Communication parent module
- ✅ Telegram notifications module (sub-module)

**Settings Management:**
- ✅ System settings table with JSONB storage
- ✅ Settings audit log
- ✅ Migrated settings: telegram_bot_token, supabase_url, supabase_service_key

**Admin Module:**
- ✅ Admin sub-modules (Users, Modules, Activity, Security, Units, Telegram)

### Pending Migrations

**None currently pending** - All migrations up to v1.13.0 have been applied.

### Planned Future Migrations

**v1.14.0+ (Framework Features):**
- 🔜 SMTP Email service tables (email_templates, email_queue, email_recipients, email_send_log)
- 🔜 Webhook system tables (webhooks, webhook_deliveries)
- 🔜 API key management tables (api_keys, api_key_usage)
- 🔜 WebSocket infrastructure

**See:** `framework/HANDOVER_*.md` for detailed implementation plans

---

## 📦 Migration Files

### v1.13.0 - Settings & Configuration Management

**Migration 008: System Settings Infrastructure**

**File:** `backend/migrations/008_system_settings.sql`
**Date:** 2025-11-22
**Prerequisites:** None
**Size:** ~5.6 KB

**Tables Created:**
- `system_settings` - Main settings table
  - Columns: setting_key (PK), setting_value (JSONB), data_type, category, description, is_encrypted, is_public, validation_rules, created_at, updated_at, updated_by
- `settings_audit_log` - Audit trail for setting changes
  - Columns: id, setting_key, old_value, new_value, changed_by, changed_at

**Indexes:**
- `idx_system_settings_category` on `system_settings(category)`
- `idx_settings_audit_log_key` on `settings_audit_log(setting_key)`
- `idx_settings_audit_log_changed_by` on `settings_audit_log(changed_by)`

**Rollback:**
```sql
DROP TABLE IF EXISTS settings_audit_log;
DROP TABLE IF EXISTS system_settings;
```

---

**Migration 009: Telegram & Supabase Settings**

**File:** `backend/migrations/009_telegram_supabase_settings.sql`
**Date:** 2025-11-23
**Prerequisites:** Migration 008
**Size:** ~3.2 KB

**Settings Added:**
- `telegram_bot_token` (category: telegram, type: string)
- `supabase_url` (category: integrations, type: string)
- `supabase_service_key` (category: integrations, type: string, encrypted: true)

**Validation Rules:**
- `telegram_bot_token`: min_length 30
- `supabase_url`: pattern `^https://.*\.supabase\.co$`
- `supabase_service_key`: min_length 100

**Rollback:**
```sql
DELETE FROM system_settings WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
);
```

---

### v1.12.0 - Admin Sub-Modules

**File:** `sql_scripts/v1.12.0_admin_submodules.sql`
**Date:** 2025-11-22

**Modules Added:**
- `admin_users` - User Management sub-module
- `admin_modules` - Module Management sub-module
- `admin_activity` - Activity Logs sub-module
- `admin_security` - Security Dashboard sub-module
- `admin_units` - Units of Measurement sub-module
- `admin_telegram` - Telegram Settings sub-module

**Rollback:**
```sql
DELETE FROM modules WHERE module_key LIKE 'admin_%';
```

---

### v1.11.0 - Unit of Measurements

**File:** `sql_scripts/v1.11.0_unit_of_measurements.sql`
**Date:** 2025-11-22

**Tables Created:**
- `unit_of_measurements` - Standardized units

**Data Inserted:**
- 25 pre-populated units across 5 categories (weight, volume, count, length, area)

**Rollback:**
```sql
DROP TABLE IF EXISTS unit_of_measurements;
```

---

## 🔗 Migration Dependencies

```
v1.0.0 (Initial Schema)
  │
  ├─ v1.1.0 (Hierarchical Modules)
  │   │
  │   ├─ v1.1.1 (Permission View Fix)
  │   │
  │   └─ v1.1.2 (Password Reset)
  │
  ├─ v1.2.0 (Account Security + Stock Adjustments)
  │
  ├─ v1.3.0 (Inventory + Biofloc + Sessions)
  │   │
  │   ├─ v1.3.1 (Fix Tank ID)
  │   │
  │   └─ v1.3.2 (Fix Unconfirmed Users)
  │
  ├─ v1.9.0 (Item Master Updates)
  │
  ├─ v1.10.0 (PO Enhancements)
  │
  ├─ v1.11.0 (Units of Measurement)
  │
  ├─ v1.12.0 (Admin Sub-Modules)
  │
  └─ Migration 007 (Communication Module)
      │
      └─ Migration 008 (System Settings)
          │
          └─ Migration 009 (Telegram & Supabase Settings) ← CURRENT
```

---

## 🚀 How to Run Migrations

### Method 1: Supabase SQL Editor (Recommended)

1. **Login to Supabase Dashboard**
   - Go to https://app.supabase.com
   - Select your project

2. **Open SQL Editor**
   - Click "SQL Editor" in left sidebar
   - Click "New Query"

3. **Copy Migration File**
   - Open migration file from `sql_scripts/` or `backend/migrations/`
   - Copy entire contents

4. **Paste and Execute**
   - Paste into SQL Editor
   - Click "Run" or press Ctrl/Cmd + Enter
   - Wait for completion

5. **Verify Results**
   - Check for "Success" message
   - Review any output
   - Verify tables in Table Editor

### Method 2: psql Command Line

```bash
# Connect to database
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"

# Run migration file
\i sql_scripts/v1.13.0_migration.sql

# Verify
\dt system_settings
```

### Method 3: Database Client (pgAdmin, DBeaver, etc.)

1. Connect to your Supabase database
2. Open SQL console
3. Load migration file
4. Execute
5. Verify results

---

## ↩️ Rollback Procedures

### General Rollback Strategy

Each migration includes rollback instructions. General process:

1. **Backup First**
   ```sql
   -- Create backup of affected tables
   CREATE TABLE system_settings_backup AS SELECT * FROM system_settings;
   ```

2. **Execute Rollback SQL**
   - See migration file for specific rollback commands
   - Usually involves `DROP TABLE` or `DELETE FROM`

3. **Verify**
   - Check tables are removed/restored
   - Verify data integrity
   - Test application

### Specific Rollbacks

**Rollback Migration 009:**
```sql
DELETE FROM system_settings WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
);
```

**Rollback Migration 008:**
```sql
DROP TABLE IF EXISTS settings_audit_log;
DROP TABLE IF EXISTS system_settings;
```

**Rollback Admin Sub-Modules:**
```sql
DELETE FROM modules WHERE module_key LIKE 'admin_%';
```

**Rollback Units of Measurement:**
```sql
DROP TABLE IF EXISTS unit_of_measurements;
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue: "relation already exists"**
- **Cause:** Migration already run or table created manually
- **Solution:** Check if migration was already applied
  ```sql
  SELECT tablename FROM pg_tables WHERE tablename = 'system_settings';
  ```
- If table exists, skip migration or use `IF NOT EXISTS` syntax

**Issue: "column does not exist"**
- **Cause:** Previous migration not run or failed
- **Solution:** Check migration dependencies and run prerequisite migrations

**Issue: "permission denied"**
- **Cause:** Using wrong user or insufficient privileges
- **Solution:** Use Supabase SQL Editor (has proper permissions) or postgres superuser

**Issue: Migration runs but no output**
- **Cause:** Migration uses `ON CONFLICT DO NOTHING` and data already exists
- **Solution:** This is normal - verify data exists:
  ```sql
  SELECT * FROM system_settings;
  ```

### Verification Queries

**Check All Tables:**
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Check System Settings:**
```sql
SELECT setting_key, category, is_encrypted, created_at
FROM system_settings
ORDER BY category, setting_key;
```

**Check Audit Log:**
```sql
SELECT setting_key, changed_by, changed_at
FROM settings_audit_log
ORDER BY changed_at DESC
LIMIT 10;
```

**Check Module Structure:**
```sql
SELECT m.module_key, m.module_name, p.module_key as parent
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
ORDER BY p.module_key NULLS FIRST, m.display_order;
```

---

## 📚 Related Documentation

- [CHANGELOG.md](../CHANGELOG.md) - Complete application changelog
- [README.md](../README.md) - Main project documentation
- [Settings Module Version History](SETTINGS_MODULE_VERSION_HISTORY.md) - Detailed settings module history
- [Migration Guide: Environment to Database](MIGRATION_GUIDE_ENV_TO_DATABASE.md) - Settings migration guide
- [Migration 009 Fix Guide](../MIGRATION_009_FIX_GUIDE.md) - Troubleshooting Migration 009

---

## 📞 Support

For migration issues:
1. Check this reference document
2. Review migration file comments
3. Check troubleshooting section
4. Review logs and error messages
5. Create issue in project repository

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-23
**Maintained By:** Development Team
