"""
================================================================================
Farm Management System - Biofloc Service Layer
================================================================================
Version: 1.0.0
Last Updated: 2025-11-18

Description:
    Business logic for biofloc aquaculture management module.
    Handles tanks, batches, feeding, sampling, mortality, water tests,
    harvests, and reporting.

================================================================================
"""

import logging
import math
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import date, datetime
from fastapi import HTTPException, status
from uuid import UUID

from app.database import (
    fetch_one, fetch_all, execute_query, DatabaseTransaction,
    fetch_one_tx, fetch_all_tx, execute_query_tx
)
from app.helpers.inventory_integration import InventoryIntegration
from app.schemas.biofloc import *

logger = logging.getLogger(__name__)

# ============================================================================
# TANK OPERATIONS
# ============================================================================

async def get_tanks_list(
    status_filter: Optional[TankStatus] = None,
    is_active: Optional[bool] = True,
    page: int = 1,
    limit: int = 50
) -> Dict:
    """Get paginated list of tanks"""
    where_conditions = []
    params = []
    param_count = 1

    if status_filter:
        where_conditions.append(f"t.status = ${param_count}")
        params.append(status_filter.value)
        param_count += 1

    if is_active is not None:
        where_conditions.append(f"t.is_active = ${param_count}")
        params.append(is_active)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM biofloc_tanks t {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get tanks
    offset = (page - 1) * limit
    tanks_query = f"""
        SELECT
            t.id, t.tank_name, t.tank_code, t.capacity_liters, t.location,
            t.tank_type, t.status, t.current_batch_id, t.is_active,
            t.created_at, t.updated_at,
            b.batch_code as current_batch_code
        FROM biofloc_tanks t
        LEFT JOIN biofloc_batches b ON b.id = t.current_batch_id
        {where_clause}
        ORDER BY t.tank_name
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    tanks = await fetch_all(tanks_query, *params)

    return {"tanks": tanks, "total": total, "page": page, "limit": limit}


async def get_tank(tank_id: UUID) -> Dict:
    """Get single tank by ID"""
    tank = await fetch_one(
        """
        SELECT
            t.*,
            b.batch_code as current_batch_code
        FROM biofloc_tanks t
        LEFT JOIN biofloc_batches b ON b.id = t.current_batch_id
        WHERE t.id = $1
        """,
        tank_id
    )

    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    return tank


async def create_tank(request: TankCreate, user_id: UUID) -> Dict:
    """Create new tank"""
    # Check if tank code already exists
    existing = await fetch_one(
        "SELECT id FROM biofloc_tanks WHERE tank_code = $1",
        request.tank_code
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tank with code '{request.tank_code}' already exists"
        )

    # Create tank
    tank_id = await execute_query(
        """
        INSERT INTO biofloc_tanks (
            tank_name, tank_code, capacity_liters, location,
            tank_type, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        request.tank_name,
        request.tank_code,
        request.capacity_liters,
        request.location,
        request.tank_type.value,
        request.notes,
        user_id
    )

    return await get_tank(tank_id)


async def update_tank(tank_id: UUID, request: TankUpdate) -> Dict:
    """Update tank"""
    # Check if exists
    existing = await fetch_one("SELECT id FROM biofloc_tanks WHERE id = $1", tank_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    # Build update query
    update_fields = []
    params = []
    param_count = 1

    if request.tank_name is not None:
        update_fields.append(f"tank_name = ${param_count}")
        params.append(request.tank_name)
        param_count += 1

    if request.capacity_liters is not None:
        update_fields.append(f"capacity_liters = ${param_count}")
        params.append(request.capacity_liters)
        param_count += 1

    if request.location is not None:
        update_fields.append(f"location = ${param_count}")
        params.append(request.location)
        param_count += 1

    if request.tank_type is not None:
        update_fields.append(f"tank_type = ${param_count}")
        params.append(request.tank_type.value)
        param_count += 1

    if request.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(request.status.value)
        param_count += 1

    if request.notes is not None:
        update_fields.append(f"notes = ${param_count}")
        params.append(request.notes)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    params.append(tank_id)

    query = f"""
        UPDATE biofloc_tanks
        SET {', '.join(update_fields)}, updated_at = NOW()
        WHERE id = ${param_count}
    """
    await execute_query(query, *params)

    return await get_tank(tank_id)


async def delete_tank(tank_id: UUID) -> None:
    """Soft delete tank"""
    # Check if tank has active batch
    tank = await get_tank(tank_id)
    if tank.get("current_batch_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tank with active batch"
        )

    await execute_query(
        "UPDATE biofloc_tanks SET is_active = FALSE WHERE id = $1",
        tank_id
    )


async def get_tank_history(tank_id: UUID) -> List[Dict]:
    """Get batch assignment history for tank"""
    history = await fetch_all(
        """
        SELECT
            a.id, a.batch_id, b.batch_code, a.start_date, a.end_date,
            a.transfer_reason, a.fish_count_at_transfer,
            a.avg_weight_at_transfer_g, a.notes,
            CASE
                WHEN a.end_date IS NULL THEN DATE_PART('day', NOW() - a.start_date)
                ELSE DATE_PART('day', a.end_date - a.start_date)
            END as cycle_duration_days
        FROM biofloc_batch_tank_assignments a
        JOIN biofloc_batches b ON b.id = a.batch_id
        WHERE a.tank_id = $1
        ORDER BY a.start_date DESC
        """,
        tank_id
    )
    return history


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def get_batches_list(
    status_filter: Optional[BatchStatus] = None,
    species: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Dict:
    """Get paginated list of batches"""
    where_conditions = []
    params = []
    param_count = 1

    if status_filter:
        where_conditions.append(f"b.status = ${param_count}")
        params.append(status_filter.value)
        param_count += 1

    if species:
        where_conditions.append(f"b.species ILIKE ${param_count}")
        params.append(f"%{species}%")
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM biofloc_batches b {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get batches
    offset = (page - 1) * limit
    batches_query = f"""
        SELECT
            b.*,
            t.id as current_tank_id,
            t.tank_name as current_tank_name
        FROM biofloc_batches b
        LEFT JOIN biofloc_batch_tank_assignments a ON a.batch_id = b.id AND a.end_date IS NULL
        LEFT JOIN biofloc_tanks t ON t.id = a.tank_id
        {where_clause}
        ORDER BY b.stocking_date DESC, b.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    batches = await fetch_all(batches_query, *params)

    return {"batches": batches, "total": total, "page": page, "limit": limit}


async def get_batch(batch_id: UUID) -> Dict:
    """Get single batch by ID"""
    batch = await fetch_one(
        """
        SELECT
            b.*,
            t.id as current_tank_id,
            t.tank_name as current_tank_name
        FROM biofloc_batches b
        LEFT JOIN biofloc_batch_tank_assignments a ON a.batch_id = b.id AND a.end_date IS NULL
        LEFT JOIN biofloc_tanks t ON t.id = a.tank_id
        WHERE b.id = $1
        """,
        batch_id
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    return batch


async def create_batch(request: BatchCreate, user_id: UUID) -> Dict:
    """Create new batch with initial tank assignment"""
    # Check if batch code exists
    existing = await fetch_one(
        "SELECT id FROM biofloc_batches WHERE batch_code = $1",
        request.batch_code
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch with code '{request.batch_code}' already exists"
        )

    # Verify tank exists and is available
    tank = await fetch_one(
        "SELECT id, status, current_batch_id FROM biofloc_tanks WHERE id = $1",
        request.tank_id
    )

    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    if tank["current_batch_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tank already has an active batch"
        )

    async with DatabaseTransaction() as conn:
        # Create batch (initial_total_biomass_kg calculated by trigger)
        batch_id = await execute_query_tx(
            """
            INSERT INTO biofloc_batches (
                batch_code, species, source, stocking_date,
                initial_count, initial_avg_weight_g, notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            request.batch_code,
            request.species,
            request.source,
            request.stocking_date,
            request.initial_count,
            request.initial_avg_weight_g,
            request.notes,
            user_id,
            conn=conn
        )

        # Create initial tank assignment
        await execute_query_tx(
            """
            INSERT INTO biofloc_batch_tank_assignments (
                batch_id, tank_id, start_date, transfer_reason,
                fish_count_at_transfer, avg_weight_at_transfer_g,
                created_by
            )
            VALUES ($1, $2, $3, 'initial stocking', $4, $5, $6)
            """,
            batch_id,
            request.tank_id,
            request.stocking_date,
            request.initial_count,
            request.initial_avg_weight_g,
            user_id,
            conn=conn
        )

        # Initialize cycle costs
        await execute_query_tx(
            "INSERT INTO biofloc_cycle_costs (batch_id) VALUES ($1) ON CONFLICT (batch_id) DO NOTHING",
            batch_id,
            conn=conn
        )

    return await get_batch(batch_id)


async def transfer_batch(
    batch_id: UUID,
    request: BatchTransferRequest,
    user_id: UUID
) -> Dict:
    """Transfer batch to different tank"""
    # Get batch
    batch = await get_batch(batch_id)

    if batch["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only transfer active batches"
        )

    # Verify new tank exists and is available
    new_tank = await fetch_one(
        "SELECT id, current_batch_id FROM biofloc_tanks WHERE id = $1",
        request.to_tank_id
    )

    if not new_tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target tank not found"
        )

    if new_tank["current_batch_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target tank already has an active batch"
        )

    async with DatabaseTransaction() as conn:
        # End current assignment
        if request.from_tank_id:
            await execute_query_tx(
                """
                UPDATE biofloc_batch_tank_assignments
                SET end_date = $1
                WHERE batch_id = $2 AND tank_id = $3 AND end_date IS NULL
                """,
                request.transfer_date,
                batch_id,
                request.from_tank_id,
                conn=conn
            )

        # Create new assignment
        await execute_query_tx(
            """
            INSERT INTO biofloc_batch_tank_assignments (
                batch_id, tank_id, start_date, transfer_reason,
                fish_count_at_transfer, avg_weight_at_transfer_g,
                notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            batch_id,
            request.to_tank_id,
            request.transfer_date,
            request.transfer_reason.value,
            request.fish_count,
            request.avg_weight_g,
            request.notes,
            user_id,
            conn=conn
        )

    return await get_batch(batch_id)


# ============================================================================
# FEEDING OPERATIONS
# ============================================================================

async def record_feeding_session(
    request: FeedingSessionCreate,
    user_id: UUID,
    username: str
) -> Dict:
    """Record feeding session with inventory deduction"""
    # Get tank and verify it has active batch
    tank = await fetch_one(
        "SELECT id, current_batch_id FROM biofloc_tanks WHERE id = $1",
        request.tank_id
    )

    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    if not tank["current_batch_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tank has no active batch"
        )

    # Use inventory integration for batch deduction
    inv = InventoryIntegration(module_name="biofloc")

    deductions = [
        {"sku": item.sku, "quantity": float(item.quantity_kg), "notes": item.notes}
        for item in request.feed_items
    ]

    try:
        inv_result = await inv.batch_deduct(
            deductions=deductions,
            module_reference="biofloc",
            tank_id=str(request.tank_id),
            batch_id=str(tank["current_batch_id"]),
            session_number=request.session_number,
            global_notes=request.notes,
            user_id=str(user_id),
            username=username
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inventory deduction failed: {str(e)}"
        )

    # Calculate total feed
    total_feed = sum(item.quantity_kg for item in request.feed_items)

    # Prepare feed_items JSON with transaction IDs
    feed_items_json = []
    for i, item in enumerate(request.feed_items):
        feed_items_json.append({
            "sku": item.sku,
            "quantity_kg": float(item.quantity_kg),
            "notes": item.notes,
            "transaction_id": str(inv_result["transaction_ids"][i]) if i < len(inv_result["transaction_ids"]) else None
        })

    # Create feeding session record
    session_id = await execute_query(
        """
        INSERT INTO biofloc_feeding_sessions (
            tank_id, batch_id, feeding_date, session_number, feed_time,
            feed_items, total_feed_kg, total_cost, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10)
        RETURNING id
        """,
        request.tank_id,
        tank["current_batch_id"],
        request.feeding_date,
        request.session_number,
        request.feed_time,
        str(feed_items_json).replace("'", '"'),  # Convert to JSON string
        total_feed,
        inv_result["total_cost"],
        request.notes,
        user_id
    )

    # Fetch created session
    session = await fetch_one(
        """
        SELECT
            f.*, t.tank_name, b.batch_code
        FROM biofloc_feeding_sessions f
        JOIN biofloc_tanks t ON t.id = f.tank_id
        JOIN biofloc_batches b ON b.id = f.batch_id
        WHERE f.id = $1
        """,
        session_id
    )

    return session


async def get_feeding_sessions(
    tank_id: Optional[UUID] = None,
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get feeding sessions with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if tank_id:
        where_conditions.append(f"f.tank_id = ${param_count}")
        params.append(tank_id)
        param_count += 1

    if batch_id:
        where_conditions.append(f"f.batch_id = ${param_count}")
        params.append(batch_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"f.feeding_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"f.feeding_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_feeding_sessions f {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get sessions
    offset = (page - 1) * limit
    sessions_query = f"""
        SELECT
            f.*, t.tank_name, b.batch_code
        FROM biofloc_feeding_sessions f
        JOIN biofloc_tanks t ON t.id = f.tank_id
        JOIN biofloc_batches b ON b.id = f.batch_id
        {where_clause}
        ORDER BY f.feeding_date DESC, f.session_number DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    sessions = await fetch_all(sessions_query, *params)

    return {"feedings": sessions, "total": total, "page": page, "limit": limit}


# ============================================================================
# SAMPLING OPERATIONS
# ============================================================================

async def record_sampling(request: SamplingCreate, user_id: UUID) -> Dict:
    """Record sampling data"""
    # Verify batch exists
    batch = await get_batch(request.batch_id)

    # Calculate condition factor if length is provided
    condition_factor = None
    if request.avg_length_cm and request.avg_length_cm > 0:
        condition_factor = (request.avg_weight_g / (request.avg_length_cm ** 3)) * 100

    # Create sampling record
    sampling_id = await execute_query(
        """
        INSERT INTO biofloc_sampling (
            batch_id, tank_id, sample_date, sample_size,
            avg_weight_g, min_weight_g, max_weight_g, std_deviation_g,
            avg_length_cm, min_length_cm, max_length_cm,
            condition_factor, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING id
        """,
        request.batch_id,
        request.tank_id,
        request.sample_date,
        request.sample_size,
        request.avg_weight_g,
        request.min_weight_g,
        request.max_weight_g,
        request.std_deviation_g,
        request.avg_length_cm,
        request.min_length_cm,
        request.max_length_cm,
        condition_factor,
        request.notes,
        user_id
    )

    # Update batch current weight
    await execute_query(
        """
        UPDATE biofloc_batches
        SET
            current_avg_weight_g = $1,
            current_total_biomass_kg = (current_count * $1) / 1000.0,
            updated_at = NOW()
        WHERE id = $2
        """,
        request.avg_weight_g,
        request.batch_id
    )

    # Fetch created sampling
    sampling = await fetch_one(
        """
        SELECT
            s.*, b.batch_code, t.tank_name
        FROM biofloc_sampling s
        JOIN biofloc_batches b ON b.id = s.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = s.tank_id
        WHERE s.id = $1
        """,
        sampling_id
    )

    return sampling


async def get_samplings(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get sampling records with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if batch_id:
        where_conditions.append(f"s.batch_id = ${param_count}")
        params.append(batch_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"s.sample_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"s.sample_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_sampling s {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get samplings
    offset = (page - 1) * limit
    samplings_query = f"""
        SELECT
            s.*, b.batch_code, t.tank_name
        FROM biofloc_sampling s
        JOIN biofloc_batches b ON b.id = s.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = s.tank_id
        {where_clause}
        ORDER BY s.sample_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    samplings = await fetch_all(samplings_query, *params)

    return {"samplings": samplings, "total": total, "page": page, "limit": limit}


# ============================================================================
# MORTALITY OPERATIONS
# ============================================================================

async def record_mortality(request: MortalityCreate, user_id: UUID) -> Dict:
    """Record mortality event (triggers will update batch)"""
    # Verify batch exists
    batch = await get_batch(request.batch_id)

    # Calculate biomass loss
    biomass_loss = None
    if request.avg_weight_g:
        biomass_loss = (request.count * request.avg_weight_g) / 1000.0

    # Create mortality record (trigger will update batch totals)
    mortality_id = await execute_query(
        """
        INSERT INTO biofloc_mortality (
            batch_id, tank_id, mortality_date, count, cause,
            avg_weight_g, total_biomass_loss_kg, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """,
        request.batch_id,
        request.tank_id,
        request.mortality_date,
        request.count,
        request.cause,
        request.avg_weight_g,
        biomass_loss,
        request.notes,
        user_id
    )

    # Fetch created mortality
    mortality = await fetch_one(
        """
        SELECT
            m.*, b.batch_code, t.tank_name
        FROM biofloc_mortality m
        JOIN biofloc_batches b ON b.id = m.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = m.tank_id
        WHERE m.id = $1
        """,
        mortality_id
    )

    return mortality


async def get_mortalities(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get mortality records with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if batch_id:
        where_conditions.append(f"m.batch_id = ${param_count}")
        params.append(batch_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"m.mortality_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"m.mortality_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_mortality m {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get mortalities
    offset = (page - 1) * limit
    mortalities_query = f"""
        SELECT
            m.*, b.batch_code, t.tank_name
        FROM biofloc_mortality m
        JOIN biofloc_batches b ON b.id = m.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = m.tank_id
        {where_clause}
        ORDER BY m.mortality_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    mortalities = await fetch_all(mortalities_query, *params)

    return {"mortalities": mortalities, "total": total, "page": page, "limit": limit}


# ============================================================================
# WATER TEST OPERATIONS
# ============================================================================

async def record_water_test(request: WaterTestCreate, user_id: UUID) -> Dict:
    """Record water quality test"""
    # Verify tank exists
    tank = await fetch_one("SELECT id, current_batch_id FROM biofloc_tanks WHERE id = $1", request.tank_id)
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    # Create water test record
    test_id = await execute_query(
        """
        INSERT INTO biofloc_water_tests (
            tank_id, batch_id, test_date, test_time,
            temperature_c, ph, dissolved_oxygen_mgl, salinity_ppt,
            ammonia_nh3_mgl, nitrite_no2_mgl, nitrate_no3_mgl,
            alkalinity_mgl, hardness_mgl, turbidity_ntu, tds_mgl,
            floc_volume_mll, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        RETURNING id
        """,
        request.tank_id,
        tank["current_batch_id"],
        request.test_date,
        request.test_time,
        request.temperature_c,
        request.ph,
        request.dissolved_oxygen_mgl,
        request.salinity_ppt,
        request.ammonia_nh3_mgl,
        request.nitrite_no2_mgl,
        request.nitrate_no3_mgl,
        request.alkalinity_mgl,
        request.hardness_mgl,
        request.turbidity_ntu,
        request.tds_mgl,
        request.floc_volume_mll,
        request.notes,
        user_id
    )

    # Fetch created test
    test = await fetch_one(
        """
        SELECT
            w.*, t.tank_name, b.batch_code
        FROM biofloc_water_tests w
        JOIN biofloc_tanks t ON t.id = w.tank_id
        LEFT JOIN biofloc_batches b ON b.id = w.batch_id
        WHERE w.id = $1
        """,
        test_id
    )

    return test


async def get_water_tests(
    tank_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get water test records with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if tank_id:
        where_conditions.append(f"w.tank_id = ${param_count}")
        params.append(tank_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"w.test_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"w.test_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_water_tests w {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get tests
    offset = (page - 1) * limit
    tests_query = f"""
        SELECT
            w.*, t.tank_name, b.batch_code
        FROM biofloc_water_tests w
        JOIN biofloc_tanks t ON t.id = w.tank_id
        LEFT JOIN biofloc_batches b ON b.id = w.batch_id
        {where_clause}
        ORDER BY w.test_date DESC, w.test_time DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    tests = await fetch_all(tests_query, *params)

    return {"water_tests": tests, "total": total, "page": page, "limit": limit}


# ============================================================================
# TANK INPUT OPERATIONS
# ============================================================================

async def record_tank_input(
    request: TankInputCreate,
    user_id: UUID,
    username: str
) -> Dict:
    """Record tank input (chemicals, probiotics, etc.)"""
    # Verify tank exists
    tank = await fetch_one(
        "SELECT id, current_batch_id FROM biofloc_tanks WHERE id = $1",
        request.tank_id
    )
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank not found"
        )

    # If item_sku provided, deduct from inventory and get cost
    unit_cost = None
    total_cost = None
    transaction_id = None

    if request.item_sku:
        inv = InventoryIntegration(module_name="biofloc")
        try:
            result = await inv.deduct_stock(
                item_sku=request.item_sku,
                quantity=request.quantity,
                user_id=str(user_id),
                username=username,
                reference_id=str(request.tank_id),
                notes=f"{request.input_type.value}: {request.reason or 'N/A'}"
            )
            total_cost = result.get("total_cost")
            unit_cost = result.get("weighted_avg_cost")
            # Get first transaction ID
            if result.get("batches_used"):
                transaction_id = result["batches_used"][0].get("batch_id")
        except Exception as e:
            logger.warning(f"Inventory deduction failed for {request.item_sku}: {e}")
            # Continue without inventory deduction

    # Create tank input record
    input_id = await execute_query(
        """
        INSERT INTO biofloc_tank_inputs (
            tank_id, batch_id, input_date, input_time, input_type,
            item_sku, item_name, quantity, unit,
            unit_cost, total_cost, inventory_transaction_id,
            reason, notes, created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        RETURNING id
        """,
        request.tank_id,
        tank["current_batch_id"],
        request.input_date,
        request.input_time,
        request.input_type.value,
        request.item_sku,
        request.item_name,
        request.quantity,
        request.unit,
        unit_cost,
        total_cost,
        transaction_id,
        request.reason,
        request.notes,
        user_id
    )

    # Fetch created input
    tank_input = await fetch_one(
        """
        SELECT
            i.*, t.tank_name, b.batch_code
        FROM biofloc_tank_inputs i
        JOIN biofloc_tanks t ON t.id = i.tank_id
        LEFT JOIN biofloc_batches b ON b.id = i.batch_id
        WHERE i.id = $1
        """,
        input_id
    )

    return tank_input


async def get_tank_inputs(
    tank_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get tank input records with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if tank_id:
        where_conditions.append(f"i.tank_id = ${param_count}")
        params.append(tank_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"i.input_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"i.input_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_tank_inputs i {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get inputs
    offset = (page - 1) * limit
    inputs_query = f"""
        SELECT
            i.*, t.tank_name, b.batch_code
        FROM biofloc_tank_inputs i
        JOIN biofloc_tanks t ON t.id = i.tank_id
        LEFT JOIN biofloc_batches b ON b.id = i.batch_id
        {where_clause}
        ORDER BY i.input_date DESC, i.input_time DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    inputs = await fetch_all(inputs_query, *params)

    return {"tank_inputs": inputs, "total": total, "page": page, "limit": limit}


# ============================================================================
# HARVEST OPERATIONS
# ============================================================================

async def record_harvest(request: HarvestCreate, user_id: UUID) -> Dict:
    """
    Record harvest and finalize batch if complete harvest.
    Calculates all final metrics (FCR, SGR, survival rate, etc.)
    """
    # Get batch
    batch = await get_batch(request.batch_id)

    if batch["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only harvest from active batches"
        )

    # Calculate avg weight
    avg_weight_g = (request.total_weight_kg * 1000) / request.fish_count

    # Calculate revenue
    total_revenue = None
    if request.price_per_kg:
        total_revenue = request.total_weight_kg * request.price_per_kg

    async with DatabaseTransaction() as conn:
        # Create harvest record
        harvest_id = await execute_query_tx(
            """
            INSERT INTO biofloc_harvests (
                batch_id, tank_id, harvest_date, harvest_type,
                fish_count, total_weight_kg, avg_weight_g,
                grade_a_kg, grade_b_kg, grade_c_kg, reject_kg,
                buyer, price_per_kg, total_revenue, notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING id
            """,
            request.batch_id,
            request.tank_id,
            request.harvest_date,
            request.harvest_type.value,
            request.fish_count,
            request.total_weight_kg,
            avg_weight_g,
            request.grade_a_kg,
            request.grade_b_kg,
            request.grade_c_kg,
            request.reject_kg,
            request.buyer,
            request.price_per_kg,
            total_revenue,
            request.notes,
            user_id,
            conn=conn
        )

        # If complete harvest, finalize batch
        if request.harvest_type == HarvestType.COMPLETE:
            # Calculate cycle duration
            cycle_days = (request.harvest_date - batch["stocking_date"]).days

            # Calculate survival rate
            survival_rate = (request.fish_count / batch["initial_count"]) * 100 if batch["initial_count"] > 0 else 0

            # Calculate FCR
            biomass_gain = request.total_weight_kg - batch["initial_total_biomass_kg"]
            fcr = batch["total_feed_kg"] / biomass_gain if biomass_gain > 0 else None

            # Calculate SGR
            sgr = None
            if cycle_days > 0 and avg_weight_g > 0 and batch["initial_avg_weight_g"] > 0:
                import math
                sgr = ((math.log(avg_weight_g) - math.log(batch["initial_avg_weight_g"])) / cycle_days) * 100

            # Update batch with final metrics
            await execute_query_tx(
                """
                UPDATE biofloc_batches
                SET
                    status = 'harvested',
                    end_date = $1,
                    cycle_duration_days = $2,
                    current_count = 0,
                    current_avg_weight_g = $3,
                    current_total_biomass_kg = 0,
                    survival_rate = $4,
                    fcr = $5,
                    sgr = $6,
                    updated_at = NOW()
                WHERE id = $7
                """,
                request.harvest_date,
                cycle_days,
                avg_weight_g,
                survival_rate,
                fcr,
                sgr,
                request.batch_id,
                conn=conn
            )

            # Update cycle costs with revenue
            if total_revenue:
                await execute_query_tx(
                    """
                    UPDATE biofloc_cycle_costs
                    SET total_revenue = total_revenue + $1, updated_at = NOW()
                    WHERE batch_id = $2
                    """,
                    total_revenue,
                    request.batch_id,
                    conn=conn
                )

            # Calculate cost and profit per kg
            costs = await fetch_one_tx(
                "SELECT total_cost, total_revenue FROM biofloc_cycle_costs WHERE batch_id = $1",
                request.batch_id,
                conn=conn
            )

            if costs and request.total_weight_kg > 0:
                cost_per_kg = costs["total_cost"] / request.total_weight_kg
                profit_per_kg = (costs["total_revenue"] - costs["total_cost"]) / request.total_weight_kg

                await execute_query_tx(
                    """
                    UPDATE biofloc_cycle_costs
                    SET cost_per_kg = $1, profit_per_kg = $2, updated_at = NOW()
                    WHERE batch_id = $3
                    """,
                    cost_per_kg,
                    profit_per_kg,
                    request.batch_id,
                    conn=conn
                )

            # End tank assignment and set tank to available
            if request.tank_id:
                await execute_query_tx(
                    """
                    UPDATE biofloc_batch_tank_assignments
                    SET end_date = $1
                    WHERE batch_id = $2 AND tank_id = $3 AND end_date IS NULL
                    """,
                    request.harvest_date,
                    request.batch_id,
                    request.tank_id,
                    conn=conn
                )

                await execute_query_tx(
                    """
                    UPDATE biofloc_tanks
                    SET current_batch_id = NULL, status = 'available', updated_at = NOW()
                    WHERE id = $1
                    """,
                    request.tank_id,
                    conn=conn
                )

        else:
            # Partial harvest - update current count
            new_count = batch["current_count"] - request.fish_count
            await execute_query_tx(
                """
                UPDATE biofloc_batches
                SET
                    current_count = $1,
                    current_total_biomass_kg = (current_count * current_avg_weight_g) / 1000.0,
                    updated_at = NOW()
                WHERE id = $2
                """,
                new_count,
                request.batch_id,
                conn=conn
            )

            # Update cycle costs with partial revenue
            if total_revenue:
                await execute_query_tx(
                    """
                    UPDATE biofloc_cycle_costs
                    SET total_revenue = total_revenue + $1, updated_at = NOW()
                    WHERE batch_id = $2
                    """,
                    total_revenue,
                    request.batch_id,
                    conn=conn
                )

    # Fetch created harvest
    harvest = await fetch_one(
        """
        SELECT
            h.*, b.batch_code, t.tank_name
        FROM biofloc_harvests h
        JOIN biofloc_batches b ON b.id = h.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = h.tank_id
        WHERE h.id = $1
        """,
        harvest_id
    )

    return harvest


async def get_harvests(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 100
) -> Dict:
    """Get harvest records with filters"""
    where_conditions = []
    params = []
    param_count = 1

    if batch_id:
        where_conditions.append(f"h.batch_id = ${param_count}")
        params.append(batch_id)
        param_count += 1

    if start_date:
        where_conditions.append(f"h.harvest_date >= ${param_count}")
        params.append(start_date)
        param_count += 1

    if end_date:
        where_conditions.append(f"h.harvest_date <= ${param_count}")
        params.append(end_date)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Count
    count_query = f"SELECT COUNT(*) as total FROM biofloc_harvests h {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get harvests
    offset = (page - 1) * limit
    harvests_query = f"""
        SELECT
            h.*, b.batch_code, t.tank_name
        FROM biofloc_harvests h
        JOIN biofloc_batches b ON b.id = h.batch_id
        LEFT JOIN biofloc_tanks t ON t.id = h.tank_id
        {where_clause}
        ORDER BY h.harvest_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    harvests = await fetch_all(harvests_query, *params)

    return {"harvests": harvests, "total": total, "page": page, "limit": limit}


# ============================================================================
# DASHBOARD & REPORTING
# ============================================================================

async def get_dashboard_stats() -> Dict:
    """Get biofloc dashboard statistics"""
    # Tank stats
    tank_stats = await fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'in_use') as active_tanks,
            COUNT(*) FILTER (WHERE status = 'available') as available_tanks,
            COUNT(*) FILTER (WHERE status = 'maintenance') as maintenance_tanks,
            COUNT(*) as total_tanks
        FROM biofloc_tanks
        WHERE is_active = TRUE
        """
    )

    # Batch stats
    batch_stats = await fetch_one(
        """
        SELECT
            COUNT(*) as active_batches,
            COALESCE(SUM(current_count), 0) as total_fish_count,
            COALESCE(SUM(current_total_biomass_kg), 0) as total_biomass_kg
        FROM biofloc_batches
        WHERE status = 'active'
        """
    )

    # Tank utilization - safe calculation
    total_tanks = tank_stats.get("total_tanks", 0) if tank_stats else 0
    active_tanks = tank_stats.get("active_tanks", 0) if tank_stats else 0
    utilization = (active_tanks / total_tanks * 100) if total_tanks > 0 else 0

    # Water quality alerts (last 3 days)
    water_alerts = await fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE dissolved_oxygen_mgl < 4.0) as low_do_alerts,
            COUNT(*) FILTER (WHERE ammonia_nh3_mgl > 1.0) as high_ammonia_alerts
        FROM biofloc_water_tests
        WHERE test_date >= CURRENT_DATE - INTERVAL '3 days'
        """
    )

    # Recent mortalities (last 7 days)
    mortality_stats = await fetch_one(
        """
        SELECT COALESCE(SUM(count), 0) as recent_mortalities_7d
        FROM biofloc_mortality
        WHERE mortality_date >= CURRENT_DATE - INTERVAL '7 days'
        """
    )

    # Upcoming harvests (batches older than 90 days)
    upcoming = await fetch_one(
        """
        SELECT COUNT(*) as upcoming_harvests
        FROM biofloc_batches
        WHERE status = 'active'
        AND CURRENT_DATE - stocking_date >= 90
        """
    )

    return {
        "active_tanks": tank_stats.get("active_tanks", 0) if tank_stats else 0,
        "available_tanks": tank_stats.get("available_tanks", 0) if tank_stats else 0,
        "maintenance_tanks": tank_stats.get("maintenance_tanks", 0) if tank_stats else 0,
        "active_batches": batch_stats.get("active_batches", 0) if batch_stats else 0,
        "total_fish_count": int(batch_stats.get("total_fish_count", 0)) if batch_stats else 0,
        "total_biomass_kg": float(batch_stats.get("total_biomass_kg", 0)) if batch_stats else 0.0,
        "avg_tank_utilization": round(utilization, 2),
        "low_do_alerts": water_alerts.get("low_do_alerts", 0) if water_alerts else 0,
        "high_ammonia_alerts": water_alerts.get("high_ammonia_alerts", 0) if water_alerts else 0,
        "recent_mortalities_7d": int(mortality_stats.get("recent_mortalities_7d", 0)) if mortality_stats else 0,
        "upcoming_harvests": upcoming.get("upcoming_harvests", 0) if upcoming else 0
    }


async def get_batch_performance_report(batch_id: UUID) -> Dict:
    """Get comprehensive performance report for a batch"""
    # Get batch
    batch = await get_batch(batch_id)

    if not batch.get("cycle_duration_days"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch must be completed to generate performance report"
        )

    # Get cycle costs
    costs = await fetch_one(
        "SELECT * FROM biofloc_cycle_costs WHERE batch_id = $1",
        batch_id
    )

    if not costs:
        costs = {
            "total_cost": 0,
            "total_revenue": 0,
            "gross_profit": 0,
            "cost_per_kg": 0,
            "profit_per_kg": 0
        }

    # Get harvests
    harvests = await fetch_all(
        "SELECT * FROM biofloc_harvests WHERE batch_id = $1 ORDER BY harvest_date",
        batch_id
    )

    # Calculate total harvested
    total_harvested_kg = sum(h["total_weight_kg"] for h in harvests)
    final_count = sum(h["fish_count"] for h in harvests)

    # Calculate metrics
    biomass_gain = total_harvested_kg - batch["initial_total_biomass_kg"]
    avg_daily_gain = (biomass_gain * 1000) / batch["cycle_duration_days"] if batch["cycle_duration_days"] > 0 else 0
    roi_percentage = (costs["gross_profit"] / costs["total_cost"] * 100) if costs["total_cost"] > 0 else 0

    return {
        "batch_id": batch["id"],
        "batch_code": batch["batch_code"],
        "species": batch["species"],
        "cycle_duration_days": batch["cycle_duration_days"],
        "initial_count": batch["initial_count"],
        "final_count": final_count,
        "survival_rate": batch["survival_rate"] or 0,
        "initial_biomass_kg": float(batch["initial_total_biomass_kg"]),
        "final_biomass_kg": float(total_harvested_kg),
        "biomass_gain_kg": float(biomass_gain),
        "avg_daily_gain_g": float(avg_daily_gain),
        "total_feed_kg": float(batch["total_feed_kg"]),
        "fcr": float(batch["fcr"]) if batch["fcr"] else 0,
        "sgr": float(batch["sgr"]) if batch["sgr"] else 0,
        "total_cost": float(costs["total_cost"]),
        "total_revenue": float(costs["total_revenue"]),
        "gross_profit": float(costs["gross_profit"]),
        "cost_per_kg": float(costs.get("cost_per_kg") or 0),
        "profit_per_kg": float(costs.get("profit_per_kg") or 0),
        "roi_percentage": float(roi_percentage)
    }
