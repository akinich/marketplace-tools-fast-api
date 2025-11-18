-- ============================================================================
-- BIOFLOC MODULE - CLEANUP SCRIPT
-- ============================================================================
-- Use this script to drop all biofloc tables if you need to start fresh
-- WARNING: This will delete ALL biofloc data!
-- ============================================================================

-- Drop tables in reverse order to handle foreign key dependencies
DROP TABLE IF EXISTS biofloc_cycle_costs CASCADE;
DROP TABLE IF EXISTS biofloc_harvests CASCADE;
DROP TABLE IF EXISTS biofloc_tank_inputs CASCADE;
DROP TABLE IF EXISTS biofloc_water_tests CASCADE;
DROP TABLE IF EXISTS biofloc_mortality CASCADE;
DROP TABLE IF EXISTS biofloc_sampling CASCADE;
DROP TABLE IF EXISTS biofloc_feeding_sessions CASCADE;
DROP TABLE IF EXISTS biofloc_batch_tank_assignments CASCADE;
DROP TABLE IF EXISTS biofloc_batches CASCADE;
DROP TABLE IF EXISTS biofloc_tanks CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_batch_mortality() CASCADE;
DROP FUNCTION IF EXISTS update_batch_feed_totals() CASCADE;
DROP FUNCTION IF EXISTS update_tank_current_batch() CASCADE;
DROP FUNCTION IF EXISTS calculate_initial_biomass() CASCADE;
DROP FUNCTION IF EXISTS update_cycle_chemical_costs() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Verify cleanup
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE tablename LIKE 'biofloc_%'
ORDER BY tablename;

-- If the above query returns no rows, cleanup was successful
