-- ============================================================================
-- Migration: Add Purchase Order Sequence Tracking
-- ============================================================================
-- Description: Adds sequence tracking columns to support PO/YY[YY+1]/XXXX format
-- Created: 2024-12-06
-- ============================================================================

-- Add sequence columns
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS sequence_number INTEGER,
ADD COLUMN IF NOT EXISTS financial_year VARCHAR(10);

-- Create index for efficient sequence lookup
CREATE INDEX IF NOT EXISTS idx_po_sequence ON purchase_orders(financial_year, sequence_number DESC);

-- Comment
COMMENT ON COLUMN purchase_orders.sequence_number IS 'Sequential number for the financial year (e.g., 1 for PO/2526/0001)';
COMMENT ON COLUMN purchase_orders.financial_year IS 'Financial year string (e.g., "2526" for FY 2025-26)';
