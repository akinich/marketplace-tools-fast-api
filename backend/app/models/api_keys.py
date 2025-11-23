"""
API Key Models
File: backend/app/models/api_keys.py
Description: Pydantic models for API key management and usage tracking
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class APIKeyCreate(BaseModel):
    """Create API key request"""
    name: str = Field(..., min_length=1, max_length=255, description="User-friendly name for the API key")
    description: Optional[str] = Field(None, description="Optional description of the key's purpose")
    scopes: List[str] = Field(default_factory=list, description="List of permission scopes")
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Number of days until the key expires (1-365)"
    )

class APIKeyResponse(BaseModel):
    """API key response (without full key)"""
    id: int
    user_id: str
    key_prefix: str = Field(..., description="First 12 characters of the key for identification")
    name: str
    description: Optional[str] = None
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response (includes full key - shown once)"""
    api_key: str = Field(..., description="Full API key - only shown once during creation")

class APIKeyUsageResponse(BaseModel):
    """API key usage log entry"""
    id: int
    endpoint: str
    method: str
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AvailableScopesResponse(BaseModel):
    """Available scopes response"""
    scopes: List[str] = Field(..., description="List of all available permission scopes")
