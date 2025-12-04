# app/models.py
from typing import List, Optional
from pydantic import BaseModel, conint


class LineItem(BaseModel):
    product_id: conint(gt=0)
    quantity: conint(gt=0)
    variation_id: Optional[int] = None  # if you use variations


class CheckoutRequest(BaseModel):
    supabase_user_id: str
    line_items: List[LineItem]
    # Optional: add billing/shipping here if you don’t want to rely on WC defaults.


class WooOrder(BaseModel):
    id: int
    status: str
    total: str

    class Config:
        extra = "allow"  # Keep additional WC fields in the response if needed
