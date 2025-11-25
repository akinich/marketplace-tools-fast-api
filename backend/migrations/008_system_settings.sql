-- ============================================================================
-- Migration 008: System Settings & Configuration Management
-- Version: 1.0.0
-- Description: Create system_settings and settings_audit_log tables
-- ============================================================================

-- Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    category VARCHAR(100) NOT NULL,
    description TEXT,
    validation_rules JSONB,
    is_public BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on setting_key for fast lookups
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_updated_at();

-- Create settings_audit_log table
CREATE TABLE IF NOT EXISTS settings_audit_log (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_settings_audit_key ON settings_audit_log(setting_key);
CREATE INDEX idx_settings_audit_changed_by ON settings_audit_log(changed_by);

-- Insert default settings
INSERT INTO system_settings (setting_key, setting_value, data_type, category, description, validation_rules, is_public) VALUES

-- Authentication Settings
('auth.jwt_expiry_minutes', '30', 'integer', 'auth', 'JWT access token expiration time in minutes', '{"min": 5, "max": 1440}', false),
('auth.refresh_expiry_days', '7', 'integer', 'auth', 'JWT refresh token expiration time in days', '{"min": 1, "max": 90}', false),
('auth.max_login_attempts', '5', 'integer', 'auth', 'Maximum failed login attempts before account lockout', '{"min": 3, "max": 10}', false),
('auth.lockout_duration_minutes', '30', 'integer', 'auth', 'Account lockout duration in minutes', '{"min": 10, "max": 1440}', false),
('auth.password_min_length', '8', 'integer', 'auth', 'Minimum password length', '{"min": 6, "max": 32}', false),
('auth.session_timeout_minutes', '30', 'integer', 'auth', 'Inactivity timeout before auto-logout (minutes)', '{"min": 5, "max": 480}', false),
('auth.max_sessions_admin', '5', 'integer', 'auth', 'Maximum concurrent sessions for admin users', '{"min": 1, "max": 10}', false),
('auth.max_sessions_user', '1', 'integer', 'auth', 'Maximum concurrent sessions for regular users', '{"min": 1, "max": 5}', false),

-- Email Settings
('email.smtp_enabled', 'false', 'boolean', 'email', 'Enable SMTP email notifications', '{}', false),
('email.smtp_host', '""', 'string', 'email', 'SMTP server hostname', '{}', false),
('email.smtp_port', '587', 'integer', 'email', 'SMTP server port', '{"min": 1, "max": 65535}', false),
('email.smtp_use_tls', 'true', 'boolean', 'email', 'Use TLS for SMTP connection', '{}', false),
('email.smtp_user', '""', 'string', 'email', 'SMTP username', '{}', false),
('email.smtp_password', '""', 'string', 'email', 'SMTP password (encrypted)', '{}', false),
('email.from_email', '"noreply@farmapp.com"', 'string', 'email', 'Default sender email address', '{}', false),
('email.from_name', '"Farm Management System"', 'string', 'email', 'Default sender name', '{}', false),

-- Webhook Settings
('webhooks.enabled', 'true', 'boolean', 'webhooks', 'Enable webhook functionality', '{}', false),
('webhooks.retry_attempts', '3', 'integer', 'webhooks', 'Number of retry attempts for failed webhooks', '{"min": 0, "max": 10}', false),
('webhooks.retry_delay_seconds', '60', 'integer', 'webhooks', 'Delay between retry attempts in seconds', '{"min": 10, "max": 3600}', false),
('webhooks.timeout_seconds', '30', 'integer', 'webhooks', 'Webhook request timeout in seconds', '{"min": 5, "max": 120}', false),

-- Application Settings
('app.name', '"Farm Management System"', 'string', 'app', 'Application name', '{}', true),
('app.support_email', '"support@farmapp.com"', 'string', 'app', 'Support email address', '{}', true),
('app.timezone', '"UTC"', 'string', 'app', 'Application timezone', '{}', true),
('app.date_format', '"DD/MM/YYYY"', 'string', 'app', 'Date format', '{}', true),
('app.maintenance_mode', 'false', 'boolean', 'app', 'Enable maintenance mode', '{}', false),

-- Feature Flags
('features.api_keys_enabled', 'false', 'boolean', 'features', 'Enable API key authentication', '{}', false),
('features.webhooks_enabled', 'false', 'boolean', 'features', 'Enable webhook management', '{}', false),
('features.websockets_enabled', 'false', 'boolean', 'features', 'Enable WebSocket real-time updates', '{}', false),
('features.email_notifications_enabled', 'false', 'boolean', 'features', 'Enable email notifications', '{}', false)

ON CONFLICT (setting_key) DO NOTHING;

-- Verify the migration
SELECT setting_key, setting_value, data_type, category, is_public
FROM system_settings
ORDER BY category, setting_key;
