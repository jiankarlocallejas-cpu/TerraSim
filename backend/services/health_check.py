"""
Health checks and system monitoring for TerraSim.
Provides endpoints for checking application and dependency health.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import asyncio
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = {}
    last_check: datetime = None


class SystemHealthResponse(BaseModel):
    """Overall system health response."""
    status: HealthStatus
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    message: str = ""
    uptime_seconds: float = 0
    version: str = "3.0.0"


class HealthChecker:
    """Performs health checks on system components."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_checks: Dict[str, ComponentHealth] = {}
    
    async def check_database(self) -> ComponentHealth:
        """Check database connectivity and performance."""
        try:
            from backend.db.session import SessionLocal
            
            db = SessionLocal()
            start = datetime.now()
            
            # Simple health check query
            db.execute("SELECT 1")
            
            elapsed = (datetime.now() - start).total_seconds()
            
            if elapsed > 1.0:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database responding slowly",
                    details={"response_time_ms": elapsed * 1000},
                    last_check=datetime.now()
                )
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database healthy",
                details={"response_time_ms": elapsed * 1000},
                last_check=datetime.now()
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}",
                details={"error": str(e)},
                last_check=datetime.now()
            )
    
    async def check_storage(self) -> ComponentHealth:
        """Check storage availability and space."""
        try:
            from backend.core.config import settings
            
            storage_path = Path(settings.LOCAL_STORAGE_PATH)
            
            # Check if path exists and is writable
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Try to write a test file
            test_file = storage_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            
            # Check free space
            import shutil
            usage = shutil.disk_usage(storage_path)
            free_percent = (usage.free / usage.total) * 100
            
            if free_percent < 10:
                return ComponentHealth(
                    name="storage",
                    status=HealthStatus.DEGRADED,
                    message=f"Storage space low ({free_percent:.1f}% free)",
                    details={
                        "free_gb": usage.free / (1024**3),
                        "total_gb": usage.total / (1024**3),
                        "free_percent": free_percent
                    },
                    last_check=datetime.now()
                )
            
            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                message="Storage healthy",
                details={
                    "free_gb": usage.free / (1024**3),
                    "total_gb": usage.total / (1024**3),
                    "free_percent": free_percent
                },
                last_check=datetime.now()
            )
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage error: {str(e)}",
                details={"error": str(e)},
                last_check=datetime.now()
            )
    
    async def check_dependencies(self) -> ComponentHealth:
        """Check required Python dependencies."""
        required_packages = [
            'numpy', 'pandas', 'geopandas', 'rasterio',
            'shapely', 'scipy', 'fastapi'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            return ComponentHealth(
                name="dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing dependencies: {', '.join(missing)}",
                details={"missing_packages": missing},
                last_check=datetime.now()
            )
        
        return ComponentHealth(
            name="dependencies",
            status=HealthStatus.HEALTHY,
            message="All dependencies available",
            details={"required_packages": required_packages},
            last_check=datetime.now()
        )
    
    async def check_memory(self) -> ComponentHealth:
        """Check system memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical ({percent_used}%)"
            elif percent_used > 75:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high ({percent_used}%)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory healthy ({percent_used}% used)"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "total_gb": memory.total / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": percent_used
                },
                last_check=datetime.now()
            )
        except ImportError:
            # psutil not installed, skip check
            return ComponentHealth(
                name="memory",
                status=HealthStatus.HEALTHY,
                message="Memory check skipped (psutil not installed)",
                last_check=datetime.now()
            )
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return ComponentHealth(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)},
                last_check=datetime.now()
            )
    
    async def run_all_checks(self) -> SystemHealthResponse:
        """Run all health checks."""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_storage(),
            self.check_dependencies(),
            self.check_memory()
        )
        
        components = {check.name: check for check in checks}
        self.last_checks = components
        
        # Determine overall status
        statuses = [check.status for check in checks]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return SystemHealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            components=components,
            message=f"System {overall_status.value}",
            uptime_seconds=uptime,
            version="3.0.0"
        )


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
