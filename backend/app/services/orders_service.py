"""
================================================================================
Orders Service - Business Logic Layer (Simplified - API Sync Only)
================================================================================
Version: 2.0.0
Created: 2025-12-07
Updated: 2025-12-07

Description:
    Service layer for Orders module
    - CRUD operations for orders and order items
    - API sync from WooCommerce (no webhooks)
    - Simple, proven approach (like Order Extractor)

Features:
    - Works with raw WooCommerce API dict data
    - Upsert logic (insert or update based on woo_order_id)
    - Automatic customer linking to woo_customers table
    - Order items stored in separate table
    - No complex schema validation
    - Comprehensive error handling and logging

================================================================================
"""

import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import fetch_one, fetch_all, execute_query, get_db
from app.schemas.orders import SyncOrdersResponse
from app.services.woocommerce_service import WooCommerceService

logger = logging.getLogger(__name__)


class OrdersService:
    """Service for managing B2C orders from WooCommerce"""

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    @staticmethod
    async def get_orders(
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get orders with optional filtering

        Args:
            status: Filter by order status
            customer_id: Filter by customer ID
            start_date: Filter by date created (from)
            end_date: Filter by date created (to)
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of order dictionaries
        """
        try:
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            param_count = 0

            if status:
                param_count += 1
                query += f" AND status = ${param_count}"
                params.append(status)

            if customer_id:
                param_count += 1
                query += f" AND customer_id = ${param_count}"
                params.append(customer_id)

            if start_date:
                param_count += 1
                query += f" AND date_created >= ${param_count}"
                params.append(start_date)

            if end_date:
                param_count += 1
                query += f" AND date_created <= ${param_count}"
                params.append(end_date)

            query += " ORDER BY date_created DESC"

            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)

            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)

            orders = await fetch_all(query, *params)
            return [dict(o) for o in orders]

        except Exception as e:
            logger.error(f"Error fetching orders: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_order_by_id(order_id: int, include_items: bool = True) -> Optional[Dict]:
        """
        Get single order by internal ID

        Args:
            order_id: Internal order ID
            include_items: Whether to include order items

        Returns:
            Order dictionary or None if not found
        """
        try:
            order = await fetch_one("SELECT * FROM orders WHERE id = $1", order_id)

            if not order:
                return None

            order_dict = dict(order)

            # Fetch order items if requested
            if include_items:
                items = await fetch_all(
                    "SELECT * FROM order_items WHERE order_id = $1 ORDER BY id",
                    order_id
                )
                order_dict['line_items'] = [dict(item) for item in items]
            else:
                order_dict['line_items'] = []

            return order_dict

        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def count_orders(
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count orders with optional filtering

        Args:
            status: Filter by order status
            customer_id: Filter by customer ID
            start_date: Filter by date created (from)
            end_date: Filter by date created (to)

        Returns:
            Number of orders matching criteria
        """
        try:
            query = "SELECT COUNT(*) as count FROM orders WHERE 1=1"
            params = []
            param_count = 0

            if status:
                param_count += 1
                query += f" AND status = ${param_count}"
                params.append(status)

            if customer_id:
                param_count += 1
                query += f" AND customer_id = ${param_count}"
                params.append(customer_id)

            if start_date:
                param_count += 1
                query += f" AND date_created >= ${param_count}"
                params.append(start_date)

            if end_date:
                param_count += 1
                query += f" AND date_created <= ${param_count}"
                params.append(end_date)

            result = await fetch_one(query, *params)
            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Error counting orders: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_order_stats() -> Dict[str, Any]:
        """
        Get order statistics

        Returns:
            Dictionary with order counts and revenue stats
        """
        try:
            stats = await fetch_one("""
                SELECT
                    COUNT(*) as total_orders,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending_orders,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing_orders,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_orders,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_orders,
                    COALESCE(SUM(total) FILTER (WHERE status IN ('completed', 'processing')), 0) as total_revenue,
                    COALESCE(AVG(total) FILTER (WHERE status IN ('completed', 'processing')), 0) as average_order_value
                FROM orders
            """)

            return dict(stats) if stats else {}

        except Exception as e:
            logger.error(f"Error fetching order stats: {e}", exc_info=True)
            raise

    @staticmethod
    async def update_order_status(order_id: int, status: str) -> Dict:
        """
        Update order status

        Args:
            order_id: Internal order ID
            status: New status value

        Returns:
            Updated order dictionary
        """
        try:
            # Validate status
            valid_statuses = ['pending', 'processing', 'on-hold', 'completed', 'cancelled', 'refunded', 'failed']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

            # Update status and set completion date if completed
            if status == 'completed':
                order = await fetch_one("""
                    UPDATE orders
                    SET status = $1, date_completed = NOW(), updated_at = NOW()
                    WHERE id = $2
                    RETURNING *
                """, status, order_id)
            else:
                order = await fetch_one("""
                    UPDATE orders
                    SET status = $1, updated_at = NOW()
                    WHERE id = $2
                    RETURNING *
                """, status, order_id)

            if not order:
                raise ValueError(f"Order {order_id} not found")

            return dict(order)

        except Exception as e:
            logger.error(f"Error updating order status: {e}", exc_info=True)
            raise

    # ========================================================================
    # API Sync (Simple, Like Order Extractor)
    # ========================================================================

    @staticmethod
    async def sync_orders_from_woocommerce(days: int = 3, force_full_sync: bool = False) -> SyncOrdersResponse:
        """
        Sync orders from WooCommerce API (simple, proven approach)

        Args:
            days: Number of days to sync (default 3)
            force_full_sync: Force sync all orders regardless of modification date

        Returns:
            SyncOrdersResponse with statistics
        """
        start_time = datetime.now()
        synced = 0
        created = 0
        updated = 0
        skipped = 0
        errors = 0

        try:
            logger.info(f"Starting WooCommerce order sync (last {days} days)")

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            # Fetch orders from WooCommerce API (returns raw dict data - proven to work!)
            woo_orders = await WooCommerceService.fetch_orders(
                start_date=start_date,
                end_date=end_date,
                status="any"  # Fetch all statuses
            )

            logger.info(f"Fetched {len(woo_orders)} orders from WooCommerce API")

            # Process each order (simple dict processing, no complex validation)
            for woo_order in woo_orders:
                try:
                    # Check if order exists
                    existing = await fetch_one(
                        "SELECT id FROM orders WHERE woo_order_id = $1",
                        woo_order.get('id')
                    )

                    # Insert or update order
                    await OrdersService._save_order_to_database(woo_order)

                    if existing:
                        updated += 1
                    else:
                        created += 1

                    synced += 1

                except Exception as e:
                    logger.error(f"Error syncing order {woo_order.get('id')}: {e}", exc_info=True)
                    errors += 1

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Sync completed: {synced} synced ({created} created, {updated} updated), {errors} errors in {duration:.2f}s")

            return SyncOrdersResponse(
                synced=synced,
                created=created,
                updated=updated,
                skipped=skipped,
                errors=errors,
                sync_duration_seconds=round(duration, 2),
                sync_source="api"
            )

        except Exception as e:
            logger.error(f"Error syncing orders from WooCommerce: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            return SyncOrdersResponse(
                synced=synced,
                created=created,
                updated=updated,
                skipped=skipped,
                errors=errors + 1,
                sync_duration_seconds=round(duration, 2),
                sync_source="api"
            )

    @staticmethod
    async def _save_order_to_database(woo_order: Dict[str, Any]) -> int:
        """
        Save order to database (insert or update)
        Works with raw WooCommerce dict data - no schema validation!

        Args:
            woo_order: Raw WooCommerce order dict from API

        Returns:
            Internal order ID
        """
        pool = get_db()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Extract basic order data (safely with .get())
                woo_order_id = woo_order.get('id')
                order_number = woo_order.get('number') or woo_order.get('order_number') or str(woo_order_id)
                status = woo_order.get('status', 'pending')

                # Dates
                date_created = OrdersService._parse_datetime(woo_order.get('date_created'))
                date_modified = OrdersService._parse_datetime(woo_order.get('date_modified'))
                date_completed = OrdersService._parse_datetime(woo_order.get('date_completed'))
                date_paid = OrdersService._parse_datetime(woo_order.get('date_paid'))

                # Financial data
                currency = woo_order.get('currency', 'INR')
                total = Decimal(str(woo_order.get('total', 0)))
                total_tax = Decimal(str(woo_order.get('total_tax', 0)))
                shipping_total = Decimal(str(woo_order.get('shipping_total', 0)))
                discount_total = Decimal(str(woo_order.get('discount_total', 0)))
                subtotal = total - total_tax - shipping_total

                # Customer
                customer_id = woo_order.get('customer_id', 0)
                if customer_id == 0:
                    customer_id = None

                # Payment
                payment_method = woo_order.get('payment_method', '')
                payment_method_title = woo_order.get('payment_method_title', '')
                transaction_id = woo_order.get('transaction_id', '')

                # Notes
                customer_note = woo_order.get('customer_note', '')
                created_via = woo_order.get('created_via', '')

                # Billing and shipping (store as-is)
                billing = woo_order.get('billing', {})
                shipping = woo_order.get('shipping', {})
                billing_json = json.dumps(billing)
                shipping_json = json.dumps(shipping)

                # Upsert order
                order_row = await conn.fetchrow("""
                    INSERT INTO orders (
                        woo_order_id, order_number, customer_id, status,
                        date_created, date_modified, date_completed, date_paid,
                        currency, subtotal, total_tax, shipping_total, discount_total, total,
                        payment_method, payment_method_title, transaction_id,
                        customer_note, created_via,
                        billing, shipping,
                        last_synced_at, sync_source
                    )
                    VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7, $8,
                        $9, $10, $11, $12, $13, $14,
                        $15, $16, $17,
                        $18, $19,
                        $20::jsonb, $21::jsonb,
                        NOW(), 'api'
                    )
                    ON CONFLICT (woo_order_id) DO UPDATE SET
                        order_number = EXCLUDED.order_number,
                        customer_id = EXCLUDED.customer_id,
                        status = EXCLUDED.status,
                        date_modified = EXCLUDED.date_modified,
                        date_completed = EXCLUDED.date_completed,
                        date_paid = EXCLUDED.date_paid,
                        currency = EXCLUDED.currency,
                        subtotal = EXCLUDED.subtotal,
                        total_tax = EXCLUDED.total_tax,
                        shipping_total = EXCLUDED.shipping_total,
                        discount_total = EXCLUDED.discount_total,
                        total = EXCLUDED.total,
                        payment_method = EXCLUDED.payment_method,
                        payment_method_title = EXCLUDED.payment_method_title,
                        transaction_id = EXCLUDED.transaction_id,
                        customer_note = EXCLUDED.customer_note,
                        created_via = EXCLUDED.created_via,
                        billing = EXCLUDED.billing,
                        shipping = EXCLUDED.shipping,
                        last_synced_at = NOW(),
                        updated_at = NOW()
                    RETURNING id
                """,
                    woo_order_id, order_number, customer_id, status,
                    date_created, date_modified, date_completed, date_paid,
                    currency, subtotal, total_tax, shipping_total, discount_total, total,
                    payment_method, payment_method_title, transaction_id,
                    customer_note, created_via,
                    billing_json, shipping_json
                )

                order_id = order_row['id']

                # Delete existing order items (we'll recreate them)
                await conn.execute("DELETE FROM order_items WHERE order_id = $1", order_id)

                # Insert order items (raw dict processing)
                line_items = woo_order.get('line_items', [])
                for item in line_items:
                    # Extract item data safely
                    product_id = item.get('product_id')
                    variation_id = item.get('variation_id')
                    name = item.get('name', 'Unknown Product')
                    sku = item.get('sku', '')
                    quantity = item.get('quantity', 1)
                    price = Decimal(str(item.get('price', 0)))
                    subtotal_item = Decimal(str(item.get('subtotal', 0)))
                    total_item = Decimal(str(item.get('total', 0)))
                    tax_item = Decimal(str(item.get('tax', 0)))

                    # Meta data (convert list to dict if needed)
                    meta_dict = {}
                    meta_data = item.get('meta_data', [])
                    if isinstance(meta_data, list):
                        for meta in meta_data:
                            if isinstance(meta, dict):
                                meta_dict[meta.get('key', '')] = meta.get('value', '')

                    await conn.execute("""
                        INSERT INTO order_items (
                            order_id, product_id, variation_id, name, sku,
                            quantity, price, subtotal, total, tax, meta_data
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                    """,
                        order_id, product_id, variation_id, name, sku,
                        quantity, price, subtotal_item, total_item, tax_item,
                        json.dumps(meta_dict)
                    )

                logger.info(f"Saved order {order_id} (woo_order_id: {woo_order_id}) with {len(line_items)} items")
                return order_id

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string from WooCommerce

        Args:
            dt_str: Datetime string in ISO format

        Returns:
            Datetime object or None
        """
        if not dt_str:
            return None

        try:
            # WooCommerce format: "2025-12-07T10:30:00"
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
            return None
