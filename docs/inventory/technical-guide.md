# Inventory Module - Technical Guide

**Version:** 1.5.0
**Audience:** Developers, System Architects, Database Administrators

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Reference](#api-reference)
4. [Service Layer Logic](#service-layer-logic)
5. [Frontend Architecture](#frontend-architecture)
6. [FIFO Stock Management](#fifo-stock-management)
7. [Integration Architecture](#integration-architecture)
8. [Performance Considerations](#performance-considerations)
9. [Security & Permissions](#security--permissions)

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Material-UI Components               │
│  - React Query for State                │
│  - Form Validation                      │
│  - Real-time Updates                    │
└──────────────┬──────────────────────────┘
               │ REST API (HTTP/JSON)
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI)               │
│  - Route Handlers                       │
│  - Service Layer                        │
│  - FIFO Logic                           │
│  - Transaction Management               │
│  - Pydantic Validation                  │
└──────────────┬──────────────────────────┘
               │ asyncpg (async)
┌──────────────▼──────────────────────────┐
│       Database (PostgreSQL)             │
│  - Relational Data                      │
│  - Triggers & Computed Columns          │
│  - Indexes for FIFO                     │
│  - Transaction Support                  │
└─────────────────────────────────────────┘
```

### Module Structure

**Backend:**
```
backend/app/
├── routes/inventory.py          # API endpoints
├── schemas/inventory.py         # Pydantic models
├── services/inventory_service.py # Business logic
├── helpers/
│   └── inventory_integration.py # Cross-module helper
└── migrations/
    └── inventory_module_v1.0.0.sql
```

**Frontend:**
```
frontend/src/
├── pages/
│   ├── InventoryModule.jsx           # Main router
│   ├── InventoryDashboard.jsx        # Dashboard
│   ├── InventoryItems.jsx            # Items management
│   ├── StockOperations.jsx           # Add/use stock
│   ├── CurrentStock.jsx              # Stock levels
│   ├── PurchaseOrders.jsx            # PO management
│   ├── Suppliers.jsx                 # Suppliers
│   ├── Categories.jsx                # Categories
│   ├── Alerts.jsx                    # Low stock & expiry
│   ├── StockAdjustments.jsx          # Adjustments
│   ├── TransactionHistory.jsx        # Audit trail
│   └── InventoryAnalytics.jsx        # Reports
└── components/
    ├── AddStockDialog.jsx
    ├── UseStockDialog.jsx
    ├── CreatePODialog.jsx
    └── StockAdjustmentDialog.jsx
```

---

## Database Schema

### Entity Relationship Overview

```
suppliers ──< inventory_batches >── item_master ──< item_module_mapping >── modules
                  │                      │
                  │                      ├──< inventory_transactions
                  │                      ├──< inventory_reservations
                  │                      └──< stock_adjustments
                  │
                  └─< purchase_order_items >── purchase_orders

inventory_categories ──< item_master
```

### Core Tables

#### 1. `item_master`

Central catalog of all inventory items.

```sql
CREATE TABLE item_master (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100),
    unit VARCHAR(50) NOT NULL,
    default_supplier_id INTEGER REFERENCES suppliers(id),
    reorder_threshold NUMERIC(12,3),
    min_stock_level NUMERIC(12,3),
    current_qty NUMERIC(12,3) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `item_name` - Descriptive name (e.g., "Premium Fish Feed 3mm")
- `sku` - Stock Keeping Unit, unique identifier
- `category` - Category name (references inventory_categories loosely)
- `unit` - Measurement unit (kg, L, pieces, boxes, etc.)
- `default_supplier_id` - FK to suppliers (optional)
- `reorder_threshold` - Alert level for low stock
- `min_stock_level` - Recommended minimum quantity
- `current_qty` - **Computed field**, sum of all batch remaining_qty
- `is_active` - Soft delete flag
- `created_by` - User who created item
- `created_at`, `updated_at` - Timestamps

**Key Constraints:**
- Unique `sku` (case-sensitive)
- Check constraint: `current_qty >= 0`

**Key Indexes:**
```sql
CREATE INDEX idx_item_master_sku ON item_master(sku);
CREATE INDEX idx_item_master_category ON item_master(category);
CREATE INDEX idx_item_master_active ON item_master(is_active);
```

**Computed Field Maintenance:**

Option 1 - Trigger-based (recommended):
```sql
CREATE OR REPLACE FUNCTION update_item_current_qty()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE item_master
    SET current_qty = (
        SELECT COALESCE(SUM(remaining_qty), 0)
        FROM inventory_batches
        WHERE item_master_id = NEW.item_master_id
          AND is_active = TRUE
    )
    WHERE id = NEW.item_master_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_item_qty_on_batch_change
AFTER INSERT OR UPDATE OR DELETE ON inventory_batches
FOR EACH ROW
EXECUTE FUNCTION update_item_current_qty();
```

Option 2 - Application-managed (current implementation):
```python
# After every batch operation
await recalculate_current_qty(item_id)
```

---

#### 2. `inventory_batches`

Tracks individual stock batches with FIFO ordering.

```sql
CREATE TABLE inventory_batches (
    id SERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    batch_number VARCHAR(100),
    quantity_purchased NUMERIC(12,3) NOT NULL,
    remaining_qty NUMERIC(12,3) NOT NULL,
    unit_cost NUMERIC(10,2),
    purchase_date DATE NOT NULL,
    expiry_date DATE,
    supplier_id INTEGER REFERENCES suppliers(id),
    po_number VARCHAR(100),
    notes TEXT,
    added_by UUID REFERENCES user_profiles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `item_master_id` - FK to item_master
- `batch_number` - Batch identifier (optional)
- `quantity_purchased` - Original quantity received
- `remaining_qty` - Current quantity in batch (decreases with usage)
- `unit_cost` - Cost per unit for this batch
- `purchase_date` - **Critical for FIFO ordering**
- `expiry_date` - Expiration date (optional, for perishables)
- `supplier_id` - FK to suppliers
- `po_number` - Related purchase order number
- `notes` - Additional information
- `added_by` - User who added batch
- `is_active` - Soft delete flag
- `created_at`, `updated_at` - Timestamps

**FIFO Logic:**
Batches are selected for deduction in order of `purchase_date ASC`.

**Key Indexes:**
```sql
CREATE INDEX idx_inventory_batches_item ON inventory_batches(item_master_id);
CREATE INDEX idx_inventory_batches_purchase_date ON inventory_batches(item_master_id, purchase_date ASC);
CREATE INDEX idx_inventory_batches_expiry ON inventory_batches(expiry_date) WHERE expiry_date IS NOT NULL;
CREATE INDEX idx_inventory_batches_active ON inventory_batches(is_active);
```

**Check Constraints:**
```sql
ALTER TABLE inventory_batches
ADD CONSTRAINT chk_remaining_qty_positive CHECK (remaining_qty >= 0),
ADD CONSTRAINT chk_remaining_lte_purchased CHECK (remaining_qty <= quantity_purchased);
```

---

#### 3. `inventory_transactions`

Complete audit trail of all inventory movements.

```sql
CREATE TABLE inventory_transactions (
    id BIGSERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    batch_id INTEGER REFERENCES inventory_batches(id),
    transaction_type VARCHAR(50) NOT NULL,
    quantity_change NUMERIC(12,3) NOT NULL,
    new_balance NUMERIC(12,3),
    unit_cost NUMERIC(10,2),
    total_cost NUMERIC(12,2),
    po_number VARCHAR(100),
    module_reference VARCHAR(100),
    tank_id INTEGER,
    user_id UUID REFERENCES user_profiles(id),
    username VARCHAR(255),
    notes TEXT,
    module_batch_id UUID,
    session_number INTEGER,
    transaction_date TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing identifier
- `item_master_id` - FK to item (what item was affected)
- `batch_id` - FK to batch (which batch was affected, NULL for adjustments)
- `transaction_type` - Type: 'add', 'use', 'adjustment'
- `quantity_change` - Amount changed (positive for add, negative for use)
- `new_balance` - Item total quantity after transaction
- `unit_cost` - Cost per unit (for FIFO weighted average)
- `total_cost` - Total cost of transaction
- `po_number` - Related purchase order (if applicable)
- `module_reference` - Which module used the stock (e.g., 'biofloc')
- `tank_id` - Tank reference (if applicable)
- `user_id` - User who performed transaction
- `username` - Denormalized username for easier querying
- `notes` - Purpose/reason for transaction
- `module_batch_id` - Biofloc/other module batch UUID reference
- `session_number` - Session grouping (e.g., feeding session 1, 2, 3)
- `transaction_date` - When transaction occurred

**Transaction Types:**
- `add` - Stock addition (purchase, receipt)
- `use` - Stock deduction (FIFO)
- `adjustment` - Manual correction (increase, decrease, recount)

**Key Indexes:**
```sql
CREATE INDEX idx_inventory_transactions_item ON inventory_transactions(item_master_id);
CREATE INDEX idx_inventory_transactions_type ON inventory_transactions(transaction_type);
CREATE INDEX idx_inventory_transactions_date ON inventory_transactions(transaction_date DESC);
CREATE INDEX idx_inventory_transactions_module_batch ON inventory_transactions(module_batch_id);
CREATE INDEX idx_inventory_transactions_session ON inventory_transactions(session_number);
```

**Query Optimization:**
```sql
-- Compound index for common query pattern
CREATE INDEX idx_transactions_item_date ON inventory_transactions(item_master_id, transaction_date DESC);
```

---

#### 4. `purchase_orders`

Purchase order header information.

```sql
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id) NOT NULL,
    po_date DATE NOT NULL,
    expected_delivery DATE,
    status VARCHAR(50) DEFAULT 'pending',
    total_cost NUMERIC(12,2),
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `po_number` - Unique PO identifier
- `supplier_id` - FK to suppliers (who are we ordering from)
- `po_date` - Date PO was created
- `expected_delivery` - Expected receipt date
- `status` - PO status enum
- `total_cost` - **Computed field**, sum of line items
- `notes` - Additional information
- `created_by` - User who created PO
- `created_at`, `updated_at` - Timestamps

**Status Enum:**
```sql
CREATE TYPE po_status AS ENUM (
    'pending',      -- Created but not approved
    'approved',     -- Approved, ready to order
    'ordered',      -- Order placed with supplier
    'received',     -- Goods received
    'closed',       -- PO completed and closed
    'cancelled'     -- PO cancelled
);

ALTER TABLE purchase_orders
ALTER COLUMN status TYPE po_status USING status::po_status;
```

**Total Cost Trigger:**
```sql
CREATE OR REPLACE FUNCTION update_po_total_cost()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE purchase_orders
    SET total_cost = (
        SELECT COALESCE(SUM(line_total), 0)
        FROM purchase_order_items
        WHERE purchase_order_id = NEW.purchase_order_id
    )
    WHERE id = NEW.purchase_order_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_po_total
AFTER INSERT OR UPDATE OR DELETE ON purchase_order_items
FOR EACH ROW
EXECUTE FUNCTION update_po_total_cost();
```

**Key Indexes:**
```sql
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_orders_date ON purchase_orders(po_date DESC);
```

---

#### 5. `purchase_order_items`

Line items for purchase orders (multi-item support).

```sql
CREATE TABLE purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    ordered_qty NUMERIC(12,3) NOT NULL,
    unit_cost NUMERIC(10,2),
    line_total NUMERIC(12,2) GENERATED ALWAYS AS (ordered_qty * unit_cost) STORED
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `purchase_order_id` - FK to purchase_orders
- `item_master_id` - FK to item_master (what item)
- `ordered_qty` - Quantity ordered
- `unit_cost` - Cost per unit
- `line_total` - **Computed column**: `ordered_qty * unit_cost`

**Key Indexes:**
```sql
CREATE INDEX idx_po_items_po ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_po_items_item ON purchase_order_items(item_master_id);
```

---

#### 6. `suppliers`

Supplier/vendor information.

```sql
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `supplier_name` - Company name
- `contact_person` - Primary contact name
- `phone` - Phone number
- `email` - Email address
- `address` - Physical address
- `is_active` - Soft delete flag
- `created_at`, `updated_at` - Timestamps

**Key Indexes:**
```sql
CREATE INDEX idx_suppliers_active ON suppliers(is_active);
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);
```

---

#### 7. `inventory_categories`

Category definitions for organizing items.

```sql
CREATE TABLE inventory_categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `category_name` - Unique category name
- `description` - Category description
- `created_at` - Timestamp

**Common Categories:**
- Feed
- Chemicals
- Equipment
- Supplies
- Probiotics
- Supplements

---

#### 8. `inventory_reservations`

Stock reservation system for planned operations.

```sql
CREATE TABLE inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id INTEGER NOT NULL REFERENCES item_master(id),
    quantity DECIMAL(12,3) NOT NULL,
    module_reference VARCHAR(50),
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'pending',
    reserved_until TIMESTAMP WITH TIME ZONE NOT NULL,
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - UUID primary key
- `item_id` - FK to item_master
- `quantity` - Amount reserved
- `module_reference` - Module that created reservation
- `reference_id` - Module-specific reference (tank, batch, etc.)
- `status` - Status: 'pending', 'confirmed', 'cancelled', 'expired'
- `reserved_until` - Expiration timestamp
- `notes` - Purpose/reason
- `created_by` - User who created reservation
- `created_at`, `updated_at` - Timestamps

**Status Enum:**
```sql
CREATE TYPE reservation_status AS ENUM (
    'pending',      -- Active reservation
    'confirmed',    -- Converted to actual stock usage
    'cancelled',    -- Manually cancelled
    'expired'       -- Expired due to time
);
```

**Key Indexes:**
```sql
CREATE INDEX idx_reservations_item ON inventory_reservations(item_id);
CREATE INDEX idx_reservations_status ON inventory_reservations(status);
CREATE INDEX idx_reservations_expiry ON inventory_reservations(reserved_until);
CREATE INDEX idx_reservations_module ON inventory_reservations(module_reference);
```

**Auto-Expiry Function:**
```sql
CREATE OR REPLACE FUNCTION expire_old_reservations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE inventory_reservations
    SET status = 'expired'
    WHERE status = 'pending'
      AND reserved_until < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule via pg_cron or external job
-- SELECT expire_old_reservations();
```

---

#### 9. `item_module_mapping`

Maps items to modules for cross-module integration.

```sql
CREATE TABLE item_module_mapping (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    module_name VARCHAR(50) NOT NULL,
    custom_settings JSONB,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(item_id, module_name)
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `item_id` - FK to item_master
- `module_name` - Module identifier ('biofloc', 'hatchery', etc.)
- `custom_settings` - Module-specific configuration in JSON
- `is_primary` - Indicates primary module for this item
- `created_at`, `updated_at` - Timestamps

**Module Types:**
```sql
CREATE TYPE module_type AS ENUM (
    'biofloc',
    'hatchery',
    'growout',
    'nursery',
    'general'
);
```

**Custom Settings Example:**
```json
{
  "feed_type": "pellet",
  "protein_percentage": 40,
  "recommended_rate": "3% body weight per day",
  "life_stage": "grow-out"
}
```

**Key Indexes:**
```sql
CREATE INDEX idx_item_module_mapping_item ON item_module_mapping(item_id);
CREATE INDEX idx_item_module_mapping_module ON item_module_mapping(module_name);
```

---

#### 10. `stock_adjustments`

Track manual stock corrections.

```sql
CREATE TABLE stock_adjustments (
    id SERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id),
    adjustment_type VARCHAR(50) NOT NULL,
    quantity_change NUMERIC(12,3) NOT NULL,
    previous_qty NUMERIC(12,3) NOT NULL,
    new_qty NUMERIC(12,3) NOT NULL,
    reason VARCHAR(255),
    notes TEXT,
    adjusted_by UUID REFERENCES user_profiles(id),
    adjustment_date TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing primary key
- `item_master_id` - FK to item_master
- `adjustment_type` - Type: 'increase', 'decrease', 'recount'
- `quantity_change` - Amount changed (can be negative)
- `previous_qty` - Quantity before adjustment
- `new_qty` - Quantity after adjustment
- `reason` - Required reason for adjustment
- `notes` - Additional details
- `adjusted_by` - User who made adjustment
- `adjustment_date` - When adjustment was made

**Adjustment Types:**
- `increase` - Add quantity (e.g., found missing stock)
- `decrease` - Remove quantity (e.g., spoilage, damage)
- `recount` - Set exact quantity (physical count result)

**Key Indexes:**
```sql
CREATE INDEX idx_stock_adjustments_item ON stock_adjustments(item_master_id);
CREATE INDEX idx_stock_adjustments_date ON stock_adjustments(adjustment_date DESC);
CREATE INDEX idx_stock_adjustments_type ON stock_adjustments(adjustment_type);
```

---

## API Reference

### Base URL
```
/api/inventory
```

### Authentication
All endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User must have `inventory` module access
- Enforced by `require_module_access("inventory")` dependency

---

### Item Management Endpoints

#### `GET /items`
Get list of items with optional filters.

**Query Parameters:**
- `category` (optional): string - Filter by category
- `is_active` (optional): boolean - Filter by active status
- `page` (default: 1): integer - Page number
- `limit` (default: 50, max: 100): integer - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "category": "Feed",
      "unit": "kg",
      "default_supplier_id": 5,
      "default_supplier_name": "Feed Supplier Inc",
      "reorder_threshold": 500.0,
      "min_stock_level": 1000.0,
      "current_qty": 1250.5,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 50
}
```

---

#### `POST /items`
Create new inventory item.

**Request Body:**
```json
{
  "item_name": "Premium Fish Feed 5mm",
  "sku": "FEED-PELLET-5MM",
  "category": "Feed",
  "unit": "kg",
  "default_supplier_id": 5,
  "reorder_threshold": 500.0,
  "min_stock_level": 1000.0
}
```

**Response:** `201 Created` with item object

**Validations:**
- SKU must be unique
- Item name required
- Unit required

---

#### `PUT /items/{item_id}`
Update existing item.

**Path Parameters:**
- `item_id`: integer - Item to update

**Request Body:** (all fields optional)
```json
{
  "item_name": "Updated Name",
  "reorder_threshold": 600.0,
  "is_active": false
}
```

**Response:** Updated item object

---

#### `DELETE /items/{item_id}`
Deactivate item (soft delete).

**Path Parameters:**
- `item_id`: integer - Item to deactivate

**Response:**
```json
{
  "message": "Item deactivated successfully"
}
```

---

### Stock Operation Endpoints

#### `POST /stock/add`
Add new stock batch.

**Request Body:**
```json
{
  "item_master_id": 1,
  "quantity": 500.0,
  "unit_cost": 50.00,
  "purchase_date": "2025-11-19",
  "supplier_id": 5,
  "batch_number": "BATCH-2025-11-19-001",
  "expiry_date": "2026-11-19",
  "po_number": "PO-001",
  "notes": "Premium quality batch"
}
```

**Response:**
```json
{
  "batch_id": 123,
  "item_id": 1,
  "quantity_added": 500.0,
  "new_current_qty": 1750.5,
  "transaction_id": 9876
}
```

**Backend Logic:**
1. Validate item exists and is active
2. Validate supplier exists (if provided)
3. Create inventory_batch record
4. Create inventory_transaction (type: 'add')
5. Update item_master.current_qty
6. Return confirmation

---

#### `POST /stock/use`
Use stock with FIFO deduction.

**Request Body:**
```json
{
  "item_master_id": 1,
  "quantity": 50.5,
  "purpose": "Tank 1 feeding - morning session",
  "module_reference": "biofloc",
  "tank_id": 1,
  "notes": "Feeding session 1"
}
```

**Response:**
```json
{
  "item_id": 1,
  "quantity_deducted": 50.5,
  "new_current_qty": 1200.0,
  "weighted_avg_cost": 49.25,
  "batches_used": [
    {
      "batch_id": 101,
      "quantity_from_batch": 30.5,
      "unit_cost": 50.00,
      "remaining_in_batch": 0
    },
    {
      "batch_id": 102,
      "quantity_from_batch": 20.0,
      "unit_cost": 48.00,
      "remaining_in_batch": 430.0
    }
  ],
  "transaction_id": 9877
}
```

**Backend Logic (FIFO):**
```python
async def use_stock_fifo(item_id, quantity, purpose, ...):
    # 1. Fetch oldest batches
    batches = await db.fetch_all(
        """
        SELECT * FROM inventory_batches
        WHERE item_master_id = $1
          AND is_active = TRUE
          AND remaining_qty > 0
        ORDER BY purchase_date ASC, id ASC
        """,
        item_id
    )

    # 2. Check total availability
    total_available = sum(b['remaining_qty'] for b in batches)
    if total_available < quantity:
        raise InsufficientStock(f"Only {total_available} available")

    # 3. Deduct from batches (FIFO)
    remaining_to_deduct = quantity
    batches_used = []
    total_cost = 0

    for batch in batches:
        if remaining_to_deduct == 0:
            break

        deduct_from_batch = min(batch['remaining_qty'], remaining_to_deduct)

        # Update batch
        await db.execute(
            "UPDATE inventory_batches SET remaining_qty = remaining_qty - $1 WHERE id = $2",
            deduct_from_batch, batch['id']
        )

        # Track for response
        batches_used.append({
            "batch_id": batch['id'],
            "quantity_from_batch": deduct_from_batch,
            "unit_cost": batch['unit_cost']
        })

        total_cost += deduct_from_batch * batch['unit_cost']
        remaining_to_deduct -= deduct_from_batch

    # 4. Calculate weighted average cost
    weighted_avg_cost = total_cost / quantity

    # 5. Create transaction record
    await log_transaction(
        item_id=item_id,
        transaction_type='use',
        quantity_change=-quantity,
        unit_cost=weighted_avg_cost,
        total_cost=total_cost,
        purpose=purpose,
        ...
    )

    # 6. Update item current_qty
    await recalculate_current_qty(item_id)

    return {
        "quantity_deducted": quantity,
        "weighted_avg_cost": weighted_avg_cost,
        "batches_used": batches_used
    }
```

---

#### `POST /stock/use-batch`
Atomic batch deduction for multiple items.

**Request Body:**
```json
{
  "deductions": [
    {
      "sku": "FEED-PELLET-3MM",
      "quantity": 5.5,
      "notes": "Tank 1 feed"
    },
    {
      "sku": "VITAMIN-MIX",
      "quantity": 0.2,
      "notes": "Supplement"
    },
    {
      "item_id": 3,
      "quantity": 0.1,
      "notes": "Probiotic"
    }
  ],
  "module_reference": "biofloc",
  "tank_id": "tank-uuid",
  "batch_id": "batch-uuid",
  "session_number": 1,
  "global_notes": "Morning feeding session"
}
```

**Response:**
```json
{
  "success": true,
  "items_processed": 3,
  "total_cost": 277.50,
  "deductions": [
    {
      "item_id": 1,
      "sku": "FEED-PELLET-3MM",
      "quantity": 5.5,
      "cost": 275.00,
      "batches_used": [...]
    },
    {
      "item_id": 2,
      "sku": "VITAMIN-MIX",
      "quantity": 0.2,
      "cost": 2.00,
      "batches_used": [...]
    },
    {
      "item_id": 3,
      "quantity": 0.1,
      "cost": 0.50,
      "batches_used": [...]
    }
  ]
}
```

**Backend Logic (Atomic Transaction):**
```python
async def batch_deduct_stock(request):
    async with db.transaction():  # Atomic!
        results = []

        for deduction in request.deductions:
            # Resolve item (by SKU or item_id)
            item = await resolve_item(deduction)

            # FIFO deduct
            result = await use_stock_fifo(
                item_id=item['id'],
                quantity=deduction['quantity'],
                purpose=deduction.get('notes', ''),
                module_reference=request.module_reference,
                tank_id=request.tank_id,
                module_batch_id=request.batch_id,
                session_number=request.session_number
            )

            results.append(result)

        # If ANY item fails, entire transaction rolls back
        return {
            "success": True,
            "items_processed": len(results),
            "deductions": results
        }
```

**Key Features:**
- All-or-nothing (if any item fails, none deducted)
- Up to 50 items per batch operation
- FIFO logic applied per item
- Session grouping for related operations

---

#### `POST /stock/adjust`
Create stock adjustment (manual correction).

**Request Body:**
```json
{
  "item_master_id": 1,
  "adjustment_type": "recount",
  "quantity": 1180.5,
  "reason": "Physical inventory count",
  "notes": "Annual stock take - Nov 2025"
}
```

**Adjustment Types:**
- `increase`: Add quantity (e.g., found missing stock)
  - `quantity` is amount to add
- `decrease`: Remove quantity (e.g., damage, spoilage)
  - `quantity` is amount to remove
- `recount`: Set exact quantity (physical count)
  - `quantity` is the actual counted amount

**Response:**
```json
{
  "adjustment_id": 55,
  "item_id": 1,
  "adjustment_type": "recount",
  "previous_qty": 1250.5,
  "quantity_change": -70.0,
  "new_qty": 1180.5,
  "reason": "Physical inventory count"
}
```

**Backend Logic:**
```python
async def create_stock_adjustment(request):
    item = await fetch_item(request.item_id)
    previous_qty = item['current_qty']

    if request.adjustment_type == 'increase':
        quantity_change = request.quantity
        new_qty = previous_qty + quantity_change
    elif request.adjustment_type == 'decrease':
        quantity_change = -request.quantity
        new_qty = previous_qty - request.quantity
    elif request.adjustment_type == 'recount':
        new_qty = request.quantity
        quantity_change = new_qty - previous_qty

    # Create adjustment record
    adjustment = await db.fetch_one(
        """
        INSERT INTO stock_adjustments
        (item_master_id, adjustment_type, quantity_change,
         previous_qty, new_qty, reason, notes, adjusted_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        request.item_id, request.adjustment_type, quantity_change,
        previous_qty, new_qty, request.reason, request.notes, user_id
    )

    # Update item current_qty
    await db.execute(
        "UPDATE item_master SET current_qty = $1 WHERE id = $2",
        new_qty, request.item_id
    )

    # Log transaction
    await log_transaction(
        item_id=request.item_id,
        transaction_type='adjustment',
        quantity_change=quantity_change,
        notes=f"Adjustment: {request.reason}"
    )

    return adjustment
```

---

#### `GET /stock/adjustments`
Get stock adjustment history.

**Query Parameters:**
- `item_id` (optional): integer - Filter by item
- `adjustment_type` (optional): string - Filter by type
- `days_back` (default: 30, max: 365): integer - Lookback period
- `page`, `limit`: Pagination

**Response:**
```json
{
  "adjustments": [
    {
      "id": 55,
      "item_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "adjustment_type": "recount",
      "quantity_change": -70.0,
      "previous_qty": 1250.5,
      "new_qty": 1180.5,
      "reason": "Physical inventory count",
      "notes": "Annual stock take - Nov 2025",
      "adjusted_by": "admin@example.com",
      "adjustment_date": "2025-11-19T14:30:00"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 50
}
```

---

### Purchase Order Endpoints

#### `GET /purchase-orders`
Get list of purchase orders (optimized, <200ms).

**Query Parameters:**
- `status` (optional): string - Filter by PO status
- `days_back` (default: 30, max: 365): integer - Lookback period
- `page` (default: 1): integer
- `page_size` (default: 20, max: 100): integer

**Response:**
```json
{
  "purchase_orders": [
    {
      "id": 10,
      "po_number": "PO-2025-001",
      "supplier_id": 5,
      "supplier_name": "Feed Supplier Inc",
      "po_date": "2025-11-15",
      "expected_delivery": "2025-11-25",
      "status": "ordered",
      "total_cost": 25000.00,
      "items_count": 3,
      "created_by": "admin@example.com",
      "created_at": "2025-11-15T10:00:00"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

**Optimized Query:**
```sql
SELECT
    po.id,
    po.po_number,
    po.supplier_id,
    s.supplier_name,
    po.po_date,
    po.expected_delivery,
    po.status,
    po.total_cost,
    COUNT(poi.id) as items_count,
    po.created_at
FROM purchase_orders po
LEFT JOIN suppliers s ON po.supplier_id = s.id
LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
WHERE po.po_date >= NOW() - INTERVAL '30 days'
  AND ($1::varchar IS NULL OR po.status = $1)
GROUP BY po.id, s.supplier_name
ORDER BY po.po_date DESC
LIMIT 20 OFFSET 0;
```

---

#### `POST /purchase-orders`
Create new purchase order with items.

**Request Body:**
```json
{
  "po_number": "PO-2025-002",
  "supplier_id": 5,
  "po_date": "2025-11-19",
  "expected_delivery": "2025-11-29",
  "items": [
    {
      "item_master_id": 1,
      "ordered_qty": 500.0,
      "unit_cost": 48.00
    },
    {
      "item_master_id": 2,
      "ordered_qty": 100.0,
      "unit_cost": 10.00
    }
  ],
  "notes": "Monthly feed order"
}
```

**Response:**
```json
{
  "id": 11,
  "po_number": "PO-2025-002",
  "supplier_id": 5,
  "status": "pending",
  "total_cost": 25000.00,
  "items": [
    {
      "id": 21,
      "item_master_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "ordered_qty": 500.0,
      "unit_cost": 48.00,
      "line_total": 24000.00
    },
    {
      "id": 22,
      "item_master_id": 2,
      "item_name": "Vitamin Mix",
      "ordered_qty": 100.0,
      "unit_cost": 10.00,
      "line_total": 1000.00
    }
  ],
  "created_at": "2025-11-19T10:00:00"
}
```

**Backend Logic:**
```python
async def create_purchase_order(request):
    async with db.transaction():
        # 1. Create PO header
        po = await db.fetch_one(
            """
            INSERT INTO purchase_orders
            (po_number, supplier_id, po_date, expected_delivery, notes, created_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            request.po_number, request.supplier_id, request.po_date,
            request.expected_delivery, request.notes, user_id
        )

        # 2. Create line items
        items = []
        for item in request.items:
            line_item = await db.fetch_one(
                """
                INSERT INTO purchase_order_items
                (purchase_order_id, item_master_id, ordered_qty, unit_cost)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                po['id'], item['item_master_id'], item['ordered_qty'], item['unit_cost']
            )
            items.append(line_item)

        # 3. Trigger auto-updates total_cost
        # 4. Return PO with items
        return {**po, "items": items}
```

---

#### `PUT /purchase-orders/{po_id}`
Update purchase order (typically status updates).

**Path Parameters:**
- `po_id`: integer - PO to update

**Request Body:**
```json
{
  "status": "received",
  "notes": "All items received in good condition"
}
```

**Response:** Updated PO object

---

### Supplier & Category Endpoints

#### `GET /suppliers`
Get list of suppliers.

**Response:**
```json
{
  "suppliers": [
    {
      "id": 5,
      "supplier_name": "Feed Supplier Inc",
      "contact_person": "John Supplier",
      "phone": "+1-555-0100",
      "email": "john@feedsupplier.com",
      "address": "123 Feed Lane, City, State 12345",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

---

#### `POST /suppliers`
Create new supplier.

**Request Body:**
```json
{
  "supplier_name": "New Supplier Co",
  "contact_person": "Jane Contact",
  "phone": "+1-555-0200",
  "email": "jane@newsupplier.com",
  "address": "456 Supply St, City, State 67890"
}
```

**Response:** `201 Created` with supplier object

---

#### `GET /categories`
Get list of categories with item counts.

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "category_name": "Feed",
      "description": "All types of animal feed",
      "item_count": 12,
      "created_at": "2025-01-01T00:00:00"
    },
    {
      "id": 2,
      "category_name": "Chemicals",
      "description": "Water treatment chemicals",
      "item_count": 8,
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

**Query with Counts:**
```sql
SELECT
    c.id,
    c.category_name,
    c.description,
    COUNT(im.id) as item_count,
    c.created_at
FROM inventory_categories c
LEFT JOIN item_master im ON c.category_name = im.category AND im.is_active = TRUE
GROUP BY c.id, c.category_name, c.description, c.created_at
ORDER BY c.category_name;
```

---

#### `POST /categories`
Create new category.

**Request Body:**
```json
{
  "category_name": "Equipment",
  "description": "Farm equipment and tools"
}
```

**Response:** `201 Created` with category object

---

### Alert Endpoints

#### `GET /alerts/low-stock`
Get items below reorder threshold.

**Response:**
```json
{
  "low_stock_items": [
    {
      "id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "current_qty": 450.0,
      "reorder_threshold": 500.0,
      "min_stock_level": 1000.0,
      "default_supplier_id": 5,
      "default_supplier_name": "Feed Supplier Inc",
      "shortage": -50.0
    }
  ],
  "count": 5
}
```

**Query:**
```sql
SELECT
    im.id,
    im.item_name,
    im.sku,
    im.current_qty,
    im.reorder_threshold,
    im.min_stock_level,
    im.default_supplier_id,
    s.supplier_name as default_supplier_name,
    (im.current_qty - im.reorder_threshold) as shortage
FROM item_master im
LEFT JOIN suppliers s ON im.default_supplier_id = s.id
WHERE im.is_active = TRUE
  AND im.current_qty < im.reorder_threshold
ORDER BY shortage ASC;
```

---

#### `GET /alerts/expiry`
Get batches expiring within X days.

**Query Parameters:**
- `days` (default: 30): integer - Days until expiry

**Response:**
```json
{
  "expiring_batches": [
    {
      "batch_id": 123,
      "item_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "batch_number": "BATCH-2024-11-20-001",
      "remaining_qty": 150.0,
      "expiry_date": "2025-11-25",
      "days_until_expiry": 6,
      "supplier_id": 5,
      "supplier_name": "Feed Supplier Inc",
      "urgency": "high"
    }
  ],
  "count": 3
}
```

**Urgency Calculation:**
- `< 7 days`: "high" (red)
- `7-14 days`: "medium" (orange)
- `> 14 days`: "low" (yellow)

**Query:**
```sql
SELECT
    ib.id as batch_id,
    ib.item_master_id as item_id,
    im.item_name,
    im.sku,
    ib.batch_number,
    ib.remaining_qty,
    ib.expiry_date,
    (ib.expiry_date - CURRENT_DATE) as days_until_expiry,
    ib.supplier_id,
    s.supplier_name
FROM inventory_batches ib
JOIN item_master im ON ib.item_master_id = im.id
LEFT JOIN suppliers s ON ib.supplier_id = s.id
WHERE ib.is_active = TRUE
  AND ib.remaining_qty > 0
  AND ib.expiry_date IS NOT NULL
  AND ib.expiry_date <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY ib.expiry_date ASC;
```

---

### Transaction History Endpoint

#### `GET /transactions`
Get complete transaction history.

**Query Parameters:**
- `item_id` (optional): integer - Filter by item
- `transaction_type` (optional): string - Filter: 'add', 'use', 'adjustment'
- `days_back` (default: 30, max: 365): integer - Lookback period
- `page`, `limit`: Pagination

**Response:**
```json
{
  "transactions": [
    {
      "id": 9877,
      "item_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "transaction_type": "use",
      "quantity_change": -50.5,
      "new_balance": 1200.0,
      "unit_cost": 49.25,
      "total_cost": 2487.13,
      "module_reference": "biofloc",
      "tank_id": 1,
      "username": "farm.operator@example.com",
      "notes": "Tank 1 feeding - morning session",
      "session_number": 1,
      "transaction_date": "2025-11-19T08:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50
}
```

---

### Dashboard Endpoint

#### `GET /dashboard`
Get inventory dashboard metrics.

**Response:**
```json
{
  "total_items": 45,
  "active_items": 42,
  "total_stock_value": 125000.50,
  "low_stock_items_count": 5,
  "expiring_soon_count": 3,
  "pending_po_count": 2,
  "recent_transactions_count_7d": 234
}
```

**Queries:**
```python
async def get_dashboard_metrics():
    # Total items
    total_items = await db.fetch_val(
        "SELECT COUNT(*) FROM item_master"
    )

    # Active items
    active_items = await db.fetch_val(
        "SELECT COUNT(*) FROM item_master WHERE is_active = TRUE"
    )

    # Total stock value (sum of all batches: remaining_qty * unit_cost)
    total_stock_value = await db.fetch_val(
        """
        SELECT COALESCE(SUM(remaining_qty * unit_cost), 0)
        FROM inventory_batches
        WHERE is_active = TRUE
        """
    )

    # Low stock items
    low_stock_count = await db.fetch_val(
        """
        SELECT COUNT(*)
        FROM item_master
        WHERE is_active = TRUE
          AND current_qty < reorder_threshold
        """
    )

    # Expiring soon (30 days)
    expiring_soon = await db.fetch_val(
        """
        SELECT COUNT(DISTINCT item_master_id)
        FROM inventory_batches
        WHERE is_active = TRUE
          AND remaining_qty > 0
          AND expiry_date IS NOT NULL
          AND expiry_date <= CURRENT_DATE + INTERVAL '30 days'
        """
    )

    # Pending POs
    pending_po = await db.fetch_val(
        """
        SELECT COUNT(*)
        FROM purchase_orders
        WHERE status IN ('pending', 'approved', 'ordered')
        """
    )

    # Recent transactions (7 days)
    recent_transactions = await db.fetch_val(
        """
        SELECT COUNT(*)
        FROM inventory_transactions
        WHERE transaction_date >= NOW() - INTERVAL '7 days'
        """
    )

    return {
        "total_items": total_items,
        "active_items": active_items,
        "total_stock_value": total_stock_value,
        "low_stock_items_count": low_stock_count,
        "expiring_soon_count": expiring_soon,
        "pending_po_count": pending_po,
        "recent_transactions_count_7d": recent_transactions
    }
```

---

### Stock Reservation Endpoints

#### `POST /stock/reserve`
Create stock reservation.

**Request Body:**
```json
{
  "item_id": 1,
  "quantity": 50.0,
  "module_reference": "biofloc",
  "reference_id": "batch-uuid",
  "duration_hours": 24,
  "notes": "Reserved for afternoon feeding session"
}
```

**Response:**
```json
{
  "id": "reservation-uuid",
  "item_id": 1,
  "quantity": 50.0,
  "status": "pending",
  "reserved_until": "2025-11-20T14:00:00Z",
  "created_at": "2025-11-19T14:00:00Z"
}
```

---

#### `GET /stock/reservations`
List reservations.

**Query Parameters:**
- `item_id` (optional): Filter by item
- `module_reference` (optional): Filter by module
- `status` (optional): Filter by status

**Response:**
```json
{
  "reservations": [
    {
      "id": "reservation-uuid",
      "item_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "quantity": 50.0,
      "module_reference": "biofloc",
      "reference_id": "batch-uuid",
      "status": "pending",
      "reserved_until": "2025-11-20T14:00:00Z",
      "created_at": "2025-11-19T14:00:00Z"
    }
  ]
}
```

---

#### `POST /stock/confirm-reservation/{reservation_id}`
Confirm reservation and convert to actual stock deduction.

**Path Parameters:**
- `reservation_id`: UUID - Reservation to confirm

**Response:**
```json
{
  "reservation_id": "reservation-uuid",
  "status": "confirmed",
  "deduction": {
    "item_id": 1,
    "quantity_deducted": 50.0,
    "batches_used": [...]
  }
}
```

**Backend Logic:**
```python
async def confirm_reservation(reservation_id):
    async with db.transaction():
        # 1. Fetch reservation
        reservation = await db.fetch_one(
            "SELECT * FROM inventory_reservations WHERE id = $1 AND status = 'pending'",
            reservation_id
        )

        # 2. Perform FIFO deduction
        deduction = await use_stock_fifo(
            item_id=reservation['item_id'],
            quantity=reservation['quantity'],
            purpose=f"Confirmed reservation {reservation_id}",
            module_reference=reservation['module_reference']
        )

        # 3. Update reservation status
        await db.execute(
            "UPDATE inventory_reservations SET status = 'confirmed', updated_at = NOW() WHERE id = $1",
            reservation_id
        )

        return {
            "reservation_id": reservation_id,
            "status": "confirmed",
            "deduction": deduction
        }
```

---

#### `DELETE /stock/reserve/{reservation_id}`
Cancel pending reservation.

**Path Parameters:**
- `reservation_id`: UUID - Reservation to cancel

**Response:**
```json
{
  "message": "Reservation cancelled successfully"
}
```

---

### Bulk Operations Endpoint

#### `POST /items/bulk-fetch`
Fetch multiple items by IDs or SKUs.

**Request Body:**
```json
{
  "item_ids": [1, 2, 3],
  "skus": ["FEED-PELLET-3MM", "VITAMIN-MIX"],
  "include_stock": true,
  "include_batches": false,
  "include_reserved": true
}
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "current_qty": 1200.0,
      "reserved_qty": 50.0,
      "available_qty": 1150.0,
      "batches": []
    },
    {
      "id": 2,
      "item_name": "Vitamin Mix",
      "sku": "VITAMIN-MIX",
      "current_qty": 50.0,
      "reserved_qty": 0,
      "available_qty": 50.0,
      "batches": []
    }
  ]
}
```

**Use Case:**
Morning stock check before operations - quickly fetch availability for all items needed.

---

### Module Integration Endpoints

#### `GET /module/{module_name}/items`
Get items mapped to a specific module.

**Path Parameters:**
- `module_name`: string - Module identifier (e.g., 'biofloc')

**Response:**
```json
{
  "module_name": "biofloc",
  "items": [
    {
      "id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "is_primary": true,
      "custom_settings": {
        "feed_type": "pellet",
        "protein_percentage": 40
      }
    }
  ]
}
```

---

#### `GET /module/{module_name}/consumption`
Get consumption report for a module.

**Path Parameters:**
- `module_name`: string - Module identifier

**Query Parameters:**
- `days_back` (default: 30): integer - Lookback period

**Response:**
```json
{
  "module_name": "biofloc",
  "period_days": 30,
  "items": [
    {
      "item_id": 1,
      "item_name": "Premium Fish Feed 3mm",
      "sku": "FEED-PELLET-3MM",
      "total_quantity": 500.0,
      "unit": "kg",
      "total_cost": 24625.00,
      "transaction_count": 90
    },
    {
      "item_id": 2,
      "item_name": "Vitamin Mix",
      "sku": "VITAMIN-MIX",
      "total_quantity": 15.0,
      "unit": "kg",
      "total_cost": 150.00,
      "transaction_count": 30
    }
  ],
  "total_cost": 24775.00
}
```

**Query:**
```sql
SELECT
    it.item_master_id as item_id,
    im.item_name,
    im.sku,
    SUM(-it.quantity_change) as total_quantity,  -- Negative because 'use' transactions
    im.unit,
    SUM(it.total_cost) as total_cost,
    COUNT(*) as transaction_count
FROM inventory_transactions it
JOIN item_master im ON it.item_master_id = im.id
WHERE it.module_reference = 'biofloc'
  AND it.transaction_type = 'use'
  AND it.transaction_date >= NOW() - INTERVAL '30 days'
GROUP BY it.item_master_id, im.item_name, im.sku, im.unit
ORDER BY total_cost DESC;
```

---

#### `POST /items/{item_id}/modules`
Map item to a module.

**Path Parameters:**
- `item_id`: integer - Item to map

**Request Body:**
```json
{
  "module_name": "biofloc",
  "is_primary": true,
  "custom_settings": {
    "feed_type": "pellet",
    "protein_percentage": 40,
    "recommended_rate": "3% body weight per day"
  }
}
```

**Response:** `201 Created` with mapping object

---

## Service Layer Logic

### Key Service Functions

#### `add_stock(request, user_id)`

**Purpose:** Add new stock batch.

**Algorithm:**
1. Validate item exists and is active
2. Validate supplier exists (if provided)
3. Begin transaction:
   - Create inventory_batch record
   - Create inventory_transaction (type: 'add')
   - Update item_master.current_qty
4. Return batch info

---

#### `use_stock_fifo(item_id, quantity, purpose, ...)`

**Purpose:** Deduct stock using FIFO logic.

**Algorithm:** (detailed in API Reference section)

---

#### `batch_deduct_stock(deductions, module_ref, ...)`

**Purpose:** Atomic multi-item deduction.

**Algorithm:**
1. Begin database transaction
2. For each deduction:
   - Resolve item by SKU or item_id
   - Perform FIFO deduction
   - Track results
3. If ANY item fails → rollback entire transaction
4. If all succeed → commit and return results

**Error Handling:**
- InsufficientStock → rollback, return error
- ItemNotFound → rollback, return error
- DatabaseError → rollback, return error

---

#### `create_stock_adjustment(request, user_id)`

**Purpose:** Manual stock correction.

**Algorithm:** (detailed in API Reference section)

---

## FIFO Stock Management

### FIFO Algorithm Deep Dive

**First-In, First-Out (FIFO)** means the oldest stock is used first.

**Ordering:**
```sql
ORDER BY purchase_date ASC, id ASC
```

**Example Scenario:**

**Batches:**
```
Batch 1: 200 kg @ ₹50/kg, purchased 2025-11-01
Batch 2: 500 kg @ ₹48/kg, purchased 2025-11-10
Batch 3: 300 kg @ ₹52/kg, purchased 2025-11-15
```

**Deduction Request: 350 kg**

**Step 1:** Select oldest batch (Batch 1)
- Deduct: min(200, 350) = 200 kg
- Batch 1 remaining: 0 kg
- Still need: 350 - 200 = 150 kg

**Step 2:** Select next batch (Batch 2)
- Deduct: min(500, 150) = 150 kg
- Batch 2 remaining: 350 kg
- Need: 0 kg (done)

**Result:**
- Deducted 200 kg from Batch 1 @ ₹50/kg = ₹10,000
- Deducted 150 kg from Batch 2 @ ₹48/kg = ₹7,200
- **Total cost:** ₹17,200
- **Weighted average:** ₹17,200 / 350 kg = ₹49.14/kg

**Batches After:**
```
Batch 1: 0 kg (depleted, can be marked inactive)
Batch 2: 350 kg @ ₹48/kg
Batch 3: 300 kg @ ₹52/kg
```

### Weighted Average Cost Calculation

**Formula:**
```
Weighted Avg Cost = (Σ(qty_i × cost_i)) / total_qty
```

**Code:**
```python
total_cost = 0
total_qty = 0

for batch in batches_used:
    total_cost += batch['quantity'] * batch['unit_cost']
    total_qty += batch['quantity']

weighted_avg_cost = total_cost / total_qty
```

---

## Integration Architecture

### InventoryIntegration Helper Class

**Location:** `/backend/app/helpers/inventory_integration.py`

**Purpose:** Simplified interface for other modules to use inventory.

**Class Definition:**
```python
class InventoryIntegration:
    def __init__(self, module_name: str):
        self.module_name = module_name

    async def batch_deduct(
        self,
        deductions: List[Dict],
        module_reference: str,
        tank_id: str = None,
        batch_id: str = None,
        session_number: int = None,
        global_notes: str = None
    ):
        """Batch deduct multiple items atomically."""
        pass

    async def bulk_fetch(
        self,
        skus: List[str] = None,
        item_ids: List[int] = None,
        include_reserved: bool = True
    ):
        """Fetch multiple items efficiently."""
        pass

    async def create_reservation(
        self,
        item_sku: str,
        quantity: float,
        module_reference: str,
        reference_id: str = None,
        duration_hours: int = 24,
        notes: str = None
    ):
        """Create stock reservation."""
        pass

    async def confirm_reservation(self, reservation_id: str):
        """Confirm reservation and deduct stock."""
        pass

    async def get_consumption_report(self, days_back: int = 30):
        """Get consumption report for this module."""
        pass
```

**Usage Example (from Biofloc module):**
```python
# In biofloc feeding handler
from helpers.inventory_integration import InventoryIntegration

inv = InventoryIntegration(module_name="biofloc")

# Record feeding with automatic inventory deduction
result = await inv.batch_deduct(
    deductions=[
        {"sku": "FEED-PELLET-3MM", "quantity": 5.5},
        {"sku": "VITAMIN-MIX", "quantity": 0.2}
    ],
    module_reference="biofloc",
    tank_id=str(tank_id),
    batch_id=str(batch_id),
    session_number=1,
    global_notes="Morning feeding session"
)

# Check if successful
if result['success']:
    # Continue with biofloc operations
    total_cost = result['total_cost']
    # ... update biofloc_cycle_costs with feed cost
else:
    # Handle insufficient stock
    raise InsufficientStockError(result['error'])
```

---

## Frontend Architecture

### State Management

**React Query Configuration:**
```javascript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: true,
      retry: 1
    }
  }
});
```

**Example Hook Usage:**
```javascript
// Fetch items
const { data: items, isLoading, error } = useQuery(
  ['inventoryItems', filters],
  () => inventoryAPI.getItems(filters),
  {
    enabled: !!user,  // Only run if user authenticated
    staleTime: 5 * 60 * 1000
  }
);

// Add stock mutation
const addStockMutation = useMutation(
  data => inventoryAPI.addStock(data),
  {
    onSuccess: () => {
      queryClient.invalidateQueries(['inventoryItems']);
      queryClient.invalidateQueries(['currentStock']);
      queryClient.invalidateQueries(['dashboard']);
      enqueueSnackbar('Stock added successfully', { variant: 'success' });
    },
    onError: (error) => {
      enqueueSnackbar(error.message, { variant: 'error' });
    }
  }
);
```

---

## Performance Considerations

### Database Optimization

**Critical Indexes:**
```sql
-- FIFO batch selection (most critical!)
CREATE INDEX idx_inventory_batches_purchase_date
ON inventory_batches(item_master_id, purchase_date ASC)
WHERE is_active = TRUE AND remaining_qty > 0;

-- Transaction history queries
CREATE INDEX idx_transactions_item_date
ON inventory_transactions(item_master_id, transaction_date DESC);

-- Alert queries
CREATE INDEX idx_item_master_low_stock
ON item_master(current_qty, reorder_threshold)
WHERE is_active = TRUE AND current_qty < reorder_threshold;

CREATE INDEX idx_batches_expiry
ON inventory_batches(expiry_date)
WHERE is_active = TRUE AND remaining_qty > 0 AND expiry_date IS NOT NULL;
```

**Query Optimization:**
- Use `EXPLAIN ANALYZE` to verify index usage
- Limit result sets with pagination
- Use covering indexes where possible
- Denormalize frequently accessed data (e.g., username in transactions)

---

### API Performance

**Optimization Strategies:**

1. **Pagination:** All list endpoints
2. **Selective Fields:** Only return needed columns
3. **Single Query Joins:** Avoid N+1 queries
4. **Connection Pooling:** asyncpg pool configuration
5. **Caching:** React Query on frontend

**Performance Targets:**
- `GET /items`: <100ms
- `POST /stock/use`: <300ms (FIFO calculation)
- `GET /purchase-orders`: <200ms (optimized)
- `POST /stock/use-batch`: <500ms (up to 50 items)

---

## Security & Permissions

### Authentication & Authorization

**Module Access Check:**
```python
@router.get("/items")
async def get_items(
    current_user: dict = Depends(require_module_access("inventory"))
):
    # User has inventory module access
    pass
```

**User Attribution:**
- All operations tracked with user_id
- Username denormalized in transactions
- Created_by field in all tables

---

### Data Protection

**Soft Deletes:**
- Items: `is_active = FALSE`
- Batches: `is_active = FALSE`
- Suppliers: `is_active = FALSE`

**Audit Trail:**
- Complete transaction history
- Stock adjustments tracked
- PO changes logged

**Validation:**
- Pydantic schemas for all inputs
- Database constraints (CHECK, FOREIGN KEY)
- Business logic validation

---

**End of Technical Guide**

For operational procedures and user workflows, see [User Guide](./user-guide.md).
