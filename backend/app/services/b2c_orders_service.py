"""
================================================================================
B2C Orders Service - Business Logic Layer
================================================================================
Version: 1.0.0
Created: 2025-12-09

Description:
    Service layer for B2C Orders module
    - Save WooCommerce orders to database
    - Retrieve orders from database
    - UPSERT logic for syncing

================================================================================
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import json

from app.database import fetch_one, fetch_all, execute_query

logger = logging.getLogger(__name__)


class B2COrdersService:
    """Service for managing B2C orders"""

    @staticmethod
    async def save_order_to_database(order_data: Dict[str, Any]) -> int:
        """
        Save or update a single order in the database
        
        Args:
            order_data: WooCommerce order dictionary
            
        Returns:
            order_id: Database order ID
        """
        try:
            # Extract order fields
            woo_order_id = order_data.get('id')
            order_number = order_data.get('order_number', order_data.get('number', str(woo_order_id)))
            status = order_data.get('status', 'pending')
            
            # Dates
            date_created = datetime.fromisoformat(order_data['date_created'].replace('Z', '+00:00'))
            date_modified = datetime.fromisoformat(order_data['date_modified'].replace('Z', '+00:00')) if order_data.get('date_modified') else None
            date_completed = datetime.fromisoformat(order_data['date_completed'].replace('Z', '+00:00')) if order_data.get('date_completed') else None
            date_paid = datetime.fromisoformat(order_data['date_paid'].replace('Z', '+00:00')) if order_data.get('date_paid') else None
            
            # Financial
            currency = order_data.get('currency', 'INR')
            subtotal = Decimal(str(order_data.get('subtotal', 0)))
            total_tax = Decimal(str(order_data.get('total_tax', 0)))
            shipping_total = Decimal(str(order_data.get('shipping_total', 0)))
            discount_total = Decimal(str(order_data.get('discount_total', 0)))
            total = Decimal(str(order_data.get('total', 0)))
            
            # Payment
            payment_method = order_data.get('payment_method', '')
            payment_method_title = order_data.get('payment_method_title', '')
            transaction_id = order_data.get('transaction_id', '')
            
            # Notes
            customer_note = order_data.get('customer_note', '')
            created_via = order_data.get('created_via', 'woocommerce')
            
            # Addresses (store as JSONB)
            billing = order_data.get('billing', {})
            shipping = order_data.get('shipping', {})
            
            # Get customer_id if exists
            customer_id = None
            if billing.get('email'):
                customer_row = await fetch_one(
                    "SELECT customer_id FROM woo_customers WHERE email = $1",
                    billing['email']
                )
                if customer_row:
                    customer_id = customer_row['customer_id']
            
            # UPSERT order
            order_row = await fetch_one("""
                INSERT INTO orders (
                    woo_order_id, order_number, customer_id, status,
                    date_created, date_modified, date_completed, date_paid,
                    currency, subtotal,total_tax, shipping_total, discount_total, total,
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
                json.dumps(billing), json.dumps(shipping)
            )
            
            order_id = order_row['id']
            
            # Delete existing order items
            await execute_query(
                "DELETE FROM order_items WHERE order_id = $1",
                order_id
            )
            
            # Insert line items
            line_items = order_data.get('line_items', [])
            for item in line_items:
                await execute_query("""
                    INSERT INTO order_items (
                        order_id, product_id, variation_id,
                        name, sku, quantity,
                        price, subtotal, total, tax,
                        meta_data
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                """,
                    order_id,
                    item.get('product_id'),
                    item.get('variation_id'),
                    item.get('name', ''),
                    item.get('sku', ''),
                    item.get('quantity', 1),
                    Decimal(str(item.get('price', 0))),
                    Decimal(str(item.get('subtotal', 0))),
                    Decimal(str(item.get('total', 0))),
                    Decimal(str(item.get('total_tax', 0))),
                    json.dumps(item.get('meta_data', {}))
                )
            
            logger.info(f"Saved order {woo_order_id} (ID: {order_id}) with {len(line_items)} items")
            return order_id
            
        except Exception as e:
            logger.error(f"Error saving order {order_data.get('id')}: {e}", exc_info=True)
            raise

    @staticmethod
    async def save_orders_batch(orders: List[Dict[str, Any]]) -> Dict[str, int]:
        """Save multiple orders to database"""
        created = 0
        updated = 0
        errors = 0
        
        for order_data in orders:
            try:
                woo_order_id = order_data.get('id')
                existing = await fetch_one(
                    "SELECT id FROM orders WHERE woo_order_id = $1",
                    woo_order_id
                )
                
                await B2COrdersService.save_order_to_database(order_data)
                
                if existing:
                    updated += 1
                else:
                    created += 1
                    
            except Exception as e:
                logger.error(f"Error in batch save for order {order_data.get('id')}: {e}")
                errors += 1
        
        return {
            "created": created,
            "updated": updated,
            "errors": errors,
            "total": len(orders)
        }

    @staticmethod
    async def get_orders(
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders from database with optional filtering"""
        where_clauses = []
        params = []
        param_count = 1
        
        if status and status != 'any':
            where_clauses.append(f"o.status = ${param_count}")
            params.append(status)
            param_count += 1
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
            SELECT 
                o.*,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', oi.id,
                            'product_id', oi.product_id,
                            'variation_id', oi.variation_id,
                            'name', oi.name,
                            'sku', oi.sku,
                            'quantity', oi.quantity,
                            'price', oi.price,
                            'subtotal', oi.subtotal,
                            'total', oi.total,
                            'tax', oi.tax
                        )
                    ) FILTER (WHERE oi.id IS NOT NULL),
                    '[]'::json
                ) as line_items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            {where_sql}
            GROUP BY o.id
            ORDER BY o.date_created DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        
        params.extend([limit, offset])
        rows = await fetch_all(query, *params)
        
        # Parse JSON strings to actual objects
        orders = []
        for row in rows:
            order_dict = dict(row)
            
            # Parse billing and shipping from JSON strings to dicts
            if isinstance(order_dict.get('billing'), str):
                order_dict['billing'] = json.loads(order_dict['billing'])
            if isinstance(order_dict.get('shipping'), str):
                order_dict['shipping'] = json.loads(order_dict['shipping'])
            
            # Parse line_items from JSON string to array
            if isinstance(order_dict.get('line_items'), str):
                order_dict['line_items'] = json.loads(order_dict['line_items'])
            
            orders.append(order_dict)
        
        return orders

    @staticmethod
    async def count_orders(status: Optional[str] = None) -> int:
        """Count total orders"""
        if status and status != 'any':
            result = await fetch_one(
                "SELECT COUNT(*) as total FROM orders WHERE status = $1",
                status
            )
        else:
            result = await fetch_one("SELECT COUNT(*) as total FROM orders")
        
        return result['total'] if result else 0

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
        """Get single order with line items"""
        result = await fetch_one("""
            SELECT 
                o.*,
                json_agg(
                    json_build_object(
                        'id', oi.id,
                        'product_id', oi.product_id,
                        'variation_id', oi.variation_id,
                        'name', oi.name,
                        'sku', oi.sku,
                        'quantity', oi.quantity,
                        'price', oi.price,
                        'subtotal', oi.subtotal,
                        'total', oi.total,
                        'tax', oi.tax
                    )
                ) as line_items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = $1
            GROUP BY o.id
        """, order_id)
        
        return dict(result) if result else None
