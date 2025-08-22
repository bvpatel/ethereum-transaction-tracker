import os
import json
from typing import Any, Dict, Optional
from datetime import datetime
from decimal import Decimal

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for special types"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)

def format_timestamp(timestamp: datetime, format_str: str = "%Y%m%d_%H%M%S") -> str:
    """Format timestamp for filename"""
    return timestamp.strftime(format_str)

def safe_get_nested(data: Dict[str, Any], keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value"""
    try:
        for key in keys.split('.'):
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default
