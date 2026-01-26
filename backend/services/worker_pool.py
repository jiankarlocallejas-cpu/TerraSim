"""
Worker Pool Manager - Handle multiple concurrent processes
Manages parallel job execution with worker pool and queue management
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from sqlalchemy.orm import Session
from queue import Queue, PriorityQueue
import threading
import uuid

logger = logging.getLogger(__name__)


class WorkerPool:
    """Thread/process pool for managing concurrent jobs"""
    
    def __init__(self, max_workers: int = 4, worker_type: str = "thread"):
        """
        Initialize worker pool
        
        Args:
            max_workers: Maximum number of concurrent workers
            worker_type: "thread" or "process" - type of workers to use
        """
        self.max_workers = max_workers
        self.worker_type = worker_type
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_queue: PriorityQueue = PriorityQueue()
        self.lock = threading.Lock()
        
        # Create executor pool
        if worker_type == "process":
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"WorkerPool initialized: {max_workers} {worker_type} workers")
    
    def submit_job(self, job_id: str, task_func: Callable, *args, priority: int = 0, **kwargs) -> bool:
        """
        Submit a job to the worker pool
        
        Args:
            job_id: Unique job identifier
            task_func: Callable function to execute
            priority: Priority level (lower = higher priority)
            args, kwargs: Arguments for the task function
            
        Returns:
            True if submitted, False if job already exists
        """
        with self.lock:
            if job_id in self.active_jobs:
                logger.warning(f"Job {job_id} already exists")
                return False
            
            # Add to queue with priority
            self.job_queue.put((priority, job_id, task_func, args, kwargs))
            
            # Track job state
            self.active_jobs[job_id] = {
                "status": "queued",
                "priority": priority,
                "submitted_at": datetime.utcnow(),
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None
            }
            
            logger.info(f"Job {job_id} queued with priority {priority}")
            return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job"""
        with self.lock:
            return self.active_jobs.get(job_id)
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs"""
        with self.lock:
            return list(self.active_jobs.values())
    
    def get_queue_size(self) -> int:
        """Get number of jobs in queue"""
        return self.job_queue.qsize()
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics"""
        with self.lock:
            active_count = sum(1 for j in self.active_jobs.values() if j["status"] == "running")
            queued_count = sum(1 for j in self.active_jobs.values() if j["status"] == "queued")
            
            return {
                "max_workers": self.max_workers,
                "active_workers": active_count,
                "queued_jobs": queued_count,
                "total_jobs": len(self.active_jobs),
                "worker_type": self.worker_type
            }
    
    def shutdown(self, wait: bool = True):
        """Shutdown worker pool"""
        self.executor.shutdown(wait=wait)
        logger.info("WorkerPool shutdown complete")
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job"""
        with self.lock:
            if job_id not in self.active_jobs:
                return False
            
            job_info = self.active_jobs[job_id]
            if job_info["status"] == "queued":
                job_info["status"] = "cancelled"
                logger.info(f"Job {job_id} cancelled")
                return True
            elif job_info["status"] == "running":
                logger.warning(f"Cannot cancel running job {job_id}")
                return False
        
        return False


class BatchJobManager:
    """Manage batch job submissions and execution"""
    
    def __init__(self, worker_pool: WorkerPool):
        """
        Initialize batch job manager
        
        Args:
            worker_pool: WorkerPool instance
        """
        self.worker_pool = worker_pool
        self.batch_jobs: Dict[str, List[str]] = {}
    
    def submit_batch(self, batch_id: str, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Submit multiple jobs as a batch
        
        Args:
            batch_id: Unique batch identifier
            jobs: List of job definitions with task_func, args, kwargs, priority
            
        Returns:
            Batch submission result with job IDs
        """
        job_ids = []
        
        for idx, job_config in enumerate(jobs):
            job_id = f"{batch_id}_job_{idx}_{uuid.uuid4().hex[:8]}"
            task_func = job_config.get("task_func")
            args = job_config.get("args", ())
            kwargs = job_config.get("kwargs", {})
            priority = job_config.get("priority", idx)  # Default: FIFO order
            
            if task_func:
                self.worker_pool.submit_job(job_id, task_func, *args, priority=priority, **kwargs)
                job_ids.append(job_id)
        
        self.batch_jobs[batch_id] = job_ids
        
        logger.info(f"Batch {batch_id} submitted with {len(job_ids)} jobs")
        
        return {
            "batch_id": batch_id,
            "job_ids": job_ids,
            "total_jobs": len(job_ids),
            "status": "submitted",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of all jobs in a batch"""
        if batch_id not in self.batch_jobs:
            return None
        
        job_ids = self.batch_jobs[batch_id]
        statuses = []
        
        for job_id in job_ids:
            status = self.worker_pool.get_job_status(job_id)
            if status:
                statuses.append({
                    "job_id": job_id,
                    "status": status["status"]
                })
        
        # Calculate batch progress
        completed = sum(1 for s in statuses if s["status"] == "completed")
        failed = sum(1 for s in statuses if s["status"] == "failed")
        running = sum(1 for s in statuses if s["status"] == "running")
        
        return {
            "batch_id": batch_id,
            "total_jobs": len(job_ids),
            "completed": completed,
            "failed": failed,
            "running": running,
            "queued": len(job_ids) - completed - failed - running,
            "progress_percent": int((completed + failed) / len(job_ids) * 100) if job_ids else 0,
            "job_statuses": statuses
        }


# Global worker pool instance
_worker_pool: Optional[WorkerPool] = None
_batch_manager: Optional[BatchJobManager] = None


def initialize_worker_pool(max_workers: int = 4, worker_type: str = "thread"):
    """Initialize global worker pool"""
    global _worker_pool, _batch_manager
    
    _worker_pool = WorkerPool(max_workers=max_workers, worker_type=worker_type)
    logger.info(f"Global worker pool initialized with {max_workers} {worker_type} workers")


def get_worker_pool() -> WorkerPool:
    """Get global worker pool instance"""
    global _worker_pool
    
    if _worker_pool is None:
        initialize_worker_pool()
    
    # Type assertion since we just initialized it
    assert _worker_pool is not None
    return _worker_pool


def get_batch_manager(db_session_factory=None) -> BatchJobManager:
    """Get global batch job manager"""
    global _batch_manager
    
    if _batch_manager is None:
        _batch_manager = BatchJobManager(get_worker_pool())
    
    return _batch_manager


def submit_parallel_simulations(
    db: Session,
    dem_data: Any,
    parameters_list: List[Dict[str, Any]],
    callback: Optional[Callable] = None
) -> str:
    """
    Submit multiple erosion simulations to run in parallel
    
    Args:
        db: Database session
        dem_data: Digital Elevation Model data
        parameters_list: List of parameter dictionaries
        callback: Optional callback function for results
        
    Returns:
        batch_id for tracking
    """
    from backend.services.simulation_engine import get_simulation_engine
    
    batch_id = f"parallel_sim_{uuid.uuid4().hex[:8]}"
    engine = get_simulation_engine()
    
    jobs = []
    for idx, params in enumerate(parameters_list):
        job_config = {
            "task_func": engine.run_single_simulation,
            "args": (dem_data,),
            "kwargs": {
                "parameters": params,
                "batch_id": batch_id,
                "scenario_id": idx
            },
            "priority": idx
        }
        jobs.append(job_config)
    
    batch_manager = get_batch_manager()
    return batch_manager.submit_batch(batch_id, jobs)["batch_id"]
