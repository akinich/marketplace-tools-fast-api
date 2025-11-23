# API Key Management - Testing Guide

**Version:** 1.0.0
**Date:** 2025-11-22
**Feature:** API Key Authentication System

---

## Overview

This guide provides comprehensive testing steps for the API Key Management system after deployment. Follow these steps sequentially to ensure all features work correctly.

---

## Prerequisites

Before starting the tests, ensure:

1. ✅ Database migration `011_api_keys.sql` has been run in Supabase
2. ✅ Backend is deployed and running
3. ✅ Frontend is deployed and accessible
4. ✅ You have admin access to the application
5. ✅ You have `curl` or Postman for API testing

---

## Part 1: Database Verification

### Step 1.1: Verify Tables Exist

Run in Supabase SQL Editor:

```sql
-- Check if tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('api_keys', 'api_key_usage')
ORDER BY table_name;
```

**Expected Result:**
```
table_name
-----------
api_key_usage
api_keys
```

### Step 1.2: Verify Indexes

```sql
-- Check indexes
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('api_keys', 'api_key_usage')
ORDER BY tablename, indexname;
```

**Expected Result:** Should show 5 indexes total:
- `idx_api_keys_user_id`
- `idx_api_keys_key_hash`
- `idx_api_keys_is_active`
- `idx_api_key_usage_key_id`
- `idx_api_key_usage_created_at`

### Step 1.3: Verify Foreign Keys

```sql
-- Check foreign key constraints
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('api_keys', 'api_key_usage');
```

**Expected Result:** Should show foreign keys linking to `auth.users` and `api_keys`.

---

## Part 2: Backend API Testing

### Step 2.1: Test Available Scopes Endpoint

**Request:**
```bash
curl -X GET "https://your-api.com/api/v1/api-keys/scopes/available" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "scopes": [
    "inventory:read",
    "inventory:write",
    "inventory:delete",
    "inventory:*",
    "tickets:read",
    ...
    "*:*"
  ]
}
```

**✅ Pass Criteria:**
- Status code: 200
- Response contains array of scopes
- At least 50+ scopes listed

### Step 2.2: Test Create API Key

**Request:**
```bash
curl -X POST "https://your-api.com/api/v1/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Key",
    "description": "Testing API key creation",
    "scopes": ["inventory:read", "dashboard:read"],
    "expires_in_days": 30
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "key_prefix": "sk_live_abc...",
  "name": "Test API Key",
  "description": "Testing API key creation",
  "scopes": ["inventory:read", "dashboard:read"],
  "is_active": true,
  "expires_at": "2025-12-22T...",
  "last_used_at": null,
  "created_at": "2025-11-22T...",
  "api_key": "sk_live_FULL_KEY_HERE"
}
```

**✅ Pass Criteria:**
- Status code: 201
- Response includes full `api_key` field (starts with `sk_live_`)
- Key is at least 40 characters long
- `key_prefix` matches first 12 chars of `api_key`
- `expires_at` is 30 days from now

**⚠️ IMPORTANT:** Save the `api_key` value - you'll need it for subsequent tests!

### Step 2.3: Test List API Keys

**Request:**
```bash
curl -X GET "https://your-api.com/api/v1/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "user_id": "user-uuid",
    "key_prefix": "sk_live_abc...",
    "name": "Test API Key",
    "description": "Testing API key creation",
    "scopes": ["inventory:read", "dashboard:read"],
    "is_active": true,
    "expires_at": "2025-12-22T...",
    "last_used_at": null,
    "created_at": "2025-11-22T..."
  }
]
```

**✅ Pass Criteria:**
- Status code: 200
- Array contains the API key you just created
- **DOES NOT** include full `api_key` field (security)

### Step 2.4: Test API Key Authentication

**Request (using API key instead of JWT):**
```bash
curl -X GET "https://your-api.com/api/v1/dashboard/summary" \
  -H "X-API-Key: sk_live_YOUR_FULL_KEY_FROM_STEP_2.2"
```

**Expected Response:**
- Status code: 200
- Normal dashboard data returned

**✅ Pass Criteria:**
- Can access protected endpoints with API key
- Same data as when using JWT token

### Step 2.5: Test Scope Restrictions

**Request (try to access endpoint without permission):**
```bash
# Your key only has "inventory:read", try to create inventory item
curl -X POST "https://your-api.com/api/v1/inventory/items" \
  -H "X-API-Key: sk_live_YOUR_FULL_KEY_FROM_STEP_2.2" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "category_id": 1
  }'
```

**Expected Response:**
```json
{
  "detail": "Missing required scope: inventory:write"
}
```

**✅ Pass Criteria:**
- Status code: 403 Forbidden
- Error message indicates missing scope

### Step 2.6: Test Usage Logging

**Request:**
```bash
curl -X GET "https://your-api.com/api/v1/api-keys/1/usage" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "endpoint": "/api/v1/dashboard/summary",
    "method": "GET",
    "status_code": 200,
    "ip_address": "123.456.789.0",
    "created_at": "2025-11-22T..."
  },
  {
    "id": 2,
    "endpoint": "/api/v1/inventory/items",
    "method": "POST",
    "status_code": 403,
    "ip_address": "123.456.789.0",
    "created_at": "2025-11-22T..."
  }
]
```

**✅ Pass Criteria:**
- Status code: 200
- Shows logs from steps 2.4 and 2.5
- Logs include endpoint, method, status code

### Step 2.7: Test API Key Revocation

**Request:**
```bash
curl -X DELETE "https://your-api.com/api/v1/api-keys/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "API key revoked successfully"
}
```

**✅ Pass Criteria:**
- Status code: 200

**Verify revocation works:**
```bash
curl -X GET "https://your-api.com/api/v1/dashboard/summary" \
  -H "X-API-Key: sk_live_YOUR_REVOKED_KEY"
```

**Expected:** Status code 401 with "Invalid or expired API key" message

---

## Part 3: Frontend UI Testing

### Step 3.1: Access API Keys Page

1. Log in to the application
2. Look for "API Keys" in the sidebar navigation (with a key icon)
3. Click "API Keys"

**✅ Pass Criteria:**
- Navigation item is visible in sidebar
- Page loads without errors
- Shows statistics cards (Total Keys, Active Keys, Revoked Keys)

### Step 3.2: Test Create API Key UI

1. Click "CREATE API KEY" button
2. Fill in the form:
   - **Name:** "Frontend Test Key"
   - **Description:** "Testing from UI"
   - **Scopes:** Select "inventory:read", "inventory:write"
   - **Expires in:** 90 days
3. Click "Create Key"

**✅ Pass Criteria:**
- Form validation works (can't submit without name/scopes)
- Success dialog appears showing the full API key
- Warning message states "This is the only time you'll see this key"
- Copy button copies key to clipboard

**⚠️ IMPORTANT:** Copy the key before closing the dialog!

### Step 3.3: Verify Key in Table

After closing the success dialog:

**✅ Pass Criteria:**
- New key appears in the table
- Shows correct name: "Frontend Test Key"
- Key prefix is displayed (e.g., "sk_live_abc...")
- Scopes show as chips (2 visible, or "+X more" if many)
- Status shows "Active" in green chip
- Expires date is ~90 days from now
- Last Used shows "Never"

### Step 3.4: Test Usage Viewer

1. Make a request using the API key (from Step 3.2):
   ```bash
   curl -X GET "https://your-api.com/api/v1/inventory/items" \
     -H "X-API-Key: YOUR_KEY_FROM_STEP_3.2"
   ```

2. Click the "eye" icon (👁️) in the Actions column
3. Usage dialog should open

**✅ Pass Criteria:**
- Dialog shows usage table
- Contains at least 1 entry from the curl request
- Shows endpoint, method, status code, IP, timestamp
- Status code is color-coded (green for 2xx, red for 4xx/5xx)

### Step 3.5: Test Key Revocation

1. Click the "delete" icon (🗑️) in the Actions column
2. Confirm the revocation

**✅ Pass Criteria:**
- Confirmation dialog appears
- After confirming, key status changes to "Revoked" (red chip)
- Delete button disappears for revoked key
- Key opacity reduces (appears faded)

**Verify revocation:**
```bash
curl -X GET "https://your-api.com/api/v1/inventory/items" \
  -H "X-API-Key: YOUR_REVOKED_KEY"
```

**Expected:** 401 error

### Step 3.6: Test Scope Selection UI

1. Click "CREATE API KEY" again
2. Open the Scopes dropdown

**✅ Pass Criteria:**
- Scopes are grouped by resource (INVENTORY, TICKETS, USERS, etc.)
- Can select multiple scopes
- Selected scopes show as chips in the dropdown
- Can unselect scopes by clicking again

---

## Part 4: Security Testing

### Step 4.1: Test Invalid API Key

```bash
curl -X GET "https://your-api.com/api/v1/dashboard/summary" \
  -H "X-API-Key: sk_live_invalid_key_12345"
```

**✅ Pass Criteria:**
- Status code: 401
- Error: "Invalid or expired API key"

### Step 4.2: Test Missing API Key

```bash
curl -X GET "https://your-api.com/api/v1/dashboard/summary"
```

**✅ Pass Criteria:**
- Status code: 401
- Error: "Authentication required" or similar

### Step 4.3: Test Expired Key (if applicable)

If you created a key with short expiration:

1. Wait for expiration
2. Try to use the key

**✅ Pass Criteria:**
- Status code: 401
- Key is rejected after expiration

### Step 4.4: Test Key Hash Security

In Supabase, check the stored key:

```sql
SELECT key_hash, key_prefix FROM api_keys LIMIT 1;
```

**✅ Pass Criteria:**
- `key_hash` does NOT contain the readable key
- `key_hash` looks like bcrypt hash (starts with `$2b$`)
- `key_prefix` only shows first 12 chars

---

## Part 5: Admin Testing (if applicable)

### Step 5.1: Admin List All Keys

```bash
curl -X GET "https://your-api.com/api/v1/api-keys/admin/all" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**✅ Pass Criteria:**
- Status code: 200
- Shows keys from all users
- Non-admin users get 403

### Step 5.2: Admin Revoke Any Key

```bash
curl -X DELETE "https://your-api.com/api/v1/api-keys/admin/1" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**✅ Pass Criteria:**
- Admin can revoke any user's key
- Non-admin users get 403

---

## Part 6: Edge Cases & Error Handling

### Step 6.1: Invalid Scopes

```bash
curl -X POST "https://your-api.com/api/v1/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Scope Test",
    "scopes": ["invalid:scope", "nonexistent:permission"]
  }'
```

**✅ Pass Criteria:**
- Status code: 400
- Error: "Invalid scopes: invalid:scope, nonexistent:permission"

### Step 6.2: Empty Name

```bash
curl -X POST "https://your-api.com/api/v1/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "scopes": ["inventory:read"]
  }'
```

**✅ Pass Criteria:**
- Status code: 422
- Validation error for name field

### Step 6.3: View Usage of Non-existent Key

```bash
curl -X GET "https://your-api.com/api/v1/api-keys/99999/usage" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**✅ Pass Criteria:**
- Status code: 404
- Error: "API key not found"

---

## Test Results Summary

Use this checklist to track your progress:

### Database
- [ ] Tables created successfully
- [ ] Indexes exist
- [ ] Foreign keys configured

### Backend API
- [ ] Can fetch available scopes
- [ ] Can create API key
- [ ] Can list user's keys
- [ ] Can authenticate with API key
- [ ] Scope restrictions work
- [ ] Usage logging works
- [ ] Can revoke keys
- [ ] Revoked keys don't work

### Frontend UI
- [ ] API Keys page accessible
- [ ] Create key dialog works
- [ ] Key displayed once with warning
- [ ] Keys listed in table
- [ ] Usage viewer works
- [ ] Revoke button works
- [ ] Scope selection grouped properly

### Security
- [ ] Invalid keys rejected
- [ ] Missing keys rejected
- [ ] Expired keys rejected (if applicable)
- [ ] Keys stored as bcrypt hash
- [ ] Full keys never shown after creation

### Admin (if applicable)
- [ ] Admin can list all keys
- [ ] Admin can revoke any key
- [ ] Non-admins blocked from admin endpoints

### Error Handling
- [ ] Invalid scopes rejected
- [ ] Empty name rejected
- [ ] Non-existent key access returns 404

---

## Common Issues & Troubleshooting

### Issue: "Module 'bcrypt' not found"

**Solution:**
```bash
cd backend
pip install bcrypt
# or
poetry add bcrypt
```

### Issue: API key authentication not working

**Check:**
1. Is `X-API-Key` header spelled correctly? (case-sensitive)
2. Did you copy the full key including `sk_live_` prefix?
3. Check backend logs for specific error

### Issue: Scope restrictions not working

**Check:**
1. Verify the endpoint you're accessing has scope protection
2. Check if the scope name matches exactly (case-sensitive)
3. Try using a key with `*:*` scope to test

### Issue: Frontend page shows errors

**Check:**
1. Browser console for JavaScript errors
2. Network tab for API call failures
3. Ensure backend is running and accessible

---

## Report Your Results

After completing all tests, please report back with:

1. **Total tests passed:** X/Y
2. **Any failures:** Describe which tests failed and error messages
3. **Browser used:** (for frontend tests)
4. **Environment:** (development/staging/production)

Example response:
```
✅ All tests passed (45/45)
✅ Database migration successful
✅ Backend API working perfectly
✅ Frontend UI fully functional
✅ Security measures verified
Browser: Chrome 120
Environment: Production
```

Or if issues:
```
⚠️ Tests passed: 42/45
❌ Failed tests:
  - Step 2.5: Scope restrictions (500 error instead of 403)
  - Step 3.4: Usage viewer (dialog not opening)
  - Step 6.1: Invalid scopes (accepted instead of rejected)

Browser: Firefox 121
Environment: Staging

Error messages:
[Paste relevant error messages here]
```

---

## Next Steps After Successful Testing

Once all tests pass:

1. ✅ System is ready for production use
2. 📖 Create user documentation (optional)
3. 🎓 Train users on API key management
4. 📊 Monitor usage logs regularly
5. 🔒 Review security policies

---

**Testing Guide Version:** 1.0.0
**Last Updated:** 2025-11-22
**Maintainer:** Development Team
