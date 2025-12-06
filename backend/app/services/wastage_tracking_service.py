"""
================================================================================
Marketplace ERP - Wastage Tracking Service
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  Business logic for wastage tracking module. Handles wastage event logging,
  photo uploads to Supabase Storage, repacking workflow, analytics calculations,
  and threshold alert evaluation.

Key Functions:
  - log_wastage_event: Create wastage event with photos
  - upload_wastage_photos: Upload to Supabase Storage
  - get_wastage_by_batch: All wastage for batch
  - get_wastage_analytics_*: Farm/stage/product analytics
  - initiate_repacking: Create repacked batch
  - check_threshold_alerts: Evaluate wastage vs thresholds

================================================================================
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from fastapi import UploadFile, HTTPException, status

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
from app.schemas.wastage_tracking import (
    LogWastageRequest, RepackRequest, PhotoUploadData,
    WastageEventResponse, WastageByBatchResponse, WastageEventDetail,
    WastagePhotoResponse, CostBreakdown, UpdateThresholdRequest,
    WastageAnalyticsByFarmResponse, WastageAnalyticsByStageResponse,
    WastageAnalyticsByProductResponse, WastageTrendsResponse,
    WastageCategoryResponse, WastageThresholdResponse, WastageAlertResponse,
    RepackBatchResponse, CategoriesListResponse, ThresholdsListResponse,
    AlertsListResponse, WastageFarmAnalytics, WastageStageAnalytics,
    WastageProductAnalytics, WastageTrendDataPoint
)
from app.utils.supabase_client import get_supabase_client_async

logger = logging.getLogger(__name__)

# Supabase Storage configuration
WASTAGE_PHOTOS_BUCKET = "wastage-photos"
MAX_PHOTO_SIZE_MB = 5
ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/jpg", "image/png"]


# ============================================================================
# WASTAGE EVENT LOGGING
# ============================================================================

async def log_wastage_event(
    request: LogWastageRequest,
    photos: List[UploadFile],
    created_by: str
) -> WastageEventResponse:
    """
    Log a new wastage event with photo documentation.
    
    Process:
    1. Validate batch exists and is active
    2. Validate minimum 1 photo uploaded
    3. Calculate estimated cost if not provided
    4. Insert wastage event record
    5. Upload photos to Supabase Storage
    6. Link photos to event
    7. Update batch history
    8. Return success response
    
    Args:
        request: Wastage event data
        photos: List of uploaded photo files
        created_by: User UUID who created the event
        
    Returns:
        WastageEventResponse with event details
        
    Raises:
        HTTPException: If validation fails or batch not found
    """
    try:
        # Validate minimum 1 photo
        if not photos or len(photos) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 1 photo is required for wastage documentation"
            )
        
        # Validate batch exists
        batch_query = """
            SELECT id, batch_number, status, po_id, grn_id
            FROM batches
            WHERE batch_number = $1 AND archived_at IS NULL
        """
        batch = await fetch_one(batch_query, request.batch_number)
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {request.batch_number} not found or is archived"
            )
        
        batch_id = batch['id']
        
        # Calculate estimated cost if not provided
        estimated_cost = request.estimated_cost
        if estimated_cost is None:
            estimated_cost = await _calculate_wastage_cost(
                batch_id=batch_id,
                quantity=request.quantity,
                po_id=batch.get('po_id')
            )
        
        # Use transaction for atomic operation
        async with DatabaseTransaction() as conn:
            # Insert wastage event
            insert_event_query = """
                INSERT INTO wastage_events (
                    batch_id, stage, wastage_type, item_name, quantity, unit,
                    cost_allocation, estimated_cost, reason, notes, location,
                    po_id, grn_id, so_id, ticket_id, created_by
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                )
                RETURNING id, event_id, created_at
            """
            
            event_result = await conn.fetchrow(
                insert_event_query,
                batch_id,
                request.stage.value,
                request.wastage_type.value,
                request.item_name,
                request.quantity,
                request.unit,
                request.cost_allocation.value,
                estimated_cost,
                request.reason,
                request.notes,
                request.location,
                request.po_id,
                request.grn_id,
                request.so_id,
                request.ticket_id,
                created_by
            )
            
            wastage_event_id = event_result['id']
            event_id = str(event_result['event_id'])
            created_at = event_result['created_at']
            
            # Upload photos to Supabase Storage
            photo_urls = await upload_wastage_photos(
                event_id=event_id,
                batch_number=request.batch_number,
                photos=photos,
                photo_metadata=request.photo_metadata
            )
            
            # Link photos to wastage event
            for i, photo_url in enumerate(photo_urls):
                metadata = request.photo_metadata[i] if i < len(request.photo_metadata) else PhotoUploadData(file_name=photos[i].filename)
                
                insert_photo_query = """
                    INSERT INTO wastage_photos (
                        wastage_event_id, photo_url, photo_path, file_name,
                        file_size_kb, gps_latitude, gps_longitude, device_info,
                        uploaded_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                
                photo_path = f"{request.batch_number}/{event_id}/{metadata.file_name}"
                
                await conn.execute(
                    insert_photo_query,
                    wastage_event_id,
                    photo_url,
                    photo_path,
                    metadata.file_name,
                    metadata.file_size_kb,
                    metadata.gps_latitude,
                    metadata.gps_longitude,
                    metadata.device_info,
                    created_by
                )
            
            # Note: Batch history will be added outside transaction to avoid nested transaction issues
        
        # Add batch history (outside transaction)
        try:
            # Import here to avoid circular import at module level
            from app.services import batch_tracking_service
            from app.schemas.batch_tracking import AddBatchHistoryRequest, BatchStage, BatchEventType
            
            await batch_tracking_service.add_batch_history(
                batch_number=request.batch_number,
                event=AddBatchHistoryRequest(
                    stage=BatchStage.INVENTORY,
                    event_type=BatchEventType.STATUS_CHANGED,
                    event_details={
                        "wastage_logged": True,
                        "wastage_event_id": wastage_event_id,
                        "stage": request.stage.value,
                        "wastage_type": request.wastage_type.value,
                        "quantity": float(request.quantity),
                        "unit": request.unit
                    },
                    location=request.location
                ),
                created_by=created_by
            )
        except Exception as e:
            logger.warning(f"Failed to add batch history for wastage event: {e}")
        
        return WastageEventResponse(
            wastage_event_id=wastage_event_id,
            event_id=event_id,
            batch_number=request.batch_number,
            stage=request.stage.value,
            wastage_type=request.wastage_type.value,
            quantity=request.quantity,
            unit=request.unit,
            cost_allocation=request.cost_allocation.value,
            estimated_cost=estimated_cost,
            photos_uploaded=len(photo_urls),
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to log wastage event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log wastage event: {str(e)}"
        )


async def upload_wastage_photos(
    event_id: str,
    batch_number: str,
    photos: List[UploadFile],
    photo_metadata: List[PhotoUploadData]
) -> List[str]:
    """
    Upload wastage photos to Supabase Storage.
    
    Path structure: {batch_number}/{event_id}/{filename}
    
    Args:
        event_id: Wastage event UUID
        batch_number: Batch number
        photos: List of uploaded files
        photo_metadata: Metadata for each photo
        
    Returns:
        List of photo URLs
        
    Raises:
        HTTPException: If upload fails or validation fails
    """
    try:
        supabase = await get_supabase_client_async()
        photo_urls = []
        
        for i, photo in enumerate(photos):
            # Validate file type
            if photo.content_type not in ALLOWED_PHOTO_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {photo.content_type}. Allowed: {ALLOWED_PHOTO_TYPES}"
                )
            
            # Read file content
            content = await photo.read()
            
            # Validate file size
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > MAX_PHOTO_SIZE_MB:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size {file_size_mb:.2f}MB exceeds maximum {MAX_PHOTO_SIZE_MB}MB"
                )
            
            # Generate storage path
            filename = photo_metadata[i].file_name if i < len(photo_metadata) else photo.filename
            storage_path = f"{batch_number}/{event_id}/{filename}"
            
            # Upload to Supabase Storage
            try:
                result = supabase.storage.from_(WASTAGE_PHOTOS_BUCKET).upload(
                    path=storage_path,
                    file=content,
                    file_options={"content-type": photo.content_type, "upsert": "true"}
                )
                
                # Get public URL
                photo_url = supabase.storage.from_(WASTAGE_PHOTOS_BUCKET).get_public_url(storage_path)
                photo_urls.append(photo_url)
                
                logger.info(f"Uploaded wastage photo: {storage_path}")
                
            except Exception as e:
                logger.error(f"Failed to upload photo to Supabase: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload photo: {str(e)}"
                )
        
        return photo_urls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload wastage photos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photos: {str(e)}"
        )


async def _calculate_wastage_cost(
    batch_id: int,
    quantity: float,
    po_id: Optional[int] = None
) -> Optional[float]:
    """
    Calculate estimated cost of wastage based on batch/PO pricing.
    
    This is a placeholder implementation. In production, this would:
    1. Get unit price from PO
    2. Calculate: quantity * unit_price
    
    Args:
        batch_id: Batch ID
        quantity: Wasted quantity
        po_id: Purchase Order ID (optional)
        
    Returns:
        Estimated cost in INR, or None if cannot calculate
    """
    # TODO: Implement actual cost calculation when PO module is ready
    # For now, return None (user must provide estimated_cost)
    return None


# ============================================================================
# WASTAGE RETRIEVAL
# ============================================================================

async def get_wastage_by_batch(batch_number: str) -> WastageByBatchResponse:
    """
    Get all wastage events for a specific batch.
    
    Args:
        batch_number: Batch number
        
    Returns:
        WastageByBatchResponse with all events and summary
        
    Raises:
        HTTPException: If batch not found
    """
    try:
        # Validate batch exists
        batch_query = "SELECT id FROM batches WHERE batch_number = $1"
        batch = await fetch_one(batch_query, batch_number)
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_number} not found"
            )
        
        # Get all wastage events for batch
        events_query = """
            SELECT 
                we.event_id, we.stage, we.wastage_type, we.item_name,
                we.quantity, we.unit, we.cost_allocation, we.estimated_cost,
                we.reason, we.notes, we.location, we.created_at,
                up.full_name as created_by
            FROM wastage_events we
            LEFT JOIN user_profiles up ON we.created_by = up.id
            WHERE we.batch_id = $1
            ORDER BY we.created_at DESC
        """
        events = await fetch_all(events_query, batch['id'])
        
        # Get photos for each event
        event_details = []
        total_quantity = 0.0
        total_cost = 0.0
        cost_farm = 0.0
        cost_us = 0.0
        
        for event in events:
            # Get photos
            photos_query = """
                SELECT id, photo_url, file_name, file_size_kb, uploaded_at
                FROM wastage_photos
                WHERE wastage_event_id = (
                    SELECT id FROM wastage_events WHERE event_id = $1
                )
                ORDER BY uploaded_at
            """
            photos_data = await fetch_all(photos_query, event['event_id'])
            photos = [WastagePhotoResponse(**photo) for photo in photos_data]
            
            # Build event detail
            event_detail = WastageEventDetail(
                event_id=str(event['event_id']),
                stage=event['stage'],
                wastage_type=event['wastage_type'],
                item_name=event['item_name'],
                quantity=float(event['quantity']),
                unit=event['unit'],
                cost_allocation=event['cost_allocation'],
                estimated_cost=float(event['estimated_cost']) if event['estimated_cost'] else None,
                reason=event['reason'],
                notes=event['notes'],
                location=event['location'],
                photos=photos,
                created_at=event['created_at'],
                created_by=event['created_by']
            )
            event_details.append(event_detail)
            
            # Accumulate totals
            total_quantity += float(event['quantity'])
            if event['estimated_cost']:
                cost = float(event['estimated_cost'])
                total_cost += cost
                if event['cost_allocation'] == 'farm':
                    cost_farm += cost
                else:
                    cost_us += cost
        
        return WastageByBatchResponse(
            batch_number=batch_number,
            total_wastage_events=len(events),
            total_quantity_wasted=total_quantity,
            total_estimated_cost=total_cost,
            cost_breakdown=CostBreakdown(farm=cost_farm, us=cost_us),
            events=event_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get wastage by batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wastage data: {str(e)}"
        )


# ============================================================================
# ANALYTICS
# ============================================================================

async def get_wastage_analytics_by_farm(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    farm_id: Optional[int] = None
) -> WastageAnalyticsByFarmResponse:
    """
    Get wastage analytics grouped by farm.
    
    Args:
        date_from: Start date (YYYY-MM-DD), defaults to 30 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
        farm_id: Optional farm filter
        
    Returns:
        WastageAnalyticsByFarmResponse with farm analytics
    """
    # Set default date range (last 30 days)
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # TODO: Implement farm analytics when farm/PO tables are ready
    # For now, return empty response
    return WastageAnalyticsByFarmResponse(
        date_range={"from": date_from, "to": date_to},
        farms=[]
    )


async def get_wastage_analytics_by_stage(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> WastageAnalyticsByStageResponse:
    """
    Get wastage analytics grouped by stage.
    
    Args:
        date_from: Start date (YYYY-MM-DD), defaults to 30 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
        
    Returns:
        WastageAnalyticsByStageResponse with stage analytics
    """
    try:
        # Set default date range
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Convert string dates to date objects for asyncpg
        from datetime import date as date_type
        date_from_obj = date_type.fromisoformat(date_from) if isinstance(date_from, str) else date_from
        date_to_obj = date_type.fromisoformat(date_to) if isinstance(date_to, str) else date_to
        
        # Get wastage by stage
        query = """
            SELECT 
                stage,
                COUNT(*) as event_count,
                SUM(quantity) as total_wastage_kg,
                SUM(estimated_cost) as total_cost,
                AVG(quantity) as avg_wastage_per_event
            FROM wastage_events
            WHERE created_at >= $1 AND created_at < ($2 + interval '1 day')
            GROUP BY stage
            ORDER BY total_wastage_kg DESC
        """
        
        results = await fetch_all(query, date_from_obj, date_to_obj)
        
        # Calculate total for percentages
        total_wastage = sum(float(r['total_wastage_kg'] or 0) for r in results)
        
        # Get top reasons for each stage
        stages = []
        for result in results:
            # Get top reasons
            reasons_query = """
                SELECT reason, COUNT(*) as count
                FROM wastage_events
                WHERE stage = $1 
                  AND created_at >= $2 
                  AND created_at < ($3 + interval '1 day')
                  AND reason IS NOT NULL
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 5
            """
            top_reasons_data = await fetch_all(reasons_query, result['stage'], date_from_obj, date_to_obj)
            top_reasons = [{"reason": r['reason'], "count": r['count']} for r in top_reasons_data]
            
            stage_analytics = WastageStageAnalytics(
                stage=result['stage'],
                stage_name=result['stage'].replace('_', ' ').title(),
                total_wastage_kg=float(result['total_wastage_kg'] or 0),
                total_cost=float(result['total_cost'] or 0),
                percentage_of_total=(float(result['total_wastage_kg'] or 0) / total_wastage * 100) if total_wastage > 0 else 0,
                event_count=result['event_count'],
                avg_wastage_per_event=float(result['avg_wastage_per_event'] or 0),
                top_reasons=top_reasons
            )
            stages.append(stage_analytics)
        
        return WastageAnalyticsByStageResponse(
            date_range={"from": date_from, "to": date_to},
            stages=stages
        )
        
    except Exception as e:
        logger.error(f"Failed to get wastage analytics by stage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


async def get_wastage_analytics_by_product(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    item_name: Optional[str] = None
) -> WastageAnalyticsByProductResponse:
    """
    Get wastage analytics grouped by product/item.
    
    Args:
        date_from: Start date (YYYY-MM-DD), defaults to 30 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
        item_name: Optional item filter
        
    Returns:
        WastageAnalyticsByProductResponse with product analytics
    """
    try:
        # Set default date range
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Convert string dates to date objects for asyncpg
        from datetime import date as date_type
        date_from_obj = date_type.fromisoformat(date_from) if isinstance(date_from, str) else date_from
        date_to_obj = date_type.fromisoformat(date_to) if isinstance(date_to, str) else date_to
        
        # Build query with optional item filter
        query = """
            SELECT 
                item_name,
                SUM(quantity) as total_wastage_kg,
                SUM(estimated_cost) as total_cost
            FROM wastage_events
            WHERE created_at >= $1 AND created_at < ($2 + interval '1 day')
        """
        params = [date_from_obj, date_to_obj]
        
        if item_name:
            query += " AND item_name ILIKE $3"
            params.append(f"%{item_name}%")
        
        query += " GROUP BY item_name ORDER BY total_wastage_kg DESC"
        
        results = await fetch_all(query, *params)
        
        # Get problematic stages for each product
        products = []
        for result in results:
            stages_query = """
                SELECT stage, SUM(quantity) as wastage_kg
                FROM wastage_events
                WHERE item_name = $1 
                  AND created_at >= $2 
                  AND created_at < ($3 + interval '1 day')
                GROUP BY stage
                ORDER BY wastage_kg DESC
                LIMIT 3
            """
            stages_data = await fetch_all(stages_query, result['item_name'], date_from_obj, date_to_obj)
            problematic_stages = [{"stage": s['stage'], "wastage_kg": float(s['wastage_kg'])} for s in stages_data]
            
            product_analytics = WastageProductAnalytics(
                item_name=result['item_name'],
                total_wastage_kg=float(result['total_wastage_kg'] or 0),
                total_cost=float(result['total_cost'] or 0),
                wastage_percentage=0.0,  # TODO: Calculate when we have total received data
                problematic_stages=problematic_stages
            )
            products.append(product_analytics)
        
        return WastageAnalyticsByProductResponse(
            date_range={"from": date_from, "to": date_to},
            products=products
        )
        
    except Exception as e:
        logger.error(f"Failed to get wastage analytics by product: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


async def get_wastage_trends(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    granularity: str = "daily"
) -> WastageTrendsResponse:
    """
    Get wastage trends over time.
    
    Args:
        date_from: Start date (YYYY-MM-DD), defaults to 30 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
        granularity: 'daily', 'weekly', or 'monthly'
        
    Returns:
        WastageTrendsResponse with time series data
    """
    try:
        # Set default date range
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Convert string dates to date objects for asyncpg
        from datetime import date as date_type
        date_from_obj = date_type.fromisoformat(date_from) if isinstance(date_from, str) else date_from
        date_to_obj = date_type.fromisoformat(date_to) if isinstance(date_to, str) else date_to
        
        # Determine date truncation based on granularity
        if granularity == "weekly":
            date_trunc = "week"
        elif granularity == "monthly":
            date_trunc = "month"
        else:
            date_trunc = "day"
        
        query = f"""
            SELECT 
                DATE_TRUNC('{date_trunc}', created_at)::date as date,
                SUM(quantity) as total_wastage_kg,
                SUM(estimated_cost) as total_cost,
                COUNT(*) as event_count
            FROM wastage_events
            WHERE created_at >= $1 AND created_at < ($2 + interval '1 day')
            GROUP BY DATE_TRUNC('{date_trunc}', created_at)
            ORDER BY date
        """
        
        results = await fetch_all(query, date_from_obj, date_to_obj)
        
        data_points = [
            WastageTrendDataPoint(
                date=r['date'].strftime("%Y-%m-%d"),
                total_wastage_kg=float(r['total_wastage_kg'] or 0),
                total_cost=float(r['total_cost'] or 0),
                event_count=r['event_count']
            )
            for r in results
        ]
        
        return WastageTrendsResponse(
            granularity=granularity,
            data_points=data_points
        )
        
    except Exception as e:
        logger.error(f"Failed to get wastage trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trends: {str(e)}"
        )


# ============================================================================
# REPACKING WORKFLOW
# ============================================================================

async def initiate_repacking(
    request: RepackRequest,
    photos: List[UploadFile],
    created_by: str
) -> RepackBatchResponse:
    """
    Initiate repacking workflow for damaged items.
    
    Process:
    1. Validate parent batch exists
    2. Check parent batch not already repacked
    3. Validate quantities
    4. Create new batch via Batch Tracking API (with R suffix)
    5. Create repacking record
    6. Upload photos
    7. Return response
    
    Args:
        request: Repacking request data
        photos: List of uploaded photo files
        created_by: User UUID
        
    Returns:
        RepackBatchResponse with new batch details
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Import batch tracking service
        from app.services import batch_tracking_service
        from app.schemas.batch_tracking import RepackBatchRequest as BatchRepackRequest
        
        # Validate repacked quantity <= damaged quantity
        if request.repacked_quantity > request.damaged_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repacked quantity cannot exceed damaged quantity"
            )
        
        # Calculate wastage in repacking if not provided
        if request.wastage_in_repacking == 0:
            request.wastage_in_repacking = request.damaged_quantity - request.repacked_quantity
        
        # Upload photos first
        event_id = str(uuid.uuid4())
        photo_urls = await upload_wastage_photos(
            event_id=event_id,
            batch_number=request.parent_batch_number,
            photos=photos,
            photo_metadata=request.photo_metadata
        )
        
        # Create repacked batch via Batch Tracking API
        batch_repack_request = BatchRepackRequest(
            reason=request.reason,
            damaged_quantity=request.damaged_quantity,
            repacked_quantity=request.repacked_quantity,
            photos=photo_urls,
            notes=request.notes
        )
        
        repack_result = await batch_tracking_service.create_repacked_batch(
            parent_batch_number=request.parent_batch_number,
            repack_data=batch_repack_request,
            created_by=created_by
        )
        
        # Get parent and child batch IDs
        parent_batch_query = "SELECT id FROM batches WHERE batch_number = $1"
        parent_batch = await fetch_one(parent_batch_query, request.parent_batch_number)
        
        child_batch_query = "SELECT id FROM batches WHERE batch_number = $1"
        child_batch = await fetch_one(child_batch_query, repack_result.new_batch_number)
        
        # Create repacking record
        insert_repack_query = """
            INSERT INTO wastage_repacking (
                parent_batch_id, child_batch_id, wastage_event_id,
                damaged_quantity, repacked_quantity, wastage_in_repacking,
                reason, notes, repacked_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        
        repacking_id = await execute_query(
            insert_repack_query,
            parent_batch['id'],
            child_batch['id'],
            request.wastage_event_id,
            request.damaged_quantity,
            request.repacked_quantity,
            request.wastage_in_repacking,
            request.reason,
            request.notes,
            created_by
        )
        
        return RepackBatchResponse(
            parent_batch=request.parent_batch_number,
            new_batch_number=repack_result.new_batch_number,
            new_batch_id=repack_result.new_batch_id,
            repacking_id=repacking_id,
            repacked_quantity=request.repacked_quantity,
            created_at=repack_result.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate repacking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate repacking: {str(e)}"
        )


# ============================================================================
# CATEGORIES & THRESHOLDS
# ============================================================================

async def get_wastage_categories(stage: Optional[str] = None) -> CategoriesListResponse:
    """
    Get wastage categories for dropdowns.
    
    Args:
        stage: Optional stage filter
        
    Returns:
        CategoriesListResponse with categories
    """
    try:
        query = """
            SELECT id, stage, wastage_type, reason, description
            FROM wastage_categories
            WHERE is_active = true
        """
        params = []
        
        if stage:
            query += " AND stage = $1"
            params.append(stage)
        
        query += " ORDER BY display_order, reason"
        
        results = await fetch_all(query, *params)
        categories = [WastageCategoryResponse(**r) for r in results]
        
        return CategoriesListResponse(categories=categories)
        
    except Exception as e:
        logger.error(f"Failed to get wastage categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


async def get_wastage_thresholds() -> ThresholdsListResponse:
    """
    Get all wastage thresholds.
    
    Returns:
        ThresholdsListResponse with thresholds
    """
    try:
        query = """
            SELECT id, scope_type, scope_value, stage, threshold_percentage,
                   alert_level, is_active, created_at, updated_at
            FROM wastage_thresholds
            ORDER BY scope_type, stage, threshold_percentage
        """
        
        results = await fetch_all(query)
        thresholds = [WastageThresholdResponse(**r) for r in results]
        
        return ThresholdsListResponse(thresholds=thresholds)
        
    except Exception as e:
        logger.error(f"Failed to get wastage thresholds: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get thresholds: {str(e)}"
        )


async def update_wastage_threshold(
    threshold_id: int,
    request: UpdateThresholdRequest
) -> WastageThresholdResponse:
    """
    Update wastage threshold (admin only).
    
    Args:
        threshold_id: Threshold ID
        request: Update data
        
    Returns:
        Updated WastageThresholdResponse
        
    Raises:
        HTTPException: If threshold not found
    """
    try:
        query = """
            UPDATE wastage_thresholds
            SET threshold_percentage = $1,
                alert_level = $2,
                is_active = $3,
                updated_at = NOW()
            WHERE id = $4
            RETURNING id, scope_type, scope_value, stage, threshold_percentage,
                      alert_level, is_active, created_at, updated_at
        """
        
        result = await fetch_one(
            query,
            request.threshold_percentage,
            request.alert_level.value,
            request.is_active,
            threshold_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Threshold {threshold_id} not found"
            )
        
        return WastageThresholdResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update wastage threshold: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update threshold: {str(e)}"
        )


# ============================================================================
# THRESHOLD ALERTS
# ============================================================================

async def check_threshold_alerts() -> AlertsListResponse:
    """
    Check current wastage against thresholds and generate alerts.
    
    This function is called by the scheduler hourly.
    Evaluates wastage percentages and compares against configured thresholds.
    
    Returns:
        AlertsListResponse with current alerts
    """
    try:
        alerts = []
        
        # Get active thresholds
        thresholds_query = """
            SELECT id, scope_type, scope_value, stage, threshold_percentage, alert_level
            FROM wastage_thresholds
            WHERE is_active = true
        """
        thresholds = await fetch_all(thresholds_query)
        
        # Check each threshold
        for threshold in thresholds:
            # Calculate wastage percentage for last 7 days
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
            
            # TODO: Implement actual threshold checking when we have total received data
            # For now, just log that we're checking
            logger.info(f"Checking threshold {threshold['id']}: {threshold['scope_type']} - {threshold['stage']}")
        
        return AlertsListResponse(alerts=alerts)
        
    except Exception as e:
        logger.error(f"Failed to check threshold alerts: {e}", exc_info=True)
        return AlertsListResponse(alerts=[])


async def get_current_alerts() -> AlertsListResponse:
    """
    Get current wastage alerts.
    
    Returns:
        AlertsListResponse with active alerts
    """
    # For now, return empty alerts
    # TODO: Implement alert storage and retrieval
    return AlertsListResponse(alerts=[])
