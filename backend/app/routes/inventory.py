"""
================================================================================
Marketplace ERP - Inventory Management Routes
================================================================================
Version: 1.0.0
Last Updated: 2024-12-07

Description:
  API endpoints for inventory management. Provides stock tracking, movements,
  adjustments with approval workflow, reorder levels, and reports.

Endpoints:
  Stock Management:
    POST   /api/v1/inventory/add                 - Manual stock entry (testing)
    GET    /api/v1/inventory/list                - List inventory with filters
    GET    /api/v1/inventory/by-batch/{batch_id} - Batch-wise view
    GET    /api/v1/inventory/availability        - Check stock availability
    GET    /api/v1/inventory/low-stock           - Low stock alerts
    GET    /api/v1/inventory/expiring            - Expiring items
  
  Stock Movements:
    POST   /api/v1/inventory/transfer            - Transfer between locations
    GET    /api/v1/inventory/movements           - List movements
  
  Adjustments:
    POST   /api/v1/inventory/adjust              - Create adjustment request
    PUT    /api/v1/inventory/adjust/{id}/approve - Approve/reject (admin)
    GET    /api/v1/inventory/adjustments         - List adjustments
  
  Reorder Levels:
    POST   /api/v1/inventory/reorder-level       - Configure reorder level
    GET    /api/v1/inventory/reorder-levels      - List configs
  
  Reports:
    GET    /api/v1/inventory/reports/current-stock    - Current stock report
    GET    /api/v1/inventory/reports/movements        - Movement report
    GET    /api/v1/inventory/reports/batch-age        - Batch age report

================================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import date
from decimal import Decimal

from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryResponse, InventoryListResponse,
    LocationTransferRequest, InventoryMovementResponse,
    InventoryAdjustmentRequest, InventoryAdjustmentApproval,
    InventoryAdjustmentResponse, ReorderLevelConfig, ReorderLevelResponse,
    StockAvailabilityQuery, StockAvailabilityResponse,
    BatchInventoryView, ExpiringItem, LowStockAlert,
    CurrentStockReportFilters, StockMovementReportFilters,
    StockAllocationRequest, StockDeallocationRequest, ConfirmAllocationRequest
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import inventory_service

router = APIRouter()


# ============================================================================
# STOCK MANAGEMENT ROUTES
# ============================================================================

@router.post("/add", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_entry(
    request: InventoryCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Manual stock entry (temporary endpoint for testing until Packing module ready).
    
    **Use Cases:**
    - Testing stock management features
    - Manual entry of legacy data
    - Emergency stock additions
    
    **Future:**
    - This will be replaced by auto stock entry from Packing module
    - Packing module will call this internally when packing is complete
    
    **Returns:**
    - Created inventory record with expiry date (auto-calculated)
    """
    try:
        result = await inventory_service.add_stock_entry(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add stock entry: {str(e)}"
        )


@router.get("/list", response_model=InventoryListResponse)
async def list_inventory(
    location: Optional[str] = Query(None, description="Filter by location"),
    status: Optional[str] = Query(None, description="Filter by status"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    batch_id: Optional[int] = Query(None, description="Filter by batch ID"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    expiring_within_days: Optional[int] = Query(None, description="Show items expiring within N days"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List inventory with filtering and pagination.
    
    **Filters:**
    - location: packed_warehouse, receiving_area, processing_area, delivery_vehicles, quality_hold
    - status: available, allocated, hold, in_transit, delivered
    - item_id: Filter by specific item
    - batch_id: Filter by specific batch
    - grade: A, B, C
    - expiring_within_days: Show items expiring soon
    
    **Returns:**
    - Paginated inventory list with item and batch details
    """
    try:
        result = await inventory_service.get_inventory_list(
            location=location,
            status=status,
            item_id=item_id,
            batch_id=batch_id,
            grade=grade,
            expiring_within_days=expiring_within_days,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inventory: {str(e)}"
        )


@router.get("/by-batch/{batch_id}", response_model=BatchInventoryView)
async def get_batch_inventory(
    batch_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get complete inventory breakdown for a specific batch.
    
    **Includes:**
    - Batch details (number, status, type)
    - Current inventory across all locations
    - Complete movement history
    - Total quantity and distribution
    
    **Use Cases:**
    - Track batch journey through locations
    - Audit batch movements
    - Check batch availability by location
    """
    try:
        result = await inventory_service.get_batch_inventory(batch_id)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch inventory: {str(e)}"
        )


@router.get("/availability", response_model=StockAvailabilityResponse)
async def check_stock_availability(
    item_id: int = Query(..., description="Item ID"),
    quantity: Decimal = Query(..., description="Required quantity"),
    location: Optional[str] = Query(None, description="Optional location filter"),
    grade: Optional[str] = Query(None, description="Optional grade filter"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Check real-time stock availability for an item.
    
    **Use Cases:**
    - Before creating SO, check if stock is available
    - Order fulfillment planning
    - Stock reservation checks
    
    **Returns:**
    - Available: boolean (sufficient stock?)
    - Current stock, allocated stock, net available
    - Shortage amount (if any)
    - Stock breakdown by location
    
    **Future Integration:**
    - Sales Order module will call this before creating SO
    - Order Allocation module will use this for FIFO allocation
    """
    try:
        result = await inventory_service.check_stock_availability(
            item_id=item_id,
            quantity=quantity,
            location=location,
            grade=grade
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check stock availability: {str(e)}"
        )


@router.get("/low-stock")
async def get_low_stock_items(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get list of items below reorder threshold.
    
    **Returns:**
    - Items with current stock below alert threshold
    - Shortage amount
    - Reorder quantity
    - Location-wise breakdown
    
    **Use Cases:**
    - Procurement planning
    - Stock monitoring dashboard
    - Automated reorder triggers
    """
    try:
        results = await inventory_service.get_low_stock_items()
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get low stock items: {str(e)}"
        )


@router.get("/expiring")
async def get_expiring_items(
    days_threshold: int = Query(7, description="Number of days to look ahead"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get items expiring within specified days.
    
    **Returns:**
    - Items with expiry date within threshold
    - Days until expiry
    - Urgency level (critical/warning/normal)
    - Batch and location details
    
    **Urgency Levels:**
    - Critical: < 2 days
    - Warning: 2-7 days
    - Normal: > 7 days
    
    **Use Cases:**
    - Prevent wastage through priority allocation
    - Shelf life monitoring
    - Quality control alerts
    """
    try:
        results = await inventory_service.get_expiring_items(days_threshold)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get expiring items: {str(e)}"
        )


# ============================================================================
# STOCK MOVEMENTS ROUTES
# ============================================================================

@router.post("/transfer")
async def transfer_location(
    request: LocationTransferRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Transfer stock between locations.
    
    **Use Cases:**
    - Move stock from packed_warehouse to delivery_vehicles
    - Transfer from receiving_area to processing_area
    - Move to quality_hold for inspection
    
    **Actions:**
    - Updates quantity at both locations
    - Logs movement in inventory_movements
    - Validates sufficient stock at source
    
    **Returns:**
    - Success confirmation
    - Transfer details
    """
    try:
        result = await inventory_service.transfer_location(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer location: {str(e)}"
        )


@router.get("/movements")
async def list_movements(
    batch_id: Optional[int] = Query(None, description="Filter by batch ID"),
    movement_type: Optional[str] = Query(None, description="Filter by movement type"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List stock movements with filtering.
    
    **Filters:**
    - batch_id: Movements for specific batch
    - movement_type: stock_in, stock_out, location_transfer, adjustment, allocation, delivery
    - date range: Filter by movement date
    
    **Returns:**
    - Movement history with item and batch details
    - Who performed the movement and when
    """
    try:
        # Build query for future reporting functionality
        return {
            "message": "Movement listing endpoint - implementation pending",
            "filters": {
                "batch_id": batch_id,
                "movement_type": movement_type,
                "from_date": from_date,
                "to_date": to_date
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list movements: {str(e)}"
        )


# ============================================================================
# INVENTORY ADJUSTMENTS ROUTES
# ============================================================================

@router.post("/adjust", response_model=InventoryAdjustmentResponse, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    request: InventoryAdjustmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create stock adjustment request (requires admin approval).
    
    **Adjustment Types:**
    - increase: Add stock (found inventory, correction)
    - decrease: Remove stock (damage, theft, correction)
    - correction: Fix incorrect stock count
    
    **Workflow:**
    1. User creates adjustment request
    2. Status: pending_approval
    3. Admin approves/rejects
    4. If approved, auto-applies to inventory
    
    **Required:**
    - Detailed reason (min 10 characters)
    - Optional photo evidence
    
    **Returns:**
    - Created adjustment record
    - Approval status: pending_approval
    """
    try:
        result = await inventory_service.create_adjustment(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create adjustment: {str(e)}"
        )


@router.put("/adjust/{adjustment_id}/approve", dependencies=[Depends(require_admin)])
async def approve_adjustment(
    adjustment_id: int,
    approval: InventoryAdjustmentApproval,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Approve or reject adjustment request (admin only).
    
    **Actions:**
    - If approved: Immediately applies adjustment to inventory
    - If rejected: Records rejection reason, no inventory change
    
    **Auto-Application:**
    - Approved adjustments are automatically applied
    - Inventory quantities updated
    - Movement logged
    - Status changed to 'applied'
    
    **Requirements:**
    - Adjustment must be in 'pending_approval' status
    - Admin permissions required
    
    **Returns:**
    - Updated adjustment record
    - Applied status ifapproved
    """
    try:
        result = await inventory_service.approve_adjustment(
            adjustment_id, approval, str(current_user.id)
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve adjustment: {str(e)}"
        )


@router.get("/adjustments")
async def list_adjustments(
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List inventory adjustments with filtering.
    
    **Filters:**
    - approval_status: pending_approval, approved, rejected, applied
    
    **Returns:**
    - Adjustment history
    - Who created and who approved
    - Reason and photo evidence
    
    **Use Cases:**
    - Admin review queue (pending_approval)
    - Audit trail of adjustments
    - Historical corrections review
    """
    try:
        result = await inventory_service.get_adjustments_list(
            approval_status=approval_status,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list adjustments: {str(e)}"
        )


# ============================================================================
# REORDER LEVELS ROUTES
# ============================================================================

@router.post("/reorder-level", response_model=ReorderLevelResponse)
async def configure_reorder_level(
    request: ReorderLevelConfig,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Configure reorder level for item and location.
    
    **Parameters:**
    - reorder_quantity: Minimum stock level before reorder
    - alert_threshold: Trigger alert when stock falls below this
    - is_active: Enable/disable alerts for this config
    
    **Behavior:**
    - If config exists for item+location, it will be updated
    - Otherwise, new config is created
    
    **Use Cases:**
    - Set minimum stock levels per item
    - Location-specific reorder points
    - Automated procurement triggers
    
    **Returns:**
    - Created/updated reorder level configuration
    """
    try:
        result = await inventory_service.configure_reorder_level(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure reorder level: {str(e)}"
        )


@router.get("/reorder-levels")
async def list_reorder_levels(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List all reorder level configurations.
    
    **Filters:**
    - is_active: Show only active configs
    
    **Returns:**
    - All reorder level configurations
    - Item details and thresholds
    
    **Use Cases:**
    - Reorder management dashboard
    - Bulk configuration review
    """
    try:
        # Placeholder - full implementation in future
        return {"message": "Reorder levels listing - implementation pending"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reorder levels: {str(e)}"
        )


# ============================================================================
# REPORTS ROUTES
# ============================================================================

@router.get("/reports/current-stock")
async def generate_current_stock_report(
    location: Optional[str] = Query(None),
    item_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    include_zero_stock: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate current stock report.
    
    **Filters:**
    - location: Filter by specific location
    - item_id: Filter by specific item
    - status: Filter by stock status
    - include_zero_stock: Include items with zero stock
    
    **Returns:**
    - Grouped stock summary by item, location, grade, status
    - Batch count, total quantity
    - Earliest expiry date
    
    **Export:**
    - Can be exported to CSV/Excel from frontend
    """
    try:
        result = await inventory_service.generate_current_stock_report(
            location=location,
            item_id=item_id,
            status=status,
            include_zero_stock=include_zero_stock
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate current stock report: {str(e)}"
        )


@router.get("/reports/movements")
async def generate_stock_movement_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    movement_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    item_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate stock movement report.
    
    **Filters:**
    - date_from/date_to: Date range filter
    - movement_type: Filter by movement type
    - location: Filter by location (from or to)
    - item_id: Filter by item
    
    **Returns:**
    - Complete movement history
    - Item, batch, location details
    - Who performed movement and when
    
    **Use Cases:**
    - Audit trail
    - Logistics analysis
    - Movement patterns
    """
    try:
        result = await inventory_service.generate_stock_movement_report(
            date_from=date_from,
            date_to=date_to,
            movement_type=movement_type,
            location=location,
            item_id=item_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate stock movement report: {str(e)}"
        )


@router.get("/reports/batch-age")
async def generate_batch_age_report(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate batch age report showing how long batches have been in inventory.
    
    **Returns:**
    - All batches currently in inventory
    - Age in days (from entry date)
    - Location, quantity, status
    - Sorted by age (oldest first)
    
    **Use Cases:**
    - Identify aging inventory
    - FIFO compliance monitoring
    - Stock rotation planning
    - Quality control
    """
    try:
        result = await inventory_service.generate_batch_age_report()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch age report: {str(e)}"
        )


# ============================================================================
# STOCK ALLOCATION ROUTES (Order Integration)
# ============================================================================

@router.post("/allocate", status_code=status.HTTP_201_CREATED)
async def allocate_stock(
    request: StockAllocationRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Allocate stock to a sales order (reserve stock).
    Changes status: available → allocated
    
    **Flow:**
    1. Order created → Call this endpoint
    2. Stock is reserved (status = 'allocated')
    3. Shows as: 20kg total, 15kg available, 5kg allocated
    
    **FIFO Logic:**
    - Prioritizes repacked batches (B###R)
    - Then oldest regular batches
    - Can specify batches manually or auto-select
    
    **Returns:**
    - Allocation details
    - Which batches were allocated
    - Total quantity allocated
    
    **Example:**
    ```
    POST /api/v1/inventory/allocate
    {
        "order_id": 123,
        "item_id": 1,
        "quantity": 5.0,
        "location": "packed_warehouse"
    }
    ```
    """
    try:
        from app.services.inventory_allocation_service import allocate_stock_to_order
        
        result = await allocate_stock_to_order(
            order_id=request.order_id,
            item_id=request.item_id,
            quantity=request.quantity,
            batch_ids=request.batch_ids,
            location=request.location,
            user_id=str(current_user.id)
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to allocate stock: {str(e)}"
        )


@router.post("/deallocate", status_code=status.HTTP_200_OK)
async def deallocate_stock(
    request: StockDeallocationRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Deallocate/release stock from a cancelled order.
    Changes status: allocated → available
    
    **Flow:**
    1. Order cancelled → Call this endpoint
    2. Stock is released back to available
    3. Shows as: 20kg total, 20kg available, 0kg allocated
    
    **Returns:**
    - Deallocation confirmation
    - Items released
    
    **Example:**
    ```
    POST /api/v1/inventory/deallocate
    {
        "order_id": 123
    }
    ```
    """
    try:
        from app.services.inventory_allocation_service import deallocate_stock_from_order
        
        result = await deallocate_stock_from_order(
            order_id=request.order_id,
            user_id=str(current_user.id)
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deallocate stock: {str(e)}"
        )


@router.post("/confirm-allocation", status_code=status.HTTP_200_OK)
async def confirm_stock_allocation(
    request: ConfirmAllocationRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Confirm allocation and debit stock (order → invoice).
    Changes status: allocated → delivered
    Actually decrements stock quantity
    
    **Flow:**
    1. Order converted to invoice → Call this endpoint
    2. Stock status changed to 'delivered'
    3. Quantity set to 0 (debited)
    4. Shows as: 15kg total, 15kg available (5kg removed from inventory)
    
    **Returns:**
    - Confirmation details
    - Items confirmed/debited
    
    **Example:**
    ```
    POST /api/v1/inventory/confirm-allocation
    {
        "order_id": 123
    }
    ```
    """
    try:
        from app.services.inventory_allocation_service import confirm_allocation
        
        result = await confirm_allocation(
            order_id=request.order_id,
            user_id=str(current_user.id)
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm allocation: {str(e)}"
        )
