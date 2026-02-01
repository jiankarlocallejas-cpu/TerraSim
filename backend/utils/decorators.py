"""Decorators for common functionality."""

import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Wrapped function with timing
        
    Example:
        >>> @timing_decorator
        >>> def slow_function():
        ...     time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper


def retry_decorator(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between attempts in seconds
        
    Returns:
        Decorator function
        
    Example:
        >>> @retry_decorator(max_attempts=3, delay=0.5)
        >>> def unstable_function():
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


def logging_decorator(func: Callable) -> Callable:
    """Decorator to log function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Wrapped function with logging
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} returned {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {str(e)}")
            raise
    return wrapper
