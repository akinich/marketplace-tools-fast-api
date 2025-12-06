-- ================================================================================
-- Migration 017: Wastage Tracking Module - Module Registration
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-06
-- Description: Registers Wastage Tracking module in the modules table
-- ================================================================================

-- Register Wastage Tracking Module under Inventory parent
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'wastage_tracking',
    'Wastage Tracking & Analytics',
    'Centralized wastage tracking with photo documentation and cost analysis',
    'AssessmentOutlined',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    20
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Wastage Tracking & Analytics',
    description = 'Centralized wastage tracking with photo documentation and cost analysis',
    display_order = 20,
    is_active = true;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 017: Wastage Tracking module registered successfully';
END $$;
