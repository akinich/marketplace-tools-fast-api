-- ================================================================================
-- Migration 016: Wastage Tracking Module - Database Tables
-- ================================================================================
-- Version: 1.0.0
-- Created: 2024-12-06
-- Description: Creates tables for wastage tracking, photo documentation,
--              repacking workflow, categories, and threshold alerts.
-- ================================================================================

-- ============================================================================
-- TABLE: wastage_events
-- ============================================================================
-- Primary table for all wastage events across the supply chain

CREATE TABLE IF NOT EXISTS wastage_events (
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE DEFAULT gen_random_uuid(),

    -- Batch & Stage
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL, -- receiving, grading, packing, cold_storage, customer
    wastage_type VARCHAR(100) NOT NULL, -- damage, reject, qc, overfill, partial_damage, full_loss, customer_claim

    -- Wastage Details
    item_id INTEGER, -- Link to items table (placeholder for future)
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL, -- Quantity wasted (kg, pcs, etc.)
    unit VARCHAR(50) NOT NULL, -- kg, pcs, boxes, etc.

    -- Cost Allocation
    cost_allocation VARCHAR(20) NOT NULL, -- 'farm' or 'us'
    estimated_cost DECIMAL(10, 2), -- Estimated cost of wastage (INR)

    -- Reason & Notes
    reason TEXT, -- Brief reason (dropdown selection)
    notes TEXT, -- Additional notes

    -- Location
    location VARCHAR(100), -- receiving_area, processing_area, cold_storage, vehicle, etc.

    -- Related Documents (placeholders for future)
    po_id INTEGER, -- Link to purchase_orders (when implemented)
    grn_id INTEGER, -- Link to grns (when implemented)
    so_id INTEGER, -- Link to sales_orders (when implemented)
    ticket_id INTEGER, -- Link to tickets (customer claims)

    -- Timestamps & User
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_cost_allocation CHECK (cost_allocation IN ('farm', 'us')),
    CONSTRAINT check_quantity_positive CHECK (quantity > 0)
);

CREATE INDEX idx_wastage_events_batch_id ON wastage_events(batch_id);
CREATE INDEX idx_wastage_events_stage ON wastage_events(stage);
CREATE INDEX idx_wastage_events_wastage_type ON wastage_events(wastage_type);
CREATE INDEX idx_wastage_events_cost_allocation ON wastage_events(cost_allocation);
CREATE INDEX idx_wastage_events_created_at ON wastage_events(created_at DESC);
CREATE INDEX idx_wastage_events_item_name ON wastage_events(item_name);

COMMENT ON TABLE wastage_events IS 'Centralized log of all wastage events across supply chain';
COMMENT ON COLUMN wastage_events.cost_allocation IS 'Who bears the cost: farm (deducted from invoice) or us (absorbed)';
COMMENT ON COLUMN wastage_events.estimated_cost IS 'Estimated cost impact in INR';


-- ============================================================================
-- TABLE: wastage_photos
-- ============================================================================
-- Photos documenting wastage events (mandatory for all wastage)

CREATE TABLE IF NOT EXISTS wastage_photos (
    id SERIAL PRIMARY KEY,
    wastage_event_id INTEGER NOT NULL REFERENCES wastage_events(id) ON DELETE CASCADE,

    -- Photo Details
    photo_url TEXT NOT NULL, -- Supabase Storage URL
    photo_path VARCHAR(500) NOT NULL, -- Path in Supabase bucket
    file_name VARCHAR(255) NOT NULL,
    file_size_kb INTEGER,

    -- Metadata
    gps_latitude DECIMAL(10, 8), -- GPS coordinates (if available from mobile)
    gps_longitude DECIMAL(11, 8),
    device_info VARCHAR(255), -- Camera/device used

    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_photo_url_not_empty CHECK (photo_url != '')
);

CREATE INDEX idx_wastage_photos_event_id ON wastage_photos(wastage_event_id);
CREATE INDEX idx_wastage_photos_uploaded_at ON wastage_photos(uploaded_at DESC);

COMMENT ON TABLE wastage_photos IS 'Photo documentation for all wastage events (mandatory)';


-- ============================================================================
-- TABLE: wastage_repacking
-- ============================================================================
-- Tracks repacking events when damaged items are consolidated

CREATE TABLE IF NOT EXISTS wastage_repacking (
    id SERIAL PRIMARY KEY,

    -- Parent & Child Batches
    parent_batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    child_batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Repacking Details
    wastage_event_id INTEGER REFERENCES wastage_events(id) ON DELETE SET NULL, -- Original damage event
    damaged_quantity DECIMAL(10, 2) NOT NULL,
    repacked_quantity DECIMAL(10, 2) NOT NULL,
    wastage_in_repacking DECIMAL(10, 2) DEFAULT 0, -- Additional wastage during repacking

    -- Reason & Notes
    reason TEXT NOT NULL,
    notes TEXT,

    -- Timestamps & User
    repacked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    repacked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_damaged_quantity_positive CHECK (damaged_quantity > 0),
    CONSTRAINT check_repacked_quantity_positive CHECK (repacked_quantity > 0),
    CONSTRAINT check_wastage_calculation CHECK (repacked_quantity <= damaged_quantity)
);

CREATE INDEX idx_wastage_repacking_parent_batch ON wastage_repacking(parent_batch_id);
CREATE INDEX idx_wastage_repacking_child_batch ON wastage_repacking(child_batch_id);
CREATE INDEX idx_wastage_repacking_wastage_event ON wastage_repacking(wastage_event_id);

COMMENT ON TABLE wastage_repacking IS 'Tracks repacking of damaged items into new batches';
COMMENT ON COLUMN wastage_repacking.wastage_in_repacking IS 'Additional wastage that occurred during repacking process';


-- ============================================================================
-- TABLE: wastage_categories
-- ============================================================================
-- Predefined wastage categories and reasons for dropdown selection

CREATE TABLE IF NOT EXISTS wastage_categories (
    id SERIAL PRIMARY KEY,
    stage VARCHAR(50) NOT NULL, -- receiving, grading, packing, cold_storage, customer
    wastage_type VARCHAR(100) NOT NULL, -- damage, reject, qc, overfill, etc.
    reason VARCHAR(255) NOT NULL, -- "Transport damage", "Quality below spec", etc.
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_wastage_categories_stage ON wastage_categories(stage);
CREATE INDEX idx_wastage_categories_wastage_type ON wastage_categories(wastage_type);

COMMENT ON TABLE wastage_categories IS 'Predefined wastage reasons for consistent categorization';

-- Insert default categories
INSERT INTO wastage_categories (stage, wastage_type, reason, description, display_order) VALUES
-- Receiving stage
('receiving', 'damage', 'Transport damage', 'Damaged during transportation from farm', 10),
('receiving', 'damage', 'Handling damage', 'Damaged during unloading/handling', 20),
('receiving', 'damage', 'Packaging damage', 'Damaged packaging leading to produce damage', 30),
('receiving', 'reject', 'Below quality spec', 'Quality does not meet minimum standards', 40),
('receiving', 'reject', 'Wrong variety', 'Farm sent wrong variety/type', 50),
('receiving', 'reject', 'Overripe', 'Produce is overripe and unsellable', 60),
('receiving', 'reject', 'Underripe', 'Produce is underripe and needs more time', 70),

-- Grading stage
('grading', 'qc', 'Size out of spec', 'Size does not meet customer requirements', 80),
('grading', 'qc', 'Color out of spec', 'Color not acceptable', 90),
('grading', 'qc', 'Blemishes', 'Surface blemishes/defects', 100),
('grading', 'qc', 'Internal damage', 'Damage found during inspection', 110),

-- Packing stage
('packing', 'overfill', 'Weight overfill', 'Packs weigh more than target (yield loss)', 120),
('packing', 'damage', 'Packing damage', 'Damaged during packing process', 130),

-- Cold storage stage
('cold_storage', 'partial_damage', 'Condensation damage', 'Moisture damage in storage', 140),
('cold_storage', 'partial_damage', 'Temperature fluctuation', 'Quality degradation due to temp issues', 150),
('cold_storage', 'partial_damage', 'Age degradation', 'Natural aging/shelf life expiry', 160),
('cold_storage', 'full_loss', 'Complete spoilage', 'Entire batch/pack spoiled', 170),
('cold_storage', 'full_loss', 'Contamination', 'Cross-contamination or pest damage', 180),

-- Customer stage
('customer', 'customer_claim', 'Arrived damaged', 'Customer received damaged goods', 190),
('customer', 'customer_claim', 'Quality complaint', 'Customer complaint about quality', 200),
('customer', 'customer_claim', 'Short shelf life', 'Produce expired too quickly', 210);


-- ============================================================================
-- TABLE: wastage_thresholds
-- ============================================================================
-- Configurable thresholds for wastage alerts (admin-configurable)

CREATE TABLE IF NOT EXISTS wastage_thresholds (
    id SERIAL PRIMARY KEY,

    -- Threshold Scope
    scope_type VARCHAR(50) NOT NULL, -- 'global', 'stage', 'farm', 'item'
    scope_value VARCHAR(255), -- NULL for global, farm name, item name, etc.

    -- Threshold Details
    stage VARCHAR(50), -- NULL for global, specific stage otherwise
    threshold_percentage DECIMAL(5, 2) NOT NULL, -- e.g., 5.00 = 5%
    alert_level VARCHAR(20) NOT NULL, -- 'critical', 'warning', 'info'

    -- Active/Inactive
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_threshold_positive CHECK (threshold_percentage > 0),
    CONSTRAINT check_alert_level CHECK (alert_level IN ('critical', 'warning', 'info'))
);

CREATE INDEX idx_wastage_thresholds_scope ON wastage_thresholds(scope_type, scope_value);
CREATE INDEX idx_wastage_thresholds_stage ON wastage_thresholds(stage);

COMMENT ON TABLE wastage_thresholds IS 'Configurable wastage thresholds for automated alerts';

-- Insert default thresholds
INSERT INTO wastage_thresholds (scope_type, stage, threshold_percentage, alert_level) VALUES
('global', 'receiving', 5.00, 'warning'),
('global', 'receiving', 10.00, 'critical'),
('global', 'grading', 10.00, 'warning'),
('global', 'grading', 15.00, 'critical'),
('global', 'packing', 5.00, 'warning'),
('global', 'cold_storage', 8.00, 'warning'),
('global', 'cold_storage', 12.00, 'critical');


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 016: Wastage Tracking tables created successfully';
END $$;
