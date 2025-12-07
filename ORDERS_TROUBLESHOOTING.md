# Orders Module Troubleshooting Guide (API Sync Only)

## Overview

The Orders module has been **simplified to use API sync only** - no webhooks.

**Sync Strategy:**
- ✅ **Automatic sync**: Every 3 hours (last 3 days of orders)
- ✅ **Manual sync**: Via API endpoint (configurable 1-90 days)
- ❌ **Webhooks**: Removed (was too complex and unreliable)

This uses the **proven Order Extractor pattern** - simple, reliable API fetching with raw dict processing.

---

## Quick Verification Checklist

- [ ] Render deploy is live with latest commit
- [ ] Render logs show "Background scheduler started successfully"
- [ ] Render logs show "Sync WooCommerce Orders: Every 3 hours"
- [ ] All 4 WooCommerce settings configured in database
- [ ] Manual sync test returns success
- [ ] Orders appear in database

---

## Step 1: Check Render Deployment Status

### In Render Dashboard:
1. Go to your service
2. Check **Latest Deploy** tab
3. Verify:
   - ✅ Deploy status: **Live**
   - ✅ Commit: `723c322` (refactor: Simplify orders module...)
   - ✅ No build errors

### If deploy failed or is outdated:
```bash
# Trigger manual deploy
git push -f origin claude/add-orders-module-webhook-01246ubYfRoFmeENVhAXjNVn
```

---

## Step 2: Check Render Logs

### In Render Dashboard → Logs tab:

**Look for these on startup:**
```
✅ Background scheduler started successfully
📅 Scheduled tasks:
   - Sync WooCommerce Orders: Every 3 hours (last 3 days)
```

**If you see errors like:**
```
❌ ModuleNotFoundError: No module named 'orders_service'
❌ ImportError: cannot import name 'OrdersService'
```
→ Code not deployed properly. Redeploy.

---

## Step 3: Run Diagnostic SQL Queries

Copy and paste these into your database:

### Query 1: Check WooCommerce Settings
```sql
SELECT
    setting_key,
    CASE
        WHEN setting_key LIKE '%secret%' OR setting_key LIKE '%key%'
        THEN '***CONFIGURED***'
        ELSE setting_value::text
    END as status,
    is_encrypted
FROM system_settings
WHERE setting_key LIKE 'woocommerce.%'
ORDER BY setting_key;
```

**Expected result:** 3 rows (API sync doesn't need webhook_secret)
- `woocommerce.api_url`
- `woocommerce.consumer_key`
- `woocommerce.consumer_secret`

**If missing rows:** Continue to Step 4

---

### Query 2: Check Tables Exist
```sql
SELECT tablename
FROM pg_tables
WHERE tablename IN ('orders', 'order_items')
  AND schemaname = 'public';
```

**Expected:** 2 rows

**If 0 rows:** Migration didn't run. Re-run `026_orders_module.sql`

---

### Query 3: Check for Any Orders
```sql
SELECT
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE sync_source = 'api') as from_api,
    MAX(created_at) as latest_order,
    MAX(last_synced_at) as last_sync
FROM orders;
```

**If total_orders = 0:** No orders have been synced yet

---

## Step 4: Fix Missing WooCommerce API Credentials

### If Query 1 showed missing credentials:

#### Get WooCommerce API Credentials:
1. WooCommerce Admin → Settings → Advanced → REST API
2. Click **Add Key**
3. Description: `Marketplace ERP API`
4. User: Select admin user
5. Permissions: **Read/Write**
6. Generate API Key
7. **COPY** Consumer Key and Consumer Secret (you can't see them again!)

#### Insert Credentials into Database:
```sql
-- Replace YOUR_CONSUMER_KEY and YOUR_CONSUMER_SECRET with actual values
INSERT INTO system_settings (
    setting_key, setting_value, data_type, category,
    description, is_public, is_encrypted
) VALUES
(
    'woocommerce.api_url',
    '"https://sustenance.co.in/wp-json/wc/v3"'::jsonb,
    'string',
    'woocommerce',
    'WooCommerce REST API URL',
    false,
    false
),
(
    'woocommerce.consumer_key',
    '"ck_YOUR_CONSUMER_KEY_HERE"'::jsonb,
    'string',
    'woocommerce',
    'WooCommerce Consumer Key',
    false,
    true
),
(
    'woocommerce.consumer_secret',
    '"cs_YOUR_CONSUMER_SECRET_HERE"'::jsonb,
    'string',
    'woocommerce',
    'WooCommerce Consumer Secret',
    false,
    true
)
ON CONFLICT (setting_key) DO UPDATE SET
    setting_value = EXCLUDED.setting_value,
    is_encrypted = EXCLUDED.is_encrypted;
```

---

## Step 5: Test Manual API Sync

Get a JWT token first, then:

```bash
# Replace YOUR_JWT_TOKEN
curl -X POST "https://marketplaceerp.sustenance.co.in/api/v1/orders/sync" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days": 1, "force_full_sync": false}'
```

**Expected Response:**
```json
{
  "synced": 10,
  "created": 8,
  "updated": 2,
  "skipped": 0,
  "errors": 0,
  "sync_duration_seconds": 3.5,
  "sync_source": "api"
}
```

**Common Errors:**

**Error: "WooCommerce API credentials not configured"**
→ Run Step 4 to add credentials

**Error: "Unable to fetch orders from WooCommerce"**
→ Check WooCommerce API credentials are correct
→ Test manually: `curl https://sustenance.co.in/wp-json/wc/v3/orders?consumer_key=ck_xxx&consumer_secret=cs_xxx`

---

## Step 6: Verify Orders Are Syncing

After fixes, check if orders appear:

```sql
SELECT
    id,
    woo_order_id,
    order_number,
    status,
    total,
    sync_source,
    DATE(created_at) as order_date,
    DATE(last_synced_at) as last_sync
FROM orders
ORDER BY created_at DESC
LIMIT 10;
```

**If you see rows:** ✅ Working!
**If still 0 rows:** Share Render logs

---

## Step 7: Verify Automatic Sync is Running

Check Render logs for scheduled sync messages:

```
🔄 Starting scheduled WooCommerce Orders sync...
✅ Scheduled Orders sync completed: 15 synced (10 created, 5 updated), 0 errors in 4.23s
```

**If you don't see these messages after 3 hours:**
- Check scheduler started: Look for "Background scheduler started successfully"
- Check scheduler job list in `/health` endpoint
- Share Render logs

---

## Testing in Postman/Insomnia

### Get Orders (List)
```http
GET https://marketplaceerp.sustenance.co.in/api/v1/orders?limit=10
Authorization: Bearer YOUR_JWT_TOKEN
```

### Get Order Stats
```http
GET https://marketplaceerp.sustenance.co.in/api/v1/orders/stats
Authorization: Bearer YOUR_JWT_TOKEN
```

### Manual Sync
```http
POST https://marketplaceerp.sustenance.co.in/api/v1/orders/sync
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "days": 7,
  "force_full_sync": false
}
```

---

## Understanding the Simplified Architecture

**What was removed:**
- ❌ Webhook endpoint (`POST /orders/webhook`)
- ❌ HMAC signature validation
- ❌ Webhook payload schemas
- ❌ Complex Pydantic validation on WooCommerce data
- ❌ Webhook secret configuration

**What remains (API sync only):**
- ✅ `WooCommerceService.fetch_orders()` - proven to work
- ✅ Raw dict processing (like Order Extractor)
- ✅ Automatic sync every 3 hours (last 3 days)
- ✅ Manual sync API endpoint (1-90 days configurable)
- ✅ Simple upsert logic (insert or update based on woo_order_id)

**Why this is better:**
- Uses the exact same `WooCommerceService.fetch_orders()` that Order Extractor uses
- No complex schema validation that can fail silently
- Easier to debug (just check logs for API errors)
- More reliable (webhooks can fail for many reasons)
- Simpler codebase (300+ lines removed)

---

## If Still Not Working

**Share these with me:**

1. **Render logs (last 100 lines):**
   ```
   [Copy from Render dashboard]
   ```

2. **Result of Query 1:**
   ```sql
   -- Paste results here
   ```

3. **Manual sync test result:**
   ```bash
   # Paste curl response
   ```

4. **Check health endpoint:**
   ```bash
   curl https://marketplaceerp.sustenance.co.in/health
   ```

I'll help debug from there!
