# How to Run the Batch Tracking Migration

You have 2 options to run the clean migration:

## Option 1: Using psql (Recommended - Fastest)

```bash
# Replace these with your actual database credentials:
# - DBNAME: your database name
# - DBUSER: your database user
# - DBHOST: your database host (e.g., localhost or Supabase URL)
# - DBPORT: your database port (default: 5432)

cd /home/user/marketplace-tools-fast-api/backend

psql -h DBHOST -p DBPORT -U DBUSER -d DBNAME -f migrations/014_batch_tracking_clean.sql
```

**Example for Supabase:**
```bash
psql -h db.xxxxx.supabase.co -p 5432 -U postgres -d postgres -f migrations/014_batch_tracking_clean.sql
```

**Example for local PostgreSQL:**
```bash
psql -h localhost -p 5432 -U your_user -d your_database -f migrations/014_batch_tracking_clean.sql
```

## Option 2: Using Python migration script

First install dependencies:
```bash
cd /home/user/marketplace-tools-fast-api/backend
pip install -r requirements.txt
```

Then run migration:
```bash
python run_migration.py migrations/014_batch_tracking_clean.sql
```

---

## What This Migration Does

✅ **Drops** all existing batch tracking tables and indexes
✅ **Creates** 4 tables fresh with FY support:
   - `batches` - Master batch records
   - `batch_history` - Complete audit trail
   - `batch_documents` - Document links
   - `batch_sequence` - FY-based sequence generator

✅ **Initializes** batch_sequence with:
   - Prefix: B
   - Financial Year: 2526 (Apr 2025 - Mar 2026)
   - Starting Number: 0
   - Next batch: B/2526/0001

✅ **Verifies** installation with test queries

---

## Expected Success Output

You should see:
```
NOTICE:  ✅ Batch Tracking module installed successfully!
NOTICE:     - 4 tables created: batches, batch_history, batch_documents, batch_sequence
NOTICE:     - 13 indexes created
NOTICE:     - FY configured: 2526 (Apr 2025 - Mar 2026)
NOTICE:     - Next batch number: B/2526/0001
NOTICE:
NOTICE:  🚀 Ready to test! Start FastAPI server and navigate to /docs
```

Plus verification query results showing the tables and initial sequence.

---

## After Successful Migration

1. **Start FastAPI server:**
   ```bash
   cd /home/user/marketplace-tools-fast-api/backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open Swagger UI:**
   Navigate to: http://localhost:8000/docs

3. **Follow Testing Guide:**
   Refer to `BATCH_TRACKING_TESTING_GUIDE.md` for complete testing instructions

---

**Need help?** Let me know if you encounter any errors!
