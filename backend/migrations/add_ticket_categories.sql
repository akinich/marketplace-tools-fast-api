-- ============================================================================
-- Add Ticket Categories Migration
-- ============================================================================
-- Version: 1.1.0
-- Created: 2025-12-06
--
-- Description:
--   Adds ticket_category field to tickets table to differentiate between:
--   - internal: Internal ERP system issues and operations
--   - b2b: B2B customer complaints and issues
--   - b2c: B2C customer complaints and issues
--
-- Changes:
--   - Add ticket_category column with default 'internal'
--   - Add CHECK constraint for valid categories
--   - Create index for performance
--   - Backfill existing tickets as 'internal'
-- ============================================================================

-- Add ticket_category column
ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS ticket_category VARCHAR(20) DEFAULT 'internal';

-- Add CHECK constraint for valid categories
ALTER TABLE tickets
DROP CONSTRAINT IF EXISTS valid_ticket_category;

ALTER TABLE tickets
ADD CONSTRAINT valid_ticket_category
CHECK (ticket_category IN ('internal', 'b2b', 'b2c'));

-- Create index for ticket_category
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(ticket_category);

-- Backfill existing tickets as 'internal' (they're ERP system related)
UPDATE tickets
SET ticket_category = 'internal'
WHERE ticket_category IS NULL;

-- Add NOT NULL constraint after backfill
ALTER TABLE tickets
ALTER COLUMN ticket_category SET NOT NULL;

-- Verification query
DO $$
BEGIN
    RAISE NOTICE '✅ Ticket categories migration completed';
    RAISE NOTICE '   - Added ticket_category column';
    RAISE NOTICE '   - Valid values: internal, b2b, b2c';
    RAISE NOTICE '   - Created index: idx_tickets_category';
    RAISE NOTICE '   - Backfilled existing tickets as internal';
END $$;
