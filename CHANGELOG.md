# Changelog

All notable changes to the Farm Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.0] - 2025-11-22

### Added - Units of Measurement System

#### Backend & Database
- **Created standardized units of measurement system**
  - Database table `unit_of_measurements` with 25 pre-populated units
  - Categories: weight, volume, count, length, area
  - Fields: unit_name, abbreviation, category, is_active
  - Migration: `sql_scripts/v1.11.0_unit_of_measurements.sql`

- **Full CRUD API for units management**
  - New service: `backend/app/services/units_service.py` (v1.0.0)
  - New routes: `backend/app/routes/units.py`
  - New schemas: `backend/app/schemas/units.py`
  - Endpoints:
    * GET `/api/v1/units` - List units with filtering
    * GET `/api/v1/units/categories` - List categories with counts
    * GET `/api/v1/units/{id}` - Get single unit
    * POST `/api/v1/units` - Create new unit
    * PUT `/api/v1/units/{id}` - Update unit
    * DELETE `/api/v1/units/{id}` - Permanent delete (if not in use)
    * POST `/api/v1/units/{id}/deactivate` - Soft delete
    * POST `/api/v1/units/{id}/reactivate` - Restore unit

- **Smart delete logic**
  - Units linked to items: Can only be deactivated
  - Units not in use: Can be permanently deleted
  - Returns item_count with each unit for smart UI decisions
  - Auto-updates item_master when unit names change

#### Frontend
- **Item Master Form Enhancement** (InventoryModule v3.1.0)
  - Replaced unit text input with Autocomplete dropdown
  - Shows all active units from database
  - Supports free text entry for custom units (freeSolo)
  - Better UX with standardized options

- **Units Management Settings Page** (UnitsSettings v1.0.0)
  - New admin page: `/admin/units`
  - Create, edit, delete, and deactivate units
  - Table view with active/inactive sections
  - Visual indicators for units in use
  - Smart action buttons based on item_count
  - Category-based organization
  - Real-time updates with React Query

- **Frontend API Integration** (api/index.js v1.3.0)
  - Added `unitsAPI` with all CRUD operations
  - Integrated with React Query for caching
  - Automatic cache invalidation

### Changed
- **Inventory Module**
  - Unit field now uses standardized dropdown instead of free text
  - Improved data consistency across inventory items
  - Admin Panel (v1.8.0) now includes Units settings route

### Design Decisions
- Database-backed approach for flexibility
- Can add/edit units without code changes
- Supports future features (unit conversions, metadata)
- Follows same soft-delete pattern as other entities
- Category system allows grouping similar units

### Migration Notes
- **Run migration:** `sql_scripts/v1.11.0_unit_of_measurements.sql`
- No data migration needed for existing items
- Existing item units remain as-is (free text)
- New items will use standardized units from dropdown

---

## [1.9.0] - 2025-11-22

### Fixed - Inventory Module Critical Issues

#### Stock Adjustments
- **Fixed AttributeError when creating stock adjustments**
  - Root cause: `execute_query_tx()` was receiving `conn` as positional argument instead of keyword argument
  - Impact: Stock adjustment creation endpoint returned 500 error
  - Solution: Changed all `execute_query_tx(conn, ...)` calls to `execute_query_tx(..., conn=conn)`
  - Files: `backend/app/services/inventory_service.py`

- **Fixed ResponseValidationError when loading adjustments list**
  - Root cause: `adjusted_by` UUID field not cast to text in SQL query
  - Impact: Adjustments list endpoint returned 500 error after creating adjustments
  - Solution: Cast `adjusted_by::text` in `get_stock_adjustments_list()` query
  - Files: `backend/app/services/inventory_service.py`

- **Fixed inventory value not updating on stock adjustments**
  - Root cause: Adjustments only updated `item_master.current_qty` but not batch quantities
  - Impact: Inventory value (calculated from batches) remained unchanged when adjusting stock
  - Solution: Complete rewrite of `create_stock_adjustment()` to properly update batches
    - Decrease adjustments: Deduct from batches using FIFO (oldest first)
    - Increase adjustments: Add to most recent batch or create adjustment batch
    - Recount adjustments: Calculate difference and apply as increase/decrease
  - Files: `backend/app/services/inventory_service.py`

#### Purchase Order Receiving
- **Fixed quantity doubling when receiving PO items**
  - Root cause: Database trigger automatically updates `current_qty`, but code was also manually updating it
  - Impact: Receiving 10 kg of stock resulted in 20 kg being added to inventory
  - Solution: Removed manual `UPDATE item_master` statement from `receive_purchase_order()`
  - Files: `backend/app/services/inventory_service.py`

- **Fixed stock not refreshing after PO receiving**
  - Root cause: React Query cache not invalidated for inventory items after receiving PO
  - Impact: Had to manually refresh page to see updated stock after receiving goods
  - Solution: Added `queryClient.invalidateQueries('inventoryItems')` and `inventoryDashboard` to PO receive mutation
  - Files: `frontend/src/pages/InventoryModule.jsx`

### Added

#### Data Reconciliation Tools
- **SQL Script: Fix Batch Quantities**
  - Path: `sql_scripts/fix_batch_quantities_after_adjustments.sql`
  - Purpose: One-time fix for batch quantities out of sync with item quantities
  - Features:
    - Identifies items where `current_qty` ≠ `SUM(batch.remaining_qty)`
    - Sets batches to 0 for items with `current_qty = 0`
    - Proportionally adjusts batches for items with `current_qty > 0`
    - Shows before/after inventory values
    - Runs in transaction (all-or-nothing)

- **Python Utility: Inventory Batch Reconciliation**
  - Path: `backend/app/utils/fix_inventory_batches.py`
  - Purpose: Same as SQL script but with detailed progress reporting
  - Usage: `python -m backend.app.utils.fix_inventory_batches`
  - Features:
    - Detailed step-by-step progress display
    - Before/after inventory value comparison
    - Verification of fixes
    - Better error handling and reporting

### Changed

#### Code Quality Improvements
- Standardized all `execute_query_tx()` calls to use `conn=conn` as keyword argument
- Added inline documentation explaining database trigger behavior
- Enhanced transaction logging in stock adjustments to include batch details

#### Database Interaction
- Stock adjustments now leverage existing database trigger `trigger_update_item_qty_on_batch_change`
- Removed redundant manual quantity updates where triggers handle automatically
- Improved consistency with FIFO costing methodology across all stock operations

---

## Version History

For detailed version history of individual modules, see:
- Backend Inventory Service: `backend/app/services/inventory_service.py` (Version 1.9.0)
- Database Schema: `sql_scripts/v*.sql`

---

## Migration Notes

### From 1.8.x to 1.9.0

If you have existing stock adjustment data with incorrect inventory values:

1. **Run the reconciliation utility** to fix batch quantities:
   ```bash
   python -m backend.app.utils.fix_inventory_batches
   ```
   OR
   ```bash
   psql $DATABASE_URL -f sql_scripts/fix_batch_quantities_after_adjustments.sql
   ```

2. **Verify inventory values** after reconciliation match expected totals

3. **Future adjustments** will work correctly with the updated code

### Breaking Changes
- None - all changes are backward compatible bug fixes

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/akinich/farm2-app-fast-api/issues
- Documentation: `/docs`
