-- ============================================================================
-- Cleanup Script: Remove Biofloc, Inventory, and Units Modules
-- Description: Drops all tables associated with the removed modules
-- ============================================================================

-- Drop Biofloc tables
DROP TABLE IF EXISTS biofloc_logs CASCADE;
DROP TABLE IF EXISTS biofloc_tanks CASCADE;
DROP TABLE IF EXISTS biofloc_parameters CASCADE;

-- Drop Inventory tables
DROP TABLE IF EXISTS inventory_transactions CASCADE;
DROP TABLE IF EXISTS inventory_reservations CASCADE;
DROP TABLE IF EXISTS inventory_batches CASCADE;
DROP TABLE IF EXISTS item_module_mapping CASCADE;
DROP TABLE IF EXISTS item_master CASCADE;
DROP TABLE IF EXISTS inventory_categories CASCADE;

-- Drop Units tables
DROP TABLE IF EXISTS units_of_measurement CASCADE;

-- Drop any other related tables if they exist (based on standard naming)
DROP TABLE IF EXISTS biofloc_daily_metrics CASCADE;
DROP TABLE IF EXISTS biofloc_harvests CASCADE;

-- Clean up system settings related to these modules
DELETE FROM system_settings WHERE setting_key LIKE 'biofloc.%';
DELETE FROM system_settings WHERE setting_key LIKE 'inventory.%';
