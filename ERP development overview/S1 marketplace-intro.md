# MARKETPLACE TOOLS - PROJECT INTRODUCTION

**Document:** Step 1 - Introduction & Tech Stack  
**Filename:** 01-Introduction-TechStack.md

---

## **Project Overview**

**Project Name:** Marketplace Tools  
**Business Type:** Farm-to-Fork Operations  
**Business Model:** 
- B2B: Hotels and Restaurants
- B2C: Direct-to-Home via WooCommerce

**Current Challenge:** Fragmented systems across Google Sheets, handwritten notes, and Zoho Books

**Solution Goal:** Centralized platform for all company operations with seamless Zoho Books integration

---

## **Technical Stack**

### **Framework (Already Built & Ready)**

**Backend:** FastAPI (Python)
- REST API architecture
- Existing authentication system
- Communication infrastructure (Telegram, SMTP, Webhooks, WebSockets)
- Swagger API documentation

**Frontend:** React
- Mobile-responsive design (mobile-first approach)
- Tailwind CSS for styling
- Touch-friendly interfaces
- Progressive Web App ready architecture

**Database:** Supabase
- PostgreSQL based
- Real-time features
- Row-level security
- Built-in storage for photos/documents

**Future Enhancement:** Progressive Web App (Phase 2, 6-12 months post-launch)

---

## **Existing Framework Features**

1. **Authentication System**
   - Login page
   - Password reset functionality

2. **Admin Panel**
   - User management (Admin/User roles)
   - Module management (control user access)
   - Audit logs (track all user actions)

3. **Internal Ticketing System**
   - For ERP system issues and support
   - Feature requests and bug reports

4. **Development Planning Module**
   - Track ERP development roadmap
   - Feature announcements and timelines

5. **Settings Management**
   - System-wide configuration
   - Module-specific settings

6. **Communication Infrastructure**
   - Telegram integration
   - SMTP (email)
   - Webhooks
   - WebSockets (real-time updates)
   - API framework

7. **Documentation & Help**
   - Swagger API docs (auto-generated)
   - Built-in help section

8. **Dynamic Dashboard**
   - Already coded
   - Aggregates data from module dashboards
   - User-specific views based on module assignments

---

## **Business Operations Context**

### **Company Profile**
- **Industry:** Fresh Produce (Farm-to-Fork)
- **Sourcing:** Multiple farms with varied pricing models (fixed and variable)
- **Processing:** Receiving → Grading → Sorting → Packing
- **Customers:** 
  - B2B: Hotels and restaurants (customer-specific pricing)
  - B2C: Direct consumers via WooCommerce
- **Team Size:** 5-10 users
- **Operating Days:** Monday to Saturday

### **Key Business Challenges**
- Batch traceability from farm to customer
- Wastage tracking across multiple stages
- Customer-specific and vendor-specific pricing
- Multi-location inventory management
- Integration between operations and accounting (Zoho Books)

---

## **Integration Strategy**

### **Zoho Books (Source of Truth for Master Data)**

**One-Way Sync (Zoho → Marketplace Tools):**
- Items/Products
- Customers (B2B)
- Vendors/Farms

**Strategy:**
- Mirror copy in Marketplace Tools database
- Extend with operational fields (tags, categories)
- Master data read-only in Marketplace Tools
- Only operational extensions editable

**Transaction Export (Marketplace Tools → Zoho):**
- **Phase 1:** CSV/Excel export for manual upload
  - Purchase Orders → Bills
  - Sales Orders → Invoices
  - Testing and validation period
- **Phase 2 (Future):** Direct API integration

### **WooCommerce (B2C Platform)**
- Order extraction via API
- Inventory sync (manual in Phase 1)
- Item mapping to Zoho Books

---

## **Development Principles**

1. **API-First Architecture**
   - All data operations via REST API
   - Frontend as stateless consumer
   - Enables future mobile apps

2. **Mobile-Responsive Design**
   - Built mobile-first from day 1
   - Tailwind responsive utilities
   - Touch-friendly (minimum 44px tap targets)
   - Works on tablets at warehouse/dock

3. **Performance Optimized**
   - Code splitting
   - Lazy loading
   - Fast initial load times

4. **Error Handling**
   - Graceful network failure handling
   - Retry mechanisms
   - User-friendly error messages

5. **Audit Trail**
   - Every action logged
   - User accountability
   - Complete traceability

6. **Photo Documentation**
   - Wastage evidence
   - Quality issues
   - Customer complaints
   - Stored in Supabase storage

---

## **User Roles & Access**

**Current Roles:**
- **Admin:** Full access, user management, pricing configuration
- **User:** Operational access based on module assignments

**Future Consideration:**
- **Manager:** Intermediate role with approval workflows

**Access Control:**
- Module-based visibility
- Dashboard shows only assigned modules
- Role-based permissions per module
- Audit logs track all actions

---

## **Currency & Localization**

- **Single Currency:** INR (Indian Rupees)
- **No Multi-Currency Support:** Simplified pricing and accounting
- **Location:** Operations based in India

---

## **Go-Live Strategy**

**Approach:** Complete system before launch
- Not rolling out modules incrementally
- Build full inward + outward flow
- Test end-to-end before going live
- B2C tools already migrated and functional

**Rationale:**
- Avoid partial data in multiple systems
- Complete workflow validation
- User training on full system
- Clean cutover from current processes

---

## **Success Metrics**

**Operational:**
- Eliminate manual data entry between systems
- Reduce order processing time
- Improve inventory accuracy
- Reduce wastage through better tracking

**Financial:**
- Better cost tracking (wastage, farm pricing)
- Accurate billing (no discrepancies)
- Improved cash flow (faster invoicing)

**User Experience:**
- Single login for all operations
- Mobile-friendly access
- Real-time data visibility
- Reduced training time (unified interface)

**Business Intelligence:**
- Farm performance insights
- Wastage pattern identification
- Customer behavior analysis
- Operational bottleneck identification