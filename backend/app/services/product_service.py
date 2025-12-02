"""
================================================================================
Product Management Service
================================================================================
Version: 1.0.0
Created: 2025-12-01

Service for managing products, WooCommerce sync, and CRUD operations
================================================================================
"""

from typing import List, Dict, Optional, Tuple
from fastapi import HTTPException, status
import logging
import httpx
import os
from datetime import datetime

from app.database import fetch_one, fetch_all, execute_query, get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services import settings_service

logger = logging.getLogger(__name__)


# ============================================================================
# PRODUCT CRUD OPERATIONS
# ============================================================================

async def get_products(
    search: Optional[str] = None,
    active_only: bool = True,
    product_type: Optional[str] = None,  # "simple", "variations", or None for all
    limit: int = 1000,
    offset: int = 0
) -> List[Dict]:
    """
    Get products with optional search and filters
    
    Args:
        search: Search term for product name
        active_only: Filter for active products only
        product_type: Filter by type (simple/variations)
        limit: Max results
        offset: Pagination offset
    
    Returns:
        List of product dictionaries
    """
    try:
        query = """
            SELECT 
                id, product_id, variation_id, sku, product_name, parent_product,
                stock_quantity, regular_price, sale_price, hsn, zoho_name, usage_units,
                categories, attribute, notes, is_active, product_status,
                last_sync_at, created_at, updated_at
            FROM products
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if active_only:
            param_count += 1
            query += f" AND is_active = ${param_count}"
            params.append(True)
        
        if search:
            param_count += 1
            query += f" AND (product_name ILIKE ${param_count} OR sku ILIKE ${param_count})"
            params.append(f"%{search}%")
        
        if product_type == "simple":
            query += " AND variation_id IS NULL"
        elif product_type == "variations":
            query += " AND variation_id IS NOT NULL"
        
        query += " ORDER BY product_name"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        products = await fetch_all(query, *params)
        return [dict(p) for p in products]
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


async def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Get a single product by ID"""
    try:
        product = await fetch_one(
            """
            SELECT 
                id, product_id, variation_id, sku, product_name, parent_product,
                stock_quantity, regular_price, sale_price, hsn, zoho_name, usage_units,
                categories, attribute, notes, is_active, product_status,
                last_sync_at, created_at, updated_at
            FROM products
            WHERE id = $1
            """,
            product_id
        )
        return dict(product) if product else None
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        return None


async def create_product(product_data: ProductCreate, created_by: str) -> Dict:
    """
    Create a new product
    
    Args:
        product_data: Product data
        created_by: User ID creating the product
    
    Returns:
        Created product dictionary
    """
    try:
        product = await fetch_one(
            """
            INSERT INTO products (
                product_id, variation_id, sku, product_name, parent_product,
                stock_quantity, regular_price, sale_price, hsn, zoho_name, usage_units,
                categories, attribute, notes, is_active, product_status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING 
                id, product_id, variation_id, sku, product_name, parent_product,
                stock_quantity, regular_price, sale_price, hsn, zoho_name, usage_units,
                categories, attribute, notes, is_active, product_status,
                last_sync_at, created_at, updated_at
            """,
            product_data.product_id,
            product_data.variation_id,
            product_data.sku,
            product_data.product_name,
            product_data.parent_product,
            product_data.stock_quantity,
            product_data.regular_price,
            product_data.sale_price,
            product_data.hsn,
            product_data.zoho_name,
            product_data.usage_units,
            product_data.categories,
            product_data.attribute,
            product_data.notes,
            product_data.is_active,
            product_data.product_status
        )
        
        logger.info(f"Product created: {product_data.product_name} by {created_by}")
        return dict(product)
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    updated_by: str,
    is_admin: bool
) -> Dict:
    """
    Update a product
    
    Args:
        product_id: Product ID
        product_data: Update data
        updated_by: User ID updating the product
        is_admin: Whether user is admin
    
    Returns:
        Updated product dictionary
    """
    try:
        # Build dynamic update query based on provided fields
        update_fields = []
        params = []
        param_count = 0
        
        # Define which fields can be edited by non-admins
        user_editable_fields = ['hsn', 'zoho_name', 'usage_units', 'notes']
        
        for field, value in product_data.model_dump(exclude_unset=True).items():
            # Check permissions
            if not is_admin and field not in user_editable_fields:
                continue
            
            param_count += 1
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Add updated_at
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        
        # Add product_id to params
        param_count += 1
        params.append(product_id)
        
        query = f"""
            UPDATE products
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING 
                id, product_id, variation_id, sku, product_name, parent_product,
                stock_quantity, regular_price, sale_price, hsn, zoho_name, usage_units,
                categories, attribute, notes, is_active, product_status,
                last_sync_at, created_at, updated_at
        """
        
        product = await fetch_one(query, *params)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Product {product_id} updated by {updated_by}")
        return dict(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


async def bulk_update_products(updates: List[Tuple[int, Dict]], updated_by: str, is_admin: bool) -> Tuple[int, int]:
    """
    Bulk update products
    
    Args:
        updates: List of (product_id, update_dict) tuples
        updated_by: User ID
        is_admin: Whether user is admin
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    for product_id, update_data in updates:
        try:
            product_update = ProductUpdate(**update_data)
            await update_product(product_id, product_update, updated_by, is_admin)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to update product {product_id}: {e}")
            failure_count += 1
    
    return success_count, failure_count


# ============================================================================
# WOOCOMMERCE SYNC
# ============================================================================

async def sync_from_woocommerce(limit: int, synced_by: str) -> Dict[str, int]:
    """
    Sync products from WooCommerce API
    
    Args:
        limit: Number of products to fetch (max 100)
        synced_by: User ID performing sync
    
    Returns:
        Dict with added, skipped, errors counts
    """
    try:
        # Get database connection pool
        pool = get_db()

        # Get WooCommerce credentials from settings (with fallback to environment variables)
        async with pool.acquire() as conn:
            # Use dotted notation matching codebase standard (category.key)
            api_url = await settings_service.get_setting(conn, "woocommerce.api_url")
            consumer_key = await settings_service.get_setting(conn, "woocommerce.consumer_key")
            consumer_secret = await settings_service.get_setting(conn, "woocommerce.consumer_secret")

        # Fallback to environment variables if not in database
        if not api_url:
            api_url = os.getenv("WOOCOMMERCE_API_URL")
            if api_url:
                logger.info("Using WOOCOMMERCE_API_URL from environment variable")

        if not consumer_key:
            consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
            if consumer_key:
                logger.info("Using WOOCOMMERCE_CONSUMER_KEY from environment variable")

        if not consumer_secret:
            consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
            if consumer_secret:
                logger.info("Using WOOCOMMERCE_CONSUMER_SECRET from environment variable")

        if not all([api_url, consumer_key, consumer_secret]):
            logger.error(f"Missing WooCommerce credentials - API URL: {bool(api_url)}, Consumer Key: {bool(consumer_key)}, Consumer Secret: {bool(consumer_secret)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WooCommerce API credentials not configured. Please set WOOCOMMERCE_API_URL, WOOCOMMERCE_CONSUMER_KEY, and WOOCOMMERCE_CONSUMER_SECRET in system settings or environment variables."
            )

        logger.info(f"Starting WooCommerce sync with limit={limit}, API URL={api_url[:40]}...")

        # Fetch simple products
        products = await fetch_wc_products(api_url, consumer_key, consumer_secret, limit)
        
        # Fetch variations for variable products
        all_products = []
        for product in products:
            all_products.append(product)
            
            if product.get('type') == 'variable':
                variations = await fetch_wc_variations(
                    api_url, consumer_key, consumer_secret, product['id']
                )
                for variation in variations:
                    variation['parent_name'] = product['name']
                    all_products.append(variation)
        
        # Sync to database
        added = 0
        skipped = 0
        errors = 0
        
        for product in all_products:
            try:
                # Check if product already exists
                existing = await fetch_one(
                    "SELECT id FROM products WHERE product_id = $1 AND (variation_id = $2 OR (variation_id IS NULL AND $2 IS NULL))",
                    product.get('id'),
                    product.get('variation_id')
                )
                
                if existing:
                    skipped += 1
                    continue
                
                # Insert new product
                product_create = ProductCreate(
                    product_id=product.get('id'),
                    variation_id=product.get('variation_id'),
                    sku=product.get('sku', ''),
                    product_name=product.get('name', ''),
                    parent_product=product.get('parent_name'),
                    stock_quantity=product.get('stock_quantity', 0),
                    regular_price=product.get('regular_price'),
                    sale_price=product.get('sale_price'),
                    categories=product.get('categories', ''),
                    attribute=product.get('attributes', ''),
                    product_status=product.get('status', 'publish'),
                    is_active=True
                )
                
                await create_product(product_create, synced_by)
                added += 1
                
            except Exception as e:
                logger.error(f"Error syncing product {product.get('id')}: {e}")
                errors += 1
        
        # Update last_sync_at for synced products
        await execute_query(
            "UPDATE products SET last_sync_at = NOW() WHERE product_id = ANY($1)",
            [p.get('id') for p in all_products]
        )
        
        logger.info(f"WooCommerce sync completed: {added} added, {skipped} skipped, {errors} errors")
        
        return {
            "added": added,
            "skipped": skipped,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WooCommerce sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


async def fetch_wc_products(api_url: str, consumer_key: str, consumer_secret: str, limit: int) -> List[Dict]:
    """Fetch products from WooCommerce API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_url}/products",
                auth=(consumer_key, consumer_secret),
                params={'per_page': min(limit, 100), 'status': 'publish'},
                timeout=30.0
            )
            response.raise_for_status()
            products = response.json()
        
        parsed_products = []
        for product in products:
            parsed = {
                'id': product['id'],
                'name': product['name'],
                'sku': product.get('sku', ''),
                'type': product.get('type', 'simple'),
                'regular_price': float(product.get('regular_price', 0) or 0),
                'sale_price': float(product.get('sale_price', 0) or 0),
                'stock_quantity': product.get('stock_quantity', 0),
                'status': product.get('status', 'publish'),
                'categories': ', '.join([cat['name'] for cat in product.get('categories', [])]),
                'variation_id': None
            }
            parsed_products.append(parsed)
        
        return parsed_products
        
    except Exception as e:
        logger.error(f"Error fetching WooCommerce products: {e}")
        raise


async def fetch_wc_variations(api_url: str, consumer_key: str, consumer_secret: str, product_id: int) -> List[Dict]:
    """Fetch variations for a variable product"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_url}/products/{product_id}/variations",
                auth=(consumer_key, consumer_secret),
                params={'per_page': 100},
                timeout=30.0
            )
            response.raise_for_status()
            variations = response.json()
        
        parsed_variations = []
        for variation in variations:
            attrs = ', '.join([f"{attr['name']}: {attr['option']}" for attr in variation.get('attributes', [])])
            
            parsed = {
                'id': product_id,  # Parent product ID
                'variation_id': variation['id'],
                'name': variation.get('name', ''),
                'sku': variation.get('sku', ''),
                'type': 'variation',
                'regular_price': float(variation.get('regular_price', 0) or 0),
                'sale_price': float(variation.get('sale_price', 0) or 0),
                'stock_quantity': variation.get('stock_quantity', 0),
                'status': variation.get('status', 'publish'),
                'attributes': attrs,
                'categories': ''
            }
            parsed_variations.append(parsed)
        
        return parsed_variations
        
    except Exception as e:
        logger.warning(f"Error fetching variations for product {product_id}: {e}")
        return []


# ============================================================================
# STATISTICS
# ============================================================================

async def get_product_stats() -> Dict[str, int]:
    """Get product statistics"""
    try:
        stats = await fetch_one(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_active = TRUE) as active,
                COUNT(*) FILTER (WHERE is_active = FALSE) as inactive,
                COUNT(*) FILTER (WHERE variation_id IS NULL) as simple,
                COUNT(*) FILTER (WHERE variation_id IS NOT NULL) as variations
            FROM products
            """
        )
        
        return dict(stats) if stats else {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "simple": 0,
            "variations": 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching product stats: {e}")
        return {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "simple": 0,
            "variations": 0
        }
