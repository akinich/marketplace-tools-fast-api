# MODULE 1: INWARD OPERATIONS

**Document:** Step 4 - Module 1: Inward Operations  
**Filename:** 04-Module-01-Inward-Operations.md

---

## **Module Overview**

**Module Name:** Inward Operations  
**Module Type:** Parent Module  
**Child Modules:** 4 (PO Management, GRN Management, Grading & Sorting, Packing & Labeling)  
**Priority:** CRITICAL PATH - Core operational workflow

**Purpose:**  
Manage the complete inward flow from farm ordering to packed inventory, including batch tracking and wastage documentation.

---

## **Workflow Summary**

```
Farm Order → PO → GRN → Grading/Sorting → Packing → Inventory

Key Activities:
- Vendor pricing management
- Purchase order creation and tracking
- Goods receiving and quality control
- Batch number generation and tracking
- Wastage documentation at every stage
- Export to Zoho Books for farm billing
```

---

## **Internal Dashboard**

**Purpose:** Overview of all inward activities

**Key Metrics:**
- Active POs (by status)
- Pending GRNs (awaiting receiving)
- Today's receiving schedule
- Grading/packing queue
- Wastage alerts (threshold exceeded)
- Inward pipeline status

**Visualizations:**
- PO timeline (created → completed)
- Daily receiving volume
- Wastage by farm (last 30 days)
- Average receiving time
- Quality issues trend

**Quick Actions:**
- Create new PO
- View pending GRNs
- Generate receiving report
- Access wastage summary

---

## **CHILD MODULE 1.1: PURCHASE ORDER (PO) MANAGEMENT**

### **Overview**

**Purpose:** Create and manage purchase orders to farms/vendors with intelligent pricing

**Build Priority:** CRITICAL - Build in Phase 2 (Weeks 3-4)  
**Estimated Duration:** 7-10 days

---

### **Core Features**

#### **1. PO Creation**

**Input Fields:**
- Vendor/Farm (dropdown from Zoho vendor database)
- Expected Dispatch/Billing Date (date picker) - **Drives pricing**
- Expected Delivery Date (date picker) - Planning/logistics
- Items and quantities (multi-line entry)
- Notes/special instructions

**Auto-Population:**
- Item prices based on 3-tier logic:
  1. Vendor-specific price (if exists for dispatch date)
  2. Zoho default item price
  3. Manual entry
- Price source indicator: `[Vendor]` / `[Zoho]` / `[Manual]`
- Total calculation (auto-sum)

**Validation:**
- Delivery date cannot be before dispatch date
- Alert if gap > 2-3 days (unusual)
- Required fields enforcement

---

#### **2. Vendor-Specific Time-Based Pricing System**

**Database Structure:**
```
vendor_item_price_history:
- vendor_id (FK to Zoho vendors)
- item_id (FK to Zoho items)
- price (INR, decimal)
- effective_from (date)
- effective_to (date, nullable)
- created_by (admin user)
- created_at (timestamp)
- notes (text)
```

**Pricing Logic:**
```
Query: 
SELECT price 
FROM vendor_item_price_history
WHERE vendor_id = [selected_vendor]
  AND item_id = [selected_item]
  AND effective_from <= [dispatch_date]
  AND (effective_to >= [dispatch_date] OR effective_to IS NULL)
ORDER BY effective_from DESC
LIMIT 1
```

**Price Management Interface (Admin Only):**
- Add/edit vendor-item prices
- Set effective date ranges
- Schedule future price changes
- View price history
- Bulk price import (CSV)

**Scheduled Price Changes:**
- Set prices weeks/months in advance
- Auto-activation on effective date
- No manual intervention needed
- Example: Set on Dec 15 that Jan 1 price = ₹45

**Notifications:**
- Price change alerts (database update)
- Reminder 1 week before scheduled price takes effect
- Activation notification when scheduled price goes live

**Price Override:**
- Users can edit auto-populated price at PO creation
- System logs: original price, new price, user who changed
- Price source changes to `[Manual]`

---

#### **3. PO Status Workflow**

**Status Options:**
1. **Draft:** PO being created, not sent to farm
2. **Sent to Farm:** PO sent via email/WhatsApp
3. **GRN Generated:** Receiving sheet created, awaiting goods
4. **Completed:** GRN finalized, goods received
5. **Exported to Zoho:** Data exported for farm billing
6. **Closed:** PO fully processed and closed

**Status Transitions:**
```
Draft → Sent to Farm → GRN Generated → Completed → Exported to Zoho → Closed
```

**Status-Based Actions:**
- Draft: Edit, Delete, Send
- Sent to Farm: Generate GRN, Cancel
- GRN Generated: View GRN, Edit (if not received)
- Completed: Export to Zoho, View GRN
- Exported: View only (locked)
- Closed: View only (archived)

---

#### **4. Handling Extra Items from Farm**

**Scenario:** Farm sends items NOT on original PO

**Approach (Option A - Auto-Add):**
1. GRN captures extra items during data entry
2. System asks: "Add extra items to PO?"
3. If Yes → PO automatically updated with extra items
4. Extra items flagged: `[Added from GRN]`
5. PO export to Zoho includes extra items for accurate billing

**Benefits:**
- Single source of truth (PO reflects reality)
- Accurate farm billing
- Clean Zoho Books data

---

#### **5. PO Export to Zoho Books**

**Export Format:** CSV/Excel (Phase 1 - Manual upload)

**Data Included:**
- Vendor details (from Zoho vendor database)
- PO number, dates
- Items (from Zoho item database + any extra items)
- Quantities: Final Accepted (from GRN)
- Pricing
- Damage/Reject amounts (for debit note calculation)
- GRN number, Batch number
- Notes

**Mapping for Zoho:**
- PO → Bill in Zoho Books
- Damage/Reject (Farm responsibility) → Debit Note

**Export Process:**
1. Select completed POs
2. Click "Export to Zoho"
3. System generates formatted file
4. Download file
5. Manual upload to Zoho Books
6. Mark POs as "Exported to Zoho" (locked)

**Future (Phase 2):** Direct API integration

---

#### **6. PO Dashboard**

**List View:**
- All POs with key info (PO#, Farm, Date, Status, Total)
- Sortable columns
- Pagination

**Filters:**
- Status (multi-select)
- Farm/Vendor (dropdown)
- Date range (from-to)
- Item (search)

**Search:**
- By PO number
- By farm name
- By item name

**Bulk Actions:**
- Export selected POs
- Print multiple POs
- Email to farms (batch)

---

#### **7. Print & Email PO**

**Print Format:**
- PDF generation
- Professional template
- Company branding
- PO details, items, terms & conditions
- Signatures (digital)

**Email to Farm:**
- Auto-compose email
- Attach PO PDF
- Track sent status
- Email template (customizable)

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/po/create` - Create new PO
- `/api/po/{po_id}` - Get PO details
- `/api/po/{po_id}/update` - Update PO
- `/api/po/{po_id}/send` - Send to farm
- `/api/po/{po_id}/export-zoho` - Generate Zoho export
- `/api/po/list` - List POs with filters
- `/api/vendor-pricing/manage` - Price management (admin)

**Frontend (React):**
- `<POCreationForm />` - Create/edit PO
- `<POList />` - Dashboard list view
- `<PODetail />` - View single PO
- `<VendorPricingManager />` - Admin price management
- `<POExportModal />` - Zoho export interface

**Database (Supabase):**
- `purchase_orders` table
- `purchase_order_items` table
- `vendor_item_price_history` table
- `po_status_history` table (audit trail)

---

### **Dependencies**

**Required:**
- Vendor Database (Zoho) ✅
- Item Database (Zoho) ✅
- User Authentication ✅
- Batch Tracking Module (for reference)

**Integrates With:**
- GRN Management (Module 1.2) - PO → GRN generation
- Wastage Tracking (Module 2.3) - Receiving wastage from GRN

---

### **User Roles & Permissions**

**Admin:**
- Create/edit/delete POs
- Manage vendor-item pricing
- Export to Zoho
- View all POs

**User:**
- Create POs (may require approval)
- View assigned POs
- Send POs to farms
- Cannot manage pricing

---

### **Validation Rules**

- Vendor must be selected
- At least one item required
- Quantities > 0
- Dispatch date < Delivery date
- Prices must be > 0 (if entered)
- Cannot delete PO after GRN generated
- Cannot edit PO after exported to Zoho

---

### **Testing Checklist**

- [ ] Create PO with vendor-specific pricing
- [ ] Create PO with Zoho default pricing
- [ ] Create PO with manual pricing
- [ ] Schedule future price change and verify auto-activation
- [ ] Send PO to farm (email/print)
- [ ] Generate GRN from PO
- [ ] Handle extra items from farm
- [ ] Export to Zoho format
- [ ] Verify status workflow
- [ ] Test mobile responsiveness
- [ ] Multi-user concurrent PO creation
- [ ] Price override and audit logging

---

## **CHILD MODULE 1.2: GRN MANAGEMENT (Goods Receipt Note)**

### **Overview**

**Purpose:** Document actual goods received from farms, assign batch numbers, log wastage

**Build Priority:** CRITICAL - Build in Phase 2 (Weeks 4-5)  
**Estimated Duration:** 7-10 days

---

### **Core Features**

#### **1. GRN Generation from PO**

**Trigger:** A few hours before receiving

**Process:**
1. User selects PO
2. Click "Generate GRN"
3. System creates GRN:
   - GRN sequential number (GRN-001, GRN-002...)
   - Links to PO (parent-child relationship)
   - **Auto-generates unique Batch Number** (B001, B002...)
   - Pre-populates from PO: Farm, items, expected quantities, dates
   - Status: Draft

**GRN Numbering:**
- Separate sequence from PO
- Format: GRN-001, GRN-002, GRN-003...
- Always references parent PO number

---

#### **2. Batch Number Generation**

**Timing:** At GRN creation (before goods arrive)

**Format:**
- Sequential only: B001, B002, B003...
- No date encoding (security/opacity)
- Unique across all batches

**Purpose:**
- End-to-end traceability
- Links PO → GRN → Grading → Packing → SO → Customer
- Wastage tracking
- Quality issue investigation
- Customer complaint resolution

---

#### **3. Printable Blank GRN Template**

**Purpose:** On-site manual data capture

**Template Includes:**
- GRN number, PO number, Batch number (pre-filled)
- Farm details (pre-filled)
- Expected items and quantities (pre-filled)
- **Blank fields for manual entry:**
  - Transport method: ________
  - Number of boxes: ________
  - Time of receiving: ________
  - Actual items received: ☐ Item A  ☐ Item B  ☐ Item C
  - Actual quantities: ________
  - Damage quantity: ________
  - Reject quantity: ________
  - Final Accepted: ________
  - Receiver signature: ________

**Print Options:**
- PDF download
- Direct print
- Multiple copies

---

#### **4. GRN Data Entry Interface**

**After Manual Fill-Out, Enter into System:**

**Fields:**
- **Transport Method:** Dropdown (Truck, Tempo, Farm Vehicle, Other)
- **Number of Boxes:** Number input
- **Actual Receiving Time:** Time picker
- **Items Received:** 
  - Pre-populated from PO (checkboxes)
  - Can add extra items (not on PO)
- **Quantities:**
  - Gross Received: Number input
  - Damage: Number input + **Mandatory Photos** + **Cost Allocation Toggle** (Farm/Us)
  - Reject: Number input + **Mandatory Photos** + **Cost Allocation Toggle** (Farm/Us)
  - **Final Accepted:** Auto-calculated (Gross - Damage - Reject)
- **Receiver:** Dropdown (user who physically received)
- **Notes:** Text area

**Photo Upload:**
- Mandatory for Damage and Reject
- Multiple photos per category
- Stored in Supabase storage
- Linked to GRN and Batch number
- Timestamp and GPS coordinates (if available)

**Cost Allocation Toggle:**
- **Farm Responsibility:** Deducted from farm invoice
- **Our Responsibility:** Absorbed in our costs
- Checkbox: "Farm Responsible" (default: checked)
- Affects Zoho export and debit note generation

---

#### **5. GRN Editing**

**Edit Window:** Always editable until PO exported to Zoho

**After Zoho Export:** GRN locked (read-only)

**Edit Tracking:**
- Audit log of all changes
- Who edited, when, what changed
- Previous values stored

---

#### **6. Update PO with Actuals**

**When GRN Finalized:**
1. PO quantities updated to match GRN actuals
2. Extra items (not on PO) added to PO with flag `[Added from GRN]`
3. PO status changes to "Completed"
4. PO locked from further edits (unless GRN edited)

**Variance Tracking:**
- Expected (from PO) vs Actual (from GRN)
- Reason for variance (damage, reject, overage)

---

#### **7. Wastage Event Logging**

**Automatic Logging to Wastage Module:**

**For Damage:**
- Wastage type: "Receiving - Damage"
- Quantity
- Photos
- Cost allocation: Farm or Us
- Batch number
- GRN number, PO number
- Farm
- Date/time
- User who logged

**For Reject:**
- Wastage type: "Receiving - Reject"
- Same details as above

**Benefits:**
- Centralized wastage data
- Farm performance tracking
- Cost impact analysis
- Pattern identification

---

#### **8. Trigger Next Workflow**

**After GRN Completion:**
1. Batch moves to Grading & Sorting (Module 1.3)
2. **Does NOT push to inventory yet**
3. Status updates to "In Grading"
4. Notification to grading team

---

#### **9. GRN Dashboard**

**List View:**
- All GRNs with key info (GRN#, PO#, Batch#, Farm, Date, Status)
- Sortable, paginated

**Filters:**
- Status (Draft, Completed, Exported)
- Farm/Vendor
- Date range
- Batch number
- PO number

**Search:**
- By GRN number
- By PO number
- By Batch number
- By Farm name

**Quick Actions:**
- Print GRN
- View linked PO
- Edit (if not locked)
- View wastage events

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/grn/generate` - Create GRN from PO
- `/api/grn/{grn_id}` - Get GRN details
- `/api/grn/{grn_id}/update` - Update GRN data
- `/api/grn/{grn_id}/finalize` - Complete GRN
- `/api/grn/{grn_id}/print` - Generate printable template
- `/api/grn/list` - List GRNs with filters
- `/api/batch/generate` - Generate batch number

**Frontend (React):**
- `<GRNGenerationModal />` - Generate GRN from PO
- `<GRNDataEntryForm />` - Enter receiving data
- `<GRNList />` - Dashboard list view
- `<GRNDetail />` - View single GRN
- `<PhotoUpload />` - Upload damage/reject photos
- `<CostAllocationToggle />` - Farm/Us toggle

**Database (Supabase):**
- `grns` table
- `grn_items` table
- `batch_tracking` table
- `wastage_events` table (via Wastage Module)
- `grn_photos` table (or use Supabase Storage)

---

### **Dependencies**

**Required:**
- PO Management (Module 1.1) - Parent PO
- Batch Tracking (Module 2.2) - Batch number generation
- Wastage Tracking (Module 2.3) - Log wastage events
- Supabase Storage - Photo uploads

**Integrates With:**
- Grading & Sorting (Module 1.3) - Next stage
- PO Management - Updates PO with actuals

---

### **Validation Rules**

- Must be generated from valid PO
- Batch number must be unique
- Quantities: Gross >= Damage + Reject
- Final Accepted = Gross - Damage - Reject
- Photos mandatory if Damage > 0 or Reject > 0
- Cannot finalize without receiver selected
- Cannot edit after PO exported to Zoho

---

### **Testing Checklist**

- [ ] Generate GRN from PO
- [ ] Auto-generate batch number
- [ ] Print blank GRN template
- [ ] Enter data with photos
- [ ] Test cost allocation toggle (Farm/Us)
- [ ] Add extra items (not on PO)
- [ ] Finalize GRN and verify PO update
- [ ] Verify wastage events logged
- [ ] Edit GRN and track changes
- [ ] Lock GRN after Zoho export
- [ ] Test mobile responsiveness
- [ ] Photo upload and storage

---

## **CHILD MODULE 1.3: GRADING & SORTING**

### **Overview**

**Purpose:** Internal quality control and grading of received produce

**Build Priority:** CRITICAL - Build in Phase 2 (Week 5-6)  
**Estimated Duration:** 5-7 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

**Process Flow:**
1. Receive batch from GRN
2. Perform quality inspection
3. Grade products (A/B/C) where applicable
4. Log QC wastage (with photos)
5. Update batch status
6. Move to Packing

**Key Features:**
- Internal grading interface (A/B/C)
- Not all products require grading
- Grade affects farm billing, not customer pricing
- QC wastage tracking (mandatory photos)
- Batch number tracking throughout
- Link to Wastage Module

**Data Capture:**
- Batch number
- Item
- Quantity per grade (A, B, C)
- QC wastage (quantity, photos, reason)
- Grading staff
- Date/time

**To Be Discussed:**
- Detailed grading criteria per product
- Grading workflow (single pass vs multiple)
- Grade impact on farm billing calculation
- Regrading scenarios
- Quality hold/quarantine process
- Integration with farm performance tracking

---

## **CHILD MODULE 1.4: PACKING & LABELING**

### **Overview**

**Purpose:** Pack products into retail units and generate labels with batch numbers

**Build Priority:** CRITICAL - Build in Phase 2 (Week 6)  
**Estimated Duration:** 5-7 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

**Process Flow:**
1. Receive batch from Grading/Sorting
2. Pack into retail units (e.g., 10kg → 0.5kg bags)
3. Track overfill wastage
4. Generate labels with batch numbers
5. **Push to Inventory** (final step)

**Key Features:**
- Packing interface (specify pack sizes)
- Overfill wastage tracking (e.g., 19 bags instead of 20)
- Mandatory photos for wastage
- Label generation with batch numbers
- Label formats (sticker, A4, thermal)
- Batch printing
- Trigger inventory update

**Data Capture:**
- Batch number
- Source quantity and grade
- Pack size and quantity
- Expected packs vs actual packs
- Overfill wastage
- Photos
- Packing staff
- Date/time

**Label Content:**
- Product name
- Batch number
- Weight/quantity
- MRP (if required)
- Mfg date
- Best before date (if applicable)
- Company branding

**To Be Discussed:**
- Packing workflows for different products
- Label templates and printing methods
- Pack size configurations
- Barcode/QR code on labels
- Integration with inventory system (how stock moves)
- Handling partial packing (incomplete batches)
- Repacking from cold storage damage

---

## **Parked for Future Discussion**

**Inward Operations Items:**
- Market procurement fast-track workflow details
- Low stock alert triggers and notification logic
- Mixed batch repacking (different batches into new packs)
- Grading & Sorting detailed workflow
- Packing & Labeling detailed workflow
- Quality hold/quarantine processes
- Batch splitting scenarios
- Cross-contamination prevention

---

## **Success Criteria**

**Operational:**
- ✅ Complete inward traceability (farm to inventory)
- ✅ Accurate wastage documentation
- ✅ Efficient vendor pricing management
- ✅ Seamless Zoho Books integration
- ✅ Mobile-friendly for warehouse use

**Data Quality:**
- ✅ Every batch has complete history
- ✅ All wastage events captured with photos
- ✅ Accurate farm billing data

**User Experience:**
- ✅ Fast PO creation (< 2 minutes)
- ✅ Easy GRN data entry on mobile/tablet
- ✅ Quick photo uploads
- ✅ Real-time status visibility

---

**End of Module 1 Documentation**