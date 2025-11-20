"""
Development Planning Schemas
Pydantic models for feature planning request/response validation
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, date
from typing import Optional, List
import math


# Enums
class FeatureStatus(str, Enum):
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class FeaturePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


# Request Schemas
class CreateFeatureRequest(BaseModel):
    """Request to create a new feature"""
    title: str = Field(..., min_length=1, max_length=200, description="Feature title")
    description: Optional[str] = Field(None, description="Detailed description")
    priority: FeaturePriority = Field(FeaturePriority.MEDIUM, description="Priority level")
    target_date: Optional[date] = Field(None, description="Target completion date")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "User Authentication System",
                "description": "Implement OAuth2 authentication with social login support",
                "priority": "high",
                "target_date": "2025-12-31"
            }
        }


class UpdateFeatureRequest(BaseModel):
    """Request to update a feature"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[FeatureStatus] = None
    priority: Optional[FeaturePriority] = None
    target_date: Optional[date] = None


class CreateStepRequest(BaseModel):
    """Request to create a new step"""
    title: str = Field(..., min_length=1, max_length=200, description="Step title")
    description: Optional[str] = Field(None, description="Step details")
    step_order: Optional[int] = Field(None, description="Order in the list")


class UpdateStepRequest(BaseModel):
    """Request to update a step"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[StepStatus] = None
    step_order: Optional[int] = None


class ReorderStepsRequest(BaseModel):
    """Request to reorder steps"""
    step_ids: List[int] = Field(..., description="Step IDs in desired order")


class CreateCommentRequest(BaseModel):
    """Request to add a comment"""
    comment: str = Field(..., min_length=1, description="Comment text")


# Response Schemas
class StepResponse(BaseModel):
    """Response model for a single step"""
    id: int
    feature_id: int
    title: str
    description: Optional[str] = None
    status: StepStatus
    step_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Response model for a single comment"""
    id: int
    feature_id: int
    user_id: str
    user_name: str
    user_email: str
    comment: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeatureResponse(BaseModel):
    """Response model for a single feature"""
    id: int
    title: str
    description: Optional[str] = None
    status: FeatureStatus
    priority: FeaturePriority
    target_date: Optional[date] = None
    created_by_id: str
    created_by_name: str
    created_by_email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    step_count: int = 0
    completed_steps: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True


class FeatureDetailResponse(BaseModel):
    """Response model for feature with steps and comments"""
    id: int
    title: str
    description: Optional[str] = None
    status: FeatureStatus
    priority: FeaturePriority
    target_date: Optional[date] = None
    created_by_id: str
    created_by_name: str
    created_by_email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    steps: List[StepResponse] = []
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True


class FeaturesListResponse(BaseModel):
    """Paginated list of features"""
    features: List[FeatureResponse]
    total: int
    page: int
    limit: int
    total_pages: int = Field(default=0)

    def __init__(self, **data):
        super().__init__(**data)
        if self.limit > 0:
            self.total_pages = math.ceil(self.total / self.limit)


class FeatureStatsResponse(BaseModel):
    """Statistics for features"""
    total_features: int
    planned: int
    in_development: int
    testing: int
    completed: int
    on_hold: int
    by_priority: dict
    total_steps: int
    completed_steps: int
