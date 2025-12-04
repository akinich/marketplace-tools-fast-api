-- ============================================================================
-- Migration 014: Batch Tracking Module (CLEAN INSTALL)
-- Description: Complete cleanup and fresh installation with FY support
-- Author: Claude
-- Date: 2024-12-04
-- ============================================================================

-- ============================================================================
-- STEP 1: DROP ALL INDEXES (Explicitly)
-- ============================================================================

DROP INDEX IF EXISTS idx_batches_batch_number;
DROP INDEX IF EXISTS idx_batches_status;
DROP INDEX IF EXISTS idx_batches_created_at;
DROP INDEX IF EXISTS idx_batches_parent_batch;
DROP INDEX IF EXISTS idx_batches_is_repacked;
DROP INDEX IF EXISTS idx_batches_po_id;
DROP INDEX IF EXISTS idx_batches_grn_id;

DROP INDEX IF EXISTS idx_batch_history_batch_id;
DROP INDEX IF EXISTS idx_batch_history_stage;
DROP INDEX IF EXISTS idx_batch_history_created_at;

DROP INDEX IF EXISTS idx_batch_documents_batch_id;
DROP INDEX IF EXISTS idx_batch_documents_document_type;
DROP INDEX IF EXISTS idx_batch_documents_document_id;

-- ============================================================================
-- STEP 2: DROP ALL TABLES (with CASCADE)
-- ============================================================================

DROP TABLE IF EXISTS batch_documents CASCADE;
DROP TABLE IF EXISTS batch_history CASCADE;
DROP TABLE IF EXISTS batches CASCADE;
DROP TABLE IF EXISTS batch_sequence CASCADE;

-- ============================================================================
-- STEP 3: RECREATE TABLES WITH FY SUPPORT
-- ============================================================================

-- TABLE: batches
CREATE TABLE batches (
    id SERIAL PRIMARY KEY,
    batch_number VARCHAR(50) UNIQUE NOT NULL, -- B/2526/0001, B/2526/0002, etc.

    -- Batch Type
    is_repacked BOOLEAN DEFAULT FALSE,
    parent_batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,

    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'ordered',

    -- Linked Documents
    po_id INTEGER,
    grn_id INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_repack_parent CHECK (
        (is_repacked = FALSE AND parent_batch_id IS NULL) OR
        (is_repacked = TRUE AND parent_batch_id IS NOT NULL)
    )
);

-- TABLE: batch_history
CREATE TABLE batch_history (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Event Details
    stage VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_details JSONB,

    -- Status Change
    old_status VARCHAR(50),
    new_status VARCHAR(50),

    -- Timestamps & User
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Location
    location VARCHAR(100)
);

-- TABLE: batch_documents
CREATE TABLE batch_documents (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Document Type & ID
    document_type VARCHAR(50) NOT NULL,
    document_id INTEGER NOT NULL,
    document_number VARCHAR(100),

    -- Timestamps
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    linked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- TABLE: batch_sequence (with FY support)
CREATE TABLE batch_sequence (
    id SERIAL PRIMARY KEY,
    current_number INTEGER NOT NULL DEFAULT 0,
    prefix VARCHAR(10) DEFAULT 'B',
    financial_year VARCHAR(10) NOT NULL DEFAULT '2526',
    fy_start_date DATE NOT NULL DEFAULT '2025-04-01',
    fy_end_date DATE NOT NULL DEFAULT '2026-03-31',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- STEP 4: CREATE INDEXES
-- ============================================================================

-- Indexes for batches table
CREATE INDEX idx_batches_batch_number ON batches(batch_number);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_batches_created_at ON batches(created_at DESC);
CREATE INDEX idx_batches_parent_batch ON batches(parent_batch_id);
CREATE INDEX idx_batches_is_repacked ON batches(is_repacked);
CREATE INDEX idx_batches_po_id ON batches(po_id);
CREATE INDEX idx_batches_grn_id ON batches(grn_id);

-- Indexes for batch_history table
CREATE INDEX idx_batch_history_batch_id ON batch_history(batch_id);
CREATE INDEX idx_batch_history_stage ON batch_history(stage);
CREATE INDEX idx_batch_history_created_at ON batch_history(created_at DESC);

-- Indexes for batch_documents table
CREATE INDEX idx_batch_documents_batch_id ON batch_documents(batch_id);
CREATE INDEX idx_batch_documents_document_type ON batch_documents(document_type);
CREATE INDEX idx_batch_documents_document_id ON batch_documents(document_type, document_id);

-- ============================================================================
-- STEP 5: ADD COMMENTS
-- ============================================================================

COMMENT ON TABLE batches IS 'Master table for batch tracking with FY-based numbering';
COMMENT ON COLUMN batches.batch_number IS 'FY-based batch number: B/2526/0001 format';
COMMENT ON COLUMN batches.is_repacked IS 'TRUE if batch was created from repacking';
COMMENT ON COLUMN batches.parent_batch_id IS 'Original batch ID if this is a repacked batch';

COMMENT ON TABLE batch_history IS 'Complete audit trail of batch journey (5-day archive window)';
COMMENT ON COLUMN batch_history.event_details IS 'JSON data specific to each stage';

COMMENT ON TABLE batch_documents IS 'Links batches to related documents';

COMMENT ON TABLE batch_sequence IS 'Sequence generator with FY rollover (Apr 1 - Mar 31)';
COMMENT ON COLUMN batch_sequence.financial_year IS 'Short FY format: 2526 for FY 2025-26';
COMMENT ON COLUMN batch_sequence.fy_start_date IS 'Start date of current financial year';
COMMENT ON COLUMN batch_sequence.fy_end_date IS 'End date of current financial year';

-- ============================================================================
-- STEP 6: INSERT INITIAL DATA
-- ============================================================================

INSERT INTO batch_sequence (current_number, prefix, financial_year, fy_start_date, fy_end_date)
VALUES (0, 'B', '2526', '2025-04-01', '2026-03-31');

-- ============================================================================
-- STEP 7: VERIFICATION
-- ============================================================================

-- Verify tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('batches', 'batch_history', 'batch_documents', 'batch_sequence')
ORDER BY table_name;

-- Verify batch_sequence initialized
SELECT
    id,
    current_number,
    prefix,
    financial_year,
    fy_start_date,
    fy_end_date,
    CONCAT(prefix, '/', financial_year, '/', LPAD((current_number + 1)::text, 4, '0')) as next_batch_number
FROM batch_sequence;

-- Expected output:
-- id | current_number | prefix | financial_year | fy_start_date | fy_end_date | next_batch_number
-- ----+----------------+--------+----------------+---------------+-------------+-------------------
--  1 |              0 | B      | 2526           | 2025-04-01    | 2026-03-31  | B/2526/0001

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Batch Tracking module installed successfully!';
    RAISE NOTICE '   - 4 tables created: batches, batch_history, batch_documents, batch_sequence';
    RAISE NOTICE '   - 13 indexes created';
    RAISE NOTICE '   - FY configured: 2526 (Apr 2025 - Mar 2026)';
    RAISE NOTICE '   - Next batch number: B/2526/0001';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready to test! Start FastAPI server and navigate to /docs';
END $$;
