"""
Email Models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class EmailTemplateSchema(BaseModel):
    """Email template model"""
    template_key: str
    name: str
    description: Optional[str] = None
    subject: str
    html_body: str
    plain_body: str
    variables: List[str] = []
    is_active: bool = True

class EmailTemplateResponse(EmailTemplateSchema):
    """Email template with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailQueueSchema(BaseModel):
    """Email queue entry"""
    to_email: EmailStr
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    subject: str
    html_body: Optional[str] = None
    plain_body: str
    template_key: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)
    scheduled_at: Optional[datetime] = None

class EmailQueueResponse(EmailQueueSchema):
    """Email queue with status"""
    id: int
    status: str
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SendEmailRequest(BaseModel):
    """Request to send email"""
    to_email: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None
    cc_emails: Optional[List[EmailStr]] = None

class SendTemplateEmailRequest(BaseModel):
    """Request to send template email"""
    to_email: EmailStr
    template_key: str
    variables: Dict[str, Any]
    cc_emails: Optional[List[EmailStr]] = None

class EmailRecipientsSchema(BaseModel):
    """Email recipients configuration"""
    notification_type: str
    recipient_emails: List[EmailStr]
    description: Optional[str] = None
    is_active: bool = True

class EmailRecipientsResponse(EmailRecipientsSchema):
    """Email recipients with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SMTPTestRequest(BaseModel):
    """Test SMTP configuration"""
    test_email: EmailStr
