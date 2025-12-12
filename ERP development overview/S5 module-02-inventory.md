# MODULE 2: INVENTORY

**Document:** Step 5 - Module 2: Inventory  
**Filename:** 05-Module-02-Inventory.md

---

## **Module Overview**

**Module Name:** Inventory  
**Module Type:** Parent Module  
**Child Modules:** 3 (Inventory Management, Batch Tracking, Wastage Tracking & Analytics)  
**Priority:** CRITICAL PATH - Central hub between inward and outward operations

**Purpose:**  
Manage stock levels, batch traceability, and comprehensive wastage tracking across the entire supply chain from farm to customer.

---

## **Workflow Summary**

```
Packing (Inward) → INVENTORY → Allocation (Outward)

Key Activities:
- Multi-location inventory tracking
- Batch-wise stock management
- FIFO allocation (with repacked batch priority)
- Real-time stock visibility
- Wastage event aggregation and analytics
- Reorder level monitoring
- Shelf life management
```

---

## **Internal Dashboard**

**Purpose:** Central inventory command center

**Key Metrics:**
- Total stock value (INR)
- Stock by location (receiving, processing, packed, vehicles)
- Low stock items count (below reorder level)
- Items requiring action (expiring soon, quality hold)
- Batch count (active, repacked, archived)
- Total wastage this month (quantity and cost)
- Stock movements (in/out) today

**Visualizations:**
- Stock levels by item (bar chart)
- Wastage trend (last 30 days)
- Batch age distribution
- Top wastage items
- Stock turnover rate
- Location-wise stock distribution

**Quick Actions:**
- View low stock items
- Check batch history
- Generate wastage report
- Adjust stock (with approval)
- View pending allocations

---

## **CHILD MODULE 2.1: INVENTORY MANAGEMENT**

### **Overview**

**Purpose:** Track stock levels across multiple locations with batch-level granularity

**Build Priority:** CRITICAL - Build in Phase 3 (Weeks 7-8)  
**Estimated Duration:** 7-10 days

---

### **Core Features**

#### **1. Multi-Location Inventory Tracking**

**Locations:**
- **Receiving Area:** Goods just arrived, awaiting grading
- **Processing Area:** In grading/sorting
- **Packed Goods Warehouse:** Ready for sale (cold storage)
- **Delivery Vehicles:** Out for delivery
- **Quality Hold:** Items quarantined for inspection

**Stock Movement Flow:**
```
Receiving Area (from GRN)
    ↓
Processing Area (grading/sorting)
    ↓
Packed Goods Warehouse (after packing)
    ↓
Delivery Vehicles (allocated to SO)
    ↓
Delivered (removed from inventory)
```

**Tracking:**
- Item
- Batch number
- Location
- Quantity
- Grade (if applicable)
- Status (available, allocated, hold, in-transit)
- Entry date/time
- Expected expiry/best-before date

---

#### **2. Stock Updates from Packing**

**NOT from GRN directly** - Stock enters inventory AFTER packing complete

**Process:**
1. Packing module completes packing for a batch
2. Triggers inventory update API
3. Stock added to "Packed Goods Warehouse" location
4. Status: Available for allocation
5. Links to batch number

**Data Received from Packing:**
- Batch number
- Item (and grade if applicable)
- Packed quantity
- Pack size
- Location (default: Packed Goods Warehouse)
- Packing date/time

---

#### **3. FIFO Allocation Logic & Stock Allocation APIs**

**Priority Order:**
1. **Repacked Batches (B###R)** - HIGHEST PRIORITY
   - Move these out fastest to avoid further degradation
2. **Oldest Regular Batches** - Standard FIFO
   - Based on packing date (or receiving date if no packing)
3. **Newer Batches** - Last in queue

**Allocation Process (OLD - Manual):**
1. SO created and awaiting allocation
2. System queries available inventory
3. Applies FIFO with repacked priority
4. Suggests batches to allocate
5. User confirms or manually adjusts
6. Stock status changes: Available → Allocated
7. Stock moves to "Delivery Vehicles" location when picked

**NEW: Automated Stock Allocation APIs** ✨

**Three Core Endpoints:**

1. **`POST /api/v1/inventory/allocate`** - Reserve Stock
   ```json
   {
       "order_id": 123,
       "item_id": 1,
       "quantity": 5.0,
       "location": "packed_warehouse",
       "batch_ids": [10, 11]  // Optional - auto FIFO if not provided
   }
   ```
   **What it does:**
   - Changes status: `available` → `allocated`
   - Uses FIFO with repacked priority
   - Supports partial allocation (splits records)
   - Creates movement log
   - Returns allocated batches

2. **`POST /api/v1/inventory/deallocate`** - Release Stock (Cancel Order)
   ```json
   {
       "order_id": 123
   }
   ```
   **What it does:**
   - Changes status: `allocated` → `available`
   - Releases ALL stock for the order
   - Creates movement log
   - Stock becomes available again

3. **`POST /api/v1/inventory/confirm-allocation`** - Debit Stock (Invoice)
   ```json
   {
       "order_id": 123
   }
   ```
   **What it does:**
   - Changes status: `allocated` → `delivered`
   - Sets quantity to 0 (stock debited)
   - Creates stock_out movement log
   - Removes from available inventory

**Stock Lifecycle with APIs:**
```
20kg Lettuce (Available)
    ↓
[Order Created] → POST /allocate {order_id: 123, qty: 5kg}
    ↓
15kg Available + 5kg Allocated (to order #123)
    ↓
[Order Cancelled] → POST /deallocate {order_id: 123}
    ↓
20kg Available + 0kg Allocated
    
OR

[Order Invoiced] → POST /confirm-allocation {order_id: 123}
    ↓
15kg Total (5kg permanently removed)
```

**Integration with Sales Orders Module:**
- When SO created → Call `/inventory/allocate`
- When SO cancelled → Call `/inventory/deallocate`
- When SO → Invoice → Call `/inventory/confirm-allocation`

**Edge Cases:**
- Partial batch allocation (e.g., need 50kg, batch has 100kg)
- Grade-specific allocation (customer wants Grade A only)
- Customer preferences (avoid certain farms)
- Insufficient stock (API returns error with available qty)

---

#### **4. Stock Reservation (Legacy - Now Replaced by Allocation APIs)**

**OLD METHOD:**
- When SO created, can optionally reserve stock
- Reserved stock not allocated to other orders
- Reservation expires after X hours (configurable)

**NEW METHOD:**
Use `/inventory/allocate` API instead - it's the same as reservation but properly tracked

---

#### **5. Reorder Level Monitoring**

**Reorder Level Configuration:**
- Set per item (e.g., Iceberg: reorder at 50kg)
- Optional: per location
- Alert threshold (notify when stock hits reorder level)

**Low Stock Alerts:**
- In-app notification
- Email to procurement team
- Dashboard widget
- Daily summary report

**Smart Reordering:**
- Consider incoming POs
- Seasonal demand patterns (future enhancement)
- Lead time from farms

---

#### **6. Batch-Wise Inventory View**

**Batch Level Tracking:**
- View all batches in inventory
- Filter by: item, location, date range, farm
- Batch details:
  - Batch number (e.g., B123, B124R)
  - Item and grade
  - Quantity available
  - Location
  - Age (days in inventory)
  - Source farm
  - Quality issues (if any)
  - Allocated quantity
  - Status

**Batch Actions:**
- View complete history (from PO to current)
- Mark for quality hold
- Trigger repacking (if damage found)
- View wastage events for this batch
- Allocate to specific SO

---

#### **7. Shelf Life Management**

**Expiry Tracking:**
- Best-before date (configurable per item)
- Alert before expiry (e.g., 2 days before)
- Auto-flag expired items

**Actions for Expiring Items:**
- Priority allocation (move out faster)
- Price reduction (if sold as-is)
- Mark for disposal
- Quality hold for inspection

---

#### **8. Inventory Adjustments**

**Stock Adjustments (Supervised):**
- Manual increase/decrease (with approval)
- Reasons: Physical count variance, damage, theft, donation
- Photo documentation required
- Approval workflow (admin only)
- Audit trail

**Physical Stock Count:**
- Cycle counting by location
- Compare system vs physical
- Variance resolution
- Adjust inventory with notes

---

#### **9. Inventory Reports**

**Standard Reports:**
- Current stock by item
- Current stock by location
- Batch age report
- Stock movement report (in/out)
- Valuation report (stock value)
- Slow-moving items
- Expiring items (next 7 days)

**Export Formats:**
- CSV, Excel, PDF
- Configurable columns
- Date range filters

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/inventory/list` - List inventory with filters
- `/api/inventory/by-batch` - Batch-wise view
- `/api/inventory/add` - Add stock (from packing)
- `/api/inventory/allocate` - Allocate stock (FIFO)
- `/api/inventory/adjust` - Manual adjustment
- `/api/inventory/check-availability` - Stock check
- `/api/inventory/low-stock` - Low stock items
- `/api/inventory/expiring` - Expiring items

**Frontend (React):**
- `<InventoryList />` - Main inventory view
- `<BatchInventory />` - Batch-wise view
- `<StockAvailabilityChecker />` - Check stock for SO
- `<InventoryAdjustment />` - Adjustment form
- `<LowStockAlert />` - Alert widget
- `<LocationStockView />` - Multi-location view

**Database (Supabase):**
- `inventory` table:
  - item_id, batch_id, location, quantity, status, grade
- `inventory_movements` table:
  - movement_type (in/out), quantity, from_location, to_location, timestamp
- `reorder_levels` table:
  - item_id, reorder_quantity, alert_threshold

---

### **Dependencies**

**Required:**
- Packing Module (Module 1.4) - Stock source
- Batch Tracking (Module 2.2) - Batch numbers
- Item Database (Zoho) - Item master
- User Authentication

**Integrates With:**
- Order Allocation (Module 3.2) - Stock allocation
- Wastage Tracking (Module 2.3) - Cold storage wastage

---

### **Validation Rules**

- Stock cannot go negative
- Location must be valid
- Batch number must exist
- Adjustments require approval (if > threshold)
- Status transitions must be valid
- Cannot allocate more than available

---

### **Testing Checklist**

- [ ] Add stock from packing module
- [ ] FIFO allocation (verify repacked priority)
- [ ] Multi-location stock movement
- [ ] Low stock alerts trigger correctly
- [ ] Batch-wise inventory view accurate
- [ ] Stock adjustment with approval
- [ ] Expiry alerts
- [ ] Stock availability check (current + incoming)
- [ ] Physical count variance resolution
- [ ] Mobile responsiveness
- [ ] Concurrent allocation (race conditions)

---

## **CHILD MODULE 2.2: BATCH TRACKING**

### **Overview**

**Purpose:** Complete traceability from farm to customer with unique batch numbers

**Build Priority:** CRITICAL - Build in Phase 1 (Week 1) - FOUNDATION MODULE  
**Estimated Duration:** 3-4 days

---

### **Core Features**

#### **1. Batch Number Generation**

**Format:**
- Sequential only: B001, B002, B003, B004...
- No date encoding (security/opacity)
- Globally unique across all batches

**Generation Trigger:**
- At GRN creation (before goods arrive)
- Auto-generated by system
- Cannot be manually edited

**Special Batch Numbers:**
- Regular batch: B001
- Repacked batch: B001R (parent-child relationship)
- System tracks lineage

---

#### **2. Batch Audit Trail**

**Complete Journey Tracked:**

**From PO:**
- PO number
- Who raised PO
- When raised
- Farm/vendor
- Items ordered
- Expected quantities
- Expected dispatch/delivery dates

**From GRN:**
- GRN number
- Who received
- When received
- Actual quantities
- Damage, reject, accepted
- Photos (if wastage)
- Cost allocation (farm/us)
- Transport details

**From Grading/Sorting:**
- Grading results (A/B/C)
- QC wastage
- Photos
- Who graded
- Date/time

**From Packing:**
- Pack sizes and quantities
- Overfill wastage
- Photos
- Who packed
- Labels printed
- Date/time

**From Inventory:**
- Entry date to inventory
- Location movements
- Status changes

**From Allocation:**
- Which SO(s) allocated to
- Allocation date
- Quantity per SO

**From Delivery:**
- Which customer(s) received
- Delivery date/time
- Proof of delivery
- Any customer complaints

---

#### **3. Active Tracking Period**

**Duration:**
- **From:** PO creation
- **To:** 3 days post-delivery to customer

**Purpose:**
- Customer claim window (end of delivery day to 3 days later)
- Fresh produce quality guarantee period

**After Active Period:**
- Batch moves to historical archive
- Still searchable forever
- No alerts or notifications

---

#### **4. Batch Query & Search**

**Search By:**
- Batch number (exact match)
- PO number
- GRN number
- SO number
- Farm name
- Item name
- Customer name
- Date range
- Status (active/archived)

**Query Results:**
- Complete batch history (all stages)
- All wastage events linked to batch
- All documents (PO, GRN, packing labels, SO)
- Photos across all stages
- Current location and status
- Customer(s) who received this batch

---

#### **5. Batch Status**

**Status Options:**
- Ordered (PO created)
- Received (GRN complete)
- In Grading
- In Packing
- In Inventory (available)
- Allocated (reserved for SO)
- In Transit (out for delivery)
- Delivered
- Archived (historical)

**Status Transitions Tracked:**
- Status, timestamp, user

---

#### **6. Repacking Workflow**

**Trigger:** Cold storage damage (partial damage to packed items)

**Process:**
1. Damage identified in cold storage
2. Log wastage event (with photos)
3. Create repacking task
4. Original batch: B124
5. New batch: B124R (child of B124)
6. Repacked quantity logged
7. Parent-child relationship maintained
8. B124R gets FIFO priority

**Repacking Rules:**
- **One repack maximum** per batch
- Cannot repack a repacked batch (B124R-R not allowed)
- Repacked batches flagged in inventory
- FIFO priority over regular batches

**Same-Batch Consolidation:**
- Multiple damaged packs (same batch) → Consolidated into fewer new packs
- Retain original batch number with repack flag

**Mixed-Batch Consolidation:**
- ⚠️ **PARKED FOR FUTURE DISCUSSION**
- Different batches combined into new packs
- Traceability challenge

---

#### **7. Batch-Linked Wastage**

**All Wastage Events Link to Batch:**
- Receiving damage/reject
- Grading QC wastage
- Packing overfill
- Cold storage damage (triggers repack)
- Customer damage claims

**Query Wastage by Batch:**
- Total wastage for batch (all stages)
- Wastage breakdown by stage
- Cost impact
- Photos

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/batch/generate` - Generate new batch number
- `/api/batch/{batch_number}` - Get batch details and history
- `/api/batch/{batch_number}/timeline` - Complete timeline
- `/api/batch/search` - Search batches
- `/api/batch/{batch_number}/repack` - Create repacked batch
- `/api/batch/active` - List active batches
- `/api/batch/archive` - Archive old batches

**Frontend (React):**
- `<BatchTimeline />` - Visual timeline of batch journey
- `<BatchSearch />` - Search interface
- `<BatchDetail />` - Complete batch info
- `<RepackingModal />` - Repacking workflow
- `<BatchWastageView />` - Wastage events for batch

**Database (Supabase):**
- `batches` table:
  - batch_number, status, created_at, archived_at
  - parent_batch_id (for repacking)
  - is_repacked (boolean)
- `batch_history` table:
  - batch_id, stage, event, details, timestamp, user_id
- `batch_documents` table:
  - Links to PO, GRN, SO, invoices

---

### **Dependencies**

**Required:**
- None (foundation module)

**Used By:**
- GRN Management (Module 1.2) - Generates batches
- Grading & Sorting (Module 1.3) - Tracks batch
- Packing (Module 1.4) - Tracks batch
- Inventory (Module 2.1) - Batch-wise inventory
- Wastage Tracking (Module 2.3) - Links wastage to batch
- Order Allocation (Module 3.2) - Allocates batches
- All reporting modules

---

### **Testing Checklist**

- [ ] Generate sequential batch numbers
- [ ] Track complete batch journey (PO → delivery)
- [ ] Search by various criteria
- [ ] View batch timeline
- [ ] Create repacked batch (B###R)
- [ ] FIFO priority for repacked batches
- [ ] Link wastage events to batch
- [ ] Archive old batches
- [ ] Historical search works
- [ ] Parent-child repacking relationship
- [ ] Performance with 1000+ batches

---

## **CHILD MODULE 2.3: WASTAGE TRACKING & ANALYTICS**

### **Overview**

**Purpose:** Centralized wastage data aggregation, cost tracking, and analytics across entire supply chain

**Build Priority:** CRITICAL - Build in Phase 1 (Weeks 1-2) - FOUNDATION MODULE  
**Estimated Duration:** 5-7 days

---

### **Core Features**

#### **1. Wastage Event Logging System**

**Centralized Database:**
- All modules log wastage events here
- Single source of truth for wastage data
- Links to batch numbers, PO, GRN, SO

**Wastage Event Structure:**
- Event ID (unique)
- Batch number
- Stage (receiving, grading, packing, cold storage, customer)
- Wastage type (damage, reject, QC, overfill, etc.)
- Quantity
- Cost allocation (Farm/Us)
- Photos (mandatory)
- Reason/notes
- User who logged
- Timestamp
- Location
- Related documents (PO, GRN, SO)

---

#### **2. Wastage Categories with Cost Allocation**

**1. Receiving - Damage (Farm or Us):**
- Transport/handling damage
- Photos mandatory
- Cost allocation toggle
- If Farm: Deducted from farm invoice
- If Us: Absorbed in our costs

**2. Receiving - Reject (Farm or Us):**
- Out-of-spec produce
- Photos mandatory
- Cost allocation toggle
- Same billing impact as damage

**3. Grading/Sorting - QC Wastage (Your cost):**
- Internal quality standard rejection
- Photos mandatory
- Always your cost
- Not charged to farm

**4. Packing - Overfill (Your cost):**
- Extra weight per pack (yield loss)
- Photos mandatory
- Example: 10kg → 19 bags instead of 20
- Cost absorbed

**5. Cold Storage - Partial Damage (Your cost):**
- Requires repacking
- Triggers repacking workflow
- Creates B###R batch
- Photos mandatory

**6. Cold Storage - Full Loss (Your cost):**
- Complete pack damage
- Write-off
- Photos mandatory

**7. Customer - Damage Claims:**
- From B2B/B2C tickets
- Photos mandatory (from customer)
- Within claim window (end of delivery day)
- May result in credit/replacement

---

#### **3. Photo Upload & Storage**

**Universal Photo Upload:**
- At ANY stage across entire process
- Mandatory for all wastage events
- Multiple photos per event
- Stored in Supabase Storage

**Photo Metadata:**
- Event ID
- Batch number
- Stage
- Timestamp
- GPS coordinates (if available)
- User who uploaded

**Photo Sharing:**
- **External Sharing (Farms):**
  - Receiving stage damage/reject
  - Grading/Sorting QC issues (as needed)
- **Internal Only:**
  - Packing wastage
  - Cold storage damage
  - Customer claims (unless farm dispute)

**Photo Retention:**
- ⚠️ **PARKED FOR FUTURE DISCUSSION**
- Consider: Legal requirements, storage costs, dispute windows

---

#### **4. Repacking Workflow**

**Trigger:** Cold storage partial damage

**Process:**
1. Wastage event logged: "Cold Storage - Partial Damage"
2. Photos uploaded
3. Quantity of damaged packs documented
4. User initiates repacking
5. System creates new batch: B124R (child of B124)
6. Repacking event logged:
   - Parent batch: B124
   - Child batch: B124R
   - Quantity repacked
   - Reason for repack
   - Photos of damage
   - Date/time, user
7. Repacked items get FIFO priority
8. **One repack maximum** - Cannot repack B124R again

**Same-Batch Consolidation:**
- Multiple damaged packs (same batch) → Fewer new packs
- Retain B124 with repack flag

**Mixed-Batch Consolidation:**
- ⚠️ **PARKED FOR FUTURE DISCUSSION**
- Different batches (B124, B125) → New hybrid batch?
- Traceability complexity

---

#### **5. Batch-Linked Wastage History**

**Query Wastage by Batch:**
- Given batch number (e.g., B124)
- Show ALL wastage events:
  - Receiving damage/reject
  - Grading QC wastage
  - Packing overfill
  - Cold storage damage (if any)
  - Customer claims (if any)
- Total wastage % for batch
- Cost impact breakdown
- All photos

**Use Cases:**
- Customer complaint investigation
- Farm quality dispute
- Cost analysis per batch
- Process improvement

---

#### **6. Analytics & Reports**

**Wastage by Farm:**
- Which farms have highest damage/reject rates
- Trend over time
- Cost impact per farm
- Identify quality issues

**Wastage by Product:**
- Which items most problematic
- Stage where most wastage occurs
- Seasonal patterns

**Wastage by Stage:**
- Receiving, grading, packing, cold storage, customer
- Where are you losing most
- Cost breakdown by stage

**Wastage Trends:**
- Daily/weekly/monthly trends
- Compare periods
- Identify anomalies

**Cost Impact Reports:**
- Total wastage cost (by period)
- Farm responsibility vs our cost
- Impact on profitability
- Per-batch cost analysis

**Operator Performance:**
- Packing efficiency (overfill rates)
- Grading accuracy
- Receiving accuracy
- Identify training needs

---

#### **7. Threshold Alerts**

**Framework in Place, Configurable:**
- Set acceptable wastage % ranges by stage
- Alert if exceeded
- Example: "Receiving damage > 5% for Farm A"

**Alert Types:**
- Critical: Immediate action needed
- Warning: Review recommended
- Info: For awareness

**Alert Delivery:**
- In-app notification
- Email to relevant users
- Dashboard widget

**Threshold Configuration:**
- Admin-only
- Per stage, per farm, per product
- After data collection, refine thresholds

---

#### **8. Integration with All Modules**

**Modules That Log Wastage:**
- GRN Management (Module 1.2) - Receiving damage/reject
- Grading & Sorting (Module 1.3) - QC wastage
- Packing (Module 1.4) - Overfill
- Inventory (Module 2.1) - Cold storage damage
- B2B Tickets (Module 7.1) - Customer claims
- B2C Tickets (Module 7.2) - Customer claims

**Wastage Module Provides:**
- Centralized logging API
- Photo storage
- Cost allocation tracking
- Analytics and reporting
- Repacking workflow

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/wastage/log` - Log wastage event
- `/api/wastage/by-batch` - Get wastage for batch
- `/api/wastage/by-farm` - Farm performance
- `/api/wastage/by-stage` - Stage analysis
- `/api/wastage/cost-impact` - Cost reports
- `/api/wastage/repack` - Initiate repacking
- `/api/wastage/photos` - Upload photos
- `/api/wastage/alerts` - Threshold alerts

**Frontend (React):**
- `<WastageLogForm />` - Log wastage event
- `<PhotoUploadMultiple />` - Photo upload
- `<CostAllocationToggle />` - Farm/Us toggle
- `<WastageAnalytics />` - Analytics dashboard
- `<WastageTrends />` - Trend charts
- `<RepackingWorkflow />` - Repacking interface
- `<WastageAlerts />` - Alert management

**Database (Supabase):**
- `wastage_events` table:
  - event_id, batch_id, stage, type, quantity, cost_allocation
  - reason, user_id, timestamp, location
- `wastage_photos` table:
  - Links to Supabase Storage
- `wastage_repacking` table:
  - parent_batch, child_batch, reason, quantity, timestamp
- `wastage_thresholds` table:
  - stage, farm, product, threshold_percentage, alert_level

---

### **Dependencies**

**Required:**
- Batch Tracking (Module 2.2) - Batch numbers
- Supabase Storage - Photo uploads
- User Authentication

**Used By:**
- All modules that log wastage
- Reporting module
- Farm performance tracking
- Cost analysis

---

### **Validation Rules**

- Batch number must exist
- Quantity > 0
- Photos mandatory for all wastage events
- Cost allocation must be selected (Farm/Us)
- Repacking: Cannot repack already repacked batch
- Only one repack allowed per batch

---

### **Testing Checklist**

- [ ] Log wastage from all stages
- [ ] Upload multiple photos
- [ ] Test cost allocation toggle
- [ ] Query wastage by batch
- [ ] Generate farm performance report
- [ ] Wastage by stage analysis
- [ ] Repacking workflow (B###R creation)
- [ ] FIFO priority for repacked batches
- [ ] Threshold alerts trigger correctly
- [ ] Photo storage and retrieval
- [ ] Mobile photo upload (camera)
- [ ] Cost impact calculations accurate
- [ ] Analytics charts render correctly
- [ ] Same-batch consolidation
- [ ] Concurrent wastage logging

---

## **Parked for Future Discussion**

**Inventory Module Items:**
- Photo retention period policy
- Mixed batch repacking (different batches consolidated)
- Advanced demand forecasting
- Automated reorder triggers
- Integration with market procurement fast-track
- Quality hold workflow details
- Batch splitting scenarios
- Insurance claims for wastage
- Seasonal pricing adjustments

---

## **Success Criteria**

**Operational:**
- ✅ Real-time inventory visibility
- ✅ Complete batch traceability
- ✅ Comprehensive wastage documentation
- ✅ Efficient FIFO allocation
- ✅ Accurate stock availability checks

**Data Quality:**
- ✅ Every wastage event captured with photos
- ✅ Complete batch history from farm to customer
- ✅ Accurate cost allocation (farm vs us)

**Business Intelligence:**
- ✅ Identify high-wastage farms and products
- ✅ Optimize stock levels (reduce spoilage)
- ✅ Improve farm negotiations with data
- ✅ Track cost impact of wastage

---

**End of Module 2 Documentation**