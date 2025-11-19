# Biofloc Module - User Guide

**Version:** 1.1.0
**Audience:** Farm Operators, Production Managers, Data Entry Staff

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Tank Management](#tank-management)
4. [Batch Management](#batch-management)
5. [Daily Operations](#daily-operations)
6. [Multi-Batch Scenarios](#multi-batch-scenarios)
7. [Grading & Transfer](#grading--transfer)
8. [Reporting & Analytics](#reporting--analytics)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Module

1. Log in to the Farm Management System
2. Navigate to **Biofloc** from the main menu
3. You'll land on the Dashboard showing current status

### Navigation

**Main Pages:**
- **Dashboard** - Overview and alerts
- **Tanks** - Manage tank infrastructure
- **Batches** - View and manage fish batches

**Daily Operations:**
- **Feeding** - Record feed for multiple tanks
- **Sampling** - Record fish measurements
- **Mortality** - Record deaths
- **Water Tests** - Record water quality
- **Tank Inputs** - Add chemicals/probiotics
- **Harvests** - Record harvest events
- **Transfer** - Move or grade batches

**History Views:**
- **Feeding History** - Past feeding sessions
- **Water Test History** - Water quality trends
- **Tank Inputs History** - Chemical usage

---

## Dashboard Overview

The dashboard provides at-a-glance information about your biofloc operation.

### Key Metrics

**Infrastructure Status:**
- **Active Tanks:** Number of tanks currently in use
- **Available Tanks:** Empty tanks ready for stocking
- **Maintenance Tanks:** Tanks under maintenance

**Production Status:**
- **Active Batches:** Total batches currently growing
- **Total Fish Count:** Combined population across all batches
- **Total Biomass:** Total weight of fish (in kg)
- **Avg Tank Utilization:** Percentage of tanks in use

**Alerts & Warnings:**
- **Low DO Alerts:** Tanks with dissolved oxygen < 4 mg/L
- **High Ammonia Alerts:** Tanks with ammonia > 0.5 mg/L
- **Recent Mortalities (7 days):** Total deaths in last week
- **Upcoming Harvests:** Batches approaching harvest size

### Alert Colors

- 🟢 **Green:** Normal operation
- 🟡 **Yellow:** Warning - attention needed
- 🔴 **Red:** Critical - immediate action required

---

## Tank Management

### Creating a New Tank

1. Go to **Tanks** page
2. Click **+ New Tank** button
3. Fill in details:
   - **Tank Code:** Unique identifier (e.g., T-001, Tank-A1)
   - **Capacity (L):** Total water volume
   - **Dimensions:** Length, width, depth (optional)
   - **Location:** Physical location description
   - **Notes:** Any additional information
4. Click **Save**

**Best Practice:** Use a consistent naming convention (e.g., Block-Row-Number: A1-01, A1-02)

### Tank Status

- **Active:** Currently has fish
- **Maintenance:** Being cleaned/repaired
- **Empty:** Available for stocking

### Editing Tanks

1. Click on a tank in the list
2. Click **Edit** button
3. Update fields as needed
4. Click **Save**

**Note:** Cannot delete tanks with historical data. Use "inactive" status instead.

---

## Batch Management

### Creating a New Batch

A batch represents a group of fish stocked on the same day.

1. Go to **Batches** page
2. Click **+ New Batch** button
3. Fill in required information:
   - **Batch Code:** Unique identifier (e.g., B-2025-001)
   - **Species:** Fish species (e.g., Litopenaeus vannamei)
   - **Source:** Hatchery or supplier name
   - **Tank:** Select destination tank
   - **Stocking Date:** Date fish were added
   - **Initial Count:** Number of fish stocked
   - **Initial Avg Weight (g):** Average weight at stocking
   - **Notes:** PL stage, quality observations, etc.
4. Click **Create Batch**

**What Happens:**
- Batch is created with status "active"
- Tank is assigned to this batch
- Initial biomass is calculated automatically
- Cycle costs record is initialized

### Batch Lifecycle

```
Stocking → Growing → Grading (optional) → Harvesting
   ↓         ↓           ↓                    ↓
Active    Active      Graded              Harvested
```

### Viewing Batch Details

Click on any batch to see:
- **Current Metrics:** Count, weight, biomass
- **Performance:** FCR, SGR, survival rate
- **Feeding History:** All feed given
- **Sampling History:** Growth measurements
- **Mortality Events:** Deaths recorded
- **Harvests:** Partial/final harvests
- **Cost Summary:** Total costs and revenue

---

## Daily Operations

### 1. Feeding (Multi-Tank)

Record feed given to multiple tanks in one session.

**Scenario:** Morning feeding for 7 tanks

1. Go to **Feeding** page
2. **Session Details** (applies to all tanks):
   - Feeding Date: Today's date
   - Session Number: 1 (morning), 2 (afternoon), 3 (evening)
   - Feed Time: 08:00
3. **Add Tanks:**
   - Click **+ Add Tank**
   - Select tank from dropdown
   - Enter feed quantity (kg)
   - Optional: Tank-specific notes
   - Repeat for all 7 tanks
4. **Feed Item:**
   - Select from inventory OR enter manually
   - SKU: FEED-001
   - Total feed shows sum across all tanks
5. Click **Record Feeding**

**What Happens:**
- Creates feeding records for each tank/batch
- Deducts feed from inventory (FIFO method)
- Updates batch `total_feed_kg`
- Updates cycle costs `feed_cost`
- Recalculates FCR

**Tip:** Use "Copy from Yesterday" button to duplicate previous day's setup

---

### 2. Sampling

Record fish measurements to track growth.

1. Go to **Sampling** page
2. Select **Batch**
3. Enter sample details:
   - **Sample Date:** Date measured
   - **Sample Size:** Number of fish measured
   - **Avg Weight (g):** Average weight of sample
   - **Min/Max Weight:** Range (optional)
   - **Std Deviation:** If calculated (optional)
   - **Avg Length (cm):** Average length (optional)
4. Click **Record Sampling**

**What Happens:**
- Updates batch `current_avg_weight_g`
- Recalculates biomass
- Updates SGR and FCR
- Triggers growth curve update

**Best Practice:**
- Sample at least weekly during first 30 days
- Sample bi-weekly after Day 30
- Use minimum 30 fish for representative sample
- Always sample from multiple locations in tank

---

### 3. Mortality (Multi-Batch Support)

Record fish deaths, with special handling for tanks containing multiple batches.

**Scenario 1: Tank with Single Batch**
1. Go to **Mortality** page
2. Select **Tank:** T-001
3. Tank shows: Batch B-001 (48,500 fish @ 12g)
4. Enter:
   - Mortality Date: Today
   - **Total Fish Died:** 150
   - Cause: Disease
   - Notes: White spot observed
5. Click **Record Mortality**

Deaths are automatically assigned to the single batch.

---

**Scenario 2: Tank with Multiple Batches**

Example: Tank T-005 contains:
- Batch B-001-A: 20,000 fish @ 15g
- Batch B-001-B: 28,000 fish @ 10g
- Total: 48,000 fish

You observe 200 dead fish.

**Option 1A - Auto-Split (Default):**
1. Select Tank T-005
2. Enter **Total Fish Died:** 200
3. Select **Auto-split (proportional by population)**
4. System shows preview:
   - B-001-A: 83 fish (20,000/48,000 × 200)
   - B-001-B: 117 fish (28,000/48,000 × 200)
5. Click **Record Mortality**

**Option 1B - Manual Split:**
1. Select Tank T-005
2. Enter **Total Fish Died:** 200
3. Select **Manual split (I know which batch died)**
4. Enter deaths per batch:
   - B-001-A: 50 fish
   - B-001-B: 150 fish
   - Total: 200 (must match!)
5. Click **Record Mortality**

**When to Use Manual:**
- You can identify which batch died (e.g., smaller fish more affected)
- Deaths are clustered in one area of tank
- Visual observation shows pattern

**When to Use Auto:**
- Deaths are evenly distributed
- Uncertain which batch is affected
- Quick recording needed

---

### 4. Water Tests (Multi-Tank)

Record water quality for multiple tanks at once.

**Scenario:** Testing 3 tanks this morning

1. Go to **Water Tests** page
2. **Test Date & Time:** Today, 08:00
3. **Add Tanks:**
   - Click **+ Add Tank**
   - Select Tank T-001
   - Enter parameters:
     - Dissolved Oxygen: 5.2 mg/L
     - pH: 7.8
     - Temperature: 28.5°C
     - Ammonia: 0.02 mg/L
     - Nitrite: 0.01 mg/L
     - Nitrate: 5.0 mg/L
     - Alkalinity: 120 mg/L
     - Floc Volume: 15 mL/L
     - Notes: Good conditions
   - Repeat for T-002, T-003
4. Click **Record Water Tests**

**Alert Thresholds:**
- ⚠️ DO < 4 mg/L
- ⚠️ Ammonia > 0.5 mg/L
- ⚠️ Nitrite > 0.3 mg/L

**Best Practice:**
- Test daily during first 2 weeks
- Test every other day after stabilization
- Test immediately if fish behavior changes
- Always test in morning before feeding

---

### 5. Tank Inputs (Chemicals, Probiotics)

Record chemicals, probiotics, and supplements added to tanks.

**Scenario:** Adding lime to 5 tanks for pH adjustment

1. Go to **Tank Inputs** page
2. **Input Details** (shared):
   - Date: Today
   - Time: 14:00
   - Type: Chemical
   - Item Name: Calcium Hydroxide (Lime)
   - Unit: kg
   - Reason: pH Adjustment
3. **Add Tanks:**
   - Tank T-001: 2.5 kg
   - Tank T-002: 3.0 kg
   - Tank T-003: 2.0 kg
   - Tank T-004: 2.5 kg
   - Tank T-005: 3.5 kg
4. **Total shows:** 13.5 kg across 5 tanks
5. Click **Record Input**

**What Happens:**
- Records input per tank
- Updates chemical costs
- Tracks total usage
- Optional: Deducts from inventory

**Input Types:**
- **Chemical:** pH adjusters, disinfectants
- **Probiotic:** Beneficial bacteria
- **Carbon Source:** Molasses, wheat flour
- **Mineral:** Calcium, magnesium supplements
- **Other:** Miscellaneous additives

---

### 6. Harvests (Multi-Batch Support)

Record partial or final harvests with smart batch matching.

**Scenario: Tank with 2 Batches**

Tank T-005 contains:
- Batch B-001-A: 19,500 fish @ 15g avg
- Batch B-001-B: 27,000 fish @ 10g avg

You harvest 5,000 fish totaling 62.5 kg.

**Harvested Avg Weight:** 62,500g / 5,000 = 12.5g

**Smart Allocation (2B - Recommended):**
1. Select **Tank:** T-005
2. Enter:
   - Harvest Date: Today
   - Type: Partial
   - **Total Fish Count:** 5,000
   - **Total Weight (kg):** 62.5
3. System calculates harvested avg: **12.5g**
4. Select **Smart allocation (weight-based)**
5. System suggests:
   - B-001-A (15g avg): 500 fish (10% - further from 12.5g)
   - B-001-B (10g avg): 4,500 fish (90% - closer to 12.5g)
6. Adjust if needed
7. Enter grading (optional):
   - Grade A: 50 kg
   - Grade B: 10 kg
   - Grade C: 2 kg
   - Reject: 0.5 kg
8. Enter sales info:
   - Buyer: Market ABC
   - Price per kg: ₹250
   - Revenue: ₹15,625 (auto-calculated)
9. Click **Record Harvest**

**Auto-Split Option (2A):**
- Allocates proportionally by population
- B-001-A: 2,096 fish (19,500/46,500 × 5,000)
- B-001-B: 2,904 fish (27,000/46,500 × 5,000)

**When to Use Smart:**
- You know the harvested average weight
- Want to match weight profiles
- Selective harvesting by size

**When to Use Auto:**
- Random sampling harvest
- Weight matching not important
- Quick recording

---

## Multi-Batch Scenarios

### Why Multiple Batches in One Tank?

Common scenarios:
1. **After grading:** Different size groups assigned to same tank
2. **Combining batches:** Moving undersized fish from multiple batches
3. **Thinning operations:** Redistributing for optimal density

### Feeding Multi-Batch Tanks

**Automatic Allocation:**
- Feed is recorded at **tank level**
- System automatically splits feed cost among batches proportionally by biomass

**Example:**
```
Tank T-005:
  - Batch A: 20,000 fish @ 15g = 300kg (60%)
  - Batch B: 10,000 fish @ 10g = 100kg (40%)
  - Total: 400kg

Feed given: 10 kg @ ₹450/kg = ₹4,500

Allocated:
  - Batch A: ₹4,500 × 0.60 = ₹2,700
  - Batch B: ₹4,500 × 0.40 = ₹1,800
```

This ensures accurate FCR calculation per batch.

---

## Grading & Transfer

### Normal Transfer

Move an entire batch from one tank to another.

**Use Cases:**
- Tank maintenance required
- Better tank available
- Overcrowding

**Steps:**
1. Go to **Transfer** page
2. Select **Normal Transfer** mode
3. Select **Source Batch:** B-001
4. Current tank shown: T-001
5. Select **Destination Tank:** T-005
6. Transfer Date: Today
7. Notes: "Moving to larger tank"
8. Click **Transfer Batch**

**What Happens:**
- Batch assignment updated to new tank
- Previous tank freed up
- Transfer history recorded

---

### Graded Transfer

Separate a batch by size, creating new child batches (most common at Day 30-60).

**Use Case:**
You've been growing Batch B-001 for 60 days:
- Population: 48,000 fish
- Average weight: 10g
- But size variation is significant (5g to 15g)

You grade and separate into 2 size groups.

**Steps:**

1. Go to **Transfer** page
2. Select **Graded Transfer** mode
3. **Source Batch:** B-001 (48,000 fish @ 10g avg in Tank T-001)
4. **Grading Date:** Today

5. **Define Size Groups:**

   **Size Group A (Large):**
   - Size Label: A
   - Fish Count: 20,000
   - Avg Weight: 15g
   - Biomass: 300kg
   - Destination Tank: T-005

   **Size Group B (Medium):**
   - Fish Count: 28,000
   - Avg Weight: 7.5g
   - Biomass: 210kg
   - Destination Tank: T-006

6. **Validation:**
   - Total fish: 48,000 ✅ (matches source)
   - Total biomass: 510kg
   - Size A: 58.8% biomass
   - Size B: 41.2% biomass

7. **Notes:** "60-day grading, 2 size groups"

8. Click **Complete Graded Transfer & Create New Batches**

---

**What Happens:**

**1. New Batches Created:**
- `B-001-A`: 20,000 fish @ 15g → Tank T-005
- `B-001-B`: 28,000 fish @ 7.5g → Tank T-006

**2. Historical Data Inherited:**

Original Batch B-001 had:
- Stocking Date: Jan 1, 2025
- Feed Cost: ₹50,000
- Chemical Cost: ₹5,000
- Total Cost: ₹55,000

Allocated to children based on biomass:

**Batch B-001-A (58.8% biomass):**
- Stocking Date: Jan 1, 2025 (inherited)
- Initial Count: 20,000
- Initial Weight: 15g (weight at grading)
- Feed Cost: ₹29,400 (58.8% × ₹50,000)
- Chemical Cost: ₹2,940
- Total Cost: ₹32,340
- Parent: B-001

**Batch B-001-B (41.2% biomass):**
- Stocking Date: Jan 1, 2025 (inherited)
- Initial Count: 28,000
- Initial Weight: 7.5g (weight at grading)
- Feed Cost: ₹20,600 (41.2% × ₹50,000)
- Chemical Cost: ₹2,060
- Total Cost: ₹22,660
- Parent: B-001

**3. Parent Batch B-001:**
- Status changed to: "graded"
- Tank assignment ended
- Becomes read-only historical record

---

**Why This Matters:**

✅ **Accurate FCR:**
- Each size group tracks its own feed costs going forward
- Historical costs properly allocated
- True FCR calculation per size

✅ **Accurate Cycle Duration:**
- Both children inherit original stocking date (Jan 1)
- If harvested on Mar 15, cycle = 73 days (not 13 days from grading!)

✅ **Proper Initial Weight:**
- B-001-A starts at 15g (weight at grading)
- Growth from 15g → harvest weight
- SGR calculated correctly

✅ **Full Traceability:**
- Can trace back to parent batch
- Historical feeding, sampling, mortality visible
- Complete audit trail

---

### After Grading

**Continue Normal Operations:**

Each child batch is now independent:
- Record feeding separately (or together if in same tank)
- Sample each batch individually
- Track mortality per batch
- Eventually harvest each batch

**Example Timeline:**
```
Day 0:   Stock B-001 (50,000 fish @ 0.5g)
Day 30:  Sample: 48,500 fish @ 5g
Day 60:  Grade into B-001-A and B-001-B
Day 90:  Sample B-001-A: 19,800 fish @ 25g
Day 90:  Sample B-001-B: 27,500 fish @ 18g
Day 120: Harvest B-001-A (final)
Day 135: Harvest B-001-B (final)
```

---

## Reporting & Analytics

### Batch Performance Report

View comprehensive metrics for any batch:

1. Go to **Batches** page
2. Click on batch code
3. View **Performance** tab

**Metrics Displayed:**
- Cycle Duration
- Survival Rate
- Biomass Gain
- Average Daily Gain
- FCR (Feed Conversion Ratio)
- SGR (Specific Growth Rate)
- Total Cost
- Total Revenue
- Gross Profit
- ROI %

**Growth Curve:**
- Chart showing weight progression over time
- Based on sampling data
- Trend line fitted

**Cost Breakdown:**
- Fingerling cost
- Feed cost (largest component)
- Chemical cost
- Labor cost
- Utilities
- Other costs

---

### Feeding History

Track all feed given over time:

1. Go to **Feeding History**
2. **Filters:**
   - Tank: Specific tank or all
   - Batch: Specific batch or all
   - Date Range: Last 30 days, custom range
3. View table showing:
   - Date/Time
   - Tank
   - Batch
   - Feed items
   - Quantity
   - Cost
   - Session number

**Use Cases:**
- Verify feed records
- Calculate feed efficiency
- Track feed inventory usage
- Cost analysis

---

### Water Test History

Analyze water quality trends:

1. Go to **Water Test History**
2. Select tank and date range
3. View trends:
   - DO over time
   - pH stability
   - Ammonia/Nitrite/Nitrate levels
   - Temperature variations

**Alert Patterns:**
- Identify recurring issues
- Correlate with mortality events
- Optimize intervention timing

---

## Best Practices

### Daily Checklist

**Morning (6:00-8:00):**
- [ ] Visual inspection of all tanks
- [ ] Remove dead fish, count and record
- [ ] Check water quality (DO, temperature)
- [ ] First feeding session
- [ ] Record any abnormal behavior

**Midday (12:00-14:00):**
- [ ] Second feeding session
- [ ] Monitor floc volume
- [ ] Check aerators functioning

**Evening (18:00-20:00):**
- [ ] Final feeding session
- [ ] Evening water quality check
- [ ] Record daily totals

**Weekly:**
- [ ] Fish sampling (at least 30 fish)
- [ ] Comprehensive water tests
- [ ] Review mortality trends
- [ ] Check growth rates vs. targets

**Monthly:**
- [ ] Batch performance review
- [ ] Cost analysis
- [ ] Equipment maintenance
- [ ] Grading evaluation (Days 30-60)

---

### Data Entry Best Practices

1. **Be Consistent:**
   - Use same units (don't mix grams and kg)
   - Standard time format (24-hour)
   - Consistent naming conventions

2. **Be Timely:**
   - Record data same day
   - Don't batch-enter old data
   - Update immediately after sampling

3. **Be Accurate:**
   - Double-check fish counts
   - Verify weight measurements
   - Confirm tank selections

4. **Add Context:**
   - Use notes fields liberally
   - Document unusual events
   - Record weather conditions

5. **Review Regularly:**
   - Check dashboard alerts daily
   - Review weekly trends
   - Investigate anomalies promptly

---

### Grading Decision Guide

**When to Grade:**
- Size variation > 30% (some fish 2x weight of others)
- Visible groupings in tank
- Days 30-60 typical timing
- Before size-based cannibalism starts

**How Many Groups:**
- **2 groups:** Most common, easier management
- **3 groups:** When variation is very high

**Size Matching:**
- Keep similar sizes together
- Larger fish → larger tanks (if possible)
- Consider growth rate differences

---

### Cost Management

**Track Everything:**
- All feed usage (largest cost)
- Chemical applications
- Labor hours (if applicable)
- Utilities (electricity for aeration)

**Regular Review:**
- Compare actual vs. target FCR
- Identify cost overruns early
- Benchmark against previous batches

**Optimize:**
- Feed efficiency (avoid overfeeding)
- Chemical usage (test before adding)
- Stock at optimal density
- Harvest at best market price

---

## Troubleshooting

### Common Issues

**Issue 1: Cannot Create Batch - "Tank already has an active batch"**

**Cause:** Tank is currently assigned to another batch.

**Solution:**
- Check which batch is in the tank
- If batch should be moved, use Transfer
- If batch is completed, use Harvest (final) to close it
- Multi-batch scenarios: You CAN have multiple batches after grading or manual assignment

---

**Issue 2: Mortality/Harvest totals don't match batches**

**Cause:** Multi-batch tank, allocation mismatch.

**Solution:**
- Use Manual split mode
- Verify total equals sum across batches
- Check batch current counts

---

**Issue 3: FCR is very high (>2.0)**

**Possible Causes:**
- Overfeeding
- Poor feed quality
- Disease affecting growth
- Inaccurate weight measurements

**Actions:**
- Review feeding rates
- Check recent sampling data
- Inspect fish health
- Verify feed batch quality

---

**Issue 4: Grading form shows "Total mismatch" error**

**Cause:** Sum of size group fish counts ≠ source batch count

**Solution:**
- Double-check your counts
- Make sure you didn't miss any fish
- Adjust one of the groups to match total

**Example:**
- Source: 48,000 fish
- Group A: 20,000
- Group B: 27,000
- Total: 47,000 ❌

Fix: Increase Group B to 28,000 ✅

---

**Issue 5: Dashboard shows wrong tank count**

**Cause:** Tanks marked inactive or status not updated.

**Solution:**
- Go to Tanks page
- Check tank status filters
- Update tank status if needed
- Refresh dashboard

---

### Getting Help

**Data Issues:**
1. Check your entries for typos
2. Verify date/time are correct
3. Review recent history for the batch/tank
4. Contact system administrator if data corruption suspected

**Performance Questions:**
1. Compare to industry benchmarks
2. Review all recorded events (sampling, feeding, mortality)
3. Check water quality history for anomalies
4. Consult with aquaculture expert

**System Errors:**
1. Note exact error message
2. Try refreshing the page
3. Log out and log back in
4. Report to technical support with:
   - Error message
   - What you were trying to do
   - Screenshots if possible

---

## Appendix: Typical Batch Timeline

### Example: 120-Day Grow-Out Cycle

**Day 0 - Stocking:**
- Receive PL12 from hatchery
- Stock 50,000 @ 0.5g avg (25kg biomass)
- Record in system: Create batch

**Days 1-15 - Establishment:**
- Feed 5-8 times daily, small amounts
- Monitor water quality closely (daily tests)
- Expect 5-10% mortality
- Record: Daily feeding, mortality, water tests

**Day 15 - First Sampling:**
- Sample 50 fish
- Expected: ~2g avg, 47,000 count
- Record sampling in system

**Days 16-30 - Rapid Growth:**
- Feed 4-5 times daily
- Increase rations as biomass grows
- Water quality critical

**Day 30 - Second Sampling:**
- Expected: ~5g avg, 46,000 count
- Survival: 92%
- Record sampling

**Days 31-60 - Size Variation Emerges:**
- Some fish noticeably larger
- Monitor feeding competition
- Plan grading if variation > 30%

**Day 60 - Grading (Optional):**
- Sample shows 5-15g range
- Decision: Grade into 2 groups
- Large group: 20,000 @ 12g → Tank A
- Medium group: 26,000 @ 7g → Tank B
- Record grading in system

**Days 61-90 - Separate Growth:**
- Manage as independent batches
- Large group grows faster
- Different feeding rates

**Day 90 - Sampling Both:**
- Tank A: 19,500 @ 25g (487kg biomass)
- Tank B: 25,500 @ 18g (459kg biomass)

**Days 91-120 - Harvest Preparation:**
- Reduce feeding 24h before harvest
- Market size target: 30g+

**Day 120 - Final Harvest:**
- Tank A: 19,000 fish @ 32g = 608kg
- FCR (Tank A): 1.3
- SGR: 1.2%
- Survival: 95% (from grading point)
- Revenue: ₹1,50,000
- Profit: ₹65,000

**Record final harvest in system.**

---

**End of User Guide**

For technical details and architecture, see [Technical Guide](./technical-guide.md).
