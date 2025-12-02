-- ============================================================================
-- Fix Product ID Unique Constraint
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-12-02
--
-- Problem:
--   - Current schema has UNIQUE constraint on product_id alone
--   - This prevents variations from being inserted (they share parent product_id)
--   - Example: Product 15725 with 3 variations all have product_id=15725
--
-- Solution:
--   - Drop the UNIQUE constraint on product_id alone
--   - Add UNIQUE constraint on (product_id, variation_id) combination
--   - This allows same product_id with different variation_ids
-- ============================================================================

-- Drop the existing unique constraint on product_id
-- First, find the constraint name (it's auto-generated as products_product_id_key)
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_product_id_key;

-- Add a unique constraint on the combination of product_id and variation_id
-- This allows:
--   - One row with product_id=123, variation_id=NULL (simple product)
--   - Multiple rows with product_id=123, variation_id=456/789/etc (variations)
-- But prevents:
--   - Duplicate simple product (same product_id, both variation_id=NULL)
--   - Duplicate variation (same product_id and variation_id)
ALTER TABLE products
ADD CONSTRAINT products_product_variation_unique
UNIQUE (product_id, variation_id);

-- Verify the change
COMMENT ON CONSTRAINT products_product_variation_unique ON products IS
'Ensures unique combination of product_id and variation_id. Allows variations (different variation_ids) for the same product_id.';
