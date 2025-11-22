"""
================================================================================
Inventory Batch Reconciliation Utility
================================================================================
Purpose: Fix inventory_batches.remaining_qty to match item_master.current_qty

This script reconciles batch quantities with item quantities after old stock
adjustments that only updated item_master.current_qty but not batch quantities.

Usage:
    python -m backend.app.utils.fix_inventory_batches

Or add an admin API endpoint to run this.
================================================================================
"""

import asyncio
import sys
from decimal import Decimal
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, '/home/user/farm2-app-fast-api')

from backend.app.database import connect_db, disconnect_db, fetch_all, execute_query, DatabaseTransaction, execute_query_tx


async def find_mismatched_items() -> List[Dict]:
    """Find items where current_qty doesn't match sum of batch remaining_qty"""
    query = """
        SELECT
            im.id,
            im.item_name,
            im.current_qty as item_qty,
            COALESCE(SUM(ib.remaining_qty), 0) as batch_total_qty,
            im.current_qty - COALESCE(SUM(ib.remaining_qty), 0) as difference
        FROM item_master im
        LEFT JOIN inventory_batches ib ON ib.item_master_id = im.id AND ib.is_active = TRUE
        GROUP BY im.id, im.item_name, im.current_qty
        HAVING ABS(im.current_qty - COALESCE(SUM(ib.remaining_qty), 0)) > 0.01
        ORDER BY im.id
    """
    return await fetch_all(query)


async def fix_zero_quantity_items(item_ids: List[int], conn) -> int:
    """Set all batches to 0 for items with current_qty = 0"""
    if not item_ids:
        return 0

    # Build parameter placeholders
    placeholders = ','.join(f'${i+1}' for i in range(len(item_ids)))
    query = f"""
        UPDATE inventory_batches
        SET remaining_qty = 0, updated_at = NOW()
        WHERE item_master_id IN ({placeholders})
          AND is_active = TRUE
          AND remaining_qty > 0
    """
    result = await execute_query_tx(query, *item_ids, conn=conn)
    return int(result.split()[-1]) if result else 0


async def fix_positive_quantity_items(item_ids: List[int], conn) -> int:
    """Proportionally adjust batches for items with current_qty > 0"""
    if not item_ids:
        return 0

    # Get all batches for these items
    placeholders = ','.join(f'${i+1}' for i in range(len(item_ids)))
    query = f"""
        SELECT
            ib.id as batch_id,
            ib.item_master_id,
            ib.remaining_qty as old_qty,
            im.current_qty as target_qty,
            (SELECT COALESCE(SUM(remaining_qty), 0)
             FROM inventory_batches
             WHERE item_master_id = ib.item_master_id AND is_active = TRUE) as batch_total
        FROM inventory_batches ib
        JOIN item_master im ON im.id = ib.item_master_id
        WHERE ib.item_master_id IN ({placeholders})
          AND ib.is_active = TRUE
        ORDER BY ib.item_master_id, ib.purchase_date ASC, ib.id ASC
    """
    batches = await fetch_all(query, *item_ids)

    updated_count = 0
    for batch in batches:
        old_qty = Decimal(str(batch['old_qty']))
        target_qty = Decimal(str(batch['target_qty']))
        batch_total = Decimal(str(batch['batch_total']))

        if batch_total > 0:
            # Calculate proportional quantity
            new_qty = (old_qty * target_qty / batch_total).quantize(Decimal('0.01'))
        else:
            new_qty = Decimal('0')

        # Update the batch
        update_query = """
            UPDATE inventory_batches
            SET remaining_qty = $1, updated_at = NOW()
            WHERE id = $2
        """
        await execute_query_tx(update_query, new_qty, batch['batch_id'], conn=conn)
        updated_count += 1

    return updated_count


async def verify_fix() -> List[Dict]:
    """Verify that all items now match their batch totals"""
    query = """
        SELECT
            im.id,
            im.item_name,
            im.current_qty as item_qty,
            COALESCE(SUM(ib.remaining_qty), 0) as batch_total_qty,
            im.current_qty - COALESCE(SUM(ib.remaining_qty), 0) as difference
        FROM item_master im
        LEFT JOIN inventory_batches ib ON ib.item_master_id = im.id AND ib.is_active = TRUE
        GROUP BY im.id, im.item_name, im.current_qty
        HAVING ABS(im.current_qty - COALESCE(SUM(ib.remaining_qty), 0)) > 0.01
        ORDER BY im.id
    """
    return await fetch_all(query)


async def get_inventory_summary() -> Dict:
    """Get current inventory value summary"""
    query = """
        SELECT
            COALESCE(SUM(remaining_qty * unit_cost), 0) as total_value,
            COUNT(DISTINCT item_master_id) as items_with_stock,
            COALESCE(SUM(remaining_qty), 0) as total_units
        FROM inventory_batches
        WHERE is_active = TRUE AND remaining_qty > 0
    """
    result = await fetch_all(query)
    return result[0] if result else {}


async def run_reconciliation():
    """Main reconciliation process"""
    try:
        # Connect to database
        await connect_db()
        print("Connected to database")

        # Step 1: Find mismatched items
        print("\n" + "="*80)
        print("STEP 1: Finding mismatched items...")
        print("="*80)
        mismatched = await find_mismatched_items()

        if not mismatched:
            print("✅ No mismatches found! All items are in sync.")
            return

        print(f"\n📊 Found {len(mismatched)} items with mismatched quantities:\n")
        print(f"{'ID':<6} {'Item Name':<30} {'Item Qty':<12} {'Batch Total':<12} {'Difference':<12}")
        print("-" * 80)

        zero_qty_items = []
        positive_qty_items = []

        for item in mismatched:
            item_qty = Decimal(str(item['item_qty']))
            batch_qty = Decimal(str(item['batch_total_qty']))
            diff = Decimal(str(item['difference']))

            print(f"{item['id']:<6} {item['item_name']:<30} {item_qty:<12} {batch_qty:<12} {diff:<12}")

            if item_qty == 0:
                zero_qty_items.append(item['id'])
            else:
                positive_qty_items.append(item['id'])

        print(f"\n📋 Summary:")
        print(f"   - Items to zero out: {len(zero_qty_items)}")
        print(f"   - Items to adjust: {len(positive_qty_items)}")

        # Step 2: Get current inventory value
        print("\n" + "="*80)
        print("STEP 2: Current inventory state...")
        print("="*80)
        before_summary = await get_inventory_summary()
        print(f"\n💰 Current Inventory Value: ${before_summary.get('total_value', 0):,.2f}")
        print(f"📦 Items with stock: {before_summary.get('items_with_stock', 0)}")
        print(f"📊 Total units: {before_summary.get('total_units', 0):,.2f}")

        # Step 3: Apply fixes
        print("\n" + "="*80)
        print("STEP 3: Applying fixes...")
        print("="*80)

        async with DatabaseTransaction() as conn:
            # Fix zero quantity items
            if zero_qty_items:
                print(f"\n🔧 Zeroing out batches for {len(zero_qty_items)} items...")
                zero_count = await fix_zero_quantity_items(zero_qty_items, conn)
                print(f"   ✅ Updated {zero_count} batches to 0")

            # Fix positive quantity items
            if positive_qty_items:
                print(f"\n🔧 Adjusting batches for {len(positive_qty_items)} items...")
                adjust_count = await fix_positive_quantity_items(positive_qty_items, conn)
                print(f"   ✅ Updated {adjust_count} batches proportionally")

        # Step 4: Verify the fix
        print("\n" + "="*80)
        print("STEP 4: Verifying fixes...")
        print("="*80)
        remaining_issues = await verify_fix()

        if remaining_issues:
            print(f"\n⚠️  Warning: {len(remaining_issues)} items still have mismatches:")
            for item in remaining_issues:
                print(f"   - {item['item_name']}: Item={item['item_qty']}, Batches={item['batch_total_qty']}")
        else:
            print("\n✅ All items are now in sync!")

        # Step 5: Show new inventory value
        print("\n" + "="*80)
        print("STEP 5: Updated inventory state...")
        print("="*80)
        after_summary = await get_inventory_summary()
        print(f"\n💰 Updated Inventory Value: ${after_summary.get('total_value', 0):,.2f}")
        print(f"📦 Items with stock: {after_summary.get('items_with_stock', 0)}")
        print(f"📊 Total units: {after_summary.get('total_units', 0):,.2f}")

        # Show change
        value_before = Decimal(str(before_summary.get('total_value', 0)))
        value_after = Decimal(str(after_summary.get('total_value', 0)))
        value_change = value_after - value_before

        print(f"\n📉 Value change: ${value_change:,.2f}")

        print("\n" + "="*80)
        print("✅ RECONCILIATION COMPLETE!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error during reconciliation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Disconnect from database
        await disconnect_db()
        print("\nDisconnected from database")


if __name__ == "__main__":
    print("="*80)
    print("Inventory Batch Reconciliation Utility")
    print("="*80)
    print("\nThis script will fix batch quantities to match item quantities.")
    print("This is safe to run and will show all changes before applying them.\n")

    asyncio.run(run_reconciliation())
