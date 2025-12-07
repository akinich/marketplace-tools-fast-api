-- ============================================================================
-- Migration 012: Rename Application to Marketplace ERP
-- Version: 1.0.0
-- Description: Update system settings to reflect new application name
-- ============================================================================

-- Update app.name
UPDATE system_settings
SET setting_value = '"Marketplace ERP"'::jsonb,
    updated_at = NOW()
WHERE setting_key = 'app.name';

-- Update email.from_name default
UPDATE system_settings
SET setting_value = '"Marketplace ERP"'::jsonb,
    updated_at = NOW()
WHERE setting_key = 'email.from_name' AND setting_value = '"Marketplace ERP Tools"'::jsonb;

-- Log the change in audit log (using a system user ID or NULL if not available contextually, 
-- but since this is a migration, we'll just insert directly)
INSERT INTO settings_audit_log (setting_key, old_value, new_value, changed_by)
VALUES 
    ('app.name', '"Marketplace ERP Tools"'::jsonb, '"Marketplace ERP"'::jsonb, NULL),
    ('email.from_name', '"Marketplace ERP Tools"'::jsonb, '"Marketplace ERP"'::jsonb, NULL);
