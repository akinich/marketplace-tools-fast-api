"""
================================================================================
Zoho Vendor Management Service
================================================================================
Version: 1.0.0
Created: 2025-12-02

Service for managing Zoho vendors, sync operations, and CRUD
================================================================================
"""

from typing import List, Dict, Optional
from fastapi import HTTPException, status
import logging
from datetime import datetime, timezone
import json
from dateutil import parser as date_parser

from app.database import fetch_one, fetch_all, execute_query
from app.schemas.zoho_vendor import ZohoVendorCreate, ZohoVendorUpdate
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
# ZOHO VENDOR CRUD OPERATIONS
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
    Get Zoho vendors with optional search and filters

    Args:
        search: Search term for contact name, company name, email
        active_only: Filter for active vendors only
        item_type: Not used for vendors (kept for API compatibility)
        product_type: Not used for vendors (kept for API compatibility)
        limit: Max results
        offset: Pagination offset

    Returns:
        Tuple of (List of vendor dictionaries, total count)
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
            where_conditions.append(f"(contact_name ILIKE ${param_count} OR company_name ILIKE ${param_count} OR email ILIKE ${param_count})")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM zoho_vendors WHERE {where_clause}"
        count_result = await fetch_one(count_query, *params)
        total_count = count_result['total'] if count_result else 0

        # Get paginated vendors
        query = f"""
            SELECT
                id, contact_id, contact_name, company_name, email,
                phone, mobile, contact_person,
                billing_address, shipping_address,
                payment_terms, payment_terms_label, status,
                gst_no, gst_treatment, pan_no, tax_id,
                place_of_contact, is_taxable,
                outstanding_balance, unused_credits,
                notes,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
            FROM zoho_vendors
            WHERE {where_clause}
            ORDER BY contact_name
            LIMIT ${param_count + 1}
            OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])

        vendors = await fetch_all(query, *params)
        return [dict(vendor) for vendor in vendors], total_count

    except Exception as e:
        logger.error(f"Error fetching Zoho vendors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Zoho vendors"
        )


async def get_item_by_id(contact_id: int) -> Optional[Dict]:
    """Get a single Zoho vendor by database ID"""
    try:
        vendor = await fetch_one(
            """
            SELECT
                id, contact_id, contact_name, company_name, email,
                phone, mobile, contact_person,
                billing_address, shipping_address,
                payment_terms, payment_terms_label, status,
                gst_no, gst_treatment, pan_no, tax_id,
                place_of_contact, is_taxable,
                outstanding_balance, unused_credits,
                notes,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
            FROM zoho_vendors
            WHERE id = $1
            """,
            contact_id
        )
        return dict(vendor) if vendor else None
    except Exception as e:
        logger.error(f"Error fetching Zoho vendor {contact_id}: {e}")
        return None


async def update_item(
    contact_id: int,
    item_data: ZohoVendorUpdate,
    updated_by: str,
    is_admin: bool
) -> Dict:
    """
    Update a Zoho vendor (limited fields - Zoho is source of truth)

    Args:
        contact_id: Vendor database ID
        item_data: Update data
        updated_by: User ID updating the vendor
        is_admin: Whether user is admin

    Returns:
        Updated vendor dictionary
    """
    try:
        # Build dynamic update query based on provided fields
        update_fields = []
        params = []
        param_count = 0

        # Notes field is user-editable for all users
        user_editable_fields = ['notes']

        for field, value in item_data.model_dump(exclude_unset=True).items():
            # Only admins can update non-editable fields
            if field not in user_editable_fields and not is_admin:
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
        params.append(datetime.now(timezone.utc))

        # Add contact_id to params
        param_count += 1
        params.append(contact_id)

        query = f"""
            UPDATE zoho_vendors
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING
                id, contact_id, contact_name, company_name, email,
                phone, mobile, contact_person,
                billing_address, shipping_address,
                payment_terms, payment_terms_label, status,
                gst_no, gst_treatment, pan_no, tax_id,
                place_of_contact, is_taxable,
                outstanding_balance, unused_credits,
                notes,
                created_time, last_modified_time,
                last_sync_at, created_at, updated_at
        """

        vendor = await fetch_one(query, *params)

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zoho vendor not found"
            )

        logger.info(f"Zoho vendor {contact_id} updated by {updated_by}")
        return dict(vendor)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Zoho vendor {contact_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Zoho vendor: {str(e)}"
        )


# ============================================================================
# ZOHO BOOKS SYNC
# ============================================================================

async def sync_from_zoho_books(synced_by: str, force_refresh: bool = False) -> Dict[str, int]:
    """
    Sync vendors from Zoho Books API

    Args:
        synced_by: User ID performing sync
        force_refresh: If True, sync all vendors; if False, only sync vendors modified in last 24 hours

    Returns:
        Dict with added, updated, skipped, errors counts
    """
    try:
        logger.info(f"Starting Zoho Books vendor sync by {synced_by} (force_refresh={force_refresh})")

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

        # Fetch all vendors from Zoho Books
        zoho_vendors = await zoho_books_client.fetch_all_contacts("vendor")

        total_vendors = len(zoho_vendors)
        logger.info(f"Fetched {total_vendors} vendors from Zoho Books")

        # Initialize progress tracking
        _sync_progress["in_progress"] = True
        _sync_progress["current"] = 0
        _sync_progress["total"] = total_vendors
        _sync_progress["added"] = 0
        _sync_progress["updated"] = 0
        _sync_progress["skipped"] = 0
        _sync_progress["errors"] = 0
        _sync_progress["start_time"] = datetime.now(timezone.utc)

        added = 0
        updated = 0
        skipped = 0
        errors = 0

        for index, vendor in enumerate(zoho_vendors, 1):
            try:
                # Convert contact_id to int (Zoho returns as string)
                contact_id = int(vendor.get('contact_id'))

                # Log progress every 50 vendors
                if index % 50 == 0 or index == total_vendors:
                    logger.info(f"Syncing progress: {index}/{total_vendors} vendors processed")

                # Check if vendor already exists
                existing = await fetch_one(
                    "SELECT id, last_sync_at FROM zoho_vendors WHERE contact_id = $1",
                    contact_id
                )

                # Update progress
                _sync_progress["current"] = index

                # Skip if not force_refresh and vendor was synced in last 24 hours
                if not force_refresh and existing and existing['last_sync_at']:
                    from datetime import timedelta
                    # Both datetimes are now timezone-aware (UTC)
                    hours_since_sync = (datetime.now(timezone.utc) - existing['last_sync_at']).total_seconds() / 3600
                    if hours_since_sync < 24:
                        skipped += 1
                        _sync_progress["skipped"] = skipped
                        continue

                # Prepare vendor data
                vendor_data = {
                    'contact_id': contact_id,
                    'contact_name': vendor.get('contact_name'),
                    'company_name': vendor.get('company_name'),
                    'email': vendor.get('email'),
                    'phone': vendor.get('phone'),
                    'mobile': vendor.get('mobile'),
                    'contact_person': vendor.get('contact_person'),
                    'billing_address': vendor.get('billing_address', {}).get('address') if isinstance(vendor.get('billing_address'), dict) else vendor.get('billing_address'),
                    'shipping_address': vendor.get('shipping_address', {}).get('address') if isinstance(vendor.get('shipping_address'), dict) else vendor.get('shipping_address'),
                    'payment_terms': vendor.get('payment_terms'),
                    'payment_terms_label': vendor.get('payment_terms_label'),
                    'status': vendor.get('status', 'active'),
                    'gst_no': vendor.get('gst_no'),
                    'gst_treatment': vendor.get('gst_treatment'),
                    'pan_no': vendor.get('pan_no'),
                    'tax_id': vendor.get('tax_id'),
                    'place_of_contact': vendor.get('place_of_contact'),
                    'is_taxable': vendor.get('is_taxable', True),
                    'outstanding_balance': vendor.get('outstanding_payable_amount', 0) or vendor.get('outstanding_balance', 0),
                    'unused_credits': vendor.get('unused_credits_payable_amount', 0) or vendor.get('unused_credits', 0),
                    'created_time': parse_zoho_datetime(vendor.get('created_time')),
                    'last_modified_time': parse_zoho_datetime(vendor.get('last_modified_time')),
                    'raw_json': json.dumps(vendor),
                    'last_sync_at': datetime.now(timezone.utc)
                }

                if existing:
                    # Update existing vendor
                    await execute_query(
                        """
                        UPDATE zoho_vendors SET
                            contact_name = $2, company_name = $3, email = $4,
                            phone = $5, mobile = $6, contact_person = $7,
                            billing_address = $8, shipping_address = $9,
                            payment_terms = $10, payment_terms_label = $11, status = $12,
                            gst_no = $13, gst_treatment = $14, pan_no = $15, tax_id = $16,
                            place_of_contact = $17, is_taxable = $18,
                            outstanding_balance = $19, unused_credits = $20,
                            created_time = $21, last_modified_time = $22,
                            raw_json = $23, last_sync_at = $24, updated_at = NOW()
                        WHERE id = $1
                        """,
                        existing['id'],
                        vendor_data['contact_name'], vendor_data['company_name'], vendor_data['email'],
                        vendor_data['phone'], vendor_data['mobile'], vendor_data['contact_person'],
                        vendor_data['billing_address'], vendor_data['shipping_address'],
                        vendor_data['payment_terms'], vendor_data['payment_terms_label'], vendor_data['status'],
                        vendor_data['gst_no'], vendor_data['gst_treatment'], vendor_data['pan_no'],
                        vendor_data['tax_id'], vendor_data['place_of_contact'], vendor_data['is_taxable'],
                        vendor_data['outstanding_balance'], vendor_data['unused_credits'],
                        vendor_data['created_time'], vendor_data['last_modified_time'],
                        vendor_data['raw_json'], vendor_data['last_sync_at']
                    )
                    updated += 1
                    _sync_progress["updated"] = updated
                else:
                    # Insert new vendor
                    await execute_query(
                        """
                        INSERT INTO zoho_vendors (
                            contact_id, contact_name, company_name, email,
                            phone, mobile, contact_person,
                            billing_address, shipping_address,
                            payment_terms, payment_terms_label, status,
                            gst_no, gst_treatment, pan_no, tax_id,
                            place_of_contact, is_taxable,
                            outstanding_balance, unused_credits,
                            created_time, last_modified_time,
                            raw_json, last_sync_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                            $21, $22, $23, $24
                        )
                        """,
                        vendor_data['contact_id'], vendor_data['contact_name'], vendor_data['company_name'],
                        vendor_data['email'], vendor_data['phone'], vendor_data['mobile'],
                        vendor_data['contact_person'], vendor_data['billing_address'], vendor_data['shipping_address'],
                        vendor_data['payment_terms'], vendor_data['payment_terms_label'], vendor_data['status'],
                        vendor_data['gst_no'], vendor_data['gst_treatment'], vendor_data['pan_no'],
                        vendor_data['tax_id'], vendor_data['place_of_contact'], vendor_data['is_taxable'],
                        vendor_data['outstanding_balance'], vendor_data['unused_credits'],
                        vendor_data['created_time'], vendor_data['last_modified_time'],
                        vendor_data['raw_json'], vendor_data['last_sync_at']
                    )
                    added += 1
                    _sync_progress["added"] = added

            except ValueError as e:
                logger.error(f"Invalid contact_id format for vendor {vendor.get('contact_id', 'unknown')}: {e}")
                errors += 1
                _sync_progress["errors"] = errors
            except Exception as e:
                logger.error(f"Error syncing Zoho vendor {vendor.get('contact_id', 'unknown')}: {e}")
                errors += 1
                _sync_progress["errors"] = errors

        logger.info(
            f"Zoho Books vendor sync completed: {total_vendors} total vendors, "
            f"{added} added, {updated} updated, {skipped} skipped, {errors} errors"
        )

        # Reset progress tracking
        _sync_progress["in_progress"] = False

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": total_vendors
        }

    except Exception as e:
        logger.error(f"Zoho Books vendor sync failed: {e}")
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
        elapsed = (datetime.now(timezone.utc) - progress["start_time"]).total_seconds()
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
    """Get Zoho vendor statistics"""
    try:
        stats = await fetch_one(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                COUNT(*) FILTER (WHERE gst_no IS NOT NULL AND gst_no != '') as with_gst,
                COUNT(*) FILTER (WHERE gst_no IS NULL OR gst_no = '') as without_gst,
                COUNT(*) FILTER (WHERE outstanding_balance > 0) as with_outstanding
            FROM zoho_vendors
            """
        )

        return dict(stats) if stats else {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "with_gst": 0,
            "without_gst": 0,
            "with_outstanding": 0
        }

    except Exception as e:
        logger.error(f"Error fetching Zoho vendor stats: {e}")
        return {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "with_gst": 0,
            "without_gst": 0,
            "with_outstanding": 0
        }
