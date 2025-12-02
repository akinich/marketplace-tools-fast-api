-- Check and fix Zoho Vendor & Customer Master modules in sidebar
-- Run this to add the modules to the database if they're missing

BEGIN;

-- First, check if modules exist
SELECT
    module_key,
    module_name,
    is_active,
    parent_module_id,
    display_order
FROM modules
WHERE module_key IN ('zoho_vendor_master', 'zoho_customer_master');

-- Get the parent module ID for Database Management
DO $$
DECLARE
    db_mgmt_id INTEGER;
BEGIN
    -- Get Database Management module ID
    SELECT id INTO db_mgmt_id
    FROM modules
    WHERE module_key = 'database_management';

    -- Insert or Update Zoho Vendor Master
    INSERT INTO modules (
        module_key,
        module_name,
        description,
        icon,
        parent_module_id,
        is_active,
        display_order
    ) VALUES (
        'zoho_vendor_master',
        'Zoho Vendor Master',
        'Manage vendors from Zoho Books, sync and view master data',
        'Store',
        db_mgmt_id,
        true,
        21
    ) ON CONFLICT (module_key) DO UPDATE SET
        module_name = 'Zoho Vendor Master',
        description = 'Manage vendors from Zoho Books, sync and view master data',
        icon = 'Store',
        parent_module_id = db_mgmt_id,
        is_active = true,
        display_order = 21;

    -- Insert or Update Zoho Customer Master
    INSERT INTO modules (
        module_key,
        module_name,
        description,
        icon,
        parent_module_id,
        is_active,
        display_order
    ) VALUES (
        'zoho_customer_master',
        'Zoho Customer Master',
        'Manage customers from Zoho Books, sync and view master data',
        'People',
        db_mgmt_id,
        true,
        22
    ) ON CONFLICT (module_key) DO UPDATE SET
        module_name = 'Zoho Customer Master',
        description = 'Manage customers from Zoho Books, sync and view master data',
        icon = 'People',
        parent_module_id = db_mgmt_id,
        is_active = true,
        display_order = 22;

    RAISE NOTICE 'Modules inserted/updated successfully!';
END $$;

-- Verify the modules are there
SELECT
    m.module_key,
    m.module_name,
    m.is_active,
    m.display_order,
    p.module_name as parent_module
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key IN ('zoho_vendor_master', 'zoho_customer_master')
ORDER BY m.display_order;

COMMIT;
