# Biofloc Aquaculture Management Module

**Version:** 1.1.0
**Last Updated:** 2025-11-19
**Status:** Production Ready ✅

## Overview

The Biofloc Aquaculture Management Module is a comprehensive system for managing biofloc-based fish farming operations. It tracks the complete lifecycle of fish batches from stocking through grading to harvest, with detailed monitoring of feeding, water quality, mortality, and operational costs.

### Key Capabilities

- **Multi-Batch Tank Support** - Tanks can contain multiple batches simultaneously
- **Grading with Batch Splitting** - Separate fish by size while maintaining cost history
- **Smart Harvest Allocation** - Weight-based matching for multi-batch harvesting
- **Cost Tracking** - Proportional feed cost allocation across batch lifecycle
- **Multi-Tank Operations** - Record feeding, water tests, and inputs for multiple tanks at once
- **Performance Analytics** - FCR, SGR, survival rate, ROI calculations
- **Full Traceability** - Parent-child batch relationships, complete history tracking

## Quick Start

### Prerequisites

- PostgreSQL database (>= 12)
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Farm Management System core installed

### Installation

1. **Run database migrations:**
   ```bash
   psql -d your_database -f backend/migrations/biofloc_module_v1.0.0.sql
   psql -d your_database -f backend/migrations/biofloc_grading_v1.0.1.sql
   ```

2. **Register module in system:**
   ```sql
   INSERT INTO modules (name, description, is_active)
   VALUES ('biofloc', 'Biofloc aquaculture management', true)
   ON CONFLICT (name) DO NOTHING;
   ```

3. **Grant user access:**
   ```sql
   INSERT INTO user_module_access (user_id, module_name)
   VALUES ('your-user-uuid', 'biofloc');
   ```

4. **Access the module:**
   - Navigate to `/biofloc` in your application
   - Dashboard displays at `/biofloc/dashboard`

## Module Structure

```
biofloc/
├── Dashboard          # Overview, metrics, alerts
├── Tanks             # Tank management
├── Batches           # Batch lifecycle tracking
├── Feeding           # Multi-tank feeding sessions
├── Sampling          # Fish sampling measurements
├── Mortality         # Mortality tracking (multi-batch support)
├── Water Tests       # Multi-tank water quality testing
├── Tank Inputs       # Chemicals, probiotics, supplements
├── Harvests          # Harvest recording (multi-batch support)
└── Transfer          # Normal transfer & graded transfer
```

## Core Concepts

### Batches

A **batch** represents a group of fish from the same stocking event. Each batch tracks:
- Population count and average weight
- Stocking date and cycle duration
- Feed costs and performance metrics (FCR, SGR)
- Current tank location
- Historical data (feedings, samplings, mortalities, etc.)

**Batch Status Flow:**
```
active → transferred → harvested
       → graded (when split by size)
```

### Multi-Batch Tanks

Tanks can contain **multiple active batches** simultaneously (e.g., after grading different size groups into the same tank, or combining batches).

**Smart Features for Multi-Batch Scenarios:**
- **Mortality:** Auto-split proportionally OR manual allocation per batch
- **Harvest:** Weight-based matching (90% from closest weight batch) OR proportional split
- **Feeding:** Tank-level recording with automatic allocation to all batches

### Grading (Batch Splitting)

**Grading** separates a batch into 2-3 size groups during the growth cycle, creating child batches with:
- ✅ **Proportional cost allocation** based on biomass
- ✅ **Original stocking date** inherited for accurate cycle calculations
- ✅ **Initial weight** set to weight at grading
- ✅ **Parent-child relationship** for full traceability

**Example:**
```
Batch-001 (500 fish, ₹10,000 feed cost)
   ↓ Grade on Day 60
   ├─ Batch-001-A: 200 fish @ 150g → Tank-5 (₹5,000 feed cost, 50% biomass)
   └─ Batch-001-B: 300 fish @ 100g → Tank-6 (₹5,000 feed cost, 50% biomass)
```

Both children inherit the original stocking date, so cycle duration continues from the parent.

## Documentation

- **[Technical Guide](./technical-guide.md)** - Architecture, database schema, API reference for developers
- **[User Guide](./user-guide.md)** - Features, workflows, and operational procedures

## Key Features by Component

### Dashboard
- Active tanks and batches overview
- Total fish count and biomass
- Recent mortality alerts
- Low DO and high ammonia warnings
- Upcoming harvests

### Tanks Management
- Create/edit tanks with capacity and dimensions
- Track tank status (active, maintenance, empty)
- View current batch assignments
- Tank history and utilization

### Batches Management
- Create new batches with stocking details
- View batch lifecycle and performance
- Monitor growth curves
- Track costs and profitability

### Feeding (Multi-Tank)
- Record feed for multiple tanks in one session
- FIFO inventory deduction
- Automatic cost tracking per batch
- Session-based recording (morning, afternoon, evening)

### Sampling
- Record fish measurements (weight, length)
- Calculate condition factor
- Track growth rates
- Support for statistical analysis (min, max, std dev)

### Mortality (Multi-Batch Support)
- **Option 1A (Auto-split):** Proportional allocation by population
- **Option 1B (Manual split):** User specifies deaths per batch
- Track causes (disease, stress, water quality, etc.)
- Biomass loss calculation

### Water Tests (Multi-Tank)
- Test multiple tanks in one session
- Track critical parameters (DO, pH, ammonia, nitrite, nitrate)
- Temperature and salinity monitoring
- Historical trend analysis

### Tank Inputs (Multi-Tank)
- Record chemicals, probiotics, carbon sources
- Multi-tank application support
- Cost tracking per input
- Inventory integration (optional SKU tracking)

### Harvests (Multi-Batch Support)
- **Option 2B (Smart):** Weight-based batch matching
- **Option 2A (Auto-split):** Proportional allocation
- Grade recording (A, B, C, reject)
- Revenue tracking

### Transfer & Grading
- **Normal Transfer:** Move batch tank-to-tank
- **Graded Transfer:** Split by size with cost allocation
- Create child batches (Batch-001-A, Batch-001-B)
- Maintain parent-child relationships

## Performance Metrics

The system automatically calculates:

- **FCR (Feed Conversion Ratio):** `total_feed_kg / biomass_gain_kg`
- **SGR (Specific Growth Rate):** `((ln(final_weight) - ln(initial_weight)) / days) × 100`
- **Survival Rate:** `(final_count / initial_count) × 100`
- **Biomass Gain:** `final_biomass - initial_biomass`
- **Average Daily Gain:** `(biomass_gain × 1000) / cycle_days`
- **ROI (Return on Investment):** `(gross_profit / total_cost) × 100`
- **Cost per kg:** `total_cost / total_harvested_kg`
- **Profit per kg:** `gross_profit / total_harvested_kg`

## Technology Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL with asyncpg
- Pydantic for validation

**Frontend:**
- React with functional components
- Material-UI (MUI) components
- React Query for state management
- React Router for navigation

## Database Tables

Core tables:
- `biofloc_tanks` - Tank infrastructure
- `biofloc_batches` - Batch records
- `biofloc_batch_tank_assignments` - Batch-tank relationships
- `biofloc_feeding_sessions` - Feeding records
- `biofloc_sampling_records` - Fish sampling data
- `biofloc_mortality_records` - Mortality events
- `biofloc_water_tests` - Water quality tests
- `biofloc_tank_inputs` - Chemicals, probiotics, etc.
- `biofloc_harvests` - Harvest events
- `biofloc_grading_records` - Grading events
- `biofloc_grading_size_groups` - Size group details
- `biofloc_cycle_costs` - Cost and revenue tracking

## API Endpoints

Base URL: `/api/v1/biofloc`

**Core Resources:**
- `GET/POST /tanks` - Tank management
- `GET/POST /batches` - Batch management
- `POST /batches/grading` - Batch grading
- `POST /batches/{id}/transfer` - Batch transfer
- `GET/POST /feeding` - Feeding sessions
- `GET/POST /sampling` - Sampling records
- `GET/POST /mortality` - Mortality events
- `GET/POST /water-tests` - Water quality tests
- `GET/POST /tank-inputs` - Tank inputs
- `GET/POST /harvests` - Harvest records
- `GET /dashboard` - Dashboard metrics

See [Technical Guide](./technical-guide.md) for complete API reference.

## Version History

### v1.1.0 (2025-11-19)
- ✅ Added grading with batch splitting (Option B)
- ✅ Proportional feed cost allocation based on biomass
- ✅ Multi-batch harvest support (2B/2A allocation)
- ✅ Multi-batch mortality support (1A/1B allocation)
- ✅ Tank inputs functionality
- ✅ Complete frontend forms
- ✅ Database migration for grading

### v1.0.0 (2025-11-18)
- ✅ Initial release
- ✅ Core biofloc operations
- ✅ Tank and batch management
- ✅ Feeding, sampling, mortality, water tests
- ✅ Dashboard and reporting

## Support & Contributing

For issues, questions, or contributions:
- Check the documentation in `docs/biofloc/`
- Review the code comments in source files
- Refer to the database schema in migration files

## License

Part of the Farm Management System
© 2025 All rights reserved
