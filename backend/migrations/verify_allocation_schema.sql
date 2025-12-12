-- ================================================================================
-- Allocation Tables Schema Verification Script
-- ================================================================================
-- Purpose: Get complete schema details for all allocation-related tables
-- Run this on Supabase and share the output for verification
-- ================================================================================

-- Section 1: Tables and Columns
SELECT 
    'TABLES_AND_COLUMNS' as section,
    t.table_name,
    c.column_name,
    c.ordinal_position,
    c.data_type,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.is_nullable,
    c.column_default,
    c.is_generated,
    c.generation_expression
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_name IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
ORDER BY t.table_name, c.ordinal_position;

-- Section 2: Constraints (Primary Keys, Foreign Keys, Checks, Unique)
SELECT 
    'CONSTRAINTS' as section,
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage ccu 
    ON tc.constraint_name = ccu.constraint_name
LEFT JOIN information_schema.check_constraints cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
AND tc.table_name IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

-- Section 3: Indexes
SELECT 
    'INDEXES' as section,
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
ORDER BY tablename, indexname;

-- Section 4: Triggers
SELECT 
    'TRIGGERS' as section,
    trigger_schema,
    event_object_table as table_name,
    trigger_name,
    event_manipulation,
    action_timing,
    action_orientation,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND event_object_table IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
ORDER BY event_object_table, trigger_name;

-- Section 5: Functions used by triggers
SELECT 
    'FUNCTIONS' as section,
    routine_name,
    routine_definition
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN (
    'update_allocation_sheet_updated_at',
    'increment_cell_version',
    'log_cell_changes'
)
ORDER BY routine_name;

-- Section 6: Table Comments
SELECT 
    'TABLE_COMMENTS' as section,
    c.relname as table_name,
    obj_description(c.oid) as table_comment
FROM pg_class c
WHERE c.relnamespace = 'public'::regnamespace
AND c.relname IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
ORDER BY c.relname;

-- Section 7: Column Comments
SELECT 
    'COLUMN_COMMENTS' as section,
    c.table_name,
    c.column_name,
    pgd.description as column_comment
FROM pg_catalog.pg_statio_all_tables st
JOIN information_schema.columns c ON c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd ON (
    pgd.objoid = st.relid 
    AND pgd.objsubid = c.ordinal_position
)
WHERE c.table_schema = 'public'
AND c.table_name IN ('allocation_sheets', 'allocation_sheet_cells', 'allocation_sheet_audit')
AND pgd.description IS NOT NULL
ORDER BY c.table_name, c.ordinal_position;

-- Section 8: Row Counts (for reference)
SELECT 
    'ROW_COUNTS' as section,
    'allocation_sheets' as table_name,
    COUNT(*) as row_count
FROM allocation_sheets
UNION ALL
SELECT 
    'ROW_COUNTS',
    'allocation_sheet_cells',
    COUNT(*)
FROM allocation_sheet_cells
UNION ALL
SELECT 
    'ROW_COUNTS',
    'allocation_sheet_audit',
    COUNT(*)
FROM allocation_sheet_audit;
