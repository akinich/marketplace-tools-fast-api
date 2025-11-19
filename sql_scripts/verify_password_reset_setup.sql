/*
================================================================================
Password Reset Verification Script
================================================================================
Run this in Supabase SQL Editor to verify your setup is correct
================================================================================
*/

-- ============================================================================
-- 1. CHECK ALL USERS EMAIL CONFIRMATION STATUS
-- ============================================================================
SELECT
    '=== USER EMAIL CONFIRMATION STATUS ===' as check_name;

SELECT
    au.id,
    au.email,
    au.email_confirmed_at,
    au.confirmed_at,
    au.created_at,
    CASE
        WHEN au.email_confirmed_at IS NULL THEN '❌ NOT CONFIRMED - WILL NOT RECEIVE RESET EMAILS'
        ELSE '✅ CONFIRMED - CAN RECEIVE RESET EMAILS'
    END as email_status,
    up.full_name,
    up.is_active,
    CASE
        WHEN up.is_active = FALSE THEN '⚠️ USER INACTIVE'
        ELSE '✅ USER ACTIVE'
    END as user_status
FROM auth.users au
LEFT JOIN user_profiles up ON up.id = au.id
ORDER BY au.created_at DESC;

-- ============================================================================
-- 2. COUNT USERS WITH ISSUES
-- ============================================================================
SELECT
    '=== SUMMARY ===' as check_name;

SELECT
    COUNT(*) as total_users,
    COUNT(CASE WHEN au.email_confirmed_at IS NULL THEN 1 END) as unconfirmed_users,
    COUNT(CASE WHEN au.email_confirmed_at IS NOT NULL THEN 1 END) as confirmed_users,
    COUNT(CASE WHEN up.is_active = FALSE THEN 1 END) as inactive_users
FROM auth.users au
LEFT JOIN user_profiles up ON up.id = au.id;

-- ============================================================================
-- 3. CHECK PASSWORD RESET TOKENS TABLE
-- ============================================================================
SELECT
    '=== RECENT PASSWORD RESET ATTEMPTS ===' as check_name;

SELECT
    prt.user_id,
    au.email,
    prt.created_at as reset_requested_at,
    prt.expires_at,
    prt.used,
    prt.used_at,
    CASE
        WHEN prt.used = TRUE THEN '✅ TOKEN USED'
        WHEN prt.expires_at < NOW() THEN '⏰ TOKEN EXPIRED'
        ELSE '⏳ TOKEN VALID'
    END as token_status
FROM password_reset_tokens prt
JOIN auth.users au ON au.id = prt.user_id
ORDER BY prt.created_at DESC
LIMIT 10;

-- ============================================================================
-- 4. CHECK FOR USERS CREATED RECENTLY (AFTER DEPLOYMENT)
-- ============================================================================
SELECT
    '=== RECENTLY CREATED USERS (LAST 24 HOURS) ===' as check_name;

SELECT
    au.email,
    up.full_name,
    au.created_at,
    au.email_confirmed_at,
    CASE
        WHEN au.email_confirmed_at IS NOT NULL THEN '✅ NEW USER SETUP CORRECT'
        ELSE '❌ NEW USER MISSING CONFIRMATION - CODE NOT DEPLOYED?'
    END as status
FROM auth.users au
LEFT JOIN user_profiles up ON up.id = au.id
WHERE au.created_at > NOW() - INTERVAL '24 hours'
ORDER BY au.created_at DESC;

-- ============================================================================
-- 5. FIX UNCONFIRMED USERS (IF ANY FOUND)
-- ============================================================================
-- Uncomment and run this section if Step 1 shows unconfirmed users:

/*
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;

-- Verify the fix:
SELECT
    COUNT(*) as fixed_users
FROM auth.users
WHERE email_confirmed_at IS NOT NULL;
*/
