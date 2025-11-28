-- ============================================================================
-- DATABASE COMPARISON SCRIPT
-- ============================================================================
-- Purpose: Compare schema and data between two databases
-- Usage: Run this script on BOTH databases and compare the outputs
-- ============================================================================

-- ============================================================================
-- 1. ALL TABLES IN DATABASE
-- ============================================================================
SELECT
    '1_ALL_TABLES' as check_type,
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- ============================================================================
-- 2. TABLE ROW COUNTS
-- ============================================================================
DO $$
DECLARE
    table_record RECORD;
    row_count INTEGER;
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'TABLE ROW COUNTS';
    RAISE NOTICE '============================================';

    FOR table_record IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', table_record.tablename) INTO row_count;
        RAISE NOTICE 'Table: % - Rows: %', table_record.tablename, row_count;
    END LOOP;
END $$;

-- ============================================================================
-- 3. TABLE SCHEMAS (All Columns)
-- ============================================================================
SELECT
    '3_TABLE_SCHEMAS' as check_type,
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- ============================================================================
-- 4. PRIMARY KEY CONSTRAINTS
-- ============================================================================
SELECT
    '4_PRIMARY_KEYS' as check_type,
    tc.table_name,
    tc.constraint_name,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public'
AND tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_name;

-- ============================================================================
-- 5. FOREIGN KEY CONSTRAINTS
-- ============================================================================
SELECT
    '5_FOREIGN_KEYS' as check_type,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- 6. UNIQUE CONSTRAINTS
-- ============================================================================
SELECT
    '6_UNIQUE_CONSTRAINTS' as check_type,
    tc.table_name,
    tc.constraint_name,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public'
AND tc.constraint_type = 'UNIQUE'
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- 7. CHECK CONSTRAINTS
-- ============================================================================
SELECT
    '7_CHECK_CONSTRAINTS' as check_type,
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- 8. INDEXES
-- ============================================================================
SELECT
    '8_INDEXES' as check_type,
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- ============================================================================
-- 9. TRIGGERS
-- ============================================================================
SELECT
    '9_TRIGGERS' as check_type,
    event_object_table as table_name,
    trigger_name,
    event_manipulation,
    action_timing,
    action_statement
FROM information_schema.triggers
WHERE event_object_schema = 'public'
ORDER BY event_object_table, trigger_name;

-- ============================================================================
-- 10. FUNCTIONS
-- ============================================================================
SELECT
    '10_FUNCTIONS' as check_type,
    n.nspname as schema,
    p.proname as function_name,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_functiondef(p.oid) as definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.prokind = 'f'  -- only functions, not procedures
ORDER BY p.proname;

-- ============================================================================
-- 11. SEQUENCES
-- ============================================================================
SELECT
    '11_SEQUENCES' as check_type,
    sequence_schema,
    sequence_name,
    data_type,
    start_value,
    minimum_value,
    maximum_value,
    increment
FROM information_schema.sequences
WHERE sequence_schema = 'public'
ORDER BY sequence_name;

-- ============================================================================
-- 12. VIEWS
-- ============================================================================
SELECT
    '12_VIEWS' as check_type,
    table_schema,
    table_name as view_name,
    view_definition
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;

-- ============================================================================
-- 13. ENUMS (Custom Types)
-- ============================================================================
SELECT
    '13_ENUMS' as check_type,
    n.nspname AS schema,
    t.typname AS type_name,
    e.enumlabel AS enum_value,
    e.enumsortorder
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY t.typname, e.enumsortorder;

-- ============================================================================
-- 14. DATA HASH COMPARISON (For critical tables)
-- ============================================================================
-- Generate MD5 hash of all data in key tables for comparison

-- Users/Roles
SELECT
    '14_DATA_HASH_user_profiles' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(full_name, '') || '|' ||
        COALESCE(is_active::text, '') || '|' ||
        COALESCE(role_id::text, ''),
        '|' ORDER BY id
    )) as data_hash
FROM user_profiles;

SELECT
    '14_DATA_HASH_roles' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(role_name, '') || '|' ||
        COALESCE(description, ''),
        '|' ORDER BY id
    )) as data_hash
FROM roles;

SELECT
    '14_DATA_HASH_modules' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(module_name, '') || '|' ||
        COALESCE(description, '') || '|' ||
        COALESCE(is_active::text, ''),
        '|' ORDER BY id
    )) as data_hash
FROM modules;

-- Inventory
SELECT
    '14_DATA_HASH_item_master' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(sku, '') || '|' ||
        COALESCE(item_name, '') || '|' ||
        COALESCE(category, ''),
        '|' ORDER BY id
    )) as data_hash
FROM item_master;

SELECT
    '14_DATA_HASH_inventory_categories' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(category_name, '') || '|' ||
        COALESCE(description, ''),
        '|' ORDER BY id
    )) as data_hash
FROM inventory_categories;

-- System Settings
SELECT
    '14_DATA_HASH_system_settings' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(setting_key, '') || '|' ||
        COALESCE(setting_value::text, '') || '|' ||
        COALESCE(data_type, '') || '|' ||
        COALESCE(category, ''),
        '|' ORDER BY id
    )) as data_hash
FROM system_settings
WHERE setting_key NOT IN ('supabase_url', 'supabase_service_key', 'telegram_bot_token'); -- Exclude secrets

-- Email Templates
SELECT
    '14_DATA_HASH_email_templates' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(template_key, '') || '|' ||
        COALESCE(name, ''),
        '|' ORDER BY id
    )) as data_hash
FROM email_templates;

-- API Keys (excluding actual keys)
SELECT
    '14_DATA_HASH_api_keys' as check_type,
    COUNT(*) as row_count,
    MD5(STRING_AGG(
        COALESCE(id::text, '') || '|' ||
        COALESCE(name, '') || '|' ||
        COALESCE(is_active::text, ''),
        '|' ORDER BY id
    )) as data_hash
FROM api_keys;

-- ============================================================================
-- 15. SUMMARY COMPARISON
-- ============================================================================
SELECT
    '15_SUMMARY' as check_type,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public') as total_columns,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'PRIMARY KEY') as primary_keys,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'FOREIGN KEY') as foreign_keys,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'UNIQUE') as unique_constraints,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public' AND constraint_type = 'CHECK') as check_constraints,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    (SELECT COUNT(*) FROM information_schema.triggers WHERE event_object_schema = 'public') as total_triggers,
    (SELECT COUNT(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public' AND p.prokind = 'f') as total_functions;

-- ============================================================================
-- 16. COMPLETION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'DATABASE COMPARISON SCRIPT COMPLETED';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Run this same script on both databases and compare the outputs.';
    RAISE NOTICE 'Pay special attention to:';
    RAISE NOTICE '  - Table counts and row counts';
    RAISE NOTICE '  - Schema differences (columns, types)';
    RAISE NOTICE '  - Constraint differences';
    RAISE NOTICE '  - Data hashes (section 14)';
    RAISE NOTICE '============================================';
END $$;
