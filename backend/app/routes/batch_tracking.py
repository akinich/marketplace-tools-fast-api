"""
================================================================================
Marketplace ERP - Batch Tracking Routes
================================================================================
Version: 1.0.0
Last Updated: 2024-12-04

Description:
  API endpoints for batch tracking module. Provides complete traceability from
  farm to customer with batch number generation, history tracking, search,
  and repacking workflows.

Endpoints:
  POST   /batches/generate                  - Generate new batch number
  GET    /batches/{batch_number}            - Get batch details
  GET    /batches/{batch_number}/timeline   - Get batch timeline
  POST   /batches/search                    - Search batches
  POST   /batches/{batch_number}/repack     - Create repacked batch
  GET    /batches/active                    - List active batches
  POST   /batches/{batch_number}/archive    - Archive batch (system/admin)
  POST   /batches/{batch_number}/history    - Add history event

================================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import datetime

from app.schemas.batch_tracking import (
    GenerateBatchRequest, RepackBatchRequest, AddBatchHistoryRequest,
    SearchBatchesRequest, BatchResponse, BatchDetailResponse,
    BatchTimelineResponse, BatchSearchResponse, RepackBatchResponse,
    BatchStatus
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import batch_tracking_service
from app.database import get_db, fetch_one, fetch_all

router = APIRouter()


# ============================================================================
# BATCH GENERATION
# ============================================================================

@router.post("/generate", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def generate_batch(
    request: GenerateBatchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate new sequential batch number.

    Called by GRN module when creating a new GRN.
    Atomically increments sequence and creates batch record.

    **Returns:**
    - batch_id: Unique batch ID
    - batch_number: Sequential batch number (B001, B002, etc.)
    - status: Initial status (ordered)
    - created_at: Timestamp
    """
    try:
        result = await batch_tracking_service.generate_batch_number(
            po_id=request.po_id,
            grn_id=request.grn_id,
            created_by=str(current_user.id)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch number: {str(e)}"
        )


# ============================================================================
# BATCH RETRIEVAL
# ============================================================================

# NOTE: /active endpoint MUST come before /{batch_number} to avoid route conflict
@router.get("/active", response_model=BatchSearchResponse)
async def get_active_batches(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List all active (non-archived) batches.

    **Query Parameters:**
    - status: Optional status filter
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 100)

    **Returns:**
    Paginated list of active batches.
    """
    try:
        results = await batch_tracking_service.get_active_batches(
            status=status,
            page=page,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active batches: {str(e)}"
        )


@router.get("/{batch_number}", response_model=BatchDetailResponse)
async def get_batch_details(
    batch_number: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get complete batch details with history and documents.

    Includes:
    - Batch metadata (status, repack info, timestamps)
    - All linked documents (PO, GRN, SO, invoices)
    - Complete history timeline with events

    **Path Parameters:**
    - batch_number: Batch number (e.g., B001, B001R)
    """
    try:
        batch = await batch_tracking_service.get_batch_details(batch_number)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_number} not found"
            )
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch details: {str(e)}"
        )


@router.get("/{batch_number}/timeline", response_model=BatchTimelineResponse)
async def get_batch_timeline(
    batch_number: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get visual timeline of batch journey through stages.

    Returns chronological stages with timestamps and status.
    Used for timeline visualization in frontend.

    **Path Parameters:**
    - batch_number: Batch number
    """
    try:
        timeline = await batch_tracking_service.get_batch_timeline(batch_number)
        if not timeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_number} not found"
            )
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch timeline: {str(e)}"
        )


# ============================================================================
# BATCH SEARCH
# ============================================================================

@router.post("/search", response_model=BatchSearchResponse)
async def search_batches(
    filters: SearchBatchesRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Search batches with multiple filter criteria.

    Supports filtering by:
    - Batch number (partial match)
    - PO, GRN, SO numbers
    - Farm name, item name, customer name
    - Status
    - Date range
    - Archived flag

    **Returns:**
    Paginated search results with total count.
    """
    try:
        results = await batch_tracking_service.search_batches(filters)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search batches: {str(e)}"
        )


# ============================================================================
# BATCH REPACKING
# ============================================================================

@router.post("/{batch_number}/repack", response_model=RepackBatchResponse, status_code=status.HTTP_201_CREATED)
async def repack_batch(
    batch_number: str,
    repack_data: RepackBatchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create repacked batch (B###R) from damaged items.

    Called when cold storage damage requires repacking.
    Creates new batch with R suffix (e.g., B001 → B001R).

    **Validation:**
    - Parent batch must exist
    - Parent batch cannot already have a repacked child
    - Repacked quantity must be <= damaged quantity
    - Photos required

    **Returns:**
    - parent_batch: Original batch number
    - new_batch_number: Repacked batch number (B###R)
    - new_batch_id: New batch ID
    - status: Batch status (in_inventory)
    - created_at: Timestamp

    **Path Parameters:**
    - batch_number: Parent batch number
    """
    try:
        result = await batch_tracking_service.create_repacked_batch(
            parent_batch_number=batch_number,
            repack_data=repack_data,
            created_by=str(current_user.id)
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
            detail=f"Failed to create repacked batch: {str(e)}"
        )


# ============================================================================
# BATCH HISTORY
# ============================================================================

@router.post("/{batch_number}/history", status_code=status.HTTP_201_CREATED)
async def add_batch_history(
    batch_number: str,
    event: AddBatchHistoryRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Add event to batch history.

    Called by other modules (GRN, Grading, Packing, etc.) to log
    events in the batch journey.

    Updates batch status if new_status is provided.

    **Path Parameters:**
    - batch_number: Batch number

    **Request Body:**
    - stage: Stage of the event (po, grn, grading, packing, etc.)
    - event_type: Type of event (created, received, graded, etc.)
    - event_details: Stage-specific data (JSON)
    - new_status: Optional new batch status
    - location: Optional physical location
    """
    try:
        result = await batch_tracking_service.add_batch_history(
            batch_number=batch_number,
            event=event,
            created_by=str(current_user.id)
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
            detail=f"Failed to add batch history: {str(e)}"
        )


# ============================================================================
# BATCH ARCHIVING
# ============================================================================

@router.post("/{batch_number}/archive", dependencies=[Depends(require_admin)])
async def archive_batch(
    batch_number: str,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Archive a batch (admin only).

    Typically called automatically by scheduled job for batches
    3+ days after delivery. Can be manually triggered by admin.

    **Path Parameters:**
    - batch_number: Batch number to archive

    **Permissions:**
    Admin only
    """
    try:
        # Get batch
        batch = await batch_tracking_service.get_batch_details(batch_number)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_number} not found"
            )

        # Update status to archived
        query = """
            UPDATE batches
            SET status = $1, archived_at = NOW()
            WHERE batch_number = $2
            RETURNING archived_at
        """
        result = await fetch_one(
            query,
            BatchStatus.ARCHIVED.value,
            batch_number
        )

        return {
            "batch_number": batch_number,
            "archived_at": result['archived_at'] if result else datetime.now(),
            "status": "archived"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive batch: {str(e)}"
        )


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@router.get("/stats/summary")
async def get_batch_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get batch statistics summary.

    Returns:
    - Total batches
    - Active batches
    - Archived batches
    - Repacked batches
    - Batches by status
    """
    try:
        from app.database import fetch_all

        # Get counts by status
        status_query = """
            SELECT status, COUNT(*) as count
            FROM batches
            WHERE archived_at IS NULL
            GROUP BY status
        """
        status_counts = await fetch_all(status_query)

        # Get repacked count
        repack_query = """
            SELECT COUNT(*) as count
            FROM batches
            WHERE is_repacked = true
        """
        repack_result = await fetch_all(repack_query)
        repack_count = repack_result[0]['count'] if repack_result else 0

        # Get archived count
        archived_query = """
            SELECT COUNT(*) as count
            FROM batches
            WHERE archived_at IS NOT NULL
        """
        archived_result = await fetch_all(archived_query)
        archived_count = archived_result[0]['count'] if archived_result else 0

        # Total
        total_query = "SELECT COUNT(*) as count FROM batches"
        total_result = await fetch_all(total_query)
        total_count = total_result[0]['count'] if total_result else 0

        return {
            "total_batches": total_count,
            "active_batches": total_count - archived_count,
            "archived_batches": archived_count,
            "repacked_batches": repack_count,
            "by_status": {row['status']: row['count'] for row in status_counts}
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch stats: {str(e)}"
        )


# ============================================================================
# BATCH CONFIGURATION
# ============================================================================

@router.get("/config")
async def get_batch_config(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get current batch sequence configuration.

    Returns:
    - prefix: Batch prefix (e.g., 'B')
    - current_number: Current sequence number
    - financial_year: FY short format (e.g., '2526')
    - fy_start_date: FY start date
    - fy_end_date: FY end date
    - next_batch_number: Preview of next batch number
    """
    try:
        config = await batch_tracking_service.get_batch_configuration()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch configuration: {str(e)}"
        )


@router.put("/config", dependencies=[Depends(require_admin)])
async def update_batch_config(
    prefix: Optional[str] = Query(None, description="Batch prefix (e.g., 'B')"),
    starting_number: Optional[int] = Query(None, ge=0, description="Reset sequence to this number"),
    financial_year: Optional[str] = Query(None, min_length=4, max_length=4, description="FY short format (e.g., '2526')"),
    fy_start_date: Optional[str] = Query(None, description="FY start date (YYYY-MM-DD)"),
    fy_end_date: Optional[str] = Query(None, description="FY end date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Update batch sequence configuration (admin only).

    **WARNING:** Use with caution!
    - Changing prefix/FY affects batch number format
    - Resetting starting_number can cause conflicts if not done at FY start
    - Typically used only at financial year start

    **Query Parameters:**
    - prefix: New batch prefix
    - starting_number: Reset sequence (usually to 0 at FY start)
    - financial_year: Override FY short format
    - fy_start_date: Override FY start date
    - fy_end_date: Override FY end date

    **Permissions:**
    Admin only
    """
    try:
        config = await batch_tracking_service.update_batch_configuration(
            prefix=prefix,
            starting_number=starting_number,
            financial_year=financial_year,
            fy_start_date=fy_start_date,
            fy_end_date=fy_end_date
        )
        return config
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update batch configuration: {str(e)}"
        )
