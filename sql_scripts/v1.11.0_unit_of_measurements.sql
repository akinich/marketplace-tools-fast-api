-- ============================================================================
-- Farm Management System - Unit of Measurements
-- ============================================================================
-- Version: 1.11.0
-- Purpose: Standardize units across inventory items with a centralized table
-- Date: 2025-11-22
-- ============================================================================

BEGIN;

-- Create unit_of_measurements table
CREATE TABLE IF NOT EXISTS unit_of_measurements (
    id SERIAL PRIMARY KEY,
    unit_name VARCHAR(50) UNIQUE NOT NULL,
    abbreviation VARCHAR(10),
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add comment
COMMENT ON TABLE unit_of_measurements IS 'Standardized units of measurement for inventory items';
COMMENT ON COLUMN unit_of_measurements.category IS 'Unit category: weight, volume, count, length, area, etc.';

-- Insert common units
INSERT INTO unit_of_measurements (unit_name, abbreviation, category) VALUES
    -- Weight
    ('Kilogram', 'kg', 'weight'),
    ('Gram', 'g', 'weight'),
    ('Ton', 't', 'weight'),
    ('Pound', 'lb', 'weight'),
    ('Ounce', 'oz', 'weight'),

    -- Volume
    ('Liter', 'L', 'volume'),
    ('Milliliter', 'mL', 'volume'),
    ('Gallon', 'gal', 'volume'),
    ('Cubic Meter', 'm³', 'volume'),

    -- Count/Quantity
    ('Piece', 'pc', 'count'),
    ('Box', 'box', 'count'),
    ('Bag', 'bag', 'count'),
    ('Pack', 'pack', 'count'),
    ('Dozen', 'doz', 'count'),
    ('Unit', 'unit', 'count'),
    ('Carton', 'ctn', 'count'),
    ('Sack', 'sack', 'count'),

    -- Length
    ('Meter', 'm', 'length'),
    ('Centimeter', 'cm', 'length'),
    ('Kilometer', 'km', 'length'),
    ('Foot', 'ft', 'length'),
    ('Inch', 'in', 'length'),

    -- Area
    ('Square Meter', 'm²', 'area'),
    ('Hectare', 'ha', 'area'),
    ('Acre', 'ac', 'area')
ON CONFLICT (unit_name) DO NOTHING;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_unit_of_measurements_active ON unit_of_measurements(is_active);
CREATE INDEX IF NOT EXISTS idx_unit_of_measurements_category ON unit_of_measurements(category);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_unit_of_measurements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_unit_of_measurements_updated_at ON unit_of_measurements;
CREATE TRIGGER trigger_update_unit_of_measurements_updated_at
BEFORE UPDATE ON unit_of_measurements
FOR EACH ROW
EXECUTE FUNCTION update_unit_of_measurements_updated_at();

-- Display created units
SELECT
    category,
    COUNT(*) as unit_count,
    STRING_AGG(unit_name || ' (' || abbreviation || ')', ', ' ORDER BY unit_name) as units
FROM unit_of_measurements
WHERE is_active = TRUE
GROUP BY category
ORDER BY category;

COMMIT;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Units linked to items cannot be deleted, only deactivated
-- 2. Units not linked to any items can be permanently deleted
-- 3. This table is referenced by item_master.unit (will be updated in future migration)
-- 4. Admin can add custom units through the settings UI
-- ============================================================================
