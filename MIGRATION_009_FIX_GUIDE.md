# Migration 009 Error Fix Guide

**Error:** `relation "idx_email_templates_key" already exists`

---

## 🔍 What Happened

You ran SQL from the wrong migration file. The error about `idx_email_templates_key` comes from the SMTP Email migration (HANDOVER_03), not the Telegram/Supabase settings migration.

---

## ✅ Solution: Run the Correct Migration

### Step 1: Check Current Database State

First, let's see what's already in your database:

```sql
-- Run this in Supabase SQL Editor:
-- File: backend/migrations/009_check_and_fix.sql
```

**Copy and paste the entire contents of `backend/migrations/009_check_and_fix.sql` into your Supabase SQL Editor and run it.**

This will show you:
- ✅ If system_settings table exists
- ✅ Which telegram/supabase settings already exist
- ⚠️ Which ones are missing

---

### Step 2: Run the Correct Migration

Based on the diagnostic results:

**If you see "No settings found" or "Partial settings found":**

```sql
-- Run this in Supabase SQL Editor:
-- File: backend/migrations/009_telegram_supabase_settings.sql
```

**Copy and paste the entire contents of `backend/migrations/009_telegram_supabase_settings.sql` into your Supabase SQL Editor and run it.**

**If you see "All 3 settings already exist":**
- ✅ Migration is already done!
- Skip to Step 3 (updating values)

---

### Step 3: Verify Migration Success

Run this query to confirm the settings are created:

```sql
SELECT
    setting_key,
    CASE
        WHEN is_encrypted THEN '***encrypted***'
        WHEN setting_value::text = '""' THEN '⚠️  EMPTY'
        ELSE '✅ HAS VALUE'
    END as status,
    category,
    created_at
FROM system_settings
WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
)
ORDER BY setting_key;
```

**Expected output:**
```
setting_key           | status         | category      | created_at
----------------------|----------------|---------------|-------------------
supabase_service_key  | ⚠️  EMPTY      | integrations  | 2025-11-23 ...
supabase_url          | ⚠️  EMPTY      | integrations  | 2025-11-23 ...
telegram_bot_token    | ⚠️  EMPTY      | telegram      | 2025-11-23 ...
```

✅ **Success!** The settings are created (they're empty, which is expected - you'll add values next)

---

## 📝 Next: Update the Values

Now that the settings exist in the database, you need to add your actual credentials.

### Option 1: Via Settings UI (Easiest)

1. Login to your app as admin
2. Go to Settings page
3. Find the Telegram/Integrations tabs
4. Edit each setting and paste your values:
   - `telegram_bot_token`: Your Telegram bot token
   - `supabase_url`: Your Supabase project URL
   - `supabase_service_key`: Your Supabase service key
5. Click Save for each

### Option 2: Via SQL (Quick)

```sql
-- Update Telegram Bot Token
UPDATE system_settings
SET setting_value = '"YOUR_ACTUAL_BOT_TOKEN_HERE"'::jsonb,
    updated_at = NOW()
WHERE setting_key = 'telegram_bot_token';

-- Update Supabase URL
UPDATE system_settings
SET setting_value = '"https://your-project.supabase.co"'::jsonb,
    updated_at = NOW()
WHERE setting_key = 'supabase_url';

-- Update Supabase Service Key
UPDATE system_settings
SET setting_value = '"YOUR_ACTUAL_SERVICE_KEY_HERE"'::jsonb,
    updated_at = NOW()
WHERE setting_key = 'supabase_service_key';
```

**⚠️ IMPORTANT:**
- The value must be wrapped in double quotes and cast to ::jsonb
- Don't forget the single quotes around the entire JSON value
- Format: `'"actual_value"'::jsonb`

### Option 3: Via API

See `/UPDATING_CREDENTIALS_GUIDE.md` for API method.

---

## 🧪 Test the Migration

After updating values:

1. **Restart your backend:**
   ```bash
   docker-compose restart backend
   ```

2. **Check logs:**
   ```bash
   docker-compose logs backend | grep "Setting.*loaded"
   ```

   **Expected output:**
   ```
   ✅ Setting 'telegram_bot_token' loaded from database (value length: 46 chars)
   ✅ Setting 'supabase_url' loaded from database (value length: 38 chars)
   ✅ Setting 'supabase_service_key' loaded from database (value length: 180 chars)
   ```

3. **Test functionality:**
   ```bash
   # Test Telegram
   curl -X POST http://localhost:8000/api/v1/telegram/test \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"channel_type": "tickets"}'
   ```

---

## 🔧 Troubleshooting

### Still seeing the idx_email_templates_key error?

**This error is harmless if you're not implementing the SMTP email feature yet.**

To fix it, run:

```sql
-- Check if the index already exists
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_email_templates_key';

-- If it exists and you see an error, you can safely ignore it
-- The index creation is idempotent - it won't break anything
```

### Migration 008 not run yet?

If the diagnostic script says "system_settings table does not exist", run this first:

```sql
-- Run: backend/migrations/008_system_settings.sql
-- This creates the system_settings table structure
```

Then come back and run migration 009.

---

## 📚 Summary

**What you should run (in order):**

1. ✅ `009_check_and_fix.sql` - Check database state
2. ✅ `009_telegram_supabase_settings.sql` - Add the settings (if needed)
3. ✅ Update values via Settings UI or SQL
4. ✅ Restart backend and check logs
5. ✅ Test Telegram and Supabase functionality

**Files created:**
- ✅ `backend/migrations/009_telegram_supabase_settings.sql` - Main migration
- ✅ `backend/migrations/009_check_and_fix.sql` - Diagnostic tool

---

## 🎯 Quick Command Reference

```bash
# 1. Open Supabase SQL Editor
# 2. Copy/paste: backend/migrations/009_check_and_fix.sql
# 3. Run it to see status
# 4. If needed, copy/paste: backend/migrations/009_telegram_supabase_settings.sql
# 5. Run it to create settings
# 6. Update values via Settings UI or SQL
# 7. Restart backend: docker-compose restart backend
# 8. Check logs: docker-compose logs backend | grep Setting
```

**Expected final state:**
- All 3 settings exist in database ✅
- All 3 have your actual credentials ✅
- Logs show "loaded from database" ✅
- Telegram test works ✅
- Supabase works ✅

---

Need help? Check: `/TESTING_FALLBACK_GUIDE.md` and `/UPDATING_CREDENTIALS_GUIDE.md`
