"""
================================================================================
B2C Operations Schemas - Pydantic Models
================================================================================
Version: 1.0.0
Created: 2025-11-30

Description:
    Pydantic schemas for B2C Operations module including:
    - Order Extractor: WooCommerce order fetching and Excel export
    - Future: Shipping Label Generator, MRP Label Generator

Schemas:
    - OrderFetchRequest: Request to fetch orders from WooCommerce
    - OrderFetchResponse: Response with fetched orders
    - OrderExportRequest: Request to export selected orders to Excel
    - WooCommerceOrder: WooCommerce order structure
    - OrderLineItem: Individual line item in an order
================================================================================
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime


# ============================================================================
# WooCommerce Order Models
# ============================================================================

class OrderLineItem(BaseModel):
    """Individual line item in a WooCommerce order"""
    product_id: int
    variation_id: Optional[int] = None
    name: str
    quantity: int
    total: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 123,
                "variation_id": None,
                "name": "Product Name",
                "quantity": 2,
                "total": "50.00"
            }
        }


class WooCommerceOrder(BaseModel):
    """WooCommerce order structure"""
    id: int
    order_number: Optional[str] = None
    status: str
    date_created: str
    total: str
    customer_note: Optional[str] = ""
    payment_method_title: Optional[str] = ""
    transaction_id: Optional[str] = ""
    billing: Dict[str, Any]
    shipping: Dict[str, Any]
    line_items: List[OrderLineItem]
    
    @validator('order_number', pre=True, always=True)
    def set_order_number(cls, v, values):
        """Use id as order_number if order_number is not provided"""
        if v is None and 'id' in values:
            return str(values['id'])
        return v or ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "order_number": "12345",
                "status": "processing",
                "date_created": "2025-11-30T10:00:00",
                "total": "100.00",
                "customer_note": "Please deliver after 5pm",
                "payment_method_title": "Cash on Delivery",
                "transaction_id": "TXN123456",
                "billing": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+1234567890"
                },
                "shipping": {
                    "address_1": "123 Main St",
                    "city": "Mumbai",
                    "state": "MH",
                    "postcode": "400001"
                },
                "line_items": []
            }
        }


# ============================================================================
# Request/Response Models
# ============================================================================

class OrderFetchRequest(BaseModel):
    """Request to fetch orders from WooCommerce"""
    start_date: date = Field(..., description="Start date for order fetching (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date for order fetching (YYYY-MM-DD)")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that date range is valid and not more than 31 days"""
        if 'start_date' in values:
            start = values['start_date']
            if v < start:
                raise ValueError('end_date must be after start_date')
            if (v - start).days > 31:
                raise ValueError('Date range cannot exceed 31 days')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-11-01",
                "end_date": "2025-11-30"
            }
        }


class OrderFetchResponse(BaseModel):
    """Response with fetched orders from WooCommerce"""
    orders: List[WooCommerceOrder]
    total_count: int
    start_date: str
    end_date: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "orders": [],
                "total_count": 0,
                "start_date": "2025-11-01",
                "end_date": "2025-11-30"
            }
        }


class OrderExportRequest(BaseModel):
    """Request to export selected orders to Excel"""
    order_ids: List[int] = Field(..., description="List of order IDs to export", min_items=1)
    start_date: date = Field(..., description="Start date for filename")
    end_date: date = Field(..., description="End date for filename")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_ids": [12345, 12346, 12347],
                "start_date": "2025-11-01",
                "end_date": "2025-11-30"
            }
        }
