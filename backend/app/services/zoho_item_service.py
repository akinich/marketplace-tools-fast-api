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
from datetime import datetime
import json

from app.database import fetch_one, fetch_all, execute_query
from app.schemas.zoho_item import ZohoItemCreate, ZohoItemUpdate
from app.services import zoho_books_client

logger = logging.getLogger(__name__)


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
) -> List[Dict]:
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
        List of item dictionaries
    """
    try:
        query = """
            SELECT 
                id, item_id, name, sku, description,
                rate, purchase_rate, item_type, product_type, status,
                hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                unit, account_id,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
            FROM zoho_items
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if active_only:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append('active')
        
        if search:
            param_count += 1
            query += f" AND (name ILIKE ${param_count} OR sku ILIKE ${param_count} OR hsn_or_sac ILIKE ${param_count})"
            params.append(f"%{search}%")
        
        if item_type:
            param_count += 1
            query += f" AND item_type = ${param_count}"
            params.append(item_type)
        
        if product_type:
            param_count += 1
            query += f" AND product_type = ${param_count}"
            params.append(product_type)
        
        query += " ORDER BY name"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        items = await fetch_all(query, *params)
        return [dict(item) for item in items]
        
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
                unit, account_id,
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
        
        for field, value in item_data.model_dump(exclude_unset=True).items():
            # Only admins can update (for now)
            if not is_admin:
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
        params.append(datetime.utcnow())
        
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
                unit, account_id,
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

async def sync_from_zoho_books(synced_by: str) -> Dict[str, int]:
    """
    Sync items from Zoho Books API
    
    Args:
        synced_by: User ID performing sync
    
    Returns:
        Dict with added, updated, skipped, errors counts
    """
    try:
        logger.info(f"Starting Zoho Books sync by {synced_by}")
        
        # Fetch all items from Zoho Books
        zoho_items = await zoho_books_client.fetch_all_items()
        
        added = 0
        updated = 0
        skipped = 0
        errors = 0
        
        for item in zoho_items:
            try:
                # Check if item already exists
                existing = await fetch_one(
                    "SELECT id FROM zoho_items WHERE item_id = $1",
                    item.get('item_id')
                )
                
                # Prepare item data
                item_data = {
                    'item_id': item.get('item_id'),
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
                    'created_time': item.get('created_time'),
                    'last_modified_time': item.get('last_modified_time'),
                    'raw_json': json.dumps(item),
                    'last_sync_at': datetime.utcnow()
                }
                
                if existing:
                    # Update existing item
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
                else:
                    # Insert new item
                    await execute_query(
                        """
                        INSERT INTO zoho_items (
                            item_id, name, sku, description,
                            rate, purchase_rate, item_type, product_type, status,
                            hsn_or_sac, tax_id, tax_name, tax_percentage, is_taxable,
                            unit, account_id,
                            created_time, last_modified_time,
                            raw_json, last_sync_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                        )
                        """,
                        item_data['item_id'], item_data['name'], item_data['sku'],
                        item_data['description'], item_data['rate'], item_data['purchase_rate'],
                        item_data['item_type'], item_data['product_type'], item_data['status'],
                        item_data['hsn_or_sac'], item_data['tax_id'], item_data['tax_name'],
                        item_data['tax_percentage'], item_data['is_taxable'], item_data['unit'],
                        item_data['account_id'], item_data['created_time'],
                        item_data['last_modified_time'], item_data['raw_json'],
                        item_data['last_sync_at']
                    )
                    added += 1
                    
            except Exception as e:
                logger.error(f"Error syncing Zoho item {item.get('item_id')}: {e}")
                errors += 1
        
        logger.info(f"Zoho Books sync completed: {added} added, {updated} updated, {errors} errors")
        
        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Zoho Books sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


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
