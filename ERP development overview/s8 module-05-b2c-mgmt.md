# MODULE 5: B2C MANAGEMENT

**Document:** Step 8 - Module 5: B2C Management  
**Filename:** 08-Module-05-B2C-Management.md

---

## **Module Overview**

**Module Name:** B2C Management  
**Module Type:** Parent Module  
**Child Modules:** 3 (Website Inventory Update, Woo to Zoho Export, B2C Subscription Management)  
**Priority:** MEDIUM - Standalone suite, partially migrated

**Purpose:**  
Manage backend operations for B2C sales including inventory sync to WooCommerce, order export to Zoho Books, and subscription management.

---

## **Module Characteristics**

**Current Status:**
- ✅ **Module 5.1 - Website Inventory Update:** MIGRATED AND OPERATIONAL
- ✅ **Module 5.2 - Woo to Zoho Export:** MIGRATED AND OPERATIONAL
- ⏳ **Module 5.3 - B2C Subscription Management:** TO BE BUILT

**Migration Notes (5.1 & 5.2):**
- Existing business logic preserved from Streamlit tools
- UI converted to React
- Backend converted to FastAPI
- Database migrated to Supabase
- Same workflows maintained

**Standalone Operation:**
- Does NOT use core inventory (yet)
- Manual triggers (no automation yet)
- Independent of main SO/Invoice modules
- Shares framework, authentication, database infrastructure

**Future Integration Plans:**
- Sync inventory from main inventory module (Module 2.1)
- Auto-sync pricing from Zoho
- Subscription orders → Auto-create SOs in Module 3.1
- Timeline: Phase 3 (Months 12-18)

---

## **Internal Dashboard**

**Purpose:** Overview of B2C backend management

**Key Metrics:**
- Last inventory sync date/time
- Products out of sync (count)
- Last Zoho export date/time
- Active subscriptions (count)
- Subscription renewals due (this week)
- Pending sync operations

**Quick Actions:**
- Update website inventory
- Export orders to Zoho
- View subscriptions
- Create new subscription

---

## **CHILD MODULE 5.1: WEBSITE INVENTORY UPDATE**

### **Overview**

**Purpose:** Sync inventory and pricing from Marketplace Tools to WooCommerce website

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
- `/wp-json/wc/v3/products` - List products
- `/wp-json/wc/v3/products/{id}` - Get/update single product

---

#### **2. Data Sync Direction**

**One-Way Sync:** Marketplace Tools → WooCommerce

**What Gets Synced:**
- Stock quantity (available inventory)
- Sales price (discounted/current price)
- Regular price (MRP)

**NOT Synced:**
- Product name (manually maintained in WooCommerce)
- Product description
- Images
- Categories/tags
- Other product metadata

---

#### **3. Stock Quantity Update**

**Current Implementation:**
- Manual entry of stock quantities per product
- User selects products to update
- Enters new stock quantities
- System updates WooCommerce

**Future (Phase 3):**
- Pull from main inventory module (Module 2.1)
- Auto-calculate available B2C stock
- Real-time sync (as inventory changes)
- Stock reservation (when customer orders)

**Stock Calculation Logic (Future):**
```
B2C Available Stock = Total Packed Inventory 
                    - Allocated to B2B orders
                    - Reserved for B2C orders
                    - Safety stock buffer
```

---

#### **4. Sales Price Update**

**Sales Price (Discounted Price):**
- Current selling price on website
- Can be lower than MRP (for promotions)
- Manually set per product

**Use Cases:**
- Seasonal discounts
- Flash sales
- Clearance pricing
- Promotional campaigns

---

#### **5. Regular Price Update (MRP)**

**Regular Price:**
- Maximum Retail Price
- Usually shown as "strikethrough" price
- Indicates discount to customer

**Sync Logic:**
- Can sync from Zoho Books item price
- Or manually entered

---

#### **6. Product Selection**

**Batch Update:**
- Select multiple products
- Update all at once
- Efficient for daily sync

**Individual Update:**
- Update single product
- Quick price/stock adjustments

**Filter/Search:**
- Search products by name/SKU
- Filter by category
- Show only out-of-stock items

---

#### **7. Sync Validation**

**Before Sync:**
- Validate stock quantities (>= 0)
- Validate pricing (sales price <= regular price)
- Check WooCommerce connection

**After Sync:**
- Confirm successful updates
- Log failures (if any)
- Retry failed updates

---

#### **8. Sync Log**

**Track Updates:**
- Date/time of sync
- Products updated (list)
- Old vs new values (stock, prices)
- User who synced
- Status (success, partial, failed)
- Error messages (if any)

**Benefits:**
- Audit trail
- Troubleshooting
- Identify sync patterns

---

### **User Interface (React)**

**Components:**
- `<InventorySync />` - Main interface
- `<ProductList />` - Select products to sync
- `<StockInput />` - Enter stock quantities
- `<PriceInput />` - Enter prices
- `<SyncButton />` - Trigger sync
- `<SyncProgress />` - Show progress
- `<SyncLog />` - View history

**Workflow:**
1. User opens Website Inventory Update
2. Views list of products (from WooCommerce)
3. Selects products to update
4. Enters new stock quantities
5. (Optional) Updates sales/regular prices
6. Clicks "Sync to WooCommerce"
7. System updates WooCommerce via API
8. User sees confirmation
9. Sync logged

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/b2c/inventory/sync` - Trigger sync
- `/api/b2c/inventory/products` - List WooCommerce products
- `/api/b2c/inventory/update` - Update single product
- `/api/b2c/inventory/sync-log` - View history
- `/api/b2c/woocommerce/test-connection` - Test API

**WooCommerce Integration:**
- Python library: `woocommerce` (REST API wrapper)
- Batch update API calls

**Database (Supabase):**
- `woo_inventory_sync_log` table:
  - sync_id, products_updated, sync_status, user_id, timestamp
- `woo_product_cache` table (optional):
  - Cache WooCommerce products for faster loading

---

### **Automation (Future - Phase 2)**

**Scheduled Sync:**
- Run daily at specific time
- Auto-sync stock quantities from main inventory
- Auto-update pricing from Zoho
- Email summary to admin

**Real-Time Sync:**
- When inventory changes in main system → Update WooCommerce
- When customer orders → Reserve stock immediately

---

### **Testing Checklist**

- [x] Connect to WooCommerce API
- [x] List products from WooCommerce
- [x] Update stock quantity
- [x] Update sales price
- [x] Update regular price
- [x] Batch update multiple products
- [x] Handle API errors gracefully
- [x] Log sync history
- [x] Mobile responsiveness

---

## **CHILD MODULE 5.2: WOO TO ZOHO EXPORT**

### **Overview**

**Purpose:** Export WooCommerce orders to Zoho Books format for invoicing

**Status:** ✅ **MIGRATED AND OPERATIONAL**  
**Migration Source:** Python/Streamlit tool

---

### **Core Features**

#### **1. Order Fetching from WooCommerce**

**Fetch Criteria:**
- Status: Completed orders (ready for accounting)
- Date range: Select period to export
- Exclude already exported (prevent duplicates)

**Data Fetched:**
- Order details (number, date, status)
- Customer details (name, email, address)
- Line items (products, quantities, prices)
- Order totals (subtotal, tax, shipping, total)
- Payment method and status

---

#### **2. Item Database Manager Integration**

**Critical Dependency:** Module 6.4 (Item Database - WooCommerce)

**Mapping Logic:**
- WooCommerce product name → Zoho item name
- Uses Item Database Manager for mapping
- Includes HSN code (for GST compliance)
- Maps usage unit (kg, pcs, box)

**Example Mapping:**
```
WooCommerce: "Organic Iceberg Lettuce 500g"
    ↓ (Item Database Manager)
Zoho: "Iceberg-500"
HSN: "0705"
Unit: "kg"
```

**Missing Mappings:**
- Alert user if product not mapped
- Allow quick mapping from export interface
- Prevent export until all items mapped

---

#### **3. Data Formatting for Zoho Books**

**Output Format:** Excel (.xlsx) or CSV

**Zoho Invoice Import Format:**
- Invoice Number (WooCommerce order number or generated)
- Invoice Date (order date)
- Customer Name
- Customer Email
- Customer Address (billing)
- Line Items:
  - Item Name (Zoho format)
  - HSN Code
  - Quantity
  - Unit
  - Rate (unit price)
  - Tax Rate (%)
  - Tax Amount
  - Total (line item)
- Shipping Charges
- Total Tax
- Total Amount

**File Structure:**
- Header row with column names
- One row per line item (not per order)
- Footer with totals (optional)

**File Naming:**
- Format: `ZohoInvoices_YYYYMMDD_YYYYMMDD.xlsx`
- Example: `ZohoInvoices_20241201_20241205.xlsx`

---

#### **4. Tax Calculation (GST)**

**HSN-Based Tax Rates:**
- Each item has HSN code (from Item Database Manager)
- HSN determines tax rate (5%, 12%, 18%, etc.)
- Calculate CGST + SGST (intra-state) or IGST (inter-state)

**Customer Location:**
- If customer in same state → CGST + SGST
- If customer in different state → IGST

**Tax Breakdown:**
- Per line item: Tax amount calculated
- Invoice total: Sum of all taxes

---

#### **5. Customer Data Handling**

**Customer in Zoho:**
- If customer exists in Zoho → Use Zoho customer ID
- If customer doesn't exist → Include full details for manual creation

**Customer Matching:**
- Match by email (primary)
- Or by name + phone
- Flag new customers

**To Be Discussed:**
- Auto-create customers in Zoho via API (Phase 2)
- Or manual creation after export

---

#### **6. Payment & Shipping Data**

**Payment Method:**
- Captured from WooCommerce (COD, online, UPI, etc.)
- Mapped to Zoho payment terms
- Payment status (paid, pending)

**Shipping Charges:**
- Included as separate line item
- Or added to invoice total
- HSN code for shipping (if applicable)

**To Be Discussed:**
- How to handle shipping in Zoho format
- Discount/coupon codes mapping
- Refund scenarios

---

#### **7. Export Process**

**Steps:**
1. User selects date range
2. System fetches completed orders from WooCommerce
3. Validates all items are mapped (Item Database Manager)
4. Calculates taxes based on HSN and customer location
5. Formats data for Zoho Books import
6. Generates Excel/CSV file
7. User downloads file
8. Manual upload to Zoho Books (Phase 1)
9. Mark orders as "Exported to Zoho" (prevent duplicate)

---

#### **8. Export Log**

**Track Exports:**
- Date/time of export
- Date range exported
- Number of orders exported
- User who exported
- File generated
- Status (success, failed)

**Prevent Duplicates:**
- Flag orders as exported
- Filter out already-exported orders
- Option to re-export (with warning)

---

### **User Interface (React)**

**Components:**
- `<WooToZohoExport />` - Main interface
- `<DateRangePicker />` - Select period
- `<OrderList />` - Preview orders to export
- `<MappingValidator />` - Check item mappings
- `<TaxSummary />` - Show tax calculations
- `<ExportButton />` - Trigger export
- `<DownloadLink />` - Download file
- `<ExportLog />` - View history

**Workflow:**
1. User opens Woo to Zoho Export
2. Selects date range (completed orders)
3. System fetches orders from WooCommerce
4. Validates item mappings (via Module 6.4)
5. Shows preview: orders, items, totals, taxes
6. User reviews
7. Clicks "Export to Zoho Format"
8. System generates Excel/CSV
9. User downloads file
10. Manually uploads to Zoho Books
11. Export logged

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/b2c/zoho/export` - Trigger export
- `/api/b2c/zoho/orders` - Fetch completed orders
- `/api/b2c/zoho/validate-mappings` - Check item mappings
- `/api/b2c/zoho/generate-file` - Create Excel/CSV
- `/api/b2c/zoho/download/{file_id}` - Download file
- `/api/b2c/zoho/export-log` - View history

**Dependencies:**
- Item Database Manager (Module 6.4) - Item mappings
- WooCommerce API - Fetch orders
- Excel generation: `openpyxl` or `pandas`

**Database (Supabase):**
- `woo_zoho_export_log` table:
  - export_id, date_from, date_to, order_count, status, user_id, timestamp
- `woo_exported_orders` table:
  - order_id, export_id, exported_at (prevent duplicates)

---

### **Automation (Future - Phase 2)**

**Direct API Integration:**
- No manual Excel upload
- System directly creates invoices in Zoho via API
- Auto-create customers if needed
- Real-time sync

**Scheduled Export:**
- Daily export of previous day's completed orders
- Auto-generate and send to accounting team
- Email summary

---

### **Testing Checklist**

- [x] Fetch completed orders from WooCommerce
- [x] Validate all items mapped (Module 6.4)
- [x] Calculate taxes correctly (HSN-based)
- [x] Generate Zoho import format (Excel/CSV)
- [x] Download file
- [x] Test manual upload to Zoho Books
- [x] Prevent duplicate exports
- [x] Log export history
- [x] Handle unmapped items gracefully
- [x] Mobile responsiveness

---

## **CHILD MODULE 5.3: B2C SUBSCRIPTION MANAGEMENT**

### **Overview**

**Purpose:** Build and track recurring monthly subscription orders for D2C customers

**Status:** ⏳ **TO BE BUILT** (Phase 5, Week 13)  
**Estimated Duration:** 5-7 days

---

### **High-Level Requirements (To Be Refined)**

#### **1. Subscription Creation**

**Custom Subscription Builder:**
- Select customer (from WooCommerce or manual)
- Select products and quantities (custom basket)
- Set subscription frequency (weekly, bi-weekly, monthly)
- Set start date
- Set end date (optional - indefinite if blank)
- Set delivery day/time preferences
- Set pricing (standard or custom)
- Special instructions

**Subscription Details:**
- Subscription ID (unique)
- Customer details
- Product basket (items + quantities)
- Frequency
- Next delivery date
- Status (active, paused, cancelled)
- Payment terms (prepaid, COD, monthly invoice)

---

#### **2. Subscription Tracking**

**Active Subscriptions:**
- List all active subscriptions
- Show next delivery dates
- Alert for upcoming renewals
- Payment status tracking

**Subscription Statuses:**
- Active (running)
- Paused (temporarily stopped)
- Cancelled (ended)
- Expired (end date reached)

---

#### **3. Generate Shareable Documents**

**Subscription Agreement:**
- PDF document
- Customer details
- Subscription details (items, frequency, pricing)
- Terms & conditions
- Signatures (digital)

**Order Confirmations:**
- Per delivery cycle
- PDF or email
- Items, quantities, delivery date
- Payment amount

**Invoices:**
- Monthly invoice (for B2B subscriptions)
- Or per-delivery invoice (for B2C prepaid)

---

#### **4. Push Subscription Orders to WooCommerce**

**Auto-Generate Orders:**
- Based on subscription schedule
- Create WooCommerce order automatically
- Customer receives order notification
- Order processed like regular WooCommerce order

**Process:**
1. System checks subscriptions due for renewal (daily job)
2. For each due subscription:
   - Create WooCommerce order via API
   - Customer: Subscription customer
   - Items: Subscription basket
   - Delivery date: Subscription schedule
3. WooCommerce order → Flows through Modules 4.1-4.3 (Order Extractor → Labels)

---

#### **5. Transaction History**

**Track All Deliveries:**
- Per subscription, show:
  - Delivery dates (past and future)
  - WooCommerce order numbers
  - Quantities delivered
  - Payment status
  - Any issues (customer tickets)

**History View:**
- Complete delivery history
- Payment history
- Modifications (product changes, pauses, etc.)

---

#### **6. Subscription Modifications**

**Customer Requests:**
- Change products (add/remove items)
- Change quantities
- Change delivery frequency
- Change delivery day/time
- Pause subscription (temporary hold)
- Cancel subscription

**Admin Actions:**
- Modify subscription on customer request
- Track modification history
- Notify customer of changes

---

#### **7. Subscription Renewals**

**Auto-Renewal:**
- Active subscriptions auto-renew
- Generate next order on schedule
- No manual intervention

**Payment:**
- Prepaid: Customer pays upfront (monthly/quarterly)
- COD: Pay on delivery (each order)
- Invoice: Monthly consolidated invoice (B2B)

**Renewal Notifications:**
- Email/SMS to customer before renewal
- Payment reminder (if prepaid)
- Confirm delivery date

---

#### **8. Subscription Dashboard**

**Overview:**
- Total active subscriptions
- Subscriptions due this week
- Pending payments (if prepaid)
- Recently cancelled/paused
- Renewal trends

**List View:**
- All subscriptions with filters (status, customer, frequency)
- Search by customer name or subscription ID
- Quick actions (view, edit, pause, cancel)

---

### **To Be Discussed**

- Subscription frequency options (weekly, bi-weekly, monthly, custom)
- Auto-renewal logic and payment handling
- Customer self-service portal (manage own subscription)
- Pause/resume workflow
- Proration for mid-cycle changes
- Discount for subscriptions (vs one-time orders)
- Delivery slot management (capacity planning)
- Subscription analytics (retention, churn, LTV)
- Integration with main SO module (create SOs for subscriptions)
- Batch tracking for subscription orders (future)

---

### **Technical Implementation (Proposed)**

**Backend (FastAPI):**
- `/api/b2c/subscriptions/create` - Create subscription
- `/api/b2c/subscriptions/list` - List subscriptions
- `/api/b2c/subscriptions/{id}` - Get subscription details
- `/api/b2c/subscriptions/{id}/update` - Modify subscription
- `/api/b2c/subscriptions/{id}/pause` - Pause subscription
- `/api/b2c/subscriptions/{id}/cancel` - Cancel subscription
- `/api/b2c/subscriptions/generate-orders` - Create WooCommerce orders (scheduled job)
- `/api/b2c/subscriptions/{id}/history` - View transaction history
- `/api/b2c/subscriptions/{id}/documents` - Generate PDFs

**Frontend (React):**
- `<SubscriptionCreator />` - Build custom subscription
- `<SubscriptionList />` - View all subscriptions
- `<SubscriptionDetail />` - Single subscription view
- `<SubscriptionEditor />` - Modify subscription
- `<SubscriptionHistory />` - Transaction history
- `<DocumentGenerator />` - Generate agreements/invoices

**Database (Supabase):**
- `b2c_subscriptions` table:
  - subscription_id, customer_id, basket (JSON), frequency, start_date, end_date, status
- `b2c_subscription_deliveries` table:
  - delivery_id, subscription_id, delivery_date, woo_order_id, status, payment_status
- `b2c_subscription_modifications` table:
  - modification_id, subscription_id, change_type, old_value, new_value, timestamp

**WooCommerce Integration:**
- Auto-create orders via WooCommerce API
- Link orders to subscriptions

---

### **Testing Checklist (To Be Built)**

- [ ] Create custom subscription
- [ ] Generate subscription agreement PDF
- [ ] Push order to WooCommerce (auto-generate)
- [ ] Track transaction history
- [ ] Modify subscription (products, frequency)
- [ ] Pause and resume subscription
- [ ] Cancel subscription
- [ ] Auto-renewal (scheduled job)
- [ ] Payment tracking
- [ ] Customer notifications
- [ ] Mobile responsiveness

---

## **Parked for Future Discussion**

**B2C Management Items:**
- Inventory sync automation (real-time vs scheduled)
- Stock reservation logic (WooCommerce orders)
- Pricing sync from Zoho (auto-update WooCommerce)
- Customer auto-creation in Zoho via API
- Direct Zoho Books API integration (Phase 2)
- Subscription self-service portal for customers
- Subscription analytics and retention tracking
- Delivery slot capacity management
- Proration logic for mid-cycle subscription changes

---

## **Success Criteria**

**Operational:**
- ✅ Accurate inventory sync to website (no overselling)
- ✅ Correct order export to Zoho (accurate invoicing)
- ✅ Efficient subscription management (auto-renewals)
- ✅ Complete subscription history tracking

**Data Quality:**
- ✅ All items properly mapped (WooCommerce ↔ Zoho)
- ✅ Accurate tax calculations (GST compliance)
- ✅ No duplicate exports to Zoho

**Customer Satisfaction:**
- ✅ Website shows accurate stock
- ✅ Subscriptions delivered on schedule
- ✅ Clear communication (agreements, invoices)
- ✅ Easy subscription modifications

---

**End of Module 5 Documentation**