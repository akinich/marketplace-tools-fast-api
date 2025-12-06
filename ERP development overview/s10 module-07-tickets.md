# MODULE 7: TICKET MANAGEMENT

**Document:** Step 10 - Module 7: Ticket Management  
**Filename:** 10-Module-07-Ticket-Management.md

---

## **Module Overview**

**Module Name:** Ticket Management  
**Module Type:** Parent Module  
**Child Modules:** 3 (B2B Tickets, B2C Tickets, Internal Tickets)  
**Priority:** LOW - Post-sale support, not blocking core operations

**Purpose:**  
Manage customer complaints, quality issues, returns, and internal ERP system issues through structured ticket workflows.

---

## **Module Characteristics**

**Ticket Types:**
- **B2B Tickets:** Hotels and restaurants (Module 7.1)
- **B2C Tickets:** Direct-to-home customers (Module 7.2)
- **Internal Tickets:** ERP system issues (Module 7.3 - Already exists in framework)

**Build Priority:**
- B2B and B2C tickets: Phase 7 (Weeks 16-17)
- Internal tickets: Already operational in framework

**Standalone Initially:**
- Can be built after core operational modules
- Not blocking inward/outward flows
- Enhances customer service post-launch

---

## **Internal Dashboard**

**Purpose:** Overview of all ticket activity

**Key Metrics:**
- Open tickets count (by type: B2B, B2C, Internal)
- Tickets by status (new, in-progress, resolved, closed)
- Tickets by priority (low, medium, high, urgent)
- Average resolution time
- Overdue tickets (past SLA)
- Tickets created today/this week
- Tickets by category (order issues, quality, returns, system)

**Visualizations:**
- Ticket status distribution (pie chart)
- Ticket volume trend (line chart)
- Resolution time by type (bar chart)
- Top issue categories
- Agent performance (tickets resolved)

**Quick Actions:**
- Create new ticket (B2B, B2C, Internal)
- View my assigned tickets
- View overdue tickets
- View recent tickets

---

## **CHILD MODULE 7.1: B2B TICKETS (Hotels/Restaurants)**

### **Overview**

**Purpose:** Manage customer issues for B2B clients (hotels and restaurants)

**Build Priority:** LOW - Build in Phase 7 (Week 16)  
**Estimated Duration:** 3-5 days

**Status:** ⚠️ **TO BE DETAILED** - Workflow discussion needed before build

---

### **High-Level Requirements (To Be Refined)**

#### **1. Ticket Categories**

**Issue Types:**
- **Order Issues:**
  - Wrong items delivered
  - Wrong quantities
  - Missing items
  - Late delivery
  - Early delivery (also a problem sometimes)
- **Quality Issues:**
  - Produce quality not up to standard
  - Damaged items
  - Over-ripe/under-ripe
  - Foreign objects
- **Returns/Refunds:**
  - Full return request
  - Partial return
  - Credit request
  - Refund request
- **General Inquiries:**
  - Product availability questions
  - Pricing queries
  - Delivery schedule questions
  - Account issues

---

#### **2. Ticket Creation**

**Created By:**
- Internal staff (on behalf of customer via phone/WhatsApp)
- Customers directly (if customer portal exists - future)

**Required Fields:**
- Customer (select from customers_zoho)
- Related SO/Invoice (link to Module 3.1/3.3)
- Issue category (dropdown)
- Priority (low, medium, high, urgent)
- Description (text)
- Photos (optional for general inquiries, mandatory for quality issues)
- Requested resolution (credit, replacement, refund, etc.)

**Optional Fields:**
- Batch number (for quality issues)
- Specific items affected
- Delivery date (for delivery issues)
- Preferred resolution date

---

#### **3. Link to SO/Invoice**

**Context from SO:**
- What was ordered
- What was delivered (allocated batches)
- Delivery date
- Customer details
- Items and quantities

**Benefits:**
- Complete order history visible
- Quick investigation
- Accurate issue resolution

---

#### **4. Ticket Workflow**

**Status Options:**
1. **New:** Just created, not yet assigned
2. **Assigned:** Assigned to staff member
3. **In Progress:** Being investigated/resolved
4. **Awaiting Customer:** Need customer input
5. **Resolved:** Issue resolved, awaiting closure
6. **Closed:** Customer confirmed resolution

**Status Transitions:**
```
New → Assigned → In Progress → Resolved → Closed
                    ↓
              Awaiting Customer → In Progress
```

---

#### **5. Priority Levels**

**Priority Options:**
- **Urgent:** Critical issue, major client, immediate attention (SLA: 2 hours)
- **High:** Significant issue, needs quick resolution (SLA: 4 hours)
- **Medium:** Standard issue (SLA: 24 hours)
- **Low:** Minor inquiry (SLA: 48 hours)

**Auto-Escalation:**
- If not resolved within SLA → Auto-escalate priority
- Notify manager

---

#### **6. Assignment & Routing**

**Assignment:**
- Manual assignment (manager assigns to staff)
- Auto-assignment (round-robin or workload-based)
- Self-assignment (staff can pick tickets)

**Team/Agent:**
- Assign to specific user
- Or assign to team (any team member can handle)

---

#### **7. Resolution Actions**

**Possible Resolutions:**
- **Credit Note:** Issue credit to customer account (linked to Zoho)
- **Replacement:** Schedule re-delivery with replacement items
- **Refund:** Process refund (tracked in Zoho)
- **No Action:** Issue not valid, close ticket
- **Goodwill:** Send complimentary items (build relationship)

**Documentation:**
- Resolution notes (what was done)
- Photos (if replacement sent)
- Credit note number (if issued)
- Approval (if manager approval required)

---

#### **8. Quality Issue Investigation**

**For Quality Complaints:**
- Link to batch number (Module 2.2)
- View batch history:
  - Source farm
  - Receiving damage/reject
  - Grading results
  - Other customers who received same batch
- Check if other complaints for same batch
- Investigate farm quality (vendor performance)

**Actions:**
- If farm issue → Flag farm, contact farm
- If packing issue → Review packing process
- If delivery issue → Review logistics
- If customer error → Educate customer

---

#### **9. Customer Communication**

**Communication Log:**
- Track all interactions (calls, emails, WhatsApp)
- Timestamp each communication
- Note who communicated
- Attach files (emails, screenshots)

**Templates:**
- Pre-defined response templates
- For common issues (late delivery, quality, returns)
- Personalize and send

---

#### **10. Ticket Dashboard (B2B)**

**List View:**
- All B2B tickets
- Filter by status, priority, category, customer
- Sort by creation date, priority, SLA
- Search by ticket number, customer name

**Metrics:**
- My assigned tickets
- Overdue tickets
- Resolved today
- Average resolution time

---

### **To Be Discussed**

- Detailed ticket workflow (states, transitions, approvals)
- SLA definitions and auto-escalation rules
- Assignment logic (manual vs auto)
- Manager approval for credits/refunds
- Customer portal (self-service) - future
- Integration with CRM (if any)
- Notification preferences (email, SMS, WhatsApp)
- Ticket categories and subcategories (finalize list)
- Resolution templates and processes
- Reporting and analytics needs

---

### **Technical Implementation (Proposed)**

**Backend (FastAPI):**
- `/api/tickets/b2b/create` - Create ticket
- `/api/tickets/b2b/list` - List tickets with filters
- `/api/tickets/b2b/{id}` - Get ticket details
- `/api/tickets/b2b/{id}/update` - Update ticket
- `/api/tickets/b2b/{id}/assign` - Assign ticket
- `/api/tickets/b2b/{id}/resolve` - Resolve ticket
- `/api/tickets/b2b/{id}/close` - Close ticket
- `/api/tickets/b2b/{id}/comments` - Add comments
- `/api/tickets/b2b/{id}/attachments` - Upload files

**Frontend (React):**
- `<B2BTicketCreator />` - Create ticket form
- `<B2BTicketList />` - List view with filters
- `<B2BTicketDetail />` - Ticket details and actions
- `<TicketTimeline />` - Activity timeline
- `<CommunicationLog />` - Customer interactions
- `<BatchInvestigation />` - Link to batch history

**Database (Supabase):**
- `tickets_b2b` table:
  - ticket_id, customer_id, so_id, invoice_id, category, priority, status, description, created_at, assigned_to, resolved_at, closed_at
- `ticket_comments` table:
  - comment_id, ticket_id, user_id, comment_text, timestamp
- `ticket_attachments` table:
  - attachment_id, ticket_id, file_url, filename, uploaded_by, timestamp

---

### **Testing Checklist (To Be Built)**

- [ ] Create B2B ticket
- [ ] Link ticket to SO/Invoice
- [ ] Upload photos (quality issues)
- [ ] Assign ticket to staff
- [ ] Update ticket status
- [ ] Add comments and communication log
- [ ] Link to batch number (investigation)
- [ ] Resolve ticket (credit, replacement, refund)
- [ ] Close ticket
- [ ] SLA tracking and auto-escalation
- [ ] Filter and search tickets
- [ ] Manager approval workflow (if needed)
- [ ] Mobile responsiveness

---

## **CHILD MODULE 7.2: B2C TICKETS (Direct-to-Home)**

### **Overview**

**Purpose:** Manage customer issues for B2C customers (direct-to-home)

**Build Priority:** LOW - Build in Phase 7 (Week 16-17)  
**Estimated Duration:** 3-5 days

---

### **Core Features**

#### **1. Ticket Categories**

**Issue Types:** (Similar to B2B)
- **Order Issues:**
  - Wrong items delivered
  - Wrong quantities
  - Missing items
  - Late delivery
  - Delivery not received
- **Quality Issues:**
  - Produce quality not acceptable
  - Damaged items
  - Spoiled/rotten items
- **Returns/Refunds:**
  - Full return request
  - Partial return
  - Refund request
- **General Inquiries:**
  - Track my order
  - Product questions
  - Account/subscription issues

---

#### **2. Customer Claim Window Policy**

**Policy:** Customer must raise issue within stipulated time

**Time Window:**
- From delivery → End of delivery day
- Example: Delivered at 10 AM → Can raise issue until midnight same day

**Implementation:**
- Tickets can reference past deliveries (backdated entry allowed)
- System doesn't lock ticket creation
- But system flags if ticket is **outside policy window**

**Late Ticket Handling:**
- Ticket flagged: "Outside Policy Window"
- Visible to staff for decision
- No automatic rejection
- Manager can approve exception

---

#### **3. Mandatory Photos for Damage/Wastage**

**Photo Requirements:**
- **Mandatory for quality issues:** Photos of damaged/spoiled produce
- Cannot submit ticket without photos
- Multiple photos allowed
- Timestamped
- Stored in Supabase Storage

**Photo Usage:**
- Evidence for resolution
- Track pattern (recurring issues with specific batches)
- Share with farms (if farm quality issue)
- Link to wastage tracking (Module 2.3)

---

#### **4. Ticket Creation**

**Created By:**
- Internal staff (on behalf of customer via phone/WhatsApp/email)
- Customers directly (via customer portal - future)

**Required Fields:**
- Customer name, email, phone (manual entry or select from database)
- Related WooCommerce Order (or SO if integrated)
- Delivery date (actual date of delivery)
- Ticket creation date (today - auto-filled)
- Issue category (dropdown)
- Description (text)
- **Photos (MANDATORY for quality/damage issues)**

**System Calculates:**
- Within policy window: Yes/No (based on delivery date vs today)
- Days late (if outside window)

**Optional Fields:**
- Batch number (if known - future integration)
- Specific items affected
- Requested resolution

---

#### **5. Link to WooCommerce Order (or SO)**

**Current (No Integration):**
- Enter WooCommerce order number manually
- Staff references order separately

**Future (After Integration - Phase 3):**
- Select order from system
- Pull order details automatically
- Link to batches allocated
- View complete order history

---

#### **6. Ticket Workflow**

**Status Options:** (Same as B2B)
1. **New:** Just created
2. **Assigned:** Assigned to staff
3. **In Progress:** Being investigated
4. **Awaiting Customer:** Need more info
5. **Resolved:** Issue resolved
6. **Closed:** Customer confirmed

**Priority:**
- Urgent: Major issue, VIP customer
- High: Needs quick resolution
- Medium: Standard
- Low: Minor inquiry

---

#### **7. Resolution Actions**

**Possible Resolutions:**
- **Refund:** Process refund via payment gateway (WooCommerce integration)
- **Replacement:** Schedule re-delivery
- **Store Credit:** Issue credit for future purchase (WooCommerce coupon)
- **No Action:** Issue not valid
- **Goodwill:** Send extra items next order

**Documentation:**
- Resolution notes
- Refund/credit confirmation
- Photos (if replacement sent)

---

#### **8. Customer Communication**

**Communication Channels:**
- Phone
- WhatsApp (primary for B2C)
- Email

**Communication Log:** (Same as B2B)
- Track all interactions
- Timestamp and user
- Attach files

---

#### **9. Late Ticket Handling**

**Flagged Tickets:**
- System shows: "⚠️ Outside Policy Window (2 days late)"
- Staff visibility: Know it's a late claim
- Decision: Manager discretion to approve or reject

**No System Lock:**
- Staff can still create and process ticket
- Flexibility for genuine cases
- Audit trail maintained

---

#### **10. B2C Ticket Dashboard**

**List View:**
- All B2C tickets
- Filter by status, priority, within/outside policy window
- Sort by creation date, priority
- Search by ticket number, customer name, order number

**Metrics:**
- Late tickets (outside window)
- Resolved today
- Average resolution time

---

### **Technical Implementation**

**Backend (FastAPI):**
- `/api/tickets/b2c/create` - Create ticket
- `/api/tickets/b2c/list` - List tickets with filters
- `/api/tickets/b2c/{id}` - Get ticket details
- `/api/tickets/b2c/{id}/update` - Update ticket
- `/api/tickets/b2c/{id}/photos` - Upload mandatory photos
- (Similar endpoints as B2B)

**Frontend (React):**
- `<B2CTicketCreator />` - Create form (with mandatory photo upload)
- `<B2CTicketList />` - List view (show late ticket flags)
- `<B2CTicketDetail />` - Ticket details
- `<PolicyWindowIndicator />` - Visual indicator (within/outside window)
- `<PhotoGallery />` - Display uploaded photos

**Database (Supabase):**
- `tickets_b2c` table:
  - Similar to B2B, plus:
  - delivery_date (actual delivery date)
  - ticket_creation_date (when ticket created)
  - within_policy_window (boolean, calculated)
  - days_late (integer, if outside window)
  - woo_order_number (if available)
- `ticket_photos` table (or use Supabase Storage with references)

---

### **Testing Checklist**

- [ ] Create B2C ticket with mandatory photos
- [ ] Test photo upload (cannot submit without photos for damage issues)
- [ ] Calculate policy window (within/outside)
- [ ] Flag late tickets
- [ ] Allow backdated entry (yesterday's delivery, ticket today)
- [ ] Link to WooCommerce order (manual entry)
- [ ] Assign and resolve ticket
- [ ] Add communication log
- [ ] Mobile responsiveness (customers may report on phone)

---

## **CHILD MODULE 7.3: INTERNAL TICKETS (ERP System Issues)**

### **Overview**

**Purpose:** Track ERP system issues, bugs, and feature requests

**Status:** ✅ **ALREADY EXISTS IN FRAMEWORK**  
**Priority:** OPERATIONAL - Already in use

---

### **Core Features (Existing)**

#### **1. Ticket Categories**

**Issue Types:**
- Bug reports (system errors, crashes)
- Feature requests (new functionality)
- Enhancements (improvements to existing features)
- User access issues (login, permissions)
- Data issues (sync problems, data errors)
- Performance issues (slow loading, timeouts)
- Training requests (how-to questions)

---

#### **2. Ticket Creation**

**Created By:**
- All users (report issues they encounter)
- Admins (on behalf of users)

**Fields:**
- Title (brief description)
- Category (bug, feature, enhancement, etc.)
- Priority (low, medium, high, critical)
- Description (detailed explanation)
- Steps to reproduce (for bugs)
- Expected behavior (for bugs)
- Actual behavior (for bugs)
- Screenshots/attachments
- Affected module (which part of ERP)

---

#### **3. Ticket Workflow**

**Status:**
- New → Triaged → In Progress → Resolved → Closed

**Assignment:**
- Assigned to development team
- Or specific developer

---

#### **4. Integration with Development Planning Module**

**Link to Roadmap:**
- Feature requests → Added to development roadmap
- Enhancements → Prioritized for future releases
- Bugs → Fixed in upcoming patch

**Announcements:**
- When feature/fix released → Notify ticket creator
- Link ticket to release notes

---

#### **5. Internal Ticket Dashboard**

**Metrics:**
- Open bugs (critical, high, medium, low)
- Feature requests in backlog
- Average resolution time
- Bugs fixed this week

**For Users:**
- My tickets
- Recent tickets
- Resolved tickets

---

### **No Additional Build Required**

**Status:** Already operational in framework, just needs to be confirmed integrated with new Marketplace Tools modules.

---

## **Cross-Module Integration**

### **Ticket Management Integration Points:**

**With Batch Tracking (Module 2.2):**
- B2B/B2C tickets link to batch numbers
- Investigate quality issues via batch history
- Identify farm source, grading, packing issues

**With Wastage Tracking (Module 2.3):**
- Customer damage claims (B2B/B2C) logged as wastage events
- Photos from tickets → Wastage module
- Cost impact tracked

**With SO/Invoice (Module 3.1/3.3):**
- Tickets link to specific orders
- Order history provides context
- Resolution (credit, refund) impacts invoicing

**With Customer Database (Module 6.2):**
- Customer details from database
- Track customer complaint history
- Customer quality sensitivity (flag repeat complainers or high-standards customers)

**With Vendor Database (Module 6.3):**
- Farm quality issues → Flag vendor
- Vendor performance impacted by complaints
- Inform procurement decisions

---

## **Success Criteria**

**Operational:**
- ✅ All customer issues tracked and resolved
- ✅ SLA adherence (resolve within policy time)
- ✅ Complete audit trail (who, what, when)
- ✅ Pattern identification (recurring issues)

**Customer Satisfaction:**
- ✅ Quick resolution (meet SLA)
- ✅ Fair policy enforcement (with flexibility)
- ✅ Clear communication throughout

**Business Intelligence:**
- ✅ Identify quality issues (farm, product, process)
- ✅ Reduce repeat complaints
- ✅ Improve customer retention

---

**End of Module 7 Documentation**