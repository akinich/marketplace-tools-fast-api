-- ============================================================================
-- ORDERS MODULE DIAGNOSTIC QUERIES (API Sync Only)
-- Run these in your database to identify issues
-- ============================================================================

-- QUERY 1: Check if tables exist
-- Expected: 2 rows (orders, order_items)
SELECT tablename
FROM pg_tables
WHERE tablename IN ('orders', 'order_items')
  AND schemaname = 'public';

-- QUERY 2: Check WooCommerce API settings configuration
-- Expected: 3 rows (api_url, consumer_key, consumer_secret)
-- Note: webhook_secret is NOT needed for API-only sync
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

-- QUERY 3: Check if orders table has any data
-- Expected: Shows count of orders (all from API sync)
SELECT
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE sync_source = 'api') as from_api,
    MAX(created_at) as latest_order,
    MAX(last_synced_at) as last_sync
FROM orders;

-- QUERY 4: Check order_items table
-- Expected: Shows count of line items
SELECT COUNT(*) as total_line_items
FROM order_items;

-- QUERY 5: If orders exist, show recent ones
-- Expected: Shows last 10 orders with details
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
LIMIT 10;

-- QUERY 6: Check if woo_customers table exists and has data
-- Expected: Shows customer count
SELECT COUNT(*) as total_customers
FROM woo_customers;

-- QUERY 7: Check order status distribution
-- Expected: Shows count of orders by status
SELECT
    status,
    COUNT(*) as order_count,
    SUM(total) as total_revenue
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- QUERY 8: Check most recent sync activity
-- Expected: Shows when orders were last synced
SELECT
    DATE(last_synced_at) as sync_date,
    COUNT(*) as orders_synced,
    MIN(last_synced_at) as earliest_sync,
    MAX(last_synced_at) as latest_sync
FROM orders
WHERE last_synced_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(last_synced_at)
ORDER BY sync_date DESC;

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
