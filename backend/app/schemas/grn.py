
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal

class GRNItemUpdate(BaseModel):
    item_id: int
    gross_received: Decimal = Field(..., ge=0, decimal_places=3)
    damage: Decimal = Field(default=0, ge=0, decimal_places=3)
    reject: Decimal = Field(default=0, ge=0, decimal_places=3)
    damage_cost_allocation: Optional[str] = Field(None, pattern='^(farm|us)$')
    reject_cost_allocation: Optional[str] = Field(None, pattern='^(farm|us)$')
    notes: Optional[str] = None
    
    @validator('damage_cost_allocation')
    def validate_damage_allocation(cls, v, values):
        if values.get('damage', 0) > 0 and not v:
            raise ValueError('Cost allocation required when damage > 0')
        return v
    
    @validator('reject_cost_allocation')
    def validate_reject_allocation(cls, v, values):
        if values.get('reject', 0) > 0 and not v:
            raise ValueError('Cost allocation required when reject > 0')
        return v

class GRNUpdateRequest(BaseModel):
    transport_method: Optional[str] = None
    number_of_boxes: Optional[int] = Field(None, ge=0)
    receiving_time: Optional[time] = None
    receiving_date: Optional[date] = None
    receiver_id: Optional[str] = None
    items: Optional[List[GRNItemUpdate]] = None
    notes: Optional[str] = None

class GRNItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None # fetched from join
    gross_received: Decimal
    damage: Decimal
    reject: Decimal
    final_accepted: Decimal
    damage_cost_allocation: Optional[str] = None
    reject_cost_allocation: Optional[str] = None
    notes: Optional[str] = None
    added_to_po: bool

class GRNPhotoResponse(BaseModel):
    id: int
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    photo_type: str
    photo_url: str
    uploaded_by: str
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime
    file_size: Optional[int] = None
    notes: Optional[str] = None

class GRNResponse(BaseModel):
    id: int
    grn_number: str
    po_id: int
    po_number: Optional[str] = None
    batch_id: int
    batch_number: Optional[str] = None
    vendor_id: Optional[int] = None # derived from PO
    vendor_name: Optional[str] = None
    transport_method: Optional[str] = None
    number_of_boxes: Optional[int] = None
    receiving_time: Optional[time] = None
    receiving_date: date
    status: str
    receiver_id: Optional[str] = None
    receiver_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class EditHistory(BaseModel):
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    edited_by: str
    edited_by_name: Optional[str] = None
    edited_at: datetime

class GRNDetailResponse(GRNResponse):
    items: List[GRNItemResponse]
    photos: List[GRNPhotoResponse]
    edit_history: List[EditHistory]

class GRNListResponse(BaseModel):
    grns: List[GRNResponse]
    total: int
    page: int
    limit: int
