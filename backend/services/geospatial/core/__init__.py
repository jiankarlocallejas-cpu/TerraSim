"""
TerraSim Geospatial Core Module

Comprehensive QGIS-like geospatial framework for terrain analysis and simulation.
"""

from .layer import Layer, LayerType, Extent, LayerStyle, LayerProperty
from .raster_layer import RasterLayer, RasterBand
from .vector_layer import VectorLayer, Feature, Geometry, GeometryType, Attribute
from .pointcloud_layer import PointCloudLayer, PointCloudStatistics
from .canvas import Canvas, LayerTree, CanvasSettings, CanvasUnit
from .crs import CRS, CoordinateTransformer, CoordinateTransform
from .spatial_ops import (
    SpatialOperator, BufferOperation, RasterAnalysis, 
    VolumeAnalysis, FeatureStatistics, SpatialOperationType
)
from .data_providers import (
    DataProvider, GeoTIFFProvider, ShapefileProvider, LASProvider,
    JSONProvider, DataProviderRegistry, get_provider_registry
)
from .processing import (
    ProcessingAlgorithm, ProcessingParameter, ProcessingResult,
    ProcessingRegistry, get_processing_registry,
    HillshadeAlgorithm, SlopeAlgorithm, ErosionAnalysisAlgorithm
)
from .gis_engine import TerraSIMGISEngine


__all__ = [
    # Layer classes
    'Layer', 'RasterLayer', 'VectorLayer', 'PointCloudLayer',
    'LayerType', 'LayerProperty', 'LayerStyle',
    
    # Geometries
    'Geometry', 'GeometryType', 'Feature', 'Attribute',
    'RasterBand', 'PointCloudStatistics', 'Extent',
    
    # Canvas
    'Canvas', 'LayerTree', 'CanvasSettings', 'CanvasUnit',
    
    # CRS
    'CRS', 'CoordinateTransformer', 'CoordinateTransform',
    
    # Spatial operations
    'SpatialOperator', 'BufferOperation', 'RasterAnalysis',
    'VolumeAnalysis', 'FeatureStatistics', 'SpatialOperationType',
    
    # Data I/O
    'DataProvider', 'GeoTIFFProvider', 'ShapefileProvider', 'LASProvider',
    'JSONProvider', 'DataProviderRegistry', 'get_provider_registry',
    
    # Processing
    'ProcessingAlgorithm', 'ProcessingParameter', 'ProcessingResult',
    'ProcessingRegistry', 'get_processing_registry',
    'HillshadeAlgorithm', 'SlopeAlgorithm', 'ErosionAnalysisAlgorithm',
    
    # Main engine
    'TerraSIMGISEngine'
]

__version__ = '1.0.0'
__author__ = 'TerraSim Development Team'
