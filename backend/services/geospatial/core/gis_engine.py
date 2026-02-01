"""
Main GIS Engine - central orchestrator.
Similar to QGIS application-level features.
"""

from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import logging
import json
from pathlib import Path

from .canvas import Canvas, LayerTree
from .layer import Layer, Extent, LayerType
from .raster_layer import RasterLayer
from .vector_layer import VectorLayer
from .pointcloud_layer import PointCloudLayer
from .crs import CRS, CoordinateTransformer
from .data_providers import get_provider_registry
from .processing import get_processing_registry, ProcessingResult
from .spatial_ops import RasterAnalysis, VolumeAnalysis, FeatureStatistics


logger = logging.getLogger(__name__)


class TerraSIMGISEngine:
    """
    Main GIS engine for TerraSim.
    Orchestrates all geospatial operations.
    """
    
    def __init__(self, name: str = "TerraSim GIS"):
        self.name = name
        self.version = "1.0.0"
        self._canvases: Dict[str, Canvas] = {}
        self._active_canvas: Optional[Canvas] = None
        self._layer_cache: Dict[str, Layer] = {}
        self._recent_files: List[str] = []
        self._created_at = datetime.utcnow()
        
        self._provider_registry = get_provider_registry()
        self._processing_registry = get_processing_registry()
    
    # Canvas Management
    def create_canvas(self, name: str, crs: str = "EPSG:4326") -> Canvas:
        """Create new map canvas."""
        canvas = Canvas(name, crs)
        self._canvases[canvas.id] = canvas
        if not self._active_canvas:
            self._active_canvas = canvas
        logger.info(f"Created canvas: {name}")
        return canvas
    
    def get_canvas(self, canvas_id: str) -> Optional[Canvas]:
        """Get canvas by ID."""
        return self._canvases.get(canvas_id)
    
    def get_active_canvas(self) -> Optional[Canvas]:
        """Get active canvas."""
        return self._active_canvas
    
    def set_active_canvas(self, canvas_id: str) -> bool:
        """Set active canvas."""
        if canvas_id in self._canvases:
            self._active_canvas = self._canvases[canvas_id]
            return True
        return False
    
    def get_canvases(self) -> List[Canvas]:
        """Get all canvases."""
        return list(self._canvases.values())
    
    def delete_canvas(self, canvas_id: str) -> bool:
        """Delete canvas."""
        if canvas_id in self._canvases:
            del self._canvases[canvas_id]
            if self._active_canvas and self._active_canvas.id == canvas_id:
                self._active_canvas = next(iter(self._canvases.values())) if self._canvases else None
            return True
        return False
    
    # Layer Management
    def add_layer(self, layer: Layer, canvas_id: Optional[str] = None) -> bool:
        """Add layer to canvas."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            logger.error("No active canvas")
            return False
        
        self._layer_cache[layer.id] = layer
        success = canvas.add_layer(layer)
        if success:
            logger.info(f"Added layer: {layer.name}")
        return success
    
    def remove_layer(self, layer_id: str, canvas_id: Optional[str] = None) -> bool:
        """Remove layer from canvas."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            return False
        
        success = canvas.remove_layer(layer_id)
        if success and layer_id in self._layer_cache:
            del self._layer_cache[layer_id]
        return success
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get layer by ID."""
        return self._layer_cache.get(layer_id)
    
    def get_layers(self, canvas_id: Optional[str] = None) -> List[Layer]:
        """Get all layers in canvas."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            return []
        return canvas.get_layers()
    
    def get_layers_by_type(self, layer_type: LayerType, 
                          canvas_id: Optional[str] = None) -> List[Layer]:
        """Get layers of specific type."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            return []
        return canvas.get_layer_by_type(layer_type)
    
    # Data I/O
    def load_layer(self, source: str, name: Optional[str] = None) -> Optional[Layer]:
        """Load layer from file."""
        try:
            layer = self._provider_registry.read(source)
            
            if not layer:
                logger.error(f"Could not load layer from: {source}")
                return None
            
            if name:
                layer.name = name
            
            self.add_layer(layer)
            self._recent_files.append(source)
            logger.info(f"Loaded layer: {layer.name} from {source}")
            
            return layer
        except Exception as e:
            logger.error(f"Error loading layer: {str(e)}")
            return None
    
    def save_layer(self, layer_id: str, destination: str) -> bool:
        """Save layer to file."""
        try:
            layer = self.get_layer(layer_id)
            if not layer:
                return False
            
            success = self._provider_registry.write(layer, destination)
            if success:
                logger.info(f"Saved layer {layer.name} to {destination}")
            return success
        except Exception as e:
            logger.error(f"Error saving layer: {str(e)}")
            return False
    
    # Coordinate Reference System
    def get_canvas_crs(self, canvas_id: Optional[str] = None) -> CRS:
        """Get canvas CRS."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            return CRS('EPSG:4326')
        return CRS(canvas.crs)
    
    def set_canvas_crs(self, crs: str, canvas_id: Optional[str] = None) -> bool:
        """Set canvas CRS."""
        canvas = self._canvases.get(canvas_id) if canvas_id else self._active_canvas
        if not canvas:
            return False
        
        canvas.crs = crs
        logger.info(f"Set canvas CRS to {crs}")
        return True
    
    def create_coordinate_transformer(self, source_crs: str, 
                                     target_crs: str) -> Optional[CoordinateTransformer]:
        """Create coordinate transformer."""
        source = CRS(source_crs)
        target = CRS(target_crs)
        return CoordinateTransformer(source, target)
    
    # Processing
    def get_processing_algorithms(self) -> Dict[str, List[Dict[str, Any]]]:
        """List available processing algorithms."""
        return self._processing_registry.list_algorithms()
    
    def run_algorithm(self, algorithm_id: str, 
                     parameters: Dict[str, Any]) -> Optional[ProcessingResult]:
        """Run processing algorithm."""
        try:
            algo = self._processing_registry.get_algorithm(algorithm_id)
            if not algo:
                logger.error(f"Algorithm not found: {algorithm_id}")
                return None
            
            result = algo.process(parameters)
            
            # Add output layers to canvas
            if result.success and result.output_layers:
                for output_name, output_layer in result.output_layers.items():
                    self.add_layer(output_layer)
            
            logger.info(f"Algorithm {algorithm_id} completed: {result.success}")
            return result
        except Exception as e:
            logger.error(f"Error running algorithm: {str(e)}")
            return None
    
    # Spatial Analysis
    def calculate_layer_statistics(self, layer_id: str) -> Dict[str, Any]:
        """Calculate layer statistics."""
        layer = self.get_layer(layer_id)
        if not layer:
            return {}
        
        stats = {
            'layer_id': layer_id,
            'layer_name': layer.name,
            'layer_type': layer.layer_type.value,
            'extent': layer.extent.to_dict() if layer.extent else None,
            'feature_count': layer.get_feature_count(),
            'attributes': layer.get_attributes()
        }
        
        if isinstance(layer, VectorLayer):
            stats['vector_stats'] = FeatureStatistics.calculate_layer_statistics(layer)
        elif isinstance(layer, PointCloudLayer):
            layer_stats = layer.get_statistics()
            if layer_stats is not None:
                stats['pointcloud_stats'] = layer_stats.to_dict()
        
        return stats
    
    def compute_dem_derivatives(self, dem_id: str) -> Dict[str, RasterLayer]:
        """Compute DEM derivative layers (slope, aspect, curvature)."""
        dem = self.get_layer(dem_id)
        if not isinstance(dem, RasterLayer) or dem._data_cache is None:
            return {}
        
        dem_data = dem._data_cache[0] if dem._data_cache.ndim == 3 else dem._data_cache
        
        try:
            import numpy as np
            
            # Slope
            slope = RasterAnalysis.slope(dem_data)
            slope_layer = RasterLayer(f"{dem.name}_slope", dem.source, dem.crs, dem.width, dem.height)
            from .raster_layer import RasterBand
            slope_layer.add_band(RasterBand(1, "slope", "float32", np.min(slope), np.max(slope)))
            slope_layer.load_data(slope[np.newaxis, :, :])
            
            # Aspect
            aspect = RasterAnalysis.aspect(dem_data)
            aspect_layer = RasterLayer(f"{dem.name}_aspect", dem.source, dem.crs, dem.width, dem.height)
            aspect_layer.add_band(RasterBand(1, "aspect", "float32", np.min(aspect), np.max(aspect)))
            aspect_layer.load_data(aspect[np.newaxis, :, :])
            
            # Hillshade
            hillshade = RasterAnalysis.hillshade(dem_data)
            hillshade_layer = RasterLayer(f"{dem.name}_hillshade", dem.source, dem.crs, dem.width, dem.height)
            hillshade_layer.add_band(RasterBand(1, "hillshade", "uint8", 0, 255))
            hillshade_layer.load_data(hillshade[np.newaxis, :, :])
            
            # Add to cache but don't add to canvas
            self._layer_cache[slope_layer.id] = slope_layer
            self._layer_cache[aspect_layer.id] = aspect_layer
            self._layer_cache[hillshade_layer.id] = hillshade_layer
            
            return {
                'slope': slope_layer,
                'aspect': aspect_layer,
                'hillshade': hillshade_layer
            }
        except Exception as e:
            logger.error(f"Error computing DEM derivatives: {str(e)}")
            return {}
    
    def analyze_erosion(self, dem_before_id: str, dem_after_id: str, 
                       cell_size: float = 1.0) -> Optional[Dict[str, Any]]:
        """Analyze erosion between two DEMs."""
        dem_before = self.get_layer(dem_before_id)
        dem_after = self.get_layer(dem_after_id)
        
        if not isinstance(dem_before, RasterLayer) or not isinstance(dem_after, RasterLayer):
            return None
        
        if dem_before._data_cache is None or dem_after._data_cache is None:
            return None
        
        try:
            dem_before_data = dem_before._data_cache[0] if dem_before._data_cache.ndim == 3 else dem_before._data_cache
            dem_after_data = dem_after._data_cache[0] if dem_after._data_cache.ndim == 3 else dem_after._data_cache
            
            if dem_before.extent is None:
                return None
            
            volume_stats = VolumeAnalysis.calculate_volume_change(
                dem_before_data,
                dem_after_data,
                cell_size,
                dem_before.extent
            )
            
            return volume_stats
        except Exception as e:
            logger.error(f"Error analyzing erosion: {str(e)}")
            return None
    
    # Status and Info
    def get_status(self) -> Dict[str, Any]:
        """Get GIS engine status."""
        canvas = self._active_canvas
        return {
            'engine_name': self.name,
            'version': self.version,
            'active_canvas': {
                'id': canvas.id,
                'name': canvas.name,
                'crs': canvas.crs,
                'layer_count': canvas.get_layer_count()
            } if canvas else None,
            'total_canvases': len(self._canvases),
            'cached_layers': len(self._layer_cache),
            'recent_files': self._recent_files[-10:] if self._recent_files else []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state."""
        canvas = self._active_canvas
        return {
            'name': self.name,
            'version': self.version,
            'active_canvas': canvas.to_dict() if canvas else None,
            'canvases': [c.to_dict() for c in self._canvases.values()],
            'created_at': self._created_at.isoformat()
        }
