-- Add MRP Label Generator Module
-- Parent: B2C Ops (b2c_ops)

INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'mrp_label_generator', 
    'MRP Label Generator', 
    'Merge product label PDFs based on Excel quantity', 
    'PictureAsPdf', 
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'), 
    true, 
    30
) ON CONFLICT (module_key) DO UPDATE SET 
    module_name = 'MRP Label Generator',
    description = 'Merge product label PDFs based on Excel quantity',
    icon = 'PictureAsPdf',
    display_order = 30;
