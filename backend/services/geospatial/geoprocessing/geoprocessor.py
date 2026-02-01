"""
Main Geoprocessing Orchestrator and Batch Processing Framework.
Unified interface for all geoprocessing operations with job queuing and progress tracking.

Features:
- Unified geoprocessing API
- Task/job queuing
- Progress tracking
- Workflow execution
- Error handling and recovery
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import numpy as np
import geopandas as gpd
from geopandas import GeoDataFrame
import json

from .vector_ops import VectorGeoprocessor, BufferParams, SimplifyParams
from .raster_algebra import RasterAlgebra
from .spatial_index import SpatialIndexer
from .expressions import FieldCalculator, QueryBuilder
from .network_analysis import NetworkGraph
from .interpolation import IDWInterpolator, ContourGenerator
from .styling import StyleRenderer, SVGMarkerLibrary
from .data_validation import DataValidator, GeometryRepair
from .layout_export import ExportManager, MapTemplate

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GeoprocessingJob:
    """Job definition for geoprocessing task."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    operation: str = ""  # buffer, clip, intersect, etc.
    input_layers: Dict[str, GeoDataFrame] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    output: Optional[GeoDataFrame] = None
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize job to dictionary."""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'operation': self.operation,
            'status': self.status.value,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }


@dataclass
class ProcessingWorkflow:
    """Multi-step processing workflow."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[GeoprocessingJob] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)


class Geoprocessor:
    """
    Main geoprocessing engine.
    Unified interface for all spatial operations.
    """
    
    def __init__(self):
        # Initialize subsystems
        self.vector_processor = VectorGeoprocessor()
        self.raster_algebra = RasterAlgebra()
        self.spatial_indexer = SpatialIndexer()
        self.field_calculator = FieldCalculator()
        self.network_graph = NetworkGraph()
        self.idw_interpolator = IDWInterpolator()
        self.contour_generator = ContourGenerator()
        self.style_renderer = StyleRenderer()
        self.data_validator = None
        self.export_manager = ExportManager()
        
        # Job management
        self.jobs: Dict[str, GeoprocessingJob] = {}
        self.workflows: Dict[str, ProcessingWorkflow] = {}
        self.job_callbacks: Dict[str, List[Callable]] = {}
    
    # ===== VECTOR OPERATIONS =====
    
    def buffer(
        self,
        input_gdf: GeoDataFrame,
        distance: float,
        quad_segs: int = 8
    ) -> GeoDataFrame:
        """Buffer geometries."""
        params = BufferParams(distance=distance, quad_segs=quad_segs)
        buffered = input_gdf.copy()
        buffered['geometry'] = input_gdf.geometry.apply(  # type: ignore
            lambda g: self.vector_processor.buffer(g, params), convert_dtype=False
        )
        return buffered
    
    def clip(
        self,
        input_gdf: GeoDataFrame,
        mask_gdf: GeoDataFrame
    ) -> GeoDataFrame:
        """Clip geometries by mask."""
        return self.vector_processor.clip(input_gdf, mask_gdf)
    
    def intersect(
        self,
        gdf1: GeoDataFrame,
        gdf2: GeoDataFrame
    ) -> GeoDataFrame:
        """Intersect two layers."""
        return self.vector_processor.intersect(gdf1, gdf2)
    
    def dissolve(
        self,
        input_gdf: GeoDataFrame,
        by: Optional[List[str]] = None,
        aggregations: Optional[Dict[str, str]] = None
    ) -> GeoDataFrame:
        """Dissolve boundaries."""
        return self.vector_processor.dissolve(input_gdf, by=by, aggregations=aggregations)
    
    def simplify(
        self,
        input_gdf: GeoDataFrame,
        tolerance: float,
        preserve_topology: bool = True
    ) -> GeoDataFrame:
        """Simplify geometries."""
        params = SimplifyParams(tolerance=tolerance, preserve_topology=preserve_topology)
        return self.vector_processor.simplify(input_gdf, params)
    
    def voronoi(self, input_gdf: GeoDataFrame) -> GeoDataFrame:
        """Generate Voronoi diagram."""
        return self.vector_processor.voronoi(input_gdf)
    
    def delaunay(self, input_gdf: GeoDataFrame) -> GeoDataFrame:
        """Generate Delaunay triangulation."""
        return self.vector_processor.delaunay(input_gdf)
    
    # ===== ATTRIBUTE OPERATIONS =====
    
    def calculate_field(
        self,
        input_gdf: GeoDataFrame,
        expression: str,
        output_field: str,
        dtype: Optional[type] = None
    ) -> GeoDataFrame:
        """Calculate field values with expression."""
        return self.field_calculator.calculate_field(
            input_gdf, expression, output_field, dtype
        )
    
    def filter_features(
        self,
        input_gdf: GeoDataFrame,
        conditions: Dict[str, tuple]
    ) -> GeoDataFrame:
        """
        Filter features by conditions.
        
        Args:
            input_gdf: Input layer
            conditions: Dict of {column: (operator, value)}
            
        Returns:
            Filtered GeoDataFrame
        """
        qb = QueryBuilder(input_gdf)
        for column, (operator, value) in conditions.items():
            qb.where(column, operator, value)
        return qb.execute()
    
    # ===== VALIDATION OPERATIONS =====
    
    def validate_data(self, input_gdf: GeoDataFrame) -> Dict[str, Any]:
        """Validate layer data quality."""
        validator = DataValidator(input_gdf)
        
        return {
            'geometries': validator.validate_geometries(),
            'attributes': validator.validate_attributes(),
            'duplicates': validator.check_duplicates(),
            'topology': validator.check_topology()
        }
    
    def repair_geometries(self, input_gdf: GeoDataFrame) -> GeoDataFrame:
        """Repair invalid geometries."""
        return GeometryRepair.fix_invalid(input_gdf)
    
    # ===== ANALYSIS OPERATIONS =====
    
    def analyze_network(self, gdf: GeoDataFrame) -> Dict[str, Any]:
        """Analyze network connectivity."""
        network = self.network_graph.from_linestring_gdf(gdf)
        return network.connectivity_analysis()
    
    def find_shortest_path(
        self,
        gdf: GeoDataFrame,
        start_id: int,
        end_id: int
    ) -> Optional[List[int]]:
        """Find shortest path in network."""
        network = self.network_graph.from_linestring_gdf(gdf)
        return network.shortest_path(start_id, end_id)
    
    def generate_contours(
        self,
        raster: 'np.ndarray',
        levels: List[float]
    ) -> GeoDataFrame:
        """Generate contour lines from raster."""
        return self.contour_generator.generate_contours(raster, levels)
    
    # ===== STYLING OPERATIONS =====
    
    def create_categorized_style(
        self,
        input_gdf: GeoDataFrame,
        column: str
    ) -> Dict[str, Any]:
        """Create categorized styling."""
        styles = self.style_renderer.create_categorized_style(input_gdf, column)
        return {k: v.to_dict() for k, v in styles.items()}
    
    def create_graduated_style(
        self,
        input_gdf: GeoDataFrame,
        column: str,
        num_classes: int = 5
    ) -> Dict[str, Any]:
        """Create graduated color styling."""
        styles = self.style_renderer.create_graduated_style(
            input_gdf, column, num_classes=num_classes
        )
        return {str(k): v.to_dict() for k, v in styles.items()}
    
    # ===== EXPORT OPERATIONS =====
    
    def export(
        self,
        input_gdf: GeoDataFrame,
        output_path: str,
        format: str
    ) -> bool:
        """Export layer to file."""
        from .layout_export import ExportFormat
        
        try:
            fmt = ExportFormat[format.upper()]
            return self.export_manager.export(input_gdf, output_path, fmt)
        except KeyError:
            raise ValueError(f"Unknown export format: {format}")
    
    # ===== JOB MANAGEMENT =====
    
    def create_job(
        self,
        name: str,
        operation: str,
        input_layers: Dict[str, GeoDataFrame],
        parameters: Dict[str, Any]
    ) -> GeoprocessingJob:
        """
        Create geoprocessing job.
        
        Args:
            name: Job name
            operation: Operation type
            input_layers: Input layers
            parameters: Operation parameters
            
        Returns:
            Created job
        """
        job = GeoprocessingJob(
            name=name,
            operation=operation,
            input_layers=input_layers,
            parameters=parameters
        )
        
        self.jobs[job.job_id] = job
        return job
    
    def execute_job(self, job_id: str) -> GeoprocessingJob:
        """Execute job."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.progress = 0.0
            
            # Execute operation
            if job.operation == "buffer":
                result = self.buffer(
                    job.input_layers['input'],
                    job.parameters['distance']
                )
            elif job.operation == "clip":
                result = self.clip(
                    job.input_layers['input'],
                    job.input_layers['mask']
                )
            elif job.operation == "intersect":
                result = self.intersect(
                    job.input_layers['layer1'],
                    job.input_layers['layer2']
                )
            elif job.operation == "dissolve":
                result = self.dissolve(
                    job.input_layers['input'],
                    by=job.parameters.get('by'),
                    aggregations=job.parameters.get('aggregations')
                )
            else:
                raise ValueError(f"Unknown operation: {job.operation}")
            
            job.output = result
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            
            self._trigger_callbacks(job_id)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Job {job_id} failed: {e}")
            self._trigger_callbacks(job_id)
        
        return job
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if not job:
            return {}
        return job.to_dict()
    
    def register_job_callback(self, job_id: str, callback: Callable):
        """Register callback for job completion."""
        if job_id not in self.job_callbacks:
            self.job_callbacks[job_id] = []
        self.job_callbacks[job_id].append(callback)
    
    def _trigger_callbacks(self, job_id: str):
        """Trigger job callbacks."""
        callbacks = self.job_callbacks.get(job_id, [])
        for callback in callbacks:
            try:
                callback(self.jobs[job_id])
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Module exports
__all__ = ['Geoprocessor', 'GeoprocessingJob', 'ProcessingWorkflow', 'JobStatus']
