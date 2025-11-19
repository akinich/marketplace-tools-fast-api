# Biofloc Module - Technical Guide

**Version:** 1.1.0
**Audience:** Developers, System Architects, Database Administrators

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Reference](#api-reference)
4. [Service Layer Logic](#service-layer-logic)
5. [Frontend Architecture](#frontend-architecture)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Performance Considerations](#performance-considerations)
8. [Security & Permissions](#security--permissions)

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Material-UI Components               │
│  - React Query for State                │
│  - Form Validation                      │
└──────────────┬──────────────────────────┘
               │ REST API (HTTP/JSON)
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI)               │
│  - Route Handlers                       │
│  - Service Layer                        │
│  - Pydantic Validation                  │
│  - Business Logic                       │
└──────────────┬──────────────────────────┘
               │ asyncpg (async)
┌──────────────▼──────────────────────────┐
│       Database (PostgreSQL)             │
│  - Relational Data                      │
│  - Triggers & Computed Columns          │
│  - Indexes                              │
└─────────────────────────────────────────┘
```

### Module Structure

**Backend:**
```
backend/app/
├── routes/biofloc.py          # API endpoints
├── schemas/biofloc.py         # Pydantic models
├── services/biofloc_service.py # Business logic
└── migrations/
    ├── biofloc_module_v1.0.0.sql
    └── biofloc_grading_v1.0.1.sql
```

**Frontend:**
```
frontend/src/
├── pages/
│   ├── BioflocModule.jsx           # Main router
│   ├── BioflocDashboard.jsx        # Dashboard
│   ├── BioflocTanks.jsx            # Tanks page
│   ├── BioflocBatches.jsx          # Batches page
│   ├── BioflocFeedingHistory.jsx   # Feeding history
│   ├── BioflocWaterTestHistory.jsx # Water test history
│   └── BioflocTankInputsHistory.jsx # Inputs history
└── components/
    ├── FeedingForm.jsx         # Multi-tank feeding
    ├── SamplingForm.jsx        # Sampling
    ├── MortalityForm.jsx       # Multi-batch mortality
    ├── WaterTestForm.jsx       # Multi-tank water tests
    ├── TankInputsForm.jsx      # Multi-tank inputs
    ├── HarvestForm.jsx         # Multi-batch harvest
    └── BatchTransferForm.jsx   # Normal & graded transfer
```

---

## Database Schema

### Entity Relationship Overview

```
biofloc_tanks ──┬──< biofloc_batch_tank_assignments >──┬── biofloc_batches
                │                                       │
                ├──< biofloc_water_tests               │
                ├──< biofloc_tank_inputs               │
                │                                       ├──< biofloc_feeding_sessions
                │                                       ├──< biofloc_sampling_records
                │                                       ├──< biofloc_mortality_records
                │                                       ├──< biofloc_harvests
                │                                       └──< biofloc_cycle_costs
                │
biofloc_grading_records ──< biofloc_grading_size_groups >── biofloc_batches (child)
```

### Core Tables

#### 1. `biofloc_tanks`

Represents physical tanks in the facility.

```sql
CREATE TABLE biofloc_tanks (
    id UUID PRIMARY KEY,
    tank_code VARCHAR(50) UNIQUE NOT NULL,
    capacity_liters DECIMAL(12,2) NOT NULL,
    length_m DECIMAL(10,2),
    width_m DECIMAL(10,2),
    depth_m DECIMAL(10,2),
    status tank_status NOT NULL DEFAULT 'active',
    location VARCHAR(200),
    current_batch_id UUID REFERENCES biofloc_batches(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Computed Fields (via triggers):**
- `current_batch_id` - Auto-updated when batches are assigned
- Status reflects current usage

**Key Indexes:**
- `idx_tanks_status`
- `idx_tanks_active`

---

#### 2. `biofloc_batches`

Core entity tracking a group of fish from stocking to harvest.

```sql
CREATE TABLE biofloc_batches (
    id UUID PRIMARY KEY,
    batch_code VARCHAR(50) UNIQUE NOT NULL,
    species VARCHAR(100) NOT NULL,
    source VARCHAR(200),
    stocking_date DATE NOT NULL,

    -- Initial metrics
    initial_count INT NOT NULL,
    initial_avg_weight_g DECIMAL(10,2) NOT NULL,
    initial_total_biomass_kg DECIMAL(12,3) GENERATED,

    -- Current metrics (updated by triggers)
    current_count INT,
    current_avg_weight_g DECIMAL(10,2),
    current_total_biomass_kg DECIMAL(12,3),
    current_tank_id UUID REFERENCES biofloc_tanks(id),

    -- Performance (calculated)
    total_feed_kg DECIMAL(12,3) DEFAULT 0,
    fcr DECIMAL(10,4),  -- Feed Conversion Ratio
    sgr DECIMAL(10,4),  -- Specific Growth Rate
    survival_rate DECIMAL(5,2),
    cycle_duration_days INT,

    -- Grading support (v1.1.0)
    parent_batch_id UUID REFERENCES biofloc_batches(id),
    parent_batch_code VARCHAR(50),
    grading_date DATE,

    status batch_status NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Batch Status Enum:**
```sql
CREATE TYPE batch_status AS ENUM (
    'active',      -- Currently growing
    'transferred', -- Moved to another system/location
    'harvested',   -- Fully harvested
    'graded'       -- Split into child batches
);
```

**Automated Updates:**
- `current_count` - Reduced by mortality and harvest
- `current_avg_weight_g` - Updated by sampling
- `current_total_biomass_kg` - Calculated: `count × avg_weight / 1000`
- `total_feed_kg` - Incremented by feeding sessions
- `fcr` - Calculated: `total_feed / biomass_gain`
- `sgr` - Calculated: `((ln(final_weight) - ln(initial_weight)) / days) × 100`

**Key Indexes:**
- `idx_batches_status`
- `idx_batches_species`
- `idx_batches_parent` (for graded batches)

---

#### 3. `biofloc_batch_tank_assignments`

Tracks batch location history (which tank, when).

```sql
CREATE TABLE biofloc_batch_tank_assignments (
    id UUID PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL = currently active
    transfer_reason transfer_reason,
    fish_count_at_transfer INT,
    avg_weight_at_transfer_g DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Transfer Reason Enum:**
```sql
CREATE TYPE transfer_reason AS ENUM (
    'initial stocking',
    'manual',
    'overcrowding',
    'size_segregation',
    'graded_size_A',
    'graded_size_B',
    'graded_size_C',
    'treatment',
    'other'
);
```

**Constraints:**
- Only one active assignment per batch (`end_date IS NULL`)
- Automatic tank update triggers

---

#### 4. `biofloc_feeding_sessions`

Records feed given to tanks/batches.

```sql
CREATE TABLE biofloc_feeding_sessions (
    id UUID PRIMARY KEY,
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    feeding_date DATE NOT NULL,
    session_number INT DEFAULT 1,  -- 1=morning, 2=afternoon, 3=evening
    feed_time TIME,
    feed_items JSONB NOT NULL,  -- [{sku, quantity_kg, unit_cost, total_cost}]
    total_feed_kg DECIMAL(10,3) NOT NULL,
    total_cost DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Feed Items JSONB Structure:**
```json
[
  {
    "sku": "FEED-001",
    "item_name": "Starter Feed 40% Protein",
    "quantity_kg": 5.5,
    "unit_cost": 45.00,
    "total_cost": 247.50,
    "inventory_transaction_id": "uuid"
  }
]
```

**Automated Actions:**
- Increments `biofloc_batches.total_feed_kg`
- Updates `biofloc_cycle_costs.feed_cost`
- FIFO inventory deduction (if integrated)

---

#### 5. `biofloc_sampling_records`

Fish measurements for growth tracking.

```sql
CREATE TABLE biofloc_sampling_records (
    id UUID PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),
    sample_date DATE NOT NULL,
    sample_size INT NOT NULL,

    -- Weight measurements
    avg_weight_g DECIMAL(10,2) NOT NULL,
    min_weight_g DECIMAL(10,2),
    max_weight_g DECIMAL(10,2),
    std_deviation_g DECIMAL(10,2),

    -- Length measurements
    avg_length_cm DECIMAL(10,2),
    min_length_cm DECIMAL(10,2),
    max_length_cm DECIMAL(10,2),

    -- Calculated
    condition_factor DECIMAL(10,4),  -- (weight / length³) × 100

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Automated Actions:**
- Updates `biofloc_batches.current_avg_weight_g`
- Recalculates `current_total_biomass_kg`
- Updates SGR and FCR

---

#### 6. `biofloc_mortality_records`

Death events tracking.

```sql
CREATE TABLE biofloc_mortality_records (
    id UUID PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),
    mortality_date DATE NOT NULL,
    count INT NOT NULL,
    cause mortality_cause,
    avg_weight_g DECIMAL(10,2),  -- Optional, for biomass loss
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Mortality Cause Enum:**
```sql
CREATE TYPE mortality_cause AS ENUM (
    'disease',
    'stress',
    'unknown',
    'predation',
    'handling',
    'water_quality',
    'starvation',
    'other'
);
```

**Automated Actions:**
- Decrements `biofloc_batches.current_count`
- Recalculates `survival_rate`

---

#### 7. `biofloc_water_tests`

Water quality monitoring.

```sql
CREATE TABLE biofloc_water_tests (
    id UUID PRIMARY KEY,
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    test_date DATE NOT NULL,
    test_time TIME,

    -- Critical parameters
    dissolved_oxygen_mg_l DECIMAL(10,2),
    ph DECIMAL(4,2),
    temperature_c DECIMAL(5,2),
    ammonia_mg_l DECIMAL(10,4),
    nitrite_mg_l DECIMAL(10,4),
    nitrate_mg_l DECIMAL(10,3),
    alkalinity_mg_l DECIMAL(10,2),
    salinity_ppt DECIMAL(5,2),

    -- Biofloc specific
    floc_volume_ml_l DECIMAL(10,2),  -- Settleable solids
    tss_mg_l DECIMAL(10,2),          -- Total suspended solids

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Alert Thresholds (configurable):**
- DO < 4 mg/L → Warning
- Ammonia > 0.5 mg/L → Warning
- Nitrite > 0.3 mg/L → Warning

---

#### 8. `biofloc_tank_inputs`

Chemicals, probiotics, supplements.

```sql
CREATE TABLE biofloc_tank_inputs (
    id UUID PRIMARY KEY,
    tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    batch_id UUID REFERENCES biofloc_batches(id),
    input_date DATE NOT NULL,
    input_time TIME,
    input_type input_type NOT NULL,

    item_sku VARCHAR(50),
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,  -- ml, g, kg, L

    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(12,2),
    inventory_transaction_id UUID,

    reason VARCHAR(200),  -- pH adjustment, ammonia control, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Input Type Enum:**
```sql
CREATE TYPE input_type AS ENUM (
    'chemical',
    'probiotic',
    'carbon_source',
    'mineral',
    'other'
);
```

**Automated Actions:**
- Updates `biofloc_cycle_costs.chemical_cost`
- Optional inventory deduction

---

#### 9. `biofloc_harvests`

Harvest events and revenue tracking.

```sql
CREATE TABLE biofloc_harvests (
    id UUID PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    tank_id UUID REFERENCES biofloc_tanks(id),
    harvest_date DATE NOT NULL,
    harvest_type harvest_type NOT NULL,

    fish_count INT NOT NULL,
    total_weight_kg DECIMAL(12,3) NOT NULL,
    avg_weight_g DECIMAL(10,2) GENERATED,

    -- Quality grading
    grade_a_kg DECIMAL(12,3),
    grade_b_kg DECIMAL(12,3),
    grade_c_kg DECIMAL(12,3),
    reject_kg DECIMAL(12,3),

    -- Sales
    buyer VARCHAR(200),
    price_per_kg DECIMAL(10,2),
    total_revenue DECIMAL(15,2),

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

**Harvest Type Enum:**
```sql
CREATE TYPE harvest_type AS ENUM (
    'partial',    -- Selective harvest
    'final',      -- Complete harvest
    'thinning'    -- Reduce stocking density
);
```

**Automated Actions:**
- Decrements `biofloc_batches.current_count`
- Updates `biofloc_cycle_costs.total_revenue`
- Marks batch as 'harvested' if final harvest

---

#### 10. `biofloc_grading_records` (v1.1.0)

Master record of grading events.

```sql
CREATE TABLE biofloc_grading_records (
    id UUID PRIMARY KEY,
    source_batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    source_batch_code VARCHAR(50) NOT NULL,
    source_tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    grading_date DATE NOT NULL,
    total_fish_graded INT NOT NULL,
    size_groups_count INT NOT NULL CHECK (size_groups_count BETWEEN 2 AND 3),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);
```

---

#### 11. `biofloc_grading_size_groups` (v1.1.0)

Detailed size group information from grading.

```sql
CREATE TABLE biofloc_grading_size_groups (
    id UUID PRIMARY KEY,
    grading_record_id UUID NOT NULL REFERENCES biofloc_grading_records(id),
    size_label VARCHAR(10) NOT NULL,  -- A, B, C
    child_batch_id UUID NOT NULL REFERENCES biofloc_batches(id),
    child_batch_code VARCHAR(50) NOT NULL,

    fish_count INT NOT NULL,
    avg_weight_g DECIMAL(10,2) NOT NULL,
    biomass_kg DECIMAL(12,3) NOT NULL,

    destination_tank_id UUID NOT NULL REFERENCES biofloc_tanks(id),
    destination_tank_code VARCHAR(50) NOT NULL,

    -- Cost allocation
    allocated_feed_cost DECIMAL(12,2) DEFAULT 0,
    biomass_percentage DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose:**
- Tracks how parent batch was split
- Records proportional cost allocation
- Maintains full traceability

---

#### 12. `biofloc_cycle_costs`

Comprehensive cost and revenue tracking per batch.

```sql
CREATE TABLE biofloc_cycle_costs (
    id UUID PRIMARY KEY,
    batch_id UUID NOT NULL UNIQUE REFERENCES biofloc_batches(id),

    -- Cost breakdown
    fingerling_cost DECIMAL(12,2) DEFAULT 0,
    feed_cost DECIMAL(12,2) DEFAULT 0,
    chemical_cost DECIMAL(12,2) DEFAULT 0,
    labor_cost DECIMAL(12,2) DEFAULT 0,
    utilities_cost DECIMAL(12,2) DEFAULT 0,
    other_cost DECIMAL(12,2) DEFAULT 0,

    -- Total (computed column)
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (
        fingerling_cost + feed_cost + chemical_cost +
        labor_cost + utilities_cost + other_cost
    ) STORED,

    -- Revenue
    total_revenue DECIMAL(12,2) DEFAULT 0,

    -- Profitability (computed)
    gross_profit DECIMAL(12,2) GENERATED ALWAYS AS (
        total_revenue - (fingerling_cost + feed_cost + chemical_cost +
                        labor_cost + utilities_cost + other_cost)
    ) STORED,

    -- Per-kg metrics
    cost_per_kg DECIMAL(10,2),
    profit_per_kg DECIMAL(10,2),

    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Key Features:**
- Automatically updated by feeding, inputs, harvests
- Used for ROI and profitability analysis
- Proportionally split during grading

---

### Database Triggers & Functions

#### 1. Auto-update Current Metrics

```sql
-- When mortality occurs, decrement current_count
CREATE OR REPLACE FUNCTION update_batch_on_mortality()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE biofloc_batches
    SET current_count = current_count - NEW.count,
        current_total_biomass_kg = (current_count - NEW.count) * current_avg_weight_g / 1000,
        updated_at = NOW()
    WHERE id = NEW.batch_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_batch_mortality
AFTER INSERT ON biofloc_mortality_records
FOR EACH ROW
EXECUTE FUNCTION update_batch_on_mortality();
```

#### 2. Auto-update Feed Costs

```sql
CREATE OR REPLACE FUNCTION update_feed_cost()
RETURNS TRIGGER AS $$
BEGIN
    -- Update batch total feed
    UPDATE biofloc_batches
    SET total_feed_kg = total_feed_kg + NEW.total_feed_kg
    WHERE id = NEW.batch_id;

    -- Update cycle costs
    UPDATE biofloc_cycle_costs
    SET feed_cost = feed_cost + COALESCE(NEW.total_cost, 0),
        updated_at = NOW()
    WHERE batch_id = NEW.batch_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### 3. Auto-calculate FCR & SGR

```sql
CREATE OR REPLACE FUNCTION calculate_performance_metrics(p_batch_id UUID)
RETURNS VOID AS $$
DECLARE
    v_batch RECORD;
    v_initial_biomass DECIMAL;
    v_current_biomass DECIMAL;
    v_biomass_gain DECIMAL;
    v_days INT;
BEGIN
    SELECT * INTO v_batch FROM biofloc_batches WHERE id = p_batch_id;

    v_initial_biomass := v_batch.initial_total_biomass_kg;
    v_current_biomass := v_batch.current_total_biomass_kg;
    v_biomass_gain := v_current_biomass - v_initial_biomass;
    v_days := EXTRACT(DAY FROM NOW() - v_batch.stocking_date);

    -- FCR = total_feed_kg / biomass_gain_kg
    UPDATE biofloc_batches
    SET fcr = CASE
        WHEN v_biomass_gain > 0 THEN total_feed_kg / v_biomass_gain
        ELSE NULL
    END,
    -- SGR = ((ln(final_weight) - ln(initial_weight)) / days) * 100
    sgr = CASE
        WHEN v_days > 0 AND current_avg_weight_g > 0 THEN
            ((LN(current_avg_weight_g) - LN(initial_avg_weight_g)) / v_days) * 100
        ELSE NULL
    END,
    survival_rate = (current_count::DECIMAL / initial_count) * 100,
    cycle_duration_days = v_days
    WHERE id = p_batch_id;
END;
$$ LANGUAGE plpgsql;
```

---

## API Reference

### Base URL
```
/api/v1/biofloc
```

### Authentication
All endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User must have `biofloc` module access

---

### Tanks Endpoints

#### `GET /tanks`
Get list of tanks with filters.

**Query Parameters:**
- `status` (optional): `active | maintenance | empty`
- `is_active` (optional): `true | false`
- `page` (default: 1)
- `limit` (default: 50, max: 100)

**Response:**
```json
{
  "tanks": [
    {
      "id": "uuid",
      "tank_code": "T-001",
      "capacity_liters": 50000,
      "length_m": 10.0,
      "width_m": 5.0,
      "depth_m": 1.0,
      "status": "active",
      "location": "Block A, Row 1",
      "current_batch_id": "uuid",
      "batch_code": "B-001",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 50
}
```

---

#### `POST /tanks`
Create new tank.

**Request Body:**
```json
{
  "tank_code": "T-010",
  "capacity_liters": 50000,
  "length_m": 10.0,
  "width_m": 5.0,
  "depth_m": 1.0,
  "location": "Block B, Row 2",
  "notes": "New circular tank"
}
```

**Response:** `201 Created` with tank object

---

### Batches Endpoints

#### `GET /batches`
Get list of batches.

**Query Parameters:**
- `status`: `active | transferred | harvested | graded`
- `species`: Filter by species name
- `page`, `limit`

**Response:**
```json
{
  "batches": [
    {
      "id": "uuid",
      "batch_code": "B-001",
      "species": "Litopenaeus vannamei",
      "source": "Hatchery ABC",
      "stocking_date": "2025-01-01",
      "initial_count": 50000,
      "initial_avg_weight_g": 0.5,
      "current_count": 48500,
      "current_avg_weight_g": 12.5,
      "current_tank_id": "uuid",
      "current_tank_code": "T-001",
      "total_feed_kg": 150.5,
      "fcr": 1.25,
      "sgr": 0.85,
      "survival_rate": 97.0,
      "cycle_duration_days": 60,
      "status": "active"
    }
  ],
  "total": 8,
  "page": 1,
  "limit": 50
}
```

---

#### `POST /batches`
Create new batch with initial tank assignment.

**Request Body:**
```json
{
  "batch_code": "B-010",
  "species": "Litopenaeus vannamei",
  "source": "Hatchery XYZ",
  "tank_id": "uuid",
  "stocking_date": "2025-11-19",
  "initial_count": 50000,
  "initial_avg_weight_g": 0.5,
  "notes": "PL12 stage"
}
```

**Response:** `201 Created` with batch object

---

#### `POST /batches/grading`
Grade a batch and split into size groups (v1.1.0).

**Request Body:**
```json
{
  "source_batch_id": "uuid",
  "source_tank_id": "uuid",
  "grading_date": "2025-03-15",
  "size_groups": [
    {
      "size_label": "A",
      "fish_count": 20000,
      "avg_weight_g": 15.0,
      "destination_tank_id": "uuid-tank-5"
    },
    {
      "size_label": "B",
      "fish_count": 28000,
      "avg_weight_g": 10.0,
      "destination_tank_id": "uuid-tank-6"
    }
  ],
  "notes": "60-day grading, 2 size groups"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid-grading-record",
  "source_batch_id": "uuid",
  "source_batch_code": "B-001",
  "grading_date": "2025-03-15",
  "total_fish_graded": 48000,
  "size_groups_created": 2,
  "child_batches": [
    {
      "batch_id": "uuid-child-a",
      "batch_code": "B-001-A",
      "size_label": "A",
      "fish_count": 20000,
      "avg_weight_g": 15.0,
      "destination_tank_id": "uuid-tank-5",
      "destination_tank_code": "T-005"
    },
    {
      "batch_id": "uuid-child-b",
      "batch_code": "B-001-B",
      "size_label": "B",
      "fish_count": 28000,
      "avg_weight_g": 10.0,
      "destination_tank_id": "uuid-tank-6",
      "destination_tank_code": "T-006"
    }
  ],
  "notes": "60-day grading, 2 size groups",
  "created_at": "2025-03-15T10:30:00"
}
```

**What Happens:**
1. Creates child batches: `B-001-A`, `B-001-B`
2. Allocates feed costs proportionally by biomass
3. Sets `initial_weight_g` = `avg_weight_g` for children
4. Inherits original `stocking_date` from parent
5. Marks parent batch as `status = 'graded'`
6. Creates tank assignments for child batches

---

### Feeding Endpoints

#### `POST /feeding`
Record feeding session (multi-tank supported).

**Request Body:**
```json
{
  "tank_id": "uuid",
  "feeding_date": "2025-11-19",
  "session_number": 1,
  "feed_time": "08:00:00",
  "feed_items": [
    {
      "sku": "FEED-001",
      "quantity_kg": 5.5
    }
  ],
  "notes": "Morning feeding"
}
```

**Response:** `201 Created` with feeding session

**FIFO Inventory Deduction:**
- Automatically deducts from inventory (if integrated)
- Calculates cost using FIFO method
- Updates `biofloc_cycle_costs.feed_cost`

---

### Mortality Endpoints

#### `POST /mortality`
Record mortality event (multi-batch support).

**Request Body:**
```json
{
  "batch_id": "uuid",
  "tank_id": "uuid",
  "mortality_date": "2025-11-19",
  "count": 150,
  "cause": "disease",
  "avg_weight_g": 12.5,
  "notes": "White spot observed"
}
```

**Response:** `201 Created`

**Automated Actions:**
- Decrements `current_count` in batch
- Recalculates `survival_rate`
- Generates dashboard alert if significant

---

### Harvest Endpoints

#### `POST /harvests`
Record harvest (multi-batch support).

**Request Body:**
```json
{
  "batch_id": "uuid",
  "tank_id": "uuid",
  "harvest_date": "2025-11-19",
  "harvest_type": "partial",
  "fish_count": 5000,
  "total_weight_kg": 62.5,
  "grade_a_kg": 50.0,
  "grade_b_kg": 10.0,
  "grade_c_kg": 2.0,
  "reject_kg": 0.5,
  "buyer": "Market ABC",
  "price_per_kg": 250.00,
  "notes": "First harvest"
}
```

**Response:** `201 Created`

**Automated Actions:**
- Decrements `current_count`
- Calculates `total_revenue` = `total_weight_kg × price_per_kg`
- Updates `biofloc_cycle_costs.total_revenue`
- Marks batch as `harvested` if final harvest

---

### Water Tests Endpoints

#### `POST /water-tests`
Record water quality test (multi-tank support).

**Request Body:**
```json
{
  "tank_id": "uuid",
  "test_date": "2025-11-19",
  "test_time": "08:00:00",
  "dissolved_oxygen_mg_l": 5.2,
  "ph": 7.8,
  "temperature_c": 28.5,
  "ammonia_mg_l": 0.02,
  "nitrite_mg_l": 0.01,
  "nitrate_mg_l": 5.0,
  "alkalinity_mg_l": 120.0,
  "floc_volume_ml_l": 15.0,
  "notes": "Good conditions"
}
```

**Response:** `201 Created`

---

### Dashboard Endpoint

#### `GET /dashboard`
Get overview metrics.

**Response:**
```json
{
  "active_tanks": 12,
  "available_tanks": 3,
  "maintenance_tanks": 0,
  "active_batches": 8,
  "total_fish_count": 385000,
  "total_biomass_kg": 4812.5,
  "avg_tank_utilization": 80.0,
  "low_do_alerts": 1,
  "high_ammonia_alerts": 0,
  "recent_mortalities_7d": 350,
  "upcoming_harvests": 2
}
```

---

## Service Layer Logic

### Key Service Functions

#### `record_grading(request, user_id)`

**Purpose:** Grade a batch and create child batches with proportional cost allocation.

**Algorithm:**
1. Fetch source batch with cycle costs
2. Validate:
   - Batch is active
   - Total graded fish = source batch count
   - All destination tanks exist
3. Calculate biomass per size group
4. Calculate cost allocation ratios:
   ```
   ratio_A = biomass_A / total_biomass
   allocated_feed_cost_A = ratio_A × parent_feed_cost
   ```
5. Begin transaction:
   - Create grading record
   - For each size group:
     - Create child batch (code: `Parent-A`, `Parent-B`)
     - Set `initial_weight_g` = `avg_weight_g` at grading
     - Inherit `stocking_date` from parent
     - Create tank assignment
     - Initialize cycle costs with allocated amounts
     - Create size group record
   - Mark parent as `status = 'graded'`
   - End parent tank assignments
6. Return grading response with child batch IDs

**Example:**
```
Parent: B-001 (48,000 fish, ₹50,000 feed cost)
Grading on Day 60:
  - Size A: 20,000 @ 15g = 300kg (50% biomass) → ₹25,000 feed cost
  - Size B: 28,000 @ 10g = 280kg (46.7% biomass) → ₹23,350 feed cost
  - Total: 600kg
```

---

#### `calculate_performance_metrics(batch_id)`

Recalculates FCR, SGR, survival rate.

**Called After:**
- Sampling (weight update)
- Feeding (feed increment)
- Mortality (count decrement)
- Harvest (count decrement)

---

## Frontend Architecture

### State Management

**React Query** handles all server state:
- Automatic caching
- Background refetching
- Optimistic updates
- Query invalidation on mutations

**Example:**
```javascript
const { data: batches, isLoading } = useQuery(
  'bioflocBatches',
  () => bioflocAPI.getBatches({ status: 'active' })
);

const mutation = useMutation(
  data => bioflocAPI.recordGrading(data),
  {
    onSuccess: () => {
      queryClient.invalidateQueries('bioflocBatches');
      queryClient.invalidateQueries('bioflocTanks');
    }
  }
);
```

### Form Patterns

**Multi-Tank Forms:**
- Session-level data (shared): date, time, type
- Per-tank data (array): quantity, notes

**Multi-Batch Forms:**
- Tank selection → fetch batches in tank
- Radio toggle for allocation mode
- Real-time allocation preview
- Validation before submit

---

## Performance Considerations

### Database Indexes

Critical indexes for performance:
```sql
CREATE INDEX idx_batches_status ON biofloc_batches(status);
CREATE INDEX idx_batches_tank ON biofloc_batches(current_tank_id);
CREATE INDEX idx_feeding_batch_date ON biofloc_feeding_sessions(batch_id, feeding_date);
CREATE INDEX idx_sampling_batch_date ON biofloc_sampling_records(batch_id, sample_date DESC);
CREATE INDEX idx_mortality_batch_date ON biofloc_mortality_records(batch_id, mortality_date);
CREATE INDEX idx_harvests_batch_date ON biofloc_harvests(batch_id, harvest_date);
CREATE INDEX idx_grading_source_batch ON biofloc_grading_records(source_batch_id);
```

### Query Optimization

**Computed Columns:**
- Use `GENERATED ALWAYS AS` for frequently calculated fields
- Stored vs. virtual: stored for expensive calculations

**Materialized Views (Future):**
```sql
CREATE MATERIALIZED VIEW mv_batch_performance AS
SELECT
  b.id,
  b.batch_code,
  COUNT(DISTINCT f.id) as feeding_count,
  COUNT(DISTINCT s.id) as sampling_count,
  COALESCE(SUM(m.count), 0) as total_mortality
FROM biofloc_batches b
LEFT JOIN biofloc_feeding_sessions f ON f.batch_id = b.id
LEFT JOIN biofloc_sampling_records s ON s.batch_id = b.id
LEFT JOIN biofloc_mortality_records m ON m.batch_id = b.id
GROUP BY b.id, b.batch_code;

-- Refresh daily
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_batch_performance;
```

---

## Security & Permissions

### Authentication
- JWT-based authentication required
- Token expiry: configurable (default 24h)
- Refresh token mechanism

### Authorization
- Module-level access control via `user_module_access` table
- User must have `biofloc` module permission
- Row-level security (future): filter by farm/organization

### Data Validation
- **Backend:** Pydantic schemas validate all inputs
- **Frontend:** Form validation before submission
- **Database:** Constraints and triggers enforce integrity

### Audit Trail
All tables include:
- `created_at` - Timestamp of creation
- `created_by` - User UUID who created
- `updated_at` - Last update timestamp (where applicable)

---

## Appendix: Key Calculations

### FCR (Feed Conversion Ratio)
```
FCR = total_feed_kg / biomass_gain_kg

Where:
  biomass_gain_kg = current_biomass_kg - initial_biomass_kg
```

### SGR (Specific Growth Rate)
```
SGR = ((ln(final_weight_g) - ln(initial_weight_g)) / days) × 100

Where:
  days = cycle_duration_days or grading_days
```

### Survival Rate
```
survival_rate = (current_count / initial_count) × 100
```

### Biomass Calculation
```
biomass_kg = (count × avg_weight_g) / 1000
```

### Proportional Cost Allocation (Grading)
```
For each size group:
  biomass_ratio = group_biomass / total_biomass
  allocated_cost = parent_cost × biomass_ratio

Example:
  Parent feed cost: ₹10,000
  Group A biomass: 300kg (50%)
  Group B biomass: 300kg (50%)

  Group A allocated: ₹10,000 × 0.50 = ₹5,000
  Group B allocated: ₹10,000 × 0.50 = ₹5,000
```

---

**End of Technical Guide**

For operational procedures and user workflows, see [User Guide](./user-guide.md).
