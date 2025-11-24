"""
================================================================================
Farm Management System - Ticket Routes
================================================================================
Version: 1.2.0
Last Updated: 2025-11-22

Changelog:
----------
v1.2.0 (2025-11-22):
  - Integrated WebSocket real-time notifications for ticket events
  - Emit ticket.created event when new tickets are created
  - Emit ticket.updated event when tickets are updated or closed
  - Real-time broadcasting to all connected clients
  - Added webhook event triggers for ticket lifecycle events
  - Trigger ticket.created, ticket.updated, ticket.closed webhook events

v1.1.0 (2025-11-20):
  - Added DELETE /tickets/{ticket_id} endpoint for ticket deletion
  - Users can delete their own tickets
  - Admins can delete any ticket
  - Cascade deletion of associated comments

v1.0.1 (2025-11-20):
  - No changes to routes - version bump to match service layer fix

v1.0.0 (2025-11-20):
  - Initial ticket system routes implementation
  - Ticket CRUD operations with filtering and pagination
  - Admin-specific endpoints for priority and status management
  - Comment system for ticket discussions
  - Ticket statistics endpoint

Description:
  API endpoints for ticket system - allows users to raise issues, feature
  requests, and upgrade suggestions. Admins can manage priorities and close tickets.

Endpoints:
  GET    /tickets         - List all tickets (filtered, paginated)
  GET    /tickets/my      - List current user's tickets
  GET    /tickets/stats   - Get ticket statistics
  GET    /tickets/{id}    - Get single ticket with comments
  POST   /tickets         - Create new ticket
  PUT    /tickets/{id}    - Update ticket (user - own tickets only)
  PUT    /tickets/{id}/admin - Admin update (priority, status)
  POST   /tickets/{id}/close - Close ticket (admin only)
  DELETE /tickets/{id}    - Delete ticket (owner or admin)

  POST   /tickets/{id}/comments        - Add comment
  PUT    /tickets/comments/{id}        - Update comment
  DELETE /tickets/comments/{id}        - Delete comment

================================================================================
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.schemas.tickets import (
    TicketType, TicketStatus, TicketPriority,
    CreateTicketRequest, UpdateTicketRequest, AdminUpdateTicketRequest,
    CloseTicketRequest, CreateCommentRequest, UpdateCommentRequest,
    TicketResponse, TicketDetailResponse, TicketsListResponse,
    CommentResponse, TicketStatsResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import tickets_service, webhook_service
from app.database import get_db
from app.websocket import events as ws_events

router = APIRouter()


# ============================================================================
# TICKET ENDPOINTS
# ============================================================================


@router.get("", response_model=TicketsListResponse)
async def list_tickets(
    ticket_type: Optional[TicketType] = Query(None, description="Filter by ticket type"),
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    priority: Optional[TicketPriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List all tickets with optional filters.
    All authenticated users can view all tickets.
    """
    return await tickets_service.get_tickets_list(
        ticket_type=ticket_type,
        ticket_status=status,
        priority=priority,
        page=page,
        limit=limit,
    )


@router.get("/my", response_model=TicketsListResponse)
async def list_my_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List tickets created by the current user.
    """
    return await tickets_service.get_my_tickets(
        user_id=current_user.id,
        ticket_status=status,
        page=page,
        limit=limit,
    )


@router.get("/stats", response_model=TicketStatsResponse)
async def get_ticket_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get ticket statistics overview.
    """
    return await tickets_service.get_ticket_stats()


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get a single ticket with all its comments.
    """
    return await tickets_service.get_ticket_by_id(ticket_id)


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: CreateTicketRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new ticket.
    Any authenticated user can create tickets.
    Priority is not set at creation - only admins can assign priority later.
    """
    ticket = await tickets_service.create_ticket(request, current_user.id)

    # Emit WebSocket event
    await ws_events.emit_ticket_created({
        "id": ticket.get('id'),
        "title": ticket.get('title'),
        "priority": ticket.get('priority'),
        "status": ticket.get('status'),
        "type": ticket.get('type')
    })

    # Trigger webhook event
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            await webhook_service.trigger_event(
                conn,
                'ticket.created',
                {
                    "id": ticket.get('id'),
                    "title": ticket.get('title'),
                    "ticket_type": ticket.get('ticket_type'),
                    "priority": ticket.get('priority'),
                    "status": ticket.get('status'),
                    "created_by": current_user.email,
                }
            )
    except Exception as e:
        # Don't fail ticket creation if webhook fails
        logger.error(f"Failed to trigger webhook for ticket creation: {e}")

    return ticket


@router.put("/{ticket_id}", response_model=TicketDetailResponse)
async def update_ticket(
    ticket_id: int,
    request: UpdateTicketRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a ticket.
    Users can only update their own tickets (title, description, type).
    Cannot update closed tickets.
    """
    is_admin = current_user.role.lower() == "admin"
    ticket = await tickets_service.update_ticket(
        ticket_id,
        request,
        current_user.id,
        is_admin=is_admin
    )

    # Emit WebSocket event
    await ws_events.emit_ticket_updated({
        "id": ticket.get('id'),
        "title": ticket.get('title'),
        "priority": ticket.get('priority'),
        "status": ticket.get('status'),
        "type": ticket.get('type')
    })

    # Trigger webhook event
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            await webhook_service.trigger_event(
                conn,
                'ticket.updated',
                {
                    "id": ticket.get('id'),
                    "title": ticket.get('title'),
                    "ticket_type": ticket.get('ticket_type'),
                    "priority": ticket.get('priority'),
                    "status": ticket.get('status'),
                    "updated_by": current_user.email,
                }
            )
    except Exception as e:
        # Don't fail ticket update if webhook fails
        logger.error(f"Failed to trigger webhook for ticket update: {e}")

    return ticket


@router.put("/{ticket_id}/admin", response_model=TicketDetailResponse)
async def admin_update_ticket(
    ticket_id: int,
    request: AdminUpdateTicketRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """
    Admin update for ticket.
    Admins can update any field including status and priority.
    """
    ticket = await tickets_service.admin_update_ticket(
        ticket_id,
        request,
        admin.id
    )

    # Emit WebSocket event
    await ws_events.emit_ticket_updated({
        "id": ticket.get('id'),
        "title": ticket.get('title'),
        "priority": ticket.get('priority'),
        "status": ticket.get('status'),
        "type": ticket.get('type')
    })

    # Trigger webhook event
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            await webhook_service.trigger_event(
                conn,
                'ticket.updated',
                {
                    "id": ticket.get('id'),
                    "title": ticket.get('title'),
                    "ticket_type": ticket.get('ticket_type'),
                    "priority": ticket.get('priority'),
                    "status": ticket.get('status'),
                    "updated_by": admin.email,
                }
            )
    except Exception as e:
        # Don't fail ticket update if webhook fails
        logger.error(f"Failed to trigger webhook for admin ticket update: {e}")

    return ticket


@router.post("/{ticket_id}/close", response_model=TicketDetailResponse)
async def close_ticket(
    ticket_id: int,
    request: Optional[CloseTicketRequest] = None,
    admin: CurrentUser = Depends(require_admin)
):
    """
    Close a ticket.
    Only admins can close tickets.
    Optionally include a closing comment.
    """
    comment = request.comment if request else None
    ticket = await tickets_service.close_ticket(
        ticket_id,
        admin.id,
        comment=comment
    )

    # Emit WebSocket event
    await ws_events.emit_ticket_updated({
        "id": ticket.get('id'),
        "title": ticket.get('title'),
        "priority": ticket.get('priority'),
        "status": ticket.get('status'),
        "type": ticket.get('type')
    })

    # Trigger webhook event
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            await webhook_service.trigger_event(
                conn,
                'ticket.closed',
                {
                    "id": ticket.get('id'),
                    "title": ticket.get('title'),
                    "ticket_type": ticket.get('ticket_type'),
                    "priority": ticket.get('priority'),
                    "closed_by": admin.email,
                }
            )
    except Exception as e:
        # Don't fail ticket close if webhook fails
        logger.error(f"Failed to trigger webhook for ticket close: {e}")

    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Delete a ticket.
    Users can only delete their own tickets.
    Admins can delete any ticket.
    """
    is_admin = current_user.role.lower() == "admin"
    return await tickets_service.delete_ticket(
        ticket_id,
        current_user.id,
        is_admin=is_admin
    )


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: int,
    request: CreateCommentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Add a comment to a ticket.
    Both users and admins can add comments.
    Cannot add comments to closed tickets.
    """
    return await tickets_service.add_comment(
        ticket_id,
        request,
        current_user.id
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    request: UpdateCommentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update a comment.
    Users can only update their own comments.
    Admins can update any comment.
    """
    is_admin = current_user.role.lower() == "admin"
    return await tickets_service.update_comment(
        comment_id,
        request,
        current_user.id,
        is_admin=is_admin
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Delete a comment.
    Users can only delete their own comments.
    Admins can delete any comment.
    """
    is_admin = current_user.role.lower() == "admin"
    return await tickets_service.delete_comment(
        comment_id,
        current_user.id,
        is_admin=is_admin
    )
