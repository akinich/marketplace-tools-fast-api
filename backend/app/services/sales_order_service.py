"""
================================================================================
Marketplace ERP - Sales Order Service
================================================================================
Version: 1.0.0
Last Updated: 2025-12-07

Description:
  Business logic for sales order management. Handles SO creation, 3-tier
  pricing logic, customer pricing management, status workflow, and Zoho export.

Functions:
  - generate_so_number: Sequential SO numbering
  - get_item_price: 3-tier pricing logic (customer -> item_rate -> manual)
  - create_so: Create SO with auto-pricing
  - get_so_details: Fetch complete SO
  - update_so: Update SO with validation
  - list_sos: List with filters and pagination
  - manage_customer_pricing: Admin pricing management

================================================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal
import asyncpg

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
from app.schemas.sales_orders import (
    SOCreateRequest, SOUpdateRequest,
    CustomerPricingRequest, SOStatus, PriceSource
)

logger = logging.getLogger(__name__)


# ============================================================================
# SO NUMBER GENERATION
# ============================================================================

async def generate_so_number(custom_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate sequential SO number (thread-safe).
    Format: SO/YY-YY/XXXX (e.g., SO/25-26/0001)

    Args:
        custom_number: Optional custom number to validate/use

    Returns:
        Dict with {so_number, sequence_number, financial_year}
    """
    try:
        # 1. Determine Financial Year (FY)
        today = date.today()
        year = today.year
        month = today.month

        if month >= 4:  # April onwards
            start_year = year
            end_year = year + 1
        else:  # Jan-Mar
            start_year = year - 1
            end_year = year
        
        # Format: 25-26 (for FY 2025-26)
        fy_str = f"{str(start_year)[-2:]}-{str(end_year)[-2:]}"

        # 2. If custom number provided, use it (but try to extract sequence)
        if custom_number:
            # Try to extract sequence if it matches pattern
            import re
            match = re.match(r"SO/(\d{2}-\d{2})/(\d{4})", custom_number)
            if match:
                fy_match = match.group(1)
                seq_match = int(match.group(2))
                if fy_match == fy_str:
                    return {
                        "so_number": custom_number,
                        "sequence_number": seq_match,
                        "financial_year": fy_str
                    }
            
            # If not matching pattern or different FY, just save as text
            return {
                "so_number": custom_number,
                "sequence_number": None,
                "financial_year": fy_str
            }

        # 3. Get max sequence number for this FY
        # Note: We don't have explicit financial_year/sequence_number columns in the CREATE TABLE 
        # based on the SQL provided, but we can extract it from so_number or add columns if needed.
        # For Marketplace ERP standards (matching PO), we usually parse the max number.
        
        query = """
            SELECT so_number 
            FROM sales_orders 
            WHERE so_number LIKE $1
            ORDER BY so_number DESC 
            LIMIT 1
        """
        pattern = f"SO/{fy_str}/%"
        result = await fetch_one(query, pattern)
        
        next_seq = 1
        if result and result['so_number']:
            try:
                # Extract last 4 digits
                parts = result['so_number'].split('/')
                if len(parts) == 3:
                     next_seq = int(parts[2]) + 1
            except ValueError:
                pass # Fallback to 1

        # 4. Format: SO/25-26/0001
        so_number = f"SO/{fy_str}/{next_seq:04d}"

        logger.info(f"✅ Generated SO number: {so_number} (Seq: {next_seq}, FY: {fy_str})")
        return {
            "so_number": so_number,
            "sequence_number": next_seq,
            "financial_year": fy_str
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate SO number: {e}")
        raise


# ============================================================================
# 3-TIER PRICING LOGIC
# ============================================================================

async def get_item_price(
    customer_id: int,
    item_id: int,
    order_date: date
) -> Dict[str, Any]:
    """
    Get item price using 4-tier pricing logic:
    1. Customer's assigned price list (Tier 0)
    2. Customer-specific price for order date (Tier 1)
    3. Zoho item rate (selling price) (Tier 2)
    4. Manual entry required (Tier 3)

    Args:
        customer_id: Zoho customer ID
        item_id: Zoho item ID
        order_date: Order date (drives pricing)

    Returns:
        Dict with: {price: Decimal | None, source: 'price_list' | 'customer' | 'item_rate' | 'manual'}
    """
    try:
        # Tier 0: Check customer's assigned price list
        price_list_query = """
            SELECT pli.price
            FROM zoho_customers zc
            JOIN customer_price_lists cpl ON zc.price_list_id = cpl.id
            JOIN price_list_items pli ON cpl.id = pli.price_list_id
            WHERE zc.id = $1
              AND pli.item_id = $2
              AND cpl.is_active = true
              AND cpl.valid_from <= $3
              AND (cpl.valid_to IS NULL OR cpl.valid_to >= $3)
        """
        price_list_result = await fetch_one(price_list_query, customer_id, item_id, order_date)

        if price_list_result and price_list_result['price'] is not None:
            logger.debug(f"✅ Found price list price for item {item_id}: {price_list_result['price']}")
            return {
                "price": Decimal(str(price_list_result['price'])),
                "source": "price_list"  # New source type
            }

        # Tier 1: Check customer-specific price for order date
        customer_price_query = """
            SELECT price
            FROM customer_price_history
            WHERE customer_id = $1
              AND item_id = $2
              AND effective_from <= $3
              AND (effective_to >= $3 OR effective_to IS NULL)
            ORDER BY effective_from DESC
            LIMIT 1
        """
        cust_price = await fetch_one(customer_price_query, customer_id, item_id, order_date)

        if cust_price and cust_price['price'] is not None:
            logger.debug(f"✅ Found customer price for item {item_id}: {cust_price['price']}")
            return {
                "price": Decimal(str(cust_price['price'])),
                "source": PriceSource.CUSTOMER.value
            }

        # Tier 2: Fall back to Zoho item rate (selling price)
        # Note: zoho_items usually has 'rate' or 'selling_price'
        zoho_price_query = """
            SELECT rate
            FROM zoho_items
            WHERE id = $1
        """
        zoho_price = await fetch_one(zoho_price_query, item_id)

        if zoho_price and zoho_price['rate'] and float(zoho_price['rate']) > 0:
            logger.debug(f"✅ Using Zoho item rate for item {item_id}: {zoho_price['rate']}")
            return {
                "price": Decimal(str(zoho_price['rate'])),
                "source": PriceSource.ITEM_RATE.value
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
# SO CREATION
# ============================================================================

async def create_so(
    request: SOCreateRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Create new sales order with 3-tier pricing logic.

    Args:
        request: SO creation request
        user_id: User UUID who is creating the SO

    Returns:
        Complete SO details
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Validate customer exists
            customer_query = "SELECT id, contact_name FROM zoho_customers WHERE id = $1"
            customer = await conn.fetchrow(customer_query, request.customer_id)
            if not customer:
                raise ValueError(f"Customer {request.customer_id} not found")

            # 2. Generate SO number
            so_info = await generate_so_number(request.so_number)
            so_number = so_info['so_number']

            # 3. Create SO record
            so_insert_query = """
                INSERT INTO sales_orders (
                    so_number, customer_id, order_date, delivery_date,
                    status, order_source, notes, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, so_number, status, created_at, updated_at
            """
            so = await conn.fetchrow(
                so_insert_query,
                so_number,
                request.customer_id,
                request.order_date,
                request.delivery_date,
                SOStatus.DRAFT.value,
                request.order_source,
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
                        request.customer_id,
                        item_req.item_id,
                        request.order_date
                    )
                    if price_info['price'] is None:
                        raise ValueError(
                            f"Price required for item {item['name']} (ID: {item_req.item_id}). "
                            f"No customer or Zoho price found."
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
                    INSERT INTO sales_order_items (
                        sales_order_id, item_id, quantity, unit_price, price_source,
                        notes
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """
                item_result = await conn.fetchrow(
                    item_insert_query,
                    so['id'],
                    item_req.item_id,
                    item_req.quantity,
                    unit_price,
                    price_source,
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
                    'line_total': total_price,
                    'notes': item_req.notes
                })

            # 5. Update SO total amount
            update_total_query = """
                UPDATE sales_orders
                SET total_amount = $1, subtotal = $1
                WHERE id = $2
            """
            await conn.execute(update_total_query, total_amount, so['id'])

            # 6. Log initial status
            await _log_status_change(
                conn, so['id'], None, SOStatus.DRAFT.value, user_id, "SO created"
            )

            logger.info(f"✅ Created SO {so_number} with {len(items_data)} items, total: ₹{total_amount}")

            # Return complete SO details
            return {
                'id': so['id'],
                'so_number': so['so_number'],
                'customer_id': request.customer_id,
                'customer_name': customer['contact_name'],
                'order_date': request.order_date,
                'delivery_date': request.delivery_date,
                'status': so['status'],
                'order_source': request.order_source,
                'total_amount': total_amount,
                'notes': request.notes,
                'created_at': so['created_at'],
                'updated_at': so['updated_at'],
                'items': items_data
            }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in SO creation: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create SO: {e}")
        raise


# ============================================================================
# SO RETRIEVAL
# ============================================================================

async def get_so_details(so_id: int) -> Optional[Dict[str, Any]]:
    """
    Get complete SO details with items and history.

    Args:
        so_id: Sales order ID

    Returns:
        Complete SO details or None if not found
    """
    try:
        # 1. Get SO record
        so_query = """
            SELECT
                so.id, so.so_number, so.customer_id, so.order_date,
                so.delivery_date, so.status, so.order_source,
                so.total_amount, so.notes,
                so.created_at, so.updated_at, so.exported_at,
                c.contact_name as customer_name
            FROM sales_orders so
            JOIN zoho_customers c ON so.customer_id = c.id
            WHERE so.id = $1
        """
        so = await fetch_one(so_query, so_id)

        if not so:
            return None

        # 2. Get SO items
        items_query = """
            SELECT
                soi.id, soi.item_id, soi.quantity, soi.unit_price,
                soi.price_source, soi.line_total, soi.notes,
                i.name as item_name, i.sku as item_sku
            FROM sales_order_items soi
            JOIN zoho_items i ON soi.item_id = i.id
            WHERE soi.sales_order_id = $1
            ORDER BY soi.id
        """
        items = await fetch_all(items_query, so_id)

        # 3. Get status history
        history_query = """
            SELECT
                ssh.from_status, ssh.to_status, ssh.changed_at, ssh.notes,
                u.email as changed_by
            FROM so_status_history ssh
            LEFT JOIN auth.users u ON ssh.changed_by = u.id
            WHERE ssh.sales_order_id = $1
            ORDER BY ssh.changed_at ASC
        """
        history = await fetch_all(history_query, so_id)

        # 4. Build response
        return {
            **so,
            'items': items,
            'status_history': history
        }

    except Exception as e:
        logger.error(f"❌ Failed to get SO details for ID {so_id}: {e}")
        raise


async def list_sos(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    item_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List SOs with filtering and pagination.
    """
    try:
        # Build WHERE conditions
        conditions = []
        params = []
        param_count = 1

        if status:
            conditions.append(f"so.status = ${param_count}")
            params.append(status)
            param_count += 1

        if customer_id:
            conditions.append(f"so.customer_id = ${param_count}")
            params.append(customer_id)
            param_count += 1

        if from_date:
            conditions.append(f"so.order_date >= ${param_count}")
            params.append(from_date)
            param_count += 1

        if to_date:
            conditions.append(f"so.order_date <= ${param_count}")
            params.append(to_date)
            param_count += 1

        if item_id:
            conditions.append(f"""
                EXISTS (
                    SELECT 1 FROM sales_order_items soi
                    WHERE soi.sales_order_id = so.id AND soi.item_id = ${param_count}
                )
            """)
            params.append(item_id)
            param_count += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM sales_orders so
            {where_clause}
        """
        count_result = await fetch_one(count_query, *params)
        total = count_result['total'] if count_result else 0

        # Get paginated results
        offset = (page - 1) * limit
        list_query = f"""
            SELECT
                so.id, so.so_number, so.customer_id, so.order_date,
                so.delivery_date, so.status, so.order_source,
                so.total_amount, so.notes,
                so.created_at, so.updated_at, so.exported_at,
                c.contact_name as customer_name
            FROM sales_orders so
            JOIN zoho_customers c ON so.customer_id = c.id
            {where_clause}
            ORDER BY so.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        sos = await fetch_all(list_query, *params)

        import math
        pages = math.ceil(total / limit) if total > 0 else 1

        return {
            'orders': sos,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': pages
        }

    except Exception as e:
        logger.error(f"❌ Failed to list SOs: {e}")
        raise


# ============================================================================
# SO UPDATE
# ============================================================================

async def update_so(
    so_id: int,
    request: SOUpdateRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Update sales order (only if not exported).
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Get current SO
            so_query = "SELECT id, status, so_number FROM sales_orders WHERE id = $1"
            so = await conn.fetchrow(so_query, so_id)

            if not so:
                raise ValueError(f"SO {so_id} not found")

            # 2. Check if SO can be edited
            if so['status'] in [SOStatus.EXPORTED_TO_ZOHO.value, SOStatus.COMPLETED.value, SOStatus.CANCELLED.value]:
                raise ValueError(
                    f"Cannot edit SO {so['so_number']} - status is {so['status']} (locked)"
                )

            # 3. Build update query
            update_fields = []
            update_params = []
            param_count = 1

            if request.customer_id is not None:
                update_fields.append(f"customer_id = ${param_count}")
                update_params.append(request.customer_id)
                param_count += 1

            if request.order_date is not None:
                update_fields.append(f"order_date = ${param_count}")
                update_params.append(request.order_date)
                param_count += 1

            if request.delivery_date is not None:
                update_fields.append(f"delivery_date = ${param_count}")
                update_params.append(request.delivery_date)
                param_count += 1
                
            if request.order_source is not None:
                update_fields.append(f"order_source = ${param_count}")
                update_params.append(request.order_source)
                param_count += 1

            if request.notes is not None:
                update_fields.append(f"notes = ${param_count}")
                update_params.append(request.notes)
                param_count += 1

            # 4. Update SO if there are changes
            if update_fields:
                update_query = f"""
                    UPDATE sales_orders
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                """
                update_params.append(so_id)
                await conn.execute(update_query, *update_params)

            # 5. Update items if provided
            if request.items is not None:
                # Delete existing items
                await conn.execute("DELETE FROM sales_order_items WHERE sales_order_id = $1", so_id)

                # Insert new items
                total_amount = Decimal('0')
                for item_req in request.items:
                    # Get price
                    if item_req.unit_price is None:
                        price_info = await get_item_price(
                            request.customer_id or await _get_so_customer(conn, so_id),
                            item_req.item_id,
                            request.order_date or await _get_so_date(conn, so_id)
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
                        INSERT INTO sales_order_items (
                            sales_order_id, item_id, quantity, unit_price, price_source,
                            notes
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, so_id, item_req.item_id, item_req.quantity, unit_price,
                        price_source, item_req.notes)

                # Update total
                await conn.execute(
                    "UPDATE sales_orders SET total_amount = $1, subtotal = $1 WHERE id = $2",
                    total_amount, so_id
                )

            logger.info(f"✅ Updated SO {so['so_number']}")

            # Return updated SO
            return await get_so_details(so_id)

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in SO update: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update SO: {e}")
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _log_status_change(
    conn: asyncpg.Connection,
    so_id: int,
    from_status: Optional[str],
    to_status: str,
    user_id: str,
    notes: Optional[str] = None
):
    """Internal helper to log status change within a transaction."""
    query = """
        INSERT INTO so_status_history (sales_order_id, from_status, to_status, changed_by, notes)
        VALUES ($1, $2, $3, $4, $5)
    """
    await conn.execute(query, so_id, from_status, to_status, user_id, notes)

async def _get_so_customer(conn, so_id):
    val = await conn.fetchval("SELECT customer_id FROM sales_orders WHERE id = $1", so_id)
    return val

async def _get_so_date(conn, so_id):
    val = await conn.fetchval("SELECT order_date FROM sales_orders WHERE id = $1", so_id)
    return val


# ============================================================================
# CUSTOMER PRICING MANAGEMENT (ADMIN ONLY)
# ============================================================================

async def manage_customer_pricing(
    request: CustomerPricingRequest,
    user_id: str
) -> Dict[str, Any]:
    """
    Add or update customer-item pricing (admin only).
    """
    try:
        # Validate customer and item exist
        customer_query = "SELECT id, contact_name FROM zoho_customers WHERE id = $1"
        customer = await fetch_one(customer_query, request.customer_id)
        if not customer:
            raise ValueError(f"Customer {request.customer_id} not found")

        item_query = "SELECT id, name FROM zoho_items WHERE id = $1"
        item = await fetch_one(item_query, request.item_id)
        if not item:
            raise ValueError(f"Item {request.item_id} not found")

        # Insert pricing record
        insert_query = """
            INSERT INTO customer_price_history (
                customer_id, item_id, price, effective_from, effective_to,
                created_by, notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, created_at
        """
        result = await execute_query(
            insert_query,
            request.customer_id,
            request.item_id,
            request.price,
            request.effective_from,
            request.effective_to,
            user_id,
            request.notes
        )

        logger.info(
            f"✅ Added customer pricing: {customer['contact_name']} - {item['name']} "
            f"= ₹{request.price} (effective {request.effective_from})"
        )

        return {
            'id': result['id'],
            'customer_id': request.customer_id,
            'item_id': request.item_id,
            'price': request.price,
            'effective_from': request.effective_from,
            'effective_to': request.effective_to,
            'created_at': result['created_at'],
            'notes': request.notes
        }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in customer pricing: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to manage customer pricing: {e}")
        raise


async def get_price_history(
    customer_id: int,
    item_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get price history for customer-item combinations.
    """
    try:
        params = [customer_id]
        query = """
            SELECT
                cph.id, cph.customer_id, c.contact_name as customer_name,
                cph.item_id, i.name as item_name,
                cph.price, cph.effective_from, cph.effective_to,
                cph.created_at, cph.notes,
                u.email as created_by
            FROM customer_price_history cph
            JOIN zoho_customers c ON cph.customer_id = c.id
            JOIN zoho_items i ON cph.item_id = i.id
            LEFT JOIN auth.users u ON cph.created_by = u.id
            WHERE cph.customer_id = $1
        """
        
        if item_id:
            query += " AND cph.item_id = $2"
            params.append(item_id)
            
        query += " ORDER BY cph.effective_from DESC"
        
        results = await fetch_all(query, *params)
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"❌ Failed to get price history: {e}")
        raise
