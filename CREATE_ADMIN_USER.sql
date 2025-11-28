-- ============================================================================
-- CREATE ADMIN USER: akinich@gmail.com
-- ============================================================================
-- Run this in Supabase SQL Editor to create/reset your admin account
-- ============================================================================

-- STEP 1: First, run the login_history fix if you haven't already
ALTER TABLE login_history ALTER COLUMN user_id DROP NOT NULL;

-- ============================================================================
-- STEP 2: Check if user exists
-- ============================================================================
DO $$
DECLARE
    user_exists BOOLEAN;
    user_uuid UUID;
    admin_role_id INTEGER;
BEGIN
    -- Check if user exists in auth.users
    SELECT EXISTS(
        SELECT 1 FROM auth.users WHERE email = 'akinich@gmail.com'
    ) INTO user_exists;

    IF user_exists THEN
        RAISE NOTICE 'User exists in auth.users, getting user ID...';
        SELECT id INTO user_uuid FROM auth.users WHERE email = 'akinich@gmail.com';
        RAISE NOTICE 'User ID: %', user_uuid;
    ELSE
        RAISE NOTICE 'User does NOT exist. Will create below.';
    END IF;

    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE role_name = 'Admin';
    RAISE NOTICE 'Admin role ID: %', admin_role_id;
END $$;

-- ============================================================================
-- STEP 3: Create the user if doesn't exist
-- ============================================================================
-- NOTE: This creates the user in Supabase Auth with the password you want
-- Password: Akhil@1996

DO $$
DECLARE
    new_user_id UUID;
    admin_role_id INTEGER;
BEGIN
    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE role_name = 'Admin';

    -- Check if user already exists
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE email = 'akinich@gmail.com') THEN
        -- Create user in auth.users using Supabase's internal function
        INSERT INTO auth.users (
            instance_id,
            id,
            aud,
            role,
            email,
            encrypted_password,
            email_confirmed_at,
            recovery_sent_at,
            last_sign_in_at,
            raw_app_meta_data,
            raw_user_meta_data,
            created_at,
            updated_at,
            confirmation_token,
            email_change,
            email_change_token_new,
            recovery_token
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            gen_random_uuid(),
            'authenticated',
            'authenticated',
            'akinich@gmail.com',
            crypt('Akhil@1996', gen_salt('bf')),  -- bcrypt hash of password
            NOW(),
            NOW(),
            NOW(),
            '{"provider":"email","providers":["email"]}',
            '{}',
            NOW(),
            NOW(),
            '',
            '',
            '',
            ''
        )
        RETURNING id INTO new_user_id;

        RAISE NOTICE 'Created user in auth.users with ID: %', new_user_id;

        -- Create user profile
        INSERT INTO user_profiles (id, full_name, role_id, is_active)
        VALUES (new_user_id, 'Akhil Kinich', admin_role_id, TRUE);

        RAISE NOTICE 'Created user profile for: akinich@gmail.com';

    ELSE
        RAISE NOTICE 'User already exists, updating password...';

        -- Update password for existing user
        UPDATE auth.users
        SET
            encrypted_password = crypt('Akhil@1996', gen_salt('bf')),
            email_confirmed_at = COALESCE(email_confirmed_at, NOW()),
            updated_at = NOW()
        WHERE email = 'akinich@gmail.com'
        RETURNING id INTO new_user_id;

        RAISE NOTICE 'Updated password for user ID: %', new_user_id;

        -- Make sure user profile exists and is active
        INSERT INTO user_profiles (id, full_name, role_id, is_active)
        VALUES (new_user_id, 'Akhil Kinich', admin_role_id, TRUE)
        ON CONFLICT (id) DO UPDATE
        SET is_active = TRUE,
            role_id = admin_role_id;

        RAISE NOTICE 'Ensured user profile is active and admin';
    END IF;

    -- Grant all module permissions
    INSERT INTO user_module_permissions (user_id, module_id, can_access)
    SELECT new_user_id, id, TRUE
    FROM modules
    ON CONFLICT (user_id, module_id) DO UPDATE
    SET can_access = TRUE;

    RAISE NOTICE 'Granted all module permissions';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'SUCCESS!';
    RAISE NOTICE 'Email: akinich@gmail.com';
    RAISE NOTICE 'Password: Akhil@1996';
    RAISE NOTICE 'Role: Admin';
    RAISE NOTICE 'Status: Active';
    RAISE NOTICE '========================================';
END $$;

-- ============================================================================
-- STEP 4: Verify the user was created/updated
-- ============================================================================
SELECT
    u.id,
    u.email,
    u.email_confirmed_at,
    u.created_at,
    up.full_name,
    r.role_name,
    up.is_active
FROM auth.users u
LEFT JOIN user_profiles up ON u.id = up.id
LEFT JOIN roles r ON up.role_id = r.id
WHERE u.email = 'akinich@gmail.com';

-- ============================================================================
-- DONE! You can now login with:
-- Email: akinich@gmail.com
-- Password: Akhil@1996
-- ============================================================================
