"""
Resource management and cleanup utilities for TerraSim.
Provides context managers for file handles, temporary files, and memory cleanup.
"""

import logging
import tempfile
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Any, Dict
import atexit
import weakref

logger = logging.getLogger(__name__)


class ResourceTracker:
    """
    Tracks and manages application resources.
    Ensures proper cleanup of files, connections, and memory.
    """
    
    def __init__(self):
        self.temp_files: weakref.WeakSet = weakref.WeakSet()
        self.temp_dirs: weakref.WeakSet = weakref.WeakSet()
        self.open_files: weakref.WeakSet = weakref.WeakSet()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
    
    def track_temp_file(self, path: Path) -> Path:
        """Track a temporary file for cleanup."""
        self.temp_files.add(path)
        logger.debug(f"Tracking temporary file: {path}")
        return path
    
    def track_temp_dir(self, path: Path) -> Path:
        """Track a temporary directory for cleanup."""
        self.temp_dirs.add(path)
        logger.debug(f"Tracking temporary directory: {path}")
        return path
    
    def track_file(self, file_obj) -> Any:
        """Track an open file for cleanup."""
        self.open_files.add(file_obj)
        logger.debug(f"Tracking open file: {file_obj.name if hasattr(file_obj, 'name') else file_obj}")
        return file_obj
    
    def cleanup_all(self) -> None:
        """Clean up all tracked resources."""
        logger.info("Cleaning up all tracked resources")
        
        # Close open files
        for file_obj in list(self.open_files):
            try:
                if not file_obj.closed:
                    file_obj.close()
                logger.debug(f"Closed file: {file_obj.name if hasattr(file_obj, 'name') else file_obj}")
            except Exception as e:
                logger.error(f"Error closing file: {e}")
        
        # Remove temp files
        for temp_file in list(self.temp_files):
            try:
                if temp_file.exists():
                    temp_file.unlink()
                logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Error removing temp file {temp_file}: {e}")
        
        # Remove temp directories
        for temp_dir in list(self.temp_dirs):
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                logger.debug(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error removing temp dir {temp_dir}: {e}")


# Global resource tracker
_resource_tracker = ResourceTracker()


def get_resource_tracker() -> ResourceTracker:
    """Get the global resource tracker."""
    return _resource_tracker


@contextmanager
def managed_temp_file(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[Path] = None
) -> Generator[Path, None, None]:
    """
    Context manager for temporary files.
    Automatically deletes file when context exits.
    
    Args:
        suffix: File suffix (e.g., '.tif')
        prefix: File prefix
        dir: Directory for temp file
    
    Yields:
        Path to temporary file
    
    Example:
        with managed_temp_file(suffix='.tif') as temp_file:
            # Use temp_file
            pass  # Automatically cleaned up
    """
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=False
        ) as f:
            temp_file = Path(f.name)
        
        _resource_tracker.track_temp_file(temp_file)
        yield temp_file
    
    finally:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Error cleaning up temp file {temp_file}: {e}")


@contextmanager
def managed_temp_dir(
    prefix: Optional[str] = None,
    dir: Optional[Path] = None
) -> Generator[Path, None, None]:
    """
    Context manager for temporary directories.
    Automatically deletes directory and contents when context exits.
    
    Args:
        prefix: Directory prefix
        dir: Parent directory for temp dir
    
    Yields:
        Path to temporary directory
    
    Example:
        with managed_temp_dir(prefix='terrasim_') as temp_dir:
            # Use temp_dir
            pass  # Automatically cleaned up recursively
    """
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=dir))
        _resource_tracker.track_temp_dir(temp_dir)
        yield temp_dir
    
    finally:
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp dir {temp_dir}: {e}")


@contextmanager
def managed_file(
    file_path: Path,
    mode: str = 'r',
    **kwargs
) -> Generator[Any, None, None]:
    """
    Context manager for file operations.
    Ensures file is properly closed even on error.
    
    Args:
        file_path: Path to file
        mode: File mode ('r', 'w', 'a', etc.)
        **kwargs: Additional arguments to open()
    
    Yields:
        File object
    
    Example:
        with managed_file(Path('data.txt'), 'r') as f:
            data = f.read()
    """
    f = None
    try:
        f = open(file_path, mode, **kwargs)
        _resource_tracker.track_file(f)
        yield f
    
    finally:
        if f and not f.closed:
            try:
                f.close()
                logger.debug(f"Closed file: {file_path}")
            except Exception as e:
                logger.error(f"Error closing file {file_path}: {e}")


@contextmanager
def memory_limit(max_memory_mb: float) -> Generator[None, None, None]:
    """
    Context manager to limit memory usage.
    Useful for long-running operations that might consume too much memory.
    
    Args:
        max_memory_mb: Maximum memory limit in MB
    
    Yields:
        None
    
    Raises:
        MemoryError: If memory limit is exceeded
    
    Note:
        This is a soft limit and may not work on all systems.
        Use with caution as it relies on system-specific mechanisms.
    
    Example:
        with memory_limit(500):  # 500 MB limit
            process_large_dataset()
    """
    try:
        import resource
        
        max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, hard))
        logger.info(f"Memory limit set to {max_memory_mb} MB")
        
        try:
            yield
        finally:
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
            logger.info("Memory limit removed")
    
    except ImportError:
        # resource module not available on Windows
        logger.warning("Memory limit not available on this system")
        yield
    except Exception as e:
        logger.error(f"Error setting memory limit: {e}")
        yield


class GPUMemoryManager:
    """
    Manages GPU memory for OpenGL and modernGL operations.
    Helps prevent memory leaks in graphics operations.
    """
    
    def __init__(self):
        self.allocated_buffers: Dict[int, Dict[str, Any]] = {}
        self.next_buffer_id = 0
    
    def allocate_buffer(self, size_mb: float, buffer_type: str = "vertex") -> int:
        """
        Register a GPU buffer allocation.
        
        Args:
            size_mb: Buffer size in MB
            buffer_type: Type of buffer (vertex, texture, etc.)
        
        Returns:
            Buffer ID for tracking
        """
        buffer_id = self.next_buffer_id
        self.allocated_buffers[buffer_id] = {
            "size_mb": size_mb,
            "type": buffer_type,
            "allocated_at": Path("GPU memory allocation registered")
        }
        self.next_buffer_id += 1
        
        logger.debug(f"GPU buffer allocated: ID={buffer_id}, size={size_mb}MB, type={buffer_type}")
        return buffer_id
    
    def free_buffer(self, buffer_id: int) -> bool:
        """
        Unregister a GPU buffer.
        
        Args:
            buffer_id: Buffer ID to free
        
        Returns:
            True if freed successfully
        """
        if buffer_id in self.allocated_buffers:
            info = self.allocated_buffers.pop(buffer_id)
            logger.debug(f"GPU buffer freed: ID={buffer_id}, size={info['size_mb']}MB")
            return True
        return False
    
    def get_total_allocated(self) -> float:
        """Get total GPU memory allocated in MB."""
        return sum(b["size_mb"] for b in self.allocated_buffers.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get GPU memory status."""
        return {
            "total_allocated_mb": self.get_total_allocated(),
            "buffer_count": len(self.allocated_buffers),
            "buffers": self.allocated_buffers
        }


# Global GPU memory manager
_gpu_memory_manager = GPUMemoryManager()


def get_gpu_memory_manager() -> GPUMemoryManager:
    """Get the global GPU memory manager."""
    return _gpu_memory_manager


@contextmanager
def gpu_buffer(size_mb: float, buffer_type: str = "vertex") -> Generator[int, None, None]:
    """
    Context manager for GPU buffer allocation.
    Automatically frees buffer when context exits.
    
    Args:
        size_mb: Buffer size in MB
        buffer_type: Type of buffer
    
    Yields:
        Buffer ID
    
    Example:
        with gpu_buffer(100, "texture") as buffer_id:
            # Use buffer_id for GPU operations
            pass  # Buffer automatically freed
    """
    manager = get_gpu_memory_manager()
    buffer_id = manager.allocate_buffer(size_mb, buffer_type)
    
    try:
        yield buffer_id
    finally:
        manager.free_buffer(buffer_id)
