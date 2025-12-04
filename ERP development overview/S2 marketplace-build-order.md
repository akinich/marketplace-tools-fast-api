# MARKETPLACE TOOLS - DEVELOPMENT SEQUENCE & BUILD ORDER

**Document:** Step 2 - Development Sequence & Build Order  
**Filename:** 02-Development-Sequence.md

---

## **Current Status**

### **✅ COMPLETED:**
- Database Management (Module 6) - All 4 databases ready
  - 6.1 Item Database (Zoho) ✅
  - 6.2 Customer Database (Zoho) ✅
  - 6.3 Vendor Database (Zoho) ✅
  - 6.4 Item Database (WooCommerce) ✅

- B2C Operations (Module 4) - Migrated from Streamlit ✅
  - 4.1 Order Extractor ✅
  - 4.2 Shipping Label Generator ✅
  - 4.3 MRP Label Generator ✅

- B2C Management (Module 5) - Partially complete
  - 5.1 Website Inventory Update ✅
  - 5.2 Woo to Zoho Export ✅
  - 5.3 B2C Subscription Management ⏳ (To be built)

---

## **BUILD PHILOSOPHY**

**Approach:** Sequential dependency-based development

**Goal:** Complete inward + outward flow before go-live

**Strategy:** Build foundation modules first, then layer operational modules on top

---

## **RECOMMENDED BUILD SEQUENCE**

### **PHASE 1: FOUNDATION MODULES (Weeks 1-2)**

#### **1.1 Batch Tracking Module (Module 2.2)**
**Duration:** 3-4 days  
**Priority:** Build FIRST  
**Dependencies:** None  

**Why First:**
- Simple, standalone module
- Creates batch numbering system
- Everything else depends on this
- PO, GRN, Inventory, SO all need batch numbers

**Deliverables:**
- Sequential batch number generation (B001, B002...)
- Batch audit trail database structure
- Batch query/search functionality
- Historical archive system

---

#### **1.2 Wastage Tracking Module (Module 2.3)**
**Duration:** 5-7 days  
**Priority:** Build SECOND  
**Dependencies:** Batch Tracking  

**Why Second:**
- Centralized wastage database
- All other modules will log wastage here
- Foundation for cost tracking

**Deliverables:**
- Wastage event logging system
- Photo upload and storage (Supabase)
- Cost allocation tracking (Farm/Us toggle)
- Wastage categories setup
- Analytics framework
- Repacking workflow (B###R numbering)

---

### **PHASE 2: INWARD FLOW (Weeks 3-6)**

#### **2.1 Purchase Order (PO) Management (Module 1.1)**
**Duration:** 7-10 days  
**Priority:** CRITICAL PATH  
**Dependencies:** Vendor DB, Item DB, Batch Tracking, Wastage Tracking  

**Why Now:**
- Entry point of entire inward flow
- Vendor-specific pricing is complex but foundational
- Immediate business value

**Deliverables:**
- PO creation interface
- Vendor-specific time-based pricing system
- Date handling (dispatch/billing vs delivery)
- PO status workflow
- Extra items handling
- Print/email PO to farms
- Export to Zoho format (CSV/Excel)
- PO dashboard with filters

**Key Features to Build:**
- 3-tier pricing logic (vendor-specific → Zoho default → manual)
- Scheduled price changes with auto-activation
- Price history tracking
- Admin-only price management interface

---

#### **2.2 GRN Management (Module 1.2)**
**Duration:** 7-10 days  
**Priority:** CRITICAL PATH  
**Dependencies:** PO, Batch Tracking, Wastage Tracking  

**Why Now:**
- Directly follows PO in workflow
- Creates batch numbers for traceability
- Logs first wastage events

**Deliverables:**
- GRN generation from PO
- Separate GRN numbering (GRN-001, GRN-002...)
- Batch number auto-generation at GRN creation
- Printable blank GRN template
- Data entry interface (transport, boxes, time, quantities)
- Photo upload for damage/reject (mandatory)
- Cost allocation toggle (Farm/Us)
- Update PO with actuals
- Log wastage events
- GRN dashboard
- Editable until Zoho export

---

#### **2.3 Grading & Sorting Module (Module 1.3)**
**Duration:** 5-7 days  
**Priority:** CRITICAL PATH  
**Dependencies:** GRN, Batch Tracking, Wastage Tracking  

**Why Now:**
- Sequential step after GRN
- Must be detailed before building

**Deliverables:**
- *To be detailed - workflow discussion needed*
- Internal grading interface (A/B/C)
- QC wastage logging (mandatory photos)
- Batch number tracking
- Grade impact on farm billing

---

#### **2.4 Packing & Labeling Module (Module 1.4)**
**Duration:** 5-7 days  
**Priority:** CRITICAL PATH  
**Dependencies:** Grading, Batch Tracking, Wastage Tracking  

**Why Now:**
- Final inward step before inventory
- Triggers inventory update

**Deliverables:**
- *To be detailed - workflow discussion needed*
- Packing interface
- Overfill wastage tracking (mandatory photos)
- Label generation with batch numbers
- Push to inventory trigger

---

### **PHASE 3: INVENTORY (Weeks 7-8)**

#### **3.1 Inventory Management (Module 2.1)**
**Duration:** 7-10 days  
**Priority:** CRITICAL PATH  
**Dependencies:** Packing, Batch Tracking  

**Why Now:**
- Sits between inward and outward
- Receives stock from packing
- Provides stock for allocation

**Deliverables:**
- Multi-location inventory tracking
- Stock level dashboard
- Batch-wise inventory view
- FIFO allocation logic (with repacked batch priority)
- Stock availability checks (current + incoming)
- Reorder level alerts
- Shelf life management
- Inventory movement tracking

---

### **PHASE 4: OUTWARD FLOW (Weeks 9-12)**

#### **4.1 Sales Order (SO) Management (Module 3.1)**
**Duration:** 5-7 days  
**Priority:** CRITICAL PATH  
**Dependencies:** Customer DB, Item DB, Inventory  

**Why Now:**
- Entry point of outward flow
- Must be detailed before building

**Deliverables:**
- *To be detailed - workflow discussion needed*
- SO creation interface
- Customer-specific pricing
- SO status tracking
- Link to customer database

---

#### **4.2 Order Allocation (FIFO) (Module 3.2)**
**Duration:** 5-7 days  
**Priority:** CRITICAL PATH  
**Dependencies:** SO, Inventory, Batch Tracking  

**Why Now:**
- Links SO to inventory
- Core allocation logic

**Deliverables:**
- FIFO allocation with priority:
  1. Repacked batches (B###R)
  2. Oldest regular batches
  3. Newer batches
- Stock availability checks
- Shortage handling workflow
- Batch-to-SO linking

---

#### **4.3 Invoice Management (Module 3.3)**
**Duration:** 5-7 days  
**Priority:** CRITICAL PATH  
**Dependencies:** SO, Allocation  

**Why Now:**
- Follows allocation
- Must be detailed before building

**Deliverables:**
- *To be detailed - workflow discussion needed*
- Convert SO to Invoice
- Invoice generation
- Export to Zoho format

---

#### **4.4 Logistics & Routing (Module 3.4)**
**Duration:** 7-10 days  
**Priority:** CRITICAL PATH  
**Dependencies:** SO, Invoice  

**Why Now:**
- Final outward step
- Must be detailed before building

**Deliverables:**
- *To be detailed - workflow discussion needed*
- Group SOs by delivery date/area
- Route optimization
- Vehicle/driver assignment
- Delivery execution tracking
- Proof of delivery
- Status updates to SO/Invoice

---

### **PHASE 5: REMAINING B2C (Week 13)**

#### **5.1 B2C Subscription Management (Module 5.3)**
**Duration:** 5-7 days  
**Priority:** MEDIUM  
**Dependencies:** WooCommerce integration  

**Why Now:**
- Last B2C module to build
- Not blocking core flow

**Deliverables:**
- Subscription order builder
- Recurring order tracking
- Documentation generation
- Push to WooCommerce
- Transaction history

---

### **PHASE 6: DASHBOARDS & REPORTS (Weeks 14-15)**

#### **6.1 Individual Module Dashboards**
**Duration:** 5-7 days  
**Priority:** MEDIUM  
**Dependencies:** All operational modules  

**Why Now:**
- All modules operational
- Can aggregate data

**Deliverables:**
- Inward Operations dashboard
- Inventory dashboard
- Outward Operations dashboard
- B2C Ops dashboard
- B2C Management dashboard
- Ticket Management dashboard

---

#### **6.2 Reporting Module (Module 8.1)**
**Duration:** 7-10 days  
**Priority:** MEDIUM  
**Dependencies:** All operational modules  

**Why Now:**
- Cross-module reporting
- Business intelligence

**Deliverables:**
- Purchase analysis reports
- Wastage reports
- Inventory reports
- Sales reports
- Operational reports
- Financial reports (Zoho export)
- Batch traceability reports
- Logistics reports

---

### **PHASE 7: TICKETS (Weeks 16-17)**

#### **7.1 B2B Tickets (Module 7.1)**
**Duration:** 3-5 days  
**Priority:** LOW  
**Dependencies:** SO, Invoice  

**Why Now:**
- Post-sale support
- Not blocking core operations

**Deliverables:**
- *To be detailed - workflow discussion needed*
- B2B ticket creation
- Link to SO/Invoice
- Issue tracking

---

#### **7.2 B2C Tickets (Module 7.2)**
**Duration:** 3-5 days  
**Priority:** LOW  
**Dependencies:** WooCommerce orders  

**Why Now:**
- Post-sale support
- Not blocking core operations

**Deliverables:**
- B2C ticket creation
- Mandatory photos for damage claims
- Customer claim window tracking
- Late ticket flagging
- Link to WooCommerce orders

---

## **CRITICAL PATH DEPENDENCIES**

```
FOUNDATION:
Batch Tracking (Week 1)
    ↓
Wastage Tracking (Week 1-2)
    ↓

INWARD FLOW:
PO (Week 3-4) → GRN (Week 4-5) → Grading (Week 5-6) → Packing (Week 6) → INVENTORY (Week 7-8)
    ↑                                                                             ↓
Vendor DB                                                                         ↓
Item DB                                                                           ↓
                                                                                  ↓
OUTWARD FLOW:                                                                     ↓
Customer DB → SO (Week 9-10) → Allocation (Week 10-11) ←────────────────────────┘
                    ↓                   ↓
                Invoice (Week 11-12) → Logistics (Week 12-13)
```

---

## **MODULES REQUIRING DETAILED DISCUSSION BEFORE BUILD**

These modules need workflow and feature discussions before development:

1. **Grading & Sorting (Module 1.3)** - Week 5
2. **Packing & Labeling (Module 1.4)** - Week 6
3. **Sales Order Management (Module 3.1)** - Week 9
4. **Invoice Management (Module 3.3)** - Week 11
5. **Logistics & Routing (Module 3.4)** - Week 12

**Action Required:** Schedule detailed sessions for each before their build week

---

## **ESTIMATED TOTAL TIMELINE**

**Phase 1 (Foundation):** 2 weeks  
**Phase 2 (Inward):** 4 weeks  
**Phase 3 (Inventory):** 2 weeks  
**Phase 4 (Outward):** 4 weeks  
**Phase 5 (B2C):** 1 week  
**Phase 6 (Dashboards/Reports):** 2 weeks  
**Phase 7 (Tickets):** 2 weeks  

**Total Build Time:** ~17 weeks (4+ months)

**Plus:**
- Testing & Bug Fixes: 2-3 weeks
- User Training: 1 week
- Go-Live Preparation: 1 week

**Total Project Timeline:** ~20-22 weeks (5-6 months)

---

## **TESTING STRATEGY**

**Continuous Testing:**
- Test each module as built
- Integration testing at phase boundaries
- End-to-end testing after Phase 4 complete

**Key Test Scenarios:**
1. Complete inward flow (Farm order → Inventory)
2. Complete outward flow (Customer order → Delivery)
3. Batch traceability (Track one batch farm to customer)
4. Wastage tracking across all stages
5. Zoho export accuracy (PO and SO)
6. Multi-user concurrent operations
7. Photo upload and storage
8. Mobile responsiveness

---

## **RISK MITIGATION**

**Critical Dependencies:**
- Zoho Books sync must be tested early
- WooCommerce API stability
- Supabase storage for photos (test at scale)
- FIFO allocation logic (complex, needs thorough testing)

**Contingency Plans:**
- Buffer time built into estimates
- Parallel development where possible
- Early prototype of complex modules (pricing, allocation)

---

## **SUCCESS CRITERIA**

**Before Go-Live:**
- ✅ All critical path modules functional
- ✅ End-to-end testing complete
- ✅ Zoho export/import validated
- ✅ User training completed
- ✅ Data migration plan ready
- ✅ Backup and rollback plan in place

---

## **NEXT IMMEDIATE STEPS**

1. **Detail Grading & Sorting workflow** (Before Week 5)
2. **Detail Packing & Labeling workflow** (Before Week 6)
3. **Detail SO Management workflow** (Before Week 9)
4. **Detail Invoice Management workflow** (Before Week 11)
5. **Detail Logistics & Routing workflow** (Before Week 12)

6. **Start Building:**
   - Week 1: Batch Tracking Module
   - Week 1-2: Wastage Tracking Module
   - Week 3-4: PO Management Module