from datetime import datetime
import pytz
from typing import Optional

from config import DEFAULT_TIMEZONE

def get_timezone(timezone_str: Optional[str] = None) -> pytz.timezone:
    """
    Get timezone object from string, defaulting to DEFAULT_TIMEZONE if none provided.
    
    Args:
        timezone_str: Optional timezone string (e.g., 'Asia/Kolkata', 'UTC')
        
    Returns:
        pytz.timezone object
        
    Raises:
        ValueError: If timezone string is invalid
    """
    try:
        return pytz.timezone(timezone_str or DEFAULT_TIMEZONE)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone_str}")

def convert_to_timezone(
    dt: datetime,
    target_timezone: str,
    source_timezone: Optional[str] = None
) -> datetime:
    """
    Convert datetime from source timezone to target timezone.
    
    Args:
        dt: datetime object to convert
        target_timezone: Target timezone string
        source_timezone: Source timezone string (defaults to DEFAULT_TIMEZONE)
        
    Returns:
        datetime object in target timezone
    """
    # Get timezone objects
    source_tz = get_timezone(source_timezone)
    target_tz = get_timezone(target_timezone)
    
    # If datetime is naive (no timezone info), localize it
    if dt.tzinfo is None:
        dt = source_tz.localize(dt)
    
    # Convert to target timezone
    return dt.astimezone(target_tz)

def format_datetime(dt: datetime, timezone: Optional[str] = None) -> str:
    """
    Format datetime in specified timezone.
    
    Args:
        dt: datetime object to format
        timezone: Optional timezone string (defaults to DEFAULT_TIMEZONE)
        
    Returns:
        Formatted datetime string
    """
    tz = get_timezone(timezone)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

def get_current_time(timezone: Optional[str] = None) -> datetime:
    """
    Get current time in specified timezone.
    
    Args:
        timezone: Optional timezone string (defaults to DEFAULT_TIMEZONE)
        
    Returns:
        Current datetime in specified timezone
    """
    tz = get_timezone(timezone)
    return datetime.now(tz) 