"""
Centralized logging configuration for TerraSim.
Implements structured logging with multiple levels and handlers.
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import sys
from pythonjsonlogger import jsonlogger
from pythonjsonlogger.jsonlogger import JsonFormatter


class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        # Add context to record
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    name: str = "terrasim",
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (if None, logs go to console only)
        enable_json: Enable JSON format for file logging
        enable_console: Enable console output
        context: Contextual information to include in all logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create logs directory if specified
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add context filter
    if context:
        context_filter = ContextFilter(context)
        
        # Define formatters
        if enable_json:
            # JSON formatter for structured logging
            json_formatter = JsonFormatter(
                fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d %(funcName)s',
                defaults=context
            )
        
        # Console formatter
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            console_handler.addFilter(context_filter)
            logger.addHandler(console_handler)
        
        # File handler - all logs
        if log_dir:
            log_file = log_dir / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10_485_760,  # 10 MB
                backupCount=10,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            if enable_json:
                file_handler.setFormatter(json_formatter)
            else:
                file_handler.setFormatter(console_formatter)
            file_handler.addFilter(context_filter)
            logger.addHandler(file_handler)
        
        # File handler - errors only
        if log_dir:
            error_log_file = log_dir / f"{name}_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=10_485_760,  # 10 MB
                backupCount=10,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            if enable_json:
                error_handler.setFormatter(json_formatter)
            else:
                error_handler.setFormatter(console_formatter)
            error_handler.addFilter(context_filter)
            logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for a module."""
    return logging.getLogger(name)


def setup_request_logging(logger: logging.Logger) -> logging.Logger:
    """Configure logging specifically for HTTP requests."""
    logger.setLevel(logging.DEBUG)
    return logger


# Default logger setup
try:
    # Try to import python-json-logger
    import pythonjsonlogger
except ImportError:
    # Fallback if not installed
    JsonFormatter = logging.Formatter
    jsonlogger = None


# Application logger
_app_logger = setup_logging(
    name="terrasim",
    level=logging.INFO,
    log_dir=Path("logs"),
    enable_json=False,
    enable_console=True,
    context={"application": "TerraSim", "version": "3.0.0"}
)
