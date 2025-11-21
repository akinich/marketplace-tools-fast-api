/*
================================================================================
Farm Management System - Item Master Updates
================================================================================
Version: 1.9.0
Created: 2025-11-21
Database: Supabase PostgreSQL

Changelog:
----------
v1.9.0 (2025-11-21):
  - Add default_price column to item_master table
  - Delete items with custom categories (not in inventory_categories)
  - Remove auto-category creation logic (now must use category dropdown)

Changes Summary:
  1. Add default_price NUMERIC(10,2) column (optional, for item pricing)
  2. Clean up items where category is not in inventory_categories table
  3. Category must now be selected from existing categories only

================================================================================
*/

-- ============================================================================
-- STEP 1: Add default_price column to item_master
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'item_master' AND column_name = 'default_price'
    ) THEN
        ALTER TABLE item_master
        ADD COLUMN default_price NUMERIC(10,2);

        RAISE NOTICE 'Added default_price column to item_master table';
    ELSE
        RAISE NOTICE 'default_price column already exists in item_master table';
    END IF;
END $$;

-- Add comment for documentation
COMMENT ON COLUMN item_master.default_price IS 'Optional default price for the item (2 decimal precision)';

-- ============================================================================
-- STEP 2: Delete items with custom categories (not in inventory_categories)
-- ============================================================================

-- First, show what will be deleted (view this before running the delete)
SELECT
    id,
    item_name,
    sku,
    category,
    'Will be deleted - custom category' as status
FROM item_master
WHERE category IS NOT NULL
  AND category NOT IN (SELECT category_name FROM inventory_categories);

-- Delete the items with custom categories
DELETE FROM item_master
WHERE category IS NOT NULL
  AND category NOT IN (SELECT category_name FROM inventory_categories);

-- ============================================================================
-- STEP 3: Update triggers if needed (current_qty trigger should still work)
-- ============================================================================

-- The existing trigger for current_qty calculation should continue to work
-- No changes needed to triggers

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify default_price column exists
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'item_master'
  AND column_name = 'default_price';

-- Verify no items with custom categories remain
SELECT COUNT(*) as items_with_custom_categories
FROM item_master
WHERE category IS NOT NULL
  AND category NOT IN (SELECT category_name FROM inventory_categories);

-- Show current item_master schema
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'item_master'
ORDER BY ordinal_position;

-- Final completion message
DO $$
BEGIN
    RAISE NOTICE 'Migration v1.9.0 completed successfully!';
END $$;
