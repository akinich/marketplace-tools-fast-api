-- ============================================================================
-- BIOFLOC MODULE - DATABASE SCHEMA v1.0.0
-- ============================================================================
-- Description: Complete database schema for biofloc aquaculture management
-- Author: Claude Code
-- Date: 2025-11-18
-- Dependencies: users table (from auth module)
--
-- This migration creates:
-- - 10 core tables for biofloc operations
-- - Indexes for performance
-- - Triggers for automatic updates
-- ============================================================================

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- 1. TANKS
CREATE TABLE IF NOT EXISTS biofloc_tanks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_name VARCHAR(100) NOT NULL,
    tank_code VARCHAR(50) UNIQUE NOT NULL,
    capacity_liters DECIMAL(12,2) NOT NULL,
    location VARCHAR(200),
    tank_type VARCHAR(50) DEFAULT 'circular', -- circular, rectangular, raceway
    status VARCHAR(20) DEFAULT 'available', -- available, in_use, maintenance, decommissioned
    current_batch_id UUID,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);

-- 2. FISH BATCHES
CREATE TABLE IF NOT EXISTS biofloc_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_code VARCHAR(50) UNIQUE NOT NULL,
    species VARCHAR(100) NOT NULL,
    source VARCHAR(200), -- hatchery, supplier name

    -- Stocking data
    stocking_date DATE NOT NULL,
    initial_count INTEGER NOT NULL,
    initial_avg_weight_g DECIMAL(10,4) NOT NULL, -- grams
    initial_total_biomass_kg DECIMAL(12,4), -- calculated

    -- Current state (updated via triggers/calculations)
    current_count INTEGER,
    current_avg_weight_g DECIMAL(10,4),
    current_total_biomass_kg DECIMAL(12,4),

    -- Mortality tracking
    total_mortality INTEGER DEFAULT 0,
    mortality_percentage DECIMAL(5,2),

    -- Cycle info
    status VARCHAR(20) DEFAULT 'active', -- active, harvested, terminated
    end_date DATE,
    cycle_duration_days INTEGER,

    -- Calculated metrics (updated on harvest/sampling)
    total_feed_kg DECIMAL(12,4) DEFAULT 0,
    fcr DECIMAL(6,4), -- Feed Conversion Ratio
    sgr DECIMAL(6,4), -- Specific Growth Rate
    survival_rate DECIMAL(5,2),

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);

-- Add FK constraint after biofloc_batches is created
ALTER TABLE biofloc_tanks
ADD CONSTRAINT fk_tank_current_batch
FOREIGN KEY (current_batch_id) REFERENCES biofloc_batches(id)
ON DELETE SET NULL;

-- 3. BATCH-TANK ASSIGNMENTS (history of which batch was in which tank)
CREATE TABLE IF NOT EXISTS biofloc_batch_tank_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    start_date DATE NOT NULL,
    end_date DATE,
    transfer_reason VARCHAR(200), -- initial stocking, growth transfer, harvest, maintenance
    fish_count_at_transfer INTEGER,
    avg_weight_at_transfer_g DECIMAL(10,4),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 4. FEEDING SESSIONS
CREATE TABLE IF NOT EXISTS biofloc_feeding_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),

    -- Feeding details
    feeding_date DATE NOT NULL,
    session_number INTEGER NOT NULL, -- 1, 2, 3... per day
    feed_time TIME,

    -- Feed items (multiple feeds per session supported)
    -- Stored as JSONB for flexibility
    feed_items JSONB NOT NULL, -- [{sku, quantity_kg, inventory_transaction_id}]

    -- Totals
    total_feed_kg DECIMAL(10,4) NOT NULL,
    total_cost DECIMAL(12,2),

    -- Inventory tracking
    inventory_batch_id UUID, -- links to inventory module's batch deduction

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 5. SAMPLING DATA (periodic measurements)
CREATE TABLE IF NOT EXISTS biofloc_sampling (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),

    sample_date DATE NOT NULL,
    sample_size INTEGER NOT NULL, -- number of fish sampled

    -- Weight measurements
    avg_weight_g DECIMAL(10,4) NOT NULL,
    min_weight_g DECIMAL(10,4),
    max_weight_g DECIMAL(10,4),
    std_deviation_g DECIMAL(10,4),

    -- Length measurements (optional)
    avg_length_cm DECIMAL(8,2),
    min_length_cm DECIMAL(8,2),
    max_length_cm DECIMAL(8,2),

    -- Condition
    condition_factor DECIMAL(6,4), -- K = (W / L³) × 100

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 6. MORTALITY RECORDS
CREATE TABLE IF NOT EXISTS biofloc_mortality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),

    mortality_date DATE NOT NULL,
    count INTEGER NOT NULL,
    cause VARCHAR(200), -- disease, stress, unknown, predation, handling

    -- Estimated weight loss
    avg_weight_g DECIMAL(10,4),
    total_biomass_loss_kg DECIMAL(10,4),

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 7. WATER QUALITY TESTS
CREATE TABLE IF NOT EXISTS biofloc_water_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    batch_id UUID REFERENCES biofloc_batches(id),

    test_date DATE NOT NULL,
    test_time TIME,

    -- Core parameters
    temperature_c DECIMAL(5,2),
    ph DECIMAL(4,2),
    dissolved_oxygen_mgl DECIMAL(6,2),
    salinity_ppt DECIMAL(6,2),

    -- Nitrogen cycle
    ammonia_nh3_mgl DECIMAL(6,3),
    nitrite_no2_mgl DECIMAL(6,3),
    nitrate_no3_mgl DECIMAL(6,3),

    -- Other parameters
    alkalinity_mgl DECIMAL(8,2),
    hardness_mgl DECIMAL(8,2),
    turbidity_ntu DECIMAL(8,2),
    tds_mgl DECIMAL(10,2), -- Total Dissolved Solids

    -- Biofloc specific
    floc_volume_mll DECIMAL(6,2), -- ml/L (Imhoff cone)

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 8. TANK INPUTS (non-feed items: chemicals, probiotics, etc.)
CREATE TABLE IF NOT EXISTS biofloc_tank_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    batch_id UUID REFERENCES biofloc_batches(id),

    input_date DATE NOT NULL,
    input_time TIME,

    -- Input details
    input_type VARCHAR(50) NOT NULL, -- chemical, probiotic, carbon_source, mineral, other
    item_sku VARCHAR(50), -- links to inventory
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,

    -- Cost tracking
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(12,2),

    -- Inventory tracking
    inventory_transaction_id UUID,

    reason VARCHAR(200), -- ph_adjustment, ammonia_control, floc_boost, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 9. HARVESTS
CREATE TABLE IF NOT EXISTS biofloc_harvests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),

    harvest_date DATE NOT NULL,
    harvest_type VARCHAR(20) NOT NULL, -- partial, complete

    -- Harvest data
    fish_count INTEGER NOT NULL,
    total_weight_kg DECIMAL(12,4) NOT NULL,
    avg_weight_g DECIMAL(10,4),

    -- Quality grading (optional)
    grade_a_kg DECIMAL(10,4),
    grade_b_kg DECIMAL(10,4),
    grade_c_kg DECIMAL(10,4),
    reject_kg DECIMAL(10,4),

    -- Sales info (optional)
    buyer VARCHAR(200),
    price_per_kg DECIMAL(10,2),
    total_revenue DECIMAL(12,2),

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID -- REFERENCES user_profiles(id)
);

-- 10. CYCLE COSTS (aggregated costs per batch)
CREATE TABLE IF NOT EXISTS biofloc_cycle_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL UNIQUE REFERENCES biofloc_batches(id),

    -- Cost breakdown
    fingerling_cost DECIMAL(12,2) DEFAULT 0,
    feed_cost DECIMAL(12,2) DEFAULT 0,
    chemical_cost DECIMAL(12,2) DEFAULT 0,
    labor_cost DECIMAL(12,2) DEFAULT 0,
    utilities_cost DECIMAL(12,2) DEFAULT 0, -- electricity, water
    other_cost DECIMAL(12,2) DEFAULT 0,

    -- Total cost (calculated)
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (
        fingerling_cost + feed_cost + chemical_cost + labor_cost + utilities_cost + other_cost
    ) STORED,

    -- Revenue
    total_revenue DECIMAL(12,2) DEFAULT 0,

    -- Profit (calculated)
    gross_profit DECIMAL(12,2) GENERATED ALWAYS AS (
        total_revenue - (fingerling_cost + feed_cost + chemical_cost + labor_cost + utilities_cost + other_cost)
    ) STORED,

    -- Per kg metrics
    cost_per_kg DECIMAL(10,2),
    profit_per_kg DECIMAL(10,2),

    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_batches_status ON biofloc_batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_stocking_date ON biofloc_batches(stocking_date);
CREATE INDEX IF NOT EXISTS idx_batches_created_at ON biofloc_batches(created_at);

CREATE INDEX IF NOT EXISTS idx_tanks_status ON biofloc_tanks(status);
CREATE INDEX IF NOT EXISTS idx_tanks_is_active ON biofloc_tanks(is_active);

CREATE INDEX IF NOT EXISTS idx_feeding_batch_date ON biofloc_feeding_sessions(batch_id, feeding_date);
CREATE INDEX IF NOT EXISTS idx_feeding_tank_date ON biofloc_feeding_sessions(tank_id, feeding_date);
CREATE INDEX IF NOT EXISTS idx_feeding_date ON biofloc_feeding_sessions(feeding_date);

CREATE INDEX IF NOT EXISTS idx_sampling_batch_date ON biofloc_sampling(batch_id, sample_date);
CREATE INDEX IF NOT EXISTS idx_sampling_date ON biofloc_sampling(sample_date);

CREATE INDEX IF NOT EXISTS idx_mortality_batch_date ON biofloc_mortality(batch_id, mortality_date);
CREATE INDEX IF NOT EXISTS idx_mortality_date ON biofloc_mortality(mortality_date);

CREATE INDEX IF NOT EXISTS idx_water_tests_tank_date ON biofloc_water_tests(tank_id, test_date);
CREATE INDEX IF NOT EXISTS idx_water_tests_date ON biofloc_water_tests(test_date);

CREATE INDEX IF NOT EXISTS idx_tank_inputs_tank_date ON biofloc_tank_inputs(tank_id, input_date);
CREATE INDEX IF NOT EXISTS idx_tank_inputs_date ON biofloc_tank_inputs(input_date);

CREATE INDEX IF NOT EXISTS idx_harvests_batch ON biofloc_harvests(batch_id);
CREATE INDEX IF NOT EXISTS idx_harvests_date ON biofloc_harvests(harvest_date);

CREATE INDEX IF NOT EXISTS idx_assignments_batch ON biofloc_batch_tank_assignments(batch_id);
CREATE INDEX IF NOT EXISTS idx_assignments_tank ON biofloc_batch_tank_assignments(tank_id);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Trigger 1: Update batch mortality when mortality record is inserted
CREATE OR REPLACE FUNCTION update_batch_mortality()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE biofloc_batches
    SET
        total_mortality = total_mortality + NEW.count,
        current_count = GREATEST(0, current_count - NEW.count),
        mortality_percentage = ((total_mortality + NEW.count)::DECIMAL / NULLIF(initial_count, 0)) * 100,
        updated_at = NOW()
    WHERE id = NEW.batch_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_batch_mortality ON biofloc_mortality;
CREATE TRIGGER trg_update_batch_mortality
AFTER INSERT ON biofloc_mortality
FOR EACH ROW EXECUTE FUNCTION update_batch_mortality();

-- Trigger 2: Update batch feed totals when feeding session is inserted
CREATE OR REPLACE FUNCTION update_batch_feed_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch total feed
    UPDATE biofloc_batches
    SET
        total_feed_kg = total_feed_kg + NEW.total_feed_kg,
        updated_at = NOW()
    WHERE id = NEW.batch_id;

    -- Update cycle costs feed cost
    INSERT INTO biofloc_cycle_costs (batch_id, feed_cost)
    VALUES (NEW.batch_id, COALESCE(NEW.total_cost, 0))
    ON CONFLICT (batch_id)
    DO UPDATE SET
        feed_cost = biofloc_cycle_costs.feed_cost + COALESCE(NEW.total_cost, 0),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_batch_feed ON biofloc_feeding_sessions;
CREATE TRIGGER trg_update_batch_feed
AFTER INSERT ON biofloc_feeding_sessions
FOR EACH ROW EXECUTE FUNCTION update_batch_feed_totals();

-- Trigger 3: Update tank current_batch_id when assignment is created
CREATE OR REPLACE FUNCTION update_tank_current_batch()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_date IS NULL THEN
        -- New assignment without end date = current batch
        UPDATE biofloc_tanks
        SET
            current_batch_id = NEW.batch_id,
            status = 'in_use',
            updated_at = NOW()
        WHERE id = NEW.tank_id;
    ELSE
        -- Assignment has end date, clear tank if this was the current batch
        UPDATE biofloc_tanks
        SET
            current_batch_id = NULL,
            status = 'available',
            updated_at = NOW()
        WHERE id = NEW.tank_id AND current_batch_id = NEW.batch_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_tank_batch ON biofloc_batch_tank_assignments;
CREATE TRIGGER trg_update_tank_batch
AFTER INSERT OR UPDATE ON biofloc_batch_tank_assignments
FOR EACH ROW EXECUTE FUNCTION update_tank_current_batch();

-- Trigger 4: Calculate initial biomass on batch creation
CREATE OR REPLACE FUNCTION calculate_initial_biomass()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.initial_total_biomass_kg IS NULL THEN
        NEW.initial_total_biomass_kg := (NEW.initial_count * NEW.initial_avg_weight_g) / 1000.0;
    END IF;

    -- Initialize current values to match initial values
    IF NEW.current_count IS NULL THEN
        NEW.current_count := NEW.initial_count;
    END IF;

    IF NEW.current_avg_weight_g IS NULL THEN
        NEW.current_avg_weight_g := NEW.initial_avg_weight_g;
    END IF;

    IF NEW.current_total_biomass_kg IS NULL THEN
        NEW.current_total_biomass_kg := NEW.initial_total_biomass_kg;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_calculate_initial_biomass ON biofloc_batches;
CREATE TRIGGER trg_calculate_initial_biomass
BEFORE INSERT ON biofloc_batches
FOR EACH ROW EXECUTE FUNCTION calculate_initial_biomass();

-- Trigger 5: Update tank inputs cost in cycle costs
CREATE OR REPLACE FUNCTION update_cycle_chemical_costs()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.batch_id IS NOT NULL AND NEW.total_cost IS NOT NULL THEN
        INSERT INTO biofloc_cycle_costs (batch_id, chemical_cost)
        VALUES (NEW.batch_id, NEW.total_cost)
        ON CONFLICT (batch_id)
        DO UPDATE SET
            chemical_cost = biofloc_cycle_costs.chemical_cost + NEW.total_cost,
            updated_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_cycle_chemical_costs ON biofloc_tank_inputs;
CREATE TRIGGER trg_update_cycle_chemical_costs
AFTER INSERT ON biofloc_tank_inputs
FOR EACH ROW EXECUTE FUNCTION update_cycle_chemical_costs();

-- Trigger 6: Update updated_at timestamp on record modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tanks_updated_at ON biofloc_tanks;
CREATE TRIGGER trg_tanks_updated_at
BEFORE UPDATE ON biofloc_tanks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_batches_updated_at ON biofloc_batches;
CREATE TRIGGER trg_batches_updated_at
BEFORE UPDATE ON biofloc_batches
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA / SEED (Optional)
-- ============================================================================

-- You can add seed data here if needed, for example:
-- INSERT INTO biofloc_tanks (tank_name, tank_code, capacity_liters, location, created_by)
-- VALUES ('Tank 1', 'T001', 10000, 'Building A', (SELECT id FROM users WHERE email = 'admin@example.com' LIMIT 1));

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'biofloc_%';

    RAISE NOTICE '✅ Biofloc module migration complete! Created % tables.', table_count;
END $$;
