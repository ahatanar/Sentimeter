"""
Timezone utilities for consistent datetime handling across the application.
All datetime operations should use UTC internally and convert to user timezone for display.
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC datetime with timezone info.
    Use this instead of datetime.now() or datetime.utcnow().
    
    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def utc_date():
    """
    Get current UTC date.
    
    Returns:
        date: Current UTC date
    """
    return datetime.now(timezone.utc).date()


def parse_user_datetime(dt_string: str, user_timezone: Optional[str] = None) -> datetime:
    """
    Parse a datetime string from user input and convert to UTC.
    
    Args:
        dt_string: Datetime string to parse
        user_timezone: User's timezone (if None, assumes UTC)
        
    Returns:
        datetime: UTC datetime with timezone info
    """
    from dateutil.parser import parse
    
    parsed_dt = parse(dt_string)
    
    if parsed_dt.tzinfo is not None:
        # Already has timezone info, convert to UTC
        return parsed_dt.astimezone(timezone.utc)
    else:
        # Naive datetime, assume UTC
        return parsed_dt.replace(tzinfo=timezone.utc)


def format_for_api(dt: datetime) -> str:
    """
    Format datetime for API response (ISO format).
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: ISO formatted datetime string
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        datetime: UTC datetime with timezone info
    """
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)