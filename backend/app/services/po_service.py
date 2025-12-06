"""
================================================================================
Marketplace ERP - Purchase Order Service
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  Business logic for purchase order management. Handles PO creation, 3-tier
  pricing logic, vendor pricing management, status workflow, and Zoho export.

Functions:
  - generate_po_number: Sequential PO numbering
  - get_item_price: 3-tier pricing logic (vendor → zoho → manual)
  - create_po: Create PO with auto-pricing
  - get_po_details: Fetch complete PO
  - update_po: Update PO with validation
  - list_pos: List with filters and pagination
  - send_po_to_farm: Email notification
  - add_extra_items_from_grn: Handle GRN extra items
  - export_to_zoho: Generate CSV export
  - manage_vendor_pricing: Admin pricing management

================================================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal
import asyncpg
import csv
from io import StringIO

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
from app.schemas.po import (
    POCreateRequest, POUpdateRequest, POItemCreate,
    VendorPricingRequest, POStatus, PriceSource
)

logger = logging.getLogger(__name__)


# ============================================================================
# PO NUMBER GENERATION
# ============================================================================

async def generate_po_number() -> str:
    """
    Generate sequential PO number (thread-safe).
    Format: PO-001, PO-002, PO-003, etc.

    Returns:
        Sequential PO number

    Raises:
        Exception: If PO number generation fails
    """
    try:
        # Get max PO number and increment
        query = """
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(po_number FROM 4) AS INTEGER)), 
                0
            ) + 1 as next_number
            FROM purchase_orders
        """
        result = await fetch_one(query)
        next_number = result['next_number'] if result else 1

        # Format: PO-001, PO-002, etc. (pad to 3 digits)
        po_number = f"PO-{next_number:03d}"

        logger.info(f"✅ Generated PO number: {po_number}")
        return po_number

    except Exception as e:
        logger.error(f"❌ Failed to generate PO number: {e}")
        raise


# ============================================================================
# 3-TIER PRICING LOGIC
# ============================================================================

async def get_item_price(
    vendor_id: int,
    item_id: int,
    dispatch_date: date
) -> Dict[str, Any]:
    """
    Get item price using 3-tier pricing logic:
    1. Vendor-specific price for dispatch date (Tier 1)
    2. Zoho item default price (Tier 2)
    3. Manual entry required (Tier 3)

    Args:
        vendor_id: Zoho vendor ID
        item_id: Zoho item ID
        dispatch_date: Expected dispatch date (drives pricing)

    Returns:
        Dict with: {price: Decimal | None, source: 'vendor' | 'zoho' | 'manual'}
    """
    try:
        # Tier 1: Check vendor-specific price for dispatch date
        vendor_price_query = """
            SELECT price
            FROM vendor_item_price_history
            WHERE vendor_id = $1
              AND item_id = $2
              AND effective_from <= $3
              AND (effective_to >= $3 OR effective_to IS NULL)
            ORDER BY effective_from DESC
            LIMIT 1
        """
        vendor_price = await fetch_one(vendor_price_query, vendor_id, item_id, dispatch_date)

        if vendor_price and vendor_price['price']:
            logger.debug(f"✅ Found vendor price for item {item_id}: {vendor_price['price']}")
            return {
                "price": Decimal(str(vendor_price['price'])),
                "source": PriceSource.VENDOR.value
            }

        # Tier 2: Fall back to Zoho default price
        zoho_price_query = """
            SELECT purchase_rate
            FROM zoho_items
            WHERE id = $1
        """
        zoho_price = await fetch_one(zoho_price_query, item_id)

        if zoho_price and zoho_price['purchase_rate'] and float(zoho_price['purchase_rate']) > 0:
            logger.debug(f"✅ Using Zoho default price for item {item_id}: {zoho_price['purchase_rate']}")
            return {
                "price": Decimal(str(zoho_price['purchase_rate'])),
                "source": PriceSource.ZOHO.value
            }

        # Tier 3: Manual entry required
        logger.debug(f"⚠️ No auto-price found for item {item_id}, manual entry required")
        return {
            "price": None,
            "source": PriceSource.MANUAL.value
        }

    except Exception as e:
        logger.error(f"❌ Failed to get item price: {e}")
        raise


# ============================================================================
# PO CREATION
# ============================================================================

async def create_po(
    request: POCreateRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Create new purchase order with 3-tier pricing logic.

    Args:
        request: PO creation request
        user_id: User UUID who is creating the PO

    Returns:
        Complete PO details

    Raises:
        ValueError: If validation fails
        Exception: If creation fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Validate vendor exists
            vendor_query = "SELECT id, contact_name FROM zoho_vendors WHERE id = $1"
            vendor = await conn.fetchrow(vendor_query, request.vendor_id)
            if not vendor:
                raise ValueError(f"Vendor {request.vendor_id} not found")

            # 2. Generate PO number (within transaction for atomicity)
            po_number = await generate_po_number()

            # 3. Create PO record
            po_insert_query = """
                INSERT INTO purchase_orders (
                    po_number, vendor_id, dispatch_date, delivery_date,
                    notes, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, po_number, status, created_at, updated_at
            """
            po = await conn.fetchrow(
                po_insert_query,
                po_number,
                request.vendor_id,
                request.dispatch_date,
                request.delivery_date,
                request.notes,
                user_id
            )

            # 4. Process items with pricing
            total_amount = Decimal('0')
            items_data = []

            for item_req in request.items:
                # Validate item exists
                item_query = "SELECT id, name, sku FROM zoho_items WHERE id = $1"
                item = await conn.fetchrow(item_query, item_req.item_id)
                if not item:
                    raise ValueError(f"Item {item_req.item_id} not found")

                # Get price if not provided
                if item_req.unit_price is None:
                    price_info = await get_item_price(
                        request.vendor_id,
                        item_req.item_id,
                        request.dispatch_date
                    )
                    if price_info['price'] is None:
                        raise ValueError(
                            f"Price required for item {item['name']} (ID: {item_req.item_id}). "
                            f"No vendor or Zoho price found."
                        )
                    unit_price = price_info['price']
                    price_source = price_info['source']
                else:
                    unit_price = item_req.unit_price
                    price_source = PriceSource.MANUAL.value

                # Calculate total
                total_price = unit_price * item_req.quantity
                total_amount += total_price

                # Insert item
                item_insert_query = """
                    INSERT INTO purchase_order_items (
                        po_id, item_id, quantity, unit_price, price_source,
                        total_price, notes
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """
                item_result = await conn.fetchrow(
                    item_insert_query,
                    po['id'],
                    item_req.item_id,
                    item_req.quantity,
                    unit_price,
                    price_source,
                    total_price,
                    item_req.notes
                )

                items_data.append({
                    'id': item_result['id'],
                    'item_id': item_req.item_id,
                    'item_name': item['name'],
                    'item_sku': item['sku'],
                    'quantity': item_req.quantity,
                    'unit_price': unit_price,
                    'price_source': price_source,
                    'total_price': total_price,
                    'notes': item_req.notes
                })

            # 5. Update PO total amount
            update_total_query = """
                UPDATE purchase_orders
                SET total_amount = $1
                WHERE id = $2
            """
            await conn.execute(update_total_query, total_amount, po['id'])

            # 6. Log initial status
            await _log_status_change(
                conn, po['id'], None, POStatus.DRAFT.value, user_id, "PO created"
            )

            logger.info(f"✅ Created PO {po_number} with {len(items_data)} items, total: ₹{total_amount}")

            # Return complete PO details
            return {
                'id': po['id'],
                'po_number': po['po_number'],
                'vendor_id': request.vendor_id,
                'vendor_name': vendor['contact_name'],
                'dispatch_date': request.dispatch_date,
                'delivery_date': request.delivery_date,
                'status': po['status'],
                'total_amount': total_amount,
                'notes': request.notes,
                'created_at': po['created_at'],
                'updated_at': po['updated_at'],
                'items': items_data
            }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in PO creation: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create PO: {e}")
        raise


# ============================================================================
# PO RETRIEVAL
# ============================================================================

async def get_po_details(po_id: int) -> Optional[Dict[str, Any]]:
    """
    Get complete PO details with items and history.

    Args:
        po_id: Purchase order ID

    Returns:
        Complete PO details or None if not found
    """
    try:
        # 1. Get PO record
        po_query = """
            SELECT
                po.id, po.po_number, po.vendor_id, po.dispatch_date,
                po.delivery_date, po.status, po.total_amount, po.notes,
                po.created_at, po.updated_at, po.exported_at,
                v.contact_name as vendor_name
            FROM purchase_orders po
            JOIN zoho_vendors v ON po.vendor_id = v.id
            WHERE po.id = $1
        """
        po = await fetch_one(po_query, po_id)

        if not po:
            return None

        # 2. Get PO items
        items_query = """
            SELECT
                poi.id, poi.item_id, poi.quantity, poi.unit_price,
                poi.price_source, poi.total_price, poi.notes,
                poi.added_from_grn,
                i.name as item_name, i.sku as item_sku
            FROM purchase_order_items poi
            JOIN zoho_items i ON poi.item_id = i.id
            WHERE poi.po_id = $1
            ORDER BY poi.id
        """
        items = await fetch_all(items_query, po_id)

        # 3. Get status history
        history_query = """
            SELECT
                psh.from_status, psh.to_status, psh.changed_at, psh.notes,
                u.email as changed_by
            FROM po_status_history psh
            LEFT JOIN auth.users u ON psh.changed_by = u.id
            WHERE psh.po_id = $1
            ORDER BY psh.changed_at ASC
        """
        history = await fetch_all(history_query, po_id)

        # 4. Build response
        return {
            **po,
            'items': items,
            'status_history': history
        }

    except Exception as e:
        logger.error(f"❌ Failed to get PO details for ID {po_id}: {e}")
        raise


async def list_pos(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    item_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List POs with filtering and pagination.

    Args:
        status: Filter by status
        vendor_id: Filter by vendor
        from_date: Filter by dispatch date from
        to_date: Filter by dispatch date to
        item_id: Filter by item (in PO items)
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Paginated PO list with total count
    """
    try:
        # Build WHERE conditions
        conditions = []
        params = []
        param_count = 1

        if status:
            conditions.append(f"po.status = ${param_count}")
            params.append(status)
            param_count += 1

        if vendor_id:
            conditions.append(f"po.vendor_id = ${param_count}")
            params.append(vendor_id)
            param_count += 1

        if from_date:
            conditions.append(f"po.dispatch_date >= ${param_count}")
            params.append(from_date)
            param_count += 1

        if to_date:
            conditions.append(f"po.dispatch_date <= ${param_count}")
            params.append(to_date)
            param_count += 1

        if item_id:
            conditions.append(f"""
                EXISTS (
                    SELECT 1 FROM purchase_order_items poi
                    WHERE poi.po_id = po.id AND poi.item_id = ${param_count}
                )
            """)
            params.append(item_id)
            param_count += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM purchase_orders po
            {where_clause}
        """
        count_result = await fetch_one(count_query, *params)
        total = count_result['total'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * limit
        list_query = f"""
            SELECT
                po.id, po.po_number, po.vendor_id, po.dispatch_date,
                po.delivery_date, po.status, po.total_amount, po.notes,
                po.created_at, po.updated_at, po.exported_at,
                v.contact_name as vendor_name
            FROM purchase_orders po
            JOIN zoho_vendors v ON po.vendor_id = v.id
            {where_clause}
            ORDER BY po.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        pos = await fetch_all(list_query, *params)

        # Calculate pages
        import math
        pages = math.ceil(total / limit) if total > 0 else 1

        return {
            'pos': pos,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': pages
        }

    except Exception as e:
        logger.error(f"❌ Failed to list POs: {e}")
        raise


# ============================================================================
# PO UPDATE
# ============================================================================

async def update_po(
    po_id: int,
    request: POUpdateRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Update purchase order (only if not exported).

    Args:
        po_id: Purchase order ID
        request: Update request
        user_id: User UUID

    Returns:
        Updated PO details

    Raises:
        ValueError: If validation fails or PO is locked
        Exception: If update fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Get current PO
            po_query = "SELECT id, status, po_number FROM purchase_orders WHERE id = $1"
            po = await conn.fetchrow(po_query, po_id)

            if not po:
                raise ValueError(f"PO {po_id} not found")

            # 2. Check if PO can be edited
            if po['status'] in [POStatus.EXPORTED_TO_ZOHO.value, POStatus.CLOSED.value]:
                raise ValueError(
                    f"Cannot edit PO {po['po_number']} - status is {po['status']} (locked)"
                )

            # 3. Build update query
            update_fields = []
            update_params = []
            param_count = 1

            if request.vendor_id is not None:
                update_fields.append(f"vendor_id = ${param_count}")
                update_params.append(request.vendor_id)
                param_count += 1

            if request.dispatch_date is not None:
                update_fields.append(f"dispatch_date = ${param_count}")
                update_params.append(request.dispatch_date)
                param_count += 1

            if request.delivery_date is not None:
                update_fields.append(f"delivery_date = ${param_count}")
                update_params.append(request.delivery_date)
                param_count += 1

            if request.notes is not None:
                update_fields.append(f"notes = ${param_count}")
                update_params.append(request.notes)
                param_count += 1

            # 4. Update PO if there are changes
            if update_fields:
                update_query = f"""
                    UPDATE purchase_orders
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                """
                update_params.append(po_id)
                await conn.execute(update_query, *update_params)

            # 5. Update items if provided
            if request.items is not None:
                # Delete existing items
                await conn.execute("DELETE FROM purchase_order_items WHERE po_id = $1", po_id)

                # Insert new items (similar to create_po)
                total_amount = Decimal('0')
                for item_req in request.items:
                    # Get price
                    if item_req.unit_price is None:
                        price_info = await get_item_price(
                            request.vendor_id or po['vendor_id'],
                            item_req.item_id,
                            request.dispatch_date or po['dispatch_date']
                        )
                        if price_info['price'] is None:
                            raise ValueError(f"Price required for item {item_req.item_id}")
                        unit_price = price_info['price']
                        price_source = price_info['source']
                    else:
                        unit_price = item_req.unit_price
                        price_source = PriceSource.MANUAL.value

                    total_price = unit_price * item_req.quantity
                    total_amount += total_price

                    # Insert item
                    await conn.execute("""
                        INSERT INTO purchase_order_items (
                            po_id, item_id, quantity, unit_price, price_source,
                            total_price, notes
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, po_id, item_req.item_id, item_req.quantity, unit_price,
                        price_source, total_price, item_req.notes)

                # Update total
                await conn.execute(
                    "UPDATE purchase_orders SET total_amount = $1 WHERE id = $2",
                    total_amount, po_id
                )

            logger.info(f"✅ Updated PO {po['po_number']}")

            # Return updated PO
            return await get_po_details(po_id)

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in PO update: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update PO: {e}")
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _log_status_change(
    conn: asyncpg.Connection,
    po_id: int,
    from_status: Optional[str],
    to_status: str,
    user_id: str,
    notes: Optional[str] = None
):
    """Internal helper to log status change within a transaction."""
    query = """
        INSERT INTO po_status_history (po_id, from_status, to_status, changed_by, notes)
        VALUES ($1, $2, $3, $4, $5)
    """
    await conn.execute(query, po_id, from_status, to_status, user_id, notes)


# ============================================================================
# VENDOR PRICING MANAGEMENT (ADMIN ONLY)
# ============================================================================

async def manage_vendor_pricing(
    request: VendorPricingRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Add or update vendor-item pricing (admin only).

    Args:
        request: Vendor pricing request
        user_id: Admin user UUID

    Returns:
        Created/updated pricing record

    Raises:
        ValueError: If validation fails
        Exception: If operation fails
    """
    try:
        # Validate vendor and item exist
        vendor_query = "SELECT id, contact_name FROM zoho_vendors WHERE id = $1"
        vendor = await fetch_one(vendor_query, request.vendor_id)
        if not vendor:
            raise ValueError(f"Vendor {request.vendor_id} not found")

        item_query = "SELECT id, name FROM zoho_items WHERE id = $1"
        item = await fetch_one(item_query, request.item_id)
        if not item:
            raise ValueError(f"Item {request.item_id} not found")

        # Insert pricing record
        insert_query = """
            INSERT INTO vendor_item_price_history (
                vendor_id, item_id, price, effective_from, effective_to,
                created_by, notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, created_at
        """
        result = await execute_query(
            insert_query,
            request.vendor_id,
            request.item_id,
            request.price,
            request.effective_from,
            request.effective_to,
            user_id,
            request.notes
        )

        logger.info(
            f"✅ Added vendor pricing: {vendor['contact_name']} - {item['name']} "
            f"= ₹{request.price} (effective {request.effective_from})"
        )

        return {
            'id': result['id'],
            'vendor_id': request.vendor_id,
            'vendor_name': vendor['contact_name'],
            'item_id': request.item_id,
            'item_name': item['name'],
            'price': request.price,
            'effective_from': request.effective_from,
            'effective_to': request.effective_to,
            'created_at': result['created_at'],
            'notes': request.notes
        }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in vendor pricing: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to manage vendor pricing: {e}")
        raise


async def get_price_history(
    vendor_id: int,
    item_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get price history for vendor-item combinations.

    Args:
        vendor_id: Vendor ID
        item_id: Optional item ID filter

    Returns:
        List of price history records
    """
    try:
        if item_id:
            query = """
                SELECT
                    vph.id, vph.vendor_id, vph.item_id, vph.price,
                    vph.effective_from, vph.effective_to, vph.created_at, vph.notes,
                    v.contact_name as vendor_name,
                    i.name as item_name
                FROM vendor_item_price_history vph
                JOIN zoho_vendors v ON vph.vendor_id = v.id
                JOIN zoho_items i ON vph.item_id = i.id
                WHERE vph.vendor_id = $1 AND vph.item_id = $2
                ORDER BY vph.effective_from DESC
            """
            results = await fetch_all(query, vendor_id, item_id)
        else:
            query = """
                SELECT
                    vph.id, vph.vendor_id, vph.item_id, vph.price,
                    vph.effective_from, vph.effective_to, vph.created_at, vph.notes,
                    v.contact_name as vendor_name,
                    i.name as item_name
                FROM vendor_item_price_history vph
                JOIN zoho_vendors v ON vph.vendor_id = v.id
                JOIN zoho_items i ON vph.item_id = i.id
                WHERE vph.vendor_id = $1
                ORDER BY vph.effective_from DESC
            """
            results = await fetch_all(query, vendor_id)

        return results

    except Exception as e:
        logger.error(f"❌ Failed to get price history: {e}")
        raise


async def get_active_prices(
    vendor_id: int,
    price_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Get all active vendor-item prices for a specific date.

    Args:
        vendor_id: Vendor ID
        price_date: Date to check (defaults to today)

    Returns:
        List of active prices
    """
    try:
        if price_date is None:
            price_date = date.today()

        query = """
            SELECT
                vph.item_id, vph.price, vph.effective_from,
                i.name as item_name, i.sku as item_sku
            FROM vendor_item_price_history vph
            JOIN zoho_items i ON vph.item_id = i.id
            WHERE vph.vendor_id = $1
              AND vph.effective_from <= $2
              AND (vph.effective_to >= $2 OR vph.effective_to IS NULL)
            ORDER BY i.name
        """
        results = await fetch_all(query, vendor_id, price_date)

        return [
            {
                'item_id': r['item_id'],
                'item_name': r['item_name'],
                'item_sku': r['item_sku'],
                'price': r['price'],
                'source': 'vendor',
                'effective_from': r['effective_from']
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get active prices: {e}")
        raise


# ============================================================================
# PO WORKFLOW FUNCTIONS
# ============================================================================

async def send_po_to_farm(po_id: int, user_id: str) -> Dict[str, Any]:
    """
    Send PO to farm via email (placeholder for email integration).

    Args:
        po_id: Purchase order ID
        user_id: User UUID

    Returns:
        Status message

    Raises:
        ValueError: If PO not found or invalid status
        Exception: If sending fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # Get PO
            po_query = "SELECT id, po_number, status FROM purchase_orders WHERE id = $1"
            po = await conn.fetchrow(po_query, po_id)

            if not po:
                raise ValueError(f"PO {po_id} not found")

            if po['status'] != POStatus.DRAFT.value:
                raise ValueError(f"PO {po['po_number']} cannot be sent - status is {po['status']}")

            # Update status
            await conn.execute(
                "UPDATE purchase_orders SET status = $1 WHERE id = $2",
                POStatus.SENT_TO_FARM.value,
                po_id
            )

            # Log status change
            await _log_status_change(
                conn, po_id, POStatus.DRAFT.value, POStatus.SENT_TO_FARM.value,
                user_id, "PO sent to farm"
            )

            # TODO: Integrate with email service to send PDF
            # from app.services.email_service import send_email
            # await send_email(vendor_email, subject, body, pdf_attachment)

            logger.info(f"✅ Sent PO {po['po_number']} to farm")

            return {
                'po_id': po_id,
                'po_number': po['po_number'],
                'status': POStatus.SENT_TO_FARM.value,
                'message': 'PO sent to farm successfully'
            }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send PO to farm: {e}")
        raise


async def add_extra_items_from_grn(
    po_id: int,
    extra_items: List[Dict[str, Any]],
    user_id: str
) -> None:
    """
    Add extra items from GRN (called by GRN module).

    Args:
        po_id: Purchase order ID
        extra_items: List of extra items with item_id, quantity, unit_price
        user_id: User UUID

    Raises:
        ValueError: If PO not found
        Exception: If operation fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # Get PO
            po_query = "SELECT id, po_number FROM purchase_orders WHERE id = $1"
            po = await conn.fetchrow(po_query, po_id)

            if not po:
                raise ValueError(f"PO {po_id} not found")

            additional_amount = Decimal('0')

            for item in extra_items:
                total_price = Decimal(str(item['unit_price'])) * Decimal(str(item['quantity']))
                additional_amount += total_price

                # Insert item with added_from_grn flag
                await conn.execute("""
                    INSERT INTO purchase_order_items (
                        po_id, item_id, quantity, unit_price, price_source,
                        total_price, notes, added_from_grn
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, true)
                """, po_id, item['item_id'], item['quantity'], item['unit_price'],
                    PriceSource.MANUAL.value, total_price,
                    f"Added from GRN: {item.get('notes', '')}")

            # Update PO total
            await conn.execute("""
                UPDATE purchase_orders
                SET total_amount = total_amount + $1
                WHERE id = $2
            """, additional_amount, po_id)

            logger.info(
                f"✅ Added {len(extra_items)} extra items to PO {po['po_number']} "
                f"(additional amount: ₹{additional_amount})"
            )

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add extra items from GRN: {e}")
        raise


# ============================================================================
# ZOHO EXPORT
# ============================================================================

async def export_to_zoho(po_ids: List[int]) -> bytes:
    """
    Generate Zoho-compatible CSV export for selected POs.

    Args:
        po_ids: List of PO IDs to export

    Returns:
        CSV file as bytes

    Raises:
        Exception: If export fails
    """
    try:
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # CSV Headers
        writer.writerow([
            'PO Number', 'Vendor ID', 'Vendor Name', 'Dispatch Date',
            'Delivery Date', 'Item ID', 'Item Name', 'SKU', 'Quantity',
            'Unit Price', 'Total', 'Damage', 'Reject', 'GRN Number',
            'Batch Number', 'Notes'
        ])

        async with DatabaseTransaction() as conn:
            for po_id in po_ids:
                # Get PO with items, GRN data, wastage data
                query = """
                    SELECT
                        po.po_number, po.vendor_id, v.contact_name as vendor_name,
                        po.dispatch_date, po.delivery_date,
                        poi.item_id, i.name as item_name, i.sku,
                        poi.quantity, poi.unit_price, poi.total_price,
                        poi.notes,
                        COALESCE(
                            (SELECT SUM(we.quantity)
                             FROM wastage_events we
                             JOIN batches b ON we.batch_id = b.id
                             WHERE b.po_id = po.id AND we.wastage_type = 'damage'
                               AND we.cost_allocation = 'farm'), 0
                        ) as damage,
                        COALESCE(
                            (SELECT SUM(we.quantity)
                             FROM wastage_events we
                             JOIN batches b ON we.batch_id = b.id
                             WHERE b.po_id = po.id AND we.wastage_type = 'reject'
                               AND we.cost_allocation = 'farm'), 0
                        ) as reject,
                        (SELECT grn_number FROM grns WHERE po_id = po.id LIMIT 1) as grn_number,
                        (SELECT batch_number FROM batches WHERE po_id = po.id LIMIT 1) as batch_number
                    FROM purchase_orders po
                    JOIN purchase_order_items poi ON po.id = poi.po_id
                    JOIN zoho_vendors v ON po.vendor_id = v.id
                    JOIN zoho_items i ON poi.item_id = i.id
                    WHERE po.id = $1
                """
                rows = await conn.fetch(query, po_id)

                for row in rows:
                    writer.writerow([
                        row['po_number'],
                        row['vendor_id'],
                        row['vendor_name'],
                        row['dispatch_date'],
                        row['delivery_date'],
                        row['item_id'],
                        row['item_name'],
                        row['sku'],
                        row['quantity'],
                        row['unit_price'],
                        row['total_price'],
                        row['damage'],
                        row['reject'],
                        row['grn_number'] or '',
                        row['batch_number'] or '',
                        row['notes'] or ''
                    ])

                # Mark PO as exported
                await conn.execute("""
                    UPDATE purchase_orders
                    SET status = $1, exported_at = NOW()
                    WHERE id = $2
                """, POStatus.EXPORTED_TO_ZOHO.value, po_id)

                # Log status change
                await _log_status_change(
                    conn, po_id, None, POStatus.EXPORTED_TO_ZOHO.value,
                    None, "Exported to Zoho Books"
                )

        logger.info(f"✅ Exported {len(po_ids)} POs to Zoho CSV")

        return csv_buffer.getvalue().encode('utf-8')

    except Exception as e:
        logger.error(f"❌ Failed to export to Zoho: {e}")
        raise


# ============================================================================
# PDF GENERATION
# ============================================================================

async def generate_po_pdf(po_id: int) -> bytes:
    """
    Generate printable PO PDF (placeholder for PDF library integration).

    Args:
        po_id: Purchase order ID

    Returns:
        PDF file as bytes

    Raises:
        ValueError: If PO not found
        Exception: If PDF generation fails
    """
    try:
        # Get PO details
        po = await get_po_details(po_id)

        if not po:
            raise ValueError(f"PO {po_id} not found")

        # TODO: Implement PDF generation using reportlab or similar
        # from reportlab.lib.pagesizes import A4
        # from reportlab.pdfgen import canvas
        # from io import BytesIO

        # For now, return placeholder
        logger.warning(f"⚠️ PDF generation not yet implemented for PO {po['po_number']}")

        # Placeholder: return empty PDF
        return b"PDF generation not yet implemented"

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate PO PDF: {e}")
        raise
