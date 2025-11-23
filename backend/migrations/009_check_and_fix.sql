-- ============================================================================
-- Migration 009 - Diagnostic & Fix Script
-- ============================================================================
-- This script checks if the telegram/supabase settings exist and helps fix issues
-- ============================================================================

-- Step 1: Check if system_settings table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_settings') THEN
        RAISE NOTICE '❌ ERROR: system_settings table does not exist!';
        RAISE NOTICE '➡️  ACTION: Run migration 008_system_settings.sql first';
        RAISE EXCEPTION 'Missing prerequisite table: system_settings';
    ELSE
        RAISE NOTICE '✅ system_settings table exists';
    END IF;
END $$;

-- Step 2: Check current state of telegram/supabase settings
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '❌ No settings found - will insert'
        WHEN COUNT(*) = 3 THEN '✅ All 3 settings already exist - safe to skip migration'
        ELSE '⚠️  Partial settings found - will insert missing ones'
    END as status,
    COUNT(*) as existing_count
FROM system_settings
WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
);

-- Step 3: Show which specific settings exist
SELECT
    'telegram_bot_token' as setting,
    CASE WHEN EXISTS (SELECT 1 FROM system_settings WHERE setting_key = 'telegram_bot_token')
        THEN '✅ EXISTS' ELSE '❌ MISSING' END as status
UNION ALL
SELECT
    'supabase_url' as setting,
    CASE WHEN EXISTS (SELECT 1 FROM system_settings WHERE setting_key = 'supabase_url')
        THEN '✅ EXISTS' ELSE '❌ MISSING' END as status
UNION ALL
SELECT
    'supabase_service_key' as setting,
    CASE WHEN EXISTS (SELECT 1 FROM system_settings WHERE setting_key = 'supabase_service_key')
        THEN '✅ EXISTS' ELSE '❌ MISSING' END as status;

-- Step 4: If settings exist, show their current values (masked for security)
SELECT
    setting_key,
    CASE
        WHEN is_encrypted THEN '***encrypted***'
        WHEN setting_value::text = '""' THEN '⚠️  EMPTY - needs to be configured'
        ELSE '✅ SET (length: ' || LENGTH(setting_value::text) || ' chars)'
    END as value_status,
    category,
    updated_at
FROM system_settings
WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
)
ORDER BY setting_key;

-- ============================================================================
-- INTERPRETATION GUIDE:
-- ============================================================================
-- If you see "All 3 settings already exist":
--   → Migration 009 is already done! Skip to updating values via Settings UI
--
-- If you see "No settings found" or "Partial settings found":
--   → Run: 009_telegram_supabase_settings.sql
--
-- If you see "EMPTY - needs to be configured":
--   → Settings exist but need values. Update via Settings UI or SQL
-- ============================================================================
