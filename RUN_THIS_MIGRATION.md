# 🚨 URGENT: Fix Missing Users Table

## Problem
Your backend is throwing `relation "users" does not exist` error because the database migrations haven't been run after the recent CI/CD infrastructure changes.

## Quick Fix

### Option 1: Run via Your Hosting Platform Shell (Render/Heroku/etc)

1. **Access your server shell** (e.g., Render Dashboard → Shell tab)

2. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

3. **Run the base schema migration:**
   ```bash
   python run_base_schema.py
   ```

4. **Restart your backend service**

### Option 2: Run SQL Directly via Database Console

If you have access to your PostgreSQL database console (Supabase SQL Editor, pgAdmin, etc.):

1. **Open your database console**

2. **Run this file:** `backend/migrations/000_base_schema.sql`

   You can copy the entire contents of the file and paste it into your SQL editor, then execute.

3. **Restart your backend service**

### Option 3: Run All Migrations (Most Complete)

If you want to ensure ALL migrations are run:

```bash
cd backend
python run_all_migrations.py
```

This will:
- Create the base schema (users, roles, user_profiles, etc.)
- Apply all module migrations (biofloc, tickets, development, etc.)
- Show a summary of all tables created

## Verification

After running the migration, check:

1. **Backend logs** - should no longer show "relation users does not exist"
2. **Login should work** - you should be able to log in again
3. **Database tables** - users table should exist

## What This Creates

The base schema migration creates these essential tables:
- `users` - user accounts
- `user_profiles` - user profile data and authentication
- `roles` - user roles (Admin, User)
- `login_history` - login tracking
- `user_sessions` - session management
- `modules` - system modules
- `user_module_permissions` - permissions
- `activity_logs` - audit trail
- `webhooks` - webhook subscriptions
- `email_queue` - email queue
- And more...

## Why This Happened

After the recent test infrastructure and CI/CD changes, the database migration step wasn't executed in your deployed environment. The test changes updated the migration files but didn't apply them to your production database.

## Prevention

To prevent this in the future, consider adding migration checks to your deployment process:

1. Add to your build/start command:
   ```bash
   python backend/run_all_migrations.py && uvicorn app.main:app
   ```

2. Or add a startup check in your deployment configuration

---

**Created:** 2025-11-27
**Issue:** Users table missing after CI/CD infrastructure changes
