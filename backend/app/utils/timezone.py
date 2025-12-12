"""
Timezone utilities for the application.
All timestamps use IST (Indian Standard Time) = GMT+5:30
"""

from datetime import datetime, timezone, timedelta

# IST timezone constant (GMT+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """
    Get current datetime in IST (Indian Standard Time).
    
    Returns:
        datetime: Current time in IST timezone
        
    Example:
        >>> from app.utils.timezone import now_ist
        >>> current_time = now_ist()
        >>> print(current_time)  # 2024-12-12 14:30:00+05:30
    """
    return datetime.now(IST)


def utc_to_ist(dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST.
    
    Args:
        dt: UTC datetime
        
    Returns:
        datetime: IST datetime
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_to_utc(dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC.
    
    Args:
        dt: IST datetime
        
    Returns:
        datetime: UTC datetime
    """
    if dt.tzinfo is None:
        # Assume IST if naive
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(timezone.utc)
