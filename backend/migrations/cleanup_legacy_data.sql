-- ============================================================================
-- Cleanup Legacy Data Migration
-- ============================================================================
-- Description: Removes legacy data from database transfer
-- WARNING: This will permanently delete data. Review carefully before running.
-- ============================================================================

-- 1. Delete all tickets and related data
-- (Cascades to ticket_comments due to ON DELETE CASCADE)
DELETE FROM tickets;

-- 2. Delete all development features and related data
-- (Cascades to feature_steps and feature_comments due to ON DELETE CASCADE)
DELETE FROM features;

-- 3. Delete all biofloc module data (legacy data from deleted module)
-- Using error-safe blocks in case tables were already cleaned up
DO $$
BEGIN
    BEGIN DELETE FROM biofloc_cycle_costs; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_harvests; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_tank_inputs; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_water_tests; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_mortality; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_sampling; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_feeding_sessions; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_batch_tank_assignments; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_batches; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM biofloc_tanks; EXCEPTION WHEN undefined_table THEN NULL; END;
END $$;

-- 4. Delete all users EXCEPT akinich@gmail.com
-- First, get the user ID to preserve
DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    -- Get the admin user ID
    SELECT id INTO admin_user_id 
    FROM auth.users 
    WHERE email = 'akinich@gmail.com';
    
    IF admin_user_id IS NULL THEN
        RAISE EXCEPTION 'Admin user akinich@gmail.com not found!';
    END IF;
    
    RAISE NOTICE 'Preserving admin user: % (ID: %)', 'akinich@gmail.com', admin_user_id;
    
    -- Delete activity_logs for other users
    DELETE FROM activity_logs 
    WHERE user_id != admin_user_id;
    
    -- Delete user_module_permissions for other users
    DELETE FROM user_module_permissions 
    WHERE user_id != admin_user_id;
    
    -- Handle ALL inventory module tables (delete ALL records - legacy data)
    BEGIN DELETE FROM po_history; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM purchase_orders; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM item_master; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM items; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM categories; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM item_categories; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM vendors; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM suppliers; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM current_stock; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM inventory_items; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM stock; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM stock_adjustments; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM inventory_adjustments; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM stock_movements; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM inventory_movements; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM inventory_alerts; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM stock_alerts; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM inventory_history; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM stock_history; EXCEPTION WHEN undefined_table THEN NULL; END;
    
    -- Delete user sessions for other users
    DELETE FROM user_sessions 
    WHERE user_id != admin_user_id;
    
    -- Delete notification settings (delete all - they're user-specific)
    BEGIN
        DELETE FROM notification_settings;
    EXCEPTION WHEN undefined_table THEN NULL;
    END;
    
    -- Handle any other common tables that might reference users
    BEGIN DELETE FROM user_preferences WHERE user_id != admin_user_id; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM user_settings WHERE user_id != admin_user_id; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM audit_logs WHERE user_id != admin_user_id; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN DELETE FROM login_history WHERE user_id != admin_user_id; EXCEPTION WHEN undefined_table THEN NULL; END;
    
    -- Now safe to delete user_profiles for other users
    DELETE FROM user_profiles 
    WHERE id != admin_user_id;
    
    -- Delete from auth.users if it doesn't cascade
    DELETE FROM auth.users 
    WHERE id != admin_user_id;
    
    RAISE NOTICE 'Cleanup complete. Preserved user: akinich@gmail.com (ID: %)', admin_user_id;
END $$;

-- 5. Reset sequences (optional - ensures IDs start from 1 for new records)
DO $$
BEGIN
    BEGIN ALTER SEQUENCE tickets_id_seq RESTART WITH 1; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN ALTER SEQUENCE ticket_comments_id_seq RESTART WITH 1; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN ALTER SEQUENCE features_id_seq RESTART WITH 1; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN ALTER SEQUENCE feature_steps_id_seq RESTART WITH 1; EXCEPTION WHEN undefined_table THEN NULL; END;
    BEGIN ALTER SEQUENCE feature_comments_id_seq RESTART WITH 1; EXCEPTION WHEN undefined_table THEN NULL; END;
END $$;

-- 6. Verify cleanup
SELECT 'Tickets remaining:' as info, COUNT(*) as count FROM tickets
UNION ALL
SELECT 'Features remaining:', COUNT(*) FROM features
UNION ALL
SELECT 'Users remaining:', COUNT(*) FROM user_profiles
UNION ALL
SELECT 'Auth users remaining:', COUNT(*) FROM auth.users
UNION ALL
SELECT 'Activity logs remaining:', COUNT(*) FROM activity_logs
UNION ALL
SELECT 'User sessions remaining:', COUNT(*) FROM user_sessions;
