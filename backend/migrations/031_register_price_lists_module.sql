-- ================================================================================
-- Migration 031: Register Customer Price Lists Module in Navigation
-- ================================================================================
-- Description:
--   Registers the Customer Price Lists module as a sub-module of Outward Operations
--   in the sidebar navigation system.
-- ================================================================================

-- Get the Outward parent module ID
DO $$
DECLARE
    v_outward_module_id INTEGER;
    v_max_display_order INTEGER;
BEGIN
    -- Get outward module ID
    SELECT id INTO v_outward_module_id
    FROM modules
    WHERE module_key = 'outward';

    IF v_outward_module_id IS NULL THEN
        RAISE EXCEPTION 'Outward module not found!';
    END IF;

    -- Get current max display order for outward sub-modules
    SELECT COALESCE(MAX(display_order), 0) INTO v_max_display_order
    FROM modules
    WHERE parent_module_id = v_outward_module_id;

    -- Insert the Price Lists module
    INSERT INTO modules (
        module_key,
        module_name,
        description,
        icon,
        display_order,
        is_active,
        parent_module_id
    )
    VALUES (
        'price_lists',
        'Customer Price Lists',
        'Manage bulk customer pricing with date-based validity, Excel import/export, and price history tracking',
        'AttachMoney',
        v_max_display_order + 1,
        TRUE,
        v_outward_module_id
    )
    ON CONFLICT (module_key) DO NOTHING;

    RAISE NOTICE 'Customer Price Lists module registered successfully under Outward Operations';
END $$;

-- ================================================================================
-- Verification Query
-- ================================================================================
-- Run this to verify the module was registered:
-- SELECT m.id, m.module_key, m.module_name, m.display_order, p.module_name as parent
-- FROM modules m
-- LEFT JOIN modules p ON m.parent_module_id = p.id
-- WHERE m.module_key = 'price_lists';
-- ================================================================================
