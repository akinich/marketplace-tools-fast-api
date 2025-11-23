-- ============================================================================
-- Migration 009: Telegram & Supabase Settings Migration to Database
-- Version: 1.0.0
-- Date: 2025-11-23
-- Description: Add Telegram and Supabase configuration settings to system_settings
-- ============================================================================
-- Prerequisites: Migration 008 (system_settings table) must be run first
-- ============================================================================

-- Insert Telegram Bot Token setting
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted,
    is_public,
    validation_rules
) VALUES (
    'telegram_bot_token',
    '""'::jsonb,
    'string',
    'telegram',
    'Telegram Bot API token for sending notifications',
    false,
    false,
    '{"min_length": 30}'::jsonb
)
ON CONFLICT (setting_key) DO NOTHING;

-- Insert Supabase URL setting
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted,
    is_public,
    validation_rules
) VALUES (
    'supabase_url',
    '""'::jsonb,
    'string',
    'integrations',
    'Supabase project URL',
    false,
    false,
    '{"pattern": "^https://.*\\.supabase\\.co$"}'::jsonb
)
ON CONFLICT (setting_key) DO NOTHING;

-- Insert Supabase Service Key setting
INSERT INTO system_settings (
    setting_key,
    setting_value,
    data_type,
    category,
    description,
    is_encrypted,
    is_public,
    validation_rules
) VALUES (
    'supabase_service_key',
    '""'::jsonb,
    'string',
    'integrations',
    'Supabase service role key (encrypted)',
    true,
    false,
    '{"min_length": 100}'::jsonb
)
ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================================
-- Verify the migration
-- ============================================================================
SELECT
    setting_key,
    CASE
        WHEN is_encrypted THEN '***encrypted***'
        ELSE LEFT(setting_value::text, 50)
    END as value_preview,
    data_type,
    category,
    description,
    is_encrypted,
    created_at
FROM system_settings
WHERE setting_key IN (
    'telegram_bot_token',
    'supabase_url',
    'supabase_service_key'
)
ORDER BY setting_key;

-- ============================================================================
-- Expected Output:
-- ============================================================================
-- setting_key           | value_preview | data_type | category      | description                       | is_encrypted
-- ----------------------|---------------|-----------|---------------|-----------------------------------|-------------
-- supabase_service_key  | ***encrypted***| string   | integrations  | Supabase service role key (...)   | t
-- supabase_url          | ""            | string    | integrations  | Supabase project URL              | f
-- telegram_bot_token    | ""            | string    | telegram      | Telegram Bot API token (...)      | f
-- ============================================================================
