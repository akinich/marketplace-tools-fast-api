# Settings Fallback Testing Guide

**Date:** 2025-11-23
**Purpose:** Verify database-first settings with environment variable fallback

---

## 🎯 Test Scenarios

### Test 1: Database Primary Source (Normal Operation)

**Goal:** Verify settings load from database when available

**Steps:**
1. **Add settings to database** (if not already done):
   ```sql
   -- Via Supabase SQL Editor or psql
   INSERT INTO system_settings (
       setting_key,
       setting_value,
       data_type,
       category,
       description,
       is_encrypted
   ) VALUES
   (
       'telegram_bot_token',
       '"YOUR_ACTUAL_BOT_TOKEN"'::jsonb,
       'string',
       'telegram',
       'Telegram Bot API token for sending notifications',
       false
   ),
   (
       'supabase_url',
       '"https://your-project.supabase.co"'::jsonb,
       'string',
       'integrations',
       'Supabase project URL',
       false
   ),
   (
       'supabase_service_key',
       '"YOUR_SERVICE_KEY"'::jsonb,
       'string',
       'integrations',
       'Supabase service role key',
       true
   )
   ON CONFLICT (setting_key) DO UPDATE
   SET setting_value = EXCLUDED.setting_value;
   ```

2. **Restart your backend application**:
   ```bash
   # If running directly
   uvicorn app.main:app --reload

   # If using Docker
   docker-compose restart backend
   ```

3. **Check logs** for database loading:
   ```bash
   # Look for ✅ emoji indicating database load
   tail -f logs/app.log | grep "Setting"

   # Or if using Docker
   docker-compose logs -f backend | grep "Setting"
   ```

4. **Expected output**:
   ```
   ✅ Setting 'telegram_bot_token' loaded from database (value length: 46 chars)
   ✅ Setting 'supabase_url' loaded from database (value length: 38 chars)
   ✅ Setting 'supabase_service_key' loaded from database (value length: 180 chars)
   ```

---

### Test 2: Environment Variable Fallback

**Goal:** Verify fallback to .env when database doesn't have the setting

**Steps:**

1. **Ensure .env has the settings**:
   ```bash
   # Edit backend/.env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   SUPABASE_URL=https://xyzproject.supabase.co
   SUPABASE_SERVICE_KEY=your_service_key_here
   ```

2. **Remove settings from database** (temporarily for testing):
   ```sql
   -- Backup current values first!
   SELECT setting_key, setting_value FROM system_settings
   WHERE setting_key IN ('telegram_bot_token', 'supabase_url', 'supabase_service_key');

   -- Delete to test fallback
   DELETE FROM system_settings
   WHERE setting_key IN ('telegram_bot_token', 'supabase_url', 'supabase_service_key');
   ```

3. **Restart backend**:
   ```bash
   docker-compose restart backend
   # OR
   # Stop and start your uvicorn process
   ```

4. **Check logs** for environment variable fallback:
   ```bash
   docker-compose logs backend | grep "Setting"
   ```

5. **Expected output**:
   ```
   📁 Setting 'telegram_bot_token' loaded from environment variable (value length: 46 chars)
   📁 Setting 'supabase_url' loaded from environment variable (value length: 38 chars)
   📁 Setting 'supabase_service_key' loaded from environment variable (value length: 180 chars)
   ```

6. **Restore database settings** after test:
   ```sql
   -- Re-insert the settings you removed
   INSERT INTO system_settings (...) VALUES (...);
   ```

---

### Test 3: Database Unavailable (Disaster Recovery)

**Goal:** Verify fallback when database is completely unavailable

**Steps:**

1. **Ensure .env has all critical settings**

2. **Stop database temporarily**:
   ```bash
   # If using Docker Compose
   docker-compose stop db
   ```

3. **Start/Restart backend**:
   ```bash
   docker-compose restart backend
   ```

4. **Check logs**:
   ```bash
   docker-compose logs backend | grep -i "setting\|database"
   ```

5. **Expected output**:
   ```
   ⚠️ Failed to fetch 'telegram_bot_token' from database: connection refused. Falling back to environment variable.
   📁 Setting 'telegram_bot_token' loaded from environment variable (value length: 46 chars)
   ```

6. **Restart database**:
   ```bash
   docker-compose start db
   ```

---

### Test 4: Functional Testing

**Goal:** Verify actual functionality works with loaded settings

#### Test Telegram Notifications:
```bash
# Send test notification
curl -X POST http://localhost:8000/api/v1/telegram/test \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel_type": "tickets"}'
```

**Expected:** You receive a test message in your Telegram channel

#### Test Supabase Connection:
```bash
# Trigger password reset (uses Supabase)
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected:** Password reset email sent successfully

---

## 🔍 Verification Checklist

After testing, verify:

- [ ] **Database Primary**: Logs show ✅ when database has settings
- [ ] **Environment Fallback**: Logs show 📁 when database doesn't have settings
- [ ] **Database Connection Failure**: Logs show ⚠️ and fallback works
- [ ] **Telegram Functions**: Test notifications work
- [ ] **Supabase Functions**: Password reset works
- [ ] **Settings UI**: Can view and update settings via Settings page
- [ ] **Audit Log**: Changes are tracked in settings_audit_log table

---

## 📊 Monitoring in Production

**Quick checks:**

```bash
# Check what source each setting is using
docker-compose logs backend | grep "Setting.*loaded" | tail -20

# Count database vs environment loads
docker-compose logs backend | grep "loaded from database" | wc -l
docker-compose logs backend | grep "loaded from environment" | wc -l

# Check for any warnings
docker-compose logs backend | grep "⚠️" | tail -10
```

---

## 🎯 Recommended Production State

For production, you should see:
```
✅ Setting 'telegram_bot_token' loaded from database
✅ Setting 'supabase_url' loaded from database
✅ Setting 'supabase_service_key' loaded from database
```

All critical settings should load from database (✅), with .env only as fallback safety net.
