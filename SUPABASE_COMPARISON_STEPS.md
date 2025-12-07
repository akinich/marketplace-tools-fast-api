# How to Compare Databases Using Supabase SQL Editor

## Quick & Easy Method (5 minutes)

### Step 1: Open Both Databases in Supabase

1. Open **marketplace-tools-fast-api** database in Supabase Dashboard
2. Open **marketplace-tools-fast-api** database in another browser tab
3. Go to **SQL Editor** in both tabs

### Step 2: Run the Quick Comparison Script

1. Open the file: `quick_db_compare.sql` in your code editor
2. Copy ALL the SQL code
3. In **Database 1** (farm2-app) SQL Editor:
   - Paste the code
   - Click "Run"
   - **Save the results** (copy to notepad or take screenshot)

4. In **Database 2** (marketplace-tools) SQL Editor:
   - Paste the SAME code
   - Click "Run"
   - **Save the results** (copy to notepad or take screenshot)

### Step 3: Compare the Results

Compare these key sections side-by-side:

#### Section 1: DATABASE SUMMARY
```
Should show:
- total_tables: 26
- primary_keys: 26
- foreign_keys: ~12-15
- total_indexes: ~25-30
- total_triggers: ~6-10
```

**✅ PASS if numbers are identical**
**❌ FAIL if numbers differ**

---

#### Section 2: ROW COUNTS
Compare the row count for each table.

**Example:**
```
farm2-app database:
user_profiles: 5 rows
roles: 3 rows
modules: 8 rows

marketplace-tools database:
user_profiles: 5 rows  ✅ Match
roles: 3 rows          ✅ Match
modules: 8 rows        ✅ Match
```

**✅ PASS if ALL row counts match**
**⚠️ WARNING if some tables have different counts**

---

#### Section 3: DATA INTEGRITY HASHES
Compare the MD5 hash values for critical tables.

**Example:**
```
farm2-app database:
HASH: user_profiles - a1b2c3d4e5f6...

marketplace-tools database:
HASH: user_profiles - a1b2c3d4e5f6...  ✅ Match
```

**✅ PASS if ALL hashes match**
**❌ FAIL if hashes differ** (means data is different)

---

## Full Comparison Method (More Detailed)

If you want a complete schema comparison, use `compare_databases.sql` instead:

1. Open `compare_databases.sql`
2. Copy ALL the code
3. Run on both databases
4. Compare outputs section by section

This gives you:
- Complete table schemas (all columns, types, defaults)
- All constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK)
- All indexes and their definitions
- All triggers
- All functions
- Data hashes for verification

---

## Expected Results

### ✅ Perfect Match (Databases are Identical)

```
DATABASE SUMMARY:
✅ Same total_tables (26)
✅ Same constraints count
✅ Same indexes count
✅ Same triggers count

ROW COUNTS:
✅ All 26 tables have matching row counts

DATA HASHES:
✅ All MD5 hashes match
```

**Conclusion: Databases are identical! ✅**

---

### ⚠️ Acceptable Differences

These differences are OK:
- Different secrets in `system_settings`:
  - `supabase_url` (different project URLs)
  - `supabase_service_key` (different API keys)
  - `telegram_bot_token` (different bot tokens)

---

### ❌ Problems Found

If you see these issues, they need attention:

**Missing Tables:**
```
farm2-app: 26 tables
marketplace-tools: 24 tables  ❌

Action: Run missing migrations in marketplace-tools database
```

**Row Count Mismatches:**
```
user_profiles:
  farm2-app: 10 rows
  marketplace-tools: 8 rows  ❌

Action: Verify data was copied correctly
```

**Different Hashes:**
```
HASH: roles
  farm2-app: abc123...
  marketplace-tools: xyz789...  ❌

Action: Data is different, review and sync
```

---

## SQL Files Available

1. **`quick_db_compare.sql`** ⭐ RECOMMENDED
   - Fast and easy
   - Shows most important comparisons
   - Perfect for Supabase SQL Editor
   - Takes ~5 seconds to run

2. **`compare_databases.sql`**
   - Complete detailed comparison
   - Shows everything (schemas, constraints, indexes, etc.)
   - Takes ~30 seconds to run
   - Use if you need full analysis

3. **`verify_schema_comprehensive.sql`**
   - Validates specific migrations (008-011)
   - Checks for expected tables and constraints
   - Good for verifying migrations ran correctly

---

## Troubleshooting

### "Table doesn't exist" Error
If you get errors like `relation "webhooks" does not exist`:
- Some tables are missing
- Check which migrations haven't been run
- Run migrations from `backend/migrations/` folder in order

### "Permission denied" Error
- Make sure you're using the Service Role key or have proper permissions
- In Supabase: Go to SQL Editor and use default connection

### Different Row Counts
Possible reasons:
1. Data wasn't copied completely
2. Application has been running and creating new data
3. Some records were deleted
4. Background jobs created/modified data

### Different Hashes but Same Row Counts
- Data exists but values are different
- Check if data was modified after cloning
- Verify timestamps, IDs, or other fields

---

## Quick Checklist

Copy this into your notes:

```
DATABASE COMPARISON CHECKLIST:

Farm2-app Database:
□ Opened in Supabase
□ Ran quick_db_compare.sql
□ Copied results

Marketplace-tools Database:
□ Opened in Supabase
□ Ran quick_db_compare.sql
□ Copied results

Comparison:
□ Total tables match (26)
□ Row counts match for all tables
□ Data hashes match
□ Constraint counts match
□ No errors during script execution

Result:
□ ✅ Databases are identical
□ ⚠️ Minor differences found (secrets only)
□ ❌ Major differences found (needs investigation)
```

---

## Next Steps After Verification

Once databases are confirmed identical:

1. ✅ Update `.env` files with correct database URLs
2. ✅ Configure secrets in `system_settings` table
3. ✅ Deploy to Render
4. ✅ Test the application
5. ✅ Set up monitoring

---

**Need Help?**

If you find differences and need to fix them:
1. Document what's different
2. Check migration history: `backend/migrations/`
3. Run missing migrations if needed
4. Re-run comparison to verify fix

---

Last Updated: 2025-11-28
