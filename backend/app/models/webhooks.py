"""
Webhook Models
Version: 1.0.0
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

class WebhookSchema(BaseModel):
    """Webhook configuration"""
    name: str
    url: HttpUrl
    events: List[str] = []
    custom_headers: Dict[str, str] = {}
    description: Optional[str] = None
    is_active: bool = True
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)

class WebhookResponse(WebhookSchema):
    """Webhook with metadata"""
    id: int
    secret: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log"""
    id: int
    webhook_id: int
    event_type: str
    payload: Dict[str, Any]
    status: str
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookTestRequest(BaseModel):
    """Test webhook"""
    webhook_id: int
    test_payload: Optional[Dict[str, Any]] = None
