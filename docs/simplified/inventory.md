# Inventory Module - Simple Guide 📦

## What Does This Module Do?

The Inventory module helps you keep track of all supplies on the farm. Think of it like managing a store:
- Know what you have
- Know when you're running low
- Record when you use things
- Order new supplies when needed

## Main Sections

### 🏠 Dashboard
Your quick view showing:
- Total items you're tracking
- Items running low (need to order more!)
- Items expiring soon
- Recent activity

---

## Working with Items

### What is an Item?

An item is anything you track in inventory. Examples:
- Fish feed (different types)
- Chemicals (for water treatment)
- Equipment (nets, buckets)
- Test kits
- Vitamins and supplements

### Viewing Your Items

1. Click **Inventory** in the menu
2. Click **Items**
3. You'll see a list showing:
   - Item name
   - How much you have right now
   - When you should reorder
   - Status (active or inactive)

**Color coding:**
- 🔴 Red number = LOW STOCK! Order more now
- 🟡 Yellow number = Getting low, plan to order soon
- 🟢 Green number = You have plenty

### Adding a New Item

**When:** You start tracking a new type of supply

**Steps:**
1. Click **+ New Item** button
2. Fill in the form:
   - **Item Name:** What is it? (Example: "Fish Feed Pellets 3mm")
   - **SKU:** A unique code for this item (Example: "FEED-001")
   - **Category:** What type? (Feed, Chemical, Equipment, etc.)
   - **Unit:** How you measure it (kg, liters, pieces, boxes)
   - **Reorder Threshold:** When should you be alerted to order more? (Example: 100 kg)
   - **Min Stock Level:** Ideal minimum amount (Example: 200 kg)
3. Click **Save**

**Tip:** The reorder threshold is like a "low fuel" warning light in a car!

---

## Stock Operations

### Adding Stock (When You Receive a Delivery)

**When:** New supplies arrive at the farm

**Steps:**
1. Go to **Stock Operations**
2. Click **Add Stock** tab
3. Fill in the details:
   - **Item:** Select what you received
   - **Quantity:** How much? (Example: 500 kg)
   - **Unit Cost:** Price per unit (Example: ₹50 per kg)
   - **Purchase Date:** Today's date
   - **Batch Number:** ID from the supplier's bag/box
   - **Expiry Date:** When does it expire? (if applicable)
4. Click **Add Stock**

**What happens:**
- Your stock quantity increases
- The system knows how much this cost
- You can track when it expires

**Example:**
```
Today you received:
- 500 kg of Fish Feed
- Cost: ₹48 per kg
- Batch: BATCH-2025-001
- Expires: June 2026

Your stock goes from 150 kg → 650 kg
```

### Using Stock (When You Consume Supplies)

**When:** You use supplies for farm operations

**Steps:**
1. Go to **Stock Operations**
2. Click **Use Stock** tab
3. Fill in the details:
   - **Item:** What are you using?
   - **Quantity:** How much? (Example: 50 kg)
   - **Purpose:** Why? (Example: "Fed Tank 1 - morning session")
   - **Notes:** Any additional info
4. Click **Use Stock**

**What happens:**
- Your stock quantity decreases
- The system tracks where it went
- Uses oldest stock first (FIFO - see below)

**Important:** Record usage right away! Don't wait until later or you might forget.

---

## Understanding FIFO (First-In-First-Out)

**What is FIFO?**
FIFO means using the oldest supplies first. Like organizing milk in a fridge - put new milk in back, use old milk first!

**Why is this important?**
- Prevents supplies from expiring
- Uses stock before it goes bad
- Saves money (less waste)

**How does it work automatically?**

If you have:
- Batch A: 200 kg (received Nov 1)
- Batch B: 500 kg (received Nov 15)

When you use 250 kg, the system automatically:
1. Uses all 200 kg from Batch A (older one first)
2. Then uses 50 kg from Batch B
3. Batch A is now empty, Batch B has 450 kg left

**You don't have to think about it - the system does it for you!**

---

## Purchase Orders (Ordering Supplies)

### What is a Purchase Order (PO)?

A PO is like a shopping list you send to suppliers. It says "Please deliver these items to us."

### Creating a Purchase Order

**When:** You're running low and need to order supplies

**Steps:**
1. Go to **Purchase Orders**
2. Click **+ New Purchase Order**
3. Enter basic info:
   - **PO Number:** Unique ID (Example: "PO-2025-001")
   - **Supplier:** Who are you ordering from?
   - **PO Date:** Today
   - **Expected Delivery:** When should it arrive?
4. Add items to order:
   - Click **+ Add Item**
   - Select the item
   - Enter quantity you want
   - Enter cost per unit
   - Repeat for all items
5. Review the total cost
6. Click **Create Purchase Order**

### Tracking Your Order

**PO Status:**
- **Pending** = Just created, not sent yet
- **Ordered** = Sent to supplier, waiting for delivery
- **Received** = Goods arrived!
- **Closed** = Everything complete

**To update status:**
1. Find your PO in the list
2. Click edit ✏️
3. Change status to next stage
4. Save

**When goods arrive:**
1. First, use **Add Stock** to record what you received
2. Then update the PO status to "Received"

---

## Alerts (Warnings!)

### Low Stock Alerts

**What it is:** Items that dropped below their reorder threshold

**Viewing alerts:**
1. Go to **Alerts** page
2. Left side shows **Low Stock Items**
3. Each alert shows:
   - Item name
   - Current amount (in red)
   - Reorder threshold
   - How much you're short

**What to do:**
1. Review the alert
2. Decide how much to order
3. Create a purchase order
4. The alert will disappear when stock increases

### Expiry Alerts

**What it is:** Items that will expire within 30 days

**Viewing alerts:**
1. Go to **Alerts** page
2. Right side shows **Expiring Soon**
3. Color coding:
   - 🔴 Red = Expires in less than 7 days (use NOW!)
   - 🟠 Orange = Expires in 7-14 days (use soon)
   - 🟡 Yellow = Expires in 15-30 days (keep an eye on it)

**What to do:**
- **If expiring < 7 days:** Use this batch FIRST before anything else
- **If expiring 7-30 days:** Plan to use it before newer batches
- **If you can't use it in time:** Contact supplier about return/exchange

**Tip:** The system automatically uses oldest stock first (FIFO), helping prevent expiry!

---

## Stock Adjustments

### When Do You Need This?

**Common situations:**
- 📊 **Physical count doesn't match system:** You counted 95 kg but system says 100 kg
- 🔍 **Found missing stock:** Discovered 20 kg in another room
- 💔 **Damage:** 10 kg got wet and ruined
- 🚨 **Loss:** Something went missing

### Making an Adjustment

**Steps:**
1. Go to **Adjustments** page
2. Click **+ New Adjustment**
3. Select the **Item**
4. Choose **Type:**
   - **Recount:** Set exact amount (best for physical counts)
   - **Increase:** Add quantity (found extra stock)
   - **Decrease:** Remove quantity (damage, loss)
5. Enter the quantity or actual amount
6. **Reason:** REQUIRED! Explain why (Example: "Monthly count - found discrepancy")
7. **Notes:** Add details (Example: "Counted by John, verified by supervisor")
8. Click **Save Adjustment**

**Example 1: Monthly Count**
```
You physically counted: 95 kg
System shows: 100 kg
Difference: -5 kg

Action:
- Type: Recount
- Actual Quantity: 95 kg
- Reason: "Monthly physical inventory"
- Notes: "Counted twice to confirm, -5 kg difference"
```

**Example 2: Damage**
```
A bag broke and 5 kg spilled and got contaminated

Action:
- Type: Decrease
- Quantity to Remove: 5 kg
- Reason: "Damaged goods"
- Notes: "Bag tore during handling, product ruined"
```

---

## Reports & History

### Transaction History

**What it is:** A complete log of every time stock was added, used, or adjusted

**Viewing history:**
1. Go to **Transaction History**
2. Use filters:
   - **Item:** See history for one item
   - **Transaction Type:** Add, Use, or Adjustment
   - **Time Period:** Last 7, 30, or 90 days
3. Review the table showing:
   - When it happened
   - What item
   - Type (Add/Use/Adjustment)
   - How much changed
   - New balance
   - Who did it

**Color coding:**
- 🟢 Green "Add" = Stock added
- 🔵 Blue "Use" = Stock used
- 🟡 Yellow "Adjustment" = Manual correction

**Example use:**
*"How much feed did we use last month?"*
1. Filter by: Item = "Fish Feed 3mm"
2. Filter by: Type = "Use"
3. Filter by: Time = Last 30 days
4. Add up all the quantities!

---

## Suppliers & Categories

### Managing Suppliers

**What it is:** Companies you buy from

**Adding a supplier:**
1. Go to **Suppliers**
2. Click **+ New Supplier**
3. Enter:
   - Name
   - Contact person
   - Phone number
   - Email
   - Address
4. Click **Save**

**Why track suppliers?**
- Quick access to contact info
- See which supplier provides which items
- Track delivery reliability

### Managing Categories

**What it is:** Groups to organize your items

**Common categories:**
- Feed
- Chemicals
- Equipment
- Test Kits
- Probiotics

**Adding a category:**
1. Go to **Categories**
2. Click **+ New Category**
3. Enter name and description
4. Save

**Why use categories?**
- Makes finding items easier
- Better organization
- Useful for reports

---

## Best Practices (Tips for Success!)

### Daily Tasks
- ✅ Check low stock alerts every morning
- ✅ Check expiry alerts (especially red ones!)
- ✅ Record stock usage right after operations
- ✅ Record deliveries as soon as they arrive

### Weekly Tasks
- ✅ Review low stock items and create POs
- ✅ Check items expiring in next 7 days
- ✅ Follow up on pending purchase orders

### Monthly Tasks
- ✅ Do a physical count of all items (or at least important ones)
- ✅ Create adjustments for any differences
- ✅ Review reorder thresholds (are they set correctly?)
- ✅ Check for slow-moving items (not being used)

### Smart Habits

✅ **Record immediately** - Don't wait! You might forget
✅ **Be accurate** - Use scales, measure properly
✅ **Add notes** - Future you will thank you
✅ **Check expiry dates** - Especially for chemicals and feed
✅ **Physical organization** - Keep older stock in front (matches FIFO)

---

## Troubleshooting (Common Problems)

### Problem: "Insufficient Stock" Error

**What it means:** You're trying to use more than you have

**Fix:**
1. Check current stock level
2. Make sure you entered the right amount (not too many zeros!)
3. If you really need more, order it first

### Problem: Wrong Quantity Recorded

**What happened:** You accidentally entered 500 instead of 50

**Fix:**
Use Stock Adjustment:
1. Go to Adjustments
2. Type: Increase or Decrease (depending on your mistake)
3. Quantity: The difference (450 in this example)
4. Reason: "Correction - typo in original entry"
5. Save

### Problem: Physical Count Doesn't Match System

**What to do:**
1. **Count again** to make sure
2. Check if items are in multiple locations
3. Verify you counted the right item (check SKU!)
4. If your count is correct:
   - Use Adjustment → Recount
   - Enter actual amount you counted
   - Reason: "Physical inventory count"
   - Add notes with who counted

### Problem: Can't Find Item in Dropdown

**Possible causes:**

**Cause 1:** Item doesn't exist
- Fix: Create the item first, then add stock

**Cause 2:** Item is inactive
- Fix: Go to Items → Show inactive → Reactivate it

**Cause 3:** Typo in search
- Fix: Try different search terms or scroll through list

---

## Quick Reference

### Stock Level Colors

| Color | Meaning | Action |
|-------|---------|--------|
| 🔴 Red | Below reorder point | Order more NOW |
| 🟡 Yellow | Between reorder and min level | Watch it |
| 🟢 Green | Above min level | You're good! |

### Transaction Types

| Type | What It Does | When to Use |
|------|-------------|-------------|
| **Add Stock** | Increases quantity | Received delivery |
| **Use Stock** | Decreases quantity | Used in operations |
| **Adjustment** | Corrects quantity | Fix errors, record damage/loss |

### Units Commonly Used

- **kg** = Kilograms (for feed, chemicals)
- **L** = Liters (for liquids)
- **pcs** = Pieces (for individual items)
- **boxes** = Boxes (for packaged items)
- **bags** = Bags (for bagged supplies)

---

## Need Help?

- Check the transaction history to see what happened
- Ask your supervisor about reorder amounts
- Contact supplier if you have questions about products
- Review this guide for step-by-step instructions

Remember: Good inventory management = Less waste + Always having what you need!
