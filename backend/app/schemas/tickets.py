"""
================================================================================
Farm Management System - Ticket System Schemas
================================================================================
Version: 1.0.1
Last Updated: 2025-11-20

Changelog:
----------
v1.0.1 (2025-11-20):
  - No schema changes - version bump to match service layer fix

v1.0.0 (2025-11-20):
  - Initial ticket system schemas
  - Ticket type, status, and priority enums
  - Request/response models for tickets and comments
  - Pagination support for ticket lists
  - Statistics response models

Description:
  Pydantic models for ticket request/response validation and serialization.
  Includes enums, request schemas, response schemas, and nested models for
  comments and user information.

================================================================================
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List
import math


# Enums
class TicketType(str, Enum):
    ISSUE = "issue"
    FEATURE_REQUEST = "feature_request"
    UPGRADE = "upgrade"
    OTHERS = "others"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Request Schemas
class CreateTicketRequest(BaseModel):
    """Request to create a new ticket"""
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Detailed description of the issue/request")
    ticket_type: TicketType = Field(..., description="Type of ticket")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Login page not loading",
                "description": "When I try to access the login page, it shows a blank screen on mobile devices.",
                "ticket_type": "issue"
            }
        }


class UpdateTicketRequest(BaseModel):
    """Request to update an existing ticket (for users)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    ticket_type: Optional[TicketType] = None


class AdminUpdateTicketRequest(BaseModel):
    """Request to update ticket by admin (includes priority and status)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    ticket_type: Optional[TicketType] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None


class CloseTicketRequest(BaseModel):
    """Request to close a ticket (admin only)"""
    comment: Optional[str] = Field(None, description="Optional closing comment")


class CreateCommentRequest(BaseModel):
    """Request to add a comment to a ticket"""
    comment: str = Field(..., min_length=1, description="Comment text")

    class Config:
        json_schema_extra = {
            "example": {
                "comment": "We are looking into this issue. Will update you soon."
            }
        }


class UpdateCommentRequest(BaseModel):
    """Request to update a comment"""
    comment: str = Field(..., min_length=1, description="Updated comment text")


# Response Schemas
class UserInfo(BaseModel):
    """Basic user information for ticket responses"""
    id: str
    full_name: str
    email: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Response model for a single comment"""
    id: int
    ticket_id: int
    user_id: str
    user_name: str
    user_email: str
    comment: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    """Response model for a single ticket"""
    id: int
    title: str
    description: str
    ticket_type: TicketType
    status: TicketStatus
    priority: Optional[TicketPriority] = None
    created_by_id: str
    created_by_name: str
    created_by_email: str
    closed_by_id: Optional[str] = None
    closed_by_name: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    comment_count: int = 0

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    """Response model for ticket with comments"""
    id: int
    title: str
    description: str
    ticket_type: TicketType
    status: TicketStatus
    priority: Optional[TicketPriority] = None
    created_by_id: str
    created_by_name: str
    created_by_email: str
    closed_by_id: Optional[str] = None
    closed_by_name: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True


class TicketsListResponse(BaseModel):
    """Paginated list of tickets"""
    tickets: List[TicketResponse]
    total: int
    page: int
    limit: int
    total_pages: int = Field(default=0)

    def __init__(self, **data):
        super().__init__(**data)
        if self.limit > 0:
            self.total_pages = math.ceil(self.total / self.limit)


class CommentsListResponse(BaseModel):
    """List of comments for a ticket"""
    comments: List[CommentResponse]
    total: int


class TicketStatsResponse(BaseModel):
    """Statistics for tickets"""
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    by_type: dict
    by_priority: dict
