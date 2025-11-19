-- ============================================================================
-- Biofloc Module - Grading & Batch Splitting Migration
-- ============================================================================
-- Version: 1.0.1
-- Created: 2025-11-19
-- Description: Adds grading functionality with batch splitting support (Option B)
-- ============================================================================

-- Add 'graded' status to batch_status enum
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'batch_status' AND e.enumlabel = 'graded'
    ) THEN
        ALTER TYPE batch_status ADD VALUE 'graded';
    END IF;
END $$;

-- Create grading_records table
CREATE TABLE IF NOT EXISTS biofloc_grading_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    source_batch_code VARCHAR(50) NOT NULL,
    source_tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    grading_date DATE NOT NULL,
    total_fish_graded INT NOT NULL,
    size_groups_count INT NOT NULL CHECK (size_groups_count BETWEEN 2 AND 3),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,

    -- Metadata
    CONSTRAINT valid_fish_count CHECK (total_fish_graded > 0)
);

-- Create grading_size_groups table (detailed size group information)
CREATE TABLE IF NOT EXISTS biofloc_grading_size_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grading_record_id UUID NOT NULL REFERENCES biofloc_grading_records(id) ON DELETE CASCADE,
    size_label VARCHAR(10) NOT NULL, -- A, B, C
    child_batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    child_batch_code VARCHAR(50) NOT NULL,
    fish_count INT NOT NULL,
    avg_weight_g DECIMAL(10,2) NOT NULL,
    biomass_kg DECIMAL(12,3) NOT NULL,
    destination_tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    destination_tank_code VARCHAR(50) NOT NULL,

    -- Feed cost allocation (proportional from parent)
    allocated_feed_cost DECIMAL(12,2) DEFAULT 0,
    biomass_percentage DECIMAL(5,2), -- % of total biomass

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_fish_count CHECK (fish_count > 0),
    CONSTRAINT valid_avg_weight CHECK (avg_weight_g > 0),
    CONSTRAINT valid_biomass CHECK (biomass_kg > 0)
);

-- Add parent_batch_id column to biofloc_batches (for tracking parent-child relationships)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'biofloc_batches' AND column_name = 'parent_batch_id'
    ) THEN
        ALTER TABLE biofloc_batches ADD COLUMN parent_batch_id UUID REFERENCES biofloc_batches(id);
        ALTER TABLE biofloc_batches ADD COLUMN parent_batch_code VARCHAR(50);
        ALTER TABLE biofloc_batches ADD COLUMN grading_date DATE;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_grading_records_source_batch ON biofloc_grading_records(source_batch_id);
CREATE INDEX IF NOT EXISTS idx_grading_records_date ON biofloc_grading_records(grading_date);
CREATE INDEX IF NOT EXISTS idx_grading_size_groups_grading ON biofloc_grading_size_groups(grading_record_id);
CREATE INDEX IF NOT EXISTS idx_grading_size_groups_child_batch ON biofloc_grading_size_groups(child_batch_id);
CREATE INDEX IF NOT EXISTS idx_batches_parent ON biofloc_batches(parent_batch_id);

-- Add comments
COMMENT ON TABLE biofloc_grading_records IS 'Records of batch grading events where batches are split by size';
COMMENT ON TABLE biofloc_grading_size_groups IS 'Detailed information about each size group created during grading';
COMMENT ON COLUMN biofloc_batches.parent_batch_id IS 'For child batches created via grading, references the parent batch';
COMMENT ON COLUMN biofloc_batches.grading_date IS 'Date when this batch was created via grading (for child batches)';

-- Grant permissions (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE ON biofloc_grading_records TO farm_app_user;
-- GRANT SELECT, INSERT, UPDATE ON biofloc_grading_size_groups TO farm_app_user;
