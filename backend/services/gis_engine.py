"""
Main GIS Engine - Integrates all QGIS-like components for TerraSim.
High-performance, resource-efficient geospatial analysis and visualization.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import threading
import time

from backend.services.visualization import LayerManager, Layer, LayerType, StyleManager, Renderer, GPURenderEngine, RenderQuality, LODManager
from backend.services.geospatial import SpatialOperations, GeometricMeasurements, CRSManager, CRSDefinition, QueryBuilder, FeatureFilter, SpatialIndex
from backend.services.attribute_table import AttributeTable, TableConfig
from backend.services.plugin_manager import PluginManager, HookRegistry
from backend.services.measurement_tools import DrawingTools, Measurement, DistanceMeasurement, AreaMeasurement
from backend.services.export_tools import ExportManager, ExportOptions, ExportFormat

logger = logging.getLogger(__name__)


class GISEngine:
    """Main GIS Engine - Core orchestration"""
    
    def __init__(self, plugin_dir: Optional[str] = None, enable_gpu: bool = True):
        """
        Initialize GIS Engine
        
        Args:
            plugin_dir: Directory to load plugins from
            enable_gpu: Enable GPU acceleration
        """
        logger.info("Initializing TerraSim GIS Engine...")
        
        # Core components
        self.layer_manager = LayerManager(max_memory_mb=500)
        self.style_manager = StyleManager()
        self.crs_manager = CRSManager()
        self.spatial_operations = SpatialOperations()
        self.export_manager = ExportManager()
        self.plugin_manager = PluginManager(plugin_dir)
        
        # Rendering
        self.render_engine = GPURenderEngine(use_moderngl=enable_gpu)
        self.lod_manager = LODManager()
        
        # Tools
        self.drawing_tools = DrawingTools()
        self.spatial_index = SpatialIndex()
        
        # Feature filters
        self.feature_filters: Dict[str, FeatureFilter] = {}
        
        # Attribute tables
        self.attribute_tables: Dict[str, AttributeTable] = {}
        
        # State
        self.current_extent = None
        self.current_zoom = 1.0
        self.active_tool = None
        self._running = True
        self._lock = threading.RLock()
        
        # Performance monitoring
        self.performance_stats: Dict[str, float] = {
            'fps': 0.0,
            'frame_time_ms': 0.0,
            'layer_count': 0.0,
            'feature_count': 0.0,
            'memory_mb': 0.0
        }
        
        logger.info("GIS Engine initialized successfully")
    
    # ==================== Layer Management ====================
    
    def add_layer(self, layer: Layer, index: Optional[int] = None) -> bool:
        """Add layer to map"""
        with self._lock:
            return self.layer_manager.add_layer(layer, index)
    
    def remove_layer(self, name: str) -> bool:
        """Remove layer from map"""
        with self._lock:
            removed = self.layer_manager.remove_layer(name)
            if removed and name in self.feature_filters:
                del self.feature_filters[name]
            if removed and name in self.attribute_tables:
                del self.attribute_tables[name]
            return removed
    
    def get_layer(self, name: str) -> Optional[Layer]:
        """Get layer by name"""
        return self.layer_manager.get_layer(name)
    
    def list_layers(self) -> List[str]:
        """List all layers"""
        return self.layer_manager.layer_order.copy()
    
    def set_layer_visibility(self, name: str, visible: bool) -> bool:
        """Toggle layer visibility"""
        return self.layer_manager.set_layer_visibility(name, visible)
    
    def set_layer_opacity(self, name: str, opacity: float) -> bool:
        """Set layer opacity"""
        return self.layer_manager.set_layer_opacity(name, opacity)
    
    # ==================== Coordinate Reference System ====================
    
    def set_project_crs(self, crs_code: str) -> bool:
        """Set project CRS"""
        crs_def = self.crs_manager.get_crs(crs_code)
        if crs_def:
            logger.info(f"Project CRS set to: {crs_code}")
            return True
        return False
    
    def transform_layer(self, layer_name: str, target_crs: str) -> bool:
        """Transform layer to different CRS"""
        layer = self.get_layer(layer_name)
        if not layer or layer.properties.layer_type != LayerType.VECTOR:
            return False
        
        try:
            data = layer.data
            if data is not None and hasattr(data, 'to_crs'):
                data = data.to_crs(target_crs)
                layer._data = data
                logger.info(f"Transformed {layer_name} to {target_crs}")
                return True
        except Exception as e:
            logger.error(f"CRS transformation failed: {e}")
        
        return False
    
    # ==================== Spatial Operations ====================
    
    def buffer_layer(self, layer_name: str, distance: float) -> Optional[Any]:
        """Create buffer around layer geometries"""
        layer = self.get_layer(layer_name)
        if not layer or layer.properties.layer_type != LayerType.VECTOR:
            return None
        
        data = layer.data
        if data is None or not hasattr(data, 'geometry'):
            return None
        
        result = self.spatial_operations.buffer(
            list(data.geometry),
            distance
        )
        
        if result and result.success and result.features:
            logger.info(f"Buffered {len(result.features)} features")
            return result
        
        return None
    
    def dissolve_layer(self, layer_name: str) -> Optional[Any]:
        """Dissolve layer features"""
        layer = self.get_layer(layer_name)
        if not layer:
            return None
        
        data = layer.data
        if data is None or not hasattr(data, 'geometry'):
            return None
        
        result = self.spatial_operations.dissolve(list(data.geometry))
        
        if result.success:
            logger.info(f"Dissolved features")
            return result.features[0] if result.features else None
        
        return None
    
    # ==================== Styling ====================
    
    def set_layer_renderer(self, layer_name: str, renderer: Renderer) -> bool:
        """Set layer renderer"""
        self.style_manager.set_layer_renderer(layer_name, renderer)
        return True
    
    def get_layer_renderer(self, layer_name: str) -> Optional[Renderer]:
        """Get layer renderer"""
        return self.style_manager.get_layer_renderer(layer_name)
    
    # ==================== Querying & Filtering ====================
    
    def create_feature_filter(self, layer_name: str) -> Optional[Any]:
        """Create filter for layer features"""
        layer = self.get_layer(layer_name)
        if not layer:
            return None
        
        data = layer.data
        if data is None or not hasattr(data, 'to_dict'):
            return None
        
        try:
            features = data.to_dict('records') if hasattr(data, 'to_dict') else data
            if isinstance(features, list):
                filter_obj = FeatureFilter(features)
            else:
                # Handle non-list iterables by converting to list of dicts
                feature_list = list(features) if hasattr(features, '__iter__') else [features]
                filter_obj = FeatureFilter([f if isinstance(f, dict) else {'geometry': f} for f in feature_list])
            self.feature_filters[layer_name] = filter_obj
            return filter_obj
        except Exception as e:
            logger.error(f"Filter creation failed: {e}")
            return None
    
    def query_features(self, layer_name: str, extent: Tuple[float, float, float, float]) -> List[int]:
        """Query features within extent"""
        layer = self.get_layer(layer_name)
        if not layer:
            return []
        
        return self.spatial_index.query_bounds(extent)
    
    # ==================== Attribute Tables ====================
    
    def create_attribute_table(self, layer_name: str, config: Optional[TableConfig] = None) -> Optional[AttributeTable]:
        """Create attribute table for layer"""
        layer = self.get_layer(layer_name)
        if not layer:
            return None
        
        data = layer.load()
        if data is None:
            return None
        
        table = AttributeTable(layer_name, data, config)
        self.attribute_tables[layer_name] = table
        return table
    
    def get_attribute_table(self, layer_name: str) -> Optional[AttributeTable]:
        """Get attribute table for layer"""
        return self.attribute_tables.get(layer_name)
    
    # ==================== Rendering ====================
    
    def render(
        self,
        canvas_bounds: Tuple[float, float, float, float],
        zoom_level: float = 1.0,
        quality: RenderQuality = RenderQuality.MEDIUM
    ) -> bool:
        """Render visible layers"""
        with self._lock:
            start_time = time.time()
            
            try:
                visible_layers = self.layer_manager.get_visible_layers()
                
                for layer in visible_layers:
                    self.render_engine.render_layer(
                        layer,
                        canvas_bounds,
                        zoom_level,
                        quality
                    )
                
                # Update stats
                frame_time = (time.time() - start_time) * 1000
                self.performance_stats['frame_time_ms'] = frame_time
                self.performance_stats['fps'] = 1000.0 / frame_time if frame_time > 0 else 0
                self.performance_stats['layer_count'] = len(visible_layers)
                
                # Optimize rendering if needed
                if self.performance_stats['fps'] < 60:
                    self.render_engine.optimize_for_performance(60, 512)
                
                return True
            except Exception as e:
                logger.error(f"Rendering failed: {e}")
                return False
    
    # ==================== Measurements & Drawing ====================
    
    def start_drawing(self, mode: str):
        """Start drawing mode"""
        from backend.services.measurement_tools import DrawingMode
        self.drawing_tools.start_drawing(DrawingMode[mode.upper()])
    
    def add_drawing_point(self, point: Tuple[float, float]):
        """Add point to drawing"""
        self.drawing_tools.add_point(point)
    
    def finish_drawing(self) -> Optional[Dict[str, Any]]:
        """Finish drawing and get geometry"""
        return self.drawing_tools.finish_drawing()
    
    def measure_distance(self, coords: List[Tuple[float, float]]) -> float:
        """Measure distance"""
        measurement = DistanceMeasurement(coords)
        result = measurement.calculate()
        return result.value
    
    def measure_area(self, coords: List[Tuple[float, float]]) -> float:
        """Measure area"""
        measurement = AreaMeasurement(coords)
        result = measurement.calculate()
        return result.value
    
    # ==================== Export ====================
    
    def export_layer(
        self,
        layer_name: str,
        output_path: str,
        format: str = "geojson"
    ) -> Tuple[bool, str]:
        """Export layer"""
        layer = self.get_layer(layer_name)
        if not layer:
            return False, "Layer not found"
        
        try:
            export_format = ExportFormat[format.upper()]
        except KeyError:
            return False, f"Unsupported format: {format}"
        
        data = layer.load()
        options = ExportOptions(
            format=export_format,
            output_path=output_path
        )
        
        return self.export_manager.export(data, options)
    
    # ==================== Plugins ====================
    
    def load_plugins(self) -> int:
        """Load plugins"""
        return self.plugin_manager.load_all_plugins()
    
    def get_plugin_manager(self) -> PluginManager:
        """Get plugin manager"""
        return self.plugin_manager
    
    def get_hook_registry(self) -> HookRegistry:
        """Get hook registry"""
        return self.plugin_manager.get_hook_registry()
    
    # ==================== Statistics & Performance ====================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        layer_stats = self.layer_manager.get_statistics()
        
        return {
            **self.performance_stats,
            **layer_stats,
            'render_quality': self.render_engine.lod_manager.current_lod.level
        }
    
    def optimize_memory(self, threshold_mb: int = 100):
        """Optimize memory usage"""
        self.layer_manager.optimize_memory()
        logger.info("Memory optimization completed")
    
    # ==================== Lifecycle ====================
    
    def shutdown(self):
        """Shutdown GIS engine"""
        logger.info("Shutting down GIS Engine...")
        self._running = False
        self.plugin_manager.unload_all_plugins()
        self.layer_manager.layers.clear()
        logger.info("GIS Engine shutdown complete")


# Global engine instance
_gis_engine: Optional[GISEngine] = None


def get_gis_engine(create_if_missing: bool = True) -> Optional[GISEngine]:
    """Get global GIS engine instance"""
    global _gis_engine
    
    if _gis_engine is None and create_if_missing:
        _gis_engine = GISEngine()
    
    return _gis_engine


def initialize_gis_engine(plugin_dir: Optional[str] = None, enable_gpu: bool = True) -> GISEngine:
    """Initialize global GIS engine"""
    global _gis_engine
    
    _gis_engine = GISEngine(plugin_dir, enable_gpu)
    return _gis_engine


def shutdown_gis_engine():
    """Shutdown global GIS engine"""
    global _gis_engine
    
    if _gis_engine:
        _gis_engine.shutdown()
        _gis_engine = None
