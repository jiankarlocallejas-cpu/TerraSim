"""
Geospatial Domain - Comprehensive spatial data processing

Consolidates all geospatial operations, CRS handling, and data services
for terrain analysis, vector operations, and raster/point cloud data management.
"""

# DEM and Terrain Processing
from .dem_processor import (
    DEMProcessor,
    LandCoverProcessor,
    SoilDataProcessor
)

# Vector Operations
from .vector_operations import (
    SpatialOperations,
    SpatialOperationType,
    SpatialOperationResult,
    GeometricMeasurements
)

# Spatial Queries
from .spatial_query import (
    SpatialQuery,
    SpatialRelation,
    AttributeFilter,
    FilterOperator,
    QueryBuilder,
    FeatureFilter,
    SpatialIndex
)

# CRS Management
from .crs_manager import (
    CRSManager,
    CRSDefinition,
    CRSType,
    MeasurementCalculator
)

# Raster Services
from .raster_service import (
    RasterService,
    get_raster,
    get_rasters,
    create_raster,
    update_raster,
    delete_raster,
    process_raster_file,
    get_raster_stats,
    create_cog
)

# Point Cloud Services
from .pointcloud_service import (
    PointCloudService,
    get_pointcloud,
    get_pointclouds,
    create_pointcloud,
    update_pointcloud,
    delete_pointcloud,
    process_pointcloud_file,
    get_pointcloud_stats
)

# Analysis Services
from .analysis import (
    get_analysis,
    get_analyses,
    create_analysis,
    update_analysis,
    delete_analysis,
    run_analysis,
    run_erosion_analysis,
    run_sediment_analysis,
    list_analysis_types,
    export_analysis_config,
    clone_analysis,
    CorrelationAnalysis,
    RegressionAnalysis,
    ModelValidation,
    UncertaintyQuantification,
)

# Domain exports
__all__ = [
    # DEM Processing
    'DEMProcessor',
    'LandCoverProcessor',
    'SoilDataProcessor',
    
    # Vector Operations
    'SpatialOperations',
    'SpatialOperationType',
    'SpatialOperationResult',
    'GeometricMeasurements',
    
    # Spatial Queries
    'SpatialQuery',
    'SpatialRelation',
    'AttributeFilter',
    'FilterOperator',
    'QueryBuilder',
    'FeatureFilter',
    'SpatialIndex',
    
    # CRS Management
    'CRSManager',
    'CRSDefinition',
    'CRSType',
    'MeasurementCalculator',
    
    # Raster Services
    'RasterService',
    'get_raster',
    'get_rasters',
    'create_raster',
    'update_raster',
    'delete_raster',
    'process_raster_file',
    'get_raster_stats',
    'create_cog',
    
    # Point Cloud Services
    'PointCloudService',
    'get_pointcloud',
    'get_pointclouds',
    'create_pointcloud',
    'update_pointcloud',
    'delete_pointcloud',
    'process_pointcloud_file',
    'get_pointcloud_stats',
    
    # Analysis Services
    'get_analysis',
    'get_analyses',
    'create_analysis',
    'update_analysis',
    'delete_analysis',
    'run_analysis',
    'run_erosion_analysis',
    'run_sediment_analysis',
    'list_analysis_types',
    'export_analysis_config',
    'clone_analysis',
    'CorrelationAnalysis',
    'RegressionAnalysis',
    'ModelValidation',
    'UncertaintyQuantification',
]
