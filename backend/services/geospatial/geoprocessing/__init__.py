"""
Geoprocessing Module - Advanced GIS Operations.

Complete geoprocessing framework comparable to QGIS Processing Toolbox with:
- Vector geoprocessing operations (buffer, clip, intersect, union, dissolve, etc.)
- Raster algebra with custom expressions
- Spatial indexing and queries
- Advanced styling and rendering
- Interpolation and analysis
- Data validation and repair
- Layout and export
- Batch processing and workflows
"""

from .vector_ops import VectorGeoprocessor, BufferParams, SimplifyParams
from .raster_algebra import RasterAlgebra, RasterAlgebraContext, ExpressionLexer, ExpressionParser
from .spatial_index import SpatialIndexer, SpatialIndex, SpatialQuery
from .expressions import FieldCalculator, QueryBuilder, FieldExpressionContext
from .network_analysis import NetworkGraph, NetworkEdge, NetworkNode
from .interpolation import (
    IDWInterpolator, RBFInterpolator, KernelDensity,
    ContourGenerator, SpatialStatistics
)
from .styling import (
    StyleRenderer, SVGMarkerLibrary, Symbol, Color, Label, 
    LayerStyle, ColorScheme, SymbolType
)
from .data_validation import DataValidator, GeometryRepair
from .layout_export import (
    MapTemplate, ExportManager, BatchExporter,
    ExportFormat, MapTitle, MapLegend, ScaleBar, NorthArrow
)
from .geoprocessor import Geoprocessor, GeoprocessingJob, ProcessingWorkflow, JobStatus

__version__ = "2.0.0"

__all__ = [
    # Vector operations
    'VectorGeoprocessor',
    'BufferParams',
    'SimplifyParams',
    
    # Raster algebra
    'RasterAlgebra',
    'RasterAlgebraContext',
    'ExpressionLexer',
    'ExpressionParser',
    
    # Spatial indexing
    'SpatialIndexer',
    'SpatialIndex',
    'SpatialQuery',
    
    # Expressions
    'FieldCalculator',
    'QueryBuilder',
    'FieldExpressionContext',
    
    # Network analysis
    'NetworkGraph',
    'NetworkEdge',
    'NetworkNode',
    
    # Interpolation
    'IDWInterpolator',
    'RBFInterpolator',
    'KernelDensity',
    'ContourGenerator',
    'SpatialStatistics',
    
    # Styling
    'StyleRenderer',
    'SVGMarkerLibrary',
    'Symbol',
    'Color',
    'Label',
    'LayerStyle',
    'ColorScheme',
    'SymbolType',
    
    # Validation
    'DataValidator',
    'GeometryRepair',
    
    # Layout and export
    'MapTemplate',
    'ExportManager',
    'BatchExporter',
    'ExportFormat',
    'MapTitle',
    'MapLegend',
    'ScaleBar',
    'NorthArrow',
    
    # Main orchestrator
    'Geoprocessor',
    'GeoprocessingJob',
    'ProcessingWorkflow',
    'JobStatus',
]
