"""
================================================================================
Orders Service - Business Logic Layer
================================================================================
Version: 1.0.0
Created: 2025-12-07

Description:
    Service layer for Orders module including:
    - CRUD operations for orders and order items
    - WooCommerce webhook processing
    - Scheduled API sync (every 3 hours, last 3 days)
    - Conflict resolution (most recent data wins)

Features:
    - Upsert logic (insert or update based on woo_order_id)
    - Automatic customer linking to woo_customers table
    - Order items stored in separate table
    - HMAC-SHA256 webhook signature validation
    - Comprehensive error handling and logging

================================================================================
"""

import logging
import hmac
import hashlib
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import fetch_one, fetch_all, execute_query, get_db
from app.schemas.orders import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderItemResponse,
    WooCommerceWebhookPayload,
    SyncOrdersResponse
)
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
    async def get_order_by_woo_id(woo_order_id: int, include_items: bool = True) -> Optional[Dict]:
        """
        Get single order by WooCommerce order ID

        Args:
            woo_order_id: WooCommerce order ID
            include_items: Whether to include order items

        Returns:
            Order dictionary or None if not found
        """
        try:
            order = await fetch_one(
                "SELECT * FROM orders WHERE woo_order_id = $1",
                woo_order_id
            )

            if not order:
                return None

            order_dict = dict(order)

            # Fetch order items if requested
            if include_items:
                items = await fetch_all(
                    "SELECT * FROM order_items WHERE order_id = $1 ORDER BY id",
                    order_dict['id']
                )
                order_dict['line_items'] = [dict(item) for item in items]
            else:
                order_dict['line_items'] = []

            return order_dict

        except Exception as e:
            logger.error(f"Error fetching order by woo_id {woo_order_id}: {e}", exc_info=True)
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
    # Webhook Processing
    # ========================================================================

    @staticmethod
    async def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Validate WooCommerce webhook signature using HMAC-SHA256

        Args:
            payload: Raw request body as bytes
            signature: Signature from X-WC-Webhook-Signature header
            secret: Webhook secret from settings

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate HMAC signature
            computed_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()

            # Convert to base64
            import base64
            computed_signature_b64 = base64.b64encode(computed_signature).decode('utf-8')

            # Compare signatures (constant time comparison)
            return hmac.compare_digest(signature, computed_signature_b64)

        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}", exc_info=True)
            return False

    @staticmethod
    async def process_webhook(payload: WooCommerceWebhookPayload, sync_source: str = "webhook") -> Tuple[bool, str, Optional[int]]:
        """
        Process WooCommerce webhook (order.created or order.updated)

        Args:
            payload: WooCommerce webhook payload
            sync_source: Source of sync (webhook, api, manual)

        Returns:
            Tuple of (success, message, order_id)
        """
        try:
            logger.info(f"Processing webhook for WooCommerce order {payload.id}")

            # Check if order already exists
            existing_order = await OrdersService.get_order_by_woo_id(payload.id, include_items=False)

            # Determine if this is create or update
            is_update = existing_order is not None

            # Upsert order (insert or update)
            order_id = await OrdersService._upsert_order_from_woocommerce(payload, sync_source)

            if is_update:
                logger.info(f"Updated order {order_id} from webhook (woo_order_id: {payload.id})")
                return (True, f"Order updated successfully", order_id)
            else:
                logger.info(f"Created order {order_id} from webhook (woo_order_id: {payload.id})")
                return (True, f"Order created successfully", order_id)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return (False, f"Error processing webhook: {str(e)}", None)

    @staticmethod
    async def _upsert_order_from_woocommerce(woo_order: Any, sync_source: str = "webhook") -> int:
        """
        Insert or update order from WooCommerce data

        Args:
            woo_order: WooCommerce order object (webhook payload or API response)
            sync_source: Source of sync (webhook, api, manual)

        Returns:
            Internal order ID
        """
        pool = get_db()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Extract dates
                date_created = OrdersService._parse_datetime(woo_order.date_created)
                date_modified = OrdersService._parse_datetime(woo_order.date_modified) if woo_order.date_modified else None
                date_completed = OrdersService._parse_datetime(woo_order.date_completed) if woo_order.date_completed else None
                date_paid = OrdersService._parse_datetime(woo_order.date_paid) if woo_order.date_paid else None

                # Check if order exists
                existing = await conn.fetchrow(
                    "SELECT id, date_modified FROM orders WHERE woo_order_id = $1",
                    woo_order.id
                )

                # Conflict resolution: Only update if WooCommerce data is newer
                if existing and date_modified:
                    existing_modified = existing['date_modified']
                    if existing_modified and existing_modified >= date_modified:
                        logger.info(f"Skipping order {woo_order.id} - existing data is newer")
                        return existing['id']

                # Prepare billing and shipping as JSONB
                billing_json = json.dumps(woo_order.billing)
                shipping_json = json.dumps(woo_order.shipping)

                # Extract customer_id (can be 0 for guest orders)
                customer_id = woo_order.customer_id if woo_order.customer_id > 0 else None

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
                        NOW(), $22
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
                        sync_source = EXCLUDED.sync_source,
                        updated_at = NOW()
                    RETURNING id
                """,
                    woo_order.id,
                    woo_order.number or str(woo_order.id),
                    customer_id,
                    woo_order.status,
                    date_created,
                    date_modified,
                    date_completed,
                    date_paid,
                    woo_order.currency,
                    Decimal(woo_order.total) - Decimal(woo_order.total_tax or "0.00") - Decimal(woo_order.shipping_total or "0.00"),  # subtotal
                    Decimal(woo_order.total_tax or "0.00"),
                    Decimal(woo_order.shipping_total or "0.00"),
                    Decimal(woo_order.discount_total or "0.00"),
                    Decimal(woo_order.total),
                    woo_order.payment_method or "",
                    woo_order.payment_method_title or "",
                    woo_order.transaction_id or "",
                    woo_order.customer_note or "",
                    woo_order.created_via or "",
                    billing_json,
                    shipping_json,
                    sync_source
                )

                order_id = order_row['id']

                # Delete existing order items (we'll recreate them)
                await conn.execute("DELETE FROM order_items WHERE order_id = $1", order_id)

                # Insert order items
                for item in woo_order.line_items:
                    # Convert meta_data list to dict
                    meta_dict = {}
                    if hasattr(item, 'meta_data') and item.meta_data:
                        for meta in item.meta_data:
                            if isinstance(meta, dict):
                                meta_dict[meta.get('key', '')] = meta.get('value', '')

                    await conn.execute("""
                        INSERT INTO order_items (
                            order_id, product_id, variation_id, name, sku,
                            quantity, price, subtotal, total, tax, meta_data
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                    """,
                        order_id,
                        item.product_id,
                        item.variation_id,
                        item.name,
                        item.sku or "",
                        item.quantity,
                        Decimal(item.price or "0.00"),
                        Decimal(item.subtotal or "0.00"),
                        Decimal(item.total or "0.00"),
                        Decimal(item.tax or "0.00"),
                        json.dumps(meta_dict)
                    )

                logger.info(f"Upserted order {order_id} (woo_order_id: {woo_order.id}) with {len(woo_order.line_items)} items")
                return order_id

    # ========================================================================
    # API Sync
    # ========================================================================

    @staticmethod
    async def sync_orders_from_woocommerce(days: int = 3, force_full_sync: bool = False) -> SyncOrdersResponse:
        """
        Sync orders from WooCommerce API

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
            logger.info(f"Starting WooCommerce order sync (last {days} days, force={force_full_sync})")

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Date range: {start_date} to {end_date}")

            # Fetch orders from WooCommerce
            woo_orders = await WooCommerceService.fetch_orders(
                start_date=start_date,
                end_date=end_date,
                status="any"  # Fetch all statuses
            )

            logger.info(f"Fetched {len(woo_orders)} orders from WooCommerce")

            # Process each order
            for woo_order_data in woo_orders:
                try:
                    # Convert to WooCommerceWebhookPayload schema
                    woo_order = WooCommerceWebhookPayload(**woo_order_data)

                    # Check if order exists
                    existing = await OrdersService.get_order_by_woo_id(woo_order.id, include_items=False)

                    # Upsert order
                    await OrdersService._upsert_order_from_woocommerce(woo_order, sync_source="api")

                    if existing:
                        updated += 1
                    else:
                        created += 1

                    synced += 1

                except Exception as e:
                    logger.error(f"Error syncing order {woo_order_data.get('id')}: {e}", exc_info=True)
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
            # Re-raise the exception so the frontend gets the actual error message
            raise Exception(f"Failed to sync orders from WooCommerce: {str(e)}")

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
