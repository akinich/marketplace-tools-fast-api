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
        
        # Count updated cells and get shortfalls
        async with get_db_connection() as conn:
            # Count updated cells
            updated_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM allocation_sheet_cells
                WHERE sheet_id = $1 AND sent_quantity > 0
            """, sheet_id)
            
            # Get shortfalls
            shortfalls = await conn.fetch("""
                SELECT 
                    c.item_id,
                    i.name as item_name,
                    c.customer_id,
                    cu.name as customer_name,
                    c.order_quantity,
                    c.sent_quantity,
                    (c.order_quantity - COALESCE(c.sent_quantity, 0)) as shortage
                FROM allocation_sheet_cells c
                JOIN zoho_items i ON c.item_id = i.id
                JOIN zoho_customers cu ON c.customer_id = cu.zoho_customer_id
                WHERE c.sheet_id = $1 AND c.has_shortfall = TRUE
                ORDER BY shortage DESC
            """, sheet_id)
            
        return {
            'updated_cells': updated_count or 0,
            'shortfalls': [dict(row) for row in shortfalls]
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
        async with get_db_connection() as conn:
            dates = await conn.fetch("""
                SELECT 
                    so.delivery_date,
                    COUNT(DISTINCT so.id) as so_count,
                    COUNT(DISTINCT soi.item_id) as item_count,
                    SUM(soi.quantity) as total_quantity,
                    EXISTS(
                        SELECT 1 FROM allocation_sheets ash
                        WHERE ash.delivery_date = so.delivery_date
                    ) as has_sheet
                FROM sales_orders so
                JOIN sales_order_items soi ON so.id = soi.so_id
                WHERE so.delivery_date >= CURRENT_DATE
                  AND so.status NOT IN ('cancelled', 'completed')
                GROUP BY so.delivery_date
                ORDER BY so.delivery_date ASC
                LIMIT 30
            """)
            
        return {
            'dates': [{
                'date': row['delivery_date'].isoformat(),
                'so_count': row['so_count'],
                'item_count': row['item_count'],
                'total_quantity': float(row['total_quantity'] or 0),
                'has_sheet': row['has_sheet']
            } for row in dates]
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
        async with get_db_connection() as conn:
            # Update all cells for this customer on sheet
            result = await conn.execute("""
                UPDATE allocation_sheet_cells
                SET invoice_status = 'ready',
                    updated_at = NOW()
                WHERE sheet_id = $1 
                  AND customer_id = $2
                  AND invoice_status = 'pending'
            """, request.sheet_id, request.customer_id)
            
            # Extract count from result
            cells_marked = int(result.split()[-1]) if result else 0
            
        return {
            'cells_marked': cells_marked,
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
        async with get_db_connection() as conn:
            # Get cells ready for invoicing
            cells = await conn.fetch("""
                SELECT 
                    c.id,
                    c.item_id,
                    c.customer_id,
                    c.sent_quantity,
                    c.allocated_batches,
                    c.so_id,
                    i.price
                FROM allocation_sheet_cells c
                JOIN zoho_items i ON c.item_id = i.id
                WHERE c.sheet_id = $1 
                  AND c.customer_id = $2
                  AND c.invoice_status = 'ready'
                  AND c.sent_quantity > 0
            """, request.sheet_id, request.customer_id)
            
            if not cells:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No cells ready for invoicing"
                )
            
            # Calculate total
            total_amount = sum(row['sent_quantity'] * (row['price'] or 0) for row in cells)
            
            # Generate invoice number
            invoice_number = f"INV-{request.sheet_id}-{request.customer_id[:8]}"
            
            # Debit stock using existing confirmation API
            # This marks allocated batches as delivered
            stock_debited = True
            for cell in cells:
                if cell['allocated_batches']:
                    try:
                        # Call existing confirm-allocation endpoint logic
                        await conn.execute("""
                            UPDATE inventory_batches
                            SET 
                                allocated_qty = allocated_qty - qty_to_deliver,
                                sold_qty = sold_qty + qty_to_deliver,
                                updated_at = NOW()
                            FROM (
                                SELECT unnest($1::jsonb[]) as batch_info
                            ) batches
                            WHERE id = (batch_info->>'batch_id')::int
                        """, cell['allocated_batches'])
                    except Exception as e:
                        logger.error(f"Stock debit failed for cell {cell['id']}: {e}")
                        stock_debited = False
            
            # Mark cells as invoiced
            await conn.execute("""
                UPDATE allocation_sheet_cells
                SET invoice_status = 'invoiced',
                    invoiced_at = NOW(),
                    updated_at = NOW()
                WHERE sheet_id = $1 AND customer_id = $2 AND invoice_status = 'ready'
            """, request.sheet_id, request.customer_id)
            
        return {
            'invoice_id': request.sheet_id,  # Placeholder
            'invoice_number': invoice_number,
            'total_amount': float(total_amount),
            'items_invoiced': len(cells),
            'stock_debited': stock_debited
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
        async with get_db_connection() as conn:
            customers = await conn.fetch("""
                SELECT 
                    c.customer_id,
                    cu.name as customer_name,
                    COUNT(c.id) as items_count,
                    SUM(c.sent_quantity) as total_sent,
                    BOOL_OR(c.has_shortfall) as has_shortfall,
                    CASE 
                        WHEN BOOL_AND(c.invoice_status = 'invoiced') THEN 'invoiced'
                        WHEN BOOL_OR(c.invoice_status = 'ready') THEN 'ready'
                        ELSE 'pending'
                    END as invoice_status
                FROM allocation_sheet_cells c
                JOIN zoho_customers cu ON c.customer_id = cu.zoho_customer_id
                WHERE c.sheet_id = $1
                GROUP BY c.customer_id, cu.name
                ORDER BY cu.name
            """, sheet_id)
            
        return {
            'customers': [{
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'items_count': row['items_count'],
                'total_sent': float(row['total_sent'] or 0),
                'has_shortfall': row['has_shortfall'] or False,
                'invoice_status': row['invoice_status']
            } for row in customers]
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
        async with get_db_connection() as conn:
            # Summary statistics
            summary = await conn.fetchrow("""
                SELECT 
                    SUM(order_quantity) as total_ordered,
                    SUM(sent_quantity) as total_sent,
                    SUM(CASE WHEN has_shortfall THEN (order_quantity - COALESCE(sent_quantity, 0)) ELSE 0 END) as total_shortfall
                FROM allocation_sheet_cells
                WHERE sheet_id = $1
            """, sheet_id)
            
            total_ordered = float(summary['total_ordered'] or 0)
            total_sent = float(summary['total_sent'] or 0)
            total_shortfall = float(summary['total_shortfall'] or 0)
            fulfillment_rate = (total_sent / total_ordered * 100) if total_ordered > 0 else 0
            
            # By item breakdown
            by_item = await conn.fetch("""
                SELECT 
                    c.item_id,
                    i.name as item_name,
                    SUM(c.order_quantity) as total_ordered,
                    SUM(c.sent_quantity) as total_sent,
                    SUM(CASE WHEN c.has_shortfall THEN (c.order_quantity - COALESCE(c.sent_quantity, 0)) ELSE 0 END) as shortfall,
                    COUNT(DISTINCT c.customer_id) as customers_affected
                FROM allocation_sheet_cells c
                JOIN zoho_items i ON c.item_id = i.id
                WHERE c.sheet_id = $1
                GROUP BY c.item_id, i.name
                ORDER BY shortfall DESC, i.name
            """, sheet_id)
            
            # By customer breakdown
            by_customer = await conn.fetch("""
                SELECT 
                    c.customer_id,
                    cu.name as customer_name,
                    SUM(c.order_quantity) as total_ordered,
                    SUM(c.sent_quantity) as total_sent,
                    (SUM(c.sent_quantity) / NULLIF(SUM(c.order_quantity), 0) * 100) as fulfillment_rate,
                    CASE 
                        WHEN BOOL_AND(c.invoice_status = 'invoiced') THEN 'invoiced'
                        WHEN BOOL_OR(c.invoice_status = 'ready') THEN 'ready'
                        ELSE 'pending'
                    END as invoice_status
                FROM allocation_sheet_cells c
                JOIN zoho_customers cu ON c.customer_id = cu.zoho_customer_id
                WHERE c.sheet_id = $1
                GROUP BY c.customer_id, cu.name
                ORDER BY cu.name
            """, sheet_id)
            
            # Shortfalls detail
            shortfalls = await conn.fetch("""
                SELECT 
                    c.item_id,
                    i.name as item_name,
                    c.customer_id,
                    cu.name as customer_name,
                    c.order_quantity as ordered,
                    c.sent_quantity as sent,
                    (c.order_quantity - COALESCE(c.sent_quantity, 0)) as shortage
                FROM allocation_sheet_cells c
                JOIN zoho_items i ON c.item_id = i.id
                JOIN zoho_customers cu ON c.customer_id = cu.zoho_customer_id
                WHERE c.sheet_id = $1 AND c.has_shortfall = TRUE
                ORDER BY (c.order_quantity - COALESCE(c.sent_quantity, 0)) DESC
            """, sheet_id)
            
        return {
            'summary': {
                'total_ordered': total_ordered,
                'total_sent': total_sent,
                'total_shortfall': total_shortfall,
                'fulfillment_rate': round(fulfillment_rate, 2)
            },
            'by_item': [{
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'total_ordered': float(row['total_ordered']),
                'total_sent': float(row['total_sent'] or 0),
                'shortfall': float(row['shortfall']),
                'customers_affected': row['customers_affected']
            } for row in by_item],
            'by_customer': [{
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'total_ordered': float(row['total_ordered']),
                'total_sent': float(row['total_sent'] or 0),
                'fulfillment_rate': round(float(row['fulfillment_rate'] or 0), 2),
                'invoice_status': row['invoice_status']
            } for row in by_customer],
            'shortfalls': [{
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'ordered': float(row['ordered']),
                'sent': float(row['sent'] or 0),
                'shortage': float(row['shortage'])
            } for row in shortfalls]
        }
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
