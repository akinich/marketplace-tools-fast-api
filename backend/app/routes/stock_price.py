from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from io import BytesIO

from app.services.stock_price_service import StockPriceService
from app.schemas.stock_price import (
    ProductListResponse,
    UpdatePreviewRequest,
    UpdatePreviewResponse,
    ApplyUpdatesRequest,
    UpdateResultResponse,
    ProductSettingUpdate,
    ChangeHistoryResponse,
    StatisticsResponse,
    SyncResponse
)
from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser

router = APIRouter(
    prefix="/stock-price",
    tags=["Stock & Price Updater"],
    responses={404: {"description": "Not found"}},
)

# ============================================================================
# Product List Management
# ============================================================================

@router.get("/products", response_model=ProductListResponse)
async def get_products(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all products categorized into updatable/non-updatable/deleted lists"""
    products = await StockPriceService.get_categorized_products()
    return products

# ============================================================================
# Update Preview and Apply
# ============================================================================

@router.post("/preview", response_model=UpdatePreviewResponse)
async def preview_changes(
    request: UpdatePreviewRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Preview and validate changes before applying"""
    changes = [change.dict() for change in request.changes]
    valid_changes, validation_errors = await StockPriceService.preview_changes(changes)
    
    return {
        "valid_changes": valid_changes,
        "validation_errors": validation_errors,
        "total_changes": len(valid_changes)
    }

@router.post("/update", response_model=UpdateResultResponse)
async def apply_updates(
    request: ApplyUpdatesRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Apply validated updates to database and WooCommerce"""
    changes = [change.dict() for change in request.changes]
    result = await StockPriceService.apply_updates(changes, current_user.id)
    return result

# ============================================================================
# Sync from WooCommerce
# ============================================================================

@router.post("/sync", response_model=SyncResponse)
async def sync_from_woocommerce(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Sync products from WooCommerce (batch fetch and parallel updates)"""
    result = await StockPriceService.sync_from_woocommerce(current_user.id)
    return result

# ============================================================================
# Excel Template and Upload
# ============================================================================

@router.get("/excel-template")
async def download_excel_template(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Download Excel template with current updatable products"""
    excel_bytes = await StockPriceService.generate_excel_template()
    
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=stock_price_template.xlsx"}
    )

@router.post("/excel-upload", response_model=UpdateResultResponse)
async def upload_excel(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Upload Excel file with bulk changes"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    content = await file.read()
    result = await StockPriceService.process_excel_upload(content, current_user.id)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Upload failed'))
    
    return result

# ============================================================================
# Product Settings Management
# ============================================================================

@router.put("/settings")
async def update_product_setting(
    setting: ProductSettingUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update product setting (lock/unlock) - Admin only"""
    # Check if user is admin
    if current_user.role.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = await StockPriceService.update_product_setting(
        setting.product_id,
        setting.variation_id,
        setting.is_updatable,
        current_user.id,
        setting.notes
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update setting")
    
    return {"message": "Setting updated successfully"}

@router.post("/restore/{product_id}")
async def restore_deleted_product(
    product_id: int,
    variation_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Restore a deleted product - Admin only"""
    # Check if user is admin
    if current_user.role.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = await StockPriceService.restore_deleted_product(
        product_id,
        variation_id,
        current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restore product")
    
    return {"message": "Product restored successfully"}

# ============================================================================
# Change History and Statistics
# ============================================================================

@router.get("/history", response_model=ChangeHistoryResponse)
async def get_change_history(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    product_id: Optional[int] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get change history with pagination"""
    items, total = await StockPriceService.get_change_history(limit, offset, product_id)
    
    return {
        "items": items,
        "total": total
    }

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get statistics for dashboard - Admin only"""
    # Check if user is admin
    if current_user.role.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = await StockPriceService.get_statistics()
    return stats
