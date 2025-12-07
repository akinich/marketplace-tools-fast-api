-- Add user-editable columns to zoho_items
ALTER TABLE zoho_items
ADD COLUMN IF NOT EXISTS for_purchase BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS segment VARCHAR(50);
