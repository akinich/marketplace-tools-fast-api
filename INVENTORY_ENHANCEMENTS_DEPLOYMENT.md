# Inventory Module Enhancements - Deployment Guide

## Overview

This guide covers the deployment of Phase 1 & 2 inventory enhancements for better biofloc module integration:

**Phase 1: Core Backend**
- ✅ Batch Deduction Endpoint (atomic multi-item operations)
- ✅ Bulk Fetch Endpoint (efficient multi-item retrieval)
- ✅ Database changes (module_batch_id, session_number)

**Phase 2: Reservation System**
- ✅ Stock Reservation system (soft locks)
- ✅ Available vs Reserved quantity tracking
- ✅ Auto-expiry background task (APScheduler)

---

## Pre-Deployment Checklist

- [ ] Backup database
- [ ] Review database migration script: `sql_scripts/v1.3.0_inventory_enhancements_biofloc.sql`
- [ ] Ensure FastAPI backend is stopped
- [ ] Ensure Python dependencies are up-to-date

---

## Deployment Steps

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependency added:**
- `APScheduler==3.10.4` - Background task scheduling

### 2. Run Database Migration

Connect to your Supabase PostgreSQL database and run the migration:

```bash
# Option 1: Via psql
psql -h <your-supabase-host> \
     -U postgres \
     -d postgres \
     -f sql_scripts/v1.3.0_inventory_enhancements_biofloc.sql

# Option 2: Via Supabase SQL Editor
# Copy and paste the contents of v1.3.0_inventory_enhancements_biofloc.sql
# into the Supabase SQL Editor and execute
```

**Migration creates:**
- `inventory_transactions.module_batch_id` column (UUID)
- `inventory_transactions.session_number` column (INTEGER)
- `inventory_reservations` table
- `item_module_mapping` table
- `inventory_available_stock` view
- `expire_old_reservations()` function

### 3. Verify Migration

Run these queries to verify:

```sql
-- Check new columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'inventory_transactions'
  AND column_name IN ('module_batch_id', 'session_number');

-- Check new tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('inventory_reservations', 'item_module_mapping');

-- Check view exists
SELECT table_name
FROM information_schema.views
WHERE table_name = 'inventory_available_stock';
```

### 4. Start FastAPI Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Background Scheduler

Check the health endpoint to confirm scheduler is running:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "database": "operational",
    "scheduler": "running"
  },
  "scheduled_jobs": [
    {
      "id": "expire_reservations",
      "name": "Expire old inventory reservations",
      "next_run": "2025-11-18T12:15:00"
    }
  ],
  "version": "1.0.0",
  "environment": "development"
}
```

---

## API Endpoints Reference

### 1. Batch Deduction

**Endpoint:** `POST /api/v1/inventory/stock/use-batch`

**Use Case:** Deduct multiple items in a single atomic transaction (e.g., feeding session)

**Request:**
```json
{
  "deductions": [
    {
      "sku": "FEED-3MM",
      "quantity": 10.5,
      "notes": "Morning feed"
    },
    {
      "item_id": 123,
      "quantity": 0.5,
      "notes": "Vitamins"
    }
  ],
  "module_reference": "biofloc",
  "tank_id": "550e8400-e29b-41d4-a716-446655440000",
  "batch_id": "660e8400-e29b-41d4-a716-446655440001",
  "session_number": 1,
  "global_notes": "Daily feeding session 1"
}
```

**Response:**
```json
{
  "success": true,
  "total": 2,
  "successful": 2,
  "failed": 0,
  "total_cost": 55.25,
  "results": [
    {
      "item_name": "Feed 3mm 32% Protein",
      "sku": "FEED-3MM",
      "quantity": 10.5,
      "cost": 52.50,
      "success": true
    },
    {
      "item_name": "Vitamin Mix",
      "sku": "VIT-MIX",
      "quantity": 0.5,
      "cost": 2.75,
      "success": true
    }
  ],
  "transaction_ids": [1001, 1002]
}
```

**Key Features:**
- ✅ Atomic: All items succeed or all fail (rollback)
- ✅ Supports both `item_id` and `sku`
- ✅ FIFO deduction for each item
- ✅ Tracks biofloc `batch_id` and `session_number`
- ✅ Max 50 items per batch

### 2. Bulk Fetch

**Endpoint:** `POST /api/v1/inventory/items/bulk-fetch`

**Use Case:** Fetch multiple items at once (e.g., morning stock check)

**Request:**
```json
{
  "skus": ["FEED-3MM", "FEED-2MM", "VIT-MIX", "PROBIOTIC"],
  "include_stock": true,
  "include_reserved": true,
  "include_batches": false
}
```

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "sku": "FEED-3MM",
      "name": "Feed 3mm 32% Protein",
      "current_qty": 500.5,
      "unit": "kg",
      "category": "Feed",
      "reorder_threshold": 100,
      "last_purchase_price": 5.25,
      "reserved_qty": 50.0,
      "available_qty": 450.5
    }
  ],
  "total": 4,
  "requested": 4,
  "found": 4,
  "not_found": []
}
```

**Key Features:**
- ✅ Fetch by `item_ids` or `skus`
- ✅ Show reserved quantities
- ✅ Include batch details optionally
- ✅ Max 100 items per request

### 3. Stock Reservation

**Endpoint:** `POST /api/v1/inventory/stock/reserve`

**Use Case:** Reserve stock for planned operations

**Request:**
```json
{
  "item_id": 123,
  "quantity": 50,
  "module_reference": "biofloc",
  "reference_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_hours": 24,
  "notes": "Tomorrow's feeding session"
}
```

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "item_id": 123,
  "item_name": "Feed 3mm 32% Protein",
  "sku": "FEED-3MM",
  "quantity": 50,
  "module_reference": "biofloc",
  "reference_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "reserved_until": "2025-11-19T12:00:00Z",
  "notes": "Tomorrow's feeding session",
  "created_by": "user-uuid",
  "created_by_name": "John Doe",
  "created_at": "2025-11-18T12:00:00Z"
}
```

### 4. List Reservations

**Endpoint:** `GET /api/v1/inventory/stock/reservations?module_reference=biofloc&status=pending`

### 5. Cancel Reservation

**Endpoint:** `DELETE /api/v1/inventory/stock/reserve/{reservation_id}`

### 6. Confirm Reservation

**Endpoint:** `POST /api/v1/inventory/stock/confirm-reservation/{reservation_id}`

**Effect:** Converts reservation to actual stock usage (FIFO deduction)

---

## Testing Guide

### 1. Test Batch Deduction

```bash
# Create test items first (via existing endpoints)
# Then test batch deduction:

curl -X POST http://localhost:8000/api/v1/inventory/stock/use-batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "deductions": [
      {"sku": "FEED-3MM", "quantity": 10.5},
      {"sku": "VIT-MIX", "quantity": 0.5}
    ],
    "module_reference": "biofloc",
    "session_number": 1,
    "global_notes": "Test batch deduction"
  }'
```

### 2. Test Bulk Fetch

```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/bulk-fetch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "skus": ["FEED-3MM", "FEED-2MM", "VIT-MIX"],
    "include_reserved": true
  }'
```

### 3. Test Reservation System

```bash
# Create reservation
RESERVATION_ID=$(curl -X POST http://localhost:8000/api/v1/inventory/stock/reserve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "item_id": 123,
    "quantity": 50,
    "module_reference": "biofloc",
    "duration_hours": 24
  }' | jq -r '.id')

# List reservations
curl http://localhost:8000/api/v1/inventory/stock/reservations \
  -H "Authorization: Bearer YOUR_TOKEN"

# Confirm reservation
curl -X POST http://localhost:8000/api/v1/inventory/stock/confirm-reservation/$RESERVATION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Test Auto-Expiry

Wait 15 minutes after creating a reservation, then check logs:

```bash
# Check FastAPI logs for:
# "Expiring N old reservations..."
# "✅ Successfully expired N reservations"
```

---

## Performance Benchmarks

**Expected performance improvements:**

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Feeding session (5 items) | 5 API calls | 1 API call | **80% reduction** |
| Morning stock check (15 items) | 15 API calls | 1 API call | **93% reduction** |
| Stock reservation | N/A | New feature | **Eliminates race conditions** |

---

## Troubleshooting

### Issue: Scheduler not starting

**Check:**
```bash
# Verify APScheduler is installed
pip show APScheduler

# Check FastAPI logs for scheduler errors
# Should see: "✅ Background scheduler started successfully"
```

### Issue: Batch deduction fails

**Common causes:**
- Insufficient stock for one or more items
- Invalid SKU or item_id
- More than 50 items in batch

**Check response for detailed error:**
```json
{
  "detail": "Batch deduction failed. 1 items failed, 2 would have succeeded. All rolled back."
}
```

### Issue: Reservation creation fails

**Common causes:**
- Insufficient available stock (current_qty - reserved_qty)
- Invalid item_id
- Duration > 30 days

---

## Rollback Procedure

If issues arise, rollback:

```sql
-- Drop new tables
DROP TABLE IF EXISTS inventory_reservations CASCADE;
DROP TABLE IF EXISTS item_module_mapping CASCADE;

-- Drop new columns
ALTER TABLE inventory_transactions DROP COLUMN IF EXISTS module_batch_id;
ALTER TABLE inventory_transactions DROP COLUMN IF EXISTS session_number;

-- Drop view and function
DROP VIEW IF EXISTS inventory_available_stock;
DROP FUNCTION IF EXISTS expire_old_reservations();
```

Then restart FastAPI server with previous code version.

---

## Next Steps (Future Phases)

**Phase 3: Module Integration (Future)**
- Module-specific view endpoints
- Item-module mapping management
- Consumption reports by module

**Phase 4: Frontend (Future)**
- Batch operation UI
- Reservation dashboard
- Module filter toggle

---

## Support

For issues or questions:
1. Check FastAPI logs: `/var/log/fastapi.log` or console output
2. Check database logs in Supabase dashboard
3. Verify health endpoint: `GET /health`
4. Review transaction history: `GET /api/v1/inventory/transactions`

---

## Summary

✅ **Completed:**
- Batch deduction (atomic transactions)
- Bulk fetch (efficient retrieval)
- Stock reservation system
- Auto-expiry background task
- Database migrations
- API documentation

🎯 **Benefits:**
- 70-93% reduction in API calls for common operations
- Atomic transactions prevent partial failures
- Stock reservations eliminate race conditions
- Better cross-module integration for biofloc

📊 **Performance:**
- All new endpoints target <200ms response time
- Background scheduler runs every 15 minutes
- Database indices optimize reservation queries
