# MODULE 6: DATABASE MANAGEMENT

**Document:** Step 9 - Module 6: Database Management  
**Filename:** 09-Module-06-Database-Management.md

---

## **Module Overview**

**Module Name:** Database Management  
**Module Type:** Parent Module  
**Child Modules:** 4 (Item Database - Zoho, Customer Database - Zoho, Vendor Database - Zoho, Item Database - WooCommerce)  
**Priority:** HIGH - Foundation for all operational modules

**Purpose:**  
Maintain synchronized master data from Zoho Books and manage item mappings between WooCommerce and Zoho for accurate invoicing.

---

## **Module Characteristics**

**Current Status:**
- ✅ **ALL 4 DATABASES COMPLETED AND OPERATIONAL**
- Foundation modules already in place
- All other modules depend on these

**Data Governance:**
- **Zoho Books:** Source of Truth for Items, Customers, Vendors
- **One-Way Sync:** Zoho → Marketplace Tools
- **Read-Only Master Data:** Cannot create/edit Items, Customers, Vendors in Marketplace Tools
- **Operational Extensions:** Can add internal tags, categories, notes (editable)

**Database Location:**
- Supabase (PostgreSQL)
- Separate tables for each database
- Logical separation from operational data

---

## **Internal Dashboard**

**Purpose:** Monitor master data sync status

**Key Metrics:**
- Last sync timestamp (per database)
- Sync status (success, failed, in-progress)
- Record counts:
  - Items (Zoho): X records
  - Customers (Zoho): X records
  - Vendors (Zoho): X records
  - Item Mappings (WooCommerce): X records
- Data discrepancy alerts (if any)
- Missing mappings (WooCommerce items not mapped)

**Visualizations:**
- Sync history timeline
- Record growth over time
- Sync failure trend
- Missing mapping count

**Quick Actions:**
- Trigger manual sync (per database)
- View sync logs
- Manage item mappings
- Export master data

---

## **CHILD MODULE 6.1: ITEM DATABASE (Zoho)**

### **Overview**

**Purpose:** Maintain synchronized copy of item master data from Zoho Books

**Status:** ✅ **COMPLETED AND OPERATIONAL**  
**Priority:** CRITICAL - All modules depend on this

---

### **Core Features**

#### **1. Source of Truth: Zoho Books**

**Master Data Location:** Zoho Books

**Why Zoho is Source:**
- Accounting system of record
- Pricing managed in Zoho
- Tax codes (HSN) in Zoho
- Financial reporting requires Zoho data

**Item Creation:**
- Items MUST originate in Zoho Books
- Cannot create items in Marketplace Tools
- New items → Add in Zoho first → Sync to Marketplace Tools

---

#### **2. One-Way Sync (Zoho → Marketplace Tools)**

**Sync Direction:** Zoho Books → Marketplace Tools (one-way only)

**Sync Frequency:**
- Manual trigger (Phase 1)
- Scheduled (daily, hourly) - Future
- Real-time webhook (Phase 2)

**Sync Process:**
1. Connect to Zoho Books API
2. Fetch all items (or incremental changes)
3. Update Marketplace Tools database
4. Log sync results

**Conflict Prevention:**
- Master data is read-only in Marketplace Tools
- No possibility of dual editing
- Changes always originate from Zoho

---

#### **3. Item Data Synced**

**Master Data (from Zoho):**
- Item ID (Zoho item ID)
- Item Name
- SKU
- Unit (kg, pcs, box, etc.)
- Item Type (goods, service)
- Category (if configured in Zoho)
- Default Price (Zoho price column)
- HSN Code (for GST)
- Tax Rate (if configured)
- Active/Inactive status
- Description
- Custom Fields (if any)

**Metadata:**
- Created Date (in Zoho)
- Last Modified Date (in Zoho)
- Last Synced Date (in Marketplace Tools)

---

#### **4. Operational Extensions (Editable in Marketplace Tools)**

**Internal Fields (Not in Zoho):**
- Internal Tags (e.g., "perishable", "seasonal", "premium")
- Categories (internal classification, separate from Zoho)
- Notes (internal use)
- Reorder Level (for low stock alerts)
- Preferred Vendors (list of farm IDs)
- Shelf Life (days)
- Storage Instructions
- Quality Grading Required (yes/no)
- B2C Availability (show on website)

**Purpose:**
- Operational metadata specific to farm-to-fork business
- Doesn't clutter Zoho Books
- Used by Marketplace Tools modules only

---

#### **5. Database Schema**

**Table: `items_zoho`**

**Columns:**
- `id` (Primary Key, internal)
- `zoho_item_id` (Unique, from Zoho)
- `item_name` (from Zoho)
- `sku` (from Zoho)
- `unit` (from Zoho)
- `item_type` (from Zoho)
- `category` (from Zoho)
- `default_price` (from Zoho)
- `hsn_code` (from Zoho)
- `tax_rate` (from Zoho)
- `is_active` (from Zoho)
- `description` (from Zoho)
- `created_at_zoho` (from Zoho)
- `last_modified_zoho` (from Zoho)
- `last_synced_at` (Marketplace Tools timestamp)
- **Operational Extensions:**
- `internal_tags` (JSON array)
- `internal_category` (text)
- `notes` (text)
- `reorder_level` (decimal)
- `preferred_vendors` (JSON array of vendor IDs)
- `shelf_life_days` (integer)
- `storage_instructions` (text)
- `requires_grading` (boolean)
- `b2c_available` (boolean)

---

#### **6. Item Management Interface**

**View:**
- List all items (paginated)
- Search by name, SKU
- Filter by category, active/inactive, B2C availability
- Sort by name, price, last synced

**Edit (Operational Fields Only):**
- Cannot edit master data (name, price, HSN, etc.)
- Can edit internal tags, notes, reorder level, etc.
- Save operational extensions

**Sync:**
- Manual sync button
- Shows last sync time
- Progress indicator during sync

---

#### **7. Used By Modules**

**Modules that use Item Database:**
- PO Management (Module 1.1) - Item selection, pricing
- GRN Management (Module 1.2) - Item validation
- Grading & Sorting (Module 1.3) - Item processing
- Packing (Module 1.4) - Item packing
- Inventory (Module 2.1) - Stock tracking
- SO Management (Module 3.1) - Item selection
- Invoice Management (Module 3.3) - Invoicing
- Woo to Zoho Export (Module 5.2) - Item mapping
- All reporting modules

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/database/items-zoho/sync` - Trigger sync from Zoho
- `/api/database/items-zoho/list` - List items
- `/api/database/items-zoho/{id}` - Get item details
- `/api/database/items-zoho/{id}/update-extensions` - Update operational fields
- `/api/database/items-zoho/sync-log` - View sync history

**Zoho Books API Integration:**
- Endpoint: `/items` (Zoho Books API)
- Authentication: OAuth or API key
- Pagination handling (large item lists)

**Database (Supabase):**
- `items_zoho` table (as described above)
- `zoho_sync_log` table:
  - sync_id, entity_type (items), sync_status, records_synced, timestamp

---

### **Testing Checklist**

- [x] Connect to Zoho Books API
- [x] Fetch all items from Zoho
- [x] Insert/update items in Marketplace Tools
- [x] Handle deleted items in Zoho (mark inactive)
- [x] Edit operational extensions (tags, notes)
- [x] Sync log tracks history
- [x] Handle API errors gracefully
- [x] Performance with 500+ items

---

## **CHILD MODULE 6.2: CUSTOMER DATABASE (Zoho)**

### **Overview**

**Purpose:** Maintain synchronized copy of customer master data from Zoho Books

**Status:** ✅ **COMPLETED AND OPERATIONAL**  
**Priority:** CRITICAL - Required for SO and Invoice modules

---

### **Core Features**

#### **1. Source of Truth: Zoho Books**

**Master Data Location:** Zoho Books

**Customer Types:**
- B2B Customers (hotels, restaurants)
- B2C Customers (may sync from WooCommerce to Zoho first, then to Marketplace Tools)

**Customer Creation:**
- Customers MUST originate in Zoho Books
- Cannot create customers in Marketplace Tools
- New customers → Add in Zoho first → Sync to Marketplace Tools

---

#### **2. One-Way Sync (Zoho → Marketplace Tools)**

**Sync Direction:** Zoho Books → Marketplace Tools (one-way only)

**Sync Frequency:**
- Manual trigger (Phase 1)
- Scheduled (daily) - Future
- Real-time webhook (Phase 2)

---

#### **3. Customer Data Synced**

**Master Data (from Zoho):**
- Customer ID (Zoho customer ID)
- Customer Name
- Contact Person
- Email
- Phone
- Billing Address (full)
- Shipping Address(es) (if multiple)
- Payment Terms (net 30, net 60, COD, etc.)
- Credit Limit (if configured)
- Customer Type (B2B, B2C)
- GST Number (if applicable)
- Active/Inactive status
- Custom Fields (if any)

**Metadata:**
- Created Date (in Zoho)
- Last Modified Date (in Zoho)
- Last Synced Date (in Marketplace Tools)

---

#### **4. Operational Extensions (Editable in Marketplace Tools)**

**Internal Fields (Not in Zoho):**
- Customer Tier (Platinum, Gold, Silver - for pricing)
- Delivery Preferences (time windows, special instructions)
- Packaging Preferences (specific packaging needs)
- Blacklisted Farms (customer doesn't want produce from specific farms)
- Delivery Route (for logistics optimization)
- Notes (internal CRM notes)
- Preferred Payment Method (for operations)
- Delivery Frequency (for recurring orders)
- Quality Sensitivity (high, medium, low)

**Purpose:**
- Operational metadata for farm-to-fork fulfillment
- CRM-like functionality within Marketplace Tools
- Not needed in accounting system (Zoho)

---

#### **5. Database Schema**

**Table: `customers_zoho`**

**Columns:**
- `id` (Primary Key, internal)
- `zoho_customer_id` (Unique, from Zoho)
- `customer_name` (from Zoho)
- `contact_person` (from Zoho)
- `email` (from Zoho)
- `phone` (from Zoho)
- `billing_address` (JSON, from Zoho)
- `shipping_addresses` (JSON array, from Zoho)
- `payment_terms` (from Zoho)
- `credit_limit` (from Zoho)
- `customer_type` (from Zoho: B2B/B2C)
- `gst_number` (from Zoho)
- `is_active` (from Zoho)
- `created_at_zoho` (from Zoho)
- `last_modified_zoho` (from Zoho)
- `last_synced_at` (Marketplace Tools timestamp)
- **Operational Extensions:**
- `customer_tier` (text: Platinum, Gold, Silver)
- `delivery_preferences` (JSON)
- `packaging_preferences` (text)
- `blacklisted_farms` (JSON array of vendor IDs)
- `delivery_route` (text)
- `notes` (text)
- `preferred_payment_method` (text)
- `delivery_frequency` (text)
- `quality_sensitivity` (text: high, medium, low)

---

#### **6. Customer Management Interface**

**View:**
- List all customers (paginated)
- Search by name, email, phone
- Filter by type (B2B, B2C), tier, active/inactive
- Sort by name, last order date

**Edit (Operational Fields Only):**
- Cannot edit master data (name, email, address from Zoho)
- Can edit tier, preferences, blacklist, notes, etc.
- Save operational extensions

**Sync:**
- Manual sync button
- Shows last sync time

---

#### **7. Customer-Specific Pricing (Future Integration)**

**Pricing Tiers:**
- Link customer tier to pricing rules
- Example: Platinum customers get 10% discount
- Or specific item-customer pricing (like vendor-item pricing)

**To Be Built:**
- Customer-item pricing table (similar to vendor-item pricing in Module 1.1)
- Pricing logic in SO Management (Module 3.1)

---

#### **8. Used By Modules**

**Modules that use Customer Database:**
- SO Management (Module 3.1) - Customer selection
- Order Allocation (Module 3.2) - Blacklist enforcement
- Invoice Management (Module 3.3) - Customer details on invoice
- Logistics & Routing (Module 3.4) - Delivery addresses and preferences
- B2B Tickets (Module 7.1) - Customer issue tracking
- Reporting (Module 8) - Customer analysis

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/database/customers-zoho/sync` - Trigger sync from Zoho
- `/api/database/customers-zoho/list` - List customers
- `/api/database/customers-zoho/{id}` - Get customer details
- `/api/database/customers-zoho/{id}/update-extensions` - Update operational fields
- `/api/database/customers-zoho/sync-log` - View sync history

**Zoho Books API Integration:**
- Endpoint: `/contacts` (Zoho Books API)
- Filter: Customer type contacts only

**Database (Supabase):**
- `customers_zoho` table (as described above)
- `zoho_sync_log` table

---

### **Testing Checklist**

- [x] Connect to Zoho Books API
- [x] Fetch all customers from Zoho
- [x] Insert/update customers in Marketplace Tools
- [x] Handle deleted customers in Zoho (mark inactive)
- [x] Edit operational extensions (tier, preferences, blacklist)
- [x] Sync log tracks history
- [x] Handle API errors gracefully
- [x] Performance with 200+ customers

---

## **CHILD MODULE 6.3: VENDOR DATABASE (Zoho)**

### **Overview**

**Purpose:** Maintain synchronized copy of vendor/farm master data from Zoho Books

**Status:** ✅ **COMPLETED AND OPERATIONAL**  
**Priority:** CRITICAL - Required for PO and vendor pricing modules

---

### **Core Features**

#### **1. Source of Truth: Zoho Books**

**Master Data Location:** Zoho Books

**Vendor Types:**
- Farms (primary suppliers)
- Market vendors (emergency procurement)
- Service providers (if tracked)

**Vendor Creation:**
- Vendors MUST originate in Zoho Books
- Cannot create vendors in Marketplace Tools
- New vendors → Add in Zoho first → Sync to Marketplace Tools

---

#### **2. One-Way Sync (Zoho → Marketplace Tools)**

**Sync Direction:** Zoho Books → Marketplace Tools (one-way only)

**Sync Frequency:**
- Manual trigger (Phase 1)
- Scheduled (daily) - Future
- Real-time webhook (Phase 2)

---

#### **3. Vendor Data Synced**

**Master Data (from Zoho):**
- Vendor ID (Zoho vendor ID)
- Vendor Name
- Contact Person
- Email
- Phone
- Address (full)
- Payment Terms (net 30, immediate, etc.)
- Bank Details (for payment)
- GST Number (if applicable)
- PAN Number (if applicable)
- Vendor Type (farm, market, service)
- Active/Inactive status
- Custom Fields (if any)

**Metadata:**
- Created Date (in Zoho)
- Last Modified Date (in Zoho)
- Last Synced Date (in Marketplace Tools)

---

#### **4. Operational Extensions (Editable in Marketplace Tools)**

**Internal Fields (Not in Zoho):**
- Farm Location (GPS coordinates)
- Farm Size (acres, if relevant)
- Primary Products (list of items they supply)
- Quality Rating (1-5 stars, based on history)
- Reliability Score (delivery on-time %)
- Wastage History (average damage/reject %)
- Certifications (organic, GAP, etc.)
- Lead Time (days from order to delivery)
- Dispatch Days (which days they dispatch)
- Notes (internal farm notes)
- Preferred Communication (phone, WhatsApp, email)
- Seasonal Availability (months they operate)

**Purpose:**
- Farm performance tracking
- Procurement planning
- Quality management
- Not needed in accounting system (Zoho)

---

#### **5. Database Schema**

**Table: `vendors_zoho`**

**Columns:**
- `id` (Primary Key, internal)
- `zoho_vendor_id` (Unique, from Zoho)
- `vendor_name` (from Zoho)
- `contact_person` (from Zoho)
- `email` (from Zoho)
- `phone` (from Zoho)
- `address` (JSON, from Zoho)
- `payment_terms` (from Zoho)
- `bank_details` (JSON, from Zoho)
- `gst_number` (from Zoho)
- `pan_number` (from Zoho)
- `vendor_type` (from Zoho)
- `is_active` (from Zoho)
- `created_at_zoho` (from Zoho)
- `last_modified_zoho` (from Zoho)
- `last_synced_at` (Marketplace Tools timestamp)
- **Operational Extensions:**
- `farm_location` (geography/GPS)
- `farm_size` (decimal)
- `primary_products` (JSON array of item IDs)
- `quality_rating` (decimal 1-5)
- `reliability_score` (decimal 0-100)
- `avg_wastage_percent` (decimal)
- `certifications` (JSON array)
- `lead_time_days` (integer)
- `dispatch_days` (JSON array: ["Monday", "Wednesday"])
- `notes` (text)
- `preferred_communication` (text)
- `seasonal_availability` (JSON: months/dates)

---

#### **6. Vendor Management Interface**

**View:**
- List all vendors (paginated)
- Search by name, phone
- Filter by type, active/inactive, quality rating
- Sort by name, quality rating, reliability score

**Edit (Operational Fields Only):**
- Cannot edit master data (name, email, address from Zoho)
- Can edit quality rating, lead time, notes, etc.
- Save operational extensions

**Sync:**
- Manual sync button
- Shows last sync time

**Vendor Performance Dashboard:**
- Quality rating trend
- Reliability score over time
- Wastage history (last 6 months)
- On-time delivery %

---

#### **7. Vendor-Item Pricing Integration**

**Links to Module 1.1 (PO Management):**
- Vendor-specific time-based pricing stored separately
- References vendor ID from this database
- Quality rating impacts pricing recommendations

---

#### **8. Used By Modules**

**Modules that use Vendor Database:**
- PO Management (Module 1.1) - Vendor selection, pricing
- GRN Management (Module 1.2) - Vendor details
- Wastage Tracking (Module 2.3) - Farm quality tracking
- Reporting (Module 8) - Vendor performance analysis

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/database/vendors-zoho/sync` - Trigger sync from Zoho
- `/api/database/vendors-zoho/list` - List vendors
- `/api/database/vendors-zoho/{id}` - Get vendor details
- `/api/database/vendors-zoho/{id}/update-extensions` - Update operational fields
- `/api/database/vendors-zoho/{id}/performance` - Vendor performance metrics
- `/api/database/vendors-zoho/sync-log` - View sync history

**Zoho Books API Integration:**
- Endpoint: `/contacts` (Zoho Books API)
- Filter: Vendor type contacts only

**Database (Supabase):**
- `vendors_zoho` table (as described above)
- `zoho_sync_log` table

---

### **Testing Checklist**

- [x] Connect to Zoho Books API
- [x] Fetch all vendors from Zoho
- [x] Insert/update vendors in Marketplace Tools
- [x] Handle deleted vendors in Zoho (mark inactive)
- [x] Edit operational extensions (quality rating, notes)
- [x] Vendor performance calculations
- [x] Sync log tracks history
- [x] Handle API errors gracefully
- [x] Performance with 50+ vendors

---

## **CHILD MODULE 6.4: ITEM DATABASE (WooCommerce)**

### **Overview**

**Purpose:** Maintain item mappings between WooCommerce products and Zoho Books items for accurate invoicing

**Status:** ✅ **COMPLETED AND OPERATIONAL** (Migrated from separate database)  
**Priority:** CRITICAL - Required for Woo to Zoho Export (Module 5.2)

---

### **Core Features**

#### **1. Purpose of Item Mapping**

**Problem:**
- WooCommerce product names are customer-facing (e.g., "Organic Iceberg Lettuce 500g")
- Zoho Books item names are internal/accounting (e.g., "Iceberg-500")
- HSN codes required for GST compliance
- Need to map WooCommerce → Zoho for invoice import

**Solution:**
- Maintain mapping table
- One WooCommerce product → One Zoho item
- Include HSN code, usage unit, tax rate

---

#### **2. Mapping Data**

**Fields Tracked:**
- WooCommerce Product ID
- WooCommerce Product Name (customer-facing)
- WooCommerce SKU
- Zoho Item ID (links to Module 6.1 Item Database)
- Zoho Item Name (accounting name)
- HSN Code (for GST)
- Usage Unit (kg, pcs, box)
- Tax Rate (%)
- Other Parameters:
  - Product Category
  - Is Taxable (yes/no)
  - Tax Exemption Reason (if applicable)
  - Custom Tax Rules (if any)

---

#### **3. Database Schema**

**Table: `item_mappings_woocommerce`**

**Columns:**
- `id` (Primary Key, internal)
- `woo_product_id` (from WooCommerce)
- `woo_product_name` (from WooCommerce)
- `woo_sku` (from WooCommerce)
- `zoho_item_id` (FK to items_zoho table)
- `zoho_item_name` (from Zoho, via items_zoho)
- `hsn_code` (for GST)
- `usage_unit` (kg, pcs, box, liters, etc.)
- `tax_rate` (decimal, %)
- `product_category` (text)
- `is_taxable` (boolean)
- `tax_exemption_reason` (text, if not taxable)
- `notes` (text, internal)
- `created_at`
- `updated_at`
- `last_modified_by` (user ID)

---

#### **4. Mapping Management Interface**

**List View:**
- All WooCommerce products
- Mapped vs Unmapped status
- Search by WooCommerce name or SKU
- Filter by mapped/unmapped, category

**Add/Edit Mapping:**
- Select WooCommerce product (dropdown or search)
- Select Zoho item (dropdown from Module 6.1)
- System auto-fills HSN, unit from Zoho item
- Can override if needed
- Enter tax rate (if different from Zoho)
- Add notes
- Save mapping

**Bulk Import:**
- Upload CSV with mappings
- Validate all products and items exist
- Import mappings
- Show success/failure report

---

#### **5. Validation Rules**

- WooCommerce product ID must be unique (one mapping per product)
- Zoho item ID must exist in items_zoho table
- HSN code required (GST compliance)
- Usage unit required
- Tax rate must be 0-100

---

#### **6. Unmapped Products Alert**

**Dashboard Widget:**
- Show count of unmapped WooCommerce products
- Alert when trying to export orders with unmapped products
- Link to mapping interface

**Prevent Export Without Mapping:**
- Module 5.2 (Woo to Zoho Export) checks mappings
- If any order has unmapped product → Block export
- Show list of unmapped products
- Allow quick mapping from export interface

---

#### **7. Sync with WooCommerce**

**Fetch WooCommerce Products:**
- Connect to WooCommerce API
- Fetch all products (or new products)
- Check which are unmapped
- Alert admin

**Frequency:**
- Manual trigger
- Or scheduled (daily check for new products)

---

#### **8. Used By Modules**

**Primary User:**
- Woo to Zoho Export (Module 5.2) - Uses mappings for invoice format

**Future:**
- B2C Subscription Management (Module 5.3) - Product selection
- Reporting (Module 8) - B2C product analysis

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/database/item-mappings/list` - List all mappings
- `/api/database/item-mappings/create` - Create new mapping
- `/api/database/item-mappings/{id}/update` - Update mapping
- `/api/database/item-mappings/{id}/delete` - Delete mapping
- `/api/database/item-mappings/unmapped` - List unmapped WooCommerce products
- `/api/database/item-mappings/bulk-import` - Bulk CSV import
- `/api/database/item-mappings/fetch-woo-products` - Sync from WooCommerce

**Integration:**
- WooCommerce API - Fetch products
- Module 6.1 (Item Database Zoho) - Link to Zoho items

**Database (Supabase):**
- `item_mappings_woocommerce` table (as described above)

---

### **Testing Checklist**

- [x] Create mapping (WooCommerce → Zoho)
- [x] Edit mapping
- [x] Delete mapping
- [x] List unmapped products
- [x] Bulk import mappings (CSV)
- [x] Validate mapping (check Zoho item exists)
- [x] Sync new products from WooCommerce
- [x] Admin-only access enforcement
- [x] Mobile responsiveness

---

## **Integration Between Modules**

### **Cross-Database Relationships**

**Vendor-Item Pricing (Module 1.1):**
- Uses vendors_zoho.id
- Uses items_zoho.id
- Stores vendor-specific prices

**PO Creation (Module 1.1):**
- Selects vendor from vendors_zoho
- Selects items from items_zoho
- Gets pricing from vendor-item pricing

**SO Creation (Module 3.1):**
- Selects customer from customers_zoho
- Selects items from items_zoho
- Gets customer-specific pricing (future)

**Woo to Zoho Export (Module 5.2):**
- Uses item_mappings_woocommerce
- Links to items_zoho for HSN, unit

---

## **Sync Strategy**

### **Phase 1 (Current): Manual Sync**
- Admin triggers sync manually
- On-demand when needed
- Simple, controlled

### **Phase 2 (Future): Scheduled Sync**
- Daily sync (overnight)
- Hourly sync (for critical data)
- Configurable frequency

### **Phase 3 (Future): Real-Time Sync**
- Zoho Books webhooks
- Near real-time updates
- Immediate sync on changes in Zoho

---

## **Data Integrity**

### **Conflict Prevention**

**Read-Only Master Data:**
- Items, Customers, Vendors from Zoho are read-only
- Cannot edit in Marketplace Tools
- Changes must be made in Zoho first

**Operational Extensions:**
- Editable in Marketplace Tools
- Not synced back to Zoho
- Independent of Zoho data

### **Deleted Records**

**Handling Deletes in Zoho:**
- Mark as inactive in Marketplace Tools
- Don't delete (preserve history)
- Prevent new transactions with inactive records

---

## **Admin Responsibilities**

**Database Management Admin Tasks:**
- Trigger manual syncs
- Monitor sync status
- Resolve sync errors
- Manage item mappings (WooCommerce)
- Update operational extensions
- Review data discrepancies

---

## **Success Criteria**

**Data Quality:**
- ✅ Master data always in sync with Zoho
- ✅ No data discrepancies
- ✅ All WooCommerce products mapped

**System Performance:**
- ✅ Sync completes in < 5 minutes (for 500 items, 200 customers, 50 vendors)
- ✅ No sync failures
- ✅ Efficient API usage (rate limits respected)

**Operational Efficiency:**
- ✅ Single source of truth maintained (Zoho)
- ✅ Operational extensions support farm-to-fork workflows
- ✅ Easy mapping management for admin

---

**End of Module 6 Documentation**