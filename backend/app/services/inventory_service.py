"""
================================================================================
Farm Management System - Inventory Service Layer
================================================================================
Version: 1.8.4
Last Updated: 2025-11-21

Changelog:
----------
v1.8.4 (2025-11-21):
  - BUGFIX: Explicit CAST to INTEGER for has_transactions to ensure proper type serialization

v1.8.3 (2025-11-21):
  - BUGFIX: has_transactions now returns integer count instead of boolean for reliable cross-stack handling

v1.8.2 (2025-11-21):
  - BUGFIX: Use CASE WHEN EXISTS for more reliable boolean return in has_transactions

v1.8.1 (2025-11-21):
  - BUGFIX: has_transactions now also checks purchase_order_items table
  - BUGFIX: hard_delete_item() now checks both inventory_transactions and purchase_order_items
  - Better error messages showing specific reasons (transactions and/or purchase orders)

v1.8.0 (2025-11-21):
  - Added has_transactions flag to get_items_list() response
  - Added transaction check in hard_delete_item() - prevents deletion of items with transaction history
  - Returns proper error message instead of 500 error for FK constraint violation

v1.7.0 (2025-11-21):
  - Added hard_delete_item() for permanent deletion of inactive items
  - Only inactive items can be permanently deleted (is_active = FALSE)
  - Cascades delete to related records (batches, transactions, mappings)

v1.6.0 (2025-11-21):
  - Added default_price field support in item master operations
  - BREAKING: Removed auto-create category logic - categories must exist before creating items
  - Added category validation in create_item (must exist in inventory_categories)
  - Updated delete_item to check stock before deactivation (prevents deletion if current_qty > 0)
  - Updated get_items_list to include default_price in SELECT
  - Updated create_item and update_item to handle default_price field

v1.5.2 (2025-11-20):
  - CRITICAL FIX: Cast tank_id to text in get_transactions_list query
  - Fixes ResponseValidationError when returning transactions with UUID tank_id
  - Aligns with database schema change (tank_id column changed to UUID)

v1.5.1 (2025-11-19):
  - CRITICAL FIX: Convert tank_id string to UUID in batch_deduct_stock INSERT
  - Fixes "invalid input for query argument $8" asyncpg error
  - Fixes "Inventory deduction failed" in biofloc feeding module

v1.5.0 (2025-11-19):
  - CRITICAL FIX: Cast UUID fields to text in purchase orders query
  - CRITICAL FIX: Cast UUID fields to text in transactions query
  - CRITICAL FIX: batch_deduct_stock now searches by SKU OR item_name
  - Added transaction_type filter parameter to get_transactions_list()
  - Made category filtering case-insensitive in get_items_list()
  - Fixes ResponseValidationError in purchase orders and transactions endpoints
  - Fixes "Inventory deduction failed" error when items have no SKU

v1.4.0 (2025-11-18):
  - Added batch_deduct_stock() for atomic multi-item deduction
  - Added bulk_fetch_items() for fetching multiple items efficiently
  - Added reservation system: create_reservation(), get_reservations_list(),
    cancel_reservation(), confirm_reservation()
  - Enhanced cross-module integration for biofloc and other modules

v1.3.1 (2025-11-18):
  - CRITICAL FIX: Categories API now returns consistent field names
  - Changed category_name to 'category' alias in all category endpoints
  - Added item_count to all category responses (GET, POST, PUT)
  - Frontend Categories page now fully functional with correct field mapping

v1.3.0 (2025-11-18):
  - CRITICAL FIX: Auto-create categories when creating items
  - Fixed foreign key violation when creating items with new categories
  - Categories are now automatically created if they don't exist
  - Added ON CONFLICT DO NOTHING to prevent duplicate category errors

v1.2.0 (2025-11-18):
  - Added delete_supplier() function for soft delete
  - Added create_category(), update_category(), delete_category() functions
  - Added create_stock_adjustment(), get_stock_adjustments_list() functions
  - Enhanced category and stock adjustment management

v1.1.0 (2025-11-17):
  - CRITICAL: Fixed transaction blocks to use transaction-aware helper functions
  - Updated add_stock() to properly use DatabaseTransaction with conn parameter
  - Updated use_stock_fifo() to properly use DatabaseTransaction with conn parameter
  - Updated create_purchase_order() to properly use DatabaseTransaction with conn parameter
  - Ensured all operations within transactions use same connection for atomicity
  - Imported transaction-aware functions (fetch_one_tx, fetch_all_tx, execute_query_tx)

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
import asyncio

from app.database import (
    get_db, fetch_one, fetch_all, execute_query, DatabaseTransaction,
    fetch_one_tx, fetch_all_tx, execute_query_tx
)
from app.services.auth_service import log_activity
from app.services import telegram_service
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
        where_conditions.append(f"LOWER(im.category) = LOWER(${param_count})")
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
            im.default_price, im.reorder_threshold, im.min_stock_level,
            im.current_qty, im.is_active, im.created_at,
            CAST((
                (SELECT COUNT(*) FROM inventory_transactions it WHERE it.item_master_id = im.id) +
                (SELECT COUNT(*) FROM purchase_order_items poi WHERE poi.item_master_id = im.id)
            ) AS INTEGER) as has_transactions
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

    # Validate category exists (required - no auto-creation)
    if request.category:
        category_exists = await fetch_one(
            "SELECT id FROM inventory_categories WHERE category_name = $1",
            request.category
        )
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{request.category}' does not exist. Please create the category first in the Categories sub-module.",
            )

    # Insert item
    item_id = await execute_query(
        """
        INSERT INTO item_master (
            item_name, sku, category, unit, default_supplier_id,
            default_price, reorder_threshold, min_stock_level, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """,
        request.item_name,
        request.sku,
        request.category,
        request.unit,
        request.default_supplier_id,
        request.default_price,
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

    if request.default_price is not None:
        update_fields.append(f"default_price = ${param_count}")
        params.append(request.default_price)
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
    await execute_query(query, *params)

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
    """Delete item (soft delete) - Only if no stock exists"""
    # Check if item exists and get current stock
    item = await fetch_one(
        "SELECT id, item_name, current_qty FROM item_master WHERE id = $1",
        item_id
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Prevent deletion if stock exists
    if item["current_qty"] and item["current_qty"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete item '{item['item_name']}' because it has stock (current quantity: {item['current_qty']}). Please use all stock before deleting.",
        )

    # Soft delete (set is_active to FALSE)
    await execute_query(
        "UPDATE item_master SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
        item_id
    )


async def hard_delete_item(item_id: int) -> None:
    """Permanently delete item (hard delete) - Only for inactive items"""
    # Check if item exists and is inactive
    item = await fetch_one(
        "SELECT id, item_name, is_active, current_qty FROM item_master WHERE id = $1",
        item_id
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Only allow hard delete for inactive items
    if item["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot permanently delete active item '{item['item_name']}'. Please deactivate the item first.",
        )

    # Check if item has any stock (extra safety check)
    if item["current_qty"] and item["current_qty"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot permanently delete item '{item['item_name']}' because it still has stock ({item['current_qty']}). Please clear all stock first.",
        )

    # Check if item has any inventory transactions or purchase order items
    transaction_count = await fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM inventory_transactions WHERE item_master_id = $1) as inv_count,
            (SELECT COUNT(*) FROM purchase_order_items WHERE item_master_id = $1) as po_count
        """,
        item_id
    )
    inv_count = transaction_count["inv_count"] if transaction_count else 0
    po_count = transaction_count["po_count"] if transaction_count else 0

    if inv_count > 0 or po_count > 0:
        reasons = []
        if inv_count > 0:
            reasons.append(f"{inv_count} inventory transaction(s)")
        if po_count > 0:
            reasons.append(f"{po_count} purchase order(s)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot permanently delete item '{item['item_name']}' because it has {' and '.join(reasons)}. Items with history cannot be permanently deleted - they can only be deactivated.",
        )

    # Hard delete - remove from database
    # Note: Due to CASCADE constraints, this will also delete related batches
    await execute_query(
        "DELETE FROM item_master WHERE id = $1",
        item_id
    )
    logger.info(f"Permanently deleted item {item_id}: {item['item_name']}")


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
    supplier_id = await execute_query(
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
    await execute_query(query, *params)

    supplier = await fetch_one("SELECT * FROM suppliers WHERE id = $1", supplier_id)
    return supplier


async def delete_supplier(supplier_id: int) -> None:
    """Delete supplier (soft delete)"""
    result = await execute_query(
        "UPDATE suppliers SET is_active = FALSE WHERE id = $1", supplier_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )


# ============================================================================
# CATEGORY OPERATIONS
# ============================================================================


async def get_categories_list() -> List[Dict]:
    """Get all categories with item counts"""
    categories = await fetch_all(
        """
        SELECT
            ic.id,
            ic.category_name as category,
            ic.description,
            ic.created_at,
            COUNT(im.id) as item_count
        FROM inventory_categories ic
        LEFT JOIN item_master im ON im.category = ic.category_name
        GROUP BY ic.id, ic.category_name, ic.description, ic.created_at
        ORDER BY ic.category_name
        """
    )
    return categories


async def create_category(request: CreateCategoryRequest) -> Dict:
    """Create new category"""
    # Check if category already exists
    existing = await fetch_one(
        "SELECT id FROM inventory_categories WHERE category_name = $1",
        request.category_name,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{request.category_name}' already exists",
        )

    category_id = await execute_query(
        """
        INSERT INTO inventory_categories (category_name, description)
        VALUES ($1, $2)
        RETURNING id
        """,
        request.category_name,
        request.description,
    )

    category = await fetch_one(
        """
        SELECT
            ic.id,
            ic.category_name as category,
            ic.description,
            ic.created_at,
            COUNT(im.id) as item_count
        FROM inventory_categories ic
        LEFT JOIN item_master im ON im.category = ic.category_name
        WHERE ic.id = $1
        GROUP BY ic.id, ic.category_name, ic.description, ic.created_at
        """,
        category_id
    )
    return category


async def update_category(category_id: int, request: UpdateCategoryRequest) -> Dict:
    """Update category"""
    # Check if exists
    existing = await fetch_one(
        "SELECT id FROM inventory_categories WHERE id = $1", category_id
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Build update query
    update_fields = []
    params = []
    param_count = 1

    if request.category_name is not None:
        # Check if new name already exists
        name_exists = await fetch_one(
            "SELECT id FROM inventory_categories WHERE category_name = $1 AND id != $2",
            request.category_name,
            category_id,
        )
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{request.category_name}' already exists",
            )
        update_fields.append(f"category_name = ${param_count}")
        params.append(request.category_name)
        param_count += 1

    if request.description is not None:
        update_fields.append(f"description = ${param_count}")
        params.append(request.description)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    params.append(category_id)

    query = f"""
        UPDATE inventory_categories
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    await execute_query(query, *params)

    category = await fetch_one(
        """
        SELECT
            ic.id,
            ic.category_name as category,
            ic.description,
            ic.created_at,
            COUNT(im.id) as item_count
        FROM inventory_categories ic
        LEFT JOIN item_master im ON im.category = ic.category_name
        WHERE ic.id = $1
        GROUP BY ic.id, ic.category_name, ic.description, ic.created_at
        """,
        category_id
    )
    return category


async def delete_category(category_id: int) -> None:
    """Delete category"""
    # Check if category is in use
    items_using = await fetch_one(
        "SELECT COUNT(*) as count FROM item_master WHERE category = (SELECT category_name FROM inventory_categories WHERE id = $1)",
        category_id,
    )
    if items_using and items_using["count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {items_using['count']} items are using it",
        )

    result = await execute_query(
        "DELETE FROM inventory_categories WHERE id = $1", category_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )


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

    async with DatabaseTransaction() as conn:
        # Insert batch
        batch_id = await execute_query_tx(
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
            conn=conn,
        )

        # Get new total (trigger updates current_qty automatically)
        item_updated = await fetch_one_tx(
            "SELECT current_qty FROM item_master WHERE id = $1",
            request.item_master_id,
            conn=conn
        )
        new_total = item_updated["current_qty"]

        # Log transaction
        await execute_query_tx(
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
            conn=conn,
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

    async with DatabaseTransaction() as conn:
        for batch in batches:
            if remaining_to_deduct <= 0:
                break

            batch_remaining = Decimal(str(batch["remaining_qty"]))
            batch_unit_cost = Decimal(str(batch["unit_cost"]))

            qty_from_batch = min(remaining_to_deduct, batch_remaining)
            cost_from_batch = qty_from_batch * batch_unit_cost

            # Update batch remaining quantity
            new_batch_qty = batch_remaining - qty_from_batch
            await execute_query_tx(
                "UPDATE inventory_batches SET remaining_qty = $1, updated_at = NOW() WHERE id = $2",
                new_batch_qty,
                batch["id"],
                conn=conn,
            )

            # Get new item balance (trigger updates current_qty)
            item_updated = await fetch_one_tx(
                "SELECT current_qty FROM item_master WHERE id = $1",
                request.item_master_id,
                conn=conn,
            )
            new_balance = item_updated["current_qty"]

            # Log transaction
            await execute_query_tx(
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
                conn=conn,
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
            po.created_by::text as created_by,
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

    async with DatabaseTransaction() as conn:
        # Create PO (total_cost will be auto-calculated by trigger)
        po_id = await execute_query_tx(
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
            conn=conn,
        )

        # Insert PO items
        for item in request.items:
            await execute_query_tx(
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
                conn=conn,
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

    # Format PO data for notification
    po_dict = dict(po)
    po_dict["item_count"] = po_dict.get("items_count", 0)

    # Send Telegram notification (non-blocking)
    asyncio.create_task(telegram_service.notify_po_created(po_dict))

    return po


async def update_purchase_order_status(po_id: int, request: UpdatePORequest) -> Dict:
    """Update purchase order"""
    # Get old PO status for notification
    old_po = await fetch_one(
        "SELECT status FROM purchase_orders WHERE id = $1",
        po_id
    )

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
    result = await execute_query(query, *params)

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

    # Send Telegram notification if status changed (non-blocking)
    if request.status is not None and old_po and old_po["status"] != request.status:
        asyncio.create_task(
            telegram_service.notify_po_status_changed(
                dict(po),
                old_po["status"],
                request.status
            )
        )

    return po


# ============================================================================
# ENHANCED PO OPERATIONS
# ============================================================================


# Import PO status transitions
from app.schemas.inventory import PO_STATUS_TRANSITIONS
import json


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if a status transition is allowed"""
    allowed = PO_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed


async def record_po_history(
    po_id: int,
    action: str,
    user_id: str,
    user_name: str = None,
    previous_status: str = None,
    new_status: str = None,
    change_details: dict = None,
    conn=None
):
    """Record PO history/audit entry"""
    query = """
        INSERT INTO po_history (
            purchase_order_id, action, previous_status, new_status,
            change_details, changed_by, changed_by_name
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    """
    try:
        if conn:
            return await execute_query_tx(
                query,
                po_id, action, previous_status, new_status,
                json.dumps(change_details) if change_details else None,
                user_id, user_name,
                conn=conn
            )
        else:
            return await execute_query(
                query,
                po_id, action, previous_status, new_status,
                json.dumps(change_details) if change_details else None,
                user_id, user_name
            )
    except Exception:
        # Table might not exist yet - migration not run
        # Silently ignore - history is optional
        return None


async def get_purchase_order_detail(po_id: int) -> Dict:
    """Get single purchase order with all line items"""
    # Get PO header
    po = await fetch_one(
        """
        SELECT
            po.id,
            po.po_number,
            po.supplier_id,
            s.supplier_name,
            po.po_date,
            po.expected_delivery,
            po.status,
            po.total_cost,
            po.notes,
            po.created_by::text as created_by,
            up.full_name as created_by_name,
            po.created_at
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        LEFT JOIN user_profiles up ON up.id = po.created_by
        WHERE po.id = $1
        """,
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    # Get line items
    items = await fetch_all(
        """
        SELECT
            poi.id,
            poi.item_master_id,
            im.item_name,
            poi.ordered_qty,
            poi.unit_cost,
            (poi.ordered_qty * poi.unit_cost) as line_total
        FROM purchase_order_items poi
        JOIN item_master im ON im.id = poi.item_master_id
        WHERE poi.purchase_order_id = $1
        ORDER BY poi.id
        """,
        po_id
    )

    # Get receiving info if table exists (graceful handling)
    receiving = []
    try:
        receiving = await fetch_all(
            """
            SELECT
                pr.id,
                pr.po_item_id,
                pr.item_master_id,
                im.item_name,
                pr.ordered_qty,
                pr.received_qty,
                pr.po_unit_cost,
                pr.actual_unit_cost,
                pr.po_line_total,
                pr.actual_line_total,
                pr.batch_id,
                pr.batch_number,
                pr.receipt_date,
                pr.expiry_date,
                pr.notes,
                pr.received_by::text as received_by,
                up.full_name as received_by_name,
                pr.created_at
            FROM po_receiving pr
            JOIN item_master im ON im.id = pr.item_master_id
            LEFT JOIN user_profiles up ON up.id = pr.received_by
            WHERE pr.purchase_order_id = $1
            ORDER BY pr.created_at DESC
            """,
            po_id
        )
    except Exception:
        # Table might not exist yet - migration not run
        receiving = []

    # Calculate receiving summary
    summary = None
    if items:
        total_items = len(items)
        total_ordered_value = sum(float(item["line_total"]) for item in items)

        # Get receiving totals per item
        receiving_by_item = {}
        for r in receiving:
            item_id = r["po_item_id"]
            if item_id not in receiving_by_item:
                receiving_by_item[item_id] = {"qty": 0, "value": 0}
            receiving_by_item[item_id]["qty"] += float(r["received_qty"])
            receiving_by_item[item_id]["value"] += float(r["actual_line_total"])

        fully_received = 0
        partially_received = 0
        not_received = 0
        total_received_value = 0

        for item in items:
            item_id = item["id"]
            ordered = float(item["ordered_qty"])
            recv_data = receiving_by_item.get(item_id, {"qty": 0, "value": 0})
            received = recv_data["qty"]
            total_received_value += recv_data["value"]

            if received >= ordered:
                fully_received += 1
            elif received > 0:
                partially_received += 1
            else:
                not_received += 1

        summary = {
            "total_items": total_items,
            "fully_received": fully_received,
            "partially_received": partially_received,
            "not_received": not_received,
            "total_ordered_value": Decimal(str(total_ordered_value)),
            "total_received_value": Decimal(str(total_received_value)),
            "variance": Decimal(str(total_received_value - total_ordered_value))
        }

    result = dict(po)
    result["items"] = items
    result["receiving"] = receiving
    result["receiving_summary"] = summary

    return result


async def delete_purchase_order(po_id: int, user_id: str, user_name: str) -> Dict:
    """Delete purchase order (only pending or cancelled)"""
    # Get PO
    po = await fetch_one(
        "SELECT id, po_number, status FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    # Only allow deletion of pending or cancelled POs
    if po["status"] not in ["pending", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete PO with status '{po['status']}'. Only pending or cancelled POs can be deleted."
        )

    # Check if there are any receiving records
    receiving = await fetch_one(
        "SELECT COUNT(*) as count FROM po_receiving WHERE purchase_order_id = $1",
        po_id
    )

    if receiving and receiving["count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete PO with receiving records"
        )

    # Record history before deletion
    await record_po_history(
        po_id, "deleted", user_id, user_name,
        previous_status=po["status"],
        change_details={"po_number": po["po_number"]}
    )

    # Delete PO (cascades to items)
    await execute_query(
        "DELETE FROM purchase_orders WHERE id = $1",
        po_id
    )

    return {
        "success": True,
        "message": f"Purchase order {po['po_number']} deleted successfully"
    }


async def duplicate_purchase_order(po_id: int, request, user_id: str, user_name: str) -> Dict:
    """Duplicate an existing purchase order"""
    # Get original PO
    original_po = await fetch_one(
        "SELECT * FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not original_po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    # Check if new PO number exists
    existing = await fetch_one(
        "SELECT id FROM purchase_orders WHERE po_number = $1",
        request.new_po_number
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PO number '{request.new_po_number}' already exists"
        )

    # Determine supplier
    supplier_id = request.supplier_id or original_po["supplier_id"]

    async with DatabaseTransaction() as conn:
        # Create new PO
        new_po_id = await execute_query_tx(
            """
            INSERT INTO purchase_orders (
                po_number, supplier_id, po_date, expected_delivery, notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            request.new_po_number,
            supplier_id,
            request.po_date,
            request.expected_delivery,
            request.notes or original_po["notes"],
            user_id,
            conn=conn
        )

        # Copy or use provided items
        if request.items:
            # Use provided items
            for item in request.items:
                await execute_query_tx(
                    """
                    INSERT INTO purchase_order_items (
                        purchase_order_id, item_master_id, ordered_qty, unit_cost
                    )
                    VALUES ($1, $2, $3, $4)
                    """,
                    new_po_id,
                    item.item_master_id,
                    item.ordered_qty,
                    item.unit_cost,
                    conn=conn
                )
        else:
            # Copy original items
            original_items = await fetch_all(
                "SELECT item_master_id, ordered_qty, unit_cost FROM purchase_order_items WHERE purchase_order_id = $1",
                po_id
            )
            for item in original_items:
                await execute_query_tx(
                    """
                    INSERT INTO purchase_order_items (
                        purchase_order_id, item_master_id, ordered_qty, unit_cost
                    )
                    VALUES ($1, $2, $3, $4)
                    """,
                    new_po_id,
                    item["item_master_id"],
                    item["ordered_qty"],
                    item["unit_cost"],
                    conn=conn
                )

        # Record history
        await record_po_history(
            new_po_id, "duplicated", user_id, user_name,
            new_status="pending",
            change_details={"duplicated_from": po_id, "original_po_number": original_po["po_number"]},
            conn=conn
        )

    # Fetch and return new PO
    new_po = await fetch_one(
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
        new_po_id
    )

    return new_po


async def receive_purchase_order(po_id: int, request, user_id: str, user_name: str) -> Dict:
    """Receive goods for a purchase order with inventory batch creation"""
    # Get PO
    po = await fetch_one(
        """
        SELECT po.*, s.supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.id = $1
        """,
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    # Check if status allows receiving
    if po["status"] not in ["ordered", "partially_received"]:
        if po["status"] == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PO must be in 'ordered' status to receive goods. Please approve and mark as ordered first."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive goods for PO with status '{po['status']}'"
        )

    # Get PO items for validation
    po_items = await fetch_all(
        """
        SELECT poi.*, im.item_name
        FROM purchase_order_items poi
        JOIN item_master im ON im.id = poi.item_master_id
        WHERE poi.purchase_order_id = $1
        """,
        po_id
    )

    po_items_dict = {item["id"]: item for item in po_items}

    # Validate received items
    for recv_item in request.items:
        if recv_item.po_item_id not in po_items_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PO item {recv_item.po_item_id} not found in this purchase order"
            )

    batches_created = []
    receiving_records = []

    async with DatabaseTransaction() as conn:
        for recv_item in request.items:
            po_item = po_items_dict[recv_item.po_item_id]

            # Create inventory batch if quantity > 0
            batch_id = None
            if recv_item.received_qty > 0:
                batch_id = await execute_query_tx(
                    """
                    INSERT INTO inventory_batches (
                        item_master_id, quantity_purchased, remaining_qty, unit_cost,
                        purchase_date, expiry_date, supplier_id, batch_number, po_number, notes
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    po_item["item_master_id"],
                    recv_item.received_qty,
                    recv_item.received_qty,
                    recv_item.actual_unit_cost,
                    request.receipt_date,
                    recv_item.expiry_date,
                    po["supplier_id"],
                    recv_item.batch_number,
                    po["po_number"],
                    recv_item.notes,
                    conn=conn
                )
                batches_created.append(batch_id)

                # Update item current_qty
                await execute_query_tx(
                    """
                    UPDATE item_master
                    SET current_qty = current_qty + $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    recv_item.received_qty,
                    po_item["item_master_id"],
                    conn=conn
                )

                # Log transaction
                await execute_query_tx(
                    """
                    INSERT INTO inventory_transactions (
                        item_master_id, batch_id, transaction_type, quantity_change,
                        new_balance, unit_cost, total_cost, po_number, user_id, notes
                    )
                    SELECT
                        $1, $2, 'purchase', $3,
                        im.current_qty, $4, $5, $6, $7, $8
                    FROM item_master im WHERE im.id = $1
                    """,
                    po_item["item_master_id"],
                    batch_id,
                    recv_item.received_qty,
                    recv_item.actual_unit_cost,
                    recv_item.received_qty * recv_item.actual_unit_cost,
                    po["po_number"],
                    user_id,
                    f"Received from PO {po['po_number']}",
                    conn=conn
                )

            # Record receiving
            recv_id = await execute_query_tx(
                """
                INSERT INTO po_receiving (
                    purchase_order_id, po_item_id, item_master_id,
                    ordered_qty, received_qty, po_unit_cost, actual_unit_cost,
                    batch_id, batch_number, receipt_date, expiry_date, notes, received_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
                """,
                po_id,
                recv_item.po_item_id,
                po_item["item_master_id"],
                po_item["ordered_qty"],
                recv_item.received_qty,
                po_item["unit_cost"],
                recv_item.actual_unit_cost,
                batch_id,
                recv_item.batch_number,
                request.receipt_date,
                recv_item.expiry_date,
                recv_item.notes,
                user_id,
                conn=conn
            )

            receiving_records.append({
                "id": recv_id,
                "po_item_id": recv_item.po_item_id,
                "item_master_id": po_item["item_master_id"],
                "item_name": po_item["item_name"],
                "ordered_qty": po_item["ordered_qty"],
                "received_qty": recv_item.received_qty,
                "po_unit_cost": po_item["unit_cost"],
                "actual_unit_cost": recv_item.actual_unit_cost,
                "po_line_total": po_item["ordered_qty"] * po_item["unit_cost"],
                "actual_line_total": recv_item.received_qty * recv_item.actual_unit_cost,
                "batch_id": batch_id,
                "batch_number": recv_item.batch_number,
                "receipt_date": request.receipt_date,
                "expiry_date": recv_item.expiry_date,
                "notes": recv_item.notes,
                "received_by": user_id,
                "received_by_name": user_name,
                "created_at": datetime.now()
            })

        # Determine new status
        # Get all receiving for this PO
        all_receiving = await fetch_all(
            """
            SELECT poi.id, poi.ordered_qty, COALESCE(SUM(pr.received_qty), 0) as total_received
            FROM purchase_order_items poi
            LEFT JOIN po_receiving pr ON pr.po_item_id = poi.id
            WHERE poi.purchase_order_id = $1
            GROUP BY poi.id, poi.ordered_qty
            """,
            po_id
        )

        all_fully_received = all(
            float(r["total_received"]) >= float(r["ordered_qty"])
            for r in all_receiving
        )
        any_received = any(float(r["total_received"]) > 0 for r in all_receiving)

        if request.close_po:
            new_status = "closed"
        elif all_fully_received:
            new_status = "received"
        elif any_received:
            new_status = "partially_received"
        else:
            new_status = po["status"]

        # Update PO status
        old_status = po["status"]
        if new_status != old_status:
            await execute_query_tx(
                "UPDATE purchase_orders SET status = $1, updated_at = NOW() WHERE id = $2",
                new_status, po_id,
                conn=conn
            )

        # Record history
        await record_po_history(
            po_id, "received", user_id, user_name,
            previous_status=old_status,
            new_status=new_status,
            change_details={
                "items_received": len(request.items),
                "batches_created": batches_created,
                "receipt_date": str(request.receipt_date)
            },
            conn=conn
        )

    # Calculate summary
    summary_result = await fetch_one(
        "SELECT * FROM get_po_receiving_summary($1)",
        po_id
    )

    summary = {
        "total_items": summary_result["total_items"] if summary_result else 0,
        "fully_received": summary_result["fully_received"] if summary_result else 0,
        "partially_received": summary_result["partially_received"] if summary_result else 0,
        "not_received": summary_result["not_received"] if summary_result else 0,
        "total_ordered_value": summary_result["total_ordered_value"] or Decimal("0"),
        "total_received_value": summary_result["total_received_value"] or Decimal("0"),
        "variance": summary_result["variance"] or Decimal("0")
    }

    return {
        "success": True,
        "message": f"Received {len(request.items)} items for PO {po['po_number']}",
        "po_id": po_id,
        "new_status": new_status,
        "items_received": receiving_records,
        "batches_created": batches_created,
        "summary": summary
    }


async def add_po_items(po_id: int, request, user_id: str, user_name: str) -> Dict:
    """Add items to an existing purchase order (only pending status)"""
    # Get PO
    po = await fetch_one(
        "SELECT id, po_number, status FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    if po["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify items on PO with status '{po['status']}'. Only pending POs can be modified."
        )

    async with DatabaseTransaction() as conn:
        added_items = []
        for item in request.items:
            # Verify item exists
            im = await fetch_one(
                "SELECT id, item_name FROM item_master WHERE id = $1",
                item.item_master_id
            )
            if not im:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {item.item_master_id} not found"
                )

            await execute_query_tx(
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
                conn=conn
            )
            added_items.append({"item_name": im["item_name"], "qty": float(item.ordered_qty)})

        # Record history
        await record_po_history(
            po_id, "items_added", user_id, user_name,
            change_details={"items_added": added_items},
            conn=conn
        )

    # Get updated totals
    po_updated = await fetch_one(
        """
        SELECT total_cost, (SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = $1) as items_count
        FROM purchase_orders WHERE id = $1
        """,
        po_id
    )

    return {
        "success": True,
        "message": f"Added {len(request.items)} items to PO {po['po_number']}",
        "po_id": po_id,
        "new_total_cost": po_updated["total_cost"],
        "items_count": po_updated["items_count"]
    }


async def update_po_items(po_id: int, request, user_id: str, user_name: str) -> Dict:
    """Update items on an existing purchase order (only pending status)"""
    # Get PO
    po = await fetch_one(
        "SELECT id, po_number, status FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    if po["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify items on PO with status '{po['status']}'. Only pending POs can be modified."
        )

    async with DatabaseTransaction() as conn:
        updated_items = []
        for item in request.items:
            # Get current item
            current = await fetch_one(
                """
                SELECT poi.*, im.item_name
                FROM purchase_order_items poi
                JOIN item_master im ON im.id = poi.item_master_id
                WHERE poi.id = $1 AND poi.purchase_order_id = $2
                """,
                item.po_item_id, po_id
            )

            if not current:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PO item {item.po_item_id} not found in this purchase order"
                )

            # Build update
            update_fields = []
            params = []
            param_count = 1
            changes = {"item_name": current["item_name"]}

            if item.ordered_qty is not None:
                update_fields.append(f"ordered_qty = ${param_count}")
                params.append(item.ordered_qty)
                changes["qty_from"] = float(current["ordered_qty"])
                changes["qty_to"] = float(item.ordered_qty)
                param_count += 1

            if item.unit_cost is not None:
                update_fields.append(f"unit_cost = ${param_count}")
                params.append(item.unit_cost)
                changes["cost_from"] = float(current["unit_cost"])
                changes["cost_to"] = float(item.unit_cost)
                param_count += 1

            if update_fields:
                params.append(item.po_item_id)
                await execute_query_tx(
                    f"UPDATE purchase_order_items SET {', '.join(update_fields)} WHERE id = ${param_count}",
                    *params,
                    conn=conn
                )
                updated_items.append(changes)

        # Record history
        await record_po_history(
            po_id, "items_updated", user_id, user_name,
            change_details={"items_updated": updated_items},
            conn=conn
        )

    # Get updated totals
    po_updated = await fetch_one(
        """
        SELECT total_cost, (SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = $1) as items_count
        FROM purchase_orders WHERE id = $1
        """,
        po_id
    )

    return {
        "success": True,
        "message": f"Updated {len(request.items)} items on PO {po['po_number']}",
        "po_id": po_id,
        "new_total_cost": po_updated["total_cost"],
        "items_count": po_updated["items_count"]
    }


async def delete_po_item(po_id: int, item_id: int, user_id: str, user_name: str) -> Dict:
    """Delete an item from a purchase order (only pending status)"""
    # Get PO
    po = await fetch_one(
        "SELECT id, po_number, status FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    if po["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify items on PO with status '{po['status']}'. Only pending POs can be modified."
        )

    # Get item to delete
    item = await fetch_one(
        """
        SELECT poi.*, im.item_name
        FROM purchase_order_items poi
        JOIN item_master im ON im.id = poi.item_master_id
        WHERE poi.id = $1 AND poi.purchase_order_id = $2
        """,
        item_id, po_id
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PO item {item_id} not found in this purchase order"
        )

    # Check if this is the last item
    count = await fetch_one(
        "SELECT COUNT(*) as count FROM purchase_order_items WHERE purchase_order_id = $1",
        po_id
    )

    if count["count"] <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last item from a PO. Delete the PO instead."
        )

    # Delete item
    await execute_query(
        "DELETE FROM purchase_order_items WHERE id = $1",
        item_id
    )

    # Record history
    await record_po_history(
        po_id, "items_deleted", user_id, user_name,
        change_details={
            "deleted_item": {
                "item_name": item["item_name"],
                "ordered_qty": float(item["ordered_qty"]),
                "unit_cost": float(item["unit_cost"])
            }
        }
    )

    # Get updated totals
    po_updated = await fetch_one(
        """
        SELECT total_cost, (SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = $1) as items_count
        FROM purchase_orders WHERE id = $1
        """,
        po_id
    )

    return {
        "success": True,
        "message": f"Deleted {item['item_name']} from PO {po['po_number']}",
        "po_id": po_id,
        "new_total_cost": po_updated["total_cost"],
        "items_count": po_updated["items_count"]
    }


async def get_po_history(po_id: int) -> Dict:
    """Get purchase order history/audit trail"""
    # Verify PO exists
    po = await fetch_one(
        "SELECT id FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    history = []
    try:
        history = await fetch_all(
            """
            SELECT
                id,
                purchase_order_id,
                action,
                previous_status,
                new_status,
                change_details,
                changed_by::text as changed_by,
                changed_by_name,
                changed_at
            FROM po_history
            WHERE purchase_order_id = $1
            ORDER BY changed_at DESC
            """,
            po_id
        )

        # Parse JSON change_details
        for h in history:
            if h["change_details"] and isinstance(h["change_details"], str):
                try:
                    h["change_details"] = json.loads(h["change_details"])
                except:
                    pass
    except Exception:
        # Table might not exist yet - migration not run
        history = []

    return {
        "history": history,
        "total": len(history)
    }


async def update_purchase_order_with_validation(po_id: int, request, user_id: str, user_name: str) -> Dict:
    """Update purchase order with status workflow validation"""
    # Get current PO
    po = await fetch_one(
        "SELECT id, po_number, status FROM purchase_orders WHERE id = $1",
        po_id
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found"
        )

    # Validate status transition
    if request.status is not None and request.status != po["status"]:
        if not validate_status_transition(po["status"], request.status):
            allowed = PO_STATUS_TRANSITIONS.get(po["status"], [])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from '{po['status']}' to '{request.status}'. Allowed transitions: {', '.join(allowed) if allowed else 'none (terminal state)'}"
            )

    # Build update
    update_fields = []
    params = []
    param_count = 1
    old_status = po["status"]

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    update_fields.append("updated_at = NOW()")
    params.append(po_id)

    async with DatabaseTransaction() as conn:
        await execute_query_tx(
            f"UPDATE purchase_orders SET {', '.join(update_fields)} WHERE id = ${param_count}",
            *params,
            conn=conn
        )

        # Record history
        action = "status_changed" if request.status and request.status != old_status else "updated"
        await record_po_history(
            po_id, action, user_id, user_name,
            previous_status=old_status if request.status else None,
            new_status=request.status if request.status else None,
            change_details={
                "expected_delivery": str(request.expected_delivery) if request.expected_delivery else None,
                "notes_updated": request.notes is not None
            },
            conn=conn
        )

    # Fetch updated PO
    po_updated = await fetch_one(
        """
        SELECT po.*, s.supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON s.id = po.supplier_id
        WHERE po.id = $1
        """,
        po_id
    )

    # Send Telegram notification if status changed
    if request.status is not None and request.status != old_status:
        asyncio.create_task(
            telegram_service.notify_po_status_changed(
                dict(po_updated),
                old_status,
                request.status
            )
        )

    return po_updated


# ============================================================================
# STOCK ADJUSTMENTS
# ============================================================================


async def create_stock_adjustment(
    request: CreateAdjustmentRequest, user_id: str
) -> Dict:
    """Create stock adjustment"""
    # Get current item quantity
    item = await fetch_one(
        "SELECT id, item_name, current_qty FROM item_master WHERE id = $1",
        request.item_master_id,
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    previous_qty = Decimal(str(item["current_qty"]))

    # Calculate new quantity based on adjustment type
    if request.adjustment_type == "recount":
        # For recount, quantity_change is the actual new quantity
        new_qty = request.quantity_change
        quantity_change = new_qty - previous_qty
    elif request.adjustment_type == "increase":
        quantity_change = abs(request.quantity_change)
        new_qty = previous_qty + quantity_change
    else:  # decrease
        quantity_change = -abs(request.quantity_change)
        new_qty = previous_qty + quantity_change

    # Ensure new quantity is not negative
    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adjustment would result in negative stock ({new_qty})",
        )

    async with DatabaseTransaction() as conn:
        # Create adjustment record
        adjustment_id = await execute_query_tx(
            conn,
            """
            INSERT INTO stock_adjustments (
                item_master_id, adjustment_type, quantity_change,
                previous_qty, new_qty, reason, notes, adjusted_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            request.item_master_id,
            request.adjustment_type,
            quantity_change,
            previous_qty,
            new_qty,
            request.reason,
            request.notes,
            user_id,
        )

        # Update item current_qty
        await execute_query_tx(
            conn,
            "UPDATE item_master SET current_qty = $1, updated_at = NOW() WHERE id = $2",
            new_qty,
            request.item_master_id,
        )

        # Log transaction
        await execute_query_tx(
            conn,
            """
            INSERT INTO inventory_transactions (
                item_master_id, transaction_type, quantity_change,
                new_balance, user_id, notes
            )
            VALUES ($1, 'adjustment', $2, $3, $4, $5)
            """,
            request.item_master_id,
            quantity_change,
            new_qty,
            user_id,
            f"{request.adjustment_type}: {request.reason}",
        )

    return {
        "success": True,
        "message": f"Stock adjusted successfully",
        "adjustment_id": adjustment_id,
        "previous_qty": previous_qty,
        "new_qty": new_qty,
        "quantity_change": quantity_change,
    }


async def get_stock_adjustments_list(
    item_id: Optional[int] = None,
    days_back: int = 30,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """Get stock adjustments list"""
    where_conditions = [
        f"sa.adjustment_date >= NOW() - INTERVAL '{days_back} days'"
    ]
    params = []
    param_count = 1

    if item_id:
        where_conditions.append(f"sa.item_master_id = ${param_count}")
        params.append(item_id)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}"

    # Count
    count_query = f"SELECT COUNT(*) as total FROM stock_adjustments sa {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get adjustments
    offset = (page - 1) * limit
    adjustments_query = f"""
        SELECT
            sa.id,
            sa.item_master_id,
            im.item_name,
            im.sku,
            im.unit,
            sa.adjustment_type,
            sa.quantity_change,
            sa.previous_qty,
            sa.new_qty,
            sa.reason,
            sa.notes,
            sa.adjusted_by,
            up.full_name as adjusted_by_name,
            sa.adjustment_date
        FROM stock_adjustments sa
        JOIN item_master im ON im.id = sa.item_master_id
        LEFT JOIN user_profiles up ON up.id = sa.adjusted_by
        {where_clause}
        ORDER BY sa.adjustment_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    adjustments = await fetch_all(adjustments_query, *params)

    return {
        "adjustments": adjustments,
        "total": total,
        "page": page,
        "limit": limit,
    }


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
          AND ib.expiry_date <= CURRENT_DATE + make_interval(days => $1)
        ORDER BY ib.expiry_date
        """,
        days,
    )
    return items


# ============================================================================
# TRANSACTIONS
# ============================================================================


async def get_transactions_list(
    item_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
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

    if transaction_type:
        where_conditions.append(f"it.transaction_type = ${param_count}")
        params.append(transaction_type)
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
            it.id,
            it.item_master_id,
            it.batch_id,
            it.transaction_type,
            it.quantity_change,
            it.new_balance,
            it.unit_cost,
            it.total_cost,
            it.po_number,
            it.module_reference,
            it.tank_id::text as tank_id,
            it.user_id::text as user_id,
            it.username,
            it.notes,
            it.transaction_date,
            COALESCE(it.module_batch_id::text, NULL) as module_batch_id,
            it.session_number,
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


# ============================================================================
# BATCH DEDUCTION (Multi-item atomic operations)
# ============================================================================


async def batch_deduct_stock(
    request: "BatchDeductionRequest", user_id: str, username: str
) -> Dict:
    """
    Deduct multiple items in a single atomic transaction.
    All items succeed or all fail (rollback).
    """
    from app.schemas.inventory import BatchDeductionResultItem

    results = []
    transaction_ids = []
    total_cost = Decimal("0")
    successful = 0
    failed = 0

    async with DatabaseTransaction() as conn:
        try:
            for deduction_item in request.deductions:
                try:
                    # Resolve item by ID, SKU, or item_name
                    if deduction_item.item_id:
                        item = await fetch_one_tx(
                            "SELECT id, item_name, sku FROM item_master WHERE id = $1 AND is_active = TRUE",
                            deduction_item.item_id,
                            conn=conn,
                        )
                    else:
                        # Try SKU first, then item_name
                        item = await fetch_one_tx(
                            "SELECT id, item_name, sku FROM item_master WHERE (sku = $1 OR item_name = $1) AND is_active = TRUE",
                            deduction_item.sku,
                            conn=conn,
                        )

                    if not item:
                        failed += 1
                        results.append(
                            BatchDeductionResultItem(
                                item_name=f"Unknown ({deduction_item.sku or deduction_item.item_id})",
                                sku=deduction_item.sku,
                                quantity=deduction_item.quantity,
                                cost=Decimal("0"),
                                success=False,
                                error="Item not found",
                            )
                        )
                        continue

                    # Get available batches (FIFO)
                    batches = await fetch_all_tx(
                        """
                        SELECT id, batch_number, remaining_qty, unit_cost
                        FROM inventory_batches
                        WHERE item_master_id = $1
                          AND is_active = TRUE
                          AND remaining_qty > 0
                        ORDER BY purchase_date ASC, id ASC
                        """,
                        item["id"],
                        conn=conn,
                    )

                    if not batches:
                        failed += 1
                        results.append(
                            BatchDeductionResultItem(
                                item_name=item["item_name"],
                                sku=item["sku"],
                                quantity=deduction_item.quantity,
                                cost=Decimal("0"),
                                success=False,
                                error="No stock available",
                                available=Decimal("0"),
                                requested=deduction_item.quantity,
                            )
                        )
                        continue

                    # Calculate total available
                    total_available = sum(Decimal(str(b["remaining_qty"])) for b in batches)

                    if deduction_item.quantity > total_available:
                        failed += 1
                        results.append(
                            BatchDeductionResultItem(
                                item_name=item["item_name"],
                                sku=item["sku"],
                                quantity=deduction_item.quantity,
                                cost=Decimal("0"),
                                success=False,
                                error="Insufficient stock",
                                available=total_available,
                                requested=deduction_item.quantity,
                            )
                        )
                        continue

                    # Deduct from batches using FIFO
                    remaining_to_deduct = deduction_item.quantity
                    item_cost = Decimal("0")

                    for batch in batches:
                        if remaining_to_deduct <= 0:
                            break

                        batch_remaining = Decimal(str(batch["remaining_qty"]))
                        batch_unit_cost = Decimal(str(batch["unit_cost"]))

                        qty_from_batch = min(remaining_to_deduct, batch_remaining)
                        cost_from_batch = qty_from_batch * batch_unit_cost

                        # Update batch remaining quantity
                        new_batch_qty = batch_remaining - qty_from_batch
                        await execute_query_tx(
                            "UPDATE inventory_batches SET remaining_qty = $1, updated_at = NOW() WHERE id = $2",
                            new_batch_qty,
                            batch["id"],
                            conn=conn,
                        )

                        # Get new item balance (trigger updates current_qty)
                        item_updated = await fetch_one_tx(
                            "SELECT current_qty FROM item_master WHERE id = $1",
                            item["id"],
                            conn=conn,
                        )
                        new_balance = item_updated["current_qty"]

                        # Log transaction with batch_id and session_number
                        notes = f"Batch operation: {request.global_notes or 'N/A'}"
                        if deduction_item.notes:
                            notes += f" | Item note: {deduction_item.notes}"

                        tx_result = await fetch_one_tx(
                            """
                            INSERT INTO inventory_transactions (
                                item_master_id, batch_id, transaction_type, quantity_change,
                                new_balance, unit_cost, total_cost, module_reference, tank_id,
                                user_id, username, notes, module_batch_id, session_number
                            )
                            VALUES ($1, $2, 'use', $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            RETURNING id
                            """,
                            item["id"],
                            batch["id"],  # inventory batch_id
                            -qty_from_batch,  # Negative for deduction
                            new_balance,
                            batch_unit_cost,
                            cost_from_batch,
                            request.module_reference.value,
                            UUID(request.tank_id) if request.tank_id else None,  # Convert string to UUID
                            user_id,
                            username,
                            notes,
                            str(request.batch_id) if request.batch_id else None,  # module_batch_id (biofloc batch)
                            request.session_number,
                            conn=conn,
                        )

                        transaction_ids.append(tx_result["id"])

                        item_cost += cost_from_batch
                        remaining_to_deduct -= qty_from_batch

                    # Item successfully deducted
                    successful += 1
                    total_cost += item_cost
                    results.append(
                        BatchDeductionResultItem(
                            item_name=item["item_name"],
                            sku=item["sku"],
                            quantity=deduction_item.quantity,
                            cost=item_cost,
                            success=True,
                        )
                    )

                except Exception as e:
                    logger.error(f"Error deducting item {deduction_item}: {e}")
                    failed += 1
                    results.append(
                        BatchDeductionResultItem(
                            item_name="Error",
                            sku=deduction_item.sku,
                            quantity=deduction_item.quantity,
                            cost=Decimal("0"),
                            success=False,
                            error=str(e),
                        )
                    )

            # If any item failed, rollback entire transaction
            if failed > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Batch deduction failed. {failed} items failed, {successful} would have succeeded. All rolled back.",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Batch deduction error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch deduction failed: {str(e)}",
            )

    return {
        "success": True,
        "total": len(request.deductions),
        "successful": successful,
        "failed": failed,
        "total_cost": total_cost,
        "results": results,
        "transaction_ids": transaction_ids,
    }


# ============================================================================
# BULK FETCH (Multi-item retrieval)
# ============================================================================


async def bulk_fetch_items(request: "BulkFetchRequest") -> Dict:
    """
    Fetch multiple items by IDs or SKUs in a single query.
    """
    from app.schemas.inventory import BulkFetchItemResponse

    items = []
    not_found = []

    # Build query based on identifiers
    if request.item_ids:
        query = """
            SELECT
                im.id,
                im.sku,
                im.item_name as name,
                im.current_qty,
                im.unit,
                im.category,
                im.reorder_threshold,
                (
                    SELECT unit_cost
                    FROM inventory_batches
                    WHERE item_master_id = im.id
                      AND is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                ) as last_purchase_price
            FROM item_master im
            WHERE im.id = ANY($1) AND im.is_active = TRUE
        """
        result_items = await fetch_all(query, request.item_ids)
        found_ids = {item["id"] for item in result_items}
        not_found.extend([id for id in request.item_ids if id not in found_ids])

    if request.skus:
        query = """
            SELECT
                im.id,
                im.sku,
                im.item_name as name,
                im.current_qty,
                im.unit,
                im.category,
                im.reorder_threshold,
                (
                    SELECT unit_cost
                    FROM inventory_batches
                    WHERE item_master_id = im.id
                      AND is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                ) as last_purchase_price
            FROM item_master im
            WHERE im.sku = ANY($1) AND im.is_active = TRUE
        """
        sku_items = await fetch_all(query, request.skus)
        result_items = result_items + sku_items if request.item_ids else sku_items
        found_skus = {item["sku"] for item in sku_items if item["sku"]}
        not_found.extend([sku for sku in request.skus if sku not in found_skus])

    # Enrich with reserved quantities if requested
    for item_data in result_items:
        item_dict = dict(item_data)

        if request.include_reserved:
            # Get reserved quantity
            reservation_result = await fetch_one(
                """
                SELECT COALESCE(SUM(quantity), 0) as reserved_qty
                FROM inventory_reservations
                WHERE item_id = $1 AND status = 'pending' AND reserved_until > NOW()
                """,
                item_data["id"],
            )
            item_dict["reserved_qty"] = reservation_result["reserved_qty"]
            item_dict["available_qty"] = item_data["current_qty"] - reservation_result["reserved_qty"]

        # Include batches if requested
        if request.include_batches:
            batches = await fetch_all(
                """
                SELECT
                    id, item_master_id, batch_number, quantity_purchased,
                    remaining_qty, unit_cost, purchase_date, expiry_date,
                    supplier_id, po_number, notes, is_active, created_at,
                    (SELECT item_name FROM item_master WHERE id = item_master_id) as item_name,
                    (SELECT supplier_name FROM suppliers WHERE id = supplier_id) as supplier_name
                FROM inventory_batches
                WHERE item_master_id = $1 AND is_active = TRUE
                ORDER BY purchase_date ASC
                """,
                item_data["id"],
            )
            item_dict["batches"] = batches

        items.append(BulkFetchItemResponse(**item_dict))

    total = len(items)
    requested = len(request.item_ids or []) + len(request.skus or [])

    return {
        "items": items,
        "total": total,
        "requested": requested,
        "found": total,
        "not_found": not_found,
    }


# ============================================================================
# STOCK RESERVATION SYSTEM
# ============================================================================


async def create_reservation(request: "CreateReservationRequest", user_id: str) -> Dict:
    """
    Create a stock reservation (soft lock) for planned usage.
    """
    from datetime import timedelta

    # Verify item exists and has sufficient available stock
    item = await fetch_one(
        "SELECT id, item_name, sku, current_qty FROM item_master WHERE id = $1 AND is_active = TRUE",
        request.item_id,
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # Get currently reserved quantity
    reserved_result = await fetch_one(
        """
        SELECT COALESCE(SUM(quantity), 0) as reserved_qty
        FROM inventory_reservations
        WHERE item_id = $1 AND status = 'pending' AND reserved_until > NOW()
        """,
        request.item_id,
    )
    reserved_qty = reserved_result["reserved_qty"]
    available_qty = item["current_qty"] - reserved_qty

    if request.quantity > available_qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient available stock. Available: {available_qty}, Requested: {request.quantity}",
        )

    # Calculate reserved_until timestamp
    from datetime import datetime, timezone
    reserved_until = datetime.now(timezone.utc) + timedelta(hours=request.duration_hours)

    # Create reservation
    reservation_id = await execute_query(
        """
        INSERT INTO inventory_reservations (
            item_id, quantity, module_reference, reference_id,
            status, reserved_until, notes, created_by
        )
        VALUES ($1, $2, $3, $4, 'pending', $5, $6, $7)
        RETURNING id
        """,
        request.item_id,
        request.quantity,
        request.module_reference.value,
        str(request.reference_id) if request.reference_id else None,
        reserved_until,
        request.notes,
        user_id,
    )

    # Fetch created reservation
    reservation = await fetch_one(
        """
        SELECT
            ir.id, ir.item_id, ir.quantity, ir.module_reference, ir.reference_id,
            ir.status, ir.reserved_until, ir.notes, ir.created_by, ir.created_at,
            im.item_name, im.sku,
            up.full_name as created_by_name
        FROM inventory_reservations ir
        JOIN item_master im ON im.id = ir.item_id
        LEFT JOIN user_profiles up ON up.id = ir.created_by
        WHERE ir.id = $1
        """,
        reservation_id,
    )

    return reservation


async def get_reservations_list(
    item_id: Optional[int] = None,
    module_reference: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Dict:
    """
    Get list of reservations with optional filters.
    """
    where_conditions = []
    params = []
    param_count = 1

    if item_id:
        where_conditions.append(f"ir.item_id = ${param_count}")
        params.append(item_id)
        param_count += 1

    if module_reference:
        where_conditions.append(f"ir.module_reference = ${param_count}")
        params.append(module_reference)
        param_count += 1

    if status_filter:
        where_conditions.append(f"ir.status = ${param_count}")
        params.append(status_filter)
        param_count += 1
    else:
        # Default: only show active reservations
        where_conditions.append("ir.status = 'pending'")

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    query = f"""
        SELECT
            ir.id, ir.item_id, ir.quantity, ir.module_reference, ir.reference_id,
            ir.status, ir.reserved_until, ir.notes, ir.created_by, ir.created_at,
            im.item_name, im.sku,
            up.full_name as created_by_name
        FROM inventory_reservations ir
        JOIN item_master im ON im.id = ir.item_id
        LEFT JOIN user_profiles up ON up.id = ir.created_by
        {where_clause}
        ORDER BY ir.created_at DESC
    """

    reservations = await fetch_all(query, *params)
    total = len(reservations)

    return {"reservations": reservations, "total": total}


async def cancel_reservation(reservation_id: str) -> Dict:
    """
    Cancel a pending reservation.
    """
    result = await execute_query(
        """
        UPDATE inventory_reservations
        SET status = 'cancelled', updated_at = NOW()
        WHERE id = $1 AND status = 'pending'
        RETURNING id
        """,
        reservation_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found or already processed",
        )

    return {"success": True, "message": "Reservation cancelled successfully"}


async def confirm_reservation(
    reservation_id: str, user_id: str, username: str
) -> Dict:
    """
    Convert a reservation to actual stock usage (FIFO deduction).
    """
    # Get reservation details
    reservation = await fetch_one(
        """
        SELECT ir.*, im.item_name
        FROM inventory_reservations ir
        JOIN item_master im ON im.id = ir.item_id
        WHERE ir.id = $1 AND ir.status = 'pending'
        """,
        reservation_id,
    )

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found or already processed",
        )

    # Create UseStockRequest from reservation
    from app.schemas.inventory import UseStockRequest

    use_request = UseStockRequest(
        item_master_id=reservation["item_id"],
        quantity=reservation["quantity"],
        purpose=f"Confirmed reservation {reservation_id}",
        module_reference=reservation["module_reference"],
        notes=reservation["notes"],
    )

    # Use existing FIFO deduction logic
    try:
        result = await use_stock_fifo(use_request, user_id, username)

        # Mark reservation as confirmed
        await execute_query(
            """
            UPDATE inventory_reservations
            SET status = 'confirmed', updated_at = NOW()
            WHERE id = $1
            """,
            reservation_id,
        )

        return {
            "success": True,
            "message": "Reservation confirmed and stock deducted",
            "reservation_id": reservation_id,
            "cost": result["total_cost"],
        }

    except HTTPException as e:
        # If deduction fails, keep reservation as pending
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Failed to confirm reservation: {e.detail}",
        )


# ============================================================================
# MODULE-SPECIFIC OPERATIONS
# ============================================================================


async def get_module_items(module_name: str) -> Dict:
    """
    Get items used by a specific module.
    """
    query = """
        SELECT DISTINCT
            im.id,
            im.item_name,
            im.sku,
            im.category,
            im.unit,
            im.current_qty,
            im.reorder_threshold,
            im.is_active,
            imm.is_primary,
            imm.custom_settings
        FROM item_master im
        INNER JOIN item_module_mapping imm ON im.id = imm.item_id
        WHERE imm.module_name = $1 AND im.is_active = TRUE
        ORDER BY imm.is_primary DESC, im.item_name ASC
    """
    items = await fetch_all(query, module_name)
    return {"items": items, "total": len(items)}


async def get_module_consumption(module_name: str, days_back: int = 30) -> Dict:
    """
    Get consumption report for a specific module.
    """
    query = """
        SELECT
            it.item_master_id as item_id,
            im.item_name,
            im.sku,
            im.category,
            im.unit,
            SUM(ABS(it.quantity_change)) as total_quantity_used,
            SUM(ABS(it.total_cost)) as total_cost,
            COUNT(*) as transaction_count,
            MAX(it.transaction_date) as last_used
        FROM inventory_transactions it
        INNER JOIN item_master im ON it.item_master_id = im.id
        WHERE it.module_reference = $1
          AND it.transaction_type = 'use'
          AND it.transaction_date >= NOW() - INTERVAL '$2 days'
        GROUP BY it.item_master_id, im.item_name, im.sku, im.category, im.unit
        ORDER BY total_cost DESC
    """
    items = await fetch_all(query, module_name, days_back)

    # Calculate total cost
    total_cost = sum(item["total_cost"] for item in items)

    return {
        "module_name": module_name,
        "items": items,
        "total_cost": total_cost,
        "total_items": len(items),
        "period_days": days_back,
    }


async def create_item_module_mapping(
    item_id: int, request: "CreateItemModuleMappingRequest"
) -> Dict:
    """
    Create a mapping between an item and a module.
    """
    # Verify item exists
    item = await fetch_one("SELECT id FROM item_master WHERE id = $1", item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # If setting as primary, unset other primary mappings for this item
    if request.is_primary:
        await execute_query(
            "UPDATE item_module_mapping SET is_primary = FALSE WHERE item_id = $1",
            item_id,
        )

    # Create mapping
    mapping_id = await execute_query(
        """
        INSERT INTO item_module_mapping (item_id, module_name, custom_settings, is_primary)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (item_id, module_name)
        DO UPDATE SET custom_settings = $3, is_primary = $4, updated_at = NOW()
        RETURNING id
        """,
        item_id,
        request.module_name.value,
        request.custom_settings,
        request.is_primary,
    )

    # Fetch created mapping
    mapping = await fetch_one(
        """
        SELECT id, item_id, module_name, custom_settings, is_primary, created_at
        FROM item_module_mapping
        WHERE id = $1
        """,
        mapping_id,
    )

    return mapping


async def get_item_module_mappings(item_id: int) -> Dict:
    """
    Get all module mappings for an item.
    """
    mappings = await fetch_all(
        """
        SELECT id, item_id, module_name, custom_settings, is_primary, created_at
        FROM item_module_mapping
        WHERE item_id = $1
        ORDER BY is_primary DESC, module_name ASC
        """,
        item_id,
    )

    return {"mappings": mappings, "total": len(mappings)}


async def delete_item_module_mapping(item_id: int, module_name: str) -> None:
    """
    Remove a module mapping from an item.
    """
    result = await execute_query(
        "DELETE FROM item_module_mapping WHERE item_id = $1 AND module_name = $2 RETURNING id",
        item_id,
        module_name,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found"
        )
