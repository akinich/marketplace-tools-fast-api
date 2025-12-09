-- Update segment column to support multiple segments
-- Convert from VARCHAR(50) to TEXT[] to allow multiple segment tags

-- Drop the old column and recreate as array type
ALTER TABLE zoho_items
DROP COLUMN IF EXISTS segment;

ALTER TABLE zoho_items
ADD COLUMN segment TEXT[] DEFAULT '{}';

-- Create index for array searching
CREATE INDEX IF NOT EXISTS idx_zoho_items_segment ON zoho_items USING GIN (segment);
