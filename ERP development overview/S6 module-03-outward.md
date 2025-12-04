# MODULE 3: OUTWARD OPERATIONS

**Document:** Step 6 - Module 3: Outward Operations  
**Filename:** 06-Module-03-Outward-Operations.md

---

## **Module Overview**

**Module Name:** Outward Operations  
**Module Type:** Parent Module  
**Child Modules:** 4 (SO Management, Order Allocation, Invoice Management, Logistics & Routing)  
**Priority:** CRITICAL PATH - Customer-facing operations

**Purpose:**  
Manage the complete outward flow from customer orders to delivery, including FIFO batch allocation, invoicing, and route optimization.

---

## **Workflow Summary**

```
Customer Order → SO → Allocation (FIFO) → Invoice → Delivery

Key Activities:
- B2B and B2C order management
- Customer-specific pricing
- FIFO batch allocation (repacked priority)
- Inventory availability checks
- Invoice generation
- Route planning and optimization
- Delivery execution and proof of delivery
- Export to Zoho Books
```

---

## **Internal Dashboard**

**Purpose:** Overview of all outward activities

**Key Metrics:**
- Pending SOs (by status)
- Today's deliveries count
- Orders in allocation queue
- Delivery status summary (on-time, delayed, completed)
- Outstanding invoices (not yet delivered)
- Route optimization status
- Average fulfillment time
- Customer satisfaction score

**Visualizations:**
- SO pipeline (created → delivered)
- Daily order volume (B2B vs B2C)
- Delivery performance (on-time %)
- Top customers by value
- Route efficiency (km/delivery)
- Fulfillment time trend

**Quick Actions:**
- Create new SO
- View today's deliveries
- Allocate pending orders
- Generate delivery manifest
- Update delivery status

---

## **CHILD MODULE 3.1: SALES ORDER (SO) MANAGEMENT**

### **Overview**

**Purpose:** Create and manage sales orders for B2B and B2C customers

**Build Priority:** CRITICAL - Build in Phase 4 (Weeks 9-10)  
**Estimated Duration:** 5-7 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

#### **1. SO Creation**

**Order Sources:**
- B2B: WhatsApp, phone, email (manual entry by staff)
- B2C: WooCommerce (manual entry or future auto-import)

**Input Fields:**
- Customer (dropdown from Zoho customer database)
- Order date
- Expected delivery date
- Delivery address (pre-filled from customer, editable)
- Items and quantities (multi-line entry)
- Customer-specific pricing (auto-populated or manual)
- Special instructions
- Priority (normal, urgent)
- Order source (WhatsApp, phone, WooCommerce)

**Auto-Population:**
- Customer details from Zoho database
- Customer-specific pricing (if configured)
- Default delivery address
- Payment terms

---

#### **2. Customer-Specific Pricing**

**Pricing Tiers:**
- Different customers, different prices (B2B)
- Hotels may have negotiated rates
- Restaurants may have volume discounts
- B2C: Standard pricing (from WooCommerce or configured)

**Pricing Logic:**
1. Check customer-specific price (if exists)
2. Else use standard price (from Zoho or system)
3. Manual override allowed (with approval/audit)

**To Be Discussed:**
- How customer pricing is configured
- Time-based pricing (seasonal)
- Volume-based discounts
- Pricing approval workflow

---

#### **3. SO Status Workflow**

**Status Options:**
1. **Draft:** SO being created
2. **Pending Allocation:** Awaiting stock allocation
3. **Allocated:** Stock reserved, ready for picking
4. **Picking:** Being picked from warehouse
5. **Packed:** Ready for delivery
6. **Out for Delivery:** Assigned to route/vehicle
7. **Delivered:** Proof of delivery received
8. **Invoiced:** Invoice sent to customer
9. **Completed:** Payment received (tracked in Zoho)
10. **Cancelled:** Order cancelled

**Status Transitions:**
```
Draft → Pending Allocation → Allocated → Picking → Packed → Out for Delivery → Delivered → Invoiced → Completed
```

---

#### **4. SO Dashboard**

**List View:**
- All SOs with key info (SO#, Customer, Date, Status, Total)
- Sortable, paginated

**Filters:**
- Status (multi-select)
- Customer (dropdown)
- Date range (from-to)
- Delivery date
- Order source (B2B, B2C)
- Priority

**Search:**
- By SO number
- By customer name
- By item name

**Bulk Actions:**
- Allocate multiple SOs
- Generate picking list
- Print packing slips
- Export to Zoho

---

#### **5. Integration with Customer Database**

**Customer Data from Zoho:**
- Customer name, contact
- Delivery addresses
- Payment terms
- Pricing tier

**Extended in Marketplace Tools:**
- Customer preferences (packaging, delivery time)
- Special instructions (recurring)
- Blacklist batches/farms (if customer has issues)

---

#### **6. B2B vs B2C Distinction**

**B2B Orders:**
- Larger quantities
- Recurring orders (hotels/restaurants)
- Customer-specific pricing
- Flexible delivery times
- Credit payment terms

**B2C Orders:**
- Smaller quantities
- One-time or subscription
- Standard pricing
- Scheduled delivery slots
- Prepaid (usually)

**System Handles Both:**
- Same SO structure
- Differentiated by customer type
- Different workflows where needed

---

#### **7. SO to Invoice Conversion**

**Timing:** After SO is packed/delivered (based on configuration)

**Process:**
1. SO status: Delivered
2. System generates invoice
3. Invoice number (sequential or Zoho-linked)
4. Invoice goes out with delivery or emailed post-delivery
5. Export to Zoho Books for accounting

---

### **To Be Discussed**

- Recurring order automation (standing orders)
- Partial fulfillment scenarios (split delivery)
- Order modification after allocation
- Customer portal (self-service ordering)
- Integration with WooCommerce for auto-import
- Order approval workflow (for large orders)
- Credit limit checks
- Backorder handling
- Subscription orders from B2C module

---

## **CHILD MODULE 3.2: ORDER ALLOCATION (FIFO)**

### **Overview**

**Purpose:** Allocate inventory batches to sales orders using FIFO with repacked batch priority

**Build Priority:** CRITICAL - Build in Phase 4 (Weeks 10-11)  
**Estimated Duration:** 5-7 days

---

### **Core Features**

#### **1. FIFO Allocation with Priority**

**Priority Order:**
1. **Repacked Batches (B###R):** HIGHEST PRIORITY
   - Move out fastest to avoid further degradation
   - Always allocated first if available
2. **Oldest Regular Batches:** Standard FIFO
   - Based on packing date (entry to inventory)
3. **Newer Batches:** Last in queue

**Allocation Algorithm:**
```
For each SO line item:
1. Query available inventory for item
2. Filter by:
   - Status = Available (not already allocated)
   - Location = Packed Goods Warehouse
   - Grade (if customer specifies)
3. Sort by:
   - is_repacked DESC (repacked first)
   - packing_date ASC (oldest first)
4. Allocate batches until quantity fulfilled
5. Handle partial batch allocation if needed
6. Update inventory status: Available → Allocated
7. Link batches to SO
```

---

#### **2. Stock Availability Checks**

**Real-Time Check:**
- Current available stock (Packed Goods Warehouse)
- Already allocated stock (reserved for other SOs)
- Net available = Total - Allocated

**Incoming Stock Check:**
- Active POs with expected delivery dates
- Expected quantity and delivery date
- Can allocate against incoming if needed (with approval)

**Shortage Handling:**
1. Check current available stock
2. If insufficient, check incoming POs:
   - "50kg short, but 100kg arriving tomorrow from Farm A"
3. If still short, flag for market procurement:
   - "Still need 20kg, recommend market buy"
4. Alert user with shortage details and recommendations

---

#### **3. Allocation Interface**

**Manual Allocation:**
- User selects SO
- System suggests batches (FIFO with priority)
- User can:
  - Accept suggestions
  - Manually adjust batch selection
  - Reserve specific batches
  - Split batches (partial allocation)
- Confirm allocation
- System updates inventory and SO status

**Auto-Allocation (Future):**
- Trigger allocation automatically when SO created
- Apply FIFO logic
- Reserve batches
- Notify if shortages

---

#### **4. Partial Batch Allocation**

**Scenario:** SO needs 50kg, batch has 100kg

**Handling:**
- Allocate 50kg from batch to SO
- Remaining 50kg stays in inventory (available)
- Batch tracks partial allocation:
  - Original: 100kg
  - Allocated: 50kg to SO-123
  - Remaining: 50kg (available)

**Alternative:** Split batch into two records
- Batch B001a: 50kg → Allocated to SO-123
- Batch B001b: 50kg → Available

**To Be Discussed:** Which approach to use

---

#### **5. Grade-Specific Allocation**

**Customer Preferences:**
- Some customers want only Grade A
- Others accept Grade B at lower price
- System must filter available batches by grade

**Allocation Logic:**
```
If customer specifies grade:
  Filter batches WHERE grade = [customer_grade]
Else:
  Allocate any available grade (FIFO priority)
```

---

#### **6. Batch-to-SO Linking**

**Traceability:**
- Each SO stores which batches were allocated
- Each batch tracks which SOs it was allocated to
- Enable complete traceability:
  - Given SO → Show all batches
  - Given batch → Show all SOs
- Critical for customer complaints and recalls

**Data Structure:**
```
so_allocations table:
- so_id
- batch_id
- quantity_allocated
- allocation_date
- allocated_by (user)
```

---

#### **7. Allocation Exceptions**

**Customer Blacklist:**
- Customer X doesn't want produce from Farm Y
- System checks batch source farm
- Skips blacklisted batches

**Quality Hold:**
- Batches on quality hold cannot be allocated
- System filters out automatically

**Expiring Soon:**
- Flag batches expiring in < 2 days
- Allocate first (priority over FIFO)
- Alert user

---

#### **8. Allocation Reports**

**Picking List:**
- Generated after allocation
- Groups by location/batch
- For warehouse staff to pick items
- Includes: SO number, customer, item, quantity, batch number, location

**Allocation Summary:**
- Which batches allocated to which SOs
- Remaining inventory after allocation
- Shortage report (if any)

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/allocation/suggest` - Suggest batches (FIFO)
- `/api/allocation/allocate` - Confirm allocation
- `/api/allocation/by-so` - Get allocations for SO
- `/api/allocation/by-batch` - Get allocations for batch
- `/api/allocation/check-availability` - Stock check
- `/api/allocation/shortage-report` - Shortage details
- `/api/allocation/picking-list` - Generate picking list

**Frontend (React):**
- `<AllocationInterface />` - Manual allocation
- `<BatchSuggestions />` - FIFO suggestions
- `<StockAvailabilityCheck />` - Real-time stock check
- `<ShortageAlert />` - Shortage warnings
- `<PickingList />` - Print picking list

**Database (Supabase):**
- `so_allocations` table:
  - so_id, batch_id, quantity, allocation_date, user_id
- Update `inventory` table:
  - status: Available → Allocated
- Update `batches` table:
  - allocated_quantity (track partial allocations)

---

### **Dependencies**

**Required:**
- SO Management (Module 3.1) - SOs to allocate
- Inventory Management (Module 2.1) - Stock to allocate
- Batch Tracking (Module 2.2) - Batch numbers and history
- Customer Database (Zoho) - Customer preferences

**Integrates With:**
- Invoice Management (Module 3.3) - After allocation
- Logistics & Routing (Module 3.4) - Picking and delivery

---

### **Testing Checklist**

- [ ] FIFO allocation (verify repacked priority)
- [ ] Oldest batch allocated first (regular FIFO)
- [ ] Partial batch allocation
- [ ] Grade-specific allocation
- [ ] Stock availability check (current + incoming)
- [ ] Shortage detection and alerts
- [ ] Customer blacklist enforcement
- [ ] Quality hold filtering
- [ ] Batch-to-SO linking (traceability)
- [ ] Concurrent allocation (race conditions)
- [ ] Picking list generation
- [ ] Mobile responsiveness

---

## **CHILD MODULE 3.3: INVOICE MANAGEMENT**

### **Overview**

**Purpose:** Generate customer invoices from sales orders

**Build Priority:** CRITICAL - Build in Phase 4 (Weeks 11-12)  
**Estimated Duration:** 5-7 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

#### **1. Invoice Generation**

**Trigger:**
- Manual: User clicks "Generate Invoice" on SO
- Auto: When SO status changes to "Delivered" (configurable)

**Invoice Data:**
- Invoice number (sequential)
- Customer details (from Zoho customer database)
- SO number (reference)
- Date of invoice
- Items (from SO with actual delivered quantities)
- Pricing (from SO)
- Taxes (GST based on HSN codes)
- Total amount
- Payment terms
- Batch numbers (for traceability)

---

#### **2. Invoice Numbering**

**Format:**
- Sequential: INV-001, INV-002, INV-003
- Or linked to Zoho Books invoice numbers (if synced)

**To Be Discussed:**
- Numbering scheme (per month, per year, global)
- Prefix/suffix options
- Integration with Zoho numbering

---

#### **3. Invoice Status**

**Status Options:**
- Draft (being created)
- Sent (emailed/delivered to customer)
- Paid (payment received - tracked in Zoho)
- Overdue (past payment terms)
- Cancelled

---

#### **4. Invoice Export to Zoho Books**

**Export Format:** CSV/Excel (Phase 1 - Manual upload)

**Data Included:**
- Customer details (from Zoho)
- Invoice number, date
- SO reference
- Items (from Zoho item database)
- Quantities (actual delivered)
- Pricing
- Taxes (calculated)
- Payment terms
- Batch numbers (for reference)
- Delivery date

**Mapping for Zoho:**
- Marketplace Tools invoice → Zoho Books invoice
- Customer ID mapping
- Item ID mapping
- Tax rate mapping (based on HSN)

**Export Process:**
1. Select completed/delivered SOs
2. Generate invoices in Marketplace Tools
3. Click "Export to Zoho"
4. System generates formatted file
5. Download file
6. Manual upload to Zoho Books
7. Mark invoices as "Exported to Zoho" (locked)

**Future (Phase 2):** Direct API integration

---

#### **5. Invoice Templates**

**Print/Email Format:**
- PDF generation
- Professional template
- Company branding
- Customer details
- Line items with batch numbers
- Taxes breakdown
- Payment terms
- Bank details
- Authorized signatory

**Multiple Templates:**
- B2B format (detailed)
- B2C format (simplified)
- Tax invoice vs proforma

---

#### **6. Invoice Dashboard**

**List View:**
- All invoices with key info (Invoice#, Customer, SO#, Date, Status, Amount)
- Sortable, paginated

**Filters:**
- Status (multi-select)
- Customer (dropdown)
- Date range (invoice date, due date)
- Payment status (paid, unpaid, overdue)

**Search:**
- By invoice number
- By SO number
- By customer name

**Bulk Actions:**
- Export multiple invoices to Zoho
- Email invoices to customers
- Print invoices (batch)
- Mark as paid (if payment received)

---

#### **7. Tax Calculation**

**GST Handling:**
- Item-wise HSN codes (from Item Database)
- Tax rate based on HSN (5%, 12%, 18%, etc.)
- CGST + SGST (intra-state) or IGST (inter-state)
- Tax summary on invoice

**Customer-Specific Tax:**
- Some customers tax-exempt
- Handle reverse charge (if applicable)

**To Be Discussed:**
- Tax configuration per item/customer
- Multi-state tax logic
- Tax reports for filing

---

### **To Be Discussed**

- Credit notes for returns/damages
- Partial payment tracking
- Payment reminders (automated)
- Invoice modification after sent
- Proforma invoice generation
- Recurring invoice (subscription orders)
- Multi-currency (if international customers)
- Invoice discounts/promotions
- Payment gateway integration (for B2C)

---

## **CHILD MODULE 3.4: LOGISTICS & ROUTING**

### **Overview**

**Purpose:** Plan delivery routes, assign vehicles/drivers, track deliveries, capture proof of delivery

**Build Priority:** CRITICAL - Build in Phase 4 (Weeks 12-13)  
**Estimated Duration:** 7-10 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

#### **1. Separate but Connected Flow**

**Not Inline with SO/Invoice:**
- Logistics is a distinct module
- Multiple SOs grouped into one delivery route
- Route-based operations, not order-based

**Integration Points:**
- Pulls SOs that are "Ready for Delivery"
- Updates SO/Invoice status when delivered
- Links proof of delivery to SOs

---

#### **2. Route Planning**

**Grouping SOs:**
- By delivery date (today, tomorrow)
- By delivery area/location (geographic clustering)
- By vehicle capacity (weight/volume)
- By customer type (B2B vs B2C)

**Manual Route Creation:**
- User selects SOs
- Groups into routes
- Assigns vehicle and driver
- Optimizes route order (future: auto-optimize)

**Auto-Route Suggestions (Future):**
- AI/algorithm-based route optimization
- Minimize distance and time
- Consider traffic patterns
- Balance vehicle load

---

#### **3. Route Optimization**

**Optimization Goals:**
- Minimize total distance
- Minimize delivery time
- Balance load across vehicles
- Respect delivery time windows
- Avoid traffic congestion

**Optimization Algorithms (Future):**
- Traveling Salesman Problem (TSP)
- Vehicle Routing Problem (VRP)
- Integration with Google Maps API or similar

**Phase 1:** Manual route planning with map view

---

#### **4. Vehicle & Driver Assignment**

**Vehicle Management:**
- Vehicle list (in-house fleet)
- Vehicle capacity (weight, volume)
- Vehicle status (available, on-route, maintenance)
- Fuel tracking (future)

**Driver Management:**
- Driver list
- Driver availability
- Driver assignments
- Performance tracking

**Assignment:**
- Assign vehicle + driver to route
- Route capacity check
- Driver shift timing

**Third-Party Couriers:**
- For B2C orders
- Courier partner selection
- Tracking number integration
- Delivery status updates from courier API (future)

---

#### **5. Delivery Execution**

**Delivery Manifest:**
- Print manifest for driver
- All SOs on route
- Customer names, addresses, contact
- Items and quantities per SO
- Special instructions
- Route map (future: GPS navigation)

**Driver App (Future):**
- Mobile app for drivers
- Show route and SOs
- Real-time navigation
- Capture proof of delivery
- Update status on-the-go

**Phase 1:** Paper manifest, manual status updates

---

#### **6. Proof of Delivery (POD)**

**Capture:**
- Customer signature (digital or paper)
- Photo of delivered goods
- Date and time of delivery
- GPS coordinates (if available)
- Receiver name
- Any issues noted (damage, shortage)

**Upload to System:**
- After delivery, upload POD
- Link to SO and Invoice
- Trigger status update: Delivered

---

#### **7. Status Updates to SO/Invoice**

**When Delivery Confirmed:**
1. Route status: In Progress → Completed
2. SO status: Out for Delivery → Delivered
3. Invoice status: Sent → Delivered (ready for payment)
4. Inventory status: In-Transit → Delivered (removed from inventory)
5. Batch tracking: Delivered (add to batch history)

---

#### **8. Delivery Performance Tracking**

**Metrics:**
- On-time delivery % (vs scheduled)
- Average delivery time
- Distance per delivery
- Fuel efficiency (future)
- Customer feedback (from tickets)
- Driver performance

**Reports:**
- Daily delivery summary
- Route efficiency analysis
- Delayed deliveries (with reasons)
- Cost per delivery

---

#### **9. Monday to Saturday Operations**

**Operational Days:**
- Deliveries Monday to Saturday
- No Sunday deliveries (unless special)

**Scheduling:**
- Plan today's deliveries in morning
- Assign routes and drivers
- Execute deliveries during day
- Update status by evening

---

#### **10. Logistics Dashboard**

**Overview:**
- Today's routes (count, status)
- Vehicles out (count)
- Deliveries completed / pending
- On-time performance
- Alerts (delayed, issues)

**Map View (Future):**
- Real-time vehicle tracking
- Route visualization
- Customer locations
- Live traffic updates

---

### **To Be Discussed**

- GPS tracking of vehicles (real-time)
- Driver mobile app requirements
- Integration with third-party courier APIs
- Route optimization algorithm details
- Vehicle maintenance tracking
- Fuel cost tracking
- Delivery time slot management (B2C)
- Customer notification (SMS/email before delivery)
- Failed delivery handling (customer not home)
- Return logistics (product returns)
- Cold chain monitoring (temperature tracking)
- Delivery scheduling (calendar integration)

---

## **Parked for Future Discussion**

**Outward Operations Items:**
- Detailed SO workflow (creation, modification, approval)
- Customer-specific pricing configuration
- Recurring/standing orders automation
- Partial fulfillment and split deliveries
- Credit limit and payment term enforcement
- Backorder management
- Invoice modification and credit notes
- Tax configuration and multi-state handling
- Route optimization algorithm selection
- Driver mobile app feature set
- Third-party courier integration
- Real-time vehicle tracking
- Delivery time slot management
- Customer self-service portal

---

## **Success Criteria**

**Operational:**
- ✅ Efficient order fulfillment (SO → Delivery)
- ✅ Accurate FIFO allocation (oldest out first)
- ✅ On-time delivery performance
- ✅ Complete delivery traceability
- ✅ Seamless Zoho Books integration

**Customer Satisfaction:**
- ✅ Correct orders (right items, quantities)
- ✅ On-time deliveries
- ✅ Quality products (proper batch selection)
- ✅ Professional invoicing
- ✅ Quick issue resolution (tickets)

**Business Intelligence:**
- ✅ Customer ordering patterns
- ✅ Delivery performance metrics
- ✅ Route efficiency analysis
- ✅ Fulfillment cost tracking

---

**End of Module 3 Documentation**