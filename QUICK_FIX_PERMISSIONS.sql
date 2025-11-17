/*
===================================================================================
QUICK FIX: Grant Full Access to Admin User
===================================================================================
Run this SQL in Supabase SQL Editor to fix permission issues

This script will:
1. Fix role name capitalization if needed
2. Grant your admin user access to ALL modules (top-level + sub-modules)
3. Recreate the permission view with simplified logic

IMPORTANT: Replace 'YOUR_EMAIL_HERE' with your actual email address
===================================================================================
*/

-- STEP 1: Fix role name capitalization
UPDATE roles SET role_name = 'Admin' WHERE LOWER(role_name) = 'admin' AND role_name != 'Admin';
UPDATE roles SET role_name = 'User' WHERE LOWER(role_name) = 'user' AND role_name != 'User';

RAISE NOTICE 'Role names fixed';


-- STEP 2: Grant your admin user access to ALL modules
-- REPLACE 'YOUR_EMAIL_HERE' with your actual email (e.g., 'your@email.com')
DO $$
DECLARE
    v_user_id UUID;
    v_module_record RECORD;
BEGIN
    -- Get user ID from email (CHANGE THIS EMAIL!)
    SELECT id INTO v_user_id
    FROM auth.users
    WHERE email = 'akinich@gmail.com';  -- ← CHANGE THIS!

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'User not found. Check the email address!';
    END IF;

    RAISE NOTICE 'Granting permissions to user: %', v_user_id;

    -- Delete existing permissions for this user
    DELETE FROM user_module_permissions WHERE user_id = v_user_id;

    -- Grant access to ALL modules (top-level and sub-modules)
    FOR v_module_record IN
        SELECT id FROM modules WHERE is_active = TRUE AND module_key != 'dashboard'
    LOOP
        INSERT INTO user_module_permissions (user_id, module_id, can_access, granted_by, granted_at)
        VALUES (v_user_id, v_module_record.id, TRUE, v_user_id, NOW());
    END LOOP;

    RAISE NOTICE 'Granted permissions to % modules', (SELECT COUNT(*) FROM user_module_permissions WHERE user_id = v_user_id);
END $$;


-- STEP 3: Verify permissions were granted
-- REPLACE 'YOUR_EMAIL_HERE' again
SELECT
    u.email,
    m.module_key,
    m.module_name,
    m.parent_module_id,
    ump.can_access
FROM user_module_permissions ump
JOIN user_profiles up ON up.id = ump.user_id
JOIN auth.users u ON u.id = up.id
JOIN modules m ON m.id = ump.module_id
WHERE u.email = 'akinich@gmail.com'  -- ← CHANGE THIS!
ORDER BY m.parent_module_id NULLS FIRST, m.display_order;

-- You should see ALL modules listed here
