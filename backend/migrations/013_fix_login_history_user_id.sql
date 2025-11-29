-- ============================================================================
-- Migration 013: Fix login_history user_id to allow NULL for failed logins
-- ============================================================================
-- Created: 2025-11-28
-- Description: Make user_id nullable in login_history table to support
--              logging failed login attempts where user_id is unknown
-- ============================================================================

-- Make user_id nullable (allow NULL for failed login attempts)
ALTER TABLE login_history
ALTER COLUMN user_id DROP NOT NULL;

-- Drop the foreign key constraint
ALTER TABLE login_history
DROP CONSTRAINT IF EXISTS login_history_user_id_fkey;

-- Re-add the foreign key constraint without the NOT NULL requirement
-- This allows NULL user_id but validates the FK when user_id is provided
ALTER TABLE login_history
ADD CONSTRAINT login_history_user_id_fkey
FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;

-- Add a comment to explain this design choice
COMMENT ON COLUMN login_history.user_id IS
'User ID - can be NULL for failed login attempts where user is unknown (e.g., invalid email)';

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify the change:
-- SELECT column_name, is_nullable, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'login_history' AND column_name = 'user_id';
--
-- Expected result: is_nullable = 'YES'
-- ============================================================================
