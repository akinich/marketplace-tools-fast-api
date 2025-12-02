-- ============================================================================
-- Migration: Rename Item Master to Woo Item Master and Move to Database Management
-- Description: Creates 'Database Management' parent module and moves renamed module
-- ============================================================================

BEGIN;

-- 1. Create Parent Module (Database Management)
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'database_management', 
    'Database Management', 
    'Manage master data and database operations', 
    'Storage', 
    NULL, 
    true, 
    35
) ON CONFLICT (module_key) DO NOTHING;

-- 2. Update existing Item Master module
-- Rename to "Woo Item Master" and move to Database Management parent
UPDATE modules 
SET 
    module_key = 'woo_item_master',
    module_name = 'Woo Item Master',
    description = 'Manage WooCommerce products, sync with WooCommerce, and edit master data',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'database_management'),
    display_order = 10
WHERE module_key = 'b2c_item_master';

-- 3. If the old key doesn't exist but we have the old name, update by name
-- This is a fallback in case module_key was different
UPDATE modules 
SET 
    module_key = 'woo_item_master',
    module_name = 'Woo Item Master',
    description = 'Manage WooCommerce products, sync with WooCommerce, and edit master data',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'database_management'),
    display_order = 10
WHERE module_name = 'Item Master' 
  AND module_key != 'woo_item_master'
  AND NOT EXISTS (SELECT 1 FROM modules WHERE module_key = 'woo_item_master');

COMMIT;
