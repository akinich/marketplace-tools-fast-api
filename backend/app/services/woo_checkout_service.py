"""
================================================================================
WooCommerce Checkout Service
================================================================================
Version: 2.0.0
Updated: 2025-12-04

Description:
    Service layer for WooCommerce checkout functionality
    - Place orders via WooCommerce REST API
    - Map users to WooCommerce customers
    - Handle order creation with line items, custom pricing, shipping
    - Deduct stock after order placement
    - Add origin metadata for tracking

================================================================================
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from asyncpg import Connection

from app.database import fetch_one, execute_query
from app.services.woocommerce_service import WooCommerceService

logger = logging.getLogger(__name__)


class WooCheckoutService:
    """Service for WooCommerce checkout operations"""

    @staticmethod
    async def get_wc_customer_id(user_id: int) -> Optional[int]:
        """
        Get WooCommerce customer ID for a user

        Args:
            user_id: Internal user ID

        Returns:
            WooCommerce customer ID if exists, None otherwise
        """
        result = await fetch_one(
            "SELECT wc_customer_id FROM user_profiles WHERE id = $1",
            user_id
        )

        if result and result.get('wc_customer_id'):
            return result['wc_customer_id']

        return None

    @staticmethod
    async def get_customer_details(wc_customer_id: int) -> Optional[Dict]:
        """
        Get customer billing and shipping details from woo_customers table

        Args:
            wc_customer_id: WooCommerce customer ID

        Returns:
            Customer details dictionary with billing and shipping info
        """
        result = await fetch_one(
            """
            SELECT
                first_name, last_name, email,
                billing_first_name, billing_last_name, billing_company,
                billing_address_1, billing_address_2, billing_city,
                billing_state, billing_postcode, billing_country,
                billing_email, billing_phone,
                shipping_first_name, shipping_last_name, shipping_company,
                shipping_address_1, shipping_address_2, shipping_city,
                shipping_state, shipping_postcode, shipping_country
            FROM woo_customers
            WHERE customer_id = $1
            """,
            wc_customer_id
        )

        return dict(result) if result else None

    @staticmethod
    async def deduct_stock(product_id: int, variation_id: Optional[int], quantity: int) -> bool:
        """
        Deduct stock quantity from products table after order placement

        Args:
            product_id: WooCommerce product ID
            variation_id: WooCommerce variation ID (if applicable)
            quantity: Quantity to deduct

        Returns:
            True if stock deducted successfully, False otherwise
        """
        try:
            if variation_id:
                # Deduct stock for variation
                await execute_query(
                    """
                    UPDATE products
                    SET stock_quantity = GREATEST(0, stock_quantity - $1),
                        updated_at = NOW()
                    WHERE product_id = $2 AND variation_id = $3
                    """,
                    quantity,
                    product_id,
                    variation_id
                )
            else:
                # Deduct stock for simple product
                await execute_query(
                    """
                    UPDATE products
                    SET stock_quantity = GREATEST(0, stock_quantity - $1),
                        updated_at = NOW()
                    WHERE product_id = $2 AND variation_id IS NULL
                    """,
                    quantity,
                    product_id
                )

            logger.info(f"Deducted {quantity} stock from product {product_id}, variation {variation_id}")
            return True

        except Exception as e:
            logger.error(f"Error deducting stock for product {product_id}: {e}")
            return False

    @staticmethod
    async def create_order(
        user_id: int,
        line_items: List[Dict[str, Any]],
        wc_customer_id: Optional[int] = None,
        shipping_total: Optional[float] = 0,
        customer_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a WooCommerce order for a user

        Args:
            user_id: Internal user ID
            line_items: List of line items with product_id, quantity, variation_id, price
            wc_customer_id: Optional WooCommerce customer ID override
            shipping_total: Shipping charges
            customer_note: Customer notes for the order

        Returns:
            WooCommerce order response dictionary

        Raises:
            ValueError: If user has no WooCommerce customer mapping and no override provided
            Exception: If order creation fails
        """
        # 1. Get WooCommerce customer ID (use override if provided)
        if wc_customer_id is None:
            wc_customer_id = await WooCheckoutService.get_wc_customer_id(user_id)

        if not wc_customer_id:
            raise ValueError(
                "No WooCommerce customer ID provided. "
                "Please select a customer or contact support to link your account."
            )

        # 2. Get customer billing/shipping details
        customer_details = await WooCheckoutService.get_customer_details(wc_customer_id)

        # 3. Get WooCommerce API credentials
        api_url, consumer_key, consumer_secret = await WooCommerceService.get_api_credentials()

        # 4. Build WooCommerce order payload with line items
        wc_line_items = []
        for item in line_items:
            line_item = {
                "product_id": item["product_id"],
                "quantity": item["quantity"]
            }

            # Add variation_id if present
            if item.get("variation_id"):
                line_item["variation_id"] = item["variation_id"]

            # Add custom price if provided
            if item.get("price") is not None:
                line_item["price"] = str(item["price"])

            wc_line_items.append(line_item)

        # 5. Build complete order payload
        order_payload = {
            "customer_id": wc_customer_id,
            "set_paid": False,  # Order will be pending payment
            "line_items": wc_line_items,
            "status": "pending"
        }

        # Add billing details if available
        if customer_details:
            order_payload["billing"] = {
                "first_name": customer_details.get('billing_first_name') or customer_details.get('first_name') or '',
                "last_name": customer_details.get('billing_last_name') or customer_details.get('last_name') or '',
                "company": customer_details.get('billing_company') or '',
                "address_1": customer_details.get('billing_address_1') or '',
                "address_2": customer_details.get('billing_address_2') or '',
                "city": customer_details.get('billing_city') or '',
                "state": customer_details.get('billing_state') or '',
                "postcode": customer_details.get('billing_postcode') or '',
                "country": customer_details.get('billing_country') or '',
                "email": customer_details.get('billing_email') or customer_details.get('email') or '',
                "phone": customer_details.get('billing_phone') or ''
            }

            # Add shipping details if available
            order_payload["shipping"] = {
                "first_name": customer_details.get('shipping_first_name') or customer_details.get('first_name') or '',
                "last_name": customer_details.get('shipping_last_name') or customer_details.get('last_name') or '',
                "company": customer_details.get('shipping_company') or '',
                "address_1": customer_details.get('shipping_address_1') or '',
                "address_2": customer_details.get('shipping_address_2') or '',
                "city": customer_details.get('shipping_city') or '',
                "state": customer_details.get('shipping_state') or '',
                "postcode": customer_details.get('shipping_postcode') or '',
                "country": customer_details.get('shipping_country') or ''
            }

        # Add shipping charges if provided
        if shipping_total and shipping_total > 0:
            order_payload["shipping_lines"] = [
                {
                    "method_id": "flat_rate",
                    "method_title": "Shipping",
                    "total": str(shipping_total)
                }
            ]

        # Add customer note if provided
        if customer_note:
            order_payload["customer_note"] = customer_note

        # Add origin metadata to track orders from mkterp
        order_payload["meta_data"] = [
            {
                "key": "_order_source",
                "value": "mkterp"
            },
            {
                "key": "_created_via",
                "value": "mkterp"
            }
        ]

        # 6. Create order via WooCommerce API
        try:
            transport = httpx.HTTPTransport(retries=2)
            client = httpx.Client(
                auth=(consumer_key, consumer_secret),
                transport=transport,
                timeout=30.0
            )

            response = client.post(
                f"{api_url}/orders",
                json=order_payload
            )

            client.close()

            if response.status_code == 201:
                order_data = response.json()
                logger.info(f"Created WooCommerce order {order_data['id']} for user {user_id}")

                # 7. Deduct stock for all line items
                for item in line_items:
                    await WooCheckoutService.deduct_stock(
                        product_id=item["product_id"],
                        variation_id=item.get("variation_id"),
                        quantity=item["quantity"]
                    )

                return order_data
            else:
                error_msg = f"WooCommerce API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(f"Failed to create order: {response.status_code}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating order: {str(e)}", exc_info=True)
            raise Exception("Unable to connect to WooCommerce API")
        except Exception as e:
            logger.error(f"Error creating WooCommerce order: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def check_customer_status(user_id: int) -> Dict[str, Any]:
        """
        Check if user has WooCommerce customer mapping

        Args:
            user_id: Internal user ID

        Returns:
            Dictionary with status information
        """
        wc_customer_id = await WooCheckoutService.get_wc_customer_id(user_id)

        if wc_customer_id:
            return {
                "has_wc_customer_id": True,
                "wc_customer_id": wc_customer_id,
                "message": "User is mapped to WooCommerce customer"
            }
        else:
            return {
                "has_wc_customer_id": False,
                "wc_customer_id": None,
                "message": "User is not mapped to a WooCommerce customer"
            }
