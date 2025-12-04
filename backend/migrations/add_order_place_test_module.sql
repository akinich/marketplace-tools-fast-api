-- ============================================================================
-- Migration: Add Order Place Test Module
-- Description: Creates 'order_place_test' module under B2C Management parent
--              Adds wc_customer_id column to users table for WooCommerce mapping
-- ============================================================================

-- 1. Add wc_customer_id column to users table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'wc_customer_id'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN wc_customer_id INTEGER;
        RAISE NOTICE 'Added wc_customer_id column to user_profiles table';
    ELSE
        RAISE NOTICE 'wc_customer_id column already exists in user_profiles table';
    END IF;
END $$;

-- 2. Create Order Place Test Module under B2C Management
-- Note: WooCommerce API settings already exist from add_b2c_ops_module.sql
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'order_place_test', 
    'Order Place Test', 
    'Test WooCommerce order placement functionality', 
    'ShoppingBag', 
    (SELECT id FROM modules WHERE module_key = 'b2c_management'), 
    true, 
    30
) ON CONFLICT (module_key) DO NOTHING;

-- 3. Grant permissions to admin role for the new module
DO $$
DECLARE
    admin_role_id INTEGER;
    module_id INTEGER;
BEGIN
    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE role_name = 'admin';
    
    -- Get module ID
    SELECT id INTO module_id FROM modules WHERE module_key = 'order_place_test';
    
    -- Grant permission if both exist
    IF admin_role_id IS NOT NULL AND module_id IS NOT NULL THEN
        INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete)
        VALUES (admin_role_id, module_id, true, true, true)
        ON CONFLICT (role_id, module_id) DO NOTHING;
        
        RAISE NOTICE 'Granted admin permissions for order_place_test module';
    END IF;
END $$;

-- 4. Verify migration
DO $$
DECLARE
    module_count INTEGER;
    column_exists BOOLEAN;
BEGIN
    -- Check module was created
    SELECT COUNT(*) INTO module_count FROM modules WHERE module_key = 'order_place_test';
    
    -- Check column exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'wc_customer_id'
    ) INTO column_exists;
    
    IF module_count > 0 AND column_exists THEN
        RAISE NOTICE '✓ Migration completed successfully';
        RAISE NOTICE '  - order_place_test module created';
        RAISE NOTICE '  - wc_customer_id column exists in user_profiles table';
    ELSE
        RAISE WARNING 'Migration may have issues - please verify manually';
    END IF;
END $$;
