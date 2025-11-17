/*
================================================================================
Farm Management System - Database Schema
================================================================================
Version: 1.0.0
Created: 2025-11-17
Database: Supabase PostgreSQL

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial database schema creation
  - Authentication and user management tables
  - Modules and permissions system
  - Activity logging
  - Inventory management (items, batches, transactions, POs, suppliers)
  - Biofloc aquaculture (tanks, water tests, growth, feed)
  - Database views for optimized queries
  - Triggers for auto-updating stock quantities
  - Performance indexes

================================================================================
*/

-- ============================================================================
-- SECTION 1: ROLES AND USER PROFILES
-- ============================================================================

-- Roles table (Admin, User)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default roles
INSERT INTO roles (role_name, description) VALUES
('Admin', 'Full system access'),
('User', 'Standard farm worker access')
ON CONFLICT (role_name) DO NOTHING;

-- User Profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 2: MODULES AND PERMISSIONS
-- ============================================================================

-- Modules (installable features)
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    module_key VARCHAR(50) UNIQUE NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT '⚙️',
    display_order INTEGER DEFAULT 99,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial modules
INSERT INTO modules (module_key, module_name, description, icon, display_order) VALUES
('inventory', 'Inventory Management', 'Track stock, POs, and suppliers', '📦', 1),
('biofloc', 'Biofloc Aquaculture', 'Manage fish tanks, water quality, growth', '🐟', 2),
('dashboard', 'Dashboard', 'Overview and analytics', '📊', 0)
ON CONFLICT (module_key) DO NOTHING;

-- User Module Permissions (granular access control)
CREATE TABLE IF NOT EXISTS user_module_permissions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES user_profiles(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, module_id)
);

-- ============================================================================
-- SECTION 3: ACTIVITY LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    module_key VARCHAR(50),
    description TEXT,
    metadata JSONB,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 4: INVENTORY MODULE
-- ============================================================================

-- Inventory Categories
CREATE TABLE IF NOT EXISTS inventory_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Item Master List (templates, NO stock quantities here initially)
CREATE TABLE IF NOT EXISTS item_master (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    category VARCHAR(100) REFERENCES inventory_categories(category_name),
    unit VARCHAR(50) NOT NULL,
    default_supplier_id INTEGER REFERENCES suppliers(id),
    reorder_threshold NUMERIC(10,2) DEFAULT 0,
    min_stock_level NUMERIC(10,2) DEFAULT 0,
    current_qty NUMERIC(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory Batches (actual stock with FIFO tracking)
CREATE TABLE IF NOT EXISTS inventory_batches (
    id SERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    batch_number VARCHAR(100),
    quantity_purchased NUMERIC(10,2) NOT NULL,
    remaining_qty NUMERIC(10,2) NOT NULL,
    unit_cost NUMERIC(10,2) NOT NULL,
    purchase_date DATE NOT NULL,
    expiry_date DATE,
    supplier_id INTEGER REFERENCES suppliers(id),
    po_number VARCHAR(100),
    notes TEXT,
    added_by UUID REFERENCES user_profiles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory Transactions (complete audit trail)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id BIGSERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    batch_id INTEGER REFERENCES inventory_batches(id),
    transaction_type VARCHAR(50) NOT NULL,
    quantity_change NUMERIC(10,2) NOT NULL,
    new_balance NUMERIC(10,2) NOT NULL,
    unit_cost NUMERIC(10,2),
    total_cost NUMERIC(10,2),
    po_number VARCHAR(100),
    module_reference VARCHAR(100),
    tank_id INTEGER,
    user_id UUID REFERENCES user_profiles(id),
    username VARCHAR(255),
    notes TEXT,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    po_date DATE NOT NULL,
    expected_delivery DATE,
    status VARCHAR(50) DEFAULT 'pending',
    total_cost NUMERIC(12,2) DEFAULT 0,
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Order Items (multi-item PO support)
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    ordered_qty NUMERIC(10,2) NOT NULL,
    unit_cost NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 5: BIOFLOC AQUACULTURE MODULE
-- ============================================================================

-- Biofloc Tanks
CREATE TABLE IF NOT EXISTS biofloc_tanks (
    id SERIAL PRIMARY KEY,
    tank_number INTEGER UNIQUE NOT NULL,
    tank_name VARCHAR(100) NOT NULL,
    capacity_m3 NUMERIC(10,2),
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Water Quality Tests
CREATE TABLE IF NOT EXISTS biofloc_water_tests (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER NOT NULL REFERENCES biofloc_tanks(id),
    test_date DATE NOT NULL,
    ph NUMERIC(4,2),
    dissolved_oxygen NUMERIC(5,2),
    ammonia NUMERIC(5,2),
    nitrite NUMERIC(5,2),
    nitrate NUMERIC(6,2),
    temp NUMERIC(4,1),
    salinity NUMERIC(5,2),
    tds NUMERIC(8,2),
    alkalinity NUMERIC(6,2),
    notes TEXT,
    tested_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Growth Records
CREATE TABLE IF NOT EXISTS biofloc_growth_records (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER NOT NULL REFERENCES biofloc_tanks(id),
    record_date DATE NOT NULL,
    biomass_kg NUMERIC(10,2) NOT NULL,
    fish_count INTEGER,
    avg_weight NUMERIC(8,2),
    mortality INTEGER DEFAULT 0,
    notes TEXT,
    recorded_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feed Logs
CREATE TABLE IF NOT EXISTS biofloc_feed_logs (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER NOT NULL REFERENCES biofloc_tanks(id),
    feed_date DATE NOT NULL,
    feed_type VARCHAR(255) NOT NULL,
    quantity_kg NUMERIC(8,2) NOT NULL,
    feeding_time VARCHAR(50),
    notes TEXT,
    logged_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 6: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Activity logs indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_module ON activity_logs(module_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action_type, created_at DESC);

-- Inventory indexes
CREATE INDEX IF NOT EXISTS idx_inventory_batches_item ON inventory_batches(item_master_id, remaining_qty DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_expiry ON inventory_batches(expiry_date) WHERE expiry_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item ON inventory_transactions(item_master_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status, po_date DESC);

-- Biofloc indexes
CREATE INDEX IF NOT EXISTS idx_water_tests_tank ON biofloc_water_tests(tank_id, test_date DESC);
CREATE INDEX IF NOT EXISTS idx_growth_records_tank ON biofloc_growth_records(tank_id, record_date DESC);
CREATE INDEX IF NOT EXISTS idx_feed_logs_tank ON biofloc_feed_logs(tank_id, feed_date DESC);

-- ============================================================================
-- SECTION 7: DATABASE VIEWS
-- ============================================================================

-- User Details View (combines auth + profile + role)
CREATE OR REPLACE VIEW user_details AS
SELECT
    up.id,
    au.email,
    up.full_name,
    up.role_id,
    r.role_name,
    up.is_active,
    up.created_at,
    up.updated_at
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
LEFT JOIN roles r ON r.id = up.role_id;

-- User Accessible Modules (RBAC + user permissions)
CREATE OR REPLACE VIEW user_accessible_modules AS
SELECT DISTINCT
    up.id AS user_id,
    m.id AS module_id,
    m.module_key,
    m.module_name,
    m.icon,
    m.display_order
FROM user_profiles up
JOIN roles r ON r.id = up.role_id
CROSS JOIN modules m
LEFT JOIN user_module_permissions ump ON ump.user_id = up.id AND ump.module_id = m.id
WHERE m.is_active = TRUE
  AND up.is_active = TRUE
  AND (
      r.role_name = 'Admin'
      OR (ump.can_access = TRUE)
  )
ORDER BY m.display_order;

-- Tank Overview (Biofloc dashboard summary)
CREATE OR REPLACE VIEW biofloc_tank_overview AS
SELECT
    t.id,
    t.tank_number,
    t.tank_name,
    t.capacity_m3,
    wt.test_date AS last_test_date,
    wt.ph AS last_ph,
    wt.dissolved_oxygen AS last_do,
    wt.temp AS last_temp,
    (NOW()::date - wt.test_date) > 2 AS test_overdue,
    gr.record_date AS last_growth_date,
    gr.biomass_kg AS current_biomass,
    gr.fish_count AS current_fish_count,
    gr.mortality AS last_mortality
FROM biofloc_tanks t
LEFT JOIN LATERAL (
    SELECT * FROM biofloc_water_tests
    WHERE tank_id = t.id
    ORDER BY test_date DESC
    LIMIT 1
) wt ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM biofloc_growth_records
    WHERE tank_id = t.id
    ORDER BY record_date DESC
    LIMIT 1
) gr ON TRUE
WHERE t.is_active = TRUE;

-- ============================================================================
-- SECTION 8: TRIGGERS
-- ============================================================================

-- Function to auto-update item_master.current_qty when batches change
CREATE OR REPLACE FUNCTION update_item_master_qty()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE item_master
    SET current_qty = (
        SELECT COALESCE(SUM(remaining_qty), 0)
        FROM inventory_batches
        WHERE item_master_id = COALESCE(NEW.item_master_id, OLD.item_master_id)
          AND is_active = TRUE
    ),
    updated_at = NOW()
    WHERE id = COALESCE(NEW.item_master_id, OLD.item_master_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger on inventory_batches
DROP TRIGGER IF EXISTS trigger_update_item_qty_on_batch_change ON inventory_batches;
CREATE TRIGGER trigger_update_item_qty_on_batch_change
AFTER INSERT OR UPDATE OF remaining_qty OR DELETE ON inventory_batches
FOR EACH ROW
EXECUTE FUNCTION update_item_master_qty();

-- Function to auto-update PO total_cost when items change
CREATE OR REPLACE FUNCTION update_po_total_cost()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE purchase_orders
    SET total_cost = (
        SELECT COALESCE(SUM(ordered_qty * unit_cost), 0)
        FROM purchase_order_items
        WHERE purchase_order_id = COALESCE(NEW.purchase_order_id, OLD.purchase_order_id)
    ),
    updated_at = NOW()
    WHERE id = COALESCE(NEW.purchase_order_id, OLD.purchase_order_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger on purchase_order_items
DROP TRIGGER IF EXISTS trigger_update_po_total ON purchase_order_items;
CREATE TRIGGER trigger_update_po_total
AFTER INSERT OR UPDATE OR DELETE ON purchase_order_items
FOR EACH ROW
EXECUTE FUNCTION update_po_total_cost();

-- ============================================================================
-- SECTION 9: ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_module_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY user_view_own_profile ON user_profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Policy: Admins can view all profiles
CREATE POLICY admin_view_all_profiles ON user_profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            JOIN roles r ON r.id = up.role_id
            WHERE up.id = auth.uid() AND r.role_name = 'Admin'
        )
    );

-- ============================================================================
-- END OF SCHEMA v1.0.0
-- ============================================================================

-- Verification queries (optional - comment out after first run)
-- SELECT 'Roles' as table_name, COUNT(*) as count FROM roles
-- UNION ALL
-- SELECT 'Modules', COUNT(*) FROM modules
-- UNION ALL
-- SELECT 'Inventory Categories', COUNT(*) FROM inventory_categories;
