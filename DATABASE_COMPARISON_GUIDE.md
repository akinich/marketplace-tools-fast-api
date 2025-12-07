# Database and Repository Comparison Guide

This guide helps you verify that the `marketplace-tools-fast-api` repository and database are exact copies of the `marketplace-tools-fast-api` repository and database.

## Repository Comparison Results

### Code Comparison Summary
✅ **Repositories are nearly identical!**

**Differences found:**
- Only 1 file differs: `frontend/.env.production`
  - **marketplace-tools-fast-api**: Uses `farm2-fastapi-backend.onrender.com`
  - **marketplace-tools-fast-api**: Uses `marketplace-erp.onrender.com`

This difference is **expected and correct** as both repositories deploy to different URLs.

**Commit history:**
- marketplace-tools-fast-api has one extra commit: `0b83ffe Update .env.production`
- Otherwise, both repositories share the same commit history
- All other files are **identical**

## Database Comparison

### Option 1: Automated Python Script (Recommended)

The Python script compares both databases automatically and generates a detailed report.

#### Prerequisites
```bash
pip install psycopg2-binary
```

#### Usage
```bash
python compare_databases.py
```

The script will:
1. Prompt for both database connection strings
2. Compare table structures, constraints, indexes, and triggers
3. Compare row counts for all tables
4. Generate a detailed comparison report

#### Example
```bash
$ python compare_databases.py

Database 1 URL (marketplace-tools-fast-api): postgresql://user:pass@db.xxx.supabase.co:5432/postgres
Database 2 URL (marketplace-tools-fast-api): postgresql://user:pass@db.yyy.supabase.co:5432/postgres
```

### Option 2: Manual SQL Script

Run the SQL script on both databases and compare outputs manually.

#### Usage with psql
```bash
# Run on farm2-app database
psql "postgresql://user:pass@db.xxx.supabase.co:5432/postgres" -f compare_databases.sql > farm2_output.txt

# Run on marketplace-tools database
psql "postgresql://user:pass@db.yyy.supabase.co:5432/postgres" -f compare_databases.sql > marketplace_output.txt

# Compare outputs
diff farm2_output.txt marketplace_output.txt
```

#### Usage with Supabase SQL Editor
1. Open Supabase SQL Editor for farm2-app database
2. Copy and paste content from `compare_databases.sql`
3. Run the script and save results
4. Repeat for marketplace-tools database
5. Compare the outputs manually

## What Gets Compared

### Repository Comparison
- ✅ All source code files
- ✅ Configuration files
- ✅ Frontend code
- ✅ Backend code
- ✅ SQL scripts
- ✅ Commit history

### Database Comparison
The comparison scripts check:

1. **Schema Structure**
   - All tables
   - All columns (names, types, defaults, nullable)
   - Table sizes

2. **Constraints**
   - Primary keys
   - Foreign keys
   - Unique constraints
   - Check constraints

3. **Indexes**
   - All indexes and their definitions

4. **Triggers**
   - All triggers and their definitions

5. **Functions**
   - All database functions

6. **Data**
   - Row counts for each table
   - Data hashes for critical tables (excluding secrets)

7. **Other Objects**
   - Sequences
   - Views
   - Enums/Custom types

## Expected Tables

Both databases should have these tables:

### Core Application Tables (16)
1. `activity_logs`
2. `biofloc_feed_logs`
3. `biofloc_growth_records`
4. `biofloc_tanks`
5. `biofloc_water_tests`
6. `inventory_batches`
7. `inventory_categories`
8. `inventory_transactions`
9. `item_master`
10. `modules`
11. `purchase_order_items`
12. `purchase_orders`
13. `roles`
14. `suppliers`
15. `user_module_permissions`
16. `user_profiles`

### Extended Feature Tables (10)
17. `api_keys`
18. `api_key_usage`
19. `email_queue`
20. `email_recipients`
21. `email_send_log`
22. `email_templates`
23. `settings_audit_log`
24. `system_settings`
25. `webhook_deliveries`
26. `webhooks`

**Total: 26 tables**

## Interpretation of Results

### ✅ Perfect Match
If both databases are identical, you should see:
- Same number of tables (26)
- Same table structures
- Same row counts for all tables
- Same constraints, indexes, and triggers
- Matching data hashes

### ⚠️ Acceptable Differences
These differences are OK and expected:
- Different values for `supabase_url`, `supabase_service_key` in `system_settings`
- Different values for `telegram_bot_token` in `system_settings`
- Different deployment URLs in environment variables

### ❌ Concerning Differences
Contact support or investigate if you see:
- Missing tables
- Different table structures
- Different row counts (especially in core tables)
- Missing constraints or indexes
- Different data hashes for non-secret data

## Quick Verification Checklist

- [ ] Clone both repositories locally
- [ ] Compare file structures (should be identical except `.env.production`)
- [ ] Verify commit history overlap
- [ ] Run database comparison script
- [ ] Check all 26 tables exist in both databases
- [ ] Verify row counts match
- [ ] Verify constraints and indexes match
- [ ] Check data hashes for critical tables

## Troubleshooting

### Connection Issues
If you can't connect to the database:
1. Verify the DATABASE_URL is correct
2. Check if your IP is whitelisted in Supabase
3. Ensure the database is accessible from your location

### Missing Tables
If tables are missing:
1. Check if migrations have been run: `backend/migrations/`
2. Run missing migrations in order
3. Verify schema version

### Row Count Mismatches
If row counts don't match:
1. Check if data was copied correctly
2. Verify no data was added/removed after cloning
3. Check application logs for any automated data changes

## Files Generated

- `compare_databases.sql` - SQL script for manual comparison
- `compare_databases.py` - Python script for automated comparison
- `DATABASE_COMPARISON_GUIDE.md` - This guide

## Next Steps

After verifying both repository and database are identical:

1. ✅ Update environment variables for the new deployment
2. ✅ Configure CI/CD for the new repository (if needed)
3. ✅ Test the cloned application thoroughly
4. ✅ Update documentation with new URLs
5. ✅ Set up monitoring for the new deployment

## Support

If you find significant differences or need help:
1. Document the differences found
2. Check migration files for any missing updates
3. Review recent commits in both repositories
4. Verify database backup/restore process

---

**Last Updated:** 2025-11-28
**Version:** 1.0.0
