# Add Missing Modules to Production

## Problem
Your admin account can't see these modules:
- ❌ Module Management (admin sub-module)
- ❌ Units of Measurement (admin sub-module)
- ❌ Documentation (top-level module)
- ❌ Telegram (under Communication)
- ❌ And possibly others

## Cause
These modules were never added to your production database's `modules` table. The migrations that create them weren't run.

## Solution
Run the SQL script that adds all missing modules.

---

## How to Fix (5 minutes)

### Option 1: Via Supabase SQL Editor (Recommended)

1. **Open Supabase Dashboard**
   - Go to your Supabase project
   - Click on "SQL Editor" in the left sidebar

2. **Run the migration**
   - Click "New Query"
   - Copy the entire contents of `sql_scripts/add_missing_modules.sql`
   - Paste into the editor
   - Click "Run" (or press Cmd/Ctrl + Enter)

3. **Verify**
   - You should see a table showing all modules
   - Look for the new modules in the output

4. **Restart backend**
   - Restart your backend service (if auto-deploy is off)
   - Or wait for auto-deploy to pick up changes

5. **Test**
   - Log in as admin
   - You should now see all modules!

### Option 2: Via psql Command Line

If you have direct database access:

```bash
psql YOUR_DATABASE_URL -f sql_scripts/add_missing_modules.sql
```

---

## What Gets Added

### Admin Sub-Modules (6 modules)
- **User Management** - Manage users, roles, permissions
- **Module Management** - Enable/disable modules ← YOU WERE MISSING THIS
- **Activity Logs** - View system activity
- **Security Dashboard** - Sessions and login history
- **Units of Measurement** - Manage measurement units ← YOU WERE MISSING THIS
- **Settings** - System configuration

### Communication Module (1 parent + 5 sub-modules)
- **Communication** (parent)
  - **Telegram Notifications** ← YOU WERE MISSING THIS
  - **Email (SMTP)** - Email settings
  - **Webhooks** - Webhook management
  - **API Keys** - API key management
  - **Real-time (WebSocket)** - Real-time notifications

### Documentation Module (1 module)
- **Documentation** - System docs and guides ← YOU WERE MISSING THIS

**Total: 13 new modules**

---

## After Running

### What Happens Automatically
✅ All modules are added to the database
✅ Admin users automatically get access (no manual permissions needed)
✅ Regular users need explicit permissions (as designed)

### What You Need to Do
1. Restart backend service (if not auto-deployed)
2. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Log in and check - all modules should appear!

---

## Verification

After running the script, you should see output like this:

```
module_key          | module_name              | type               | display_order | is_active
--------------------+--------------------------+--------------------+---------------+-----------
admin              | Administration           | Parent Module      | 1             | t
admin_users        | User Management          | Administration > Sub-module | 1    | t
admin_modules      | Module Management        | Administration > Sub-module | 2    | t
admin_units        | Units of Measurement     | Administration > Sub-module | 5    | t
communication      | Communication            | Parent Module      | 50            | t
com_telegram       | Telegram Notifications   | Communication > Sub-module  | 1    | t
docs               | Documentation            | Parent Module      | 90            | t
...
```

---

## Troubleshooting

### "Admin module not found" error
- Your database is missing the base `admin` module
- Run `sql_scripts/v1.0.0_initial_schema.sql` first
- Then run `add_missing_modules.sql`

### Still don't see modules after running
1. Check if the script ran successfully (no errors)
2. Restart your backend service
3. Hard refresh browser (Ctrl+Shift+R)
4. Check browser console for errors
5. Verify you're logged in as Admin role

### Modules appear but are empty
- Some modules may need additional migrations
- Check `backend/migrations/` for module-specific migrations
- Run them in order (e.g., `telegram_notifications_v1.0.0.sql`)

---

## Files

- **Migration Script**: `sql_scripts/add_missing_modules.sql`
- **This Guide**: `ADD_MISSING_MODULES.md`

---

**Created**: 2025-11-27
**Issue**: Admin can't see Module Management, Units, Docs, Telegram modules
**Fix**: Run add_missing_modules.sql on production database
