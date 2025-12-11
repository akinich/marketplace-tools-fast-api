-- ================================================================================
-- Migration 030: Customer Price Lists Module
-- ================================================================================
-- Description: 
--   Creates customer price list management system with date-based validity,
--   price history tracking, and customer assignment.
--
-- Tables Created:
--   - customer_price_lists: Main price list definitions
--   - price_list_items: Items and prices in each list
--   - price_list_history: Audit log of price changes
--
-- Tables Modified:
--   - zoho_customer_master: Add price_list_id column
--
-- ================================================================================

-- ============================================================================
-- 1. CREATE customer_price_lists TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS customer_price_lists (
    id SERIAL PRIMARY KEY,
    price_list_name VARCHAR(255) NOT NULL,
    description TEXT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_date_range CHECK (valid_to IS NULL OR valid_from <= valid_to),
    CONSTRAINT unique_price_list_name UNIQUE (price_list_name)
);

COMMENT ON TABLE customer_price_lists IS 'Customer price lists with date-based validity';
COMMENT ON COLUMN customer_price_lists.price_list_name IS 'Unique name for the price list';
COMMENT ON COLUMN customer_price_lists.valid_from IS 'Date from which this price list is active';
COMMENT ON COLUMN customer_price_lists.valid_to IS 'Date until which this price list is active (NULL = indefinite)';
COMMENT ON COLUMN customer_price_lists.is_active IS 'Manual override to disable price list';


-- ============================================================================
-- 2. CREATE price_list_items TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS price_list_items (
    id SERIAL PRIMARY KEY,
    price_list_id INTEGER NOT NULL REFERENCES customer_price_lists(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES zoho_items(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT positive_price CHECK (price > 0),
    CONSTRAINT unique_price_list_item UNIQUE (price_list_id, item_id)
);

COMMENT ON TABLE price_list_items IS 'Items and their prices within each price list';
COMMENT ON COLUMN price_list_items.price IS 'Item price in INR for this price list';
COMMENT ON COLUMN price_list_items.notes IS 'Optional notes about this item price';


-- ============================================================================
-- 3. CREATE price_list_history TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS price_list_history (
    id SERIAL PRIMARY KEY,
    price_list_id INTEGER NOT NULL REFERENCES customer_price_lists(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES zoho_items(id) ON DELETE SET NULL,
    field_changed VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE price_list_history IS 'Audit log of all price list and price changes';
COMMENT ON COLUMN price_list_history.field_changed IS 'Name of field that was changed (price, valid_from, etc)';
COMMENT ON COLUMN price_list_history.old_value IS 'Previous value before change';
COMMENT ON COLUMN price_list_history.new_value IS 'New value after change';


-- ============================================================================
-- 4. MODIFY zoho_customer_master TABLE
-- ============================================================================

-- Add price_list_id column to assign customers to price lists
ALTER TABLE zoho_customers 
ADD COLUMN IF NOT EXISTS price_list_id INTEGER REFERENCES customer_price_lists(id) ON DELETE SET NULL;

COMMENT ON COLUMN zoho_customers.price_list_id IS 'Assigned price list (NULL = use Zoho default pricing)';


-- ============================================================================
-- 5. CREATE INDEXES
-- ============================================================================

-- Index for quick price lookups by price list
CREATE INDEX IF NOT EXISTS idx_price_list_items_price_list 
ON price_list_items(price_list_id);

-- Index for quick price lookups by item
CREATE INDEX IF NOT EXISTS idx_price_list_items_item 
ON price_list_items(item_id);

-- Index for quick customer lookups by price list
CREATE INDEX IF NOT EXISTS idx_customer_price_list 
ON zoho_customers(price_list_id);

-- Index for date-based price list queries
CREATE INDEX IF NOT EXISTS idx_price_list_dates 
ON customer_price_lists(valid_from, valid_to);

-- Index for active price lists
CREATE INDEX IF NOT EXISTS idx_price_list_active 
ON customer_price_lists(is_active);

-- Index for price history queries
CREATE INDEX IF NOT EXISTS idx_price_list_history_price_list 
ON price_list_history(price_list_id);

CREATE INDEX IF NOT EXISTS idx_price_list_history_changed_at 
ON price_list_history(changed_at DESC);


-- ============================================================================
-- 6. CREATE FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_price_list_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER trigger_update_customer_price_lists_updated_at
    BEFORE UPDATE ON customer_price_lists
    FOR EACH ROW
    EXECUTE FUNCTION update_price_list_updated_at();

CREATE TRIGGER trigger_update_price_list_items_updated_at
    BEFORE UPDATE ON price_list_items
    FOR EACH ROW
    EXECUTE FUNCTION update_price_list_updated_at();


-- Function to log price changes to history table
CREATE OR REPLACE FUNCTION log_price_list_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Log price list metadata changes
    IF TG_TABLE_NAME = 'customer_price_lists' THEN
        IF OLD.price_list_name != NEW.price_list_name THEN
            INSERT INTO price_list_history (price_list_id, field_changed, old_value, new_value, changed_by)
            VALUES (NEW.id, 'price_list_name', OLD.price_list_name, NEW.price_list_name, NEW.created_by);
        END IF;
        
        IF OLD.valid_from != NEW.valid_from THEN
            INSERT INTO price_list_history (price_list_id, field_changed, old_value, new_value, changed_by)
            VALUES (NEW.id, 'valid_from', OLD.valid_from::TEXT, NEW.valid_from::TEXT, NEW.created_by);
        END IF;
        
        IF (OLD.valid_to IS DISTINCT FROM NEW.valid_to) THEN
            INSERT INTO price_list_history (price_list_id, field_changed, old_value, new_value, changed_by)
            VALUES (NEW.id, 'valid_to', OLD.valid_to::TEXT, NEW.valid_to::TEXT, NEW.created_by);
        END IF;
        
        IF OLD.is_active != NEW.is_active THEN
            INSERT INTO price_list_history (price_list_id, field_changed, old_value, new_value, changed_by)
            VALUES (NEW.id, 'is_active', OLD.is_active::TEXT, NEW.is_active::TEXT, NEW.created_by);
        END IF;
    END IF;
    
    -- Log item price changes
    IF TG_TABLE_NAME = 'price_list_items' THEN
        IF OLD.price != NEW.price THEN
            INSERT INTO price_list_history (price_list_id, item_id, field_changed, old_value, new_value)
            VALUES (NEW.price_list_id, NEW.item_id, 'price', OLD.price::TEXT, NEW.price::TEXT);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic history logging
CREATE TRIGGER trigger_log_price_list_changes
    AFTER UPDATE ON customer_price_lists
    FOR EACH ROW
    EXECUTE FUNCTION log_price_list_change();

CREATE TRIGGER trigger_log_price_item_changes
    AFTER UPDATE ON price_list_items
    FOR EACH ROW
    EXECUTE FUNCTION log_price_list_change();


-- ============================================================================
-- 7. GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to authenticated users (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON customer_price_lists TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON price_list_items TO authenticated;
GRANT SELECT ON price_list_history TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE customer_price_lists_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE price_list_items_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE price_list_history_id_seq TO authenticated;


-- ============================================================================
-- 8. SAMPLE DATA (Optional - Remove in production)
-- ============================================================================

-- Example price list for Q1 2026
-- INSERT INTO customer_price_lists (price_list_name, description, valid_from, valid_to)
-- VALUES ('Q1 2026 Pricing', 'Special pricing for Q1 FY 2026', '2026-01-01', '2026-03-31');


-- ================================================================================
-- END OF MIGRATION
-- ================================================================================
