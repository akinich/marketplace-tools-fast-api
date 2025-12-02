-- ============================================================================
-- Remove Duplicate WooCommerce Settings
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-12-02
--
-- This migration removes duplicate WooCommerce settings from system_settings.
-- The migration add_b2c_ops_module.sql created lowercase keys (api_url, etc.)
-- but someone may have also added uppercase versions (WOOCOMMERCE_API_URL, etc.)
--
-- We keep the lowercase versions as they're used in the codebase.
-- ============================================================================

-- Remove duplicate uppercase WooCommerce settings if they exist
DELETE FROM system_settings
WHERE setting_key IN (
    'WOOCOMMERCE_API_URL',
    'WooCommerce API URL',
    'WOOCOMMERCE_CONSUMER_KEY',
    'WooCommerce API Consumer Key',
    'WOOCOMMERCE_CONSUMER_SECRET',
    'WooCommerce API Consumer Secret'
);

-- Ensure correct lowercase settings exist with proper descriptions
INSERT INTO system_settings (category, setting_key, setting_value, data_type, is_public, is_encrypted, description)
VALUES
    ('woocommerce', 'api_url', '', 'string', false, false, 'WooCommerce API URL (e.g., https://your-site.com/wp-json/wc/v3)'),
    ('woocommerce', 'consumer_key', '', 'string', false, true, 'WooCommerce API Consumer Key'),
    ('woocommerce', 'consumer_secret', '', 'string', false, true, 'WooCommerce API Consumer Secret')
ON CONFLICT (setting_key) DO UPDATE SET
    description = EXCLUDED.description,
    category = EXCLUDED.category;

-- Update the description to be clearer
COMMENT ON TABLE system_settings IS 'System-wide configuration settings. Use lowercase_with_underscores for setting_key naming convention.';
