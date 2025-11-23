# Migration Guide: Environment Variables to Database Settings

**Version:** 1.0.0
**Date:** 2025-11-23
**Status:** Active

---

## Overview

This guide explains how to migrate settings from `.env` environment variables to database-managed settings, which provides:

- ✅ **Centralized Configuration**: Manage settings via Settings UI without server restarts
- ✅ **Audit Trail**: Track who changed what and when
- ✅ **Validation**: Built-in validation rules for settings
- ✅ **Security**: Encrypted storage for sensitive settings
- ✅ **Fallback Support**: Automatic fallback to environment variables if database unavailable

---

## Affected Settings

The following settings have been migrated from `.env` to database:

### 1. Telegram Bot Configuration
- **Database Key**: `telegram_bot_token`
- **Environment Variable**: `TELEGRAM_BOT_TOKEN`
- **Category**: `telegram`

### 2. Supabase Configuration
- **Database Key**: `supabase_url`
- **Environment Variable**: `SUPABASE_URL`
- **Category**: `integrations`

- **Database Key**: `supabase_service_key`
- **Environment Variable**: `SUPABASE_SERVICE_KEY`
- **Category**: `integrations`

---

## Migration Steps

### Option 1: Using Settings UI (Recommended)

1. **Login as Admin**
   - Navigate to your application
   - Login with admin credentials

2. **Access Settings**
   - Click on "Settings" in the sidebar
   - You'll see all system settings organized by category

3. **Configure Settings**
   - Find the setting you want to configure
   - Click "Edit" or toggle the edit mode
   - Enter the new value
   - Click "Save"

4. **Verify Configuration**
   - The system will validate your input
   - Check the audit log to confirm the change was recorded
   - Test the functionality (e.g., send a test Telegram notification)

### Option 2: Using SQL (For Initial Setup)

```sql
-- Insert Telegram Bot Token
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted
) VALUES (
    'telegram_bot_token',
    '"your_telegram_bot_token_here"'::jsonb,
    'string',
    'telegram',
    'Telegram Bot API token for sending notifications',
    false
)
ON CONFLICT (setting_key) DO UPDATE
SET setting_value = EXCLUDED.setting_value;

-- Insert Supabase URL
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted
) VALUES (
    'supabase_url',
    '"https://your-project.supabase.co"'::jsonb,
    'string',
    'integrations',
    'Supabase project URL',
    false
)
ON CONFLICT (setting_key) DO UPDATE
SET setting_value = EXCLUDED.setting_value;

-- Insert Supabase Service Key
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted
) VALUES (
    'supabase_service_key',
    '"your_supabase_service_key_here"'::jsonb,
    'string',
    'integrations',
    'Supabase service role key for admin operations',
    true
)
ON CONFLICT (setting_key) DO UPDATE
SET setting_value = EXCLUDED.setting_value;
```

---

## Fallback Mechanism

### How It Works

The system follows this priority order when loading settings:

```
1. Database (system_settings table)
   ↓ (if not found or database unavailable)
2. Environment Variable (.env file)
   ↓ (if not set)
3. Default Value (usually empty or None)
```

### Example: Telegram Bot Token

```python
# The system will try in this order:
1. SELECT setting_value FROM system_settings WHERE setting_key = 'telegram_bot_token'
2. os.getenv('TELEGRAM_BOT_TOKEN')
3. None (default)
```

### Debugging

The system logs which source was used for each setting:

```
✅ Setting 'telegram_bot_token' loaded from database (value length: 46 chars)
📁 Setting 'supabase_url' loaded from environment variable (value length: 38 chars)
⚠️ Setting 'some_setting' not found in database or environment. Using default value: None
```

---

## Environment Variable Configuration (Fallback)

### When to Use Environment Variables

Use environment variables as fallback in these scenarios:

1. **Initial Setup**: Before migrating to database
2. **Development**: For local development convenience
3. **Disaster Recovery**: If database becomes unavailable
4. **CI/CD**: For automated testing environments

### Updating .env File

The `.env.example` file has been updated with clear instructions:

```bash
# ============================================================================
# TELEGRAM BOT CONFIGURATION
# ============================================================================
# ⚠️ IMPORTANT: This setting has been moved to the database!
# Configure via: Settings UI > Telegram Settings (Admin only)
#
# The value below serves as FALLBACK ONLY if database setting is not available.
# For production, it's recommended to configure this via the Settings UI.
TELEGRAM_BOT_TOKEN=

# ============================================================================
# SUPABASE CONFIGURATION
# ============================================================================
# ⚠️ IMPORTANT: These settings have been moved to the database!
# Configure via: Settings UI > System Settings (Admin only)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```

---

## Testing Your Migration

### 1. Test Telegram Bot

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/telegram/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel_type": "tickets"}'

# Expected: Test notification sent to your Telegram channel
```

### 2. Test Supabase Connection

```bash
# Via password reset endpoint
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected: Password reset email sent
```

### 3. Check Logs

```bash
# Look for setting load messages
tail -f logs/app.log | grep -i "setting"

# Expected output:
# ✅ Setting 'telegram_bot_token' loaded from database (value length: 46 chars)
# ✅ Setting 'supabase_url' loaded from database (value length: 38 chars)
```

---

## Troubleshooting

### Issue: Setting not loading from database

**Symptoms:**
- Logs show: `Setting 'xxx' not found in database, trying fallback...`

**Solutions:**
1. Check if setting exists in database:
   ```sql
   SELECT * FROM system_settings WHERE setting_key = 'telegram_bot_token';
   ```
2. If not exists, insert it (see "Option 2: Using SQL" above)
3. Clear settings cache by restarting the application

### Issue: Fallback to environment not working

**Symptoms:**
- Logs show: `Setting 'xxx' not found in database or environment`

**Solutions:**
1. Check your `.env` file has the variable set:
   ```bash
   cat .env | grep TELEGRAM_BOT_TOKEN
   ```
2. Ensure `.env` file is in the correct location (`backend/.env`)
3. Restart the application to reload environment variables

### Issue: Setting value is incorrect

**Symptoms:**
- Feature not working despite setting being configured

**Solutions:**
1. Use the diagnostic function to check setting source:
   ```python
   from app.utils.settings_helper import diagnose_setting
   from app.database import get_db

   pool = get_db()
   async with pool.acquire() as conn:
       result = await diagnose_setting(conn, "telegram_bot_token")
       print(result)
   ```

2. Check the audit log to see recent changes:
   ```sql
   SELECT * FROM settings_audit_log
   WHERE setting_key = 'telegram_bot_token'
   ORDER BY changed_at DESC
   LIMIT 5;
   ```

### Issue: Database unavailable, need emergency fallback

**Symptoms:**
- Database is down but need application to work

**Solutions:**
1. Set environment variables in `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_actual_token
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your_actual_key
   ```

2. Restart application
3. Application will automatically fall back to environment variables
4. Check logs to confirm fallback:
   ```
   ⚠️ Database unavailable for Telegram token lookup: <error>. Falling back to environment variable.
   📁 Setting 'telegram_bot_token' loaded from environment variable
   ```

---

## API Reference

### Helper Functions

#### `get_setting_with_fallback()`

```python
from app.utils.settings_helper import get_setting_with_fallback

# Get setting with database-first approach
value = await get_setting_with_fallback(
    conn=conn,                              # Database connection
    setting_key="telegram_bot_token",       # Setting key
    env_fallback=settings.TELEGRAM_BOT_TOKEN,  # Fallback value
    default=None,                           # Default if all else fails
    use_cache=True                          # Use cache (default: True)
)
```

#### `get_telegram_bot_token()`

```python
from app.utils.settings_helper import get_telegram_bot_token

# Specialized getter for Telegram bot token
token = await get_telegram_bot_token(conn)
```

#### `get_supabase_credentials()`

```python
from app.utils.settings_helper import get_supabase_credentials

# Get both Supabase URL and Service Key
supabase_url, supabase_service_key = await get_supabase_credentials(conn)
```

#### `diagnose_setting()`

```python
from app.utils.settings_helper import diagnose_setting

# Diagnose where a setting is coming from
result = await diagnose_setting(
    conn=conn,
    setting_key="telegram_bot_token",
    env_key="TELEGRAM_BOT_TOKEN"  # Optional, defaults to setting_key.upper()
)

print(result)
# {
#     "setting_key": "telegram_bot_token",
#     "env_key": "TELEGRAM_BOT_TOKEN",
#     "in_database": True,
#     "in_environment": False,
#     "value_source": "database",
#     "value_length": 46,
#     "errors": []
# }
```

---

## Security Considerations

### Encrypted Settings

Some settings (like `supabase_service_key`) are marked as `is_encrypted=true` in the database. These settings:

- Are encrypted at rest in the database
- Are never displayed in full in the Settings UI
- Are logged only as masked values in audit logs
- Require additional permissions to view/modify

### Audit Trail

All setting changes are tracked in the `settings_audit_log` table:

```sql
SELECT
    setting_key,
    old_value,
    new_value,
    changed_by,
    changed_at
FROM settings_audit_log
ORDER BY changed_at DESC
LIMIT 10;
```

### Access Control

- Only admin users can view/modify system settings
- Each change is attributed to the user who made it
- Non-admin users can only see public settings via `/api/v1/settings/public`

---

## Rollback Procedure

If you need to rollback to environment-only configuration:

1. **Set environment variables** in `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   SUPABASE_URL=your_url
   SUPABASE_SERVICE_KEY=your_key
   ```

2. **Delete database settings** (optional):
   ```sql
   DELETE FROM system_settings WHERE setting_key IN (
       'telegram_bot_token',
       'supabase_url',
       'supabase_service_key'
   );
   ```

3. **Restart application**

The application will automatically fall back to environment variables.

---

## Support

For questions or issues:

1. Check the logs: `tail -f logs/app.log`
2. Review the troubleshooting section above
3. Create an issue in the project repository
4. Contact the development team

---

## Changelog

### v1.0.0 (2025-11-23)
- Initial migration guide
- Documented Telegram and Supabase settings migration
- Added troubleshooting section
- Added API reference
