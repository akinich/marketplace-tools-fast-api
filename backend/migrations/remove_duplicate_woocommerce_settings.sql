-- ============================================================================
-- Remove Duplicate WooCommerce Settings
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-12-02
--
-- This migration removes duplicate/incorrect WooCommerce settings from system_settings.
-- The correct format should be 'woocommerce.key_name' following the codebase standard.
--
-- Standard format (category.key):
--   - woocommerce.api_url
--   - woocommerce.consumer_key
--   - woocommerce.consumer_secret
--
-- This migration removes incorrect formats:
--   - Plain: api_url, consumer_key (missing prefix)
--   - Uppercase: WOOCOMMERCE_API_URL (wrong convention)
-- ============================================================================

-- Remove duplicate/incorrect WooCommerce settings
DELETE FROM system_settings
WHERE setting_key IN (
    -- Plain lowercase (wrong - missing woocommerce. prefix)
    'api_url',
    'consumer_key',
    'consumer_secret',
    -- Uppercase (wrong convention)
    'WOOCOMMERCE_API_URL',
    'WOOCOMMERCE_CONSUMER_KEY',
    'WOOCOMMERCE_CONSUMER_SECRET',
    -- Mixed case variants
    'WooCommerce API URL',
    'WooCommerce API Consumer Key',
    'WooCommerce API Consumer Secret'
);

-- Ensure correct settings exist with proper dotted notation
INSERT INTO system_settings (category, setting_key, setting_value, data_type, is_public, is_encrypted, description)
VALUES
    ('woocommerce', 'woocommerce.api_url', '', 'string', false, false, 'WooCommerce API URL (e.g., https://your-site.com/wp-json/wc/v3)'),
    ('woocommerce', 'woocommerce.consumer_key', '', 'string', false, true, 'WooCommerce API Consumer Key'),
    ('woocommerce', 'woocommerce.consumer_secret', '', 'string', false, true, 'WooCommerce API Consumer Secret')
ON CONFLICT (setting_key) DO UPDATE SET
    description = EXCLUDED.description,
    category = EXCLUDED.category;

-- Update the description to be clearer
COMMENT ON TABLE system_settings IS 'System-wide configuration settings. Use category.key_name format for setting_key naming convention (e.g., email.smtp_host, woocommerce.api_url).';
