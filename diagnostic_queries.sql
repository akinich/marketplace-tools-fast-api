-- ============================================================================
-- ORDERS MODULE DIAGNOSTIC QUERIES
-- Run these in your database to identify issues
-- ============================================================================

-- QUERY 1: Check if tables exist
-- Expected: 2 rows (orders, order_items)
SELECT tablename
FROM pg_tables
WHERE tablename IN ('orders', 'order_items')
  AND schemaname = 'public';

-- QUERY 2: Check WooCommerce settings configuration
-- Expected: 4 rows (api_url, consumer_key, consumer_secret, webhook_secret)
SELECT
    setting_key,
    CASE
        WHEN setting_key LIKE '%secret%' OR setting_key LIKE '%key%'
        THEN '***CONFIGURED***'
        ELSE setting_value::text
    END as value,
    data_type,
    is_encrypted
FROM system_settings
WHERE setting_key LIKE 'woocommerce.%'
ORDER BY setting_key;

-- QUERY 3: Check webhook secret specifically
-- Expected: 1 row with the UUID secret
SELECT
    setting_key,
    setting_value,
    is_encrypted,
    updated_at
FROM system_settings
WHERE setting_key = 'woocommerce.webhook_secret';

-- QUERY 4: Check if orders table has any data
-- Expected: Shows count of orders
SELECT
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE sync_source = 'webhook') as from_webhooks,
    COUNT(*) FILTER (WHERE sync_source = 'api') as from_api,
    COUNT(*) FILTER (WHERE sync_source = 'manual') as from_manual,
    MAX(created_at) as latest_order,
    MAX(last_synced_at) as last_sync
FROM orders;

-- QUERY 5: Check order_items table
-- Expected: Shows count of line items
SELECT COUNT(*) as total_line_items
FROM order_items;

-- QUERY 6: If orders exist, show recent ones
-- Expected: Shows last 5 orders
SELECT
    id,
    woo_order_id,
    order_number,
    status,
    total,
    sync_source,
    last_synced_at,
    created_at
FROM orders
ORDER BY created_at DESC
LIMIT 5;

-- QUERY 7: Check if woo_customers table exists and has data
-- Expected: Shows customer count
SELECT COUNT(*) as total_customers
FROM woo_customers;

-- ============================================================================
-- MISSING CREDENTIALS FIX
-- If QUERY 2 shows missing WooCommerce API credentials, get them from:
-- WooCommerce → Settings → Advanced → REST API → Add Key
-- Then run these INSERTs (replace with your actual values):
-- ============================================================================

-- INSERT INTO system_settings (
--     setting_key, setting_value, data_type, category, description, is_public, is_encrypted
-- ) VALUES
-- ('woocommerce.api_url', '"https://sustenance.co.in/wp-json/wc/v3"'::jsonb, 'string', 'woocommerce', 'WooCommerce REST API URL', false, false),
-- ('woocommerce.consumer_key', '"ck_YOUR_CONSUMER_KEY"'::jsonb, 'string', 'woocommerce', 'WooCommerce Consumer Key', false, true),
-- ('woocommerce.consumer_secret', '"cs_YOUR_CONSUMER_SECRET"'::jsonb, 'string', 'woocommerce', 'WooCommerce Consumer Secret', false, true)
-- ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;
