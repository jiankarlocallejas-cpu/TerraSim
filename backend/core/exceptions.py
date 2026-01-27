"""
Custom exception classes for TerraSim application.
Provides structured error handling and HTTP-friendly responses.
"""

from typing import Optional, Dict, Any


class TerraSIMException(Exception):
    """
    Base exception for all TerraSim errors.
    Provides consistent error structure across the application.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TerraSim exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (default 500)
            error_code: Machine-readable error code for API clients
            details: Additional error details
            context: Contextual information for debugging
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "context": self.context,
        }


class ValidationError(TerraSIMException):
    """Raised when input validation fails."""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        if field:
            message = f"{field}: {message}"
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details or {},
            **kwargs
        )


class NotFoundError(TerraSIMException):
    """Raised when a resource is not found."""
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            **kwargs
        )


class AuthorizationError(TerraSIMException):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            **kwargs
        )


class AuthenticationError(TerraSIMException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            **kwargs
        )


class ConflictError(TerraSIMException):
    """Raised when operation conflicts with existing data."""
    def __init__(
        self,
        message: str,
        conflict_with: Optional[str] = None,
        **kwargs
    ):
        if conflict_with:
            message = f"{message} (conflicts with: {conflict_with})"
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            **kwargs
        )


class DatabaseError(TerraSIMException):
    """Raised when database operation fails."""
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details={"query": query} if query else {},
            **kwargs
        )


class ProcessingError(TerraSIMException):
    """Raised when erosion model or analysis processing fails."""
    def __init__(
        self,
        message: str,
        process_type: Optional[str] = None,
        step: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if process_type:
            details["process_type"] = process_type
        if step:
            details["step"] = step
        
        super().__init__(
            message=message,
            status_code=500,
            error_code="PROCESSING_ERROR",
            details=details,
            **kwargs
        )


class GISError(ProcessingError):
    """Raised when GIS operation fails."""
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            process_type="GIS_OPERATION",
            step=operation,
            **kwargs
        )


class FileOperationError(TerraSIMException):
    """Raised when file operation fails."""
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            status_code=500,
            error_code="FILE_OPERATION_ERROR",
            details=details,
            **kwargs
        )


class ConfigurationError(TerraSIMException):
    """Raised when configuration is missing or invalid."""
    def __init__(
        self,
        message: str,
        setting: Optional[str] = None,
        **kwargs
    ):
        if setting:
            message = f"Configuration error - {setting}: {message}"
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            **kwargs
        )


class DependencyError(TerraSIMException):
    """Raised when required dependency is missing or unavailable."""
    def __init__(
        self,
        dependency: str,
        message: Optional[str] = None,
        **kwargs
    ):
        msg = f"Required dependency unavailable: {dependency}"
        if message:
            msg += f" ({message})"
        super().__init__(
            message=msg,
            status_code=500,
            error_code="DEPENDENCY_ERROR",
            **kwargs
        )


class ResourceLimitError(TerraSIMException):
    """Raised when resource limit is exceeded."""
    def __init__(
        self,
        resource: str,
        limit: Optional[str] = None,
        current: Optional[str] = None,
        **kwargs
    ):
        message = f"{resource} limit exceeded"
        details = {}
        if limit:
            details["limit"] = limit
        if current:
            details["current"] = current
        
        super().__init__(
            message=message,
            status_code=429,
            error_code="RESOURCE_LIMIT",
            details=details,
            **kwargs
        )


class TimeoutError(TerraSIMException):
    """Raised when operation exceeds time limit."""
    def __init__(
        self,
        operation: str,
        timeout: Optional[float] = None,
        **kwargs
    ):
        message = f"{operation} exceeded time limit"
        details = {}
        if timeout:
            details["timeout_seconds"] = timeout
        
        super().__init__(
            message=message,
            status_code=504,
            error_code="OPERATION_TIMEOUT",
            details=details,
            **kwargs
        )
