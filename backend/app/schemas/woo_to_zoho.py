from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import date, datetime

class ExportRequestBase(BaseModel):
    start_date: date
    end_date: date
    invoice_prefix: str
    start_sequence: int

class ExportPreviewResponse(BaseModel):
    csv_rows: List[Any]
    replacements_log: List[Any]
    summary: Any
    total_orders: int

class ExportHistoryItem(BaseModel):
    id: int
    invoice_number: str
    invoice_prefix: str
    sequence_number: int
    order_id: int
    order_date: Optional[datetime]
    customer_name: Optional[str]
    order_total: float
    date_range_start: date
    date_range_end: date
    total_orders_in_export: int
    exported_by: Optional[str]
    exported_by_email: Optional[str]
    created_at: datetime

class LastSequenceResponse(BaseModel):
    last_sequence: Optional[int]
    suggested_sequence: int
