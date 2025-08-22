import os
from datetime import datetime

def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)

def format_timestamp(timestamp: datetime, format_str: str = "%Y%m%d_%H%M%S") -> str:
    """Format timestamp for filename"""
    return timestamp.strftime(format_str)
