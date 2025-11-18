/*
================================================================================
Verify and Fix User Permissions
================================================================================
Run this to check your admin user's role and fix any permission issues
================================================================================
*/

-- Step 1: Check your user's role
SELECT
    up.id,
    au.email,
    up.full_name,
    r.role_name,
    up.is_active
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
LEFT JOIN roles r ON r.id = up.role_id
ORDER BY up.created_at;

-- Expected: You should see role_name = 'Admin' for your account


-- Step 2: Check available modules (should show all modules including sub-modules)
SELECT
    id,
    module_key,
    module_name,
    parent_module_id,
    is_active,
    display_order
FROM modules
ORDER BY parent_module_id NULLS FIRST, display_order;

-- Expected: Should see ~14 modules total (dashboard, admin, inventory, biofloc + 11 inventory sub-modules)


-- Step 3: Test the view for your user (replace 'YOUR_USER_ID' with your actual user ID from Step 1)
-- SELECT * FROM user_accessible_modules WHERE user_id = 'YOUR_USER_ID' ORDER BY display_order;


-- Step 4: If you're an Admin but still not seeing modules, grant explicit permissions as a workaround
-- Replace 'YOUR_USER_ID' and 'YOUR_ADMIN_ID' below:

/*
DO $$
DECLARE
    target_user_id UUID := 'YOUR_USER_ID';  -- Replace with your user ID
    admin_user_id UUID := 'YOUR_ADMIN_ID';  -- Same as above if you're granting to yourself
BEGIN
    -- Grant permission to all top-level modules
    INSERT INTO user_module_permissions (user_id, module_id, can_access, granted_by, granted_at)
    SELECT
        target_user_id,
        id,
        TRUE,
        admin_user_id,
        NOW()
    FROM modules
    WHERE parent_module_id IS NULL AND module_key != 'dashboard'
    ON CONFLICT (user_id, module_id)
    DO UPDATE SET can_access = TRUE, granted_at = NOW();

    RAISE NOTICE 'Granted permissions to all top-level modules for user';
END $$;
*/


-- Step 5: Verify role names are correct
SELECT role_name FROM roles;

-- Expected: Should see 'Admin' and 'User' (case-sensitive!)
-- If you see 'admin' (lowercase), update it:
-- UPDATE roles SET role_name = 'Admin' WHERE LOWER(role_name) = 'admin';
