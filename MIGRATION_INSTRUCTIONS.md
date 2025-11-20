# Development Module Migration Instructions

## Problem
The Development Planning module is throwing a "Failed to fetch features" error because the required database tables (`features`, `feature_steps`, `feature_comments`) don't exist yet. The migration hasn't been run on the production database.

## Solution
You need to run the development module migration on your Render database.

## Option 1: Run via Render Shell (Recommended)

1. Go to your Render dashboard
2. Navigate to your backend service
3. Click on "Shell" tab
4. Run the following command:
   ```bash
   cd backend
   python run_development_migration.py
   ```

This will:
- Create the `features`, `feature_steps`, and `feature_comments` tables
- Add the development module to the `modules` table
- Create necessary indexes and triggers

## Option 2: Run All Pending Migrations

To check and run ALL pending migrations (including development):

```bash
cd backend
python run_all_migrations.py
```

This will:
- Check which migrations have been applied
- Run any pending migrations
- Show a summary of all tables and modules

## Option 3: Direct SQL Execution

If you prefer to run the SQL directly through Render's PostgreSQL console or any SQL client:

1. Connect to your database using the connection string from Render
2. Execute the file: `backend/migrations/development_module_v1.0.0.sql`

## Verification

After running the migration, verify it worked by:

1. Checking the backend logs - no more errors
2. Opening the Development Planning module in the UI
3. The page should load without errors

## Prevention

To avoid this issue in the future, consider:

1. **Add migration check to startup**: Modify `backend/app/main.py` to check for required tables on startup
2. **Document deployment steps**: Add migration steps to your deployment documentation
3. **Use build commands**: Add the migration runner to your Render build command

---

**Created:** 2025-11-20
**Related Issue:** Development Planning Module - Failed to fetch features (CORS error)
