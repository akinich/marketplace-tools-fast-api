"""
Inventory Allocation Service Functions
For order integration - allocate, deallocate, and confirm stock
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
import logging

logger = logging.getLogger(__name__)


async def allocate_stock_to_order(
    order_id: int,
    item_id: int,
    quantity: Decimal,
    batch_ids: Optional[List[int]] = None,
    location: str = 'packed_warehouse',
    user_id: str = None
) -> Dict[str, Any]:
    """
    Allocate stock to a sales order.
    Changes status from 'available' → 'allocated'
    
    Args:
        order_id: Sales order ID
        item_id: Item ID to allocate
        quantity: Quantity to allocate
        batch_ids: Specific batches (optional, uses FIFO if not provided)
        location: Location to allocate from
        user_id: User performing allocation
        
    Returns:
        Allocation details with batches allocated
        
    Raises:
        ValueError: If insufficient stock or validation fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Get item info
            item_query = "SELECT id, name, sku FROM zoho_items WHERE id = $1"
            item = await conn.fetchrow(item_query, item_id)
            if not item:
                raise ValueError(f"Item {item_id} not found")
            
            # 2. Check if order exists (optional - depends on sales_orders table structure)
            # order_query = "SELECT id FROM sales_orders WHERE id = $1"
            # order = await conn.fetchrow(order_query, order_id)
            # if not order:
            #     raise ValueError(f"Order {order_id} not found")
            
            # 3. Get available stock (use specific batches or FIFO)
            if batch_ids:
                # Use specified batches
                batch_placeholders = ','.join([f'${i+3}' for i in range(len(batch_ids))])
                stock_query = f"""
                    SELECT
                        i.id, i.batch_id, i.quantity, b.batch_number,
                        b.is_repacked
                    FROM inventory i
                    JOIN batches b ON i.batch_id = b.id
                    WHERE i.item_id = $1
                      AND i.location = $2
                      AND i.batch_id IN ({batch_placeholders})
                      AND i.status = 'available'
                    ORDER BY b.is_repacked DESC, i.entry_date ASC
                """
                params = [item_id, location] + batch_ids
                available_stock = await conn.fetch(stock_query, *params)
            else:
                # FIFO: Prioritize repacked batches, then oldest first
                stock_query = """
                    SELECT
                        i.id, i.batch_id, i.quantity, b.batch_number,
                        b.is_repacked
                    FROM inventory i
                    JOIN batches b ON i.batch_id = b.id
                    WHERE i.item_id = $1
                      AND i.location = $2
                      AND i.status = 'available'
                    ORDER BY b.is_repacked DESC, i.entry_date ASC
                """
                available_stock = await conn.fetch(stock_query, item_id, location)
            
            if not available_stock:
                raise ValueError(f"No available stock found for item {item['name']} at {location}")
            
            # 4. Calculate total available
            total_available = sum(Decimal(str(s['quantity'])) for s in available_stock)
            if total_available < quantity:
                raise ValueError(
                    f"Insufficient stock. Requested: {quantity}, Available: {total_available}"
                )
            
            # 5. Allocate stock (FIFO - take from batches in order)
            allocated_batches = []
            remaining_to_allocate = quantity
            
            for stock_record in available_stock:
                if remaining_to_allocate <= 0:
                    break
                
                record_qty = Decimal(str(stock_record['quantity']))
                allocate_qty = min(record_qty, remaining_to_allocate)
                
                # Update inventory record
                if allocate_qty == record_qty:
                    # Allocate entire record
                    update_query = """
                        UPDATE inventory
                        SET status = 'allocated', updated_at = NOW()
                        WHERE id = $1
                    """
                    await conn.execute(update_query, stock_record['id'])
                else:
                    # Partial allocation - split record
                    # Reduce available quantity
                    reduce_query = """
                        UPDATE inventory
                        SET quantity = quantity - $1, updated_at = NOW()
                        WHERE id = $2
                    """
                    await conn.execute(reduce_query, allocate_qty, stock_record['id'])
                    
                    # Create new allocated record
                    split_query = """
                        INSERT INTO inventory (
                            item_id, batch_id, location, quantity, grade, status,
                            shelf_life_days, entry_date, expiry_date, created_by
                        )
                        SELECT
                            item_id, batch_id, location, $1, grade, 'allocated',
                            shelf_life_days, entry_date, expiry_date, $2
                        FROM inventory
                        WHERE id = $3
                    """
                    await conn.execute(split_query, allocate_qty, user_id, stock_record['id'])
                
                # Log movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        item_id, batch_id, movement_type, quantity,
                        from_location, to_location,
                        reference_type, reference_id, notes, created_by
                    ) VALUES ($1, $2, 'allocation', $3, $4, $4, 'sales_order', $5, $6, $7)
                """
                await conn.execute(
                    movement_query,
                    item_id,
                    stock_record['batch_id'],
                    allocate_qty,
                    location,
                    order_id,
                    f"Allocated to order #{order_id}",
                    user_id
                )
                
                allocated_batches.append({
                    'batch_id': stock_record['batch_id'],
                    'batch_number': stock_record['batch_number'],
                    'quantity': float(allocate_qty),
                    'is_repacked': stock_record['is_repacked']
                })
                
                remaining_to_allocate -= allocate_qty
            
            logger.info(
                f"✅ Allocated {quantity} of {item['name']} to order #{order_id} "
                f"from {len(allocated_batches)} batch(es)"
            )
            
            return {
                'order_id': order_id,
                'item_id': item_id,
                'item_name': item['name'],
                'total_allocated': float(quantity),
                'batches_allocated': allocated_batches,
                'status': 'allocated',
                'created_at': datetime.now()
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Allocation failed: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to allocate stock: {e}")
        raise


async def deallocate_stock_from_order(
    order_id: int,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Deallocate/release stock from a cancelled order.
    Changes status from 'allocated' → 'available'
    
    Args:
        order_id: Sales order ID
        user_id: User performing deallocation
        
    Returns:
        Deallocation details
        
    Raises:
        ValueError: If no allocations found
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Find allocated stock for this order
            find_query = """
                SELECT
                    m.item_id, m.batch_id, m.quantity, m.from_location,
                    i.name as item_name, b.batch_number
                FROM inventory_movements m
                JOIN zoho_items i ON m.item_id = i.id
                JOIN batches b ON m.batch_id = b.id
                WHERE m.reference_type = 'sales_order'
                  AND m.reference_id = $1
                  AND m.movement_type = 'allocation'
            """
            allocations = await conn.fetch(find_query, order_id)
            
            if not allocations:
                raise ValueError(f"No allocations found for order #{order_id}")
            
            deallocated_items = []
            
            for allocation in allocations:
                item_id = allocation['item_id']
                batch_id = allocation['batch_id']
                quantity = Decimal(str(allocation['quantity']))
                location = allocation['from_location']
                
                # 2. Change allocated stock back to available
                update_query = """
                    UPDATE inventory
                    SET status = 'available', updated_at = NOW()
                    WHERE item_id = $1
                      AND batch_id = $2
                      AND location = $3
                      AND status = 'allocated'
                """
                await conn.execute(update_query, item_id, batch_id, location)
                
                # 3. Log deallocation movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        item_id, batch_id, movement_type, quantity,
                        from_location, to_location,
                        reference_type, reference_id, notes, created_by
                    ) VALUES ($1, $2, 'adjustment', $3, $4, $4, 'sales_order', $5, $6, $7)
                """
                await conn.execute(
                    movement_query,
                    item_id,
                    batch_id,
                    quantity,
                    location,
                    order_id,
                    f"Deallocated from cancelled order #{order_id}",
                    user_id
                )
                
                deallocated_items.append({
                    'item_id': item_id,
                    'item_name': allocation['item_name'],
                    'batch_id': batch_id,
                    'batch_number': allocation['batch_number'],
                    'quantity': float(quantity),
                    'location': location
                })
            
            logger.info(
                f"✅ Deallocated stock from order #{order_id}: "
                f"{len(deallocated_items)} item(s)"
            )
            
            return {
                'order_id': order_id,
                'items_deallocated': deallocated_items,
                'status': 'deallocated',
                'created_at': datetime.now()
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Deallocation failed: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to deallocate stock: {e}")
        raise


async def confirm_allocation(
    order_id: int,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Confirm allocation and debit stock (order → invoice).
    Changes status from 'allocated' → 'delivered' and decrements quantity
    
    Args:
        order_id: Sales order ID
        user_id: User confirming allocation
        
    Returns:
        Confirmation details
        
    Raises:
        ValueError: If no allocations found
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Find allocated stock for this order
            find_query = """
                SELECT
                    m.item_id, m.batch_id, m.quantity, m.from_location,
                    i.name as item_name, b.batch_number
                FROM inventory_movements m
                JOIN zoho_items i ON m.item_id = i.id
                JOIN batches b ON m.batch_id = b.id
                WHERE m.reference_type = 'sales_order'
                  AND m.reference_id = $1
                  AND m.movement_type = 'allocation'
            """
            allocations = await conn.fetch(find_query, order_id)
            
            if not allocations:
                raise ValueError(f"No allocations found for order #{order_id}")
            
            confirmed_items = []
            
            for allocation in allocations:
                item_id = allocation['item_id']
                batch_id = allocation['batch_id']
                quantity = Decimal(str(allocation['quantity']))
                location = allocation['from_location']
                
                # 2. Update allocated stock to delivered and decrement quantity
                # Option A: Change status to 'delivered' and keep quantity
                # Option B: Delete record entirely (stock is gone)
                # We'll use Option A for audit trail
                update_query = """
                    UPDATE inventory
                    SET status = 'delivered',
                        quantity = 0,
                        updated_at = NOW()
                    WHERE item_id = $1
                      AND batch_id = $2
                      AND location = $3
                      AND status = 'allocated'
                """
                await conn.execute(update_query, item_id, batch_id, location)
                
                # 3. Log stock out movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        item_id, batch_id, movement_type, quantity,
                        from_location, to_location,
                        reference_type, reference_id, notes, created_by
                    ) VALUES ($1, $2, 'stock_out', $3, $4, NULL, 'sales_order', $5, $6, $7)
                """
                await conn.execute(
                    movement_query,
                    item_id,
                    batch_id,
                    quantity,
                    location,
                    order_id,
                    f"Stock out for order #{order_id} (invoiced)",
                    user_id
                )
                
                confirmed_items.append({
                    'item_id': item_id,
                    'item_name': allocation['item_name'],
                    'batch_id': batch_id,
                    'batch_number': allocation['batch_number'],
                    'quantity': float(quantity),
                    'location': location
                })
            
            logger.info(
                f"✅ Confirmed allocation for order #{order_id}: "
                f"{len(confirmed_items)} item(s), stock debited"
            )
            
            return {
                'order_id': order_id,
                'items_confirmed': confirmed_items,
                'status': 'confirmed',
                'created_at': datetime.now()
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Confirmation failed: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to confirm allocation: {e}")
        raise
