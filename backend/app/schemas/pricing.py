from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerPriceBase(BaseModel):
    customer_id: int
    item_id: int
    custom_price: float

class CustomerPriceCreate(CustomerPriceBase):
    pass

class CustomerPriceUpdate(BaseModel):
    custom_price: float

class CustomerPriceResponse(CustomerPriceBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class PriceLookupResponse(BaseModel):
    item_id: int
    price: float
    source: str  # 'custom', 'default_price', 'zoho_rate'
