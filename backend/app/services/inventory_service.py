"""
================================================================================
Marketplace ERP - Inventory Management Service
================================================================================
Version: 1.0.0
Last Updated: 2024-12-07

Description:
  Business logic for inventory management. Handles stock tracking across
  multiple locations, stock movements,

 adjustments with approval workflow,
  reorder levels, and inventory reports.

Functions:
  Stock Management:
    - add_stock_entry: Manual stock entry (for testing)
    - get_inventory_list: List inventory with filters
    - get_batch_inventory: Batch-wise inventory view
    - check_stock_availability: Real-time availability check
    
  Stock Movements:
    - record_stock_movement: Log stock movement
    - transfer_location: Move stock between locations
    
  Adjustments:
    - create_adjustment: Create adjustment request
    - approve_adjustment: Admin approval
    - apply_adjustment: Apply approved adjustment
    
  Reorder Levels:
    - configure_reorder_level: Set reorder levels
    - get_low_stock_items: Items below threshold
    
  Reports:
    - generate_current_stock_report: Current stock
    - generate_stock_movement_report: Movement history
    - generate_batch_age_report: Batch aging
    - get_expiring_items: Items expiring soon

================================================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncpg

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
from app.utils.timezone import now_ist
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryMovementCreate,
    LocationTransferRequest, InventoryAdjustmentRequest,
    InventoryAdjustmentApproval, ReorderLevelConfig,
    StockAvailabilityQuery, VALID_LOCATIONS, VALID_STATUSES
)

logger = logging.getLogger(__name__)


# ============================================================================
# STOCK MANAGEMENT
# ============================================================================

async def add_stock_entry(
    request: InventoryCreate,
    user_id: str
) -> Dict[str, Any]:
    """
    Manual stock entry (temporary endpoint for testing until Packing module ready).
    
    Args:
        request: Stock entry request
        user_id: User UUID
        
    Returns:
        Created inventory record
        
    Raises:
        ValueError: If validation fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Validate item exists
            item_query = "SELECT id, name, sku FROM zoho_items WHERE id = $1"
            item = await conn.fetchrow(item_query, request.item_id)
            if not item:
                raise ValueError(f"Item {request.item_id} not found")
            
            # 2. Validate batch exists
            batch_query = "SELECT id, batch_number FROM batches WHERE id = $1"
            batch = await conn.fetchrow(batch_query, request.batch_id)
            if not batch:
                raise ValueError(f"Batch {request.batch_id} not found")
            
            # 3. Use provided entry_date or default to now
            entry_date = request.entry_date or now_ist()
            
            # 4. Insert inventory record (expiry_date auto-calculated by trigger)
            insert_query = """
                INSERT INTO inventory (
                    item_id, batch_id, location, quantity, grade,
                    shelf_life_days, entry_date, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, expiry_date, created_at, updated_at
            """
            result = await conn.fetchrow(
                insert_query,
                request.item_id,
                request.batch_id,
                request.location,
                request.quantity,
                request.grade,
                request.shelf_life_days,
                entry_date,
                user_id
            )
            
            # 5. Log stock movement
            await conn.execute("""
                INSERT INTO inventory_movements (
                    item_id, batch_id, movement_type, quantity,
                    to_location, reference_type, notes, created_by
                )
                VALUES ($1, $2, 'stock_in', $3, $4, 'manual', 'Manual stock entry', $5)
            """, request.item_id, request.batch_id, request.quantity,
                request.location, user_id)
            
            logger.info(
                f"✅ Added stock: {item['name']} (Batch: {batch['batch_number']}) "
                f"- {request.quantity} units to {request.location}"
            )
            
            return {
                'id': result['id'],
                'item_id': request.item_id,
                'item_name': item['name'],
                'item_sku': item['sku'],
                'batch_id': request.batch_id,
                'batch_number': batch['batch_number'],
                'location': request.location,
                'quantity': request.quantity,
                'grade': request.grade,
                'status': 'available',
                'shelf_life_days': request.shelf_life_days,
                'entry_date': entry_date,
                'expiry_date': result['expiry_date'],
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in stock entry: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add stock entry: {e}")
        raise


async def get_inventory_list(
    location: Optional[str] = None,
    status: Optional[str] = None,
    item_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    grade: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List inventory with filtering and pagination.
    
    Args:
        location: Filter by location
        status: Filter by status
        item_id: Filter by item
        batch_id: Filter by batch
        grade: Filter by grade
        expiring_within_days: Show items expiring within N days
        page: Page number
        limit: Items per page
        
    Returns:
        Paginated inventory list
    """
    try:
        # Build WHERE conditions
        conditions = []
        params = []
        param_count = 1
        
        if location:
            conditions.append(f"i.location = ${param_count}")
            params.append(location)
            param_count += 1
        
        if status:
            conditions.append(f"i.status = ${param_count}")
            params.append(status)
            param_count += 1
        
        if item_id:
            conditions.append(f"i.item_id = ${param_count}")
            params.append(item_id)
            param_count += 1
        
        if batch_id:
            conditions.append(f"i.batch_id = ${param_count}")
            params.append(batch_id)
            param_count += 1
        
        if grade:
            conditions.append(f"i.grade = ${param_count}")
            params.append(grade)
            param_count += 1
        
        if expiring_within_days:
            expiry_threshold = date.today() + timedelta(days=expiring_within_days)
            conditions.append(f"i.expiry_date IS NOT NULL AND i.expiry_date <= ${param_count}")
            params.append(expiry_threshold)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM inventory i
            {where_clause}
        """
        count_result = await fetch_one(count_query, *params)
        total = count_result['total'] if count_result else 0
        
        # Get paginated results
        offset = (page - 1) * limit
        list_query = f"""
            SELECT
                i.id, i.item_id, i.batch_id, i.location, i.quantity,
                i.grade, i.status, i.shelf_life_days, i.entry_date,
                i.expiry_date, i.created_at, i.updated_at,
                item.name as item_name, item.sku as item_sku,
                b.batch_number,
                u.email as created_by
            FROM inventory i
            JOIN zoho_items item ON i.item_id = item.id
            JOIN batches b ON i.batch_id = b.id
            LEFT JOIN auth.users u ON i.created_by = u.id
            {where_clause}
            ORDER BY i.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])
        
        items = await fetch_all(list_query, *params)
        
        # Calculate pages
        import math
        pages = math.ceil(total / limit) if total > 0 else 1
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': limit,
            'pages': pages
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list inventory: {e}")
        raise


async def get_batch_inventory(batch_id: int) -> Dict[str, Any]:
    """
    Get complete inventory breakdown for a specific batch.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        Batch inventory details with locations and movements
    """
    try:
        # 1. Get batch info
        batch_query = """
            SELECT b.id, b.batch_number, b.is_repacked, b.status,
                   b.created_at
            FROM batches b
            WHERE b.id = $1
        """
        batch = await fetch_one(batch_query, batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        # 2. Get inventory records for this batch
        inventory_query = """
            SELECT
                i.id, i.item_id, i.location, i.quantity, i.grade,
                i.status, i.entry_date, i.expiry_date,
                item.name as item_name, item.sku as item_sku
            FROM inventory i
            JOIN zoho_items item ON i.item_id = item.id
            WHERE i.batch_id = $1
            ORDER BY i.location, i.created_at
        """
        locations = await fetch_all(inventory_query, batch_id)
        
        # 3. Get movement history
        movements_query = """
            SELECT
                m.id, m.movement_type, m.quantity, m.from_location,
                m.to_location, m.reference_type, m.notes, m.created_at,
                item.name as item_name,
                u.email as created_by
            FROM inventory_movements m
            JOIN zoho_items item ON m.item_id = item.id
            LEFT JOIN auth.users u ON m.created_by = u.id
            WHERE m.batch_id = $1
            ORDER BY m.created_at DESC
        """
        movements = await fetch_all(movements_query, batch_id)
        
        # 4. Calculate total quantity
        total_quantity = sum(Decimal(str(loc['quantity'])) for loc in locations)
        
        return {
            'batch_id': batch['id'],
            'batch_number': batch['batch_number'],
            'is_repacked': batch['is_repacked'],
            'status': batch['status'],
            'item_id': locations[0]['item_id'] if locations else None,
            'item_name': locations[0]['item_name'] if locations else None,
            'total_quantity': total_quantity,
            'locations': locations,
            'movements': movements
        }
        
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get batch inventory: {e}")
        raise


async def check_stock_availability(
    item_id: int,
    quantity: Decimal,
    location: Optional[str] = None,
    grade: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check real-time stock availability for an item.
    
    Args:
        item_id: Item ID
        quantity: Required quantity
        location: Optional location filter
        grade: Optional grade filter
        
    Returns:
        Availability status with stock breakdown
    """
    try:
        # 1. Get item info
        item_query = "SELECT id, name, sku FROM zoho_items WHERE id = $1"
        item = await fetch_one(item_query, item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        # 2. Build query for available stock
        conditions = ["i.item_id = $1", "i.status = 'available'"]
        params = [item_id]
        param_count = 2
        
        if location:
            conditions.append(f"i.location = ${param_count}")
            params.append(location)
            param_count += 1
        
        if grade:
            conditions.append(f"i.grade = ${param_count}")
            params.append(grade)
            param_count += 1
        
        # 3. Get available stock by location
        stock_query = f"""
            SELECT
                i.location,
                SUM(i.quantity) as quantity
            FROM inventory i
            WHERE {' AND '.join(conditions)}
            GROUP BY i.location
        """
        stock_by_location = await fetch_all(stock_query, *params)
        
        # 4. Get allocated stock
        allocated_query = f"""
            SELECT COALESCE(SUM(i.quantity), 0) as allocated
            FROM inventory i
            WHERE i.item_id = $1 AND i.status = 'allocated'
        """
        allocated_result = await fetch_one(allocated_query, item_id)
        allocated_stock = Decimal(str(allocated_result['allocated'])) if allocated_result else Decimal('0')
        
        # 5. Calculate totals
        current_stock = sum(Decimal(str(s['quantity'])) for s in stock_by_location)
        net_available = current_stock
        shortage = max(Decimal('0'), quantity - net_available)
        available = net_available >= quantity
        
        # 6. Build locations dict
        locations = {s['location']: float(s['quantity']) for s in stock_by_location}
        
        logger.info(
            f"Stock check for {item['name']}: Requested={quantity}, "
            f"Available={net_available}, Sufficient={available}"
        )
        
        return {
            'item_id': item_id,
            'item_name': item['name'],
            'requested_quantity': float(quantity),
            'available': available,
            'current_stock': float(current_stock),
            'allocated_stock': float(allocated_stock),
            'net_available': float(net_available),
            'shortage': float(shortage),
            'locations': locations
        }
        
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to check stock availability: {e}")
        raise


# ============================================================================
# STOCK MOVEMENTS
# ============================================================================

async def record_stock_movement(
    movement: InventoryMovementCreate,
    user_id: str
) -> Dict[str, Any]:
    """
    Record stock movement (internal use by other modules).
    
    Args:
        movement: Movement details
        user_id: User UUID
        
    Returns:
        Created movement record
    """
    try:
        async with DatabaseTransaction() as conn:
            # Insert movement
            insert_query = """
                INSERT INTO inventory_movements (
                    item_id, batch_id, movement_type, quantity,
                    from_location, to_location, reference_type,
                    reference_id, notes, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id, created_at
            """
            result = await conn.fetchrow(
                insert_query,
                movement.item_id,
                movement.batch_id,
                movement.movement_type,
                movement.quantity,
                movement.from_location,
                movement.to_location,
                movement.reference_type,
                movement.reference_id,
                movement.notes,
                user_id
            )
            
            logger.info(
                f"✅ Recorded movement: {movement.movement_type} - "
                f"{movement.quantity} units (Batch: {movement.batch_id})"
            )
            
            return {
                'id': result['id'],
                **movement.model_dump(),
                'created_by': user_id,
                'created_at': result['created_at']
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to record stock movement: {e}")
        raise


async def transfer_location(
    request: LocationTransferRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Transfer stock between locations.
    
    Args:
        request: Transfer request
        user_id: User UUID
        
    Returns:
        Updated inventory and movement record
        
    Raises:
        ValueError: If validation fails or insufficient stock
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Find inventory record at from_location
            inventory_query = """
                SELECT i.id, i.item_id, i.batch_id, i.quantity,
                       item.name as item_name, b.batch_number
                FROM inventory i
                JOIN zoho_items item ON i.item_id = item.id
                JOIN batches b ON i.batch_id = b.id
                WHERE i.batch_id = $1
                  AND i.location = $2
                  AND i.status = 'available'
            """
            inventory = await conn.fetchrow(
                inventory_query,
                request.batch_id,
                request.from_location
            )
            
            if not inventory:
                raise ValueError(
                    f"No available stock found for batch {request.batch_id} "
                    f"at {request.from_location}"
                )
            
            if Decimal(str(inventory['quantity'])) < request.quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {inventory['quantity']}, "
                    f"Requested: {request.quantity}"
                )
            
            # 2. Check if inventory exists at to_location for this batch
            to_inventory_query = """
                SELECT id, quantity
                FROM inventory
                WHERE batch_id = $1 AND location = $2 AND item_id = $3
            """
            to_inventory = await conn.fetchrow(
                to_inventory_query,
                request.batch_id,
                request.to_location,
                inventory['item_id']
            )
            
            if to_inventory:
                # Update existing inventory at to_location
                await conn.execute("""
                    UPDATE inventory
                    SET quantity = quantity + $1, updated_at = NOW()
                    WHERE id = $2
                """, request.quantity, to_inventory['id'])
            else:
                # Create new inventory record at to_location
                await conn.execute("""
                    INSERT INTO inventory (
                        item_id, batch_id, location, quantity, status, created_by
                    )
                    VALUES ($1, $2, $3, $4, 'available', $5)
                """, inventory['item_id'], request.batch_id, request.to_location,
                    request.quantity, user_id)
            
            # 3. Reduce quantity at from_location
            new_from_quantity = Decimal(str(inventory['quantity'])) - request.quantity
            if new_from_quantity == 0:
                # Delete if quantity reaches zero
                await conn.execute(
                    "DELETE FROM inventory WHERE id = $1",
                    inventory['id']
                )
            else:
                await conn.execute("""
                    UPDATE inventory
                    SET quantity = $1, updated_at = NOW()
                    WHERE id = $2
                """, new_from_quantity, inventory['id'])
            
            # 4. Log movement
            await conn.execute("""
                INSERT INTO inventory_movements (
                    item_id, batch_id, movement_type, quantity,
                    from_location, to_location, notes, created_by
                )
                VALUES ($1, $2, 'location_transfer', $3, $4, $5, $6, $7)
            """, inventory['item_id'], request.batch_id, request.quantity,
                request.from_location, request.to_location,
                request.notes, user_id)
            
            logger.info(
                f"✅ Transferred {request.quantity} units of "
                f"{inventory['item_name']} (Batch: {inventory['batch_number']}) "
                f"from {request.from_location} to {request.to_location}"
            )
            
            return {
                'success': True,
                'message': 'Stock transferred successfully',
                'item_name': inventory['item_name'],
                'batch_number': inventory['batch_number'],
                'quantity': float(request.quantity),
                'from_location': request.from_location,
                'to_location': request.to_location
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in location transfer: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to transfer location: {e}")
        raise


# ============================================================================
# INVENTORY ADJUSTMENTS
# ============================================================================

async def create_adjustment(
    request: InventoryAdjustmentRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Create stock adjustment request (requires approval).
    
    Args:
        request: Adjustment request
        user_id: User UUID
        
    Returns:
        Created adjustment record
    """
    try:
        # Validate item exists
        item_query = "SELECT id, name FROM zoho_items WHERE id = $1"
        item = await fetch_one(item_query, request.item_id)
        if not item:
            raise ValueError(f"Item {request.item_id} not found")
        
        # Validate batch if provided
        batch_number = None
        if request.batch_id:
            batch_query = "SELECT batch_number FROM batches WHERE id = $1"
            batch = await fetch_one(batch_query, request.batch_id)
            if not batch:
                raise ValueError(f"Batch {request.batch_id} not found")
            batch_number = batch['batch_number']
        
        # Insert adjustment
        insert_query = """
            INSERT INTO inventory_adjustments (
                item_id, batch_id, location, adjustment_type, quantity,
                reason, photo_urls, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, approval_status, created_at, updated_at
        """
        result = await execute_query(
            insert_query,
            request.item_id,
            request.batch_id,
            request.location,
            request.adjustment_type,
            request.quantity,
            request.reason,
            request.photo_urls,
            user_id
        )
        
        logger.info(
            f"✅ Created adjustment request: {request.adjustment_type} "
            f"{request.quantity} units of {item['name']} at {request.location}"
        )
        
        return {
            'id': result['id'],
            'item_id': request.item_id,
            'item_name': item['name'],
            'batch_id': request.batch_id,
            'batch_number': batch_number,
            'location': request.location,
            'adjustment_type': request.adjustment_type,
            'quantity': request.quantity,
            'reason': request.reason,
            'photo_urls': request.photo_urls,
            'approval_status': result['approval_status'],
            'created_at': result['created_at'],
            'updated_at': result['updated_at']
        }
        
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in adjustment creation: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create adjustment: {e}")
        raise


async def approve_adjustment(
    adjustment_id: int,
    approval: InventoryAdjustmentApproval,
    user_id: str
) -> Dict[str, Any]:
    """
    Approve or reject adjustment request (admin only).
    
    Args:
        adjustment_id: Adjustment ID
        approval: Approval decision
        user_id: Admin user UUID
        
    Returns:
        Updated adjustment record
        
    Raises:
        ValueError: If adjustment not found or already processed
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Get adjustment
            adj_query = """
                SELECT id, approval_status, item_id, batch_id, location,
                       adjustment_type, quantity
                FROM inventory_adjustments
                WHERE id = $1
            """
            adj = await conn.fetchrow(adj_query, adjustment_id)
            
            if not adj:
                raise ValueError(f"Adjustment {adjustment_id} not found")
            
            if adj['approval_status'] != 'pending_approval':
                raise ValueError(
                    f"Adjustment already processed (status: {adj['approval_status']})"
                )
            
            # 2. Update approval status
            new_status = 'approved' if approval.approved else 'rejected'
            update_query = """
                UPDATE inventory_adjustments
                SET approval_status = $1,
                    approved_by = $2,
                    approved_at = NOW(),
                    rejection_reason = $3
                WHERE id = $4
                RETURNING updated_at
            """
            result = await conn.fetchrow(
                update_query,
                new_status,
                user_id,
                approval.rejection_reason,
                adjustment_id
            )
            
            logger.info(f"✅ Adjustment {adjustment_id} {new_status}")
            
            # 3. If approved, apply the adjustment immediately
            if approval.approved:
                await _apply_adjustment_internal(conn, adj, user_id)
            
            return {
                'id': adjustment_id,
                'approval_status': new_status,
                'approved_by': user_id,
                'approved_at': result['updated_at'],
                'rejection_reason': approval.rejection_reason
            }
            
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in adjustment approval: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to approve adjustment: {e}")
        raise


async def _apply_adjustment_internal(
    conn: asyncpg.Connection,
    adj: Dict[str, Any],
    user_id: str
):
    """
    Internal helper to apply approved adjustment within transaction.
    
    Args:
        conn: Database connection
        adj: Adjustment record
        user_id: User UUID
    """
    # Find inventory record
    if adj['batch_id']:
        inventory_query = """
            SELECT id, quantity
            FROM inventory
            WHERE item_id = $1 AND batch_id = $2 AND location = $3
        """
        inventory = await conn.fetchrow(
            inventory_query,
            adj['item_id'],
            adj['batch_id'],
            adj['location']
        )
    else:
        # Item-level adjustment (no specific batch)
        inventory_query = """
            SELECT id, quantity
            FROM inventory
            WHERE item_id = $1 AND location = $2
            ORDER BY created_at ASC
            LIMIT 1
        """
        inventory = await conn.fetchrow(inventory_query, adj['item_id'], adj['location'])
    
    if adj['adjustment_type'] == 'increase':
        if inventory:
            # Update existing
            await conn.execute("""
                UPDATE inventory
                SET quantity = quantity + $1, updated_at = NOW()
                WHERE id = $2
            """, adj['quantity'], inventory['id'])
        else:
            # Create new inventory record
            await conn.execute("""
                INSERT INTO inventory (
                    item_id, batch_id, location, quantity, status, created_by
                )
                VALUES ($1, $2, $3, $4, 'available', $5)
            """, adj['item_id'], adj['batch_id'], adj['location'],
                adj['quantity'], user_id)
    
    elif adj['adjustment_type'] in ['decrease', 'correction']:
        if not inventory:
            raise ValueError(f"No inventory found to decrease at {adj['location']}")
        
        new_quantity = Decimal(str(inventory['quantity'])) - Decimal(str(adj['quantity']))
        if new_quantity < 0:
            raise ValueError(
                f"Adjustment would result in negative stock "
                f"(current: {inventory['quantity']}, decrease: {adj['quantity']})"
            )
        
        if new_quantity == 0:
            await conn.execute("DELETE FROM inventory WHERE id = $1", inventory['id'])
        else:
            await conn.execute("""
                UPDATE inventory
                SET quantity = $1, updated_at = NOW()
                WHERE id = $2
            """, new_quantity, inventory['id'])
    
    # Log movement
    movement_type = 'adjustment'
    await conn.execute("""
        INSERT INTO inventory_movements (
            item_id, batch_id, movement_type, quantity,
            to_location, reference_type, reference_id,
            notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, 'adjustment', $6, 'Adjustment applied', $7)
    """, adj['item_id'], adj['batch_id'], movement_type, adj['quantity'],
        adj['location'], adj['id'], user_id)
    
    # Mark as applied
    await conn.execute("""
        UPDATE inventory_adjustments
        SET approval_status = 'applied'
        WHERE id = $1
    """, adj['id'])
    
    logger.info(f"✅ Applied adjustment {adj['id']}: {adj['adjustment_type']} {adj['quantity']} units")


async def get_adjustments_list(
    approval_status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List inventory adjustments with filtering.
    
    Args:
        approval_status: Filter by status
        page: Page number
        limit: Items per page
        
    Returns:
        Paginated adjustments list
    """
    try:
        # Build WHERE clause
        where_clause = f"WHERE approval_status = '{approval_status}'" if approval_status else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM inventory_adjustments {where_clause}"
        count_result = await fetch_one(count_query)
        total = count_result['total'] if count_result else 0
        
        # Get paginated results
        offset = (page - 1) * limit
        list_query = f"""
            SELECT
                a.id, a.item_id, a.batch_id, a.location, a.adjustment_type,
                a.quantity, a.reason, a.photo_urls, a.approval_status,
                a.approved_at, a.rejection_reason, a.created_at, a.updated_at,
                item.name as item_name,
                b.batch_number,
                creator.email as created_by,
                approver.email as approved_by
            FROM inventory_adjustments a
            JOIN zoho_items item ON a.item_id = item.id
            LEFT JOIN batches b ON a.batch_id = b.id
            LEFT JOIN auth.users creator ON a.created_by = creator.id
            LEFT JOIN auth.users approver ON a.approved_by = approver.id
            {where_clause}
            ORDER BY a.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        items = await fetch_all(list_query)
        
        import math
        pages = math.ceil(total / limit) if total > 0 else 1
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': pages
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list adjustments: {e}")
        raise


# ============================================================================
# REORDER LEVELS
# ============================================================================

async def configure_reorder_level(
    request: ReorderLevelConfig,
    user_id: str
) -> Dict[str, Any]:
    """
    Configure reorder level for item and location.
    
    Args:
        request: Reorder level configuration
        user_id: User UUID
        
    Returns:
        Created/updated reorder level config
    """
    try:
        # Validate item exists
        item_query = "SELECT id, name FROM zoho_items WHERE id = $1"
        item = await fetch_one(item_query, request.item_id)
        if not item:
            raise ValueError(f"Item {request.item_id} not found")
        
        # Upsert reorder level
        upsert_query = """
            INSERT INTO reorder_levels (
                item_id, location, reorder_quantity, alert_threshold,
                is_active, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (item_id, location)
            DO UPDATE SET
                reorder_quantity = EXCLUDED.reorder_quantity,
                alert_threshold = EXCLUDED.alert_threshold,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id, created_at, updated_at
        """
        result = await execute_query(
            upsert_query,
            request.item_id,
            request.location,
            request.reorder_quantity,
            request.alert_threshold,
            request.is_active,
            user_id
        )
        
        logger.info(
            f"✅ Configured reorder level for {item['name']} at {request.location}: "
            f"Reorder={request.reorder_quantity}, Alert={request.alert_threshold}"
        )
        
        return {
            'id': result['id'],
            'item_id': request.item_id,
            'item_name': item['name'],
            'location': request.location,
            'reorder_quantity': request.reorder_quantity,
            'alert_threshold': request.alert_threshold,
            'is_active': request.is_active,
            'created_at': result['created_at'],
            'updated_at': result['updated_at']
        }
        
    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in reorder level config: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to configure reorder level: {e}")
        raise


async def get_low_stock_items() -> List[Dict[str, Any]]:
    """
    Get list of items below reorder threshold.
    
    Returns:
        List of low stock alerts
    """
    try:
        query = """
            SELECT
                rl.item_id,
                item.name as item_name,
                item.sku as item_sku,
                rl.location,
                COALESCE(SUM(i.quantity), 0) as current_stock,
                rl.reorder_quantity,
                rl.alert_threshold,
                (rl.alert_threshold - COALESCE(SUM(i.quantity), 0)) as shortage
            FROM reorder_levels rl
            JOIN zoho_items item ON rl.item_id = item.id
            LEFT JOIN inventory i ON rl.item_id = i.item_id
                AND rl.location = i.location
                AND i.status = 'available'
            WHERE rl.is_active = true
            GROUP BY rl.item_id, item.name, item.sku, rl.location,
                     rl.reorder_quantity, rl.alert_threshold
            HAVING COALESCE(SUM(i.quantity), 0) < rl.alert_threshold
            ORDER BY shortage DESC
        """
        results = await fetch_all(query)
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"❌ Failed to get low stock items: {e}")
        raise


# ============================================================================
# EXPIRING ITEMS
# ============================================================================

async def get_expiring_items(days_threshold: int = 7) -> List[Dict[str, Any]]:
    """
    Get items expiring within specified days.
    
    Args:
        days_threshold: Number of days to look ahead
        
    Returns:
        List of expiring items with urgency levels
    """
    try:
        expiry_date = date.today() + timedelta(days=days_threshold)
        
        query = """
            SELECT
                i.id, i.item_id, i.batch_id, i.location, i.quantity,
                i.grade, i.entry_date, i.expiry_date,
                item.name as item_name,
                b.batch_number,
                (i.expiry_date - CURRENT_DATE) as days_until_expiry,
                CASE
                    WHEN (i.expiry_date - CURRENT_DATE) < 2 THEN 'critical'
                    WHEN (i.expiry_date - CURRENT_DATE) BETWEEN 2 AND 7 THEN 'warning'
                    ELSE 'normal'
                END as urgency
            FROM inventory i
            JOIN zoho_items item ON i.item_id = item.id
            JOIN batches b ON i.batch_id = b.id
            WHERE i.expiry_date IS NOT NULL
              AND i.expiry_date <= $1
              AND i.status = 'available'
            ORDER BY i.expiry_date ASC
        """
        results = await fetch_all(query, expiry_date)
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"❌ Failed to get expiring items: {e}")
        raise


# ============================================================================
# REPORTS
# ============================================================================

async def generate_current_stock_report(
    location: Optional[str] = None,
    item_id: Optional[int] = None,
    status: Optional[str] = None,
    include_zero_stock: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate current stock report.
    
    Args:
        location: Filter by location
        item_id: Filter by item
        status: Filter by status
        include_zero_stock: Include items with zero stock
        
    Returns:
        Current stock report data
    """
    try:
        conditions = []
        params = []
        param_count = 1
        
        if location:
            conditions.append(f"i.location = ${param_count}")
            params.append(location)
            param_count += 1
        
        if item_id:
            conditions.append(f"i.item_id = ${param_count}")
            params.append(item_id)
            param_count += 1
        
        if status:
            conditions.append(f"i.status = ${param_count}")
            params.append(status)
            param_count += 1
        
        if not include_zero_stock:
            conditions.append("i.quantity > 0")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT
                item.id as item_id,
                item.name as item_name,
                item.sku as item_sku,
                i.location,
                i.grade,
                i.status,
                COUNT(DISTINCT i.batch_id) as batch_count,
                SUM(i.quantity) as total_quantity,
                MIN(i.expiry_date) as earliest_expiry,
                MAX(i.entry_date) as latest_entry
            FROM inventory i
            JOIN zoho_items item ON i.item_id = item.id
            {where_clause}
            GROUP BY item.id, item.name, item.sku, i.location, i.grade, i.status
            ORDER BY item.name, i.location
        """
        results = await fetch_all(query, *params)
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"❌ Failed to generate current stock report: {e}")
        raise


async def generate_stock_movement_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    movement_type: Optional[str] = None,
    location: Optional[str] = None,
    item_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate stock movement report.
    
    Args:
        date_from: Start date
        date_to: End date
        movement_type: Filter by movement type
        location: Filter by location (from or to)
        item_id: Filter by item
        
    Returns:
        Stock movement report data
    """
    try:
        conditions = []
        params = []
        param_count = 1
        
        if date_from:
            conditions.append(f"m.created_at >= ${param_count}")
            params.append(date_from)
            param_count += 1
        
        if date_to:
            # Add one day to include entire end date
            end_date = date_to + timedelta(days=1)
            conditions.append(f"m.created_at < ${param_count}")
            params.append(end_date)
            param_count += 1
        
        if movement_type:
            conditions.append(f"m.movement_type = ${param_count}")
            params.append(movement_type)
            param_count += 1
        
        if location:
            conditions.append(f"(m.from_location = ${param_count} OR m.to_location = ${param_count})")
            params.append(location)
            param_count += 1
        
        if item_id:
            conditions.append(f"m.item_id = ${param_count}")
            params.append(item_id)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT
                m.id, m.created_at, m.movement_type, m.quantity,
                m.from_location, m.to_location, m.reference_type, m.notes,
                item.name as item_name,
                b.batch_number,
                u.email as created_by
            FROM inventory_movements m
            JOIN zoho_items item ON m.item_id = item.id
            JOIN batches b ON m.batch_id = b.id
            LEFT JOIN auth.users u ON m.created_by = u.id
            {where_clause}
            ORDER BY m.created_at DESC
        """
        results = await fetch_all(query, *params)
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"❌ Failed to generate stock movement report: {e}")
        raise


async def generate_batch_age_report() -> List[Dict[str, Any]]:
    """
    Generate batch age report showing how long batches have been in inventory.
    
    Returns:
        Batch age report data
    """
    try:
        query = """
            SELECT
                b.id as batch_id,
                b.batch_number,
                item.id as item_id,
                item.name as item_name,
                i.location,
                i.quantity,
                i.entry_date,
                i.status,
                (CURRENT_DATE - i.entry_date::date) as age_days
            FROM inventory i
            JOIN batches b ON i.batch_id = b.id
            JOIN zoho_items item ON i.item_id = item.id
            WHERE i.quantity > 0
            ORDER BY age_days DESC, item.name
        """
        results = await fetch_all(query)
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"❌ Failed to generate batch age report: {e}")
        raise

