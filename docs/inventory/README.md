# Inventory Management Module

**Version:** 1.5.0
**Last Updated:** 2025-11-19
**Status:** Production Ready ✅

## Overview

The Inventory Management Module is a comprehensive stock tracking and control system designed for farm operations. It provides complete visibility into inventory levels, automated FIFO (First-In-First-Out) stock deduction, purchase order management, supplier tracking, and seamless integration with other farm modules like biofloc, hatchery, and nursery operations.

### Key Capabilities

- **Item Master Management** - Centralized catalog of all inventory items
- **FIFO Stock Control** - Automated first-in-first-out batch tracking
- **Batch Operations** - Atomic multi-item deductions for complex operations
- **Purchase Order Management** - Complete PO lifecycle from creation to receipt
- **Supplier Management** - Contact and relationship tracking
- **Category Management** - Organize items by category
- **Stock Reservations** - Soft-lock inventory for planned operations
- **Low Stock Alerts** - Automatic alerts when inventory falls below threshold
- **Expiry Tracking** - Monitor batch expiration dates
- **Cost Tracking** - Weighted average cost calculation
- **Transaction History** - Complete audit trail of all inventory movements
- **Module Integration** - Cross-module consumption tracking and reporting
- **Bulk Operations** - Efficient multi-item fetch and deduction

## Quick Start

### Prerequisites

- PostgreSQL database (>= 12)
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Farm Management System core installed

### Installation

1. **Run database migrations:**
   ```bash
   psql -d your_database -f backend/migrations/inventory_module_v1.0.0.sql
   ```

2. **Register module in system:**
   ```sql
   INSERT INTO modules (name, description, is_active)
   VALUES ('inventory', 'Inventory management system', true)
   ON CONFLICT (name) DO NOTHING;
   ```

3. **Grant user access:**
   ```sql
   INSERT INTO user_module_access (user_id, module_name)
   VALUES ('your-user-uuid', 'inventory');
   ```

4. **Access the module:**
   - Navigate to `/inventory` in your application
   - Dashboard displays at `/inventory/dashboard`

## Module Structure

```
inventory/
├── Dashboard          # Overview, metrics, alerts
├── Items             # Item master management
├── Stock Operations  # Add/use stock, adjustments
├── Current Stock     # Real-time stock levels
├── Purchase Orders   # PO management
├── Suppliers         # Supplier information
├── Categories        # Category management
├── Alerts            # Low stock & expiry warnings
├── Adjustments       # Stock adjustment history
├── Transaction History # Complete audit trail
└── Analytics         # Reports and insights
```

## Core Concepts

### Items (Item Master)

An **item** represents a stockable product in your inventory. Each item has:
- **SKU (Stock Keeping Unit):** Unique identifier
- **Item Name:** Descriptive name
- **Category:** Grouping (e.g., "Feed", "Chemicals", "Equipment")
- **Unit:** Measurement unit (kg, liters, pieces, etc.)
- **Default Supplier:** Primary supplier for this item
- **Reorder Threshold:** Alert level when stock is low
- **Min Stock Level:** Ideal minimum quantity
- **Current Quantity:** Real-time stock level (auto-calculated)

**Example:**
```
SKU: FEED-PELLET-3MM
Name: Premium Fish Feed Pellets 3mm
Category: Feed
Unit: kg
Reorder Threshold: 500 kg
Current Qty: 1,250 kg
```

### Batches (Inventory Batches)

A **batch** represents a specific purchase or receipt of an item. Batches enable FIFO tracking:
- **Batch Number:** Unique identifier for this batch
- **Quantity Purchased:** Original amount received
- **Remaining Qty:** Current quantity in this batch
- **Unit Cost:** Cost per unit for this batch
- **Purchase Date:** When received (used for FIFO ordering)
- **Expiry Date:** When batch expires (optional)
- **Supplier:** Who supplied this batch

**FIFO Logic:**
When stock is used, the system automatically deducts from the oldest batch first (earliest purchase date).

**Example:**
```
Item: FEED-PELLET-3MM

Batch 1: 500 kg @ ₹50/kg, purchased Jan 1, remaining: 200 kg
Batch 2: 750 kg @ ₹48/kg, purchased Feb 1, remaining: 750 kg

Use 300 kg:
  - Deduct 200 kg from Batch 1 (now 0 kg remaining)
  - Deduct 100 kg from Batch 2 (now 650 kg remaining)

Weighted cost: (200×50 + 100×48) / 300 = ₹49.33/kg
```

### Stock Operations

**Add Stock:**
- Record new inventory receipts
- Create batch with quantity, cost, dates
- Increases current quantity

**Use Stock (FIFO):**
- Deduct inventory for operations
- Automatically selects oldest batches
- Calculates weighted average cost
- Records purpose and module reference

**Stock Adjustments:**
- Manual corrections for physical count discrepancies
- Three types:
  - **Increase:** Add quantity (e.g., found missing stock)
  - **Decrease:** Remove quantity (e.g., damage, spoilage)
  - **Recount:** Set exact quantity (physical count result)

### Purchase Orders

A **purchase order (PO)** tracks orders placed with suppliers:
- **PO Number:** Unique identifier
- **Supplier:** Who you're ordering from
- **PO Date:** When order was placed
- **Expected Delivery:** When you expect to receive items
- **Status:** Pending, Approved, Ordered, Received, Closed, Cancelled
- **Line Items:** Multiple items can be in one PO
- **Total Cost:** Auto-calculated from line items

**PO Lifecycle:**
```
Pending → Approved → Ordered → Received → Closed
                                ↓
                            Cancelled
```

### Suppliers

A **supplier** is a vendor who provides inventory items:
- **Supplier Name:** Company name
- **Contact Person:** Primary contact
- **Phone & Email:** Contact information
- **Address:** Physical location
- **Status:** Active/inactive

### Categories

**Categories** organize inventory items into logical groups:
- Feed (all types of animal feed)
- Chemicals (water treatment, probiotics)
- Equipment (aerators, nets, tanks)
- Supplies (test kits, containers)

### Stock Reservations

**Reservations** are soft-locks on inventory for planned operations:
- Reserve quantity for specific module/operation
- Prevents over-commitment of stock
- Time-limited (expires after duration)
- Can be confirmed (converts to actual deduction) or cancelled

**Use Case:**
```
Morning planning:
- Reserve 50 kg feed for afternoon feeding session
- Stock shows: 1000 kg total, 50 kg reserved, 950 kg available
- Afternoon: Confirm reservation → actual FIFO deduction
- OR: Cancel reservation → stock freed for other use
```

### Module Integration

**Item-Module Mapping** links items to specific farm modules:
- Associate items with modules that use them
- Track consumption per module
- Generate module-specific reports
- Custom settings per module-item pair

**Example:**
```
Item: FEED-PELLET-3MM
Modules:
  - biofloc (primary)
  - hatchery
  - nursery

Module consumption report shows:
  Biofloc: 500 kg (last 30 days)
  Hatchery: 150 kg (last 30 days)
  Nursery: 200 kg (last 30 days)
```

## Documentation

- **[Technical Guide](./technical-guide.md)** - Architecture, database schema, API reference for developers
- **[User Guide](./user-guide.md)** - Features, workflows, and operational procedures

## Key Features by Component

### Dashboard
- Total items count (active only)
- Total stock value (cost-based calculation)
- Low stock items alert count
- Expiring soon items count (next 30 days)
- Pending purchase orders count
- Recent transaction activity count

### Items Management
- Create, view, update, deactivate items
- SKU and category management
- Reorder threshold configuration
- Default supplier assignment
- Search and filter by category/status

### Stock Operations
- **Add Stock:** Record receipts with batch tracking
- **Use Stock:** FIFO deduction with cost calculation
- **Batch Deduction:** Atomic multi-item operations
- Real-time availability checks

### Purchase Order Management
- Create POs with multiple line items
- Track PO status throughout lifecycle
- Filter by status and date range
- Auto-calculated totals
- Optimized performance (<200ms)

### Supplier Management
- Complete CRUD operations
- Contact information tracking
- Active/inactive status
- Search functionality

### Category Management
- Create and manage categories
- View item count per category
- Soft delete protection

### Alerts & Monitoring
- **Low Stock Alerts:** Items below reorder threshold
- **Expiry Alerts:** Batches expiring within X days (configurable)
- Color-coded urgency indicators
- Default supplier information included

### Transaction History
- Complete audit trail of all movements
- Filter by item, transaction type, date range
- Cost tracking for financial reporting
- User attribution for accountability

### Stock Adjustments
- Three adjustment types (increase, decrease, recount)
- Reason and notes documentation
- Adjustment history tracking
- Previous/new quantity comparison

### Current Stock View
- Real-time stock levels across all items
- Min level comparison
- Low stock indicators
- Search and category filtering

### Analytics & Reports
- Stock overview metrics
- Consumption patterns
- Supplier performance (future)
- Cost analysis (future)
- Forecasting (future)

## Technology Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL with asyncpg
- Pydantic for validation
- Database transaction management

**Frontend:**
- React with functional components
- Material-UI (MUI) components
- React Query for state management
- React Router for navigation
- Notistack for notifications

## Database Tables

Core tables:
- `item_master` - Item catalog
- `inventory_batches` - Stock batches with FIFO
- `inventory_transactions` - Complete audit trail
- `purchase_orders` - PO headers
- `purchase_order_items` - PO line items
- `suppliers` - Supplier information
- `inventory_categories` - Category definitions
- `inventory_reservations` - Stock reservations
- `item_module_mapping` - Module integration
- `stock_adjustments` - Adjustment tracking

## API Endpoints

Base URL: `/api/inventory`

**Core Resources:**
- `GET/POST /items` - Item management
- `POST /stock/add` - Add stock
- `POST /stock/use` - Use stock (FIFO)
- `POST /stock/use-batch` - Batch deduction
- `POST /stock/adjust` - Stock adjustments
- `GET /stock/adjustments` - Adjustment history
- `GET/POST /purchase-orders` - PO management
- `GET/POST /suppliers` - Supplier management
- `GET/POST /categories` - Category management
- `GET /alerts/low-stock` - Low stock alerts
- `GET /alerts/expiry` - Expiry alerts
- `GET /transactions` - Transaction history
- `GET /dashboard` - Dashboard metrics
- `POST /stock/reserve` - Create reservation
- `GET /stock/reservations` - List reservations
- `POST /items/bulk-fetch` - Bulk item fetch
- `GET /module/{module_name}/items` - Module items
- `GET /module/{module_name}/consumption` - Module consumption

See [Technical Guide](./technical-guide.md) for complete API reference.

## Integration with Other Modules

### Biofloc Module Integration

The inventory module provides seamless integration for biofloc feeding operations:

**InventoryIntegration Helper:**
```python
# In biofloc feeding code
from helpers.inventory_integration import InventoryIntegration

inv = InventoryIntegration(module_name="biofloc")

# Batch deduct for feeding session
result = await inv.batch_deduct(
    deductions=[
        {"sku": "FEED-PELLET-3MM", "quantity": 5.5},
        {"sku": "VITAMIN-MIX", "quantity": 0.2}
    ],
    module_reference="biofloc",
    tank_id=tank_uuid,
    batch_id=batch_uuid,
    session_number=1
)
```

**Benefits:**
- Automatic FIFO deduction
- Atomic operations (all succeed or all fail)
- Cost tracking per batch
- Consumption reporting
- Inventory availability checks

### Future Module Support

Framework ready for:
- Hatchery operations
- Growout operations
- Nursery operations
- General farm operations

## Version History

### v1.5.0 (2025-11-19)
- ✅ UUID field casting fixes for PostgreSQL
- ✅ Enhanced SKU/item_name search in batch deduction
- ✅ Transaction type filtering
- ✅ Case-insensitive category filtering
- ✅ ResponseValidationError fixes

### v1.4.0 (2025-11-18)
- ✅ Stock reservations system
- ✅ Bulk item fetch endpoint
- ✅ Module integration framework
- ✅ Item-module mapping

### v1.3.0 (2025-11-17)
- ✅ Batch operations (atomic multi-item deduction)
- ✅ Enhanced transaction logging
- ✅ Session-based grouping

### v1.2.0 (2025-11-16)
- ✅ Stock adjustments (increase, decrease, recount)
- ✅ Adjustment history tracking
- ✅ Enhanced validation

### v1.1.0 (2025-11-15)
- ✅ Purchase order management
- ✅ Supplier management
- ✅ Category management
- ✅ Frontend enhancements

### v1.0.0 (2025-11-14)
- ✅ Initial release
- ✅ Item master management
- ✅ FIFO stock operations
- ✅ Transaction history
- ✅ Basic alerts

## Performance Metrics

The system provides:

- **Purchase Order Queries:** <200ms response time
- **Batch Deduction:** Up to 50 items per atomic transaction
- **Bulk Fetch:** Efficient multi-item retrieval
- **FIFO Deduction:** Optimized batch selection algorithm
- **Transaction Logging:** Async background logging

## Best Practices

### Inventory Management
- Set appropriate reorder thresholds (2-4 weeks of average usage)
- Conduct physical stock counts monthly
- Use stock adjustments for count discrepancies
- Track expiry dates for perishable items
- Maintain accurate batch numbers

### Purchase Orders
- Create PO before ordering (not after receipt)
- Update status as PO progresses
- Link receipts to POs for traceability
- Review pending POs weekly

### Stock Operations
- Record stock usage immediately after operations
- Use descriptive notes for tracking
- Include module and tank references
- Verify stock availability before operations

### Supplier Management
- Keep supplier information up to date
- Track delivery reliability
- Maintain multiple suppliers for critical items
- Review supplier performance quarterly

## Support & Contributing

For issues, questions, or contributions:
- Check the documentation in `docs/inventory/`
- Review the code comments in source files
- Refer to the database schema in migration files

## License

Part of the Farm Management System
© 2025 All rights reserved
