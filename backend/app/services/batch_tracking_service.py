"""
================================================================================
Marketplace ERP - Batch Tracking Service
================================================================================
Version: 1.0.0
Last Updated: 2024-12-04

Description:
  Business logic for batch tracking module. Handles batch number generation,
  batch history tracking, document linking, repacking workflow, and search.

Functions:
  - generate_batch_number: Atomic batch number generation
  - get_batch_details: Complete batch information
  - get_batch_timeline: Visual timeline of batch journey
  - search_batches: Search with multiple criteria
  - create_repacked_batch: Repacking workflow
  - add_batch_history: Log event to batch history
  - archive_old_batches: Auto-archive batches 3 days after delivery
  - link_document_to_batch: Link documents to batch
  - get_batch_wastage_summary: All wastage for batch (integration with wastage module)

================================================================================
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import asyncpg

from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
from app.schemas.batch_tracking import (
    BatchStatus, BatchStage, BatchEventType, DocumentType,
    GenerateBatchRequest, RepackBatchRequest, AddBatchHistoryRequest,
    SearchBatchesRequest, BatchResponse, BatchDetailResponse,
    BatchTimelineResponse, BatchTimelineStage, BatchSearchResponse,
    BatchSearchResult, RepackBatchResponse, BatchHistoryEvent,
    BatchDocumentLink
)

logger = logging.getLogger(__name__)


# ============================================================================
# BATCH NUMBER GENERATION
# ============================================================================

async def _check_and_rollover_fy(conn: asyncpg.Connection):
    """
    Check if financial year rollover is needed and perform it.
    Called within a transaction before generating batch number.

    Indian FY: April 1 to March 31
    Example: FY 2025-26 = April 1, 2025 to March 31, 2026
    """
    from datetime import date

    # Get current batch sequence
    query = """
        SELECT fy_end_date, financial_year, prefix
        FROM batch_sequence
        WHERE id = 1
    """
    seq = await conn.fetchrow(query)

    if not seq:
        return

    today = date.today()
    fy_end_date = seq['fy_end_date']

    # Check if we've passed the FY end date
    if today > fy_end_date:
        # Calculate new FY
        # If today is after March 31, new FY starts April 1 of current year
        if today.month >= 4:  # Apr-Dec
            new_fy_start = date(today.year, 4, 1)
            new_fy_end = date(today.year + 1, 3, 31)
            new_fy_short = f"{str(today.year)[-2:]}{str(today.year + 1)[-2:]}"  # 2526
        else:  # Jan-Mar (already in next FY)
            new_fy_start = date(today.year - 1, 4, 1)
            new_fy_end = date(today.year, 3, 31)
            new_fy_short = f"{str(today.year - 1)[-2:]}{str(today.year)[-2:]}"  # 2425

        # Rollover: reset sequence, update FY
        update_query = """
            UPDATE batch_sequence
            SET current_number = 0,
                financial_year = $1,
                fy_start_date = $2,
                fy_end_date = $3,
                updated_at = NOW()
            WHERE id = 1
        """
        await conn.execute(update_query, new_fy_short, new_fy_start, new_fy_end)

        logger.info(f"✅ FY Rollover: Reset batch sequence. New FY: {new_fy_short} ({new_fy_start} to {new_fy_end})")


async def generate_batch_number(
    po_id: Optional[int] = None,
    grn_id: Optional[int] = None,
    created_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate new sequential batch number (thread-safe).
    Format: B/2526/0001 (prefix/fy_short/sequence)

    Args:
        po_id: Purchase Order ID (optional)
        grn_id: GRN ID (optional)
        created_by: User UUID who created the batch

    Returns:
        Dict with batch_id, batch_number, status, created_at

    Raises:
        Exception: If batch generation fails
    """
    try:
        async with DatabaseTransaction() as conn:
            # 1. Check if FY rollover needed
            await _check_and_rollover_fy(conn)

            # 2. Lock and increment batch_sequence (atomic)
            sequence_query = """
                UPDATE batch_sequence
                SET current_number = current_number + 1,
                    updated_at = NOW()
                WHERE id = 1
                RETURNING current_number, prefix, financial_year
            """
            sequence_row = await conn.fetchrow(sequence_query)

            if not sequence_row:
                raise Exception("Batch sequence not initialized")

            current_number = sequence_row['current_number']
            prefix = sequence_row['prefix']
            financial_year = sequence_row['financial_year']

            # 3. Format batch number: B/2526/0001 - pad to 4 digits
            batch_number = f"{prefix}/{financial_year}/{current_number:04d}"

            # 3. Create batch record
            insert_query = """
                INSERT INTO batches (
                    batch_number, status, po_id, grn_id, created_by
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, batch_number, status, created_at
            """
            batch_row = await conn.fetchrow(
                insert_query,
                batch_number,
                BatchStatus.ORDERED.value,
                po_id,
                grn_id,
                created_by
            )

            # 4. Add initial history event
            history_query = """
                INSERT INTO batch_history (
                    batch_id, stage, event_type, new_status, created_by
                )
                VALUES ($1, $2, $3, $4, $5)
            """
            await conn.execute(
                history_query,
                batch_row['id'],
                BatchStage.PO.value,
                BatchEventType.CREATED.value,
                BatchStatus.ORDERED.value,
                created_by
            )

            # 5. Link documents (if provided)
            if po_id:
                await _link_document_internal(
                    conn, batch_row['id'], DocumentType.PO.value, po_id, None, created_by
                )
            if grn_id:
                await _link_document_internal(
                    conn, batch_row['id'], DocumentType.GRN.value, grn_id, None, created_by
                )

            logger.info(f"✅ Generated batch number: {batch_number} (ID: {batch_row['id']})")

            return {
                "batch_id": batch_row['id'],
                "batch_number": batch_row['batch_number'],
                "status": batch_row['status'],
                "created_at": batch_row['created_at']
            }

    except Exception as e:
        logger.error(f"❌ Failed to generate batch number: {e}")
        raise


# ============================================================================
# BATCH RETRIEVAL
# ============================================================================

async def get_batch_details(batch_number: str) -> Optional[Dict[str, Any]]:
    """
    Get complete batch details with history and documents.

    Args:
        batch_number: Batch number to retrieve

    Returns:
        Complete batch details or None if not found
    """
    try:
        # 1. Get batch record
        batch_query = """
            SELECT
                b.id, b.batch_number, b.status, b.is_repacked,
                b.parent_batch_id, b.po_id, b.grn_id,
                b.created_at, b.archived_at,
                pb.batch_number as parent_batch_number,
                cb.batch_number as child_batch_number
            FROM batches b
            LEFT JOIN batches pb ON b.parent_batch_id = pb.id
            LEFT JOIN batches cb ON cb.parent_batch_id = b.id
            WHERE b.batch_number = $1
        """
        batch = await fetch_one(batch_query, batch_number)

        if not batch:
            return None

        # 2. Get linked documents
        docs_query = """
            SELECT document_type, document_id, document_number
            FROM batch_documents
            WHERE batch_id = $1
            ORDER BY linked_at
        """
        documents = await fetch_all(docs_query, batch['id'])

        # 3. Get history events
        history_query = """
            SELECT
                bh.stage, bh.event_type, bh.event_details,
                bh.old_status, bh.new_status, bh.location,
                bh.created_at,
                u.email as created_by_email
            FROM batch_history bh
            LEFT JOIN auth.users u ON bh.created_by = u.id
            WHERE bh.batch_id = $1
            ORDER BY bh.created_at ASC
        """
        history = await fetch_all(history_query, batch['id'])

        # 4. Build response
        return {
            "batch_id": batch['id'],
            "batch_number": batch['batch_number'],
            "status": batch['status'],
            "is_repacked": batch['is_repacked'],
            "parent_batch_number": batch['parent_batch_number'],
            "child_batch_number": batch['child_batch_number'],
            "po_id": batch['po_id'],
            "grn_id": batch['grn_id'],
            "created_at": batch['created_at'],
            "archived_at": batch['archived_at'],
            "documents": [
                {
                    "document_type": doc['document_type'],
                    "document_id": doc['document_id'],
                    "document_number": doc['document_number']
                }
                for doc in documents
            ],
            "history": [
                {
                    "stage": h['stage'],
                    "event_type": h['event_type'],
                    "event_details": h['event_details'],
                    "old_status": h['old_status'],
                    "new_status": h['new_status'],
                    "location": h['location'],
                    "created_at": h['created_at'],
                    "created_by_name": h['created_by_email']
                }
                for h in history
            ]
        }

    except Exception as e:
        logger.error(f"❌ Failed to get batch details for {batch_number}: {e}")
        raise


async def get_batch_timeline(batch_number: str) -> Optional[Dict[str, Any]]:
    """
    Get visual timeline of batch journey through stages.

    Args:
        batch_number: Batch number

    Returns:
        Timeline data or None if batch not found
    """
    try:
        # Get batch history
        details = await get_batch_details(batch_number)
        if not details:
            return None

        # Define stage order and names
        stage_map = {
            "po": "Purchase Order",
            "grn": "Goods Receipt",
            "grading": "Grading & Sorting",
            "packing": "Packing",
            "inventory": "Inventory",
            "allocation": "Order Allocation",
            "delivery": "Delivery"
        }

        # Build timeline from history
        timeline = []
        history_by_stage = {}

        for event in details['history']:
            stage = event['stage']
            if stage not in history_by_stage:
                history_by_stage[stage] = []
            history_by_stage[stage].append(event)

        # Create timeline stages
        for stage_key, stage_name in stage_map.items():
            if stage_key in history_by_stage:
                events = history_by_stage[stage_key]
                latest_event = events[-1]  # Most recent event in this stage

                timeline.append({
                    "stage": stage_key,
                    "stage_name": stage_name,
                    "timestamp": latest_event['created_at'],
                    "status": "completed",
                    "details": latest_event.get('event_details', {})
                })

        return {
            "batch_number": batch_number,
            "timeline": timeline
        }

    except Exception as e:
        logger.error(f"❌ Failed to get batch timeline for {batch_number}: {e}")
        raise


# ============================================================================
# BATCH SEARCH
# ============================================================================

async def search_batches(filters: SearchBatchesRequest) -> Dict[str, Any]:
    """
    Search batches with multiple filter criteria.

    Args:
        filters: Search filters and pagination

    Returns:
        Search results with pagination
    """
    try:
        # Build WHERE conditions
        conditions = []
        params = []
        param_count = 1

        # Batch number (partial match)
        if filters.batch_number:
            conditions.append(f"b.batch_number ILIKE ${param_count}")
            params.append(f"%{filters.batch_number}%")
            param_count += 1

        # Status
        if filters.status:
            conditions.append(f"b.status = ${param_count}")
            params.append(filters.status.value)
            param_count += 1

        # Date range
        if filters.date_from:
            conditions.append(f"b.created_at >= ${param_count}")
            # Convert string to date object for asyncpg
            from datetime import datetime
            date_obj = datetime.strptime(filters.date_from, "%Y-%m-%d").date()
            params.append(date_obj)
            param_count += 1

        if filters.date_to:
            conditions.append(f"b.created_at <= ${param_count}")
            # Convert string to date object for asyncpg
            from datetime import datetime
            date_obj = datetime.strptime(filters.date_to, "%Y-%m-%d").date()
            params.append(date_obj)
            param_count += 1

        # Archived filter
        if not filters.is_archived:
            conditions.append("b.archived_at IS NULL")

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM batches b
            {where_clause}
        """
        count_result = await fetch_one(count_query, *params)
        total = count_result['total'] if count_result else 0

        # Get paginated results
        offset = (filters.page - 1) * filters.limit
        search_query = f"""
            SELECT
                b.id, b.batch_number, b.status, b.is_repacked,
                b.created_at
            FROM batches b
            {where_clause}
            ORDER BY b.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([filters.limit, offset])

        batches = await fetch_all(search_query, *params)

        # Build response
        results = [
            {
                "batch_id": b['id'],
                "batch_number": b['batch_number'],
                "status": b['status'],
                "is_repacked": b['is_repacked'],
                "created_at": b['created_at'],
                "farm": None,  # TODO: Get from linked PO when implemented
                "current_location": None  # TODO: Get from latest history
            }
            for b in batches
        ]

        return {
            "batches": results,
            "total": total,
            "page": filters.page,
            "limit": filters.limit,
            "pages": (total + filters.limit - 1) // filters.limit if total > 0 else 1
        }

    except Exception as e:
        logger.error(f"❌ Failed to search batches: {e}")
        raise


# ============================================================================
# BATCH REPACKING
# ============================================================================

async def create_repacked_batch(
    parent_batch_number: str,
    repack_data: RepackBatchRequest,
    created_by: str
) -> Dict[str, Any]:
    """
    Create repacked batch (B###R) from damaged items.

    Args:
        parent_batch_number: Original batch number
        repack_data: Repacking details
        created_by: User UUID

    Returns:
        New repacked batch details

    Raises:
        ValueError: If parent batch already repacked or invalid quantities
        Exception: If repacking fails
    """
    try:
        # 1. Validate parent batch exists and not already repacked
        parent_query = """
            SELECT id, batch_number, status
            FROM batches
            WHERE batch_number = $1
        """
        parent_batch = await fetch_one(parent_query, parent_batch_number)

        if not parent_batch:
            raise ValueError(f"Parent batch {parent_batch_number} not found")

        # Check if already repacked
        child_check_query = """
            SELECT id FROM batches WHERE parent_batch_id = $1
        """
        existing_child = await fetch_one(child_check_query, parent_batch['id'])

        if existing_child:
            raise ValueError(f"Parent batch {parent_batch_number} already has a repacked child")

        # 2. Validate quantities
        if repack_data.repacked_quantity > repack_data.damaged_quantity:
            raise ValueError("Repacked quantity cannot exceed damaged quantity")

        # 3. Generate repacked batch number (B/2526/0001R)
        # Format: parent_batch + 'R' suffix
        new_batch_number = f"{parent_batch_number}R"

        # 4. Create repacked batch
        async with DatabaseTransaction() as conn:
            insert_query = """
                INSERT INTO batches (
                    batch_number, is_repacked, parent_batch_id,
                    status, po_id, grn_id, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, batch_number, status, created_at
            """
            new_batch = await conn.fetchrow(
                insert_query,
                new_batch_number,
                True,
                parent_batch['id'],
                BatchStatus.IN_INVENTORY.value,
                parent_batch.get('po_id'),
                parent_batch.get('grn_id'),
                created_by
            )

            # 5. Add history event
            history_query = """
                INSERT INTO batch_history (
                    batch_id, stage, event_type, event_details, new_status, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            await conn.execute(
                history_query,
                new_batch['id'],
                BatchStage.INVENTORY.value,
                BatchEventType.REPACKED.value,
                {
                    "parent_batch": parent_batch_number,
                    "reason": repack_data.reason,
                    "damaged_quantity": repack_data.damaged_quantity,
                    "repacked_quantity": repack_data.repacked_quantity
                },
                BatchStatus.IN_INVENTORY.value,
                created_by
            )

            logger.info(f"✅ Created repacked batch: {new_batch_number} from {parent_batch_number}")

            return {
                "parent_batch": parent_batch_number,
                "new_batch_number": new_batch['batch_number'],
                "new_batch_id": new_batch['id'],
                "status": new_batch['status'],
                "created_at": new_batch['created_at']
            }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error in repacking: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create repacked batch: {e}")
        raise


# ============================================================================
# BATCH HISTORY
# ============================================================================

async def add_batch_history(
    batch_number: str,
    event: AddBatchHistoryRequest,
    created_by: str
) -> Dict[str, Any]:
    """
    Add event to batch history (called by other modules).

    Args:
        batch_number: Batch number
        event: Event details
        created_by: User UUID

    Returns:
        Created history record

    Raises:
        ValueError: If batch not found
        Exception: If history add fails
    """
    try:
        # 1. Get batch ID
        batch_query = "SELECT id, status FROM batches WHERE batch_number = $1"
        batch = await fetch_one(batch_query, batch_number)

        if not batch:
            raise ValueError(f"Batch {batch_number} not found")

        old_status = batch['status']
        new_status = event.new_status.value if event.new_status else old_status

        # 2. Insert history event
        async with DatabaseTransaction() as conn:
            history_query = """
                INSERT INTO batch_history (
                    batch_id, stage, event_type, event_details,
                    old_status, new_status, location, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, created_at
            """
            history = await conn.fetchrow(
                history_query,
                batch['id'],
                event.stage.value,
                event.event_type.value,
                event.event_details,
                old_status if new_status != old_status else None,
                new_status if new_status != old_status else None,
                event.location,
                created_by
            )

            # 3. Update batch status if changed
            if new_status != old_status:
                update_query = """
                    UPDATE batches
                    SET status = $1
                    WHERE id = $2
                """
                await conn.execute(update_query, new_status, batch['id'])

            return {
                "history_id": history['id'],
                "batch_number": batch_number,
                "created_at": history['created_at']
            }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add batch history: {e}")
        raise


# ============================================================================
# DOCUMENT LINKING
# ============================================================================

async def link_document_to_batch(
    batch_number: str,
    document_type: str,
    document_id: int,
    document_number: Optional[str],
    linked_by: str
) -> Dict[str, Any]:
    """
    Link document to batch.

    Args:
        batch_number: Batch number
        document_type: Type of document (po, grn, so, invoice, packing_label)
        document_id: Document ID
        document_number: Human-readable document number
        linked_by: User UUID

    Returns:
        Link confirmation

    Raises:
        ValueError: If batch not found
        Exception: If linking fails
    """
    try:
        # Get batch ID
        batch_query = "SELECT id FROM batches WHERE batch_number = $1"
        batch = await fetch_one(batch_query, batch_number)

        if not batch:
            raise ValueError(f"Batch {batch_number} not found")

        # Insert link
        query = """
            INSERT INTO batch_documents (
                batch_id, document_type, document_id, document_number, linked_by
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, linked_at
        """
        result = await execute_query(
            query,
            batch['id'],
            document_type,
            document_id,
            document_number,
            linked_by
        )

        logger.info(f"✅ Linked {document_type} #{document_id} to batch {batch_number}")

        return {
            "batch_number": batch_number,
            "document_type": document_type,
            "document_id": document_id,
            "linked_at": datetime.now()
        }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to link document: {e}")
        raise


async def _link_document_internal(
    conn: asyncpg.Connection,
    batch_id: int,
    document_type: str,
    document_id: int,
    document_number: Optional[str],
    linked_by: Optional[str]
):
    """Internal helper to link document within a transaction."""
    query = """
        INSERT INTO batch_documents (
            batch_id, document_type, document_id, document_number, linked_by
        )
        VALUES ($1, $2, $3, $4, $5)
    """
    await conn.execute(query, batch_id, document_type, document_id, document_number, linked_by)


# ============================================================================
# BATCH ARCHIVING
# ============================================================================

async def archive_old_batches() -> Dict[str, Any]:
    """
    Archive batches that are 5+ days past delivery (scheduled job).

    Returns:
        Count of archived batches
    """
    try:
        # Find batches delivered 5+ days ago
        cutoff_date = datetime.now() - timedelta(days=5)

        query = """
            UPDATE batches
            SET status = $1, archived_at = NOW()
            WHERE status = $2
            AND created_at < $3
            AND archived_at IS NULL
            RETURNING id, batch_number
        """
        archived = await fetch_all(
            query,
            BatchStatus.ARCHIVED.value,
            BatchStatus.DELIVERED.value,
            cutoff_date
        )

        count = len(archived)
        if count > 0:
            logger.info(f"✅ Archived {count} old batches")

        return {
            "archived_count": count,
            "archived_batches": [b['batch_number'] for b in archived]
        }

    except Exception as e:
        logger.error(f"❌ Failed to archive old batches: {e}")
        raise


# ============================================================================
# ACTIVE BATCHES
# ============================================================================

async def get_active_batches(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get all active (non-archived) batches.

    Args:
        status: Optional status filter
        page: Page number
        limit: Items per page

    Returns:
        Paginated active batches
    """
    try:
        # Build query
        conditions = ["archived_at IS NULL"]
        params = []
        param_count = 1

        if status:
            conditions.append(f"status = ${param_count}")
            params.append(status)
            param_count += 1

        where_clause = "WHERE " + " AND ".join(conditions)

        # Count
        count_query = f"SELECT COUNT(*) as total FROM batches {where_clause}"
        count_result = await fetch_one(count_query, *params)
        total = count_result['total'] if count_result else 0

        # Get batches
        offset = (page - 1) * limit
        query = f"""
            SELECT id, batch_number, status, is_repacked, created_at
            FROM batches
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        batches = await fetch_all(query, *params)

        return {
            "batches": batches,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 1
        }

    except Exception as e:
        logger.error(f"❌ Failed to get active batches: {e}")
        raise


# ============================================================================
# BATCH CONFIGURATION
# ============================================================================

async def get_batch_configuration() -> Dict[str, Any]:
    """
    Get current batch sequence configuration.

    Returns:
        Current prefix, sequence number, FY info
    """
    try:
        query = """
            SELECT prefix, current_number, financial_year,
                   fy_start_date, fy_end_date, updated_at
            FROM batch_sequence
            WHERE id = 1
        """
        config = await fetch_one(query)

        if not config:
            raise Exception("Batch configuration not found")

        return {
            "prefix": config['prefix'],
            "current_number": config['current_number'],
            "financial_year": config['financial_year'],
            "fy_start_date": config['fy_start_date'].isoformat(),
            "fy_end_date": config['fy_end_date'].isoformat(),
            "next_batch_number": f"{config['prefix']}/{config['financial_year']}/{config['current_number'] + 1:04d}",
            "updated_at": config['updated_at']
        }

    except Exception as e:
        logger.error(f"❌ Failed to get batch configuration: {e}")
        raise


async def update_batch_configuration(
    prefix: Optional[str] = None,
    starting_number: Optional[int] = None,
    financial_year: Optional[str] = None,
    fy_start_date: Optional[str] = None,
    fy_end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update batch sequence configuration (admin only).

    Args:
        prefix: New prefix (e.g., 'B', 'BATCH')
        starting_number: Reset sequence to this number
        financial_year: Override FY short format (e.g., '2526')
        fy_start_date: Override FY start date (YYYY-MM-DD)
        fy_end_date: Override FY end date (YYYY-MM-DD)

    Returns:
        Updated configuration

    Raises:
        ValueError: If invalid parameters
        Exception: If update fails
    """
    try:
        # Build update query dynamically
        updates = []
        params = []
        param_count = 1

        if prefix is not None:
            updates.append(f"prefix = ${param_count}")
            params.append(prefix)
            param_count += 1

        if starting_number is not None:
            if starting_number < 0:
                raise ValueError("Starting number must be >= 0")
            updates.append(f"current_number = ${param_count}")
            params.append(starting_number)
            param_count += 1

        if financial_year is not None:
            if len(financial_year) != 4:
                raise ValueError("Financial year must be 4 digits (e.g., '2526')")
            updates.append(f"financial_year = ${param_count}")
            params.append(financial_year)
            param_count += 1

        if fy_start_date is not None:
            updates.append(f"fy_start_date = ${param_count}")
            params.append(fy_start_date)
            param_count += 1

        if fy_end_date is not None:
            updates.append(f"fy_end_date = ${param_count}")
            params.append(fy_end_date)
            param_count += 1

        if not updates:
            raise ValueError("No updates provided")

        # Add updated_at
        updates.append("updated_at = NOW()")

        query = f"""
            UPDATE batch_sequence
            SET {', '.join(updates)}
            WHERE id = 1
            RETURNING prefix, current_number, financial_year, fy_start_date, fy_end_date
        """

        result = await execute_query(query, *params)

        logger.info(f"✅ Updated batch configuration: {result}")

        return {
            "prefix": result['prefix'],
            "current_number": result['current_number'],
            "financial_year": result['financial_year'],
            "fy_start_date": result['fy_start_date'].isoformat() if result['fy_start_date'] else None,
            "fy_end_date": result['fy_end_date'].isoformat() if result['fy_end_date'] else None,
            "next_batch_number": f"{result['prefix']}/{result['financial_year']}/{result['current_number'] + 1:04d}"
        }

    except ValueError as ve:
        logger.warning(f"⚠️ Validation error: {ve}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update batch configuration: {e}")
        raise
