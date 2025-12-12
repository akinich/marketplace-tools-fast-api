"""
================================================================================
Zoho Item Management Service
================================================================================
Version: 1.0.0
Created: 2025-12-02

Service for managing Zoho items, sync operations, and CRUD
================================================================================
"""

from typing import List, Dict, Optional
from fastapi import HTTPException, status
import logging
from datetime import datetime, timezone
from app.utils.timezone import now_ist
import json
from dateutil import parser as date_parser

from app.database import fetch_one, fetch_all, execute_query
from app.schemas.zoho_item import ZohoItemCreate, ZohoItemUpdate
from app.services import zoho_books_client

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


def parse_zoho_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse Zoho datetime string to Python datetime object

    Args:
        date_string: ISO format datetime string from Zoho API

    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None
    try:
        # Zoho returns dates like '2021-03-02T16:56:44+0530'
        return date_parser.parse(date_string)
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{date_string}': {e}")
        return None


# ============================================================================
# ZOHO ITEM CRUD OPERATIONS
# ============================================================================

async def get_items(
    search: Optional[str] = None,
    active_only: bool = True,
    item_type: Optional[str] = None,
    product_type: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
) -> tuple[List[Dict], int]:
    """
    Get Zoho items with optional search and filters

    Args:
        search: Search term for item name or SKU
        active_only: Filter for active items only
        item_type: Filter by item_type (sales, purchases, etc.)
        product_type: Filter by product_type (goods, service)
        limit: Max results
        offset: Pagination offset

    Returns:
        Tuple of (List of item dictionaries, total count)
    """
    try:
        # Build WHERE clause for both queries
        where_conditions = []
        params = []
        param_count = 0

        if active_only:
            param_count += 1
            where_conditions.append(f"status = ${param_count}")
            params.append('active')

        if search:
            param_count += 1
            where_conditions.append(f"(name ILIKE ${param_count} OR sku ILIKE ${param_count} OR hsn_or_sac ILIKE ${param_count})")
            params.append(f"%{search}%")

        if item_type:
            param_count += 1
            where_conditions.append(f"item_type = ${param_count}")
            params.append(item_type)

        if product_type:
            param_count += 1
            where_conditions.append(f"product_type = ${param_count}")
            params.append(product_type)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM zoho_items WHERE {where_clause}"
        count_result = await fetch_one(count_query, *params)
        total_count = count_result['total'] if count_result else 0

        # Get paginated items
        query = f"""
            SELECT
                id, item_id, name, sku, description,
                rate, purchase_rate, item_type, product_type, status,
                hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                unit, account_id, for_purchase, segment,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
            FROM zoho_items
            WHERE {where_clause}
            ORDER BY name
            LIMIT ${param_count + 1}
            OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])

        items = await fetch_all(query, *params)
        return [dict(item) for item in items], total_count

    except Exception as e:
        logger.error(f"Error fetching Zoho items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Zoho items"
        )


async def get_item_by_id(item_id: int) -> Optional[Dict]:
    """Get a single Zoho item by database ID"""
    try:
        item = await fetch_one(
            """
            SELECT 
                id, item_id, name, sku, description,
                rate, purchase_rate, item_type, product_type, status,
                hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                unit, account_id, for_purchase, segment,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
            FROM zoho_items
            WHERE id = $1
            """,
            item_id
        )
        return dict(item) if item else None
    except Exception as e:
        logger.error(f"Error fetching Zoho item {item_id}: {e}")
        return None


async def update_item(
    item_id: int,
    item_data: ZohoItemUpdate,
    updated_by: str,
    is_admin: bool
) -> Dict:
    """
    Update a Zoho item (limited fields - Zoho is source of truth)
    
    Args:
        item_id: Item database ID
        item_data: Update data
        updated_by: User ID updating the item
        is_admin: Whether user is admin
    
    Returns:
        Updated item dictionary
    """
    try:
        # Build dynamic update query based on provided fields
        update_fields = []
        params = []
        param_count = 0
        
        # For now, all fields are read-only since Zoho is source of truth
        # In future, you can add editable fields here if needed
        # user_editable_fields = []
        user_editable_fields = ['for_purchase', 'segment']

        for field, value in item_data.model_dump(exclude_unset=True).items():
            # Only admins can update (for now), UNLESS it is a whitelisted field
            if not is_admin and field not in user_editable_fields:
                continue
            
            param_count += 1
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update or insufficient permissions"
            )
        
        # Add updated_at
        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(now_ist())
        
        # Add item_id to params
        param_count += 1
        params.append(item_id)
        
        query = f"""
            UPDATE zoho_items
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING 
                id, item_id, name, sku, description,
                rate, purchase_rate, item_type, product_type, status,
                hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                unit, account_id, for_purchase, segment,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
        """
        
        item = await fetch_one(query, *params)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zoho item not found"
            )
        
        logger.info(f"Zoho item {item_id} updated by {updated_by}")
        return dict(item)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Zoho item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Zoho item: {str(e)}"
        )


# ============================================================================
# ZOHO BOOKS SYNC
# ============================================================================

async def sync_from_zoho_books(synced_by: str, force_refresh: bool = False) -> Dict[str, int]:
    """
    Sync items from Zoho Books API

    Args:
        synced_by: User ID performing sync
        force_refresh: If True, sync all items; if False, only sync items modified in last 24 hours

    Returns:
        Dict with added, updated, skipped, errors counts
    """
    try:
        logger.info(f"Starting Zoho Books sync by {synced_by} (force_refresh={force_refresh})")

        # Validate Zoho credentials are configured
        from app.database import get_db
        from app.services import settings_service

        pool = get_db()
        async with pool.acquire() as conn:
            client_id = await settings_service.get_setting(conn, "zoho.client_id")
            client_secret = await settings_service.get_setting(conn, "zoho.client_secret")
            refresh_token = await settings_service.get_setting(conn, "zoho.refresh_token")
            organization_id = await settings_service.get_setting(conn, "zoho.organization_id")

        if not all([client_id, client_secret, refresh_token, organization_id]):
            missing = []
            if not client_id: missing.append("zoho.client_id")
            if not client_secret: missing.append("zoho.client_secret")
            if not refresh_token: missing.append("zoho.refresh_token")
            if not organization_id: missing.append("zoho.organization_id")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Zoho Books API credentials not configured. Missing: {', '.join(missing)}. Please configure in System Settings → Zoho Books."
            )

        # Fetch all items from Zoho Books
        zoho_items = await zoho_books_client.fetch_all_items()

        total_items = len(zoho_items)
        logger.info(f"Fetched {total_items} items from Zoho Books")

        # Initialize progress tracking
        _sync_progress["in_progress"] = True
        _sync_progress["current"] = 0
        _sync_progress["total"] = total_items
        _sync_progress["added"] = 0
        _sync_progress["updated"] = 0
        _sync_progress["skipped"] = 0
        _sync_progress["errors"] = 0
        _sync_progress["start_time"] = now_ist()

        added = 0
        updated = 0
        skipped = 0
        errors = 0

        for index, item in enumerate(zoho_items, 1):
            try:
                # Convert item_id to int (Zoho returns as string)
                item_id = int(item.get('item_id'))

                # Log progress every 50 items
                if index % 50 == 0 or index == total_items:
                    logger.info(f"Syncing progress: {index}/{total_items} items processed")

                # Check if item already exists
                existing = await fetch_one(
                    "SELECT id, last_sync_at FROM zoho_items WHERE item_id = $1",
                    item_id
                )

                # Update progress
                _sync_progress["current"] = index

                # Skip if not force_refresh and item was synced in last 24 hours
                if not force_refresh and existing and existing['last_sync_at']:
                    from datetime import timedelta
                    # Both datetimes are now timezone-aware (UTC)
                    hours_since_sync = (now_ist() - existing['last_sync_at']).total_seconds() / 3600
                    if hours_since_sync < 24:
                        skipped += 1
                        _sync_progress["skipped"] = skipped
                        continue

                # Prepare item data
                item_data = {
                    'item_id': item_id,
                    'name': item.get('name'),
                    'sku': item.get('sku'),
                    'description': item.get('description'),
                    'rate': item.get('rate'),
                    'purchase_rate': item.get('purchase_rate'),
                    'item_type': item.get('item_type'),
                    'product_type': item.get('product_type'),
                    'status': item.get('status', 'active'),
                    'hsn_or_sac': item.get('hsn_or_sac'),
                    'tax_id': item.get('tax_id'),
                    'tax_name': item.get('tax_name'),
                    'tax_percentage': item.get('tax_percentage'),
                    'is_taxable': item.get('is_taxable', True),
                    'unit': item.get('unit'),
                    'account_id': item.get('account_id'),
                    'created_time': parse_zoho_datetime(item.get('created_time')),
                    'last_modified_time': parse_zoho_datetime(item.get('last_modified_time')),
                    'raw_json': json.dumps(item),
                    'last_sync_at': now_ist()
                }
                
                if existing:
                    # Update existing item (preserve user-edited fields: for_purchase, segment)
                    await execute_query(
                        """
                        UPDATE zoho_items SET
                            name = $2, sku = $3, description = $4,
                            rate = $5, purchase_rate = $6, item_type = $7, product_type = $8,
                            status = $9, hsn_or_sac = $10, tax_id = $11, tax_name = $12,
                            tax_percentage = $13, is_taxable = $14, unit = $15, account_id = $16,
                            created_time = $17, last_modified_time = $18,
                            raw_json = $19, last_sync_at = $20, updated_at = NOW()
                        WHERE id = $1
                        -- Note: for_purchase and segment are NOT updated to preserve user edits
                        """,
                        existing['id'],
                        item_data['name'], item_data['sku'], item_data['description'],
                        item_data['rate'], item_data['purchase_rate'], item_data['item_type'],
                        item_data['product_type'], item_data['status'], item_data['hsn_or_sac'],
                        item_data['tax_id'], item_data['tax_name'], item_data['tax_percentage'],
                        item_data['is_taxable'], item_data['unit'], item_data['account_id'],
                        item_data['created_time'], item_data['last_modified_time'],
                        item_data['raw_json'], item_data['last_sync_at']
                    )
                    updated += 1
                    _sync_progress["updated"] = updated
                else:
                    # Insert new item with default values for user-editable fields
                    await execute_query(
                        """
                        INSERT INTO zoho_items (
                            item_id, name, sku, description,
                            rate, purchase_rate, item_type, product_type, status,
                            hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                            unit, account_id, for_purchase, segment,
                            created_time, last_modified_time,
                            raw_json, last_sync_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                        )
                        """,
                        item_data['item_id'], item_data['name'], item_data['sku'],
                        item_data['description'], item_data['rate'], item_data['purchase_rate'],
                        item_data['item_type'], item_data['product_type'], item_data['status'],
                        item_data['hsn_or_sac'], item_data['tax_id'], item_data['tax_name'],
                        item_data['tax_percentage'], item_data['is_taxable'], item_data['unit'],
                        item_data['account_id'], False, [],  # for_purchase=False, segment=empty array
                        item_data['created_time'],
                        item_data['last_modified_time'], item_data['raw_json'],
                        item_data['last_sync_at']
                    )
                    added += 1
                    _sync_progress["added"] = added

            except ValueError as e:
                logger.error(f"Invalid item_id format for item {item.get('item_id', 'unknown')}: {e}")
                errors += 1
                _sync_progress["errors"] = errors
            except Exception as e:
                logger.error(f"Error syncing Zoho item {item.get('item_id', 'unknown')}: {e}")
                errors += 1
                _sync_progress["errors"] = errors
        
        logger.info(
            f"Zoho Books sync completed: {total_items} total items, "
            f"{added} added, {updated} updated, {skipped} skipped, {errors} errors"
        )

        # Reset progress tracking
        _sync_progress["in_progress"] = False

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": total_items
        }
        
    except Exception as e:
        logger.error(f"Zoho Books sync failed: {e}")
        # Reset progress tracking on error
        _sync_progress["in_progress"] = False
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


async def get_sync_progress() -> Dict:
    """
    Get current sync progress

    Returns:
        Dict with progress information including percentage and ETA
    """
    progress = _sync_progress.copy()

    # Calculate percentage
    if progress["total"] > 0:
        progress["percentage"] = round((progress["current"] / progress["total"]) * 100, 1)
    else:
        progress["percentage"] = 0

    # Calculate ETA
    if progress["in_progress"] and progress["start_time"] and progress["current"] > 0:
        elapsed = (now_ist() - progress["start_time"]).total_seconds()
        items_per_second = progress["current"] / elapsed if elapsed > 0 else 0
        remaining_items = progress["total"] - progress["current"]
        eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
        progress["eta_seconds"] = int(eta_seconds)
    else:
        progress["eta_seconds"] = 0

    # Remove start_time from response (not JSON serializable)
    progress.pop("start_time", None)

    return progress


# ============================================================================
# STATISTICS
# ============================================================================

async def get_item_stats() -> Dict[str, int]:
    """Get Zoho item statistics"""
    try:
        stats = await fetch_one(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                COUNT(*) FILTER (WHERE product_type = 'goods') as goods,
                COUNT(*) FILTER (WHERE product_type = 'service') as services,
                COUNT(*) FILTER (WHERE is_taxable = TRUE) as taxable,
                COUNT(*) FILTER (WHERE is_taxable = FALSE) as non_taxable
            FROM zoho_items
            """
        )
        
        return dict(stats) if stats else {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "goods": 0,
            "services": 0,
            "taxable": 0,
            "non_taxable": 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching Zoho item stats: {e}")
        return {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "goods": 0,
            "services": 0,
            "taxable": 0,
            "non_taxable": 0
        }
