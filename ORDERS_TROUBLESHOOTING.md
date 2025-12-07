# Orders Module Troubleshooting Guide

## Issue: Webhooks and API Sync Not Working

Both webhooks and API sync failing suggests a **common issue** - likely configuration or deployment.

---

## Step 1: Check Render Deployment Status

### In Render Dashboard:
1. Go to your service
2. Check **Latest Deploy** tab
3. Verify:
   - ✅ Deploy status: **Live**
   - ✅ Commit: `eab1363` (fix: Handle JSONB encoding...)
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

**For webhook requests, look for:**
```
Received webhook: topic=order.created, source=https://sustenance.co.in
```

**If you see:**
```
❌ Webhook secret not configured
❌ Invalid webhook signature
```
→ Continue to Step 3

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

**Expected result:** 4 rows
- `woocommerce.api_url`
- `woocommerce.consumer_key`
- `woocommerce.consumer_secret`
- `woocommerce.webhook_secret`

**If missing rows:** Continue to Step 4

---

### Query 2: Test Webhook Secret Extraction
```sql
SELECT
    setting_key,
    setting_value,
    setting_value::text as extracted_value,
    CASE
        WHEN setting_value::text LIKE '"%"'
        THEN regexp_replace(setting_value::text, '^"|"$', '', 'g')
        ELSE setting_value::text
    END as final_value
FROM system_settings
WHERE setting_key = 'woocommerce.webhook_secret';
```

**Expected `final_value`:** `2a7429ec-6ac8-4f44-9cac-1c066e355b97`

**If different or NULL:** Webhook secret is wrong. Re-run INSERT from Step 4.

---

### Query 3: Check Tables Exist
```sql
SELECT tablename
FROM pg_tables
WHERE tablename IN ('orders', 'order_items')
  AND schemaname = 'public';
```

**Expected:** 2 rows

**If 0 rows:** Migration didn't run. Re-run `026_orders_module.sql`

---

### Query 4: Check for Any Orders
```sql
SELECT
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE sync_source = 'webhook') as from_webhooks,
    COUNT(*) FILTER (WHERE sync_source = 'api') as from_api,
    MAX(created_at) as latest_order
FROM orders;
```

**If total_orders = 0:** No orders have been synced yet (expected if webhooks/API failing)

---

##Step 4: Fix Missing WooCommerce API Credentials

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

## Step 5: Test Webhook Endpoint

### Test from command line:
```bash
# Replace with your actual values
WEBHOOK_SECRET="2a7429ec-6ac8-4f44-9cac-1c066e355b97"
API_URL="https://marketplaceerp.sustenance.co.in"

# Generate test signature
PAYLOAD='{"id":999,"number":"999","status":"pending","date_created":"2025-12-07T12:00:00","total":"100.00","billing":{},"shipping":{},"line_items":[]}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" -binary | base64)

# Send test webhook
curl -X POST "$API_URL/api/v1/orders/webhook" \
  -H "Content-Type: application/json" \
  -H "X-WC-Webhook-Signature: $SIGNATURE" \
  -H "X-WC-Webhook-Topic: order.created" \
  -H "X-WC-Webhook-Source: https://sustenance.co.in" \
  -d "$PAYLOAD"
```

**Expected Response:**
```json
{
  "valid": true,
  "message": "Order created successfully",
  "order_id": 1
}
```

**If you get HTTP 401:** Signature validation failing
**If you get HTTP 500:** Check Render logs for error

---

## Step 6: Test Manual API Sync

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

## Step 7: Check WooCommerce Webhook Delivery Logs

### In WooCommerce:
1. Settings → Advanced → Webhooks
2. Click on "marketplace erp order created"
3. Scroll down to **Delivery Logs**
4. Click **View Logs**

**Look for:**
- ✅ **HTTP 200** = Success (webhook working!)
- ❌ **HTTP 401** = Signature validation failed (secret mismatch)
- ❌ **HTTP 500** = Server error (check Render logs)
- ❌ **Failed to deliver** = Network/DNS issue

**If all HTTP 401:**
- Secret in WooCommerce doesn't match database
- Re-check Query 2 results
- Re-save webhook in WooCommerce

**If HTTP 500:**
- Check Render logs for Python traceback
- Share the error here

---

## Step 8: Verify Orders Are Syncing

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

## Quick Checklist

- [ ] Render deploy is live with commit `eab1363`
- [ ] Render logs show scheduler started
- [ ] Query 1: All 4 WooCommerce settings exist
- [ ] Query 2: Webhook secret extracts correctly
- [ ] Query 3: Tables exist
- [ ] WooCommerce API credentials configured (if missing)
- [ ] Test webhook endpoint returns HTTP 200
- [ ] Test manual sync returns success
- [ ] WooCommerce delivery logs show HTTP 200
- [ ] Query shows orders in database

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

3. **WooCommerce webhook delivery status:**
   - HTTP status code: ___
   - Error message: ___

4. **Manual sync test result:**
   ```bash
   # Paste curl response
   ```

I'll help debug from there!
