"""
================================================================================
WooCommerce Checkout Service
================================================================================
Version: 1.0.0
Created: 2025-12-04

Description:
    Service layer for WooCommerce checkout functionality
    - Place orders via WooCommerce REST API
    - Map users to WooCommerce customers
    - Handle order creation with line items

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
    async def create_order(
        user_id: int,
        line_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a WooCommerce order for a user
        
        Args:
            user_id: Internal user ID
            line_items: List of line items with product_id, quantity, variation_id
            
        Returns:
            WooCommerce order response dictionary
            
        Raises:
            ValueError: If user has no WooCommerce customer mapping
            Exception: If order creation fails
        """
        # 1. Get WooCommerce customer ID
        wc_customer_id = await WooCheckoutService.get_wc_customer_id(user_id)
        
        if not wc_customer_id:
            raise ValueError(
                "No WooCommerce customer mapping found for this user. "
                "Please contact support to link your account."
            )
        
        # 2. Get WooCommerce API credentials
        api_url, consumer_key, consumer_secret = await WooCommerceService.get_api_credentials()
        
        # 3. Build WooCommerce order payload
        wc_line_items = []
        for item in line_items:
            line_item = {
                "product_id": item["product_id"],
                "quantity": item["quantity"]
            }
            
            # Add variation_id if present
            if item.get("variation_id"):
                line_item["variation_id"] = item["variation_id"]
            
            wc_line_items.append(line_item)
        
        order_payload = {
            "customer_id": wc_customer_id,
            "set_paid": False,  # Order will be pending payment
            "line_items": wc_line_items,
            "status": "pending"
        }
        
        # 4. Create order via WooCommerce API
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
