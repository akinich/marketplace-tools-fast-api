-- ============================================================================
-- Communication Module Verification Script
-- ============================================================================
-- Description: Verifies that Communication module structure is properly set up
-- Author: System
-- Date: 2025-11-23
-- Version: 1.0.0
-- ============================================================================

-- This script checks if the Communication module migrations have been applied
-- Run this to verify the database state before deploying frontend changes

\echo '=========================='
\echo 'Communication Module Verification'
\echo '=========================='
\echo ''

-- Check 1: Communication parent module exists
\echo '1. Checking Communication parent module...'
SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM modules WHERE module_key = 'communication' AND parent_module_id IS NULL)
        THEN '✓ Communication parent module exists'
        ELSE '✗ ERROR: Communication parent module NOT found'
    END as status;

\echo ''
\echo '2. Checking Communication child modules...'
-- Check 2: All child modules exist
SELECT
    module_key,
    module_name,
    is_active,
    display_order,
    CASE
        WHEN parent_module_id IS NOT NULL THEN '✓ Has parent'
        ELSE '✗ Missing parent'
    END as parent_status
FROM modules
WHERE module_key IN ('com_telegram', 'com_smtp', 'com_webhooks', 'com_api_keys', 'com_websockets')
ORDER BY display_order;

\echo ''
\echo '3. Checking legacy telegram module...'
-- Check 3: Legacy telegram module renamed
SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM modules WHERE module_key = 'telegram_legacy')
        THEN '✓ Legacy telegram module renamed to telegram_legacy'
        WHEN EXISTS (SELECT 1 FROM modules WHERE module_key = 'telegram' AND is_active = false)
        THEN '⚠ Legacy telegram module exists but not renamed yet'
        ELSE '✓ No legacy telegram module found'
    END as status;

\echo ''
\echo '4. Full Communication module hierarchy:'
-- Check 4: Show full hierarchy
SELECT
    m.id,
    m.module_key,
    m.module_name,
    CASE
        WHEN m.parent_module_id IS NULL THEN 'PARENT'
        ELSE '  └─ CHILD'
    END as level,
    p.module_name as parent_name,
    m.display_order,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key = 'communication'
   OR m.parent_module_id = (SELECT id FROM modules WHERE module_key = 'communication')
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;

\echo ''
\echo '5. Checking admin user permissions...'
-- Check 5: Admin users have access to Communication modules
SELECT
    COUNT(DISTINCT ump.user_id) as admin_users_with_access,
    COUNT(DISTINCT m.id) as communication_modules_count
FROM user_module_permissions ump
JOIN modules m ON ump.module_id = m.id
JOIN user_profiles up ON ump.user_id = up.id
JOIN roles r ON up.role_id = r.id
WHERE r.role_name = 'Admin'
  AND (m.module_key = 'communication' OR m.parent_module_id = (SELECT id FROM modules WHERE module_key = 'communication'));

\echo ''
\echo '=========================='
\echo 'Verification Complete'
\echo '=========================='
\echo ''
\echo 'If any checks show errors, run these migrations in order:'
\echo '  1. backend/migrations/007_communication_module.sql'
\echo '  2. backend/migrations/007_communication_module_patch.sql'
\echo ''
