"""
================================================================================
Marketplace ERP - Purchase Order Routes
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  API endpoints for purchase order management. Provides PO creation, updates,
  vendor pricing management, Zoho export, and PDF generation.

Endpoints:
  POST   /api/v1/po/create                  - Create new PO
  GET    /api/v1/po/{po_id}                 - Get PO details
  PUT    /api/v1/po/{po_id}/update          - Update PO
  POST   /api/v1/po/{po_id}/send            - Send PO to farm
  GET    /api/v1/po/list                    - List POs with filters
  POST   /api/v1/po/export-zoho             - Export to Zoho (admin)
  GET    /api/v1/po/{po_id}/pdf             - Generate PO PDF
  POST   /api/v1/vendor-pricing/manage      - Manage pricing (admin)
  GET    /api/v1/vendor-pricing/history     - Get price history (admin)
  GET    /api/v1/vendor-pricing/active      - Get active prices

================================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from typing import Optional
from datetime import date

from app.schemas.po import (
    POCreateRequest, POUpdateRequest, POResponse, PODetailResponse,
    POListResponse, VendorPricingRequest, PriceHistoryResponse,
    ActivePriceResponse, ExportToZohoRequest
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import po_service

router = APIRouter()


# ============================================================================
# PO MANAGEMENT ROUTES
# ============================================================================

@router.post("/create", response_model=PODetailResponse, status_code=status.HTTP_201_CREATED)
async def create_po(
    request: POCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create new purchase order with 3-tier pricing logic.

    **3-Tier Pricing:**
    1. Vendor-specific price for dispatch date (if exists)
    2. Zoho item default price (if exists)
    3. Manual entry required (if no auto-price found)

    **Returns:**
    - Complete PO details with items and pricing
    - Auto-generated PO number (PO-001, PO-002, etc.)
    - Initial status: draft
    """
    try:
        result = await po_service.create_po(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create PO: {str(e)}"
        )


@router.get("/{po_id}", response_model=PODetailResponse)
async def get_po(
    po_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get complete PO details.

    **Includes:**
    - PO metadata (number, vendor, dates, status, total)
    - All PO items with pricing details
    - Complete status history
    - Vendor information
    """
    try:
        po = await po_service.get_po_details(po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PO {po_id} not found"
            )
        return po
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PO: {str(e)}"
        )


@router.put("/{po_id}/update", response_model=PODetailResponse)
async def update_po(
    po_id: int,
    request: POUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update purchase order.

    **Edit Restrictions:**
    - Cannot edit if status is 'exported_to_zoho' or 'closed'
    - All changes are logged in status history
    - Price overrides are tracked

    **Partial Updates:**
    - Only provide fields you want to update
    - Omitted fields remain unchanged
    """
    try:
        result = await po_service.update_po(po_id, request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update PO: {str(e)}"
        )


@router.post("/{po_id}/send")
async def send_po_to_farm(
    po_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Send PO to farm via email.

    **Actions:**
    - Updates status: draft → sent_to_farm
    - Generates PDF attachment
    - Sends email to vendor
    - Logs status change

    **Requirements:**
    - PO must be in 'draft' status
    """
    try:
        result = await po_service.send_po_to_farm(po_id, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send PO: {str(e)}"
        )


@router.get("/list", response_model=POListResponse)
async def list_pos(
    status: Optional[str] = Query(None, description="Filter by status"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    from_date: Optional[date] = Query(None, description="Filter by dispatch date from"),
    to_date: Optional[date] = Query(None, description="Filter by dispatch date to"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List purchase orders with filtering and pagination.

    **Filters:**
    - status: Filter by PO status
    - vendor_id: Filter by vendor
    - from_date/to_date: Filter by dispatch date range
    - item_id: Filter by item (in PO items)

    **Pagination:**
    - page: Page number (1-indexed)
    - limit: Items per page (max 100)

    **Returns:**
    - Paginated list of POs
    - Total count for pagination
    """
    try:
        result = await po_service.list_pos(
            status=status,
            vendor_id=vendor_id,
            from_date=from_date,
            to_date=to_date,
            item_id=item_id,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list POs: {str(e)}"
        )


@router.post("/export-zoho", dependencies=[Depends(require_admin)])
async def export_to_zoho(
    request: ExportToZohoRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Export selected POs to Zoho Books format (admin only).

    **Actions:**
    - Generates Zoho-compatible CSV
    - Includes final quantities from GRN
    - Includes damage/reject for debit notes
    - Marks POs as 'exported_to_zoho'
    - Locks POs from further edits

    **CSV Columns:**
    - PO details, vendor info, item details
    - Quantities, pricing
    - Damage/reject amounts
    - GRN and batch numbers

    **Returns:**
    - CSV file download
    """
    try:
        csv_bytes = await po_service.export_to_zoho(request.po_ids)

        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=po_export.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export to Zoho: {str(e)}"
        )


@router.get("/{po_id}/pdf")
async def generate_po_pdf(
    po_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate printable PO PDF.

    **PDF Contents:**
    - Company branding
    - PO details (number, dates, vendor)
    - Items table
    - Total amount
    - Terms & conditions
    - Authorized signature

    **Returns:**
    - PDF file download
    """
    try:
        pdf_bytes = await po_service.generate_po_pdf(po_id)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=PO-{po_id}.pdf"
            }
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


# ============================================================================
# VENDOR PRICING ROUTES (ADMIN ONLY)
# ============================================================================

@router.post("/vendor-pricing/manage", dependencies=[Depends(require_admin)])
async def manage_vendor_pricing(
    request: VendorPricingRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Add or update vendor-item pricing (admin only).

    **Features:**
    - Set vendor-specific prices for items
    - Support scheduled price changes (effective_from in future)
    - Manage price validity periods
    - Track who set each price

    **Use Cases:**
    - Set seasonal pricing
    - Schedule future price changes
    - Override Zoho default prices

    **Returns:**
    - Created pricing record with details
    """
    try:
        result = await po_service.manage_vendor_pricing(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage vendor pricing: {str(e)}"
        )


@router.get("/vendor-pricing/history", dependencies=[Depends(require_admin)])
async def get_price_history(
    vendor_id: int = Query(..., description="Vendor ID"),
    item_id: Optional[int] = Query(None, description="Optional item ID filter"),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get price history for vendor-item combinations (admin only).

    **Query Parameters:**
    - vendor_id: Required vendor ID
    - item_id: Optional item ID (if omitted, returns all items for vendor)

    **Returns:**
    - Historical pricing data with effective date ranges
    - Who created each price and when
    """
    try:
        results = await po_service.get_price_history(vendor_id, item_id)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price history: {str(e)}"
        )


@router.get("/vendor-pricing/active")
async def get_active_prices(
    vendor_id: int = Query(..., description="Vendor ID"),
    price_date: Optional[date] = Query(None, description="Date to check (defaults to today)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get all active vendor-item prices for a specific date.

    **Use Case:**
    - Auto-populate prices in PO creation form
    - Check current pricing for vendor

    **Query Parameters:**
    - vendor_id: Required vendor ID
    - price_date: Optional date (defaults to today)

    **Returns:**
    - List of active prices for all items
    - Includes item details (name, SKU)
    """
    try:
        results = await po_service.get_active_prices(vendor_id, price_date)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active prices: {str(e)}"
        )
