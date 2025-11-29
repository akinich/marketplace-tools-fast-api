-- ============================================================================
-- QUICKFIX: Add password_hash to user_profiles for akinich@gmail.com
-- ============================================================================
-- Run this in Supabase SQL Editor RIGHT NOW
-- ============================================================================

-- Make sure password_hash column exists
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Update password_hash for your user
UPDATE user_profiles
SET password_hash = crypt('Akhil@1996', gen_salt('bf'))
WHERE id = '3867eb67-c1b2-463c-b3c7-5457127d64b9';

-- Verify it worked
SELECT
    up.id,
    up.full_name,
    r.role_name,
    up.is_active,
    CASE
        WHEN up.password_hash IS NOT NULL THEN '✅ Password Set'
        ELSE '❌ Missing Password'
    END as password_status
FROM user_profiles up
LEFT JOIN roles r ON up.role_id = r.id
WHERE up.id = '3867eb67-c1b2-463c-b3c7-5457127d64b9';

-- ============================================================================
-- DONE! You can now login with:
-- Email: akinich@gmail.com
-- Password: Akhil@1996
-- ============================================================================
