# BATCH TRACKING MODULE - BACKEND TESTING GUIDE

**Version:** 1.0.0
**Created:** 2024-12-04
**Module:** Batch Tracking (Module 2.2)

---

## 🎯 **What's Been Built**

✅ Complete backend implementation with:
- **FY-based batch numbering:** B/2526/0001 (prefix/fy/sequence)
- **Auto FY rollover:** Resets on April 1st each year
- **5-day auto-archive:** Batches archived 5 days after delivery
- **Configurable settings:** Prefix, starting number, FY dates
- **9 API endpoints** + 2 configuration endpoints
- **Complete database schema** with 4 tables

---

## 📋 **Prerequisites**

Before testing, ensure you have:
1. ✅ Python 3.8+ installed
2. ✅ PostgreSQL/Supabase database running
3. ✅ Database connection configured in `.env`
4. ✅ Backend dependencies installed

---

## 🚀 **Step 1: Run Database Migration**

### **Option A: Using Migration Script**
```bash
cd backend
python run_migration.py migrations/014_batch_tracking.sql
python run_migration.py migrations/015_batch_tracking_module.sql
```

### **Option B: Direct SQL Execution**
```bash
# Connect to your database and run:
psql -U your_user -d your_database -f backend/migrations/014_batch_tracking.sql
psql -U your_user -d your_database -f backend/migrations/015_batch_tracking_module.sql
```

### **Verify Migration Success**
Check that tables were created:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('batches', 'batch_history', 'batch_documents', 'batch_sequence');
```

Expected output: 4 tables

Check batch_sequence initial values:
```sql
SELECT * FROM batch_sequence;
```

Expected:
| id | current_number | prefix | financial_year | fy_start_date | fy_end_date |
|----|---------------|--------|---------------|--------------|-------------|
| 1  | 0             | B      | 2526          | 2025-04-01   | 2026-03-31  |

---

## 🏃 **Step 2: Start FastAPI Server**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Database connected (Pool: 5-20, prepared statements: disabled)
✅ All services initialized successfully
INFO:     Application startup complete.
```

---

## 📖 **Step 3: Open Swagger UI**

Navigate to: **http://localhost:8000/docs**

You'll see interactive API documentation with all endpoints grouped under **"Batch Tracking"**.

---

## 🧪 **Step 4: Test API Endpoints**

### **Test 1: Get Configuration**
**Endpoint:** `GET /api/v1/batches/config`

**Steps:**
1. Click "Try it out"
2. Click "Execute"

**Expected Response:**
```json
{
  "prefix": "B",
  "current_number": 0,
  "financial_year": "2526",
  "fy_start_date": "2025-04-01",
  "fy_end_date": "2026-03-31",
  "next_batch_number": "B/2526/0001",
  "updated_at": "2024-12-04T10:00:00Z"
}
```

---

### **Test 2: Generate First Batch**
**Endpoint:** `POST /api/v1/batches/generate`

**Steps:**
1. Click "Try it out"
2. Enter request body:
```json
{
  "po_id": 1,
  "grn_id": 1,
  "created_by": "your-user-uuid"
}
```
3. Click "Execute"

**Expected Response:**
```json
{
  "batch_id": 1,
  "batch_number": "B/2526/0001",
  "status": "ordered",
  "created_at": "2024-12-04T10:05:00Z"
}
```

✅ **Success!** You generated your first batch with FY-based numbering!

---

### **Test 3: Generate More Batches**
Repeat Test 2 multiple times with different PO/GRN IDs.

**Expected Batch Numbers:**
- 1st: `B/2526/0001`
- 2nd: `B/2526/0002`
- 3rd: `B/2526/0003`
- etc.

---

### **Test 4: Get Batch Details**
**Endpoint:** `GET /api/v1/batches/{batch_number}`

**Steps:**
1. Click "Try it out"
2. Enter: `B/2526/0001`
3. Click "Execute"

**Expected Response:**
```json
{
  "batch_id": 1,
  "batch_number": "B/2526/0001",
  "status": "ordered",
  "is_repacked": false,
  "parent_batch_number": null,
  "child_batch_number": null,
  "po_id": 1,
  "grn_id": 1,
  "created_at": "2024-12-04T10:05:00Z",
  "archived_at": null,
  "documents": [
    {
      "document_type": "po",
      "document_id": 1,
      "document_number": null
    },
    {
      "document_type": "grn",
      "document_id": 1,
      "document_number": null
    }
  ],
  "history": [
    {
      "stage": "po",
      "event_type": "created",
      "event_details": null,
      "old_status": null,
      "new_status": "ordered",
      "location": null,
      "created_at": "2024-12-04T10:05:00Z",
      "created_by_name": "user@example.com"
    }
  ]
}
```

---

### **Test 5: Search Batches**
**Endpoint:** `POST /api/v1/batches/search`

**Steps:**
1. Click "Try it out"
2. Enter request body:
```json
{
  "page": 1,
  "limit": 10
}
```
3. Click "Execute"

**Expected Response:**
```json
{
  "batches": [
    {
      "batch_id": 3,
      "batch_number": "B/2526/0003",
      "status": "ordered",
      "is_repacked": false,
      "created_at": "2024-12-04T10:10:00Z",
      "farm": null,
      "current_location": null
    },
    {
      "batch_id": 2,
      "batch_number": "B/2526/0002",
      "status": "ordered",
      "is_repacked": false,
      "created_at": "2024-12-04T10:08:00Z",
      "farm": null,
      "current_location": null
    },
    {
      "batch_id": 1,
      "batch_number": "B/2526/0001",
      "status": "ordered",
      "is_repacked": false,
      "created_at": "2024-12-04T10:05:00Z",
      "farm": null,
      "current_location": null
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

---

### **Test 6: Get Active Batches**
**Endpoint:** `GET /api/v1/batches/active`

**Steps:**
1. Click "Try it out"
2. Leave defaults (page=1, limit=50)
3. Click "Execute"

**Expected:** List of all non-archived batches

---

### **Test 7: Add Batch History Event**
**Endpoint:** `POST /api/v1/batches/{batch_number}/history`

**Steps:**
1. Click "Try it out"
2. Enter batch_number: `B/2526/0001`
3. Enter request body:
```json
{
  "stage": "grn",
  "event_type": "received",
  "event_details": {
    "received_qty": 100,
    "damaged_qty": 5,
    "accepted_qty": 95
  },
  "new_status": "received",
  "location": "receiving_area"
}
```
4. Click "Execute"

**Expected Response:**
```json
{
  "history_id": 2,
  "batch_number": "B/2526/0001",
  "created_at": "2024-12-04T10:20:00Z"
}
```

Now fetch batch details again - you'll see the new history event!

---

### **Test 8: Get Batch Timeline**
**Endpoint:** `GET /api/v1/batches/{batch_number}/timeline`

**Steps:**
1. Click "Try it out"
2. Enter: `B/2526/0001`
3. Click "Execute"

**Expected Response:**
```json
{
  "batch_number": "B/2526/0001",
  "timeline": [
    {
      "stage": "po",
      "stage_name": "Purchase Order",
      "timestamp": "2024-12-04T10:05:00Z",
      "status": "completed",
      "details": {}
    },
    {
      "stage": "grn",
      "stage_name": "Goods Receipt",
      "timestamp": "2024-12-04T10:20:00Z",
      "status": "completed",
      "details": {
        "received_qty": 100,
        "damaged_qty": 5,
        "accepted_qty": 95
      }
    }
  ]
}
```

---

### **Test 9: Create Repacked Batch**
**Endpoint:** `POST /api/v1/batches/{batch_number}/repack`

**Steps:**
1. Click "Try it out"
2. Enter batch_number: `B/2526/0001`
3. Enter request body:
```json
{
  "reason": "Cold storage condensation damage",
  "damaged_quantity": 10,
  "repacked_quantity": 8,
  "photos": ["https://example.com/photo1.jpg"],
  "notes": "Repacked into smaller portions"
}
```
4. Click "Execute"

**Expected Response:**
```json
{
  "parent_batch": "B/2526/0001",
  "new_batch_number": "B/2526/0001R",
  "new_batch_id": 4,
  "status": "in_inventory",
  "created_at": "2024-12-04T10:30:00Z"
}
```

✅ **Success!** Repacked batch created with 'R' suffix!

---

### **Test 10: Get Batch Statistics**
**Endpoint:** `GET /api/v1/batches/stats/summary`

**Steps:**
1. Click "Try it out"
2. Click "Execute"

**Expected Response:**
```json
{
  "total_batches": 4,
  "active_batches": 4,
  "archived_batches": 0,
  "repacked_batches": 1,
  "by_status": {
    "ordered": 2,
    "received": 1,
    "in_inventory": 1
  }
}
```

---

### **Test 11: Update Configuration (Admin Only)**
**Endpoint:** `PUT /api/v1/batches/config`

⚠️ **WARNING:** This requires admin authentication!

**Steps:**
1. Click "Try it out"
2. Add query parameters:
   - `prefix`: "BATCH"
   - `starting_number`: 100
3. Click "Execute"

**Expected Response:**
```json
{
  "prefix": "BATCH",
  "current_number": 100,
  "financial_year": "2526",
  "fy_start_date": "2025-04-01",
  "fy_end_date": "2026-03-31",
  "next_batch_number": "BATCH/2526/0101"
}
```

✅ Next batch will be: `BATCH/2526/0101`

---

## 🧪 **Test FY Rollover Logic**

### **Simulate FY Rollover:**

**Option A: Change System Date (Advanced)**
```bash
# Change system date to April 1, 2026
sudo date -s "2026-04-01 10:00:00"

# Generate a batch - it should reset sequence and use FY 2627
# Expected: B/2627/0001

# Restore system date
sudo ntpdate -s time.nist.gov
```

**Option B: Manually Update FY End Date**
```sql
UPDATE batch_sequence
SET fy_end_date = '2024-12-01'  -- Set to yesterday
WHERE id = 1;
```

Then generate a new batch - it will trigger rollover!

---

## ✅ **Success Criteria**

Your backend is working correctly if:

1. ✅ Batches generate with format: `B/2526/0001`
2. ✅ Sequence increments: 0001 → 0002 → 0003
3. ✅ Repacked batches get 'R' suffix: `B/2526/0001R`
4. ✅ Configuration endpoint shows current settings
5. ✅ All endpoints return expected responses
6. ✅ Batch history tracks events correctly
7. ✅ Search and filtering work
8. ✅ Timeline visualizes batch journey

---

## 🐛 **Troubleshooting**

### **Issue: "Batch sequence not initialized"**
**Solution:** Run the migrations again. The initial record should be inserted.

### **Issue: 401 Unauthorized**
**Solution:** You need to authenticate first:
1. Go to `/api/v1/auth/login` endpoint
2. Login with your credentials
3. Copy the access token
4. Click "Authorize" button at top of Swagger UI
5. Paste token in format: `Bearer <your-token>`

### **Issue: Database connection error**
**Solution:** Check your `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

### **Issue: Import errors**
**Solution:** Reinstall dependencies:
```bash
cd backend
pip install -r requirements.txt
```

---

## 📊 **Database Verification Queries**

### **Check Batch Sequence:**
```sql
SELECT * FROM batch_sequence;
```

### **View All Batches:**
```sql
SELECT * FROM batches ORDER BY created_at DESC;
```

### **View Batch History:**
```sql
SELECT b.batch_number, bh.stage, bh.event_type, bh.created_at
FROM batch_history bh
JOIN batches b ON bh.batch_id = b.id
ORDER BY bh.created_at DESC;
```

### **Check Repacked Batches:**
```sql
SELECT b.batch_number, p.batch_number as parent_batch
FROM batches b
LEFT JOIN batches p ON b.parent_batch_id = p.id
WHERE b.is_repacked = true;
```

---

## 🎯 **Next Steps After Backend Testing**

Once you've verified all endpoints work:

### **Option 1: Build Frontend First**
✅ **Recommended** if you want a complete UI before going live
- Faster development (UI + backend together)
- Visual testing
- Better UX feedback

### **Option 2: Integrate with GRN Module**
✅ **Recommended** if GRN module is ready
- Test real workflow (PO → GRN → Batch generation)
- Validate integration points
- Test with actual farm data

### **Option 3: Continue to Wastage Tracking**
✅ **Recommended** if you want complete foundation first
- Both modules work together
- Wastage events link to batches
- Complete traceability

---

## 📝 **Testing Checklist**

Copy this checklist and mark as you test:

- [ ] Migrations ran successfully
- [ ] FastAPI server starts without errors
- [ ] Swagger UI loads at /docs
- [ ] GET /config returns initial configuration
- [ ] POST /generate creates B/2526/0001
- [ ] Sequence increments correctly (0002, 0003...)
- [ ] GET /{batch_number} retrieves batch details
- [ ] POST /search returns filtered results
- [ ] GET /active lists non-archived batches
- [ ] POST /{batch_number}/history adds events
- [ ] GET /{batch_number}/timeline shows journey
- [ ] POST /{batch_number}/repack creates B/2526/0001R
- [ ] GET /stats/summary shows correct counts
- [ ] PUT /config updates settings (admin)
- [ ] Repacked batch cannot be repacked again
- [ ] Database contains expected records

---

## 🚀 **Performance Testing (Optional)**

### **Load Test: Generate 1000 Batches**
```python
import requests
import time

url = "http://localhost:8000/api/v1/batches/generate"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

start = time.time()
for i in range(1000):
    response = requests.post(url, json={
        "po_id": i,
        "grn_id": i,
        "created_by": "test-user"
    }, headers=headers)
    if i % 100 == 0:
        print(f"Generated {i} batches...")

end = time.time()
print(f"Generated 1000 batches in {end - start:.2f} seconds")
```

**Expected:** Should complete in < 30 seconds

---

## 📞 **Support**

If you encounter issues:
1. Check the FastAPI console for error logs
2. Check database logs for SQL errors
3. Verify authentication token is valid
4. Ensure all migrations ran successfully
5. Review the technical design document

---

**Happy Testing! 🎉**

Once backend is verified, we can proceed to build the frontend or integrate with other modules!
