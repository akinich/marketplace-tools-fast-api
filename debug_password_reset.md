# Password Reset Email Debugging Guide

## Problem
Password reset emails are not being sent to users created via admin panel.

## Code Changes Verified ✅
1. ✅ `backend/app/services/admin_service.py` - Using Supabase Admin API
2. ✅ `sql_scripts/v1.3.2_fix_unconfirmed_users.sql` - SQL fix available
3. ✅ Frontend deployed with latest code

---

## Debugging Checklist

### 1. Verify SQL Script Was Run on PRODUCTION Database ⚠️

**Run this in your PRODUCTION Supabase SQL Editor:**
```sql
-- Check if users have email_confirmed_at set
SELECT
    id,
    email,
    email_confirmed_at,
    confirmed_at,
    created_at,
    CASE
        WHEN email_confirmed_at IS NULL THEN '❌ NOT CONFIRMED'
        ELSE '✅ CONFIRMED'
    END as status
FROM auth.users
ORDER BY created_at DESC
LIMIT 20;
```

**Expected Result:** All users should have `email_confirmed_at` populated.

**If NULL values exist, run the fix again:**
```sql
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;
```

---

### 2. Verify Users Were Created AFTER Deployment 🆕

**Important:** Users created BEFORE the code deployment need to be recreated OR manually updated.

**Check when users were created:**
```sql
SELECT
    au.email,
    up.full_name,
    au.created_at as user_created,
    au.email_confirmed_at
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
ORDER BY au.created_at DESC;
```

**Test with a NEW user:**
1. Delete test users created before deployment
2. Create a BRAND NEW test user via admin panel
3. Try password reset with this new user

---

### 3. Check Supabase Email Configuration 📧

Go to **Supabase Dashboard → Authentication → Email Templates**

#### Required Settings:

**A. Confirm Email Setting:**
- Navigate to: **Authentication → Settings → Email → Confirm Email**
- **Set to:** `DISABLED` (since admins create users)
- Screenshot what you see here

**B. SMTP Configuration:**
- Navigate to: **Project Settings → Auth → SMTP Settings**
- Verify SMTP is enabled and configured
- Supabase's default email service should work
- Check if "Enable Custom SMTP" is needed for your region

**C. Email Templates:**
- Navigate to: **Authentication → Email Templates → Reset Password**
- Verify template exists and is enabled
- Check the template content
- Look for the magic link: `{{ .ConfirmationURL }}`

---

### 4. Verify Backend Environment Variables 🔧

**Check your PRODUCTION backend environment:**

```bash
# These must be set in your production environment:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ... (service_role key, NOT anon key)
FRONTEND_URL=https://farm2-app-frontend.onrender.com
```

**How to verify:**
1. Check your Render/deployment platform dashboard
2. Go to Environment Variables section
3. Confirm all three are set correctly
4. `SUPABASE_SERVICE_KEY` must be the **service_role** key (starts with `eyJ...`)
5. NOT the anon/public key

**Get the correct key:**
- Supabase Dashboard → Settings → API → `service_role` key (secret)

---

### 5. Test with Backend Logs 📝

**Add temporary logging to check what's happening:**

**Option A: Check existing logs**
Look for these log messages in your backend deployment logs:
```
Password reset email sent to: [email]
Password reset token generated for user: [user_id]
```

**Option B: Test directly via API**
```bash
# Test password reset API directly
curl -X POST https://your-backend-url/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check backend logs immediately after this request.

---

### 6. Verify Supabase Rate Limits 🚦

Supabase has email rate limits:
- **Free tier:** 4 emails/hour per user
- **Pro tier:** Higher limits

**Check:**
1. Are you testing with the same email repeatedly?
2. Wait 1 hour and try again
3. Or try with a different email address

---

### 7. Check Supabase Auth Logs 🔍

**Supabase Dashboard → Authentication → Logs**

Look for:
- `user.recovery.send` events
- Any error messages
- Rate limit warnings

---

### 8. Test Email Delivery Path 📬

**Create a completely new test user:**

```sql
-- Option 1: Via Admin Panel (after deployment)
-- Go to Admin Panel → Add User
-- Email: newtestuser@gmail.com
-- Full Name: Test User
-- Role: User

-- Option 2: Via Supabase Dashboard (for comparison)
-- Supabase Dashboard → Authentication → Users → Add User
-- Create with same email
-- Then try password reset with this user
```

**Compare:** Does the user created via Supabase dashboard receive reset emails?

---

### 9. Inspect a Specific User in Database 🔬

**Run this for a test user:**
```sql
SELECT
    au.id,
    au.email,
    au.email_confirmed_at,
    au.confirmed_at,
    au.created_at,
    au.last_sign_in_at,
    up.full_name,
    up.is_active
FROM auth.users au
LEFT JOIN user_profiles up ON up.id = au.id
WHERE au.email = 'test@example.com';  -- Replace with actual test email
```

**Expected:**
- `email_confirmed_at`: Should have a timestamp
- `confirmed_at`: Should have a timestamp (auto-generated)
- `is_active`: Should be TRUE

---

### 10. Supabase Project Status ⚡

**Check Supabase Project Health:**
- Dashboard → Project Health
- Verify no outages or issues
- Check if project is paused (free tier inactivity)

---

## Quick Debug Script

**Run this test sequence:**

1. ✅ Check SQL results (Step 1)
2. ✅ Create NEW test user via admin panel
3. ✅ Verify user in database (Step 9)
4. ✅ Check Supabase email templates (Step 3)
5. ✅ Check environment variables (Step 4)
6. ✅ Try password reset with new user
7. ✅ Check backend logs (Step 5)
8. ✅ Check Supabase Auth logs (Step 7)

---

## Expected Behavior After Fix

**For NEW users created after deployment:**
1. User created via Admin API → `email_confirmed_at` automatically set
2. Password reset requested → Supabase sends email
3. User receives email with reset link
4. User clicks link → redirected to frontend reset page
5. User enters new password → account updated

**For OLD users (created before deployment):**
- Need SQL migration run on production database
- OR recreate the users

---

## Common Issues and Solutions

### Issue 1: "No email received"
**Solution:** Check spam folder, verify SMTP settings, check rate limits

### Issue 2: "Email confirmed_at is NULL"
**Solution:** Run SQL update script on PRODUCTION database

### Issue 3: "Backend logs show success but no email"
**Solution:** Check Supabase Auth logs, verify SMTP configuration

### Issue 4: "Different behavior for admin vs regular users"
**Solution:** Check how admin user was created (probably via Supabase dashboard)

---

## Next Steps

After running through this checklist, report back:
1. Which step failed or showed unexpected results?
2. What does the SQL query in Step 1 show?
3. What do the backend logs show when testing?
4. Any errors in Supabase Auth logs?

This will help narrow down the exact issue!
