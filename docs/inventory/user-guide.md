# Inventory Module - User Guide

**Version:** 1.5.0
**Audience:** Farm Operators, Inventory Managers, Production Staff

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Items](#managing-items)
4. [Stock Operations](#stock-operations)
5. [Purchase Orders](#purchase-orders)
6. [Suppliers & Categories](#suppliers--categories)
7. [Alerts & Monitoring](#alerts--monitoring)
8. [Stock Adjustments](#stock-adjustments)
9. [Reports & History](#reports--history)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Inventory Module

1. Log in to the Farm Management System
2. Navigate to **Inventory** from the main menu
3. You'll land on the Dashboard showing current inventory status

### Navigation

**Main Pages:**
- **Dashboard** - Overview and key metrics
- **Items** - Item master catalog
- **Stock Operations** - Add/use stock
- **Current Stock** - Real-time stock levels
- **Purchase Orders** - PO management
- **Suppliers** - Supplier information
- **Categories** - Category management
- **Alerts** - Low stock & expiry warnings
- **Adjustments** - Stock corrections
- **Transaction History** - Complete audit trail
- **Analytics** - Reports and insights

---

## Dashboard Overview

The dashboard provides at-a-glance information about your inventory.

### Key Metrics

**Inventory Status:**
- **Total Items:** All items in catalog
- **Active Items:** Items currently in use
- **Total Stock Value:** Cost-based valuation (₹)
- **Low Stock Items:** Items below reorder threshold
- **Expiring Soon:** Batches expiring within 30 days

**Purchase Orders:**
- **Pending POs:** Orders awaiting fulfillment
- **Recent Activity:** Transactions in last 7 days

### Alert Indicators

- 🔴 **Red:** Critical (very low stock, expiring < 7 days)
- 🟡 **Yellow:** Warning (low stock, expiring 7-30 days)
- 🟢 **Green:** Normal operation

---

## Managing Items

### Creating a New Item

**Scenario:** You're adding a new feed type to your inventory.

**Steps:**

1. Go to **Items** page
2. Click **+ New Item** button
3. Fill in the form:
   - **Item Name:** Descriptive name (e.g., "Premium Fish Feed Pellets 3mm")
   - **SKU:** Unique identifier (e.g., "FEED-PELLET-3MM")
   - **Category:** Select from dropdown OR type new category
   - **Unit:** Measurement unit (kg, liters, pieces, boxes, etc.)
   - **Default Supplier:** Select primary supplier (optional)
   - **Reorder Threshold:** Alert level (e.g., 500 kg)
   - **Min Stock Level:** Ideal minimum (e.g., 1000 kg)
4. Click **Save**

**Tips:**
- Use consistent SKU naming (e.g., CATEGORY-TYPE-VARIANT)
- Set reorder threshold = 2-4 weeks of average usage
- Min stock level = reorder threshold × 2

**Example:**
```
Item Name: Premium Fish Feed Pellets 3mm
SKU: FEED-PELLET-3MM
Category: Feed
Unit: kg
Default Supplier: Feed Supplier Inc
Reorder Threshold: 500 kg
Min Stock Level: 1000 kg
```

---

### Viewing Items

**Items List shows:**
- Item name and SKU
- Category
- Current quantity (color-coded)
- Reorder threshold
- Status (active/inactive)

**Color Coding:**
- 🔴 **Red:** Below reorder threshold (low stock)
- 🟡 **Yellow:** Between reorder and min level
- 🟢 **Green:** Above min stock level

**Filters:**
- **Category:** Filter by category
- **Status:** Show active or inactive items
- **Search:** Type to find by name or SKU

---

### Editing an Item

1. Find item in the list
2. Click **Edit** icon (pencil)
3. Update fields as needed
4. Click **Save Changes**

**Common Edits:**
- Adjust reorder threshold (based on usage patterns)
- Change default supplier
- Update item name (more descriptive)

---

### Deactivating an Item

**When to Deactivate:**
- Item no longer used
- Replaced by different product
- Discontinued by supplier

**Steps:**
1. Find item in the list
2. Click **Delete** icon (trash)
3. Confirm deactivation
4. Item marked inactive (preserves history)

**Note:** Deactivated items still show in transaction history for audit trail.

---

## Stock Operations

### Adding Stock (Receiving Inventory)

**Scenario:** You received a delivery of 500 kg fish feed.

**Steps:**

1. Go to **Stock Operations** page
2. Click **Add Stock** tab
3. Fill in the form:
   - **Item:** Select from dropdown (e.g., "Premium Fish Feed 3mm")
   - **Quantity:** Amount received (e.g., 500)
   - **Unit Cost:** Cost per unit (e.g., ₹48.00 per kg)
   - **Purchase Date:** Date received (e.g., today)
   - **Supplier:** Auto-filled from item default, or select different
   - **Batch Number:** Batch identifier (e.g., "BATCH-2025-11-19-001")
   - **Expiry Date:** Expiration date (optional, for perishables)
   - **PO Number:** Related purchase order (optional)
   - **Notes:** Additional info (e.g., "Good quality batch")
4. Click **Add Stock**

**What Happens:**
- Creates a new batch in the system
- Increases item current quantity
- Records transaction for audit
- Adds to inventory value

**Best Practice:**
- Record stock immediately upon receipt
- Verify quantity before entering
- Note batch number from supplier packaging
- Check expiry date for perishable items

---

### Using Stock (Deducting Inventory)

**Scenario:** You used 50 kg of feed for tank feeding.

**Steps:**

1. Go to **Stock Operations** page
2. Click **Use Stock** tab
3. Fill in the form:
   - **Item:** Select item to deduct
   - **Quantity:** Amount used (e.g., 50.5)
   - **Purpose:** Why you're using this (e.g., "Tank 1 feeding - morning session")
   - **Module Reference:** Which module (e.g., "biofloc")
   - **Tank ID:** Tank identifier (optional)
   - **Notes:** Additional details
4. Click **Use Stock**

**What Happens:**
- System automatically uses FIFO (First-In-First-Out)
- Deducts from oldest batches first
- Calculates weighted average cost
- Decreases item current quantity
- Records transaction with cost tracking

**FIFO Explanation:**

If you have:
- Batch A: 200 kg @ ₹50/kg (purchased Nov 1)
- Batch B: 500 kg @ ₹48/kg (purchased Nov 10)

And you use 250 kg:
- System deducts 200 kg from Batch A (older)
- Then deducts 50 kg from Batch B
- Weighted cost: (200×50 + 50×48) / 250 = ₹49.60/kg

**Why FIFO?**
- Ensures older stock is used first
- Reduces risk of expiry/spoilage
- Accurate cost tracking

---

### Understanding FIFO (First-In-First-Out)

**What is FIFO?**
FIFO means the oldest stock is used first, like organizing a fridge - put new milk in the back, use old milk first.

**Example Timeline:**
```
Nov 1:  Receive 500 kg @ ₹50/kg (Batch A)
Nov 10: Receive 750 kg @ ₹48/kg (Batch B)
Nov 15: Use 600 kg

System automatically:
- Uses all 500 kg from Batch A (older)
- Uses 100 kg from Batch B
- Batch A is now depleted
- Batch B has 650 kg remaining
```

**Benefits:**
- Prevents old stock from sitting unused
- Critical for items with expiry dates
- Matches natural inventory flow

---

## Purchase Orders

### Creating a Purchase Order

**Scenario:** You need to order feed and chemicals from supplier.

**Steps:**

1. Go to **Purchase Orders** page
2. Click **+ New Purchase Order** button
3. **Header Information:**
   - **PO Number:** Unique identifier (e.g., "PO-2025-001")
   - **Supplier:** Select supplier from dropdown
   - **PO Date:** Today's date
   - **Expected Delivery:** When you expect to receive (e.g., 10 days)
   - **Notes:** Additional info (e.g., "Monthly feed order")

4. **Add Items:**
   - Click **+ Add Item** button
   - Select **Item** from dropdown
   - Enter **Quantity** to order
   - Enter **Unit Cost** (price per unit)
   - Line Total auto-calculates (qty × cost)
   - Repeat for all items you're ordering

5. **Review Total:**
   - System shows **Total Cost** (sum of all line totals)
   - Verify all items and quantities

6. Click **Create Purchase Order**

**Example PO:**
```
PO Number: PO-2025-11-19-001
Supplier: Feed Supplier Inc
PO Date: 2025-11-19
Expected Delivery: 2025-11-29

Items:
1. Premium Fish Feed 3mm - 500 kg @ ₹48.00 = ₹24,000.00
2. Vitamin Mix - 100 kg @ ₹10.00 = ₹1,000.00
3. pH Adjuster - 50 L @ ₹15.00 = ₹750.00

Total Cost: ₹25,750.00
```

---

### Tracking Purchase Orders

**PO Status Flow:**
```
Pending → Approved → Ordered → Received → Closed
                                ↓
                            Cancelled
```

**Status Meanings:**
- **Pending:** Created but not yet approved
- **Approved:** Approved, ready to send to supplier
- **Ordered:** Order placed with supplier
- **Received:** Goods received at farm
- **Closed:** PO completed and closed
- **Cancelled:** PO cancelled (no longer needed)

**Updating PO Status:**
1. Find PO in the list
2. Click **Edit** icon
3. Change **Status** to next stage
4. Click **Save**

**Example Workflow:**
```
Day 1: Create PO (status: Pending)
Day 1: Manager approves (status: Approved)
Day 1: Send to supplier (status: Ordered)
Day 10: Goods delivered (status: Received)
Day 10: Record stock receipt using "Add Stock"
Day 10: Close PO (status: Closed)
```

---

### Receiving Against a PO

**Scenario:** Your PO-2025-001 was delivered today.

**Steps:**

1. **Verify delivery** against PO:
   - Check all items received
   - Verify quantities
   - Inspect quality

2. **Record stock** for each item:
   - Go to **Stock Operations → Add Stock**
   - For each item in PO:
     - Select item
     - Enter quantity received
     - Enter unit cost (from PO)
     - **Enter PO number** in "PO Number" field
     - Click Add Stock
     - Repeat for all items

3. **Update PO status:**
   - Go to **Purchase Orders**
   - Find your PO
   - Edit and change status to "Received"

**Best Practice:**
- Physically count items before recording
- Note any discrepancies in notes
- Link stock additions to PO for traceability

---

## Suppliers & Categories

### Managing Suppliers

**Adding a New Supplier:**

1. Go to **Suppliers** page
2. Click **+ New Supplier** button
3. Fill in information:
   - **Supplier Name:** Company name
   - **Contact Person:** Primary contact
   - **Phone:** Contact number
   - **Email:** Email address
   - **Address:** Physical location
4. Click **Save**

**Editing Supplier:**
- Click edit icon next to supplier
- Update information
- Save changes

**Deactivating Supplier:**
- Click delete icon
- Confirm deactivation
- Supplier marked inactive (preserves history)

---

### Managing Categories

**Creating a Category:**

1. Go to **Categories** page
2. Click **+ New Category** button
3. Enter:
   - **Category Name:** (e.g., "Feed", "Chemicals")
   - **Description:** What this category includes
4. Click **Save**

**Common Categories:**
- **Feed:** All animal feed types
- **Chemicals:** Water treatment, disinfectants
- **Equipment:** Tanks, aerators, tools
- **Supplies:** Test kits, containers
- **Probiotics:** Beneficial bacteria products
- **Supplements:** Vitamins, minerals

**Viewing Category Info:**
- Each category card shows **item count**
- Helps organize inventory
- Makes filtering easier

---

## Alerts & Monitoring

### Low Stock Alerts

**What are Low Stock Alerts?**
Items that have fallen below their reorder threshold.

**Viewing Low Stock Alerts:**
1. Go to **Alerts** page
2. Left column shows **Low Stock Items**
3. Each alert shows:
   - Item name and SKU
   - Current quantity (red)
   - Reorder threshold
   - Shortage (how much below threshold)
   - Default supplier

**Responding to Low Stock:**
1. Review alert
2. Calculate how much to order:
   - Order enough to reach min stock level
   - Consider lead time from supplier
   - Account for usage rate
3. Create purchase order
4. Track PO until received

**Example:**
```
Alert: Premium Fish Feed 3mm
Current: 450 kg
Threshold: 500 kg
Min Level: 1000 kg
Shortage: -50 kg

Action: Order 600 kg (brings to 1,050 kg, above min level)
```

---

### Expiry Alerts

**What are Expiry Alerts?**
Batches that will expire within 30 days.

**Viewing Expiry Alerts:**
1. Go to **Alerts** page
2. Right column shows **Expiring Soon**
3. Each alert shows:
   - Item name and batch
   - Remaining quantity
   - Expiry date
   - Days until expiry (color-coded)
   - Supplier info

**Urgency Colors:**
- 🔴 **Red:** Expiring in < 7 days (use immediately!)
- 🟠 **Orange:** Expiring in 7-14 days (use soon)
- 🟡 **Yellow:** Expiring in 15-30 days (monitor)

**Responding to Expiry Alerts:**

**For items expiring < 7 days:**
1. Plan to use this batch FIRST
2. Prioritize in feeding/operations
3. Use before it expires
4. If can't use in time, contact supplier about return/exchange

**For items expiring 7-30 days:**
1. Monitor usage
2. Plan operations to use this batch
3. Avoid ordering more until batch depleted

**Best Practice:**
- Check expiry alerts daily
- Use FIFO (system does this automatically)
- Order smaller quantities of perishable items
- Rotate stock physically (older batches accessible first)

---

## Stock Adjustments

### When to Use Stock Adjustments

**Common Scenarios:**
- **Physical count mismatch:** Counted 980 kg but system shows 1,000 kg
- **Found missing stock:** Discovered 50 kg we didn't know we had
- **Damage/spoilage:** 20 kg damaged and unsaleable
- **Theft or loss:** Stock went missing

### Creating a Stock Adjustment

**Scenario:** Physical count shows 980 kg, but system shows 1,000 kg.

**Steps:**

1. Go to **Adjustments** page
2. Click **+ New Adjustment** button
3. Select **Item** to adjust
4. Choose **Adjustment Type:**
   - **Increase:** Add quantity
   - **Decrease:** Remove quantity
   - **Recount:** Set exact quantity
5. Enter quantity:
   - For **Increase/Decrease:** Enter amount to add/remove
   - For **Recount:** Enter actual counted quantity
6. Enter **Reason** (required):
   - "Physical inventory count"
   - "Damage - spoiled batch"
   - "Found missing stock"
7. Add **Notes** with details
8. Click **Save Adjustment**

**Example Adjustments:**

**Type 1: Recount (Recommended for physical counts)**
```
Item: Premium Fish Feed 3mm
Type: Recount
Actual Quantity: 980 kg
Reason: Monthly physical inventory count
Notes: Counted by John Doe, verified by supervisor

System shows:
Previous: 1,000 kg
Change: -20 kg
New: 980 kg
```

**Type 2: Decrease (For known losses)**
```
Item: Vitamin Mix
Type: Decrease
Quantity to Remove: 5 kg
Reason: Damaged container - unusable
Notes: Container cracked during handling, product contaminated

System shows:
Previous: 50 kg
Change: -5 kg
New: 45 kg
```

**Type 3: Increase (For found stock)**
```
Item: pH Adjuster
Type: Increase
Quantity to Add: 10 L
Reason: Found stock in secondary storage
Notes: Located 2 bottles in back warehouse

System shows:
Previous: 25 L
Change: +10 L
New: 35 L
```

---

### Viewing Adjustment History

1. Go to **Adjustments** page
2. View **Adjustment History** table
3. Shows:
   - Date and time
   - Item adjusted
   - Adjustment type (color-coded chip)
   - Quantity change
   - Previous and new quantity
   - Reason
   - Who made adjustment

**Use Cases:**
- Audit physical count history
- Investigate discrepancies
- Track who made changes
- Verify adjustment reasons

---

## Reports & History

### Transaction History

**What is Transaction History?**
Complete log of all inventory movements - additions, usages, and adjustments.

**Viewing Transaction History:**

1. Go to **Transaction History** page
2. Use filters:
   - **Item:** Select specific item (or view all)
   - **Transaction Type:** Add, Use, Adjustment (or all)
   - **Time Period:** Last 7, 30, 90 days
3. Review table showing:
   - Date/time
   - Item name and SKU
   - Transaction type (color-coded)
   - Quantity change (+ or -)
   - New balance after transaction
   - Cost information
   - User who performed action
   - Purpose/notes

**Color Coding:**
- 🟢 **Green "Add":** Stock addition
- 🔵 **Blue "Use":** Stock usage
- 🟡 **Yellow "Adjustment":** Manual correction

**Use Cases:**
- **Verify usage:** Check when and how much was used
- **Cost tracking:** See cost per transaction
- **Audit trail:** Who did what and when
- **Investigate discrepancies:** Track down errors
- **Module tracking:** See which modules used stock

**Example Investigation:**

*Question: "How much feed did biofloc module use last month?"*

1. Go to Transaction History
2. Filter:
   - Item: "Premium Fish Feed 3mm"
   - Transaction Type: "Use"
   - Time Period: Last 30 days
3. Further filter by Module Reference: "biofloc"
4. Review results:
   - Sum total quantity used
   - See feeding sessions (by session number)
   - Calculate total cost

---

### Current Stock View

**Real-time Stock Levels:**

1. Go to **Current Stock** page
2. See table with all items showing:
   - Item name and SKU
   - Current quantity
   - Min stock level
   - Status indicator
   - Unit

**Status Indicators:**
- 🔴 **Low Stock:** Below threshold
- 🟢 **OK:** Above min level

**Use Case:**
- Quick morning stock check
- Verify availability before operations
- Export for reports

---

### Analytics (Future)

**Coming Features:**
- Stock movement trends
- Consumption patterns by module
- Supplier performance metrics
- Cost analysis and forecasting
- Automated reorder suggestions

---

## Best Practices

### Daily Operations

**Morning Checklist:**
- [ ] Check low stock alerts
- [ ] Review expiry alerts (urgent items)
- [ ] Verify stock levels for day's operations
- [ ] Record any overnight deliveries

**During Operations:**
- [ ] Record stock usage immediately after operations
- [ ] Note any issues (damage, quality problems)
- [ ] Update PO status when goods received

**End of Day:**
- [ ] Review day's transactions
- [ ] Update pending POs
- [ ] Note any discrepancies for investigation

---

### Weekly Tasks

**Every Week:**
- [ ] Review low stock alerts and create POs
- [ ] Check expiring batches (7-30 day window)
- [ ] Review pending POs (follow up with suppliers)
- [ ] Spot-check random items (quick count verification)

---

### Monthly Tasks

**Every Month:**
- [ ] **Physical inventory count** (full or cycle counting)
- [ ] Create stock adjustments for discrepancies
- [ ] Review consumption patterns
- [ ] Analyze supplier performance
- [ ] Clean up old/inactive items
- [ ] Review reorder thresholds (adjust based on usage)

---

### Stock Management Best Practices

**1. FIFO Physical Storage**
- Arrange physical stock to match system FIFO
- New deliveries go to back/bottom
- Older stock accessible first
- Label batches with receipt date

**2. Accurate Record-Keeping**
- Record transactions immediately (don't wait)
- Be precise with quantities (use scales)
- Include detailed notes
- Link to POs when applicable

**3. Regular Physical Counts**
- Monthly full count for high-value items
- Weekly cycle counting (rotate through all items)
- Annual complete physical inventory
- Adjust system to match counts

**4. Smart Reorder Management**
- Set thresholds = 2-4 weeks average usage
- Consider supplier lead time
- Account for seasonal variations
- Review and adjust thresholds quarterly

**5. Expiry Management**
- Order smaller quantities of perishables
- First-In-First-Out physically and in system
- Daily check of items expiring < 7 days
- Work with suppliers on returns/exchanges

**6. Category Organization**
- Use consistent category names
- Group similar items together
- Makes filtering and reporting easier
- Helps with physical warehouse organization

**7. Supplier Relationships**
- Maintain accurate supplier contact info
- Track delivery reliability
- Note quality issues
- Have backup suppliers for critical items

---

## Troubleshooting

### Common Issues

#### Issue 1: "Insufficient stock" error when using stock

**Cause:** Trying to use more than available quantity.

**Solution:**
1. Check current stock level for the item
2. Verify you entered correct quantity (not in wrong unit)
3. Check if there are reservations reducing available stock
4. If stock truly insufficient:
   - Reduce usage amount
   - Order more stock
   - Use alternative item if available

---

#### Issue 2: Wrong quantity recorded - need to fix

**Scenario:** You recorded 500 kg but actually received 550 kg.

**Solution: Use Stock Adjustment**
1. Go to Adjustments
2. Create new adjustment
3. Type: Increase
4. Quantity to Add: 50 kg
5. Reason: "Correction - actual receipt was 550 kg not 500 kg"
6. Save adjustment

**Alternative: For recent additions**
- Contact administrator to delete incorrect transaction
- Re-record with correct quantity
- Only do this immediately after error (within same day)

---

#### Issue 3: Physical count doesn't match system

**Scenario:** System shows 1,000 kg but you counted 980 kg.

**Solution: Recount Adjustment**
1. **First, verify your count:**
   - Count again to be sure
   - Check if items in multiple locations
   - Verify you counted correct item/SKU

2. **If count is accurate:**
   - Go to Adjustments
   - Create new adjustment
   - Type: Recount
   - Enter actual quantity: 980 kg
   - Reason: "Monthly physical count"
   - Notes: "Counted by [name], verified by [supervisor]"
   - Save

3. **Investigate discrepancy:**
   - Review transaction history
   - Look for unrecorded usage
   - Check for damage/spoilage
   - Verify no theft

---

#### Issue 4: Can't find item in dropdown when adding stock

**Possible Causes:**

**Cause A: Item doesn't exist**
- Solution: Create new item first, then add stock

**Cause B: Item is inactive**
- Solution:
  1. Go to Items page
  2. Filter: Show Inactive items
  3. Find item and reactivate
  4. Then add stock

**Cause C: Typo in search**
- Solution: Try different search terms or scroll through list

---

#### Issue 5: Wrong cost entered - need to correct

**Scenario:** You entered unit cost ₹50 but it should be ₹48.

**Problem:** Cannot edit transactions directly (audit trail protection).

**Solutions:**

**Option A: If just added (within minutes):**
- Contact administrator to delete transaction
- Re-record with correct cost

**Option B: If older transaction:**
- **Accept it for audit trail integrity**
- Note the error in a stock adjustment notes
- Future transactions will have correct cost
- Weighted average will balance out over time

**Prevention:**
- Double-check cost before clicking submit
- Have PO or invoice handy when entering
- Verify unit (sometimes ₹50/kg vs ₹50/bag confusion)

---

#### Issue 6: Item showing as low stock but I just received delivery

**Possible Causes:**

**Cause A: Delivery not recorded**
- Solution: Record stock addition immediately

**Cause B: Added to wrong item**
- Solution:
  1. Check transaction history for both items
  2. Contact administrator to correct
  3. May need adjustment on both items

**Cause C: Reorder threshold too high**
- Solution:
  1. Review item settings
  2. Adjust reorder threshold if appropriate
  3. Min level might need adjustment too

---

#### Issue 7: Multiple batches showing, how do I know which is used first?

**Answer:** System uses FIFO automatically.

**FIFO Order:**
- Oldest purchase date used first
- If same date, lowest batch ID used first
- You don't need to select batches manually
- System handles it automatically

**To See Batch Order:**
1. View Current Stock page
2. Click item to see batches (if feature available)
3. Or view Transaction History
   - Look at "Use" transactions
   - Notes will show which batches were deducted

---

### Error Messages Explained

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Insufficient stock" | Not enough available quantity | Check current stock, reduce usage, or order more |
| "Item not found" | Invalid item ID or SKU | Verify item exists and is active |
| "Duplicate SKU" | SKU already exists | Use different SKU or reactivate existing item |
| "Invalid PO number" | PO doesn't exist | Check PO number or leave blank |
| "Supplier not found" | Invalid supplier | Select valid supplier or create new |
| "Negative quantity not allowed" | Entered negative number | Enter positive number |
| "Quantity exceeds purchased amount" | Batch error | Contact administrator |

---

## Getting Help

### For Inventory Issues

**Level 1: Self-Help**
- Check this guide
- Review transaction history
- Verify item settings
- Try adjustments for corrections

**Level 2: Peer Support**
- Ask colleague who uses inventory
- Check with supervisor
- Review farm procedures

**Level 3: Administrator**
- Contact IT support
- Report bugs or errors
- Request training
- Get help with complex adjustments

### Reporting a Problem

**Include:**
1. What you were trying to do
2. What happened instead
3. Error message (if any)
4. Screenshot (if helpful)
5. Item SKU or transaction ID
6. Date and time of issue

**Example:**
```
Subject: Can't add stock for FEED-PELLET-3MM

I'm trying to record receipt of 500 kg feed (SKU: FEED-PELLET-3MM)
but when I click "Add Stock" I get error "Item not found".

The item shows in the Items list as active.

Screenshot attached.
Date: 2025-11-19 10:30 AM
```

---

## Appendix: Inventory Checklist

### Daily Checklist
- [ ] Check low stock alerts
- [ ] Review items expiring today/tomorrow
- [ ] Record all stock usage from operations
- [ ] Add stock for any deliveries received
- [ ] Update PO status for received orders

### Weekly Checklist
- [ ] Review all low stock items
- [ ] Create POs for items below threshold
- [ ] Check items expiring in next 7 days
- [ ] Follow up on pending POs
- [ ] Spot-check 5-10 random items

### Monthly Checklist
- [ ] Conduct physical inventory count (full or partial)
- [ ] Create adjustments for discrepancies
- [ ] Review and update reorder thresholds
- [ ] Analyze consumption patterns
- [ ] Review supplier performance
- [ ] Clean up old batches (mark depleted ones inactive)
- [ ] Check for slow-moving items
- [ ] Update categories if needed

### Quarterly Checklist
- [ ] Full physical inventory count
- [ ] Review all item reorder thresholds
- [ ] Evaluate supplier relationships
- [ ] Review storage procedures
- [ ] Update min stock levels based on growth
- [ ] Archive old transaction data (if needed)

### Annual Checklist
- [ ] Complete physical inventory (all items)
- [ ] Major review of all thresholds and settings
- [ ] Supplier contract reviews
- [ ] System training refresh for all users
- [ ] Warehouse organization review
- [ ] Deactivate permanently discontinued items
- [ ] Update categories and organization

---

**End of User Guide**

For technical details and architecture, see [Technical Guide](./technical-guide.md).
