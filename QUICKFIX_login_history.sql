-- ============================================================================
-- QUICKFIX: Allow NULL user_id in login_history for failed login attempts
-- ============================================================================
-- Run this in Supabase SQL Editor NOW to fix the login error
-- ============================================================================

-- Make user_id nullable
ALTER TABLE login_history ALTER COLUMN user_id DROP NOT NULL;

-- Verify the fix
SELECT
    column_name,
    is_nullable,
    data_type
FROM information_schema.columns
WHERE table_name = 'login_history'
AND column_name = 'user_id';

-- Expected result: is_nullable should be 'YES'
