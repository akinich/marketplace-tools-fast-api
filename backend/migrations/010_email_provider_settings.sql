-- ============================================================================
-- Migration 010: Email Provider Settings
-- ============================================================================
-- Add settings for multi-provider email support
-- Supports: SendGrid, Resend, Brevo, Mailgun, SMTP

-- Add email provider dropdown setting
INSERT INTO system_settings (setting_key, setting_value, data_type, category, description, is_public)
VALUES
('email.provider', '"sendgrid"', 'string', 'email', 'Email provider (smtp, sendgrid, resend, brevo, mailgun)', false),
('email.sendgrid_api_key', '""', 'string', 'email', 'SendGrid API key (100 emails/day free)', false),
('email.resend_api_key', '""', 'string', 'email', 'Resend API key (100 emails/day free)', false),
('email.brevo_api_key', '""', 'string', 'email', 'Brevo API key (300 emails/day free)', false),
('email.mailgun_api_key', '""', 'string', 'email', 'Mailgun API key', false),
('email.mailgun_domain', '""', 'string', 'email', 'Mailgun domain', false)
ON CONFLICT (setting_key) DO NOTHING;

-- Verify settings
SELECT 'Email provider settings created:' as info, COUNT(*) as count
FROM system_settings
WHERE setting_key LIKE 'email.%' AND setting_key IN (
    'email.provider',
    'email.sendgrid_api_key',
    'email.resend_api_key',
    'email.brevo_api_key',
    'email.mailgun_api_key',
    'email.mailgun_domain'
);
