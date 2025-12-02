-- ============================================================================
-- Migration: Add Zoho Customer Master Module
-- Description: Creates zoho_customers table and module
-- ============================================================================

BEGIN;

-- 1. Create zoho_customers table
CREATE TABLE IF NOT EXISTS zoho_customers (
    id SERIAL PRIMARY KEY,
    contact_id BIGINT UNIQUE NOT NULL, -- Zoho's unique contact ID

    -- Basic Information
    contact_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),

    -- Contact Person
    contact_person VARCHAR(255),

    -- Address
    billing_address TEXT,
    shipping_address TEXT,

    -- Business Details
    payment_terms INTEGER, -- Days
    payment_terms_label VARCHAR(100),
    customer_type VARCHAR(50), -- business, individual
    status VARCHAR(50) DEFAULT 'active', -- active, inactive

    -- Tax Information
    gst_no VARCHAR(50), -- GST Number
    gst_treatment VARCHAR(50), -- business_gst, overseas, consumer, etc.
    pan_no VARCHAR(50), -- PAN Number
    tax_id VARCHAR(100),
    place_of_contact VARCHAR(100),
    is_taxable BOOLEAN DEFAULT TRUE,

    -- Financial
    outstanding_receivable_amount DECIMAL(15, 2) DEFAULT 0,
    unused_credits DECIMAL(15, 2) DEFAULT 0,
    credit_limit DECIMAL(15, 2) DEFAULT 0,

    -- Contact Type
    contact_type VARCHAR(50) DEFAULT 'customer', -- customer

    -- Notes (User Editable)
    notes TEXT,

    -- Timestamps from Zoho
    created_time TIMESTAMP WITH TIME ZONE,
    last_modified_time TIMESTAMP WITH TIME ZONE,

    -- Our Timestamps
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Store full Zoho response for reference
    raw_json JSONB
);

-- Create indexes for faster search
CREATE INDEX IF NOT EXISTS idx_zoho_customers_contact_id ON zoho_customers(contact_id);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_contact_name ON zoho_customers(contact_name);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_company_name ON zoho_customers(company_name);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_email ON zoho_customers(email);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_status ON zoho_customers(status);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_customer_type ON zoho_customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_zoho_customers_gst_no ON zoho_customers(gst_no);

-- 2. Register Zoho Customer Master module under Database Management
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
    (SELECT id FROM modules WHERE module_key = 'database_management'),
    true,
    22
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Zoho Customer Master',
    description = 'Manage customers from Zoho Books, sync and view master data',
    icon = 'People',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'database_management'),
    display_order = 22;

COMMIT;
