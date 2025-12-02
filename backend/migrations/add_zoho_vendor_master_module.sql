-- ============================================================================
-- Migration: Add Zoho Vendor Master Module
-- Description: Creates zoho_vendors table and module
-- ============================================================================

BEGIN;

-- 1. Create zoho_vendors table
CREATE TABLE IF NOT EXISTS zoho_vendors (
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
    status VARCHAR(50) DEFAULT 'active', -- active, inactive

    -- Tax Information
    gst_no VARCHAR(50), -- GST Number
    gst_treatment VARCHAR(50), -- business_gst, overseas, etc.
    pan_no VARCHAR(50), -- PAN Number
    tax_id VARCHAR(100),
    place_of_contact VARCHAR(100),
    is_taxable BOOLEAN DEFAULT TRUE,

    -- Financial
    outstanding_balance DECIMAL(15, 2) DEFAULT 0,
    unused_credits DECIMAL(15, 2) DEFAULT 0,

    -- Contact Type
    contact_type VARCHAR(50) DEFAULT 'vendor', -- vendor

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
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_contact_id ON zoho_vendors(contact_id);
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_contact_name ON zoho_vendors(contact_name);
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_company_name ON zoho_vendors(company_name);
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_email ON zoho_vendors(email);
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_status ON zoho_vendors(status);
CREATE INDEX IF NOT EXISTS idx_zoho_vendors_gst_no ON zoho_vendors(gst_no);

-- 2. Register Zoho Vendor Master module under Database Management
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
    (SELECT id FROM modules WHERE module_key = 'database_management'),
    true,
    21
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Zoho Vendor Master',
    description = 'Manage vendors from Zoho Books, sync and view master data',
    icon = 'Store',
    parent_module_id = (SELECT id FROM modules WHERE module_key = 'database_management'),
    display_order = 21;

COMMIT;
