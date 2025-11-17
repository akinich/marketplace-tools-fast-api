"""
================================================================================
Farm Management System - Inventory Service Layer
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial inventory service implementation
  - Item master CRUD operations
  - Supplier and category management
  - Batch management and stock operations
  - FIFO stock deduction logic (ported from Streamlit v2.0.0)
  - Purchase order management
  - Transaction history and alerts
  - Dashboard statistics

================================================================================
"""

from typing import Optional, List, Dict
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
import math

from app.database import get_db, fetch_one, fetch_all, execute, DatabaseTransaction
from app.services.auth_service import log_activity
from app.schemas.inventory import *

logger = logging.getLogger(__name__)


# ============================================================================
# ITEM MASTER OPERATIONS
# ============================================================================


async def get_items_list(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """Get paginated list of items"""
    where_conditions = []
    params = []
    param_count = 1

    if category:
        where_conditions.append(f"im.category = ${param_count}")
        params.append(category)
        param_count += 1

    if is_active is not None:
        where_conditions.append(f"im.is_active = ${param_count}")
        params.append(is_active)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM item_master im {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get items
    offset = (page - 1) * limit
    items_query = f"""
        SELECT
            im.id, im.item_name, im.sku, im.category, im.unit,
            im.default_supplier_id, s.supplier_name as default_supplier_name,
            im.reorder_threshold, im.min_stock_level, im.current_qty,
            im.is_active, im.created_at
        FROM item_master im
        LEFT JOIN suppliers s ON s.id = im.default_supplier_id
        {where_clause}
        ORDER BY im.item_name
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    items = await fetch_all(items_query, *params)

    return {"items": items, "total": total, "page": page, "limit": limit}


async def create_item(request: CreateItemRequest, user_id: str) -> Dict:
    """Create new item master"""
    # Check if SKU already exists (if provided)
    if request.sku:
        existing = await fetch_one(
            "SELECT id FROM item_master WHERE sku = $1", request.sku
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item with SKU '{request.sku}' already exists",
            )

    # Insert item
    item_id = await execute(
        """
        INSERT INTO item_master (
            item_name, sku, category, unit, default_supplier_id,
            reorder_threshold, min_stock_level, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """,
        request.item_name,
        request.sku,
        request.category,
        request.unit,
        request.default_supplier_id,
        request.reorder_threshold,
        request.min_stock_level,
        user_id,
    )

    # Fetch created item
    item = await fetch_one(
        """
        SELECT im.*, s.supplier_name as default_supplier_name
        FROM item_master im
        LEFT JOIN suppliers s ON s.id = im.default_supplier_id
        WHERE im.id = $1
        """,
        item_id,
    )

    return item


async def update_item(
    item_id: int, request: UpdateItemRequest, user_id: str
) -> Dict:
    """Update item master"""
    # Check if exists
    existing = await fetch_one("SELECT id FROM item_master WHERE id = $1", item_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # Build update query
    update_fields = []
    params = []
    param_count = 1

    if request.item_name is not None:
        update_fields.append(f"item_name = ${param_count}")
        params.append(request.item_name)
        param_count += 1

    if request.sku is not None:
        update_fields.append(f"sku = ${param_count}")
        params.append(request.sku)
        param_count += 1

    if request.category is not None:
        update_fields.append(f"category = ${param_count}")
        params.append(request.category)
        param_count += 1

    if request.unit is not None:
        update_fields.append(f"unit = ${param_count}")
        params.append(request.unit)
        param_count += 1

    if request.default_supplier_id is not None:
        update_fields.append(f"default_supplier_id = ${param_count}")
        params.append(request.default_supplier_id)
        param_count += 1

    if request.reorder_threshold is not None:
        update_fields.append(f"reorder_threshold = ${param_count}")
        params.append(request.reorder_threshold)
        param_count += 1

    if request.min_stock_level is not None:
        update_fields.append(f"min_stock_level = ${param_count}")
        params.append(request.min_stock_level)
        param_count += 1

    if request.is_active is not None:
        update_fields.append(f"is_active = ${param_count}")
        params.append(request.is_active)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    update_fields.append(f"updated_at = NOW()")
    params.append(item_id)

    query = f"""
        UPDATE item_master
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    await execute(query, *params)

    # Fetch updated item
    item = await fetch_one(
        """
        SELECT im.*, s.supplier_name as default_supplier_name
        FROM item_master im
        LEFT JOIN suppliers s ON s.id = im.default_supplier_id
        WHERE im.id = $1
        """,
        item_id,
    )

    return item


async def delete_item(item_id: int) -> None:
    """Delete item (soft delete)"""
    result = await execute(
        "UPDATE item_master SET is_active = FALSE WHERE id = $1", item_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )


# ============================================================================
# SUPPLIER OPERATIONS
# ============================================================================


async def get_suppliers_list() -> List[Dict]:
    """Get all suppliers"""
    suppliers = await fetch_all(
        """
        SELECT id, supplier_name, contact_person, phone, email, address, is_active, created_at
        FROM suppliers
        WHERE is_active = TRUE
        ORDER BY supplier_name
        """
    )
    return suppliers


async def create_supplier(request: CreateSupplierRequest) -> Dict:
    """Create new supplier"""
    supplier_id = await execute(
        """
        INSERT INTO suppliers (supplier_name, contact_person, phone, email, address)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        request.supplier_name,
        request.contact_person,
        request.phone,
        request.email,
        request.address,
    )

    supplier = await fetch_one("SELECT * FROM suppliers WHERE id = $1", supplier_id)
    return supplier


async def update_supplier(supplier_id: int, request: UpdateSupplierRequest) -> Dict:
    """Update supplier"""
    # Build update query (similar pattern as update_item)
    update_fields = []
    params = []
    param_count = 1

    if request.supplier_name is not None:
        update_fields.append(f"supplier_name = ${param_count}")
        params.append(request.supplier_name)
        param_count += 1

    if request.contact_person is not None:
        update_fields.append(f"contact_person = ${param_count}")
        params.append(request.contact_person)
        param_count += 1

    if request.phone is not None:
        update_fields.append(f"phone = ${param_count}")
        params.append(request.phone)
        param_count += 1

    if request.email is not None:
        update_fields.append(f"email = ${param_count}")
        params.append(request.email)
        param_count += 1

    if request.address is not None:
        update_fields.append(f"address = ${param_count}")
        params.append(request.address)
        param_count += 1

    if request.is_active is not None:
        update_fields.append(f"is_active = ${param_count}")
        params.append(request.is_active)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    update_fields.append(f"updated_at = NOW()")
    params.append(supplier_id)

    query = f"""
        UPDATE suppliers
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    await execute(query, *params)

    supplier = await fetch_one("SELECT * FROM suppliers WHERE id = $1", supplier_id)
    return supplier


# ============================================================================
# CATEGORY OPERATIONS
# ============================================================================


async def get_categories_list() -> List[Dict]:
    """Get all categories"""
    categories = await fetch_all(
        "SELECT id, category_name, description, created_at FROM inventory_categories ORDER BY category_name"
    )
    return categories


# ============================================================================
# STOCK OPERATIONS - ADD STOCK
# ============================================================================


async def add_stock(request: AddStockRequest, user_id: str) -> Dict:
    """Add stock batch"""
    # Verify item exists
    item = await fetch_one("SELECT id, item_name FROM item_master WHERE id = $1", request.item_master_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    async with DatabaseTransaction():
        # Insert batch
        batch_id = await execute(
            """
            INSERT INTO inventory_batches (
                item_master_id, batch_number, quantity_purchased, remaining_qty,
                unit_cost, purchase_date, expiry_date, supplier_id, po_number, notes, added_by
            )
            VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            request.item_master_id,
            request.batch_number,
            request.quantity,
            request.unit_cost,
            request.purchase_date,
            request.expiry_date,
            request.supplier_id,
            request.po_number,
            request.notes,
            user_id,
        )

        # Get new total (trigger updates current_qty automatically)
        item_updated = await fetch_one(
            "SELECT current_qty FROM item_master WHERE id = $1", request.item_master_id
        )
        new_total = item_updated["current_qty"]

        # Log transaction
        await execute(
            """
            INSERT INTO inventory_transactions (
                item_master_id, batch_id, transaction_type, quantity_change,
                new_balance, unit_cost, total_cost, po_number, user_id, notes
            )
            VALUES ($1, $2, 'add', $3, $4, $5, $6, $7, $8, $9)
            """,
            request.item_master_id,
            batch_id,
            request.quantity,
            new_total,
            request.unit_cost,
            request.quantity * request.unit_cost,
            request.po_number,
            user_id,
            request.notes,
        )

    return {
        "success": True,
        "message": f"Added {request.quantity} units successfully",
        "batch_id": batch_id,
        "new_total_qty": new_total,
    }


# ============================================================================
# STOCK OPERATIONS - USE STOCK (FIFO)
# ============================================================================


async def use_stock_fifo(request: UseStockRequest, user_id: str, username: str) -> Dict:
    """
    Deduct stock using FIFO (First-In-First-Out) logic.
    Ported from Streamlit v2.0.0 db_inventory.py::deduct_stock_fifo()
    """
    # Verify item exists
    item = await fetch_one("SELECT id, item_name FROM item_master WHERE id = $1", request.item_master_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # Get available batches (FIFO - oldest first)
    batches = await fetch_all(
        """
        SELECT id, batch_number, remaining_qty, unit_cost
        FROM inventory_batches
        WHERE item_master_id = $1
          AND is_active = TRUE
          AND remaining_qty > 0
        ORDER BY purchase_date ASC, id ASC
        """,
        request.item_master_id,
    )

    if not batches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No stock available for this item",
        )

    # Calculate total available
    total_available = sum(Decimal(str(b["remaining_qty"])) for b in batches)

    if request.quantity > total_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {total_available}, Requested: {request.quantity}",
        )

    # Deduct from batches using FIFO
    remaining_to_deduct = request.quantity
    batches_used = []
    total_cost = Decimal("0")

    async with DatabaseTransaction():
        for batch in batches:
            if remaining_to_deduct <= 0:
                break

            batch_remaining = Decimal(str(batch["remaining_qty"]))
            batch_unit_cost = Decimal(str(batch["unit_cost"]))

            qty_from_batch = min(remaining_to_deduct, batch_remaining)
            cost_from_batch = qty_from_batch * batch_unit_cost

            # Update batch remaining quantity
            new_batch_qty = batch_remaining - qty_from_batch
            await execute(
                "UPDATE inventory_batches SET remaining_qty = $1, updated_at = NOW() WHERE id = $2",
                new_batch_qty,
                batch["id"],
            )

            # Get new item balance (trigger updates current_qty)
            item_updated = await fetch_one(
                "SELECT current_qty FROM item_master WHERE id = $1",
                request.item_master_id,
            )
            new_balance = item_updated["current_qty"]

            # Log transaction
            await execute(
                """
                INSERT INTO inventory_transactions (
                    item_master_id, batch_id, transaction_type, quantity_change,
                    new_balance, unit_cost, total_cost, module_reference, tank_id,
                    user_id, username, notes
                )
                VALUES ($1, $2, 'use', $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                request.item_master_id,
                batch["id"],
                -qty_from_batch,  # Negative for deduction
                new_balance,
                batch_unit_cost,
                cost_from_batch,
                request.module_reference,
                request.tank_id,
                user_id,
                username,
                f"{request.purpose} | {request.notes}" if request.notes else request.purpose,
            )

            batches_used.append(
                {
                    "batch_id": batch["id"],
                    "batch_number": batch.get("batch_number"),
                    "qty_from_batch": qty_from_batch,
                    "unit_cost": batch_unit_cost,
                    "cost": cost_from_batch,
                }
            )

            total_cost += cost_from_batch
            remaining_to_deduct -= qty_from_batch

    # Calculate weighted average cost
    weighted_avg_cost = total_cost / request.quantity if request.quantity > 0 else Decimal("0")

    # Get final balance
    final_item = await fetch_one(
        "SELECT current_qty FROM item_master WHERE id = $1", request.item_master_id
    )
    final_balance = final_item["current_qty"]

    return {
        "success": True,
        "message": f"Successfully used {request.quantity} units",
        "quantity_used": request.quantity,
        "batches_used": batches_used,
        "total_cost": total_cost,
        "weighted_avg_cost": weighted_avg_cost,
        "new_balance": final_balance,
    }


# ============================================================================
# PURCHASE ORDER OPERATIONS
# ============================================================================


async def get_purchase_orders_list(
    status: Optional[str] = None,
    days_back: int = 30,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    Get purchase orders list (OPTIMIZED - from spec requirements).
    Target: <200ms response time
    """
    where_conditions = [f"po.po_date >= CURRENT_DATE - INTERVAL '{days_back} days'"]
    params = []
    param_count = 1

    if status and status != "All":
        where_conditions.append(f"po.status = ${param_count}")
        params.append(status)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}"

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM purchase_orders po {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get POs with single optimized query
    offset = (page - 1) * page_size
    pos_query = f"""
        SELECT
            po.id,
            po.po_number,
            po.supplier_id,
            s.supplier_name,
            po.po_date,
            po.expected_delivery,
            po.status,
            po.total_cost,
            COUNT(poi.id) as items_count,
            po.created_by,
            up.full_name as created_by_name,
            po.created_at
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        LEFT JOIN user_profiles up ON up.id = po.created_by
        LEFT JOIN purchase_order_items poi ON poi.purchase_order_id = po.id
        {where_clause}
        GROUP BY po.id, s.supplier_name, up.full_name
        ORDER BY po.po_date DESC, po.id DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([page_size, offset])
    pos = await fetch_all(pos_query, *params)

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "pos": pos,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def create_purchase_order(request: CreatePORequest, user_id: str) -> Dict:
    """Create purchase order with multiple items"""
    # Check if PO number exists
    existing = await fetch_one(
        "SELECT id FROM purchase_orders WHERE po_number = $1", request.po_number
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PO number '{request.po_number}' already exists",
        )

    # Verify supplier exists
    supplier = await fetch_one(
        "SELECT id FROM suppliers WHERE id = $1", request.supplier_id
    )
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )

    async with DatabaseTransaction():
        # Create PO (total_cost will be auto-calculated by trigger)
        po_id = await execute(
            """
            INSERT INTO purchase_orders (
                po_number, supplier_id, po_date, expected_delivery, notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            request.po_number,
            request.supplier_id,
            request.po_date,
            request.expected_delivery,
            request.notes,
            user_id,
        )

        # Insert PO items
        for item in request.items:
            await execute(
                """
                INSERT INTO purchase_order_items (
                    purchase_order_id, item_master_id, ordered_qty, unit_cost
                )
                VALUES ($1, $2, $3, $4)
                """,
                po_id,
                item.item_master_id,
                item.ordered_qty,
                item.unit_cost,
            )

    # Fetch created PO
    po = await fetch_one(
        """
        SELECT
            po.*,
            s.supplier_name,
            up.full_name as created_by_name,
            (SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = po.id) as items_count
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        LEFT JOIN user_profiles up ON up.id = po.created_by
        WHERE po.id = $1
        """,
        po_id,
    )

    return po


async def update_purchase_order_status(po_id: int, request: UpdatePORequest) -> Dict:
    """Update purchase order"""
    # Build update
    update_fields = []
    params = []
    param_count = 1

    if request.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(request.status)
        param_count += 1

    if request.expected_delivery is not None:
        update_fields.append(f"expected_delivery = ${param_count}")
        params.append(request.expected_delivery)
        param_count += 1

    if request.notes is not None:
        update_fields.append(f"notes = ${param_count}")
        params.append(request.notes)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    update_fields.append(f"updated_at = NOW()")
    params.append(po_id)

    query = f"""
        UPDATE purchase_orders
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    result = await execute(query, *params)

    # Fetch updated PO
    po = await fetch_one(
        """
        SELECT po.*, s.supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.id = $1
        """,
        po_id,
    )

    return po


# ============================================================================
# ALERTS
# ============================================================================


async def get_low_stock_alerts() -> List[Dict]:
    """Get items with low stock"""
    items = await fetch_all(
        """
        SELECT
            im.id,
            im.item_name,
            im.category,
            im.unit,
            im.current_qty,
            im.reorder_threshold,
            (im.reorder_threshold - im.current_qty) as deficit,
            s.supplier_name as default_supplier_name
        FROM item_master im
        LEFT JOIN suppliers s ON s.id = im.default_supplier_id
        WHERE im.is_active = TRUE
          AND im.current_qty <= im.reorder_threshold
        ORDER BY deficit DESC
        """
    )
    return items


async def get_expiry_alerts(days: int = 30) -> List[Dict]:
    """Get items expiring soon"""
    items = await fetch_all(
        """
        SELECT
            ib.id as batch_id,
            ib.item_master_id as item_id,
            im.item_name,
            ib.batch_number,
            ib.remaining_qty,
            im.unit,
            ib.expiry_date,
            (ib.expiry_date - CURRENT_DATE) as days_until_expiry,
            s.supplier_name
        FROM inventory_batches ib
        JOIN item_master im ON im.id = ib.item_master_id
        LEFT JOIN suppliers s ON s.id = ib.supplier_id
        WHERE ib.is_active = TRUE
          AND ib.remaining_qty > 0
          AND ib.expiry_date IS NOT NULL
          AND ib.expiry_date <= CURRENT_DATE + $1::interval
        ORDER BY ib.expiry_date
        """,
        f"{days} days",
    )
    return items


# ============================================================================
# TRANSACTIONS
# ============================================================================


async def get_transactions_list(
    item_id: Optional[int] = None,
    days_back: int = 30,
    page: int = 1,
    limit: int = 100,
) -> Dict:
    """Get transaction history"""
    where_conditions = [f"it.transaction_date >= NOW() - INTERVAL '{days_back} days'"]
    params = []
    param_count = 1

    if item_id:
        where_conditions.append(f"it.item_master_id = ${param_count}")
        params.append(item_id)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}"

    # Count
    count_query = f"SELECT COUNT(*) as total FROM inventory_transactions it {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get transactions
    offset = (page - 1) * limit
    transactions_query = f"""
        SELECT
            it.*,
            im.item_name,
            ib.batch_number
        FROM inventory_transactions it
        JOIN item_master im ON im.id = it.item_master_id
        LEFT JOIN inventory_batches ib ON ib.id = it.batch_id
        {where_clause}
        ORDER BY it.transaction_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    transactions = await fetch_all(transactions_query, *params)

    return {"transactions": transactions, "total": total, "page": page, "limit": limit}


# ============================================================================
# DASHBOARD
# ============================================================================


async def get_inventory_dashboard() -> Dict:
    """Get inventory dashboard statistics"""
    # Total items
    total_items_result = await fetch_one("SELECT COUNT(*) as count FROM item_master")
    total_items = total_items_result["count"] if total_items_result else 0

    # Active items
    active_items_result = await fetch_one(
        "SELECT COUNT(*) as count FROM item_master WHERE is_active = TRUE"
    )
    active_items = active_items_result["count"] if active_items_result else 0

    # Total stock value
    stock_value_result = await fetch_one(
        """
        SELECT COALESCE(SUM(remaining_qty * unit_cost), 0) as total
        FROM inventory_batches
        WHERE is_active = TRUE AND remaining_qty > 0
        """
    )
    total_stock_value = stock_value_result["total"] if stock_value_result else 0

    # Low stock items
    low_stock_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM item_master
        WHERE is_active = TRUE AND current_qty <= reorder_threshold
        """
    )
    low_stock_items = low_stock_result["count"] if low_stock_result else 0

    # Expiring soon
    expiring_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM inventory_batches
        WHERE is_active = TRUE
          AND remaining_qty > 0
          AND expiry_date IS NOT NULL
          AND expiry_date <= CURRENT_DATE + INTERVAL '30 days'
        """
    )
    expiring_soon_items = expiring_result["count"] if expiring_result else 0

    # Pending POs
    pending_pos_result = await fetch_one(
        "SELECT COUNT(*) as count FROM purchase_orders WHERE status = 'pending'"
    )
    pending_pos = pending_pos_result["count"] if pending_pos_result else 0

    # Recent transactions
    recent_tx_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM inventory_transactions
        WHERE transaction_date >= NOW() - INTERVAL '7 days'
        """
    )
    recent_transactions_count = recent_tx_result["count"] if recent_tx_result else 0

    return {
        "total_items": total_items,
        "active_items": active_items,
        "total_stock_value": total_stock_value,
        "low_stock_items": low_stock_items,
        "expiring_soon_items": expiring_soon_items,
        "pending_pos": pending_pos,
        "recent_transactions_count": recent_transactions_count,
    }
