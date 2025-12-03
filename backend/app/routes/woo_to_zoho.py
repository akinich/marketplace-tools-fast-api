from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date
import io

from app.services.woo_to_zoho_service import WooToZohoService
from app.schemas.woo_to_zoho import (
    ExportRequestBase, 
    ExportPreviewResponse, 
    ExportHistoryItem,
    LastSequenceResponse
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/woo-to-zoho",
    tags=["Woo to Zoho Export"],
    responses={404: {"description": "Not found"}},
)

@router.get("/last-sequence", response_model=LastSequenceResponse)
async def get_last_sequence(
    prefix: str = Query(..., description="Invoice prefix to check")
):
    """Get the last used sequence number for a prefix."""
    last_seq = await WooToZohoService.get_last_sequence(prefix)
    suggested = (last_seq + 1) if last_seq is not None else 1
    return {"last_sequence": last_seq, "suggested_sequence": suggested}

@router.post("/preview", response_model=ExportPreviewResponse)
async def preview_export(
    request: ExportRequestBase,
    current_user = Depends(get_current_user)
):
    """Preview the export data before generating files."""
    # 1. Fetch orders
    orders = await WooToZohoService.fetch_orders(request.start_date, request.end_date)
    
    if not orders:
        return {
            "csv_rows": [],
            "replacements_log": [],
            "summary": None,
            "total_orders": 0
        }

    # 2. Get mapping
    mapping = await WooToZohoService.get_product_mapping()

    # 3. Transform
    csv_rows, replacements_log, completed_orders = await WooToZohoService.transform_orders(
        orders, mapping, request.invoice_prefix, request.start_sequence
    )

    # 4. Generate summary (simple version for preview)
    summary = {
        "total_orders": len(completed_orders),
        "date_range": f"{request.start_date} to {request.end_date}",
        "invoice_range": f"{request.invoice_prefix}{request.start_sequence:05d}..."
    }

    return {
        "csv_rows": csv_rows[:50], # Limit preview to 50 rows
        "replacements_log": replacements_log,
        "summary": summary,
        "total_orders": len(completed_orders)
    }

@router.post("/export")
async def generate_export(
    request: ExportRequestBase,
    current_user = Depends(get_current_user)
):
    """Generate and download the export ZIP file."""
    # 1. Fetch orders
    orders = await WooToZohoService.fetch_orders(request.start_date, request.end_date)
    
    if not orders:
        raise HTTPException(status_code=404, detail="No completed orders found in this date range")

    # 2. Get mapping
    mapping = await WooToZohoService.get_product_mapping()

    # 3. Transform
    csv_rows, replacements_log, completed_orders = await WooToZohoService.transform_orders(
        orders, mapping, request.invoice_prefix, request.start_sequence
    )
    
    if not completed_orders:
        raise HTTPException(status_code=404, detail="No completed orders found")

    # 4. Generate Files
    zip_bytes = WooToZohoService.generate_files(
        csv_rows, completed_orders, request.invoice_prefix, request.start_sequence,
        request.start_date, request.end_date
    )

    # 5. Save History
    await WooToZohoService.save_history(
        completed_orders, request.invoice_prefix, request.start_sequence,
        request.start_date, request.end_date, current_user.id
    )

    # 6. Return File
    filename = f"orders_export_{request.start_date}_{request.end_date}.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/history", response_model=List[ExportHistoryItem])
async def get_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user = Depends(get_current_user)
):
    """Get export history."""
    return await WooToZohoService.get_history(start_date, end_date)
