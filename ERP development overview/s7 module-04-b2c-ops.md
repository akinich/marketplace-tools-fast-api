# MODULE 4: B2C OPS

**Document:** Step 7 - Module 4: B2C Ops  
**Filename:** 07-Module-04-B2C-Ops.md

---

## **Module Overview**

**Module Name:** B2C Ops (B2C Operations)  
**Module Type:** Parent Module  
**Child Modules:** 3 (Order Extractor, Shipping Label Generator, MRP Label Generator)  
**Priority:** MEDIUM - Standalone suite, already migrated

**Purpose:**  
Process WooCommerce orders from extraction to label generation for shipping and product identification.

---

## **Module Characteristics**

**Current Status:**
- ✅ **ALL 3 MODULES MIGRATED** from Python/Streamlit to FastAPI + React
- ✅ Functional and operational
- ⚠️ Independent of core farm-to-fork modules (no integration yet)
- 🔄 Future: Integrate with Inventory, SO, Batch Tracking

**Migration Notes:**
- Existing business logic preserved
- UI converted from Streamlit to React
- Backend converted to FastAPI endpoints
- Database migrated to Supabase
- Same workflows maintained

**Standalone Operation:**
- Does NOT use core inventory
- Does NOT create SOs in main system
- Does NOT track batches (yet)
- Shares only framework, authentication, database infrastructure

**Future Integration Plans:**
- WooCommerce orders → Auto-create SOs in Module 3.1
- Allocate from main inventory (Module 2.1)
- Track batches for B2C orders (Module 2.2)
- Link to B2C tickets (Module 7.2)
- Timeline: Phase 3 (Months 12-18)

---

## **Internal Dashboard**

**Purpose:** Overview of B2C order processing

**Key Metrics:**
- Orders extracted today
- Pending shipping labels
- Pending MRP labels
- Last extraction date/time
- Orders processed this week
- Label generation queue

**Quick Actions:**
- Extract new orders
- Generate shipping labels
- Generate MRP labels
- Download generated files

---

## **CHILD MODULE 4.1: ORDER EXTRACTOR (WooCommerce)**

### **Overview**

**Purpose:** Extract orders from WooCommerce for processing

**Status:** ✅ **MIGRATED AND OPERATIONAL**  
**Migration Source:** Python/Streamlit tool

---

### **Core Features**

#### **1. WooCommerce API Integration**

**Connection:**
- WooCommerce REST API
- API credentials configured in settings
- Secure authentication (OAuth or API keys)
- Connection test functionality

**API Endpoints Used:**
- `/wp-json/wc/v3/orders` - List orders
- Query parameters: date range, status, per_page, page

---

#### **2. Date Range Selection**

**User Input:**
- From Date (date picker)
- To Date (date picker)
- Default: Today's orders

**Validation:**
- To Date >= From Date
- Maximum range: 30 days (configurable)

---

#### **3. Order Data Extraction**

**Data Fetched per Order:**
- Order number (WooCommerce order ID)
- Order date
- Order status (processing, completed, etc.)
- Customer details:
  - Name (first, last)
  - Email
  - Phone
  - Billing address
  - Shipping address
- Line items:
  - Product name
  - SKU
  - Quantity
  - Price (unit and total)
  - Variations (if applicable)
- Order totals:
  - Subtotal
  - Shipping charges
  - Taxes
  - Discounts/coupons
  - Total amount
- Payment method
- Payment status (paid, pending, COD)
- Shipping method
- Order notes (customer and internal)

---

#### **4. Excel File Generation**

**Output Format:** Excel (.xlsx)

**File Structure:**
- One row per order line item (not per order)
- Columns:
  - Order Number
  - Order Date
  - Customer Name
  - Customer Email
  - Customer Phone
  - Shipping Address (line 1, line 2, city, state, pincode)
  - Product Name
  - SKU
  - Quantity
  - Unit Price
  - Total Price
  - Payment Method
  - Payment Status
  - Shipping Method
  - Special Instructions

**File Naming:**
- Format: `WooOrders_YYYYMMDD_YYYYMMDD.xlsx`
- Example: `WooOrders_20241201_20241205.xlsx`

---

#### **5. Order Status Filtering**

**Filter Options:**
- Processing (default)
- Completed
- On-hold
- Pending payment
- All statuses

**Default:** Processing (orders ready to fulfill)

---

#### **6. Extraction Log**

**Track Extractions:**
- Date/time of extraction
- Date range extracted
- Number of orders extracted
- User who extracted
- Status (success, failed)
- Error messages (if any)

**Benefits:**
- Audit trail
- Prevent duplicate processing
- Troubleshooting

---

#### **7. Error Handling**

**API Connection Errors:**
- Invalid credentials
- API rate limits
- Network timeout
- Server errors

**User Feedback:**
- Clear error messages
- Retry suggestions
- Log errors for admin review

---

### **User Interface (React)**

**Components:**
- `<OrderExtractor />` - Main interface
- `<DateRangePicker />` - Select date range
- `<StatusFilter />` - Order status selection
- `<ExtractButton />` - Trigger extraction
- `<ProgressIndicator />` - Show extraction progress
- `<DownloadLink />` - Download generated Excel
- `<ExtractionHistory />` - Past extractions log

**Workflow:**
1. User opens Order Extractor
2. Selects date range (from, to)
3. (Optional) Filters by order status
4. Clicks "Extract Orders"
5. System connects to WooCommerce API
6. Fetches orders
7. Generates Excel file
8. User downloads file
9. Extraction logged

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/b2c/orders/extract` - Trigger extraction
- `/api/b2c/orders/download/{file_id}` - Download Excel
- `/api/b2c/orders/extraction-log` - View history
- `/api/b2c/woocommerce/test-connection` - Test API

**WooCommerce Integration:**
- Python library: `woocommerce` (WooCommerce REST API wrapper)
- Excel generation: `openpyxl` or `pandas`

**Database (Supabase):**
- `woo_extraction_log` table:
  - extraction_id, date_from, date_to, order_count, status, user_id, timestamp

---

### **Automation (Future - Phase 2)**

**Scheduled Extraction:**
- Run daily at specific time (e.g., 8 AM)
- Extract previous day's orders
- Auto-generate Excel
- Email to fulfillment team

**Webhook Integration:**
- WooCommerce sends webhook on new order
- System triggers extraction
- Near-real-time order processing

---

### **Testing Checklist**

- [x] Connect to WooCommerce API
- [x] Extract orders by date range
- [x] Generate Excel with correct data
- [x] Download Excel file
- [x] Log extraction history
- [x] Handle API errors gracefully
- [x] Test with large order volume (100+ orders)
- [x] Mobile responsiveness

---

## **CHILD MODULE 4.2: SHIPPING LABEL GENERATOR**

### **Overview**

**Purpose:** Generate shipping labels for courier dispatch

**Status:** ✅ **MIGRATED AND OPERATIONAL**  
**Migration Source:** Python/Streamlit tool

---

### **Core Features**

#### **1. Input: Excel File from Order Extractor**

**Process:**
1. User uploads Excel file (from Module 4.1)
2. System parses file
3. Extracts shipping data per order

**Expected Columns:**
- Order Number
- Customer Name
- Shipping Address (full)
- Phone Number
- Pincode

---

#### **2. Label Template**

**Label Format:**
- Customer name (bold, large font)
- Full shipping address (multi-line)
- Pincode (highlighted)
- Phone number
- Order number (for reference)
- Company branding (optional)

**Label Size:**
- Standard thermal printer format (100mm x 150mm)
- Or A4 sticker sheets (configurable)

**Template Customization:**
- Admin can modify template
- Font sizes, logo placement
- Additional fields (if needed)

---

#### **3. Batch Label Generation**

**Process:**
1. Parse Excel (all orders)
2. Generate one label per order
3. Compile into single PDF
4. Paginate appropriately (labels per page)

**Output:** PDF file with all shipping labels

**File Naming:**
- Format: `ShippingLabels_YYYYMMDD.pdf`
- Example: `ShippingLabels_20241205.pdf`

---

#### **4. Courier Integration (Current: Manual)**

**Phase 1 (Current):**
- Labels generated in generic format
- Print and affix to packages
- Manually book with courier

**Phase 2 (Future):**
- Integrate with courier APIs (Delhivery, Blue Dart, etc.)
- Auto-generate AWB (Airway Bill) numbers
- Print courier-specific labels
- Auto-track shipments

---

#### **5. Print Options**

**Printer Support:**
- Thermal printer (direct print via browser)
- Regular printer (A4 sheets with stickers)
- Export to PDF (for later printing)

**Batch Printing:**
- Print all labels at once
- Or select specific orders to print

---

#### **6. Label Preview**

**Before Printing:**
- Preview labels on screen
- Verify customer details
- Correct any errors
- Regenerate if needed

---

### **User Interface (React)**

**Components:**
- `<ShippingLabelGen />` - Main interface
- `<FileUpload />` - Upload Excel
- `<LabelPreview />` - Preview labels
- `<GenerateButton />` - Create PDF
- `<DownloadButton />` - Download PDF
- `<PrintButton />` - Direct print

**Workflow:**
1. User uploads Excel from Order Extractor
2. System parses and validates
3. Generates label preview
4. User reviews
5. Clicks "Generate Labels"
6. System creates PDF
7. User downloads or prints

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/b2c/labels/shipping/upload` - Upload Excel
- `/api/b2c/labels/shipping/generate` - Generate PDF
- `/api/b2c/labels/shipping/download/{file_id}` - Download PDF

**Label Generation:**
- Python library: `reportlab` (PDF generation)
- Or `weasyprint` (HTML to PDF)

**Template Engine:**
- HTML/CSS templates for labels
- Convert to PDF via library

---

### **Testing Checklist**

- [x] Upload Excel and parse correctly
- [x] Generate labels with correct data
- [x] Download PDF
- [x] Print labels (thermal and A4)
- [x] Handle missing/invalid data gracefully
- [x] Test with 100+ orders
- [x] Mobile upload support

---

## **CHILD MODULE 4.3: MRP LABEL GENERATOR**

### **Overview**

**Purpose:** Generate product MRP labels for items in orders

**Status:** ✅ **MIGRATED AND OPERATIONAL**  
**Migration Source:** Python/Streamlit tool

---

### **Core Features**

#### **1. Input: Excel File from Order Extractor**

**Process:**
1. User uploads Excel file (from Module 4.1)
2. System parses file
3. Extracts product data per line item

**Expected Columns:**
- Order Number
- Product Name
- SKU
- Quantity
- (Optional) Batch Number (future integration)

---

#### **2. MRP Label Content**

**Label Includes:**
- Product name
- Weight/quantity (e.g., "500g", "1kg")
- MRP (Maximum Retail Price)
- Mfg Date (if applicable)
- Best Before Date (if applicable)
- Batch Number (future)
- Company name and logo
- Nutritional info (if required)
- Barcode/QR code (optional)

**Label Size:**
- Small sticker labels (50mm x 75mm)
- Standard product label format

---

#### **3. Individual Label Generation**

**Process:**
1. For each line item in Excel:
   - Generate individual MRP label
   - If quantity > 1, generate multiple labels
2. Example: Order has 3 x 500g Tomatoes → Generate 3 labels

**Output:** Multiple individual PDF files per product

---

#### **4. Merge PDFs into Preset Files**

**Organization:**
- Group labels by product (all tomato labels together)
- Or by order (all labels for Order #123 together)
- Or by print batch (50 labels per file for easy printing)

**Preset Files:**
- Admin configures grouping logic
- System automatically merges individual PDFs
- Creates organized files for efficient printing

**File Naming:**
- By product: `MRP_Labels_Tomatoes_500g_20241205.pdf`
- By order: `MRP_Labels_Order123_20241205.pdf`
- By batch: `MRP_Labels_Batch1_20241205.pdf`

---

#### **5. Label Template**

**Template Customization:**
- Admin can modify label template
- Product-specific templates (different items may have different label formats)
- Include/exclude fields as needed

**Dynamic Fields:**
- Product name (from Excel)
- Weight/quantity (from product database or Excel)
- MRP (from product database)
- Dates (calculated or from database)
- Batch number (future: from batch tracking module)

---

#### **6. Print Options**

**Printer Support:**
- Sticker label printer
- Regular printer with label sheets
- Export to PDF (for later printing)

**Batch Printing:**
- Print all labels at once
- Or select specific products/orders

---

### **User Interface (React)**

**Components:**
- `<MRPLabelGen />` - Main interface
- `<FileUpload />` - Upload Excel
- `<LabelPreview />` - Preview labels
- `<OrganizationOptions />` - Choose grouping method
- `<GenerateButton />` - Create PDFs
- `<DownloadButton />` - Download merged PDFs
- `<PrintButton />` - Direct print

**Workflow:**
1. User uploads Excel from Order Extractor
2. System parses and identifies products
3. Generates label previews
4. User selects organization method (by product, order, or batch)
5. Clicks "Generate MRP Labels"
6. System creates individual labels
7. System merges into preset files
8. User downloads or prints

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/b2c/labels/mrp/upload` - Upload Excel
- `/api/b2c/labels/mrp/generate` - Generate labels
- `/api/b2c/labels/mrp/merge` - Merge PDFs
- `/api/b2c/labels/mrp/download/{file_id}` - Download

**Label Generation:**
- Python library: `reportlab` or `weasyprint`
- PDF merging: `PyPDF2` or `pypdf`

**Template Engine:**
- HTML/CSS templates for MRP labels
- Dynamic data injection
- Convert to PDF

---

### **Future Integration with Batch Tracking**

**Current:** No batch numbers on MRP labels

**Future (Phase 3):**
- Link B2C orders to batch tracking module
- WooCommerce orders allocated from inventory
- Batches assigned to B2C orders
- Batch numbers printed on MRP labels
- Complete traceability for B2C customers (if needed for recalls)

---

### **Testing Checklist**

- [x] Upload Excel and parse correctly
- [x] Generate individual MRP labels
- [x] Merge labels into preset files
- [x] Download merged PDFs
- [x] Print labels (sticker printer)
- [x] Handle products with multiple quantities
- [x] Test with 50+ products
- [x] Mobile upload support

---

## **Data Flow (Module 4 - B2C Ops)**

```
WooCommerce (Orders)
    ↓
Module 4.1: Order Extractor
    ↓ (Excel file)
    ├─→ Module 4.2: Shipping Label Generator → Shipping Labels (PDF)
    └─→ Module 4.3: MRP Label Generator → MRP Labels (PDFs)
    
Manual Process:
- Print labels
- Affix to packages
- Dispatch via courier
```

---

## **Future Automation Plans**

**Phase 2 (Automation):**
- Scheduled daily order extraction
- Auto-generate labels
- Email labels to fulfillment team
- Webhook-triggered extraction (real-time)

**Phase 3 (Integration):**
- WooCommerce orders → Auto-create SOs in Module 3.1
- Allocate from main inventory (Module 2.1)
- Track batches for B2C (Module 2.2)
- Batch numbers on MRP labels
- Link to B2C tickets (Module 7.2)
- Complete traceability

---

## **Success Criteria**

**Operational:**
- ✅ Quick order processing (extract to labels in < 10 minutes)
- ✅ Accurate shipping labels (no delivery errors)
- ✅ Correct MRP labels (regulatory compliance)
- ✅ Efficient printing (batch processing)

**User Experience:**
- ✅ Simple 3-step workflow (extract → shipping → MRP)
- ✅ Mobile-friendly uploads
- ✅ Fast PDF generation
- ✅ Easy printing

**Data Quality:**
- ✅ No missing customer details
- ✅ Correct product information
- ✅ Accurate quantities

---

**End of Module 4 Documentation**