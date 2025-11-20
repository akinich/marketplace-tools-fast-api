"""
================================================================================
Farm Management System - Ticket Service Layer
================================================================================
Version: 1.0.1
Last Updated: 2025-11-20

Changelog:
----------
v1.0.1 (2025-11-20):
  - CRITICAL FIX: Resolved SQL query error causing 500 errors on ticket fetch
  - Added JOIN with auth.users table to properly retrieve user email addresses
  - Fixed get_tickets_list() - added LEFT JOIN for auth.users on created_by and closed_by
  - Fixed get_ticket_by_id() - added LEFT JOIN for auth.users on created_by and closed_by
  - Fixed add_comment() - added LEFT JOIN for auth.users to get commenter email
  - Fixed update_comment() - added LEFT JOIN for auth.users to get commenter email
  - Changed all email field selections from up.email to au.email
  - Resolves: "column up_created.email does not exist" database error

v1.0.0 (2025-11-20):
  - Initial ticket service implementation
  - Ticket CRUD operations with filtering and pagination
  - Admin-specific operations (set priority, change status, close tickets)
  - Comment system with CRUD operations
  - Ticket statistics aggregation
  - Transaction support for ticket closing with comments

Description:
  Service layer for ticket system - handles issues, feature requests, and
  upgrade suggestions from users. Admins can manage priorities and close tickets.

Features:
  - Create, read, update tickets
  - Admin-only: set priority, change status, close tickets
  - Comments system for both users and admins
  - Ticket statistics and filtering

================================================================================
"""

from typing import Optional, List, Dict
from fastapi import HTTPException, status
from datetime import datetime
from uuid import UUID
import logging

from app.database import (
    fetch_one, fetch_all, execute_query, DatabaseTransaction,
    fetch_one_tx, execute_query_tx
)
from app.schemas.tickets import (
    TicketType, TicketStatus, TicketPriority,
    CreateTicketRequest, UpdateTicketRequest, AdminUpdateTicketRequest,
    CreateCommentRequest, UpdateCommentRequest
)

logger = logging.getLogger(__name__)


# ============================================================================
# TICKET OPERATIONS
# ============================================================================


async def get_tickets_list(
    ticket_type: Optional[TicketType] = None,
    ticket_status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    created_by_id: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """
    Get paginated list of tickets with optional filters.
    All users can see all tickets.
    """
    # Build WHERE clause
    where_conditions = []
    params = []
    param_count = 1

    if ticket_type:
        where_conditions.append(f"t.ticket_type = ${param_count}")
        params.append(ticket_type.value)
        param_count += 1

    if ticket_status:
        where_conditions.append(f"t.status = ${param_count}")
        params.append(ticket_status.value)
        param_count += 1

    if priority:
        where_conditions.append(f"t.priority = ${param_count}")
        params.append(priority.value)
        param_count += 1

    if created_by_id:
        where_conditions.append(f"t.created_by_id = ${param_count}")
        params.append(UUID(created_by_id))
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM tickets t {where_clause}"
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get paginated results with user info and comment count
    offset = (page - 1) * limit
    tickets_query = f"""
        SELECT
            t.id,
            t.title,
            t.description,
            t.ticket_type,
            t.status,
            t.priority,
            t.created_by_id::text,
            up_created.full_name as created_by_name,
            au_created.email as created_by_email,
            t.closed_by_id::text,
            up_closed.full_name as closed_by_name,
            t.closed_at,
            t.created_at,
            t.updated_at,
            COALESCE(
                (SELECT COUNT(*) FROM ticket_comments tc WHERE tc.ticket_id = t.id),
                0
            ) as comment_count
        FROM tickets t
        LEFT JOIN user_profiles up_created ON t.created_by_id = up_created.id
        LEFT JOIN auth.users au_created ON au_created.id = up_created.id
        LEFT JOIN user_profiles up_closed ON t.closed_by_id = up_closed.id
        LEFT JOIN auth.users au_closed ON au_closed.id = up_closed.id
        {where_clause}
        ORDER BY t.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """

    tickets = await fetch_all(tickets_query, *params, limit, offset)

    return {
        "tickets": tickets,
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_ticket_by_id(ticket_id: int) -> Dict:
    """
    Get a single ticket with all its comments.
    """
    # Get ticket with user info
    ticket_query = """
        SELECT
            t.id,
            t.title,
            t.description,
            t.ticket_type,
            t.status,
            t.priority,
            t.created_by_id::text,
            up_created.full_name as created_by_name,
            au_created.email as created_by_email,
            t.closed_by_id::text,
            up_closed.full_name as closed_by_name,
            t.closed_at,
            t.created_at,
            t.updated_at
        FROM tickets t
        LEFT JOIN user_profiles up_created ON t.created_by_id = up_created.id
        LEFT JOIN auth.users au_created ON au_created.id = up_created.id
        LEFT JOIN user_profiles up_closed ON t.closed_by_id = up_closed.id
        LEFT JOIN auth.users au_closed ON au_closed.id = up_closed.id
        WHERE t.id = $1
    """

    ticket = await fetch_one(ticket_query, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found"
        )

    # Get comments for this ticket
    comments_query = """
        SELECT
            tc.id,
            tc.ticket_id,
            tc.user_id::text,
            up.full_name as user_name,
            au.email as user_email,
            tc.comment,
            tc.created_at,
            tc.updated_at
        FROM ticket_comments tc
        LEFT JOIN user_profiles up ON tc.user_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE tc.ticket_id = $1
        ORDER BY tc.created_at ASC
    """

    comments = await fetch_all(comments_query, ticket_id)

    ticket["comments"] = comments

    return ticket


async def create_ticket(request: CreateTicketRequest, user_id: str) -> Dict:
    """
    Create a new ticket. Any user can create tickets.
    Priority is not set at creation - only admins can set it later.
    """
    insert_query = """
        INSERT INTO tickets (
            title,
            description,
            ticket_type,
            status,
            created_by_id
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
    """

    ticket_id = await execute_query(
        insert_query,
        request.title,
        request.description,
        request.ticket_type.value,
        TicketStatus.OPEN.value,
        UUID(user_id)
    )

    logger.info(f"Ticket {ticket_id} created by user {user_id}")

    # Return the created ticket
    return await get_ticket_by_id(ticket_id)


async def update_ticket(
    ticket_id: int,
    request: UpdateTicketRequest,
    user_id: str,
    is_admin: bool = False
) -> Dict:
    """
    Update a ticket. Users can only update their own tickets.
    Only title, description, and ticket_type can be updated by users.
    """
    # Check if ticket exists
    ticket = await fetch_one(
        "SELECT id, created_by_id::text, status FROM tickets WHERE id = $1",
        ticket_id
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found"
        )

    # Check ownership (unless admin)
    if not is_admin and ticket["created_by_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tickets"
        )

    # Check if ticket is closed
    if ticket["status"] == TicketStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a closed ticket"
        )

    # Build update query dynamically
    update_fields = []
    params = []
    param_count = 1

    if request.title is not None:
        update_fields.append(f"title = ${param_count}")
        params.append(request.title)
        param_count += 1

    if request.description is not None:
        update_fields.append(f"description = ${param_count}")
        params.append(request.description)
        param_count += 1

    if request.ticket_type is not None:
        update_fields.append(f"ticket_type = ${param_count}")
        params.append(request.ticket_type.value)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Add ticket_id as last parameter
    params.append(ticket_id)

    update_query = f"""
        UPDATE tickets
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """

    await execute_query(update_query, *params)

    logger.info(f"Ticket {ticket_id} updated by user {user_id}")

    return await get_ticket_by_id(ticket_id)


async def admin_update_ticket(
    ticket_id: int,
    request: AdminUpdateTicketRequest,
    admin_id: str
) -> Dict:
    """
    Admin update for ticket - can change status and priority.
    """
    # Check if ticket exists
    ticket = await fetch_one(
        "SELECT id, status FROM tickets WHERE id = $1",
        ticket_id
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found"
        )

    # Build update query dynamically
    update_fields = []
    params = []
    param_count = 1

    if request.title is not None:
        update_fields.append(f"title = ${param_count}")
        params.append(request.title)
        param_count += 1

    if request.description is not None:
        update_fields.append(f"description = ${param_count}")
        params.append(request.description)
        param_count += 1

    if request.ticket_type is not None:
        update_fields.append(f"ticket_type = ${param_count}")
        params.append(request.ticket_type.value)
        param_count += 1

    if request.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(request.status.value)
        param_count += 1

        # If closing, set closed_by and closed_at
        if request.status == TicketStatus.CLOSED:
            update_fields.append(f"closed_by_id = ${param_count}")
            params.append(UUID(admin_id))
            param_count += 1
            update_fields.append(f"closed_at = ${param_count}")
            params.append(datetime.utcnow())
            param_count += 1

    if request.priority is not None:
        update_fields.append(f"priority = ${param_count}")
        params.append(request.priority.value)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Add ticket_id as last parameter
    params.append(ticket_id)

    update_query = f"""
        UPDATE tickets
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """

    await execute_query(update_query, *params)

    logger.info(f"Ticket {ticket_id} admin-updated by {admin_id}")

    return await get_ticket_by_id(ticket_id)


async def close_ticket(
    ticket_id: int,
    admin_id: str,
    comment: Optional[str] = None
) -> Dict:
    """
    Close a ticket. Only admins can close tickets.
    Optionally add a closing comment.
    """
    # Check if ticket exists
    ticket = await fetch_one(
        "SELECT id, status FROM tickets WHERE id = $1",
        ticket_id
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found"
        )

    if ticket["status"] == TicketStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket is already closed"
        )

    async with DatabaseTransaction() as conn:
        # Close the ticket
        await execute_query_tx(
            """
            UPDATE tickets
            SET status = $1, closed_by_id = $2, closed_at = $3
            WHERE id = $4
            """,
            TicketStatus.CLOSED.value,
            UUID(admin_id),
            datetime.utcnow(),
            ticket_id,
            conn=conn
        )

        # Add closing comment if provided
        if comment:
            await execute_query_tx(
                """
                INSERT INTO ticket_comments (ticket_id, user_id, comment)
                VALUES ($1, $2, $3)
                """,
                ticket_id,
                UUID(admin_id),
                f"[Closing comment] {comment}",
                conn=conn
            )

    logger.info(f"Ticket {ticket_id} closed by admin {admin_id}")

    return await get_ticket_by_id(ticket_id)


# ============================================================================
# COMMENT OPERATIONS
# ============================================================================


async def add_comment(
    ticket_id: int,
    request: CreateCommentRequest,
    user_id: str
) -> Dict:
    """
    Add a comment to a ticket. Both users and admins can comment.
    """
    # Check if ticket exists
    ticket = await fetch_one(
        "SELECT id, status FROM tickets WHERE id = $1",
        ticket_id
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id {ticket_id} not found"
        )

    if ticket["status"] == TicketStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add comments to a closed ticket"
        )

    # Insert comment
    comment_id = await execute_query(
        """
        INSERT INTO ticket_comments (ticket_id, user_id, comment)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        ticket_id,
        UUID(user_id),
        request.comment
    )

    logger.info(f"Comment {comment_id} added to ticket {ticket_id} by user {user_id}")

    # Return the created comment
    comment = await fetch_one(
        """
        SELECT
            tc.id,
            tc.ticket_id,
            tc.user_id::text,
            up.full_name as user_name,
            au.email as user_email,
            tc.comment,
            tc.created_at,
            tc.updated_at
        FROM ticket_comments tc
        LEFT JOIN user_profiles up ON tc.user_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE tc.id = $1
        """,
        comment_id
    )

    return comment


async def update_comment(
    comment_id: int,
    request: UpdateCommentRequest,
    user_id: str,
    is_admin: bool = False
) -> Dict:
    """
    Update a comment. Users can only update their own comments.
    """
    # Check if comment exists
    comment = await fetch_one(
        """
        SELECT tc.id, tc.user_id::text, tc.ticket_id, t.status
        FROM ticket_comments tc
        JOIN tickets t ON tc.ticket_id = t.id
        WHERE tc.id = $1
        """,
        comment_id
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found"
        )

    # Check ownership (unless admin)
    if not is_admin and comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own comments"
        )

    if comment["status"] == TicketStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update comments on a closed ticket"
        )

    # Update comment
    await execute_query(
        "UPDATE ticket_comments SET comment = $1 WHERE id = $2",
        request.comment,
        comment_id
    )

    logger.info(f"Comment {comment_id} updated by user {user_id}")

    # Return updated comment
    updated_comment = await fetch_one(
        """
        SELECT
            tc.id,
            tc.ticket_id,
            tc.user_id::text,
            up.full_name as user_name,
            au.email as user_email,
            tc.comment,
            tc.created_at,
            tc.updated_at
        FROM ticket_comments tc
        LEFT JOIN user_profiles up ON tc.user_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE tc.id = $1
        """,
        comment_id
    )

    return updated_comment


async def delete_comment(
    comment_id: int,
    user_id: str,
    is_admin: bool = False
) -> Dict:
    """
    Delete a comment. Users can only delete their own comments.
    Admins can delete any comment.
    """
    # Check if comment exists
    comment = await fetch_one(
        """
        SELECT tc.id, tc.user_id::text, tc.ticket_id, t.status
        FROM ticket_comments tc
        JOIN tickets t ON tc.ticket_id = t.id
        WHERE tc.id = $1
        """,
        comment_id
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found"
        )

    # Check ownership (unless admin)
    if not is_admin and comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    if comment["status"] == TicketStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete comments from a closed ticket"
        )

    # Delete comment
    await execute_query(
        "DELETE FROM ticket_comments WHERE id = $1",
        comment_id
    )

    logger.info(f"Comment {comment_id} deleted by user {user_id}")

    return {"message": "Comment deleted successfully"}


# ============================================================================
# STATISTICS
# ============================================================================


async def get_ticket_stats() -> Dict:
    """
    Get ticket statistics for dashboard/overview.
    """
    # Get counts by status
    status_query = """
        SELECT
            COUNT(*) as total_tickets,
            COUNT(*) FILTER (WHERE status = 'open') as open_tickets,
            COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tickets,
            COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
            COUNT(*) FILTER (WHERE status = 'closed') as closed_tickets
        FROM tickets
    """
    status_stats = await fetch_one(status_query)

    # Get counts by type
    type_query = """
        SELECT ticket_type, COUNT(*) as count
        FROM tickets
        GROUP BY ticket_type
    """
    type_results = await fetch_all(type_query)
    by_type = {row["ticket_type"]: row["count"] for row in type_results}

    # Get counts by priority
    priority_query = """
        SELECT
            COALESCE(priority, 'unassigned') as priority,
            COUNT(*) as count
        FROM tickets
        GROUP BY priority
    """
    priority_results = await fetch_all(priority_query)
    by_priority = {row["priority"]: row["count"] for row in priority_results}

    return {
        "total_tickets": status_stats["total_tickets"],
        "open_tickets": status_stats["open_tickets"],
        "in_progress_tickets": status_stats["in_progress_tickets"],
        "resolved_tickets": status_stats["resolved_tickets"],
        "closed_tickets": status_stats["closed_tickets"],
        "by_type": by_type,
        "by_priority": by_priority,
    }


async def get_my_tickets(
    user_id: str,
    ticket_status: Optional[TicketStatus] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """
    Get tickets created by the current user.
    """
    return await get_tickets_list(
        ticket_status=ticket_status,
        created_by_id=user_id,
        page=page,
        limit=limit,
    )
