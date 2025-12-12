"""
================================================================================
Allocation Cleanup Service
================================================================================
Version: 1.0.0
Created: 2024-12-12

Description:
  Service to automatically release stale allocations (older than 24 hours).
  Should be run as a scheduled task (cron/celery).

Usage:
  - Run manually: python -m app.services.allocation_cleanup_service
  - Schedule: Add to cron or Celery Beat
  - Frequency: Every 1 hour recommended

================================================================================
"""

from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from app.database import fetch_all, execute_query, DatabaseTransaction
import logging

logger = logging.getLogger(__name__)


async def release_stale_allocations(timeout_hours: int = 24) -> Dict[str, Any]:
    """
    Release stock allocations older than specified timeout.
    
    Args:
        timeout_hours: Hours before allocation is considered stale (default: 24)
        
    Returns:
        Summary of released allocations
        
    Business Logic:
        - Stock in 'allocated' status for >24 hours is released
        - Changed to 'available' status
        - Deallocation movement logged
        - Admin notified of auto-releases
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Find stale allocations
            stale_query = """
                SELECT 
                    i.id as inventory_id,
                    i.item_id,
                    i.batch_id,
                    i.quantity,
                    i.location,
                    i.updated_at,
                    m.reference_id as order_id,
                    zi.name as item_name,
                    b.batch_number
                FROM inventory i
                JOIN inventory_movements m ON (
                    m.item_id = i.item_id 
                    AND m.batch_id = i.batch_id
                    AND m.reference_type = 'sales_order'
                    AND m.movement_type = 'allocation'
                )
                JOIN zoho_items zi ON i.item_id = zi.id
                JOIN batches b ON i.batch_id = b.id
                WHERE i.status = 'allocated'
                  AND i.updated_at < NOW() - INTERVAL '%s hours'
                ORDER BY i.updated_at ASC
            """ % timeout_hours
            
            stale_allocations = await conn.fetch(stale_query)
            
            if not stale_allocations:
                logger.info("✅ No stale allocations found (timeout: ${timeout_hours}hrs)")
                return {
                    'released_count': 0,
                    'timeout_hours': timeout_hours,
                    'message': 'No stale allocations'
                }
            
            released_items = []
            
            for allocation in stale_allocations:
                inventory_id = allocation['inventory_id']
                item_id = allocation['item_id']
                batch_id = allocation['batch_id']
                quantity = allocation['quantity']
                location = allocation['location']
                order_id = allocation['order_id']
                age_hours = (datetime.now(timezone.utc) - allocation['updated_at']).total_seconds() / 3600
                
                # 2. Release allocation (allocated → available)
                update_query = """
                    UPDATE inventory
                    SET status = 'available', updated_at = NOW()
                    WHERE id = $1
                    RETURNING id
                """
                await conn.execute(update_query, inventory_id)
                
                # 3. Log deallocation movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        item_id, batch_id, movement_type, quantity,
                        from_location, to_location,
                        reference_type, reference_id, notes, created_by
                    ) VALUES ($1, $2, 'deallocation', $3, $4, $4, 
                              'sales_order', $5, $6, NULL)
                """
                notes = f"Auto-released due to timeout ({age_hours:.1f} hours old, limit: {timeout_hours}hrs)"
                await conn.execute(
                    movement_query,
                    item_id,
                    batch_id,
                    quantity,
                    location,
                    order_id,
                    notes
                )
                
                released_items.append({
                    'order_id': order_id,
                    'item_id': item_id,
                    'item_name': allocation['item_name'],
                    'batch_id': batch_id,
                    'batch_number': allocation['batch_number'],
                    'quantity': float(quantity),
                    'location': location,
                    'age_hours': round(age_hours, 1),
                    'allocated_at': allocation['updated_at'].isoformat()
                })
            
            logger.warning(
                f"⚠️ Auto-released {len(released_items)} stale allocation(s) "
                f"(>{timeout_hours}hrs old)"
            )
            
            # 4. Return summary for admin notification
            return {
                'released_count': len(released_items),
                'timeout_hours': timeout_hours,
                'released_items': released_items,
                'message': f'Released {len(released_items)} stale allocations',
                'executed_at': datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to release stale allocations: {e}")
        raise


async def get_stale_allocations_report(timeout_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get report of allocations approaching timeout (for monitoring).
    
    Args:
        timeout_hours: Timeout threshold
        
    Returns:
        List of allocations with remaining time
    """
    try:
        # Find allocations approaching timeout (e.g., >20 hours old)
        warning_threshold = timeout_hours - 4  # 4 hours before timeout
        
        query = """
            SELECT 
                m.reference_id as order_id,
                i.item_id,
                zi.name as item_name,
                i.batch_id,
                b.batch_number,
                i.quantity,
                i.location,
                i.updated_at as allocated_at,
                EXTRACT(EPOCH FROM (NOW() - i.updated_at))/3600 as age_hours,
                $1 - EXTRACT(EPOCH FROM (NOW() - i.updated_at))/3600 as hours_remaining
            FROM inventory i
            JOIN inventory_movements m ON (
                m.item_id = i.item_id 
                AND m.batch_id = i.batch_id
                AND m.reference_type = 'sales_order'
                AND m.movement_type = 'allocation'
            )
            JOIN zoho_items zi ON i.item_id = zi.id
            JOIN batches b ON i.batch_id = b.id
            WHERE i.status = 'allocated'
              AND i.updated_at < NOW() - INTERVAL '%s hours'
            ORDER BY i.updated_at ASC
        """ % warning_threshold
        
        approaching_timeout = await fetch_all(query, timeout_hours)
        
        return [
            {
                'order_id': row['order_id'],
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'batch_number': row['batch_number'],
                'quantity': float(row['quantity']),
                'location': row['location'],
                'allocated_at': row['allocated_at'].isoformat(),
                'age_hours': round(float(row['age_hours']), 1),
                'hours_remaining': round(float(row['hours_remaining']), 1),
                'will_expire_at': (row['allocated_at'] + timedelta(hours=timeout_hours)).isoformat()
            }
            for row in approaching_timeout
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get stale allocations report: {e}")
        raise


# For manual testing
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        print("Running allocation cleanup service...")
        result = await release_stale_allocations(timeout_hours=24)
        print(f"\nResult: {result}")
        
        print("\n\nChecking for approaching timeout...")
        report = await get_stale_allocations_report(timeout_hours=24)
        print(f"Found {len(report)} allocations approaching timeout")
        for item in report:
            print(f"  - Order #{item['order_id']}: {item['hours_remaining']:.1f}hrs remaining")
    
    asyncio.run(main())
