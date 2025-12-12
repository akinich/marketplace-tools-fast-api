-- Add customer_segment column to zoho_customers table
-- Allows multi-select tagging of customers (B2B, B2C, B2R)

ALTER TABLE zoho_customers
ADD COLUMN IF NOT EXISTS customer_segment TEXT[] DEFAULT '{}';

-- Create GIN index for efficient array searching
CREATE INDEX IF NOT EXISTS idx_zoho_customers_customer_segment 
ON zoho_customers USING GIN (customer_segment);
