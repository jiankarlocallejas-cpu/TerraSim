"""Validators for common data types and formats."""

from typing import Any, Dict, List, Optional, Union
import re


def validate_dem_data(dem_data: Any) -> bool:
    """Validate DEM data format.
    
    Args:
        dem_data: Data to validate
        
    Returns:
        True if valid DEM data
    """
    # Implementation to validate DEM arrays
    pass


def validate_coordinates(
    latitude: float,
    longitude: float
) -> bool:
    """Validate geographic coordinates.
    
    Args:
        latitude: Latitude value (-90 to 90)
        longitude: Longitude value (-180 to 180)
        
    Returns:
        True if coordinates are valid
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """Validate file path and extension.
    
    Args:
        file_path: Path to file
        allowed_extensions: List of allowed file extensions
        
    Returns:
        True if file path is valid
    """
    if not file_path:
        return False
    
    if allowed_extensions:
        ext = file_path.split('.')[-1].lower()
        return ext in allowed_extensions
    
    return True
