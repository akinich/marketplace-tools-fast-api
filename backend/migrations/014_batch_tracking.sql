-- ============================================================================
-- Migration 014: Batch Tracking Module
-- Description: Creates tables for complete batch traceability from farm to customer
-- Author: Claude
-- Date: 2024-12-04
-- ============================================================================

-- ============================================================================
-- TABLE: batches
-- Description: Master table for batch tracking with complete traceability
-- ============================================================================

CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    batch_number VARCHAR(50) UNIQUE NOT NULL, -- B001, B002, B003, etc.

    -- Batch Type
    is_repacked BOOLEAN DEFAULT FALSE, -- TRUE if this is a repacked batch (B###R)
    parent_batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL, -- Link to original batch if repacked

    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'ordered', -- ordered, received, in_grading, in_packing, in_inventory, allocated, in_transit, delivered, archived

    -- Linked Documents
    po_id INTEGER, -- Link to purchase_orders table (when implemented)
    grn_id INTEGER, -- Link to grns table (when implemented)

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE, -- When batch moves to historical archive (3 days after delivery)

    -- Audit
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_repack_parent CHECK (
        (is_repacked = FALSE AND parent_batch_id IS NULL) OR
        (is_repacked = TRUE AND parent_batch_id IS NOT NULL)
    )
);

CREATE INDEX idx_batches_batch_number ON batches(batch_number);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_batches_created_at ON batches(created_at DESC);
CREATE INDEX idx_batches_parent_batch ON batches(parent_batch_id);
CREATE INDEX idx_batches_is_repacked ON batches(is_repacked);
CREATE INDEX idx_batches_po_id ON batches(po_id);
CREATE INDEX idx_batches_grn_id ON batches(grn_id);

COMMENT ON TABLE batches IS 'Master table for batch tracking and traceability';
COMMENT ON COLUMN batches.batch_number IS 'Sequential batch number (B001, B002...) or repacked (B001R)';
COMMENT ON COLUMN batches.is_repacked IS 'TRUE if batch was created from repacking damaged items';
COMMENT ON COLUMN batches.parent_batch_id IS 'Original batch ID if this is a repacked batch';

-- ============================================================================
-- TABLE: batch_history
-- Description: Complete audit trail of all events in batch lifecycle
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch_history (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Event Details
    stage VARCHAR(50) NOT NULL, -- po, grn, grading, packing, inventory, allocation, delivery
    event_type VARCHAR(100) NOT NULL, -- created, received, graded, packed, allocated, delivered, status_changed, etc.
    event_details JSONB, -- Flexible storage for stage-specific data

    -- Status Change
    old_status VARCHAR(50),
    new_status VARCHAR(50),

    -- Timestamps & User
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Location
    location VARCHAR(100) -- receiving_area, processing_area, packed_warehouse, vehicle, etc.
);

CREATE INDEX idx_batch_history_batch_id ON batch_history(batch_id);
CREATE INDEX idx_batch_history_stage ON batch_history(stage);
CREATE INDEX idx_batch_history_created_at ON batch_history(created_at DESC);

COMMENT ON TABLE batch_history IS 'Complete audit trail of batch journey through all stages';
COMMENT ON COLUMN batch_history.event_details IS 'JSON data specific to each stage (quantities, grades, allocations, etc.)';

-- ============================================================================
-- TABLE: batch_documents
-- Description: Links batches to related documents (PO, GRN, SO, Invoices)
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch_documents (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Document Type & ID
    document_type VARCHAR(50) NOT NULL, -- po, grn, so, invoice, packing_label
    document_id INTEGER NOT NULL, -- Foreign key to respective tables
    document_number VARCHAR(100), -- Human-readable reference (PO-001, GRN-001, etc.)

    -- Timestamps
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    linked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

CREATE INDEX idx_batch_documents_batch_id ON batch_documents(batch_id);
CREATE INDEX idx_batch_documents_document_type ON batch_documents(document_type);
CREATE INDEX idx_batch_documents_document_id ON batch_documents(document_type, document_id);

COMMENT ON TABLE batch_documents IS 'Links batches to all related documents for quick reference';

-- ============================================================================
-- TABLE: batch_sequence
-- Description: Sequence counter for generating batch numbers (thread-safe)
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch_sequence (
    id SERIAL PRIMARY KEY,
    current_number INTEGER NOT NULL DEFAULT 0,
    prefix VARCHAR(10) DEFAULT 'B',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial record
INSERT INTO batch_sequence (current_number, prefix) VALUES (0, 'B')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE batch_sequence IS 'Sequence generator for batch numbers (atomic increments)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('batches', 'batch_history', 'batch_documents', 'batch_sequence')
ORDER BY table_name;

-- Verify indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('batches', 'batch_history', 'batch_documents', 'batch_sequence')
ORDER BY tablename, indexname;

-- Verify batch_sequence initialized
SELECT * FROM batch_sequence;
