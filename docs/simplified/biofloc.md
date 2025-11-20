# Biofloc Module - Simple Guide 🐠

## What Does This Module Do?

The Biofloc module helps you manage fish farming operations. It tracks:
- Fish tanks (where fish live)
- Fish batches (groups of fish growing together)
- Daily tasks (feeding, water testing, counting deaths)
- Growth progress (how big are the fish getting?)
- Harvest results (money made from selling fish)

Think of it as a digital diary for your fish farm!

---

## Main Sections

### 🏠 Dashboard
Your home page showing:
- How many tanks are active
- Total number of fish
- Alerts (water quality problems, deaths)
- Upcoming harvests

---

## Tanks

### What is a Tank?

A tank is a container where fish grow. Each tank has:
- A unique code/name (like "Tank-001" or "A1")
- Size (how much water it holds)
- Location (where it is on the farm)
- Status (Active, Empty, or Under Maintenance)

### Creating a New Tank

**When:** You build or prepare a new tank

**Steps:**
1. Go to **Tanks** page
2. Click **+ New Tank**
3. Fill in:
   - **Tank Code:** Unique name (Example: "T-001" or "Block-A-01")
   - **Capacity:** How many liters of water (Example: 50000 L)
   - **Location:** Where is it? (Example: "Block A, Row 1")
   - **Notes:** Any special info
4. Click **Save**

**Tip:** Use a consistent naming system for all tanks!

### Tank Status

- **Active:** Has fish in it right now
- **Empty:** Ready for new fish
- **Maintenance:** Being cleaned or repaired

---

## Batches

### What is a Batch?

A batch is a group of fish that were put in a tank on the same day. It's like a "class" of fish growing up together.

**Example:** On March 1st, you put 50,000 baby fish in Tank-001. That's Batch "B-2025-001".

### Creating a New Batch (Stocking Fish)

**When:** You receive baby fish from a hatchery and put them in a tank

**Steps:**
1. Go to **Batches** page
2. Click **+ New Batch**
3. Fill in the details:
   - **Batch Code:** Unique ID (Example: "B-2025-001")
   - **Species:** Type of fish (Example: "Shrimp")
   - **Source:** Where did you buy them? (Hatchery name)
   - **Tank:** Which tank are they going in?
   - **Stocking Date:** Today's date
   - **Initial Count:** How many fish? (Example: 50,000)
   - **Initial Avg Weight:** Average weight of each fish (Example: 0.5 grams for babies)
4. Click **Create Batch**

**What happens:**
- The tank becomes "Active"
- System starts tracking this group of fish
- You can now record feeding, growth, etc.

### Batch Lifecycle (Fish Journey)

```
Start → Growing → Grading (optional) → Harvest
```

1. **Start (Day 0):** Put baby fish in tank
2. **Growing (Days 1-120):** Feed daily, they get bigger
3. **Grading (Day 30-60):** Separate by size if needed
4. **Harvest (Day 90-150):** Catch and sell fish

---

## Daily Operations

### 1. Feeding 🍽️

**When:** Every day, usually 2-5 times per day

**What it does:** Records how much feed you gave to the tanks

**Steps:**
1. Go to **Feeding** page
2. Enter session details:
   - **Date:** Today
   - **Session Number:** 1 (morning), 2 (afternoon), 3 (evening)
   - **Time:** When you fed (Example: 08:00)
3. Add tanks (can add multiple at once!):
   - Click **+ Add Tank**
   - Select tank
   - Enter how many kg of feed
   - Repeat for all tanks you're feeding
4. Select **Feed Item** from inventory (Example: "Fish Feed 3mm")
5. Click **Record Feeding**

**What happens:**
- Records feed given
- Deducts feed from inventory automatically
- Updates fish growth calculations
- Tracks costs

**Example:**
```
Morning feeding session (08:00):
- Tank-001: 15 kg
- Tank-002: 12 kg
- Tank-003: 18 kg
Total: 45 kg of feed used
```

---

### 2. Sampling (Measuring Fish Growth) 📏

**When:** Weekly or bi-weekly to check how big fish are getting

**What it does:** Updates the average weight of fish in a batch

**Steps:**
1. Go to **Sampling** page
2. Select which **Batch** you're measuring
3. Enter details:
   - **Sample Date:** Today
   - **Sample Size:** How many fish did you weigh? (Example: 30 fish)
   - **Average Weight:** Average weight of those fish (Example: 12.5 grams)
   - **Min/Max Weight:** Smallest and biggest fish (optional)
4. Click **Record Sampling**

**What happens:**
- System updates the batch average weight
- Calculates growth rate
- Shows if fish are growing well
- Helps plan harvest time

**Tip:** Always sample at least 30 fish from different parts of the tank for accuracy!

---

### 3. Mortality (Recording Deaths) ☠️

**When:** You find dead fish in a tank

**What it does:** Tracks fish deaths to monitor health

**Steps:**

**For a tank with ONE batch:**
1. Go to **Mortality** page
2. Select **Tank**
3. System shows which batch is in that tank
4. Enter:
   - **Date:** Today
   - **Total Fish Died:** How many dead fish? (Example: 150)
   - **Cause:** Why did they die? (Disease, low oxygen, etc.)
   - **Notes:** Any observations
5. Click **Record Mortality**

**For a tank with MULTIPLE batches:**
(This happens after grading - see Grading section below)

- **Option A - Auto-split:** System divides deaths proportionally
- **Option B - Manual split:** You say how many died from each batch

**What happens:**
- Batch fish count decreases
- System tracks survival rate
- Helps identify problems

**Important:** Record deaths every day! This helps you notice problems early.

---

### 4. Water Testing 💧

**When:** Daily (especially in first 2 weeks), then every 2-3 days

**What it does:** Monitors water quality to keep fish healthy

**Steps:**
1. Go to **Water Tests** page
2. Enter **Date & Time**
3. Add tanks (can test multiple at once):
   - Click **+ Add Tank**
   - Select tank
   - Enter measurements:
     - **Dissolved Oxygen (DO):** Should be > 4 mg/L
     - **pH:** Should be 7.0-8.5
     - **Temperature:** Ideal around 28-30°C
     - **Ammonia:** Should be < 0.5 mg/L
     - **Other parameters** if you measure them
   - Repeat for other tanks
4. Click **Record Water Tests**

**Alert levels (watch out!):**
- ⚠️ DO < 4 mg/L = Danger! Fish need oxygen
- ⚠️ Ammonia > 0.5 mg/L = Toxic, fix quickly
- ⚠️ Nitrite > 0.3 mg/L = Harmful

**What to do if you see red alerts:**
- Low oxygen → Turn on more aerators
- High ammonia → Add probiotics, reduce feeding
- Talk to your supervisor immediately!

---

### 5. Tank Inputs (Adding Chemicals/Probiotics) 🧪

**When:** You add lime, probiotics, or other treatments to tanks

**What it does:** Tracks what chemicals/supplements you added

**Steps:**
1. Go to **Tank Inputs** page
2. Enter details:
   - **Date & Time**
   - **Type:** Chemical, Probiotic, Carbon Source, Mineral, Other
   - **Item Name:** What are you adding? (Example: "Lime powder")
   - **Unit:** kg, liters, etc.
   - **Reason:** Why? (Example: "pH adjustment")
3. Add tanks:
   - Select each tank
   - Enter amount for each tank
4. Click **Record Input**

**What happens:**
- Tracks chemical usage
- Updates costs
- Helps analyze what treatments work

---

### 6. Harvest 🎣

**When:** Fish reach market size and you sell them

**What it does:** Records fish sold, calculates profit

**Steps:**
1. Go to **Harvests** page
2. Select **Tank** (and batch if multiple)
3. Enter harvest details:
   - **Date:** Today
   - **Type:**
     - **Partial** = Catching some fish, leaving rest to grow
     - **Final** = Catching all remaining fish
   - **Total Fish Count:** How many fish caught?
   - **Total Weight (kg):** Total weight of caught fish
4. Enter **Grading** (optional):
   - Grade A: XX kg (largest fish)
   - Grade B: XX kg (medium)
   - Grade C: XX kg (small)
   - Reject: XX kg (damaged/dead)
5. Enter **Sales Info:**
   - **Buyer:** Who bought the fish?
   - **Price per kg:** How much per kg?
   - Revenue calculates automatically
6. Click **Record Harvest**

**What happens:**
- Batch fish count decreases
- System calculates profit (revenue - costs)
- If "Final harvest", batch is closed

**Example:**
```
Harvest from Tank-001, Batch B-2025-001:
- Caught: 45,000 fish
- Total weight: 1,350 kg
- Average: 30 grams per fish
- Price: ₹250 per kg
- Revenue: ₹3,37,500

Grading:
- Grade A: 1,200 kg (best quality)
- Grade B: 120 kg
- Grade C: 30 kg
```

---

## Grading & Transfer

### What is Grading?

Grading is separating fish by size. Why?
- Bigger fish might eat smaller ones
- Different sizes grow at different rates
- Easier to manage similar-sized fish together

**When to grade:** Usually around Day 30-60 when you notice big size differences

### How Grading Works

**Scenario:** You have Batch B-001 with 48,000 fish in Tank-001. Some are big (15g), some are small (7g).

**Steps:**
1. Go to **Transfer** page
2. Select **Graded Transfer** mode
3. Select **Source Batch:** B-001
4. Enter **Grading Date:** Today
5. Define size groups:

   **Group A (Large fish):**
   - Size Label: A
   - Fish Count: 20,000
   - Average Weight: 15g
   - Destination Tank: Tank-005

   **Group B (Small fish):**
   - Size Label: B
   - Fish Count: 28,000
   - Average Weight: 7.5g
   - Destination Tank: Tank-006

6. Verify total = 48,000 fish (must match!)
7. Add notes: "60-day grading"
8. Click **Complete Graded Transfer**

**What happens:**
- Original batch B-001 becomes inactive
- Creates new batches:
  - B-001-A: 20,000 large fish in Tank-005
  - B-001-B: 28,000 small fish in Tank-006
- Each new batch inherits history (costs, stocking date)
- From now on, you manage them separately

**Benefits:**
- Fish grow better with similar-sized companions
- Prevents bullying/cannibalism
- Easier to harvest at optimal size

### Normal Transfer (Moving Without Grading)

**When:** You want to move all fish from one tank to another (no size separation)

**Steps:**
1. Go to **Transfer** page
2. Select **Normal Transfer**
3. Select **Batch** to move
4. Select **Destination Tank**
5. Click **Transfer**

**Why transfer?**
- Original tank needs cleaning
- Moving to bigger tank
- Better location

---

## Reports & Performance

### Viewing Batch Performance

**To see how a batch is doing:**
1. Go to **Batches** page
2. Click on any batch code
3. View performance tab

**Metrics you'll see:**
- **Survival Rate:** What % of fish are still alive?
- **FCR (Feed Conversion Ratio):** How much feed to grow 1 kg of fish? (lower is better!)
- **Growth Rate:** How fast are fish growing?
- **Total Cost:** How much spent so far?
- **Projected Revenue:** Expected money from harvest

**Example:**
```
Batch B-2025-001 Performance (Day 90):
- Started: 50,000 fish @ 0.5g
- Current: 47,500 fish @ 25g (survival = 95%)
- Total feed used: 1,450 kg
- FCR: 1.22 (good!)
- Total cost: ₹95,000
- Estimated harvest: 1,187 kg @ ₹250/kg = ₹2,96,750
- Projected profit: ₹2,01,750
```

### Feeding History

See all past feeding sessions:
1. Go to **Feeding History**
2. Filter by tank, batch, or date range
3. Review what was fed when

### Water Test History

See water quality trends over time:
1. Go to **Water Test History**
2. Select tank and date range
3. View charts showing DO, pH, temperature trends
4. Spot patterns or problems

---

## Best Practices (How to Do It Right!)

### Daily Checklist

**Morning:**
- [ ] Check all tanks visually (any problems?)
- [ ] Remove and count dead fish
- [ ] Test water (especially DO and temperature)
- [ ] First feeding session
- [ ] Record everything in the app

**Afternoon:**
- [ ] Second feeding session
- [ ] Check aerators are working

**Evening:**
- [ ] Final feeding session
- [ ] Evening water test
- [ ] Review dashboard alerts

### Weekly Tasks
- [ ] Sample fish (weigh at least 30 fish)
- [ ] Full water quality tests
- [ ] Check mortality trends (is it increasing?)
- [ ] Review growth rates

### Monthly Tasks
- [ ] Full batch performance review
- [ ] Check if grading is needed
- [ ] Equipment maintenance
- [ ] Cost analysis

### Smart Habits

✅ **Record immediately** - Don't wait! Data is most accurate when fresh
✅ **Be consistent** - Test water at same time each day
✅ **Sample properly** - Catch fish from different areas of tank
✅ **Watch for patterns** - Is mortality increasing? Is growth slowing?
✅ **Check alerts daily** - Red alerts need immediate action

---

## Troubleshooting

### Problem: Can't Create Batch - "Tank Already Has Active Batch"

**What it means:** Tank is occupied by another batch

**Fix:**
- Check which batch is in the tank
- If old batch is done, record final harvest to close it
- Or use a different empty tank

### Problem: High Mortality

**Possible causes:**
- Poor water quality (check DO, ammonia)
- Disease outbreak
- Temperature stress
- Poor quality fingerlings

**What to do:**
1. Test water immediately
2. Record mortality in app
3. Check water quality history for patterns
4. Talk to supervisor
5. May need to add probiotics or reduce feeding

### Problem: FCR Too High (>2.0)

**What it means:** Using too much feed to grow fish (expensive!)

**Possible causes:**
- Overfeeding
- Poor quality feed
- Fish are sick
- Inaccurate measurements

**What to do:**
1. Review recent feeding amounts
2. Check fish health
3. Verify sampling measurements
4. Reduce feeding slightly and monitor

### Problem: Fish Not Growing Well

**Check:**
- Are you feeding enough? (but not too much!)
- Is water quality good?
- Are fish healthy? (any disease signs?)
- Is it too crowded?

**What to do:**
1. Review feeding history
2. Check water test results
3. Sample to get accurate weight
4. Talk to supervisor about adjustments

---

## Understanding Key Terms

| Term | What It Means | Example |
|------|---------------|---------|
| **Batch** | Group of fish stocked together | B-2025-001 |
| **Stocking** | Putting baby fish in tank | Day 0 |
| **Sampling** | Weighing fish to check growth | Weighed 30 fish, avg 12g |
| **FCR** | Feed Conversion Ratio - feed needed per 1kg fish growth | 1.3 = used 1.3kg feed to grow 1kg fish |
| **DO** | Dissolved Oxygen - oxygen in water | Should be >4 mg/L |
| **Grading** | Separating fish by size | Large vs. small groups |
| **Harvest** | Catching and selling fish | Final = all fish, Partial = some fish |
| **Biomass** | Total weight of all fish | 50,000 fish × 20g = 1,000kg |

---

## Quick Reference

### Water Quality - Good vs. Bad

| Parameter | Good | Warning | Danger |
|-----------|------|---------|--------|
| DO | > 5 mg/L | 4-5 mg/L | < 4 mg/L |
| pH | 7.5-8.2 | 7.0-7.4 or 8.3-8.5 | < 7.0 or > 8.5 |
| Ammonia | < 0.2 mg/L | 0.2-0.5 mg/L | > 0.5 mg/L |
| Temperature | 28-30°C | 26-28°C or 30-32°C | < 26°C or > 32°C |

### Typical Batch Timeline

- **Day 0:** Stock 50,000 baby fish @ 0.5g
- **Day 15:** Sample: ~47,000 fish @ 2g
- **Day 30:** Sample: ~46,000 fish @ 5g
- **Day 60:** Grade if needed, or Sample: ~45,000 fish @ 12g
- **Day 90:** Sample: ~44,000 fish @ 20g
- **Day 120:** Harvest: ~43,000 fish @ 30g

---

## Need Help?

- Check the dashboard for alerts
- Review water test history for problems
- Ask your supervisor or manager
- Look at past batches for comparison

Remember: Fish farming is a daily commitment. Small attention to detail = Big success! 🐟
