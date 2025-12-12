# S12: Order Allocation Module (Spreadsheet-Style)

**Module Type:** Child Module (3.2)  
**Parent Module:** Outward Operations (Module 3)  
**Build Priority:** CRITICAL PATH  
**Estimated Duration:** 65-70 hours (8-9 days)  
**Status:** Architecture Complete - Ready for Implementation

---

## 📋 Overview

### Primary Purpose
Spreadsheet-style allocation interface for allocating inventory to sales orders based on delivery date.

### Key Differentiator
Unlike traditional order-by-order allocation, this system uses a **master allocation sheet** organized as:
- **Rows:** Items (products)
- **Columns:** Customers  
- **Sheet per delivery date:** One allocation sheet for each delivery date

---

## 🎯 Core Workflow

### 1. Sheet Generation
```
User selects delivery_date = '2025-12-15'
    ↓
System queries all SOs with delivery_date = '2025-12-15'
    ↓
Creates matrix: Items (rows) × Customers (columns)
    ↓
Populates ORDER column from SO line items
    ↓
Auto-fills SENT column using FIFO algorithm
```

### 2. Stock Status Lifecycle
```
1. SO Created → Call /inventory/allocate → Stock: available → allocated (on hold)
2A. SO Cancelled → Call /inventory/deallocate → Stock: allocated → available (released)
2B. Invoice Generated → Call /inventory/confirm-allocation → Stock: allocated → delivered, qty=0 (debited)
```

### 3. Invoice Generation Workflow
```
User fills SENT quantities (auto-filled or manual edits)
    ↓
User clicks "Mark Ready" for customer
    ↓
User clicks "Generate Invoice" button
    ↓
System creates invoice using SENT quantities
    ↓
System debits stock from inventory
    ↓
Button changes to "Invoiced" (disabled)
```

---

## 🏗️ Database Schema

### Table 1: allocation_sheets
```sql
CREATE TABLE allocation_sheets (
    id SERIAL PRIMARY KEY,
    delivery_date DATE NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active', -- active, archived
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_allocation_sheets_date ON allocation_sheets(delivery_date);
```

**Purpose:** One record per delivery date to organize allocation work.

---

### Table 2: allocation_sheet_cells
```sql
CREATE TABLE allocation_sheet_cells (
    id SERIAL PRIMARY KEY,
    sheet_id INT REFERENCES allocation_sheets(id) ON DELETE CASCADE,
    item_id INT REFERENCES zoho_items(id),
    customer_id VARCHAR(100), -- Zoho customer ID
    so_id INT REFERENCES sales_orders(id),
    
    -- Data columns
    order_quantity DECIMAL(10,3) NOT NULL, -- From SO, editable
    sent_quantity DECIMAL(10,3), -- Auto-filled by FIFO, editable
    
    -- Tracking
    order_modified BOOLEAN DEFAULT FALSE, -- True if ORDER edited
    invoice_status VARCHAR(50) DEFAULT 'pending', -- pending, ready, invoiced
    invoice_id INT, -- FK to invoices table (when ready)
    
    -- Allocation details (JSON for batch tracking)
    allocated_batches JSONB, -- [{batch_id: 1, quantity: 2.5}, ...]
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    UNIQUE(sheet_id, item_id, customer_id)
);

CREATE INDEX idx_allocation_cells_sheet ON allocation_sheet_cells(sheet_id);
CREATE INDEX idx_allocation_cells_so ON allocation_sheet_cells(so_id);
CREATE INDEX idx_allocation_cells_invoice_status ON allocation_sheet_cells(invoice_status);
```

**Purpose:** Each cell represents one (item, customer) combination with ORDER and SENT quantities.

**Key Fields:**
- `order_quantity`: From SO, user-editable, syncs back to SO
- `sent_quantity`: Auto-filled via FIFO, user-editable, used for invoicing
- `allocated_batches`: JSON tracking which batches were allocated (backend only)
- `invoice_status`: pending → ready → invoiced workflow

---

### Table 3: allocation_sheet_audit
```sql
CREATE TABLE allocation_sheet_audit (
    id SERIAL PRIMARY KEY,
    cell_id INT REFERENCES allocation_sheet_cells(id),
    field_changed VARCHAR(50), -- 'order_quantity', 'sent_quantity'
    old_value DECIMAL(10,3),
    new_value DECIMAL(10,3),
    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose:** Audit trail for all cell modifications.

---

## 🧮 FIFO Allocation Algorithm

### Priority System (3-Tier)

**Priority Order:**
1. **Expiring Soon (< 2 days)** - HIGHEST PRIORITY
2. **Repacked Batches (B###R)** - Second
3. **Oldest Regular Batches** - Standard FIFO by entry_date

### Customer Priority (FIFO)
Customers allocated in order of SO number (lower number = earlier = higher priority).

**Example:**
```
Available Stock: 20kg Basil
- SO-301 (radha regent): 15kg ordered
- SO-302 (coffee ecr): 10kg ordered

Result:
- SO-301 gets 15kg
- SO-302 gets 5kg (shortfall of 5kg)
```

### Auto-Fill Algorithm
```python
async def auto_fill_sent_quantities(sheet_id, delivery_date):
    # Get all cells for this sheet
    cells = await get_cells(sheet_id)
    
    # Group by item
    for item_id, item_cells in group_by_item(cells):
        # Get available stock for this item
        stock = await get_available_stock(
            item_id=item_id,
            location='packed_warehouse'
        )
        
        # Sort stock by FIFO priority
        # ORDER BY: expiry_date (< 2 days first), is_repacked DESC, entry_date ASC
        stock_sorted = sort_by_fifo(stock)
        
        # Sort customers by SO number (FIFO)
        customers_sorted = sort_by_so_number(item_cells)
        
        # Allocate stock to customers
        remaining_stock = stock_sorted.copy()
        
        for customer_cell in customers_sorted:
            needed = customer_cell.order_quantity
            allocated = []
            
            for batch in remaining_stock:
                if needed <= 0:
                    break
                    
                take = min(batch.quantity, needed)
                allocated.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'quantity': take
                })
                batch.quantity -= take
                needed -= take
            
            # Update cell
            customer_cell.sent_quantity = sum(a['quantity'] for a in allocated)
            customer_cell.allocated_batches = allocated
            
            # Remove exhausted batches
            remaining_stock = [b for b in remaining_stock if b.quantity > 0]
```

**Key Features:**
- Respects expiry priority (move out soon-to-expire items first)
- Respects repacked priority (move out degraded items)
- Respects customer FIFO (earliest SO gets priority)
- Handles partial fulfillment (shortfalls tracked)

---

## 🔌 API Endpoints (12 Total)

### Sheet Management (4 endpoints)

#### 1. GET /api/v1/allocation/sheet/{delivery_date}
**Purpose:** Load/generate allocation sheet for delivery date

**Response:**
```json
{
  "sheet_id": 123,
  "delivery_date": "2025-12-15",
  "items": [
    {"id": 1, "name": "Basil", "variety": "Italian", ...}
  ],
  "customers": [
    {"id": "C001", "name": "radha regent", "so_number": "SO-301"}
  ],
  "cells": [
    {
      "id": 1,
      "item_id": 1,
      "customer_id": "C001",
      "order_quantity": 10.0,
      "sent_quantity": 7.0,
      "has_shortfall": true,
      "allocated_batches": [...]
    }
  ],
  "totals": {"total_order": 315.5, "total_sent": 312.0, "shortfall": 3.5}
}
```

#### 2. PUT /api/v1/allocation/cell/{cell_id}
**Purpose:** Update ORDER or SENT quantity (optimistic updates)

**Request:**
```json
{
  "order_quantity": 12.0,  // Optional
  "sent_quantity": 10.0,   // Optional
  "version": 5  // For conflict detection
}
```

**Actions:**
- If ORDER changed: Update SO, mark as modified
- If SENT changed: Recalculate batches, reset invoice status
- Return updated cell with new version

#### 3. POST /api/v1/allocation/sheet/{sheet_id}/auto-fill
**Purpose:** Trigger FIFO auto-fill for entire sheet

**Response:**
```json
{
  "updated_cells": 45,
  "shortfalls": [
    {"item_id": 1, "customer_id": "C003", "shortage": 3.0}
  ]
}
```

#### 4. GET /api/v1/allocation/dates
**Purpose:** List available delivery dates with SO counts

**Response:**
```json
{
  "dates": [
    {
      "delivery_date": "2025-12-15",
      "so_count": 12,
      "has_shortfalls": true,
      "invoice_status": "partial"
    }
  ]
}
```

---

### Invoice Generation (3 endpoints)

#### 5. POST /api/v1/allocation/customer/mark-ready
**Purpose:** Mark customer as ready for invoice generation

**Request:**
```json
{
  "sheet_id": 123,
  "customer_id": "C001"
}
```

**Actions:** Update all cells for customer: invoice_status = 'ready'

#### 6. POST /api/v1/allocation/customer/generate-invoice
**Purpose:** Generate invoice and debit stock

**Request:**
```json
{
  "sheet_id": 123,
  "customer_id": "C001"
}
```

**Actions:**
1. Get all cells with invoice_status='ready' for customer
2. Create invoice with SENT quantities
3. Call /inventory/confirm-allocation (debit stock)
4. Update cells: invoice_status='invoiced', invoice_id=X

**Response:**
```json
{
  "invoice_id": 456,
  "invoice_number": "INV-2025-001",
  "total_amount": 1250.00,
  "stock_debited": true
}
```

#### 7. GET /api/v1/allocation/sheet/{sheet_id}/invoice-status
**Purpose:** Get invoice status for all customers on sheet

**Response:**
```json
{
  "customers": [
    {
      "customer_id": "C001",
      "customer_name": "radha regent",
      "invoice_status": "ready",
      "items_count": 8,
      "total_sent": 45.5
    }
  ]
}
```

---

### Statistics (2 endpoints)

#### 8. GET /api/v1/allocation/sheet/{sheet_id}/statistics
**Purpose:** Get comprehensive statistics for sheet

**Response:**
```json
{
  "summary": {
    "total_ordered": 315.5,
    "total_sent": 312.0,
    "total_shortfall": 3.5,
    "fulfillment_rate": 98.9
  },
  "by_item": [
    {
      "item_name": "Basil Italian",
      "total_ordered": 50.0,
      "total_sent": 47.0,
      "shortfall": 3.0,
      "customers_affected": 2
    }
  ],
  "by_customer": [
    {
      "customer_name": "radha regent",
      "total_ordered": 45.5,
      "total_sent": 45.5,
      "fulfillment_rate": 100
    }
  ]
}
```

#### 9. GET /api/v1/allocation/statistics/dashboard
**Purpose:** Cross-date statistics for management dashboard

---

### Utility (3 endpoints)

#### 10. POST /api/v1/allocation/sheet/{sheet_id}/recalculate
**Purpose:** Re-run FIFO for entire sheet (admin)

#### 11. GET /api/v1/allocation/sheet/{sheet_id}/audit-log
**Purpose:** Get change history for sheet

#### 12. POST /api/v1/allocation/batch/reassign
**Purpose:** Manually reassign specific batches (admin override)

---

## 🎨 Frontend Components

### UI Structure
```
/allocation/sheet/:date
├── Date Picker (Calendar)
└── Tabs:
    ├── Allocation Grid (main spreadsheet)
    ├── Statistics (totals, charts)
    └── Invoice Status (customer list)
```

### Component 1: AllocationGrid
**Spreadsheet-style grid with:**
- Item columns: NO, TYPE, VARIETY, SUB VARIETY
- Customer columns (repeated): ORDER, SENT
- Totals columns: TOTAL ORDER, TOTAL SENT

**Visual Indicators:**
- 🟨 Yellow: SENT cell with shortfall
- 🟧 Orange: ORDER cell that was edited
- ⚠️ Icon: Next to SENT header when shortfalls exist
- \* Asterisk: On customer name when ORDER modified

**Editable Cells:**
- ORDER: Edit saves immediately, syncs to SO, marks modified
- SENT: Edit saves immediately, recalculates batches

**Optimistic Updates:**
- Saves happen instantly (no Save button)
- Backend validates and returns conflicts if any
- Multi-user: Last save wins with warning

### Component 2: StatisticsDashboard
**Three sections:**
1. **Summary Cards:** Total Ordered, Total Sent, Shortfall, Fulfillment %
2. **Charts:** Item breakdown, Customer fulfillment
3. **Shortfalls Table:** Detailed list of unfulfilled items

### Component 3: InvoiceStatusList
**Customer list table:**
- Customer name
- Items count
- Total sent (kg)
- Invoice status (pending/ready/invoiced)
- Action buttons:
  - "Mark Ready" (pending → ready)
  - "Generate Invoice" (ready → invoiced)
  - "Invoiced" chip (disabled)

---

## 🔄 Key Features

### 1. Real-Time Multi-User Editing
- **Strategy:** Optimistic updates
- **Mechanism:** 
  - User edits cell → Save immediately
  - Backend validates with version check
  - If conflict: Warn user, reload cell
- **Best for:** Low-conflict scenarios (users edit different cells)

### 2. Two-Way SO Synchronization
- **ORDER Column:** Editable in allocation sheet
- **Action:** When edited, updates `sales_order_items.quantity`
- **Visual:** Orange background + asterisk on customer name
- **Audit:** Logged in `allocation_sheet_audit`

### 3. Shortfall Handling
- **Detection:** SENT \u003c ORDER
- **Visual:** Yellow cell background + ⚠️ icon
- **Reporting:** Tracked in statistics dashboard
- **Action:** User can manually adjust or wait for restock

### 4. Batch Tracking (Backend Only)
- **UI Shows:** Only quantities (e.g., "7.5 kg sent")
- **Backend Tracks:** Exact batches in `allocated_batches` JSON
  ```json
  [
    {"batch_id": 10, "batch_number": "B120R", "quantity": 5.0},
    {"batch_id": 11, "batch_number": "B121", "quantity": 2.5}
  ]
  ```
- **Purpose:** Full traceability for invoicing and stock debit

---

## 📊 Implementation Phases

### Phase 1: Core Allocation (30-35 hours)
**Backend:**
- Database migrations (3 tables)
- Sheet generation API
- FIFO auto-fill algorithm
- Cell update API with optimistic locking
- SO sync on ORDER edit

**Frontend:**
- AllocationGrid component
- DatePicker integration
- Optimistic updates hook
- Visual indicators (colors, icons)

### Phase 2: Invoice Generation (15-20 hours)
**Backend:**
- Mark ready endpoint
- Generate invoice endpoint
- Invoice status endpoint
- Integration with invoice module

**Frontend:**
- InvoiceStatusList tab
- Customer action buttons
- Status workflow UI

### Phase 3: Statistics & Polish (15-20 hours)
**Backend:**
- Statistics API
- Dashboard aggregations

**Frontend:**
- StatisticsDashboard component
- Charts integration
- Multi-user conflict handling
- Polish & bug fixes

**Total Estimated Effort:** 65-70 hours (8-9 days)

---

## ✅ Dependencies

### Required Modules (Must Exist First)
- ✅ Sales Orders Module (3.1) - For SO data
- ✅ Inventory Module (2.1) - For stock APIs
- ✅ Batch Tracking Module (2.2) - For batch data
- ⏳ Invoice Module (3.3) - For invoice generation

### Inventory APIs Used
1. `POST /api/v1/inventory/allocate` - Reserve stock (SO creation)
2. `POST /api/v1/inventory/deallocate` - Release stock (SO cancel)
3. `POST /api/v1/inventory/confirm-allocation` - Debit stock (Invoice)
4. `GET /api/v1/inventory/availability` - Check stock levels

---

## 🎯 Testing Checklist

### Allocation Logic
- [ ] FIFO respects expiry priority (< 2 days allocated first)
- [ ] FIFO respects repacked priority (B###R allocated second)
- [ ] FIFO respects customer priority (SO number sequence)
- [ ] Partial fulfillment handled correctly
- [ ] Shortfalls highlighted in UI

### Multi-User
- [ ] Two users editing different cells (no conflict)
- [ ] Two users editing same cell (conflict detected, last save wins)
- [ ] Reload on conflict works correctly

### SO Synchronization
- [ ] Editing ORDER updates SO quantity
- [ ] ORDER changes marked with orange + asterisk
- [ ] Audit log captures changes

### Invoice Generation
- [ ] Mark ready changes status correctly
- [ ] Generate invoice creates invoice with SENT quantities
- [ ] Stock debited via /confirm-allocation
- [ ] Button states update correctly

### Statistics
- [ ] Totals calculate correctly
- [ ] Shortfalls reported accurately
- [ ] Customer fulfillment rates correct

---

## 📝 Future Enhancements (Post-Phase 3)

1. **Bulk Operations**
   - "Auto-fill all sheets for week"
   - "Generate all invoices" button

2. **Advanced Filters**
   - Filter by customer type (B2B/B2C)
   - Filter by fulfillment status

3. **Export Features**
   - Export sheet to Excel
   - Email allocation summary to customers

4. **Real-Time Sync (WebSockets)**
   - Upgrade from optimistic updates to live sync
   - See other users' cursors/edits in real-time

5. **Mobile App**
   - Warehouse staff view allocation on tablets
   - Mark items as "picked" directly from app

---

**Document Version:** 1.0  
**Last Updated:** December 12, 2025  
**Status:** Architecture Complete - Ready for Phase 1 Implementation
