# MODULE 8: REPORTING

**Document:** Step 11 - Module 8: Reporting  
**Filename:** 11-Module-08-Reporting.md

---

## **Module Overview**

**Module Name:** Reporting & Analytics  
**Module Type:** Parent Module  
**Child Modules:** 1 comprehensive reporting module with multiple sub-modules  
**Priority:** MEDIUM - Build after core operations functional

**Purpose:**  
Provide comprehensive business intelligence through reports and analytics across all operational modules for data-driven decision making.

---

## **Module Characteristics**

**Build Priority:**
- Phase 6 (Weeks 14-15)
- After core operational modules functional
- Requires data from all modules

**Reporting Approach:**
- Comprehensive reporting suite
- Multiple report categories
- Flexible filters and date ranges
- Export options (CSV, Excel, PDF)
- Scheduled reports (future)
- Custom report builder (future enhancement)

---

## **Internal Dashboard**

**Purpose:** Quick access to frequently run reports

**Key Metrics:**
- Reports run today/this week
- Scheduled reports status
- Most popular reports
- Recent downloads

**Quick Actions:**
- Run standard reports
- Generate custom report
- Schedule report
- Download recent reports

---

## **CHILD MODULE 8.1: REPORTING & ANALYTICS (Comprehensive)**

### **Overview**

**Purpose:** Generate business intelligence reports across all modules

**Build Priority:** MEDIUM - Build in Phase 6 (Weeks 14-15)  
**Estimated Duration:** 7-10 days

---

## **REPORT CATEGORIES**

### **1. PURCHASE ANALYSIS REPORTS**

**Purpose:** Analyze procurement from farms, vendor performance, pricing trends

---

#### **1.1 PO Summary Report**

**Data Included:**
- Date range
- PO count
- Total value
- By farm/vendor (breakdown)
- By item (breakdown)
- Average PO value
- On-time delivery %

**Filters:**
- Date range (from, to)
- Farm/vendor (select multiple)
- Item (select multiple)
- PO status (sent, completed, exported)

**Export Formats:** CSV, Excel, PDF

---

#### **1.2 Vendor Performance Report**

**Data Included:**
- Vendor name
- Total POs placed
- Total value purchased
- On-time delivery %
- Average delivery lead time
- Damage rate (from GRN)
- Reject rate (from GRN)
- Quality rating (from Module 6.3)
- Reliability score

**Ranking:**
- Best vendors (by quality, reliability, price)
- Problem vendors (high damage/reject)

**Filters:**
- Date range
- Vendor (select multiple)
- Sort by (quality, reliability, value)

**Use Case:** Inform procurement decisions, negotiate pricing, identify reliable farms

---

#### **1.3 Price Trend Analysis**

**Data Included:**
- Item
- Price over time (line chart)
- By vendor (compare vendors for same item)
- Seasonal patterns
- Price variance (high, low, average)
- Current price vs historical average

**Filters:**
- Date range
- Item (select multiple)
- Vendor (select multiple)

**Use Case:** Negotiate pricing, plan budget, identify seasonal opportunities

---

#### **1.4 PO vs GRN Variance Report**

**Data Included:**
- PO number
- Expected quantity (from PO)
- Actual received (from GRN)
- Variance (quantity and %)
- Reason (damage, reject, shortage, extra items)
- Financial impact

**Filters:**
- Date range
- Vendor
- Variance threshold (e.g., > 5%)

**Use Case:** Identify vendors with consistent shortages, improve forecasting

---

### **2. WASTAGE REPORTS**

**Purpose:** Track wastage across all stages, identify cost impact, improve processes

---

#### **2.1 Wastage Summary Report**

**Data Included:**
- Total wastage (quantity and value)
- By stage (receiving, grading, packing, cold storage, customer)
- By wastage type (damage, reject, QC, overfill, customer claim)
- Cost allocation (Farm vs Us)
- Trend over time (daily, weekly, monthly)

**Filters:**
- Date range
- Stage (select multiple)
- Wastage type (select multiple)
- Cost allocation (Farm, Us, Both)

**Use Case:** Understand total wastage impact, allocate costs correctly

---

#### **2.2 Wastage by Farm Report**

**Data Included:**
- Farm name
- Total wastage (quantity)
- Damage rate (%)
- Reject rate (%)
- Cost impact (₹)
- Comparison across farms (ranking)

**Filters:**
- Date range
- Farm (select multiple)
- Wastage type (damage, reject)

**Use Case:** Identify problematic farms, negotiate quality standards, improve sourcing

---

#### **2.3 Wastage by Product Report**

**Data Included:**
- Item name
- Total wastage (quantity and %)
- By stage (where most wastage occurs for this item)
- Cost impact
- Comparison across products (ranking)

**Filters:**
- Date range
- Item (select multiple)
- Stage (select multiple)

**Use Case:** Identify high-wastage products, improve handling, adjust sourcing

---

#### **2.4 Wastage by Stage Report**

**Data Included:**
- Stage (receiving, grading, packing, cold storage, customer)
- Total wastage (quantity and %)
- Top reasons (damage, reject, overfill, etc.)
- Cost impact
- Trend over time

**Filters:**
- Date range
- Stage (select multiple)

**Use Case:** Identify bottlenecks, improve processes (e.g., if packing overfill high → training needed)

---

#### **2.5 Wastage Cost Impact Report**

**Data Included:**
- Total wastage cost (₹)
- Farm responsibility (₹) vs Our cost (₹)
- By stage (cost breakdown)
- By product (cost breakdown)
- Impact on profitability (% of revenue)

**Filters:**
- Date range
- Cost allocation (Farm, Us)

**Use Case:** Financial planning, cost control, pricing adjustments

---

#### **2.6 Repacking Report**

**Data Included:**
- Repacked batches (B###R)
- Parent batch (original)
- Reason for repacking
- Quantity repacked
- Wastage from repacking
- Date repacked
- Days to sell (repacked batch FIFO priority)

**Filters:**
- Date range
- Batch number

**Use Case:** Monitor repacking frequency, improve cold storage management

---

### **3. INVENTORY REPORTS**

**Purpose:** Track stock levels, turnover, aging, valuation

---

#### **3.1 Current Stock Report**

**Data Included:**
- Item name
- Quantity in stock
- Location (packed goods, cold storage, etc.)
- Batch numbers (list)
- Oldest batch date (aging)
- Value (₹)

**Filters:**
- Item (select multiple)
- Location (select multiple)
- Stock level (low stock only, all)

**Export:** CSV, Excel

**Use Case:** Daily stock check, reorder planning

---

#### **3.2 Stock Movement Report**

**Data Included:**
- Date range
- Item
- Opening stock
- Stock in (from packing)
- Stock out (allocated to SOs)
- Adjustments (if any)
- Closing stock

**Filters:**
- Date range
- Item (select multiple)

**Use Case:** Understand stock flow, reconcile inventory

---

#### **3.3 Batch Age Report**

**Data Included:**
- Batch number
- Item
- Quantity
- Packing date
- Age (days in inventory)
- Status (available, allocated, delivered)
- Expiry date (if applicable)

**Filters:**
- Age threshold (e.g., > 7 days)
- Item
- Status

**Use Case:** Identify slow-moving batches, prioritize sales, reduce spoilage

---

#### **3.4 Stock Turnover Report**

**Data Included:**
- Item
- Average stock level
- Total sold (quantity)
- Turnover rate (times/month)
- Days to sell (average)

**Filters:**
- Date range
- Item (select multiple)

**Use Case:** Optimize stock levels, identify fast/slow movers

---

#### **3.5 Low Stock Alert Report**

**Data Included:**
- Item name
- Current stock
- Reorder level
- Days until stock-out (estimated)
- Incoming POs (if any)

**Filters:**
- Below reorder level only

**Use Case:** Proactive reordering, prevent stock-outs

---

#### **3.6 Stock Valuation Report**

**Data Included:**
- Item
- Quantity in stock
- Unit cost (from PO/GRN)
- Total value (₹)
- By location (breakdown)
- Total inventory value

**Filters:**
- Date (valuation as of date)
- Location (select multiple)

**Use Case:** Financial reporting, balance sheet, insurance

---

### **4. SALES REPORTS**

**Purpose:** Analyze B2B and B2C sales, customer performance, product trends

---

#### **4.1 Sales Summary Report**

**Data Included:**
- Date range
- Total sales (₹)
- SO count
- By customer type (B2B vs B2C)
- By customer (top customers)
- By product (top products)
- Average order value

**Filters:**
- Date range
- Customer type (B2B, B2C, Both)
- Customer (select multiple)

**Export:** CSV, Excel, PDF

---

#### **4.2 Customer Analysis Report**

**Data Included:**
- Customer name
- Total orders (count)
- Total sales (₹)
- Average order value
- Order frequency (orders/month)
- Last order date
- Lifetime value (LTV)

**Ranking:**
- Top customers by value
- Most frequent customers

**Filters:**
- Date range
- Customer type (B2B, B2C)
- Minimum order count

**Use Case:** Identify VIP customers, retention strategies, upsell opportunities

---

#### **4.3 Product Performance Report**

**Data Included:**
- Item name
- Units sold
- Sales value (₹)
- Contribution to total sales (%)
- Growth vs previous period (%)
- Seasonality pattern

**Filters:**
- Date range
- Item (select multiple)
- Customer type (B2B, B2C)

**Use Case:** Product strategy, inventory planning, pricing

---

#### **4.4 B2B vs B2C Comparison Report**

**Data Included:**
- Sales comparison:
  - B2B: Total sales, order count, average order value
  - B2C: Total sales, order count, average order value
- Product mix (which products sell more in B2B vs B2C)
- Profitability (if margin data available)
- Growth trends

**Filters:**
- Date range

**Use Case:** Channel strategy, marketing focus, resource allocation

---

### **5. OPERATIONAL REPORTS**

**Purpose:** Evaluate operational efficiency, fulfillment, process performance

---

#### **5.1 Order Fulfillment Report**

**Data Included:**
- SO count
- Fulfilled on time (%)
- Delayed (%)
- Average fulfillment time (SO created → delivered)
- By customer (fulfillment performance)
- Reasons for delay (if tracked)

**Filters:**
- Date range
- Customer type (B2B, B2C)
- Status (on-time, delayed, all)

**Use Case:** Improve fulfillment speed, identify bottlenecks

---

#### **5.2 Grading Efficiency Report**

**Data Included:**
- Batch number
- Total received (from GRN)
- Grade A, B, C quantities (%)
- QC wastage (quantity and %)
- Grading staff performance

**Filters:**
- Date range
- Item (select multiple)
- Grading staff (select multiple)

**Use Case:** Improve grading accuracy, staff training, reduce QC wastage

---

#### **5.3 Packing Yield Report**

**Data Included:**
- Batch number
- Item
- Gross quantity (from grading)
- Expected packs (calculated)
- Actual packs (from packing)
- Overfill wastage (quantity and %)
- Packing staff performance

**Filters:**
- Date range
- Item (select multiple)
- Packing staff (select multiple)

**Use Case:** Optimize packing process, reduce overfill, staff training

---

#### **5.4 Delivery Performance Report**

**Data Included:**
- Delivery date
- Routes planned
- Deliveries completed
- On-time deliveries (%)
- Average delivery time
- Failed deliveries (customer not home)
- Distance traveled
- Fuel efficiency (future)

**Filters:**
- Date range
- Driver (select multiple)
- Route (select multiple)

**Use Case:** Optimize routes, improve on-time delivery, reduce costs

---

### **6. FINANCIAL REPORTS (Zoho Export)**

**Purpose:** Export data formatted for Zoho Books, financial analysis

---

#### **6.1 PO Export for Zoho (Bills)**

**Data Included:**
- Completed POs
- Formatted for Zoho Bills import
- Vendor details
- Items, quantities, prices
- Taxes
- Damage/Reject deductions (for debit notes)

**Filters:**
- Date range
- Vendor (select multiple)
- Exported vs Not Exported

**Export:** CSV/Excel (Zoho import format)

**Use Case:** Streamline accounting, ensure accurate farm payments

---

#### **6.2 SO Export for Zoho (Invoices)**

**Data Included:**
- Completed SOs
- Formatted for Zoho Invoices import
- Customer details
- Items, quantities, prices
- Taxes
- Delivery details

**Filters:**
- Date range
- Customer (select multiple)
- Exported vs Not Exported

**Export:** CSV/Excel (Zoho import format)

**Use Case:** Streamline invoicing, ensure accurate customer billing

---

#### **6.3 Profitability Report**

**Data Included:**
- Revenue (from SOs)
- Cost of Goods Sold (from POs/GRNs)
- Gross margin (₹ and %)
- By product (profitability by item)
- By customer (profitability by customer)

**Filters:**
- Date range
- Product (select multiple)
- Customer (select multiple)

**Use Case:** Understand profitability, pricing strategy, focus on high-margin products

**Note:** Requires cost allocation from POs and GRNs

---

### **7. BATCH TRACEABILITY REPORTS**

**Purpose:** Complete traceability from farm to customer

---

#### **7.1 Batch History Report**

**Data Included:**
- Batch number (input)
- Complete journey:
  - PO details (farm, date, items, quantities)
  - GRN details (received, damage, reject, accepted)
  - Grading results (A/B/C)
  - Packing details (quantities, overfill)
  - Allocated to which SOs
  - Delivered to which customers (names, dates)
  - Any customer complaints (tickets)
  - All wastage events linked to batch
  - All photos across journey

**Use Case:** Customer complaint investigation, recall management, quality assurance

---

#### **7.2 Customer Batch Report (Reverse Trace)**

**Data Included:**
- Customer name (input)
- SO number (input)
- Which batches were delivered
- Source farms for each batch
- Receiving dates
- Quality issues (if any)

**Use Case:** Customer inquiry (which farm supplied their produce), quality investigation

---

#### **7.3 Farm Batch Report**

**Data Included:**
- Farm name (input)
- All batches from this farm
- Receiving outcomes (damage, reject rates)
- Customer feedback (tickets related to these batches)
- Overall farm performance

**Use Case:** Farm evaluation, sourcing decisions, quality discussions

---

### **8. LOGISTICS REPORTS**

**Purpose:** Route efficiency, delivery performance, vehicle utilization

---

#### **8.1 Route Efficiency Report**

**Data Included:**
- Route ID/name
- Deliveries on route
- Total distance
- Total time
- Deliveries per km
- On-time deliveries (%)
- Optimization score (compared to ideal route)

**Filters:**
- Date range
- Route (select multiple)
- Driver (select multiple)

**Use Case:** Optimize routes, reduce distance/time, improve efficiency

---

#### **8.2 Driver Performance Report**

**Data Included:**
- Driver name
- Routes assigned
- Deliveries completed
- On-time delivery (%)
- Average delivery time
- Distance covered
- Fuel consumption (future)

**Filters:**
- Date range
- Driver (select multiple)

**Use Case:** Driver evaluation, training needs, performance management

---

#### **8.3 Vehicle Utilization Report**

**Data Included:**
- Vehicle (in-house fleet)
- Days used
- Routes assigned
- Deliveries completed
- Capacity utilization (%)
- Maintenance schedule

**Filters:**
- Date range
- Vehicle (select multiple)

**Use Case:** Fleet management, capacity planning, maintenance scheduling

---

### **9. TICKET REPORTS**

**Purpose:** Customer service performance, issue tracking

---

#### **9.1 Ticket Summary Report**

**Data Included:**
- Total tickets (B2B, B2C, Internal)
- By status (new, in-progress, resolved, closed)
- By priority (urgent, high, medium, low)
- By category (order issues, quality, returns, inquiries)
- Average resolution time
- SLA adherence (%)

**Filters:**
- Date range
- Ticket type (B2B, B2C, Internal)
- Status, priority, category

**Use Case:** Monitor customer service performance, identify trends

---

#### **9.2 Quality Issue Report (from Tickets)**

**Data Included:**
- Quality tickets only
- By product (which products have most issues)
- By farm (which farms' produce causes issues)
- By customer (repeat complainers)
- Resolution (credit, replacement, refund)
- Cost impact

**Filters:**
- Date range
- Product (select multiple)
- Farm (select multiple)

**Use Case:** Improve quality, inform sourcing decisions, reduce complaints

---

#### **9.3 Agent Performance Report**

**Data Included:**
- Agent/staff name
- Tickets assigned
- Tickets resolved
- Average resolution time
- Customer satisfaction score (if tracked)

**Filters:**
- Date range
- Agent (select multiple)

**Use Case:** Staff performance evaluation, training needs

---

### **10. CUSTOM REPORTS (Future Enhancement)**

**Purpose:** User-defined reports

**Features:**
- Drag-and-drop report builder
- Select data sources (tables)
- Select fields (columns)
- Apply filters
- Group by (dimensions)
- Aggregate (sum, average, count)
- Visualize (charts, graphs)
- Save report template
- Schedule report (daily, weekly, monthly)

**Use Case:** Ad-hoc analysis, unique business needs

---

## **REPORT FEATURES (Universal)**

### **Common Features Across All Reports:**

**1. Date Range Selection:**
- Pre-defined ranges: Today, Yesterday, This Week, Last Week, This Month, Last Month, This Quarter, This Year
- Custom range: From Date → To Date

**2. Filters:**
- Multi-select dropdowns
- Search/autocomplete
- Cascading filters (e.g., select vendor → see only their items)

**3. Export Options:**
- **CSV:** Raw data, Excel-compatible
- **Excel (.xlsx):** Formatted, with charts (where applicable)
- **PDF:** Professional report format, printable

**4. Visualizations:**
- Tables (sortable, paginated)
- Bar charts
- Line charts (trends)
- Pie charts (distribution)
- Heatmaps (patterns)

**5. Scheduling (Future):**
- Schedule report to run daily/weekly/monthly
- Auto-email to recipients
- Save to cloud storage

**6. Report History:**
- View previously run reports
- Re-download past reports
- Track who ran which report when (audit)

---

## **Technical Implementation**

### **Backend (FastAPI):**

**Report Endpoints:**
- `/api/reports/purchase/po-summary` - PO Summary
- `/api/reports/purchase/vendor-performance` - Vendor Performance
- `/api/reports/wastage/summary` - Wastage Summary
- `/api/reports/wastage/by-farm` - Wastage by Farm
- `/api/reports/inventory/current-stock` - Current Stock
- `/api/reports/sales/summary` - Sales Summary
- `/api/reports/sales/customer-analysis` - Customer Analysis
- `/api/reports/operational/fulfillment` - Order Fulfillment
- `/api/reports/batch/history` - Batch History
- `/api/reports/logistics/route-efficiency` - Route Efficiency
- `/api/reports/tickets/summary` - Ticket Summary
- (Similar endpoints for all report types)

**Universal Endpoints:**
- `/api/reports/{report_id}/export` - Export to CSV/Excel/PDF
- `/api/reports/{report_id}/schedule` - Schedule report
- `/api/reports/history` - View past reports

**Query Optimization:**
- Indexed database queries (fast retrieval)
- Caching (for frequently run reports)
- Pagination (large datasets)
- Background jobs (for slow reports)

---

### **Frontend (React):**

**Components:**
- `<ReportSelector />` - Choose report type
- `<ReportFilters />` - Dynamic filters per report
- `<DateRangePicker />` - Select date range
- `<ReportViewer />` - Display report (table/chart)
- `<ExportButtons />` - Download CSV/Excel/PDF
- `<ReportHistory />` - Past reports
- `<ScheduleReport />` - Schedule future runs (future)

**Report Builder (Future):**
- `<CustomReportBuilder />` - Drag-and-drop interface

---

### **Database (Supabase):**

**Report Storage:**
- `reports_run_history` table:
  - report_id, report_type, filters (JSON), run_by, run_at, file_url
- `scheduled_reports` table:
  - schedule_id, report_type, frequency, recipients, last_run_at, next_run_at

**Data Sources:**
- Pull from all operational tables (POs, GRNs, inventory, SOs, batches, wastage, tickets, etc.)
- Join tables as needed
- Pre-aggregated views (for performance)

---

## **Success Criteria**

**Operational:**
- ✅ All critical reports available
- ✅ Fast report generation (< 10 seconds for most reports)
- ✅ Easy export (one-click download)
- ✅ Mobile-friendly (view reports on phone/tablet)

**Business Intelligence:**
- ✅ Data-driven decision making
- ✅ Identify trends and patterns
- ✅ Improve operational efficiency
- ✅ Reduce costs (wastage, logistics)
- ✅ Increase profitability

**User Adoption:**
- ✅ Reports used daily/weekly
- ✅ Managers rely on reports for decisions
- ✅ Reports inform procurement, sales, operations

---

**End of Module 8 Documentation**

---

**END OF ALL MODULE DOCUMENTATION**

---

## **COMPLETE MODULE SUMMARY**

**Total Modules:** 9 Parent Modules (0-8)
- Module 0: Dashboard (Main/Global)
- Module 1: Inward Operations (4 child modules)
- Module 2: Inventory (3 child modules)
- Module 3: Outward Operations (4 child modules)
- Module 4: B2C Ops (3 child modules)
- Module 5: B2C Management (3 child modules)
- Module 6: Database Management (4 child modules)
- Module 7: Ticket Management (3 child modules)
- Module 8: Reporting (1 comprehensive module)

**Total Child Modules:** 25+

**Status:**
- ✅ Completed: Database Management (4 modules), B2C Ops (3 modules), B2C Management (2/3 modules), Internal Tickets
- 🔨 To Be Built: All other modules as per development sequence

**Estimated Total Timeline:** 20-22 weeks (5-6 months including testing and training)