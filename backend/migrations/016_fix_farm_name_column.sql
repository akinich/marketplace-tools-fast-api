-- ============================================================================
-- Fix: Add farm_name column to purchase_orders table
-- ============================================================================
-- Run this if the purchase_orders table was created without the farm_name column
-- ============================================================================

-- Add the column if it doesn't exist
ALTER TABLE purchase_orders 
ADD COLUMN IF NOT EXISTS farm_name VARCHAR(255);

-- Create index
CREATE INDEX IF NOT EXISTS idx_purchase_orders_farm_name ON purchase_orders(farm_name);

-- Add comment
COMMENT ON COLUMN purchase_orders.farm_name IS 'Name of the farm/vendor - temporary field until vendor master is linked';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ farm_name column added to purchase_orders table!';
END $$;
