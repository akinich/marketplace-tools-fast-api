-- ============================================================================
-- Migration: Add B2B and B2C Ticket Support (Unified System)
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-12-07
--
-- Description:
--   Extends existing tickets table to support B2B and B2C tickets
--   Uses ticket_category field to distinguish between internal/b2b/b2c
--   Adds B2B and B2C specific fields to existing table
-- ============================================================================

-- Add ticket_category column
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ticket_category VARCHAR(20) DEFAULT 'internal';

-- Add B2B/B2C specific fields
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(50);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS woocommerce_order_id VARCHAR(50);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS sales_order_id INTEGER;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS invoice_id INTEGER;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS batch_number VARCHAR(50);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS delivery_date DATE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS claim_window_days INTEGER;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS is_late_claim BOOLEAN DEFAULT FALSE;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS photo_urls TEXT[];
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS assigned_to_id UUID REFERENCES user_profiles(id);

-- Backfill existing tickets as 'internal' category
UPDATE tickets SET ticket_category = 'internal' WHERE ticket_category IS NULL;

-- Update ticket_type constraint to include B2B/B2C types
ALTER TABLE tickets DROP CONSTRAINT IF EXISTS valid_ticket_type;
ALTER TABLE tickets ADD CONSTRAINT valid_ticket_type CHECK (
    ticket_type IN (
        -- Internal ticket types
        'issue', 'feature_request', 'upgrade', 'others',
        -- B2B/B2C ticket types
        'quality_issue', 'delivery_issue', 'order_issue', 'return_request', 'general'
    )
);

-- Add constraint for ticket_category
ALTER TABLE tickets ADD CONSTRAINT valid_ticket_category CHECK (
    ticket_category IN ('internal', 'b2b', 'b2c')
);

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(ticket_category);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_email ON tickets(customer_email);
CREATE INDEX IF NOT EXISTS idx_tickets_woo_order ON tickets(woocommerce_order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_sales_order ON tickets(sales_order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_batch ON tickets(batch_number);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to_id);

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- Verify columns were added
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'tickets' 
  AND column_name IN (
      'ticket_category', 'customer_name', 'customer_email', 'customer_phone',
      'woocommerce_order_id', 'sales_order_id', 'batch_number', 'photo_urls',
      'assigned_to_id', 'delivery_date', 'claim_window_days', 'is_late_claim'
  )
ORDER BY column_name;

-- Verify existing tickets are categorized as internal
SELECT ticket_category, COUNT(*) as count
FROM tickets
GROUP BY ticket_category;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
