"""
================================================================================
Marketplace ERP - Pricing Service
================================================================================
Version: 1.0.0
Created: 2025-12-07

Service for managing customer-specific pricing and price lookup logic.
Three-tier pricing logic:
1. Customer specific price (customer_prices table)
2. Item default price (item_master.default_price)
3. Zoho base rate (zoho_items.rate)
================================================================================
"""

from typing import Optional, List, Dict
import logging
from fastapi import HTTPException, status

from app.database import fetch_one, fetch_all, execute_query
from app.schemas.pricing import CustomerPriceCreate, CustomerPriceUpdate, PriceLookupResponse

logger = logging.getLogger(__name__)

async def get_item_price(customer_id: int, item_id: int) -> PriceLookupResponse:
    """
    Get the selling price for an item for a specific customer.
    Logic:
    1. Check customer_prices table.
    2. Check item_master.default_price.
    3. Check item_master -> zoho_items.rate (fallback).
    """
    try:
        # 1. Check Customer Specific Price
        customer_price = await fetch_one(
            """
            SELECT custom_price 
            FROM customer_prices 
            WHERE customer_id = $1 AND item_id = $2
            """,
            customer_id, item_id
        )
        
        if customer_price:
            return PriceLookupResponse(
                item_id=item_id,
                price=float(customer_price['custom_price']),
                source='custom'
            )

        # 2 & 3. Fetch Item Master details (with fallback to Zoho rate linked via sku or just current logic)
        # Note: item_master usually links to zoho_items via SKU or similar, or we might need to look up zoho_item directly if item_master structure implies it.
        # Based on schema v1.0.0, item_master has columns, and v1.9.0 added default_price.
        # We also need to check if item_master links to zoho_items. 
        # Typically item_master.sku = zoho_items.sku.
        
        item_query = """
            SELECT 
                im.default_price, 
                zi.rate as zoho_rate
            FROM item_master im
            LEFT JOIN zoho_items zi ON im.sku = zi.sku
            WHERE im.id = $1
        """
        
        item_data = await fetch_one(item_query, item_id)
        
        if not item_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Item with ID {item_id} not found in master"
            )

        # Check default price
        if item_data['default_price'] is not None and float(item_data['default_price']) > 0:
            return PriceLookupResponse(
                item_id=item_id,
                price=float(item_data['default_price']),
                source='default_price'
            )

        # Check Zoho rate
        if item_data['zoho_rate'] is not None:
             return PriceLookupResponse(
                item_id=item_id,
                price=float(item_data['zoho_rate']),
                source='zoho_rate'
            )
            
        # Fallback if no price found (return 0 or error?)
        # Returning 0 allows editing in frontend
        return PriceLookupResponse(
            item_id=item_id,
            price=0.0,
            source='manual_required'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for customer {customer_id}, item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to fetch item price"
        )

async def set_customer_price(data: CustomerPriceCreate) -> int:
    """
    Set a custom price for a customer/item combination.
    Upserts (Insert or Update).
    """
    try:
        query = """
            INSERT INTO customer_prices (customer_id, item_id, custom_price, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (customer_id, item_id) 
            DO UPDATE SET 
                custom_price = EXCLUDED.custom_price,
                updated_at = NOW()
            RETURNING id
        """
        record = await fetch_one(
            query, 
            data.customer_id, 
            data.item_id, 
            data.custom_price
        )
        return record['id']
    except Exception as e:
        logger.error(f"Error setting customer price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set customer price"
        )

async def get_customer_prices(customer_id: int) -> List[Dict]:
    """
    Get all custom prices for a specific customer.
    """
    try:
        query = """
            SELECT 
                cp.id, cp.customer_id, cp.item_id, cp.custom_price, cp.updated_at,
                im.item_name, im.sku, im.unit
            FROM customer_prices cp
            JOIN item_master im ON cp.item_id = im.id
            WHERE cp.customer_id = $1
            ORDER BY im.item_name
        """
        records = await fetch_all(query, customer_id)
        return [dict(r) for r in records]
    except Exception as e:
        logger.error(f"Error fetching prices for customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch customer prices"
        )
