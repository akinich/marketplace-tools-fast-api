"""
================================================================================
Marketplace ERP - Allocation Sheet Routes
================================================================================
Version: 1.0.0
Last Updated: 2024-12-12

Description:
  API endpoints for allocation sheet management. Spreadsheet-style allocation
  interface organized by delivery date with Items × Customers matrix.

Endpoints:
  Sheet Management:
    GET    /api/v1/allocation/sheet/{delivery_date}  - Get/generate sheet
    PUT    /api/v1/allocation/cell/{cell_id}         - Update cell
    POST   /api/v1/allocation/sheet/{sheet_id}/auto-fill - Auto-fill SENT
    GET    /api/v1/allocation/dates                  - List available dates
  
  Invoice Generation:
    POST   /api/v1/allocation/customer/mark-ready    - Mark ready for invoice
    POST   /api/v1/allocation/customer/generate-invoice - Generate invoice
    GET    /api/v1/allocation/sheet/{sheet_id}/invoice-status - Status list
  
  Statistics:
    GET    /api/v1/allocation/sheet/{sheet_id}/statistics - Statistics dashboard

================================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from typing import Optional
from datetime import date
from app.schemas.allocation import (
    AllocationGridResponse,
    AllocationCellUpdate,
    CellUpdateResponse,
    AutoFillResponse,
    AvailableDatesResponse,
    MarkReadyRequest,
    GenerateInvoiceRequest,
    GenerateInvoiceResponse,
    InvoiceStatusListResponse,
    AllocationStatisticsResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import allocation_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# SHEET MANAGEMENT ROUTES
# ============================================================================

@router.get("/sheet/{delivery_date}", response_model=AllocationGridResponse)
async def get_allocation_sheet(
    delivery_date: date = Path(..., description="Delivery date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get or generate allocation sheet for delivery date.
    
    **Workflow:**
    1. Checks if sheet exists for date, creates if not
    2. Queries all SOs with this delivery_date
    3. Generates (item, customer) matrix
    4. Auto-fills SENT using FIFO if first time
    5. Returns complete grid data
    
    **Returns:**
    - Items list (rows)
    - Customers list (columns, sorted by SO number)
    - Cells data (ORDER, SENT for each combination)
    - Totals (total_order, total_sent, shortfall)
    
    **Use Cases:**
    - Initial sheet load
    - Refresh after changes
    - Date navigation
    """
    try:
        sheet_data = await allocation_service.generate_sheet_data(
            delivery_date=delivery_date,
            user_id=str(current_user.id)
        )
        return sheet_data
    except Exception as e:
        logger.error(f"❌ Failed to load sheet for {delivery_date}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load allocation sheet: {str(e)}"
        )


@router.put("/cell/{cell_id}", response_model=CellUpdateResponse)
async def update_allocation_cell(
    cell_id: int = Path(..., gt=0),
    update: AllocationCellUpdate = ...,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update ORDER or SENT quantity for a cell (optimistic locking).
    
    **Optimistic Updates:**
    - Frontend saves immediately
    - Backend validates version
    - If conflict: Returns error, frontend reloads
    
    **ORDER Quantity Update:**
    - Syncs to SO (sales_order_items)
    - Marks cell as modified (orange highlight)
    - Logs to audit trail
    
    **SENT Quantity Update:**
    - Recalculates batch allocation
    - Resets invoice_status to 'pending'
    
    **Version Conflict:**
    - HTTP 409 if version mismatch
    - Frontend must reload cell
    
    **Example:**
    ```json
    {
      "order_quantity": 12.0,
      "version": 5
    }
    ```
    """
    try:
        result = await allocation_service.update_cell(
            cell_id=cell_id,
            order_quantity=update.order_quantity,
            sent_quantity=update.sent_quantity,
            version=update.version,
            user_id=str(current_user.id)
        )
        return result
    except ValueError as ve:
        # Version conflict or validation error
        if "conflict" in str(ve).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(ve)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"❌ Failed to update cell {cell_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cell: {str(e)}"
        )


@router.post("/sheet/{sheet_id}/auto-fill", response_model=AutoFillResponse)
async def auto_fill_sheet(
    sheet_id: int = Path(..., gt=0),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Trigger FIFO auto-fill for all cells in sheet.
    
    **Use Cases:**
    - Recalculate after stock changes
    - Refresh allocations
    - Reset to FIFO suggestions
    
    **FIFO Priority:**
    1. Expiring soon (<2 days)
    2. Repacked batches (B###R)
    3. Oldest by entry_date
    
    **Customer Priority:**
    - SO number ascending (lower number = first)
    
    **Returns:**
    - Number of cells updated
    - List of shortfalls detected
    """
    try:
        # Run auto-fill
        await allocation_service.auto_fill_sent_quantities(sheet_id)
        
        # Get shortfalls
        # TODO: Implement shortfall detection
        
        return {
            'updated_cells': 0,  # TODO: Count updated cells
            'shortfalls': []
        }
    except Exception as e:
        logger.error(f"❌ Failed to auto-fill sheet {sheet_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-fill: {str(e)}"
        )


@router.get("/dates", response_model=AvailableDatesResponse)
async def get_available_dates(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get list of delivery dates with SO counts.
    
    **Returns:**
    - Dates with active SOs
    - SO count per date
    - Shortfall indicators
    - Invoice status summary
    
    **Use Cases:**
    - Date picker dropdown
    - Dashboard overview
    - Quick navigation
    """
    try:
        # TODO: Implement date listing
        return {
            'dates': []
        }
    except Exception as e:
        logger.error(f"❌ Failed to get available dates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dates: {str(e)}"
        )


# ============================================================================
# INVOICE GENERATION ROUTES
# ============================================================================

@router.post("/customer/mark-ready")
async def mark_customer_ready(
    request: MarkReadyRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Mark all cells for customer as ready for invoice generation.
    
    **Workflow:**
    1. Get all cells for customer on sheet
    2. Update invoice_status = 'ready'
    3. Return count
    
    **UI Action:**
    - User clicks "Mark Ready" button
    - Button changes to "Generate Invoice"
    """
    try:
        # TODO: Implement mark ready
        return {
            'cells_marked': 0,
            'invoice_status': 'ready'
        }
    except Exception as e:
        logger.error(f"❌ Failed to mark customer ready: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark ready: {str(e)}"
        )


@router.post("/customer/generate-invoice", response_model=GenerateInvoiceResponse)
async def generate_customer_invoice(
    request: GenerateInvoiceRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate invoice for customer using SENT quantities.
    
    **Workflow:**
    1. Get all cells with invoice_status='ready' for customer
    2. Create invoice with SENT quantities (not ORDER)
    3. Call /inventory/confirm-allocation (debit stock)
    4. Update cells: invoice_status='invoiced', invoice_id=X
    
    **Stock Flow:**
    - Stock was allocated (available → allocated) when SO created
    - Now debited (allocated → delivered, qty=0)
    
    **Returns:**
    - Invoice ID and number
    - Total amount
    - Stock debit confirmation
    """
    try:
        # TODO: Implement invoice generation
        return {
            'invoice_id': 0,
            'invoice_number': '',
            'total_amount': 0,
            'items_invoiced': 0,
            'stock_debited': False
        }
    except Exception as e:
        logger.error(f"❌ Failed to generate invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


@router.get("/sheet/{sheet_id}/invoice-status", response_model=InvoiceStatusListResponse)
async def get_invoice_status(
    sheet_id: int = Path(..., gt=0),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get invoice status for all customers on sheet.
    
    **Returns:**
    - Customer list with status (pending/ready/invoiced)
    - Items count per customer
    - Total SENT quantity
    - Shortfall indicators
    
    **Use Cases:**
    - Invoice Status tab
    - Quick overview of invoice progress
    - Batch operations
    """
    try:
        # TODO: Implement status list
        return {
            'customers': []
        }
    except Exception as e:
        logger.error(f"❌ Failed to get invoice status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# ============================================================================
# STATISTICS ROUTES
# ============================================================================

@router.get("/sheet/{sheet_id}/statistics", response_model=AllocationStatisticsResponse)
async def get_sheet_statistics(
    sheet_id: int = Path(..., gt=0),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get comprehensive statistics for sheet.
    
    **Returns:**
    - Summary: total ordered, sent, shortfall, fulfillment rate
    - By Item: detailed item breakdown
    - By Customer: customer fulfillment rates
    - Shortfalls: list of unfulfilled items
    
    **Use Cases:**
    - Statistics tab
    - Management dashboard
    - Reports
    """
    try:
        # TODO: Implement statistics
        return {
            'summary': {
                'total_ordered': 0,
                'total_sent': 0,
                'total_shortfall': 0,
                'fulfillment_rate': 0
            },
            'by_item': [],
            'by_customer': [],
            'shortfalls': []
        }
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
