
"""
================================================================================
Marketplace ERP - GRN Management Service
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date, time
from decimal import Decimal
import asyncpg
import uuid
from io import BytesIO

from fastapi import UploadFile

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction, get_db_connection
from app.schemas.grn import (
    GRNUpdateRequest, GRNResponse, GRNDetailResponse, GRNItemResponse, GRNPhotoResponse
)
from app.schemas.batch_tracking import BatchStage, BatchEventType, AddBatchHistoryRequest, BatchStatus
from app.services import po_service, batch_tracking_service, wastage_tracking_service
from app.utils.supabase_client import supabase

# Try importing ReportLab, fallback if not available
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# GRN NUMBER GENERATION
# ============================================================================

async def generate_grn_number(conn: asyncpg.Connection) -> str:
    """
    Generate sequential GRN number: GRN-001, GRN-002, etc.
    Thread-safe using database sequence
    """
    result = await conn.fetchval("SELECT nextval('grn_number_seq')")
    return f"GRN-{result:03d}"

# ============================================================================
# GRN GENERATION FROM PO
# ============================================================================

async def generate_grn_from_po(
    po_id: int,
    user_id: str
) -> Dict[str, Any]:
    """
    Create new GRN from PO
    """
    try:
        async with DatabaseTransaction() as conn:
            # Validate PO
            po = await conn.fetchrow("""
                SELECT * FROM purchase_orders WHERE id = $1
            """, po_id)
            
            if not po:
                raise ValueError(f"PO {po_id} not found")

            if po['status'] != 'sent_to_farm':
                raise ValueError(f"PO must be in 'sent_to_farm' status. Current: {po['status']}")
            
            existing_grn = await conn.fetchval("SELECT id FROM grns WHERE po_id = $1", po_id)
            if existing_grn:
                raise ValueError(f"GRN already exists for PO {po_id}")

            # Generate numbers
            # Generate numbers
            grn_number = await generate_grn_number(conn)

            # Generate batch (this creates the batch record and returns dict)
            batch_result = await batch_tracking_service.generate_batch_number(po_id=po_id, created_by=str(user_id))
            batch_id = batch_result['batch_id']
            batch_number = batch_result['batch_number']
            
            # Create GRN
            grn = await conn.fetchrow("""
                INSERT INTO grns (grn_number, po_id, batch_id, created_by, status)
                VALUES ($1, $2, $3, $4, 'draft')
                RETURNING *
            """, grn_number, po_id, batch_id, user_id)
            
            # Pre-populate items from PO
            po_items = await conn.fetch("""
                SELECT * FROM purchase_order_items WHERE po_id = $1
            """, po_id)
            
            for item in po_items:
                await conn.execute("""
                    INSERT INTO grn_items (grn_id, item_id, gross_received, damage, reject, final_accepted)
                    VALUES ($1, $2, 0, 0, 0, 0)
                """, grn['id'], item['item_id'])
            
            # Update PO status
            await po_service._log_status_change(conn, po_id, 'sent_to_farm', 'grn_generated', str(user_id))
            await conn.execute("""
                UPDATE purchase_orders SET status = 'grn_generated' WHERE id = $1
            """, po_id)
            
            logger.info(f"✅ Generated GRN {grn_number} for PO {po_id}")
            
            return await get_grn_details(conn, grn['id'])

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in GRN generation: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate GRN: {e}")
        raise

# ============================================================================
# GRN DETAILS
# ============================================================================

async def get_grn_details(conn_or_id: Any, grn_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get complete GRN details.
    Supports passing connection explicitly or just ID (wraps in transaction).
    """
    if isinstance(conn_or_id, int):
        # Case: get_grn_details(grn_id)
        grn_id = conn_or_id
        async with DatabaseTransaction() as conn:
            return await _get_grn_details_internal(conn, grn_id)
    else:
        # Case: get_grn_details(conn, grn_id)
        return await _get_grn_details_internal(conn_or_id, grn_id)

async def _get_grn_details_internal(conn: asyncpg.Connection, grn_id: int) -> Optional[Dict[str, Any]]:
    grn = await conn.fetchrow("""
        SELECT 
            g.*, 
            po.po_number, po.vendor_id, 
            b.batch_number,
            v.contact_name as vendor_name,
            u.email as receiver_name
        FROM grns g
        JOIN purchase_orders po ON g.po_id = po.id
        JOIN batches b ON g.batch_id = b.id
        JOIN zoho_vendors v ON po.vendor_id = v.id
        LEFT JOIN auth.users u ON g.receiver_id = u.id
        WHERE g.id = $1
    """, grn_id)
    
    if not grn:
        return None
    
    # Items
    items = await conn.fetch("""
        SELECT 
            gi.*, 
            i.name as item_name
        FROM grn_items gi
        JOIN grns g ON gi.grn_id = g.id  -- Join GRN to get po_id if needed, but not needed for item_name
        JOIN purchase_orders po ON g.po_id = po.id 
        JOIN purchase_order_items poi ON poi.po_id = po.id AND poi.item_id = gi.item_id -- Map to PO Item to get SKU/Name
        JOIN zoho_items i ON gi.item_id = i.id
        WHERE gi.grn_id = $1
    """, grn_id)
    
    # Photos
    photos = await conn.fetch("""
        SELECT 
            gp.*,
            i.name as item_name,
            u.email as uploaded_by_name
        FROM grn_photos gp
        LEFT JOIN zoho_items i ON gp.item_id = i.id
        JOIN auth.users u ON gp.uploaded_by = u.id
        WHERE gp.grn_id = $1
        ORDER BY gp.uploaded_at DESC
    """, grn_id)
    
    # History
    history = await conn.fetch("""
        SELECT 
            gh.*,
            u.email as edited_by_name
        FROM grn_edit_history gh
        JOIN auth.users u ON gh.edited_by = u.id
        WHERE gh.grn_id = $1
        ORDER BY gh.edited_at DESC
    """, grn_id)
    
    return {
        **grn,
        'items': items,
        'photos': photos,
        'edit_history': history
    }

async def get_grn_by_id(grn_id: int) -> Optional[Dict[str, Any]]:
    """Helper wrapper"""
    return await get_grn_details(grn_id)

# ============================================================================
# GRN LISTING
# ============================================================================

async def list_grns(
    status: Optional[str] = None,
    po_id: Optional[int] = None,
    batch_number: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """List GRNs with filters"""
    try:
        offset = (page - 1) * limit
        params = []
        where_clauses = ["1=1"]
        param_idx = 1
        
        if status:
            where_clauses.append(f"g.status = ${param_idx}")
            params.append(status)
            param_idx += 1
            
        if po_id:
            where_clauses.append(f"g.po_id = ${param_idx}")
            params.append(po_id)
            param_idx += 1
            
        if batch_number:
            # Need to join batches to filter by batch number if passed, or if batch_id matches (but typically pass number)
            # Query below joins batches so we can filter by number
            where_clauses.append(f"b.batch_number = ${param_idx}")
            params.append(batch_number)
            param_idx += 1
            
        if from_date:
            where_clauses.append(f"g.receiving_date >= ${param_idx}")
            params.append(from_date)
            param_idx += 1
            
        if to_date:
            where_clauses.append(f"g.receiving_date <= ${param_idx}")
            params.append(to_date)
            param_idx += 1

        where_stmt = " AND ".join(where_clauses)
        
        base_query = f"""
            SELECT 
                g.*, 
                po.po_number, po.vendor_id, 
                b.batch_number,
                v.contact_name as vendor_name,
                u.email as receiver_name
            FROM grns g
            JOIN purchase_orders po ON g.po_id = po.id
            JOIN batches b ON g.batch_id = b.id
            JOIN zoho_vendors v ON po.vendor_id = v.id
            LEFT JOIN auth.users u ON g.receiver_id = u.id
            WHERE {where_stmt}
        """
        
        count_query = f"SELECT COUNT(*) FROM grns g JOIN batches b ON g.batch_id = b.id WHERE {where_stmt}"
        
        async with get_db_connection() as conn:
            total = await conn.fetchval(count_query, *params)
            
            # Pagination
            query = f"{base_query} ORDER BY g.created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.append(limit)
            params.append(offset)
            
            grns = await conn.fetch(query, *params)
            
            return {
                "grns": grns,
                "total": total,
                "page": page,
                "limit": limit
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to list GRNs: {e}")
        raise

# ============================================================================
# GRN UPDATE
# ============================================================================

async def log_edit(conn, grn_id, field_name, old_val, new_val, user_id):
    await conn.execute("""
        INSERT INTO grn_edit_history (grn_id, field_name, old_value, new_value, edited_by)
        VALUES ($1, $2, $3, $4, $5)
    """, grn_id, field_name, str(old_val), str(new_val), user_id)

async def update_grn(
    grn_id: int,
    request: GRNUpdateRequest,
    user_id: str
) -> Dict[str, Any]:
    """Update GRN details"""
    try:
        async with DatabaseTransaction() as conn:
            # Check if locked
            grn = await conn.fetchrow("SELECT * FROM grns WHERE id = $1", grn_id)
            if not grn:
                raise ValueError(f"GRN {grn_id} not found")
            
            if grn['status'] == 'locked':
                raise ValueError("GRN is locked and cannot be edited")
            
            # Check if PO exported
            po = await conn.fetchrow("SELECT status FROM purchase_orders WHERE id = $1", grn['po_id'])
            if po['status'] == 'exported_to_zoho':
                raise ValueError("Cannot edit GRN after PO exported to Zoho")
            
            # Update fields
            if request.transport_method and request.transport_method != grn['transport_method']:
                await log_edit(conn, grn_id, 'transport_method', grn['transport_method'], request.transport_method, user_id)
                await conn.execute("UPDATE grns SET transport_method = $1 WHERE id = $2", request.transport_method, grn_id)
            
            if request.number_of_boxes is not None and request.number_of_boxes != grn['number_of_boxes']:
                await log_edit(conn, grn_id, 'number_of_boxes', grn['number_of_boxes'], request.number_of_boxes, user_id)
                await conn.execute("UPDATE grns SET number_of_boxes = $1 WHERE id = $2", request.number_of_boxes, grn_id)

            if request.receiving_time and request.receiving_time != grn['receiving_time']:
                await log_edit(conn, grn_id, 'receiving_time', grn['receiving_time'], request.receiving_time, user_id)
                await conn.execute("UPDATE grns SET receiving_time = $1 WHERE id = $2", request.receiving_time, grn_id)

            if request.receiving_date and request.receiving_date != grn['receiving_date']:
                await log_edit(conn, grn_id, 'receiving_date', grn['receiving_date'], request.receiving_date, user_id)
                await conn.execute("UPDATE grns SET receiving_date = $1 WHERE id = $2", request.receiving_date, grn_id)

            if request.receiver_id and request.receiver_id != grn['receiver_id']:
                await log_edit(conn, grn_id, 'receiver_id', grn['receiver_id'], request.receiver_id, user_id)
                await conn.execute("UPDATE grns SET receiver_id = $1 WHERE id = $2", request.receiver_id, grn_id)
            
            if request.notes and request.notes != grn['notes']:
                 await log_edit(conn, grn_id, 'notes', grn['notes'], request.notes, user_id)
                 await conn.execute("UPDATE grns SET notes = $1 WHERE id = $2", request.notes, grn_id)


            # Update items
            if request.items:
                for item_req in request.items:
                    old_item = await conn.fetchrow("""
                        SELECT * FROM grn_items WHERE grn_id = $1 AND item_id = $2
                    """, grn_id, item_req.item_id)
                    
                    if not old_item:
                         # Potentially adding a new item not in PO? 
                         continue 

                    final_accepted = item_req.gross_received - item_req.damage - item_req.reject
                    if final_accepted < 0:
                        raise ValueError(f"Invalid quantities for item ID {item_req.item_id}")
                    
                    # Log important changes
                    if old_item['gross_received'] != item_req.gross_received:
                        await log_edit(conn, grn_id, f'item_{item_req.item_id}_gross', old_item['gross_received'], item_req.gross_received, user_id)
                    
                    await conn.execute("""
                        UPDATE grn_items
                        SET gross_received = $1, damage = $2, reject = $3, final_accepted = $4,
                            damage_cost_allocation = $5, reject_cost_allocation = $6, notes = $7
                        WHERE grn_id = $8 AND item_id = $9
                    """, item_req.gross_received, item_req.damage, item_req.reject, final_accepted,
                        item_req.damage_cost_allocation, item_req.reject_cost_allocation, item_req.notes,
                        grn_id, item_req.item_id)
            
            await conn.execute("UPDATE grns SET updated_at = NOW() WHERE id = $1", grn_id)

            return await _get_grn_details_internal(conn, grn_id)

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update GRN: {e}")
        raise

# ============================================================================
# FINALIZE GRN
# ============================================================================

async def finalize_grn(grn_id: int, user_id: str) -> Dict[str, Any]:
    """
    Finalize GRN and trigger downstream processes
    """
    try:
        async with DatabaseTransaction() as conn:
            grn = await conn.fetchrow("SELECT * FROM grns WHERE id = $1", grn_id)
            if not grn:
                raise ValueError(f"GRN {grn_id} not found")
            
            if grn['status'] != 'draft':
                 raise ValueError("Only draft GRNs can be finalized")

            if not grn['receiver_id']:
                raise ValueError("Receiver must be assigned before finalization")
            
            items = await conn.fetch("SELECT * FROM grn_items WHERE grn_id = $1", grn_id)
            
            # Validations
            for item in items:
                if item['damage'] > 0:
                    count = await conn.fetchval("""
                        SELECT COUNT(*) FROM grn_photos 
                        WHERE grn_id = $1 AND item_id = $2 AND photo_type = 'damage'
                    """, grn_id, item['item_id'])
                    if count == 0:
                        raise ValueError(f"Photos required for damage on item ID {item['item_id']}")
                
                if item['reject'] > 0:
                     count = await conn.fetchval("""
                        SELECT COUNT(*) FROM grn_photos 
                        WHERE grn_id = $1 AND item_id = $2 AND photo_type = 'reject'
                    """, grn_id, item['item_id'])
                     if count == 0:
                        raise ValueError(f"Photos required for reject on item ID {item['item_id']}")

            # Update PO items and add extra items
            po_id = grn['po_id']
            
            extra_items_list = []
            
            for item in items:
                po_item = await conn.fetchrow("""
                    SELECT * FROM purchase_order_items WHERE po_id = $1 AND item_id = $2
                """, po_id, item['item_id'])
                
                if po_item:
                    await conn.execute("""
                        UPDATE purchase_order_items SET quantity = $1 WHERE po_id = $2 AND item_id = $3
                    """, item['final_accepted'], po_id, item['item_id'])
                else:
                    # Extra item
                    extra_items_list.append({
                        'item_id': item['item_id'],
                        'quantity': float(item['final_accepted']), 
                        'unit_price': 0,
                        'notes': f"Extra item from GRN {grn['grn_number']}"
                    })
                    await conn.execute("""
                        UPDATE grn_items SET added_to_po = true WHERE grn_id = $1 AND item_id = $2
                    """, grn_id, item['item_id'])
            
            if extra_items_list:
                for extra in extra_items_list:
                     await conn.execute("""
                        INSERT INTO purchase_order_items (po_id, item_id, quantity, unit_price, total_price, notes)
                        VALUES ($1, $2, $3, 0, 0, $4)
                     """, po_id, extra['item_id'], extra['quantity'], extra['notes'])
            
            # Log Wastage
            batch = await conn.fetchrow("SELECT * FROM batches WHERE id = $1", grn['batch_id'])
            
            for item in items:
                if item['damage'] > 0:
                    photos = await conn.fetch("""
                        SELECT photo_url, photo_path, file_size FROM grn_photos WHERE grn_id = $1 AND item_id = $2 AND photo_type = 'damage'
                    """, grn_id, item['item_id'])
                    
                    # Log wastage directly (service expects UploadFile)
                    wastage_event = await conn.fetchrow("""
                        INSERT INTO wastage_events (
                            batch_id, stage, wastage_type, item_name, quantity, unit,
                            cost_allocation, reason, notes,
                            po_id, grn_id, created_by
                        ) VALUES (
                            $1, $2, 'damage', $3, $4, 'units',
                            $5, 'Damaged during receiving', $6,
                            $7, $8, $9
                        )
                        RETURNING id, event_id
                    """, grn['batch_id'], 'receiving', item['item_name'], 
                         float(item['damage']), item['damage_cost_allocation'],
                         item.get('notes'), po_id, grn_id, user_id)

                    # Link photos
                    for p in photos:
                         # We copy GRN photo to wastage photo table
                         # Note: Optimally we might move file or just ref the URL. 
                         # Wastage module expects files in its own bucket structure usually, 
                         # but here we just link the URL.
                         await conn.execute("""
                            INSERT INTO wastage_photos (
                                wastage_event_id, photo_url, photo_path, file_name,
                                file_size_kb, uploaded_by
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                         """, wastage_event['id'], p['photo_url'], p['photo_path'], 
                             p['photo_path'].split('/')[-1], p['file_size'] or 0, user_id)
                
                if item['reject'] > 0:
                    photos = await conn.fetch("""
                        SELECT photo_url, photo_path, file_size FROM grn_photos WHERE grn_id = $1 AND item_id = $2 AND photo_type = 'reject'
                    """, grn_id, item['item_id'])
                     
                    wastage_event = await conn.fetchrow("""
                        INSERT INTO wastage_events (
                            batch_id, stage, wastage_type, item_name, quantity, unit,
                            cost_allocation, reason, notes,
                            po_id, grn_id, created_by
                        ) VALUES (
                            $1, $2, 'reject', $3, $4, 'units',
                            $5, 'Rejected during receiving', $6,
                            $7, $8, $9
                        )
                        RETURNING id, event_id
                    """, grn['batch_id'], 'receiving', item['item_name'], 
                         float(item['reject']), item['reject_cost_allocation'],
                         item.get('notes'), po_id, grn_id, user_id)
                    
                    for p in photos:
                         await conn.execute("""
                            INSERT INTO wastage_photos (
                                wastage_event_id, photo_url, photo_path, file_name,
                                file_size_kb, uploaded_by
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                         """, wastage_event['id'], p['photo_url'], p['photo_path'], 
                             p['photo_path'].split('/')[-1], p['file_size'] or 0, user_id)

            # Update Statuses
            await conn.execute("UPDATE grns SET status = 'completed', completed_at = NOW() WHERE id = $1", grn_id)
            await conn.execute("UPDATE purchase_orders SET status = 'completed' WHERE id = $1", po_id)
            await po_service._log_status_change(conn, po_id, 'grn_generated', 'completed', str(user_id), "GRN Finalized")
            
            await conn.execute("UPDATE batches SET status = 'received' WHERE id = $1", grn['batch_id'])
            
            # Batch History
            await batch_tracking_service.add_batch_history(
                batch_number=batch['batch_number'],
                event=AddBatchHistoryRequest( 
                     stage=BatchStage.GRN,
                     event_type=BatchEventType.RECEIVED,
                     new_status=BatchStatus.RECEIVED,
                     event_details={'grn_number': grn['grn_number'], 'status': 'received'}
                ),
                created_by=str(user_id)
            )

            logger.info(f"✅ Finalized GRN {grn['grn_number']}")
            return await _get_grn_details_internal(conn, grn_id)

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in GRN finalize: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to finalize GRN: {e}")
        raise

# ============================================================================
# PHOTOS AND PDF
# ============================================================================

async def upload_grn_photos(
    grn_id: int,
    item_id: int,
    photo_type: str,
    files: List[UploadFile],
    user_id: str
) -> List[str]:
    """Upload photos to Supabase"""
    if photo_type not in ['damage', 'reject']:
        raise ValueError("photo_type must be 'damage' or 'reject'")
    
    # We need GRN number for path
    grn = await get_grn_by_id(grn_id)
    if not grn:
        raise ValueError("GRN not found")
        
    photo_urls = []
    
    for file in files:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
             raise ValueError("Only JPG/PNG allowed")

        unique_filename = f"{uuid.uuid4()}.{ext}"
        storage_path = f"{grn['grn_number']}/{item_id}/{photo_type}/{unique_filename}"
        
        file_bytes = await file.read()
        
        # Upload
        try:
             res = supabase.storage.from_('grn-photos').upload(
                 path=storage_path,
                 file=file_bytes,
                 file_options={"content-type": file.content_type}
             )
        except Exception as e:
             raise Exception(f"Upload failed: {e}")

        public_url = supabase.storage.from_('grn-photos').get_public_url(storage_path)
        
        # Save DB
        async with DatabaseTransaction() as conn:
            await conn.execute("""
                INSERT INTO grn_photos (grn_id, item_id, photo_type, photo_url, photo_path, uploaded_by, file_size)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, grn_id, item_id, photo_type, public_url, storage_path, user_id, 0) # size 0 or len(file_bytes)
        
        photo_urls.append(public_url)
        
    return photo_urls

async def delete_grn_photo(photo_id: int, user_id: str) -> bool:
    async with DatabaseTransaction() as conn:
        photo = await conn.fetchrow("SELECT * FROM grn_photos WHERE id = $1", photo_id)
        if not photo:
            raise ValueError("Photo not found")
            
        # Check GRN status
        grn = await conn.fetchrow("SELECT status FROM grns WHERE id = $1", photo['grn_id'])
        if grn['status'] == 'locked':
            raise ValueError("GRN locked")
            
        # Delete from storage
        supabase.storage.from_('grn-photos').remove([photo['photo_path']])
        
        # Delete from DB
        await conn.execute("DELETE FROM grn_photos WHERE id = $1", photo_id)
        return True

async def generate_blank_grn_pdf(grn_id: int) -> bytes:
    """Generate blank PDF template"""
    if not REPORTLAB_AVAILABLE:
        return b"PDF generation unavailable (ReportLab missing)"
        
    grn = await get_grn_by_id(grn_id)
    if not grn:
        raise ValueError("GRN not found")
        
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Goods Receipt Note: {grn['grn_number']}")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"PO #: {grn['po_number']}")
    p.drawString(50, height - 100, f"Batch #: {grn['batch_number']}")
    p.drawString(50, height - 120, f"Vendor: {grn['vendor_name']}")
    p.drawString(300, height - 80, f"Date: {date.today()}")
    
    # Items Header
    y = height - 160
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Item")
    p.drawString(250, y, "Exp Qty")
    p.drawString(320, y, "Actual")
    p.drawString(400, y, "Damage")
    p.drawString(480, y, "Reject")
    
    y -= 20
    p.setFont("Helvetica", 10)
    for item in grn['items']:
         p.drawString(50, y, str(item['item_name'])[:30])
         p.drawString(250, y, "_______") # Placeholder since we want blank for filling
         p.drawString(320, y, "_______")
         p.drawString(400, y, "_______")
         p.drawString(480, y, "_______")
         y -= 20
         
    p.showPage()
    p.save()
    return buffer.getvalue()
