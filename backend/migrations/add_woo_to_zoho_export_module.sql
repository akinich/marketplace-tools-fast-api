-- Add Woo to Zoho Export Module
-- Created: 2025-12-03

-- 1. Create export_history table
CREATE TABLE IF NOT EXISTS export_history (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL,
    invoice_prefix VARCHAR(20) NOT NULL,
    sequence_number INTEGER NOT NULL,
    order_id BIGINT NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE,
    customer_name VARCHAR(255),
    order_total DECIMAL(10, 2),
    
    -- Export Metadata
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    total_orders_in_export INTEGER,
    
    -- Audit
    exported_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster search
CREATE INDEX IF NOT EXISTS idx_export_history_invoice_prefix ON export_history(invoice_prefix);
CREATE INDEX IF NOT EXISTS idx_export_history_sequence_number ON export_history(sequence_number);
CREATE INDEX IF NOT EXISTS idx_export_history_order_date ON export_history(order_date);
CREATE INDEX IF NOT EXISTS idx_export_history_created_at ON export_history(created_at);

-- 2. Register module
INSERT INTO modules (
    module_key, 
    module_name, 
    description, 
    icon, 
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'woo_to_zoho_export',
    'Woo to Zoho Export',
    'Export WooCommerce orders to Zoho Books format with product mapping',
    'ImportExport',
    (SELECT id FROM modules WHERE module_key = 'b2c_ops'),
    true,
    30
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Woo to Zoho Export',
    description = 'Export WooCommerce orders to Zoho Books format with product mapping',
    icon = 'ImportExport',
    display_order = 30;
