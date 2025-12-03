"""
================================================================================
WooCommerce Customer Service
================================================================================
Version: 1.0.0
Created: 2025-12-03

Service layer for WooCommerce customer operations
================================================================================
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from fastapi import HTTPException, status

from app.database import fetch_all, fetch_one, execute_query
from app.services.woocommerce_service import WooCommerceService
from app.schemas.woo_customer import WooCustomerUpdate

logger = logging.getLogger(__name__)

# Global progress tracking for sync operations
_sync_progress = {
    "in_progress": False,
    "current": 0,
    "total": 0,
    "added": 0,
    "updated": 0,
    "skipped": 0,
    "errors": 0,
    "start_time": None
}


# ============================================================================
# CUSTOMER CRUD OPERATIONS
# ============================================================================

async def get_customers(
    search: Optional[str] = None,
    paying_only: bool = False,
    limit: int = 1000,
    offset: int = 0
) -> Tuple[List[Dict], int]:
    """
    Get WooCommerce customers with optional search and filters
    
    Args:
        search: Search term for name, email, company
        paying_only: Filter for paying customers only
        limit: Max results
        offset: Pagination offset
        
    Returns:
        Tuple of (List of customer dictionaries, total count)
    """
    try:
        # Build WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if paying_only:
            param_count += 1
            where_conditions.append(f"is_paying_customer = ${param_count}")
            params.append(True)
        
        if search:
            param_count += 1
            search_condition = f"""(
                first_name ILIKE ${param_count} OR 
                last_name ILIKE ${param_count} OR 
                email ILIKE ${param_count} OR 
                billing_company ILIKE ${param_count} OR
                billing_phone ILIKE ${param_count}
            )"""
            where_conditions.append(search_condition)
            params.append(f"%{search}%")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM woo_customers WHERE {where_clause}"
        count_result = await fetch_one(count_query, *params)
        total_count = count_result['total'] if count_result else 0
        
        # Get paginated customers
        query = f"""
            SELECT
                id, customer_id, email, username, first_name, last_name, role,
                billing_first_name, billing_last_name, billing_company,
                billing_address_1, billing_address_2, billing_city, billing_state,
                billing_postcode, billing_country, billing_email, billing_phone,
                shipping_first_name, shipping_last_name, shipping_company,
                shipping_address_1, shipping_address_2, shipping_city, shipping_state,
                shipping_postcode, shipping_country,
                is_paying_customer, avatar_url,
                date_created, date_modified, last_sync_at,
                created_at, updated_at, notes
            FROM woo_customers
            WHERE {where_clause}
            ORDER BY first_name, last_name
            LIMIT ${param_count + 1}
            OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])
        
        customers = await fetch_all(query, *params)
        return [dict(customer) for customer in customers], total_count
        
    except Exception as e:
        logger.error(f"Error fetching WooCommerce customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch WooCommerce customers"
        )


async def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """Get a single WooCommerce customer by database ID"""
    try:
        query = """
            SELECT
                id, customer_id, email, username, first_name, last_name, role,
                billing_first_name, billing_last_name, billing_company,
                billing_address_1, billing_address_2, billing_city, billing_state,
                billing_postcode, billing_country, billing_email, billing_phone,
                shipping_first_name, shipping_last_name, shipping_company,
                shipping_address_1, shipping_address_2, shipping_city, shipping_state,
                shipping_postcode, shipping_country,
                is_paying_customer, avatar_url,
                date_created, date_modified, last_sync_at,
                created_at, updated_at, notes
            FROM woo_customers
            WHERE id = $1
        """
        result = await fetch_one(query, customer_id)
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch customer"
        )


async def update_customer(
    customer_id: int,
    customer_data: WooCustomerUpdate,
    updated_by: str,
    is_admin: bool
) -> Dict:
    """
    Update a WooCommerce customer (limited fields - WooCommerce is source of truth)
    
    Args:
        customer_id: Customer database ID
        customer_data: Update data
        updated_by: User ID updating the customer
        is_admin: Whether user is admin
        
    Returns:
        Updated customer dictionary
    """
    try:
        # Get existing customer
        existing = await get_customer_by_id(customer_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Build update query
        update_fields = []
        params = []
        param_count = 0
        
        # Only allow notes for non-admin users
        if not is_admin:
            if customer_data.notes is not None:
                param_count += 1
                update_fields.append(f"notes = ${param_count}")
                params.append(customer_data.notes)
        else:
            # Admins can update any field
            update_dict = customer_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                param_count += 1
                update_fields.append(f"{field} = ${param_count}")
                params.append(value)
        
        if not update_fields:
            return existing
        
        # Add updated_by and updated_at
        param_count += 1
        update_fields.append(f"updated_by = ${param_count}")
        params.append(updated_by)
        
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        
        # Add customer_id to params
        param_count += 1
        params.append(customer_id)
        
        query = f"""
            UPDATE woo_customers
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """
        
        result = await fetch_one(query, *params)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        logger.info(f"Customer {customer_id} updated by {updated_by}")
        return dict(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )


# ============================================================================
# WOOCOMMERCE SYNC
# ============================================================================

async def sync_from_woocommerce(synced_by: str) -> Dict:
    """
    Sync customers from WooCommerce API
    
    Args:
        synced_by: User ID performing sync
        
    Returns:
        Dict with added, updated, skipped, errors counts
    """
    global _sync_progress
    
    # Check if sync already in progress
    if _sync_progress["in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sync already in progress"
        )
    
    # Initialize progress
    _sync_progress = {
        "in_progress": True,
        "current": 0,
        "total": 0,
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "start_time": datetime.utcnow()
    }
    
    try:
        logger.info(f"Starting WooCommerce customer sync by {synced_by}")
        
        # Fetch customers from WooCommerce
        woo_customers = await WooCommerceService.fetch_customers(
            per_page=100,
            max_customers=10000
        )
        
        _sync_progress["total"] = len(woo_customers)
        logger.info(f"Fetched {len(woo_customers)} customers from WooCommerce")
        
        # Process each customer
        for idx, woo_customer in enumerate(woo_customers):
            _sync_progress["current"] = idx + 1
            
            try:
                await _process_customer(woo_customer, synced_by)
            except Exception as e:
                logger.error(f"Error processing customer {woo_customer.get('id')}: {e}")
                _sync_progress["errors"] += 1
        
        logger.info(
            f"WooCommerce customer sync completed: "
            f"{_sync_progress['total']} total, "
            f"{_sync_progress['added']} added, "
            f"{_sync_progress['updated']} updated, "
            f"{_sync_progress['skipped']} skipped, "
            f"{_sync_progress['errors']} errors"
        )
        
        return {
            "total": _sync_progress["total"],
            "added": _sync_progress["added"],
            "updated": _sync_progress["updated"],
            "skipped": _sync_progress["skipped"],
            "errors": _sync_progress["errors"]
        }
        
    except Exception as e:
        logger.error(f"WooCommerce customer sync failed: {e}")
        _sync_progress["errors"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
    finally:
        _sync_progress["in_progress"] = False


async def _process_customer(woo_customer: Dict, synced_by: str):
    """Process a single customer from WooCommerce"""
    customer_id = woo_customer.get('id')
    
    if not customer_id:
        logger.warning("Customer missing ID, skipping")
        _sync_progress["skipped"] += 1
        return
    
    # Check if customer exists
    existing = await fetch_one(
        "SELECT id FROM woo_customers WHERE customer_id = $1",
        customer_id
    )
    
    # Parse dates
    date_created = None
    date_modified = None
    if woo_customer.get('date_created'):
        try:
            date_created = datetime.fromisoformat(woo_customer['date_created'].replace('Z', '+00:00'))
        except:
            pass
    if woo_customer.get('date_modified'):
        try:
            date_modified = datetime.fromisoformat(woo_customer['date_modified'].replace('Z', '+00:00'))
        except:
            pass
    
    # Extract billing and shipping info
    billing = woo_customer.get('billing', {})
    shipping = woo_customer.get('shipping', {})
    
    if existing:
        # Update existing customer
        query = """
            UPDATE woo_customers SET
                email = $1, username = $2, first_name = $3, last_name = $4, role = $5,
                billing_first_name = $6, billing_last_name = $7, billing_company = $8,
                billing_address_1 = $9, billing_address_2 = $10, billing_city = $11,
                billing_state = $12, billing_postcode = $13, billing_country = $14,
                billing_email = $15, billing_phone = $16,
                shipping_first_name = $17, shipping_last_name = $18, shipping_company = $19,
                shipping_address_1 = $20, shipping_address_2 = $21, shipping_city = $22,
                shipping_state = $23, shipping_postcode = $24, shipping_country = $25,
                is_paying_customer = $26, avatar_url = $27,
                date_created = $28, date_modified = $29,
                last_sync_at = $30, updated_by = $31, updated_at = $32
            WHERE customer_id = $33
        """
        await execute_query(
            query,
            woo_customer.get('email'),
            woo_customer.get('username'),
            woo_customer.get('first_name'),
            woo_customer.get('last_name'),
            woo_customer.get('role', 'customer'),
            billing.get('first_name'),
            billing.get('last_name'),
            billing.get('company'),
            billing.get('address_1'),
            billing.get('address_2'),
            billing.get('city'),
            billing.get('state'),
            billing.get('postcode'),
            billing.get('country'),
            billing.get('email'),
            billing.get('phone'),
            shipping.get('first_name'),
            shipping.get('last_name'),
            shipping.get('company'),
            shipping.get('address_1'),
            shipping.get('address_2'),
            shipping.get('city'),
            shipping.get('state'),
            shipping.get('postcode'),
            shipping.get('country'),
            woo_customer.get('is_paying_customer', False),
            woo_customer.get('avatar_url'),
            date_created,
            date_modified,
            datetime.utcnow(),
            synced_by,
            datetime.utcnow(),
            customer_id
        )
        _sync_progress["updated"] += 1
    else:
        # Insert new customer
        query = """
            INSERT INTO woo_customers (
                customer_id, email, username, first_name, last_name, role,
                billing_first_name, billing_last_name, billing_company,
                billing_address_1, billing_address_2, billing_city,
                billing_state, billing_postcode, billing_country,
                billing_email, billing_phone,
                shipping_first_name, shipping_last_name, shipping_company,
                shipping_address_1, shipping_address_2, shipping_city,
                shipping_state, shipping_postcode, shipping_country,
                is_paying_customer, avatar_url,
                date_created, date_modified,
                last_sync_at, created_by, updated_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
                $29, $30, $31, $32, $33
            )
        """
        await execute_query(
            query,
            customer_id,
            woo_customer.get('email'),
            woo_customer.get('username'),
            woo_customer.get('first_name'),
            woo_customer.get('last_name'),
            woo_customer.get('role', 'customer'),
            billing.get('first_name'),
            billing.get('last_name'),
            billing.get('company'),
            billing.get('address_1'),
            billing.get('address_2'),
            billing.get('city'),
            billing.get('state'),
            billing.get('postcode'),
            billing.get('country'),
            billing.get('email'),
            billing.get('phone'),
            shipping.get('first_name'),
            shipping.get('last_name'),
            shipping.get('company'),
            shipping.get('address_1'),
            shipping.get('address_2'),
            shipping.get('city'),
            shipping.get('state'),
            shipping.get('postcode'),
            shipping.get('country'),
            woo_customer.get('is_paying_customer', False),
            woo_customer.get('avatar_url'),
            date_created,
            date_modified,
            datetime.utcnow(),
            synced_by,
            synced_by
        )
        _sync_progress["added"] += 1


async def get_sync_progress() -> Dict:
    """
    Get current sync progress
    
    Returns:
        Dict with progress information including percentage and ETA
    """
    progress = _sync_progress.copy()
    
    # Calculate percentage
    if progress["total"] > 0:
        progress["percentage"] = int((progress["current"] / progress["total"]) * 100)
    else:
        progress["percentage"] = 0
    
    return progress


# ============================================================================
# STATISTICS
# ============================================================================

async def get_customer_stats() -> Dict:
    """Get WooCommerce customer statistics"""
    try:
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_paying_customer = true) as paying_customers,
                COUNT(DISTINCT billing_country) as countries,
                COUNT(*) FILTER (WHERE billing_country = 'IN') as india_customers,
                COUNT(*) FILTER (WHERE date_created >= NOW() - INTERVAL '30 days') as new_this_month
            FROM woo_customers
        """
        result = await fetch_one(query)
        
        return {
            "total": result['total'] if result else 0,
            "paying_customers": result['paying_customers'] if result else 0,
            "countries": result['countries'] if result else 0,
            "india_customers": result['india_customers'] if result else 0,
            "new_this_month": result['new_this_month'] if result else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching customer stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch customer statistics"
        )
