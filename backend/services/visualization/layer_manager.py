"""
Layer management system for rendering.
Implements QGIS-like layer stack with spatial indexing, visibility control,
blend modes, and memory-optimized lazy loading.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import spatial indexing
RTREE_AVAILABLE = False
try:
    from rtree import index as rtree_index
    RTREE_AVAILABLE = True
except ImportError:
    logger.debug("Rtree not available - spatial queries will be slower")


class LayerType(Enum):
    """Types of geographic layers"""
    RASTER = "raster"
    VECTOR = "vector"
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"


class BlendMode(Enum):
    """Layer blending modes (compatible with standard graphics software)"""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    LIGHTEN = "lighten"
    DARKEN = "darken"


@dataclass
class LayerProperties:
    """Metadata about a layer"""
    name: str
    layer_type: LayerType
    crs: str = "EPSG:4326"
    source_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'layer_type': self.layer_type.value,
            'crs': self.crs,
            'source_path': self.source_path,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'metadata': self.metadata,
        }


class Layer:
    """Represents a single geographic layer with lazy loading and spatial indexing"""
    
    def __init__(
        self,
        properties: LayerProperties,
        data_loader: Optional[Callable] = None
    ):
        self.properties = properties
        self.data_loader = data_loader
        self._data = None
        self._is_loaded = False
        self._spatial_index = None
        self._features = []
        self._min_memory = 0
        self._max_memory = 512  # MB
    
    @property
    def data(self) -> Any:
        """Get layer data (lazy loading)"""
        if not self._is_loaded and self.data_loader:
            try:
                self._data = self.data_loader()
                self._is_loaded = True
                self._build_spatial_index()
                logger.info(f"Loaded layer: {self.properties.name}")
            except Exception as e:
                logger.error(f"Failed to load layer {self.properties.name}: {e}")
                self._is_loaded = False
        
        return self._data
    
    @property
    def is_loaded(self) -> bool:
        """Check if layer data is loaded"""
        return self._is_loaded
    
    def load(self) -> bool:
        """Explicitly load layer data"""
        try:
            _ = self.data
            return self._is_loaded
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False
    
    def unload(self) -> bool:
        """Unload layer data from memory"""
        try:
            self._data = None
            self._is_loaded = False
            self._spatial_index = None
            logger.info(f"Unloaded layer: {self.properties.name}")
            return True
        except Exception as e:
            logger.error(f"Unload failed: {e}")
            return False
    
    def _build_spatial_index(self):
        """Build spatial index for faster queries"""
        if not self._is_loaded or self._data is None:
            return
        
        try:
            if not RTREE_AVAILABLE:
                logger.debug("Spatial indexing not available")
                return
            
            # Create R-tree index
            rtree_idx = rtree_index.Index()  # type: ignore
            
            # Index features
            if hasattr(self._data, '__iter__'):
                for i, feature in enumerate(self._data):
                    bounds = self._get_feature_bounds(feature)
                    if bounds:
                        rtree_idx.add(i, bounds)
            
            self._spatial_index = rtree_idx
            logger.debug(f"Built spatial index for {self.properties.name}")
        except Exception as e:
            logger.warning(f"Failed to build spatial index: {e}")
    
    def _get_feature_bounds(self, feature: Any) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box of feature"""
        try:
            if hasattr(feature, 'bounds'):
                # GeoJSON-like feature
                bounds = feature.bounds
                if isinstance(bounds, (list, tuple)) and len(bounds) == 4:
                    return tuple(bounds)
            elif hasattr(feature, 'geometry') and hasattr(feature.geometry, 'bounds'):
                bounds = feature.geometry.bounds
                if isinstance(bounds, (list, tuple)) and len(bounds) == 4:
                    return tuple(bounds)
            elif isinstance(feature, (list, tuple)) and len(feature) >= 4:
                return tuple(feature[:4])
        except:
            pass
        
        return None
    
    def query_spatial(self, bounds: Tuple[float, float, float, float]) -> List[int]:
        """
        Query features within spatial bounds using R-tree.
        
        Args:
            bounds: (xmin, xmax, ymin, ymax)
        
        Returns:
            List of feature indices
        """
        try:
            if self._spatial_index is None:
                # Fallback: linear search
                results = []
                if self._data is not None and hasattr(self._data, '__iter__'):
                    for i, feature in enumerate(self._data):
                        feature_bounds = self._get_feature_bounds(feature)
                        if feature_bounds:
                            fbxmin, fbxmax, fbymin, fbymax = feature_bounds
                            xmin, xmax, ymin, ymax = bounds
                            # Check if intersects
                            if not (fbxmax < xmin or fbxmin > xmax or
                                   fbymax < ymin or fbymin > ymax):
                                results.append(i)
                return results
            
            # Use R-tree
            results = list(self._spatial_index.intersection(bounds))
            return results
        except Exception as e:
            logger.warning(f"Spatial query failed: {e}")
            return []
            return []
    
    def get_feature_attributes(self, feature_id: int) -> Dict[str, Any]:
        """Get attributes of specific feature"""
        try:
            if not self._is_loaded or self._data is None:
                return {}
            
            if hasattr(self._data, '__getitem__'):
                feature = self._data[feature_id]
                
                if hasattr(feature, 'properties'):
                    return feature.properties
                elif hasattr(feature, '__dict__'):
                    return feature.__dict__
                elif isinstance(feature, dict):
                    return feature
            
            return {}
        except Exception as e:
            logger.warning(f"Failed to get attributes: {e}")
            return {}
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in MB"""
        try:
            if self._data is None:
                return 0
            
            if isinstance(self._data, np.ndarray):
                return int(self._data.nbytes / (1024 * 1024))
            
            import sys
            return int(sys.getsizeof(self._data) / (1024 * 1024))
        except:
            return 0


class LayerManager:
    """
    Manages collection of layers similar to QGIS.
    Handles layer stack, visibility, blending, and memory optimization.
    """
    
    def __init__(self, max_memory_mb: int = 1024):
        self.layers: Dict[str, Layer] = {}
        self.layer_order: List[str] = []  # Top to bottom order
        self.visibility: Dict[str, bool] = {}
        self.opacity: Dict[str, float] = {}
        self.blend_modes: Dict[str, BlendMode] = {}
        self.max_memory_mb = max_memory_mb
        self._extent = None
    
    def add_layer(
        self,
        layer: Layer,
        index: Optional[int] = None,
        visible: bool = True
    ) -> bool:
        """
        Add layer to manager.
        
        Args:
            layer: Layer to add
            index: Position in stack (None = top)
            visible: Layer visibility
        
        Returns:
            Success status
        """
        try:
            name = layer.properties.name
            
            if name in self.layers:
                logger.warning(f"Layer already exists: {name}")
                return False
            
            self.layers[name] = layer
            self.visibility[name] = visible
            self.opacity[name] = 1.0
            self.blend_modes[name] = BlendMode.NORMAL
            
            # Add to order
            if index is None:
                self.layer_order.append(name)
            else:
                self.layer_order.insert(index, name)
            
            logger.info(f"Added layer: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add layer: {e}")
            return False
    
    def remove_layer(self, name: str) -> bool:
        """Remove layer from manager"""
        try:
            if name not in self.layers:
                logger.warning(f"Layer not found: {name}")
                return False
            
            del self.layers[name]
            del self.visibility[name]
            del self.opacity[name]
            del self.blend_modes[name]
            self.layer_order.remove(name)
            
            logger.info(f"Removed layer: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove layer: {e}")
            return False
    
    def set_layer_visibility(self, name: str, visible: bool) -> bool:
        """Set layer visibility"""
        try:
            if name not in self.layers:
                return False
            
            self.visibility[name] = visible
            logger.debug(f"Layer {name} visibility: {visible}")
            return True
        except Exception as e:
            logger.error(f"Failed to set visibility: {e}")
            return False
    
    def set_layer_opacity(self, name: str, opacity: float) -> bool:
        """Set layer opacity (0.0-1.0)"""
        try:
            if name not in self.layers:
                return False
            
            opacity = max(0.0, min(1.0, opacity))
            self.opacity[name] = opacity
            return True
        except Exception as e:
            logger.error(f"Failed to set opacity: {e}")
            return False
    
    def set_layer_blend_mode(self, name: str, blend_mode: BlendMode) -> bool:
        """Set layer blending mode"""
        try:
            if name not in self.layers:
                return False
            
            self.blend_modes[name] = blend_mode
            logger.debug(f"Layer {name} blend mode: {blend_mode.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set blend mode: {e}")
            return False
    
    def get_layer(self, name: str) -> Optional[Layer]:
        """Get layer by name"""
        return self.layers.get(name)
    
    def get_visible_layers(self) -> List[Layer]:
        """Get list of visible layers (bottom to top)"""
        visible = []
        for name in reversed(self.layer_order):
            if self.visibility.get(name, False):
                visible.append(self.layers[name])
        return visible
    
    def move_layer(self, name: str, index: int) -> bool:
        """Move layer to position in stack"""
        try:
            if name not in self.layers:
                return False
            
            self.layer_order.remove(name)
            self.layer_order.insert(index, name)
            return True
        except Exception as e:
            logger.error(f"Failed to move layer: {e}")
            return False
    
    def get_layer_order(self) -> List[str]:
        """Get layer order (top to bottom)"""
        return self.layer_order.copy()
    
    def get_extent(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Get combined extent of all visible layers.
        
        Returns:
            (xmin, xmax, ymin, ymax) or None
        """
        try:
            extents = []
            
            for layer in self.get_visible_layers():
                if hasattr(layer.data, 'bounds'):
                    extents.append(layer.data.bounds)
                elif hasattr(layer.data, 'total_bounds'):
                    extents.append(layer.data.total_bounds)
            
            if not extents:
                return None
            
            # Merge extents
            xmins = [e[0] for e in extents]
            xmaxs = [e[1] for e in extents]
            ymins = [e[2] for e in extents]
            ymaxs = [e[3] for e in extents]
            
            extent = (min(xmins), max(xmaxs), min(ymins), max(ymaxs))
            self._extent = extent
            return extent
        except Exception as e:
            logger.warning(f"Failed to get extent: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get layer stack statistics"""
        stats = {
            'total_layers': len(self.layers),
            'visible_layers': sum(self.visibility.values()),
            'loaded_layers': sum(1 for l in self.layers.values() if l.is_loaded),
            'total_memory_mb': 0,
            'layer_details': {},
        }
        
        for name, layer in self.layers.items():
            memory_mb = layer.get_memory_usage()
            stats['total_memory_mb'] += memory_mb
            stats['layer_details'][name] = {
                'type': layer.properties.layer_type.value,
                'visible': self.visibility[name],
                'opacity': self.opacity[name],
                'blend_mode': self.blend_modes[name].value,
                'loaded': layer.is_loaded,
                'memory_mb': memory_mb,
            }
        
        return stats
    
    def optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage by unloading non-visible layers"""
        unloaded_count = 0
        freed_memory = 0
        
        try:
            for name, layer in self.layers.items():
                if not self.visibility.get(name, False) and layer.is_loaded:
                    memory_before = layer.get_memory_usage()
                    if layer.unload():
                        unloaded_count += 1
                        freed_memory += memory_before
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
        
        logger.info(f"Memory optimization: unloaded {unloaded_count} layers, freed {freed_memory} MB")
        return {
            'unloaded_count': unloaded_count,
            'freed_memory_mb': freed_memory,
        }
    
    def export_layer_config(self) -> Dict[str, Any]:
        """Export layer configuration as dictionary"""
        config = {
            'layers': [],
            'layer_order': self.layer_order,
            'visibility': self.visibility,
            'opacity': self.opacity,
            'blend_modes': {k: v.value for k, v in self.blend_modes.items()},
        }
        
        for name, layer in self.layers.items():
            config['layers'].append(layer.properties.to_dict())
        
        return config
    
    def import_layer_config(self, config: Dict[str, Any]) -> bool:
        """Import layer configuration"""
        try:
            self.layer_order = config.get('layer_order', [])
            self.visibility = config.get('visibility', {})
            self.opacity = config.get('opacity', {})
            
            blend_modes = config.get('blend_modes', {})
            self.blend_modes = {
                k: BlendMode(v) for k, v in blend_modes.items()
            }
            
            return True
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False
    
    def save_to_file(self, filepath: str) -> bool:
        """Save layer configuration to file"""
        try:
            config = self.export_layer_config()
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            logger.info(f"Saved layer config: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Load layer configuration from file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            return self.import_layer_config(config)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
