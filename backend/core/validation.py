"""
Data validation and sanitization utilities for TerraSim.
Provides request/response validation and input sanitization.
"""

import re
from typing import Any, Optional, Dict, List, Union, Type, TypeVar
from pydantic import BaseModel, ValidationError, Field, field_validator
from pathlib import Path
import html
from backend.core.exceptions import ValidationError as TerraSIMValidationError


T = TypeVar('T', bound=BaseModel)


class SanitizationConfig:
    """Configuration for input sanitization."""
    
    # Maximum file upload size (100 MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Maximum request body size (10 MB)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024
    
    # Maximum string field length
    MAX_STRING_LENGTH = 10000
    
    # Allowed file extensions for uploads
    ALLOWED_FILE_EXTENSIONS = {
        '.tif', '.tiff', '.shp', '.dbf', '.shx', '.prj',
        '.las', '.laz', '.csv', '.json', '.geojson',
        '.gpkg', '.nc', '.hdf5'
    }
    
    # Dangerous patterns (basic XSS/injection prevention)
    DANGEROUS_PATTERNS = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers
        r'<!--',  # HTML comments
        r'-->', 
    ]


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length (default from config)
    
    Returns:
        Sanitized string
    
    Raises:
        TerraSIMValidationError: If string contains dangerous content
    """
    if not isinstance(value, str):
        raise TerraSIMValidationError("Value must be a string", field="input")
    
    # Check length
    max_len = max_length or SanitizationConfig.MAX_STRING_LENGTH
    if len(value) > max_len:
        raise TerraSIMValidationError(
            f"String exceeds maximum length of {max_len}",
            field="input"
        )
    
    # Check for dangerous patterns
    for pattern in SanitizationConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise TerraSIMValidationError(
                "String contains potentially dangerous content",
                field="input"
            )
    
    # HTML escape
    return html.escape(value.strip())


def sanitize_file_path(file_path: Union[str, Path], allowed_dir: Optional[Path] = None) -> Path:
    """
    Validate and sanitize file path to prevent directory traversal attacks.
    
    Args:
        file_path: File path to sanitize
        allowed_dir: Base directory (if None, no directory check)
    
    Returns:
        Validated Path object
    
    Raises:
        TerraSIMValidationError: If path is invalid or outside allowed directory
    """
    try:
        path = Path(file_path).resolve()
    except (ValueError, TypeError) as e:
        raise TerraSIMValidationError(f"Invalid file path: {e}", field="file_path")
    
    # Check for directory traversal
    if allowed_dir:
        allowed_dir = Path(allowed_dir).resolve()
        try:
            path.relative_to(allowed_dir)
        except ValueError:
            raise TerraSIMValidationError(
                "File path is outside allowed directory",
                field="file_path"
            )
    
    return path


def validate_file_extension(file_path: Union[str, Path]) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        file_path: File path to validate
    
    Returns:
        True if valid, raises otherwise
    
    Raises:
        TerraSIMValidationError: If extension not allowed
    """
    ext = Path(file_path).suffix.lower()
    if ext not in SanitizationConfig.ALLOWED_FILE_EXTENSIONS:
        raise TerraSIMValidationError(
            f"File type not allowed. Allowed types: {', '.join(SanitizationConfig.ALLOWED_FILE_EXTENSIONS)}",
            field="file_extension"
        )
    return True


def validate_file_size(file_path: Union[str, Path], max_size: Optional[int] = None) -> bool:
    """
    Validate file size.
    
    Args:
        file_path: File path to validate
        max_size: Maximum allowed size in bytes
    
    Returns:
        True if valid, raises otherwise
    
    Raises:
        TerraSIMValidationError: If file exceeds maximum size
    """
    path = Path(file_path)
    if not path.exists():
        raise TerraSIMValidationError("File does not exist", field="file_path")
    
    max_sz = max_size or SanitizationConfig.MAX_FILE_SIZE
    file_size = path.stat().st_size
    
    if file_size > max_sz:
        raise TerraSIMValidationError(
            f"File size ({file_size} bytes) exceeds maximum ({max_sz} bytes)",
            field="file_size"
        )
    return True


def validate_numeric_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field_name: str = "value"
) -> Union[int, float]:
    """
    Validate numeric value is within range.
    
    Args:
        value: Numeric value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Field name for error messages
    
    Returns:
        Validated value
    
    Raises:
        TerraSIMValidationError: If value outside range
    """
    if not isinstance(value, (int, float)):
        raise TerraSIMValidationError(
            "Value must be numeric",
            field=field_name
        )
    
    if min_value is not None and value < min_value:
        raise TerraSIMValidationError(
            f"Value must be >= {min_value}",
            field=field_name
        )
    
    if max_value is not None and value > max_value:
        raise TerraSIMValidationError(
            f"Value must be <= {max_value}",
            field=field_name
        )
    
    return value


class SanitizedString(str):
    """Pydantic field type that sanitizes string input."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any, max_length: Optional[int] = None) -> str:
        if not isinstance(value, str):
            raise ValueError("String required")
        return sanitize_string(value, max_length)


class SafeFilePathField(str):
    """Pydantic field type for safe file paths."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any) -> str:
        if not isinstance(value, (str, Path)):
            raise ValueError("File path required")
        return str(sanitize_file_path(value))


# Pydantic v2 compatible validators
class ValidatedBaseModel(BaseModel):
    """Base model with common validation patterns."""
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_strings(cls, v):
        """Sanitize all string fields."""
        if isinstance(v, str) and len(v) > SanitizationConfig.MAX_STRING_LENGTH:
            raise ValueError(f"String exceeds maximum length of {SanitizationConfig.MAX_STRING_LENGTH}")
        return v
    
    class Config:
        # Validate on assignment
        validate_assignment = True
        # Allow extra fields but warn
        extra = "forbid"


# Request/Response models with validation
class PaginationParams(ValidatedBaseModel):
    """Common pagination parameters."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")


class ErrorResponse(ValidatedBaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: Optional[str] = Field(None, description="Timestamp of error")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SuccessResponse(ValidatedBaseModel):
    """Standard success response format."""
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Success message")
    timestamp: Optional[str] = Field(None, description="Timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
