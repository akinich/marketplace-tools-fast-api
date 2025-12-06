
-- GRN Management Module (Module 1.2)
-- Migration 023

-- Table: grns
CREATE TABLE IF NOT EXISTS grns (
    id SERIAL PRIMARY KEY,
    grn_number VARCHAR(50) UNIQUE NOT NULL,  -- e.g., GRN-001, GRN-002
    po_id INTEGER NOT NULL REFERENCES purchase_orders(id),
    batch_id INTEGER NOT NULL REFERENCES batches(id),  -- Auto-generated at GRN creation
    
    -- Transport details
    transport_method VARCHAR(50),  -- Truck, Tempo, Farm Vehicle, Other
    number_of_boxes INTEGER,
    receiving_time TIME,
    receiving_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Status values: draft, completed, locked
    
    -- Personnel
    receiver_id UUID REFERENCES auth.users(id),  -- User who physically received
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_grn_po ON grns(po_id);
CREATE INDEX IF NOT EXISTS idx_grn_batch ON grns(batch_id);
CREATE INDEX IF NOT EXISTS idx_grn_status ON grns(status);
CREATE INDEX IF NOT EXISTS idx_grn_date ON grns(receiving_date);

-- Sequence for GRN numbering
CREATE SEQUENCE IF NOT EXISTS grn_number_seq START 1;

-- Table: grn_items
CREATE TABLE IF NOT EXISTS grn_items (
    id SERIAL PRIMARY KEY,
    grn_id INTEGER NOT NULL REFERENCES grns(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES zoho_items(id),
    
    -- Quantities
    gross_received DECIMAL(10, 3) NOT NULL DEFAULT 0,  -- Total received
    damage DECIMAL(10, 3) NOT NULL DEFAULT 0,          -- Damaged quantity
    reject DECIMAL(10, 3) NOT NULL DEFAULT 0,          -- Rejected quantity
    final_accepted DECIMAL(10, 3) NOT NULL DEFAULT 0,  -- Auto-calculated
    
    -- Cost allocation for damage/reject
    damage_cost_allocation VARCHAR(10),  -- 'farm' or 'us'
    reject_cost_allocation VARCHAR(10),  -- 'farm' or 'us'
    
    notes TEXT,
    added_to_po BOOLEAN DEFAULT FALSE,  -- For extra items
    
    CONSTRAINT valid_quantities CHECK (
        final_accepted = gross_received - damage - reject
        AND gross_received >= 0
        AND damage >= 0
        AND reject >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_grn_items_grn ON grn_items(grn_id);
CREATE INDEX IF NOT EXISTS idx_grn_items_item ON grn_items(item_id);

-- Table: grn_photos
CREATE TABLE IF NOT EXISTS grn_photos (
    id SERIAL PRIMARY KEY,
    grn_id INTEGER NOT NULL REFERENCES grns(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES zoho_items(id),
    
    -- Photo details
    photo_type VARCHAR(20) NOT NULL,  -- 'damage' or 'reject'
    photo_url TEXT NOT NULL,          -- Supabase Storage URL
    photo_path TEXT NOT NULL,         -- Storage path for deletion
    
    -- Metadata
    uploaded_by UUID NOT NULL REFERENCES auth.users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    file_size INTEGER,                -- Bytes
    gps_coordinates POINT,            -- PostGIS point type (optional)
    
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_grn_photos_grn ON grn_photos(grn_id);
CREATE INDEX IF NOT EXISTS idx_grn_photos_type ON grn_photos(photo_type);

-- Table: grn_edit_history
CREATE TABLE IF NOT EXISTS grn_edit_history (
    id SERIAL PRIMARY KEY,
    grn_id INTEGER NOT NULL REFERENCES grns(id) ON DELETE CASCADE,
    
    -- What changed
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    
    -- Who and when
    edited_by UUID NOT NULL REFERENCES auth.users(id),
    edited_at TIMESTAMP DEFAULT NOW(),
    
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_grn_history_grn ON grn_edit_history(grn_id);

-- Module Registration
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'grn_management',
    'GRN Management',
    'Goods receiving, batch assignment, and wastage documentation',
    'Inventory',
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    30
)
ON CONFLICT (module_key) DO UPDATE SET
    module_name = EXCLUDED.module_name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    parent_module_id = EXCLUDED.parent_module_id,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order;
