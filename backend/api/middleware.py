"""
Middleware components for TerraSim API.
Handles request/response logging, error handling, and security.
"""

import time
import uuid
import logging
from typing import Callable, Any
from datetime import datetime
import json

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.exceptions import TerraSIMException
from backend.core.validation import ErrorResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to all requests.
    Useful for request tracing and debugging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID from header
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state for use in handlers
        request.state.request_id = request_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    Includes timing and status code information.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get request info
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Log request
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "elapsed_time_ms": elapsed_time * 1000,
                    "client": request.client.host if request.client else "unknown"
                }
            )
            
            return response
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Request failed with exception",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "elapsed_time_ms": elapsed_time * 1000,
                    "error": str(e),
                    "client": request.client.host if request.client else "unknown"
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and format exceptions.
    Converts TerraSIMException to proper HTTP responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            return await call_next(request)
        
        except TerraSIMException as e:
            logger.error(
                f"TerraSIM error: {e.error_code}",
                extra={
                    "request_id": request_id,
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "context": e.context
                }
            )
            
            error_response = ErrorResponse(
                error=e.error_code,
                message=e.message,
                status_code=e.status_code,
                details=e.details,
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.dict()
            )
        
        except Exception as e:
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            error_response = ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                status_code=500,
                details={"error": str(e)} if logger.level == logging.DEBUG else {},
                timestamp=datetime.now().isoformat(),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict()
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    Tracks requests per IP address.
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict = {}  # {ip: [(timestamp, count)]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                (timestamp, count) for timestamp, count in self.request_counts[client_ip]
                if current_time - timestamp < 60
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Count requests in last minute
        total_requests = sum(count for _, count in self.request_counts[client_ip])
        
        if total_requests >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}",
                extra={"client_ip": client_ip, "request_count": total_requests}
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "status_code": 429,
                    "details": {
                        "limit": self.requests_per_minute,
                        "window_seconds": 60
                    },
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Add request to count
        self.request_counts[client_ip].append((current_time, 1))
        
        return await call_next(request)


def add_middlewares(app: Any) -> None:
    """
    Add all middlewares to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add middlewares in reverse order (they execute bottom-up)
    
    # Rate limiting (outermost)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Request ID (innermost)
    app.add_middleware(RequestIDMiddleware)
