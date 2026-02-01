"""Helper functions for common operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def safe_dict_get(data: Dict, *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary values.
    
    Args:
        data: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Value at keys or default
        
    Example:
        >>> data = {'user': {'profile': {'name': 'John'}}}
        >>> safe_dict_get(data, 'user', 'profile', 'name')
        'John'
        >>> safe_dict_get(data, 'user', 'email', default='N/A')
        'N/A'
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable file size.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
        
    Example:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_time_delta_string(seconds: float) -> str:
    """Convert seconds to human-readable duration.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
        
    Example:
        >>> get_time_delta_string(3661)
        '1h 1m 1s'
    """
    delta = timedelta(seconds=seconds)
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    
    return ' '.join(parts) or '0s'


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
        
    Example:
        >>> d = {'a': 1, 'b': {'c': 2, 'd': 3}}
        >>> flatten_dict(d)
        {'a': 1, 'b.c': 2, 'b.d': 3}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
