-- ============================================================================
-- Add Label Generator Module to B2C Operations
-- ============================================================================
-- Description: Adds Label Generator as a sub-module of B2C Operations
-- Version: 1.0.0
-- Created: 2025-12-01
-- ============================================================================

-- Add Label Generator sub-module
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'label_generator', 
    'Label Generator', 
    'Generate printable shipping labels from Excel/CSV', 
    'LocalShipping', 
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'), 
    true, 
    20
) ON CONFLICT (module_key) DO NOTHING;

-- Verify insertion
SELECT 
    m.module_key,
    m.module_name,
    m.description,
    p.module_name as parent_module
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key = 'label_generator';
