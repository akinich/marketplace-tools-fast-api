-- ============================================================================
-- QUICK DATABASE COMPARISON
-- ============================================================================
-- Run this on BOTH databases in Supabase SQL Editor
-- Then compare the results side-by-side
-- ============================================================================

-- ============================================================================
-- STEP 1: SUMMARY (Most Important - Check This First!)
-- ============================================================================
SELECT
    '📊 DATABASE SUMMARY' as section,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'PRIMARY KEY') as primary_keys,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'FOREIGN KEY') as foreign_keys,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    (SELECT COUNT(*) FROM information_schema.triggers WHERE event_object_schema = 'public') as total_triggers;

-- ============================================================================
-- STEP 2: TABLE LIST WITH ROW COUNTS
-- ============================================================================
SELECT
    '📋 TABLE: ' || tablename as table_info,
    (SELECT COUNT(*) FROM information_schema.tables t WHERE t.table_name = pt.tablename AND t.table_schema = 'public') as exists,
    pg_size_pretty(pg_total_relation_size('public.' || tablename)) as size
FROM pg_tables pt
WHERE schemaname = 'public'
ORDER BY tablename;

-- ============================================================================
-- STEP 3: ROW COUNTS FOR ALL TABLES
-- ============================================================================

-- Core Application Tables
SELECT 'user_profiles' as table_name, COUNT(*) as row_count FROM user_profiles
UNION ALL SELECT 'roles', COUNT(*) FROM roles
UNION ALL SELECT 'modules', COUNT(*) FROM modules
UNION ALL SELECT 'user_module_permissions', COUNT(*) FROM user_module_permissions
UNION ALL SELECT 'activity_logs', COUNT(*) FROM activity_logs

-- Inventory Tables
UNION ALL SELECT 'item_master', COUNT(*) FROM item_master
UNION ALL SELECT 'inventory_categories', COUNT(*) FROM inventory_categories
UNION ALL SELECT 'inventory_batches', COUNT(*) FROM inventory_batches
UNION ALL SELECT 'inventory_transactions', COUNT(*) FROM inventory_transactions

-- Purchase Tables
UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL SELECT 'purchase_orders', COUNT(*) FROM purchase_orders
UNION ALL SELECT 'purchase_order_items', COUNT(*) FROM purchase_order_items

-- Biofloc Tables
UNION ALL SELECT 'biofloc_tanks', COUNT(*) FROM biofloc_tanks
UNION ALL SELECT 'biofloc_water_tests', COUNT(*) FROM biofloc_water_tests
UNION ALL SELECT 'biofloc_feed_logs', COUNT(*) FROM biofloc_feed_logs
UNION ALL SELECT 'biofloc_growth_records', COUNT(*) FROM biofloc_growth_records

-- System Settings Tables
UNION ALL SELECT 'system_settings', COUNT(*) FROM system_settings
UNION ALL SELECT 'settings_audit_log', COUNT(*) FROM settings_audit_log

-- Email Tables
UNION ALL SELECT 'email_templates', COUNT(*) FROM email_templates
UNION ALL SELECT 'email_queue', COUNT(*) FROM email_queue
UNION ALL SELECT 'email_recipients', COUNT(*) FROM email_recipients
UNION ALL SELECT 'email_send_log', COUNT(*) FROM email_send_log

-- Webhook Tables
UNION ALL SELECT 'webhooks', COUNT(*) FROM webhooks
UNION ALL SELECT 'webhook_deliveries', COUNT(*) FROM webhook_deliveries

-- API Key Tables
UNION ALL SELECT 'api_keys', COUNT(*) FROM api_keys
UNION ALL SELECT 'api_key_usage', COUNT(*) FROM api_key_usage

ORDER BY table_name;

-- ============================================================================
-- STEP 4: DATA INTEGRITY HASHES (Critical Tables Only)
-- ============================================================================

-- Users and Roles
SELECT
    'HASH: user_profiles' as check_name,
    COUNT(*) as rows,
    MD5(STRING_AGG(
        COALESCE(user_id::text, '') || '|' ||
        COALESCE(username, '') || '|' ||
        COALESCE(email, ''),
        '|' ORDER BY user_id
    )) as data_hash
FROM user_profiles

UNION ALL

SELECT
    'HASH: roles',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(role_id::text, '') || '|' ||
        COALESCE(role_name, ''),
        '|' ORDER BY role_id
    ))
FROM roles

UNION ALL

SELECT
    'HASH: modules',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(module_id::text, '') || '|' ||
        COALESCE(module_name, ''),
        '|' ORDER BY module_id
    ))
FROM modules

UNION ALL

SELECT
    'HASH: item_master',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(item_id::text, '') || '|' ||
        COALESCE(item_code, '') || '|' ||
        COALESCE(item_name, ''),
        '|' ORDER BY item_id
    ))
FROM item_master

UNION ALL

SELECT
    'HASH: inventory_categories',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(category_id::text, '') || '|' ||
        COALESCE(category_name, ''),
        '|' ORDER BY category_id
    ))
FROM inventory_categories

UNION ALL

-- System Settings (excluding secrets)
SELECT
    'HASH: system_settings',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(setting_key, '') || '|' ||
        COALESCE(setting_value, ''),
        '|' ORDER BY setting_id
    ))
FROM system_settings
WHERE setting_key NOT IN ('supabase_url', 'supabase_service_key', 'telegram_bot_token')

UNION ALL

SELECT
    'HASH: email_templates',
    COUNT(*),
    MD5(STRING_AGG(
        COALESCE(template_key, '') || '|' ||
        COALESCE(template_name, ''),
        '|' ORDER BY template_id
    ))
FROM email_templates;

-- ============================================================================
-- STEP 5: CONSTRAINT COUNTS
-- ============================================================================
SELECT
    '🔒 CONSTRAINTS' as section,
    constraint_type,
    COUNT(*) as count
FROM information_schema.table_constraints
WHERE table_schema = 'public'
GROUP BY constraint_type
ORDER BY constraint_type;

-- ============================================================================
-- STEP 6: INDEX COUNTS BY TABLE
-- ============================================================================
SELECT
    '📇 INDEXES: ' || tablename as table_info,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- ============================================================================
-- DONE!
-- ============================================================================
-- Copy all these results and compare them between both databases.
-- The key things to match:
--   ✅ Total tables (should be 26)
--   ✅ Row counts for each table
--   ✅ Data hashes (MD5 values should be identical)
--   ✅ Constraint counts
--   ✅ Index counts
-- ============================================================================
