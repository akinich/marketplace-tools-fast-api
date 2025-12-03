-- ================================================================================
-- Reorder Database Management Modules
-- ================================================================================
-- Description: Updates display_order for database management modules
-- 
-- New Order:
--   1. WooCommerce Customer Master (display_order: 10)
--   2. WooCommerce Item Master (display_order: 11)
--   3. Zoho Customer Master (display_order: 12)
--   4. Zoho Item Master (display_order: 13)
--   5. Zoho Vendor Master (display_order: 14)
-- ================================================================================

-- Check current state
SELECT 
    module_key,
    module_name,
    display_order,
    parent_module_id
FROM modules
WHERE module_key IN (
    'woo_customer_master',
    'woo_item_master',
    'zoho_customer_master',
    'zoho_item_master',
    'zoho_vendor_master'
)
ORDER BY display_order;

-- Update display_order for database management modules
UPDATE modules SET display_order = 10 WHERE module_key = 'woo_customer_master';
UPDATE modules SET display_order = 11 WHERE module_key = 'woo_item_master';
UPDATE modules SET display_order = 12 WHERE module_key = 'zoho_customer_master';
UPDATE modules SET display_order = 13 WHERE module_key = 'zoho_item_master';
UPDATE modules SET display_order = 14 WHERE module_key = 'zoho_vendor_master';

-- Verify the changes
SELECT 
    module_key,
    module_name,
    display_order,
    parent_module_id
FROM modules
WHERE module_key IN (
    'woo_customer_master',
    'woo_item_master',
    'zoho_customer_master',
    'zoho_item_master',
    'zoho_vendor_master'
)
ORDER BY display_order;

-- Expected output:
-- woo_customer_master  | WooCommerce Customer Master | 10
-- woo_item_master      | WooCommerce Item Master     | 11
-- zoho_customer_master | Zoho Customer Master        | 12
-- zoho_item_master     | Zoho Item Master            | 13
-- zoho_vendor_master   | Zoho Vendor Master          | 14
