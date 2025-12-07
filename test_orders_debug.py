#!/usr/bin/env python3
"""
Orders Module Diagnostic Script
Run this to identify why webhooks and API sync aren't working
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def main():
    print("=" * 80)
    print("ORDERS MODULE DIAGNOSTIC")
    print("=" * 80)
    print()

    # Test 1: Check if database connection works
    print("TEST 1: Database Connection")
    print("-" * 80)
    try:
        from app.database import connect_db, fetch_one, disconnect_db
        await connect_db()
        result = await fetch_one("SELECT 1 as test")
        if result and result['test'] == 1:
            print("✅ Database connection: OK")
        else:
            print("❌ Database connection: FAILED")
            return
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return
    print()

    # Test 2: Check if orders tables exist
    print("TEST 2: Database Tables")
    print("-" * 80)
    try:
        from app.database import fetch_all
        tables = await fetch_all("""
            SELECT tablename
            FROM pg_tables
            WHERE tablename IN ('orders', 'order_items')
              AND schemaname = 'public'
        """)
        table_names = [t['tablename'] for t in tables]

        if 'orders' in table_names:
            print("✅ Table 'orders': EXISTS")
        else:
            print("❌ Table 'orders': MISSING")

        if 'order_items' in table_names:
            print("✅ Table 'order_items': EXISTS")
        else:
            print("❌ Table 'order_items': MISSING")

        # Count rows
        order_count = await fetch_one("SELECT COUNT(*) as count FROM orders")
        print(f"   Orders in database: {order_count['count']}")
    except Exception as e:
        print(f"❌ Table check failed: {e}")
    print()

    # Test 3: Check webhook secret configuration
    print("TEST 3: Webhook Secret Configuration")
    print("-" * 80)
    try:
        from app.database import fetch_one
        secret_row = await fetch_one("""
            SELECT setting_key, setting_value, is_encrypted
            FROM system_settings
            WHERE setting_key = 'woocommerce.webhook_secret'
        """)

        if secret_row:
            print("✅ Webhook secret: CONFIGURED")
            print(f"   Value: {secret_row['setting_value']}")
            print(f"   Encrypted: {secret_row['is_encrypted']}")

            # Test extraction logic
            webhook_secret = secret_row['setting_value']
            import json
            if isinstance(webhook_secret, str) and webhook_secret.startswith('"') and webhook_secret.endswith('"'):
                webhook_secret = json.loads(webhook_secret)
            webhook_secret = str(webhook_secret)
            print(f"   Extracted value: {webhook_secret}")
        else:
            print("❌ Webhook secret: NOT CONFIGURED")
            print("   Run this SQL:")
            print("""
            INSERT INTO system_settings (
                setting_key, setting_value, data_type, category,
                description, is_public, is_encrypted
            ) VALUES (
                'woocommerce.webhook_secret',
                '"2a7429ec-6ac8-4f44-9cac-1c066e355b97"'::jsonb,
                'string', 'woocommerce',
                'Secret for validating WooCommerce webhook signatures',
                false, true
            );
            """)
    except Exception as e:
        print(f"❌ Webhook secret check failed: {e}")
    print()

    # Test 4: Check WooCommerce API credentials
    print("TEST 4: WooCommerce API Credentials")
    print("-" * 80)
    try:
        from app.database import fetch_all
        woo_settings = await fetch_all("""
            SELECT setting_key,
                   CASE
                       WHEN setting_key LIKE '%secret%' THEN '***HIDDEN***'
                       ELSE setting_value::text
                   END as value
            FROM system_settings
            WHERE setting_key LIKE 'woocommerce.%'
            ORDER BY setting_key
        """)

        required_keys = ['woocommerce.api_url', 'woocommerce.consumer_key', 'woocommerce.consumer_secret']
        found_keys = [s['setting_key'] for s in woo_settings]

        for key in required_keys:
            if key in found_keys:
                print(f"✅ {key}: CONFIGURED")
            else:
                print(f"❌ {key}: MISSING")

        if 'woocommerce.webhook_secret' in found_keys:
            print(f"✅ woocommerce.webhook_secret: CONFIGURED")
        else:
            print(f"❌ woocommerce.webhook_secret: MISSING")

        print("\nAll WooCommerce settings:")
        for setting in woo_settings:
            print(f"   - {setting['setting_key']}: {setting['value']}")

        # Test if we can get credentials
        if all(key in found_keys for key in required_keys):
            from app.services.woocommerce_service import WooCommerceService
            try:
                api_url, consumer_key, consumer_secret = await WooCommerceService.get_api_credentials()
                print("\n✅ WooCommerce API credentials extraction: SUCCESS")
                print(f"   API URL: {api_url}")
            except Exception as e:
                print(f"\n❌ WooCommerce API credentials extraction: FAILED - {e}")
    except Exception as e:
        print(f"❌ WooCommerce settings check failed: {e}")
    print()

    # Test 5: Test OrdersService import
    print("TEST 5: Orders Service Import")
    print("-" * 80)
    try:
        from app.services.orders_service import OrdersService
        print("✅ OrdersService: IMPORT OK")
    except Exception as e:
        print(f"❌ OrdersService: IMPORT FAILED - {e}")
        import traceback
        traceback.print_exc()
    print()

    # Test 6: Test manual sync (if credentials exist)
    print("TEST 6: Manual Sync Test")
    print("-" * 80)
    try:
        from app.services.orders_service import OrdersService
        from datetime import datetime, timedelta

        print("Attempting to sync orders from last 1 day...")
        result = await OrdersService.sync_orders_from_woocommerce(days=1, force_full_sync=False)

        print(f"✅ Sync completed:")
        print(f"   Synced: {result.synced}")
        print(f"   Created: {result.created}")
        print(f"   Updated: {result.updated}")
        print(f"   Errors: {result.errors}")
        print(f"   Duration: {result.sync_duration_seconds}s")
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
    print()

    # Test 7: Test webhook signature validation
    print("TEST 7: Webhook Signature Validation")
    print("-" * 80)
    try:
        from app.services.orders_service import OrdersService

        test_payload = b'{"test": "data"}'
        test_secret = "2a7429ec-6ac8-4f44-9cac-1c066e355b97"

        # Generate valid signature
        import hmac
        import hashlib
        import base64

        signature = base64.b64encode(
            hmac.new(test_secret.encode('utf-8'), test_payload, hashlib.sha256).digest()
        ).decode('utf-8')

        is_valid = await OrdersService.validate_webhook_signature(test_payload, signature, test_secret)

        if is_valid:
            print("✅ Webhook signature validation: WORKING")
        else:
            print("❌ Webhook signature validation: FAILED")
    except Exception as e:
        print(f"❌ Webhook signature test failed: {e}")
    print()

    # Cleanup
    await disconnect_db()

    print("=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
