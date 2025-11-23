# Guide: Updating Credentials for Primary Database Use

**Date:** 2025-11-23
**Purpose:** Move credentials from .env to database for primary use

---

## 🎯 Overview

This guide shows you how to migrate your credentials from environment variables to the database, making the database the primary source and .env only a fallback.

---

## 📋 Option 1: Using the Settings UI (Recommended)

This is the easiest and safest method for production use.

### Steps:

1. **Login to your application** with admin credentials

2. **Navigate to Settings page**:
   - Click **"Settings"** in the sidebar menu
   - You should see the Settings page with multiple tabs

3. **Update Telegram Settings**:
   - Go to the **"Telegram"** or **"Integrations"** tab
   - Find **"telegram_bot_token"** setting
   - Click **Edit** or toggle edit mode
   - Paste your bot token: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Click **Save**
   - ✅ You should see a success message

4. **Update Supabase Settings**:
   - In the **"Integrations"** tab
   - Find **"supabase_url"**
   - Edit and enter: `https://your-project.supabase.co`
   - Save
   - Find **"supabase_service_key"**
   - Edit and enter your service key
   - Save

5. **Verify in Audit Log**:
   - Go to **Settings > Audit Log** tab
   - You should see your recent changes logged
   - This confirms the updates were recorded

6. **Test the changes**:
   - Restart your backend: `docker-compose restart backend`
   - Check logs: You should see `✅ loaded from database`
   - Test functionality (send Telegram notification)

---

## 📋 Option 2: Using SQL (Direct Database)

If Settings UI is not accessible or you prefer SQL.

### Steps:

1. **Open Supabase SQL Editor** or connect via `psql`:
   ```bash
   # If using Docker
   docker-compose exec db psql -U postgres -d farm_management

   # Or via Supabase dashboard: SQL Editor tab
   ```

2. **Check existing settings**:
   ```sql
   SELECT setting_key,
          LEFT(setting_value::text, 50) as value_preview,
          category,
          updated_at
   FROM system_settings
   WHERE setting_key IN (
       'telegram_bot_token',
       'supabase_url',
       'supabase_service_key'
   )
   ORDER BY setting_key;
   ```

3. **Insert or update Telegram Bot Token**:
   ```sql
   INSERT INTO system_settings (
       setting_key,
       setting_value,
       data_type,
       category,
       description,
       is_encrypted,
       updated_by
   ) VALUES (
       'telegram_bot_token',
       '"1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"'::jsonb,
       'string',
       'telegram',
       'Telegram Bot API token for sending notifications',
       false,
       NULL  -- Or your user_id
   )
   ON CONFLICT (setting_key)
   DO UPDATE SET
       setting_value = EXCLUDED.setting_value,
       updated_at = NOW();
   ```

   **⚠️ Important Notes:**
   - The value must be valid JSON, so wrap strings in double quotes
   - The `::jsonb` cast is required
   - Don't forget the quotes around the entire JSON value

4. **Insert or update Supabase URL**:
   ```sql
   INSERT INTO system_settings (
       setting_key,
       setting_value,
       data_type,
       category,
       description,
       is_encrypted,
       updated_by
   ) VALUES (
       'supabase_url',
       '"https://xyzproject.supabase.co"'::jsonb,
       'string',
       'integrations',
       'Supabase project URL',
       false,
       NULL
   )
   ON CONFLICT (setting_key)
   DO UPDATE SET
       setting_value = EXCLUDED.setting_value,
       updated_at = NOW();
   ```

5. **Insert or update Supabase Service Key**:
   ```sql
   INSERT INTO system_settings (
       setting_key,
       setting_value,
       data_type,
       category,
       description,
       is_encrypted,
       updated_by
   ) VALUES (
       'supabase_service_key',
       '"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."'::jsonb,
       'string',
       'integrations',
       'Supabase service role key',
       true,  -- Marked as encrypted for security display
       NULL
   )
   ON CONFLICT (setting_key)
   DO UPDATE SET
       setting_value = EXCLUDED.setting_value,
       updated_at = NOW();
   ```

6. **Verify the inserts**:
   ```sql
   SELECT
       setting_key,
       CASE
           WHEN is_encrypted THEN '***encrypted***'
           ELSE LEFT(setting_value::text, 50)
       END as value_preview,
       data_type,
       category,
       updated_at
   FROM system_settings
   WHERE setting_key IN (
       'telegram_bot_token',
       'supabase_url',
       'supabase_service_key'
   )
   ORDER BY setting_key;
   ```

7. **Restart backend** to clear cache and reload:
   ```bash
   docker-compose restart backend
   ```

---

## 📋 Option 3: Using API (Programmatic)

If you want to automate the process or use an API client.

### Steps:

1. **Get admin authentication token**:
   ```bash
   # Login and get token
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@example.com",
       "password": "your_password"
     }'

   # Copy the access_token from response
   ```

2. **Update Telegram Bot Token**:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/settings/telegram_bot_token \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "setting_value": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
     }'
   ```

3. **Update Supabase URL**:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/settings/supabase_url \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "setting_value": "https://xyzproject.supabase.co"
     }'
   ```

4. **Update Supabase Service Key**:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/settings/supabase_service_key \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "setting_value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
     }'
   ```

5. **Restart backend**:
   ```bash
   docker-compose restart backend
   ```

---

## ✅ Verification Steps

After updating via any method:

### 1. Check Logs
```bash
# View backend logs
docker-compose logs backend | grep "Setting.*loaded"

# Expected output (all should show ✅ database):
# ✅ Setting 'telegram_bot_token' loaded from database (value length: 46 chars)
# ✅ Setting 'supabase_url' loaded from database (value length: 38 chars)
# ✅ Setting 'supabase_service_key' loaded from database (value length: 180 chars)
```

### 2. Test Telegram Functionality
```bash
curl -X POST http://localhost:8000/api/v1/telegram/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel_type": "tickets"}'
```

Expected: Test message arrives in your Telegram channel

### 3. Test Supabase Functionality
```bash
# Test password reset
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Expected: Password reset email sent

### 4. Check Database Directly
```sql
SELECT
    setting_key,
    LENGTH(setting_value::text) as value_length,
    category,
    updated_at,
    updated_by
FROM system_settings
WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
)
ORDER BY setting_key;
```

Expected: All three settings present with recent `updated_at` timestamps

---

## 🔒 Security Best Practices

### After Migration:

1. **Keep .env as fallback** but ensure it's:
   - Not committed to git (in `.gitignore`)
   - Has proper file permissions (600 or 644)
   - Only accessible to necessary users

2. **Optional: Clear .env values** (advanced):
   ```bash
   # If you want database to be ONLY source
   # Comment out in .env:
   # TELEGRAM_BOT_TOKEN=
   # SUPABASE_URL=
   # SUPABASE_SERVICE_KEY=
   ```

   ⚠️ **Warning:** Only do this if you're confident your database is stable and backed up!

3. **Enable encryption** for sensitive settings (future enhancement):
   ```sql
   UPDATE system_settings
   SET is_encrypted = true
   WHERE setting_key IN (
       'telegram_bot_token',
       'supabase_service_key'
   );
   ```

4. **Regular backups**:
   ```bash
   # Backup settings
   docker-compose exec db pg_dump -U postgres -d farm_management \
     --table=system_settings \
     --table=settings_audit_log \
     > settings_backup_$(date +%Y%m%d).sql
   ```

---

## 🔄 Rollback Procedure

If something goes wrong:

1. **Database has wrong values**:
   ```sql
   -- View audit log to see previous value
   SELECT * FROM settings_audit_log
   WHERE setting_key = 'telegram_bot_token'
   ORDER BY changed_at DESC
   LIMIT 5;

   -- Restore previous value manually
   UPDATE system_settings
   SET setting_value = '"old_value"'::jsonb
   WHERE setting_key = 'telegram_bot_token';
   ```

2. **Database is unavailable**:
   - Fallback automatically activates
   - Ensure .env has correct values
   - Restart backend: `docker-compose restart backend`
   - Logs will show: `📁 Setting 'xxx' loaded from environment variable`

3. **Complete rollback to .env**:
   ```sql
   -- Remove from database
   DELETE FROM system_settings
   WHERE setting_key IN (
       'telegram_bot_token',
       'supabase_url',
       'supabase_service_key'
   );
   ```
   - Ensure .env has all values
   - Restart backend

---

## 📚 Related Documentation

- **Migration Guide**: `/docs/MIGRATION_GUIDE_ENV_TO_DATABASE.md`
- **Testing Guide**: `/TESTING_FALLBACK_GUIDE.md`
- **Settings Management**: `/framework/HANDOVER_02_SETTINGS_MANAGEMENT.md`

---

## 🆘 Troubleshooting

### Issue: Settings not saving via UI

**Check:**
```sql
-- Verify admin permissions
SELECT u.email, up.is_admin
FROM auth.users u
JOIN user_profiles up ON u.id = up.user_id
WHERE up.is_admin = true;
```

### Issue: Values still loading from environment

**Check:**
1. Database actually has the setting:
   ```sql
   SELECT * FROM system_settings WHERE setting_key = 'telegram_bot_token';
   ```
2. Backend was restarted after update (cache cleared)
3. Check logs for errors during database fetch

### Issue: Invalid JSON error

**Fix:**
```sql
-- Correct format (string values need quotes):
INSERT INTO system_settings (...)
VALUES ('key', '"value"'::jsonb, ...);  -- ✅ Correct

-- Wrong:
VALUES ('key', 'value'::jsonb, ...);    -- ❌ Wrong - missing quotes
VALUES ('key', '"value"', ...);          -- ❌ Wrong - missing ::jsonb
```

---

**Need Help?** Check logs first: `docker-compose logs backend | grep -i setting`
