"""
Professional Layer Management System for TerraSim
Handles erosion-specific layers with metadata, styling, and rendering control
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Erosion-specific layer types"""
    BASE_TERRAIN = "base_terrain"  # Base DEM
    COMPARISON_DEM = "comparison_dem"  # For change detection
    EROSION_RESULT = "erosion_result"  # Erosion analysis output
    SEDIMENT_RESULT = "sediment_result"  # Sediment analysis output
    POINT_CLOUD = "point_cloud"  # LiDAR/point cloud data
    VECTOR_DATA = "vector_data"  # Shapefiles, boundaries
    RASTER_DATA = "raster_data"  # General raster


class RenderingMode(Enum):
    """Rendering modes for erosion visualization"""
    ELEVATION = "elevation"  # Standard elevation heatmap
    DIFFERENCE = "difference"  # Elevation difference (change)
    EROSION_DEPOSITION = "erosion_deposition"  # Red/Blue for erosion/deposition
    VOLUME = "volume"  # Volume change
    SLOPE = "slope"  # Slope calculation
    HILLSHADE = "hillshade"  # Hillshade relief


@dataclass
class LayerStyle:
    """Layer styling configuration"""
    colormap: str = "viridis"  # Matplotlib colormap name
    opacity: float = 0.8
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    contour_interval: Optional[float] = None
    show_contours: bool = False
    rendering_mode: RenderingMode = RenderingMode.ELEVATION
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "colormap": self.colormap,
            "opacity": self.opacity,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "contour_interval": self.contour_interval,
            "show_contours": self.show_contours,
            "rendering_mode": self.rendering_mode.value
        }


@dataclass
class LayerMetadata:
    """Layer metadata for professional management"""
    name: str
    description: str = ""
    layer_type: LayerType = LayerType.RASTER_DATA
    crs: str = "EPSG:4326"  # Coordinate Reference System
    extent: Tuple[float, float, float, float] = (0, 0, 0, 0)  # (xmin, ymin, xmax, ymax)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    source_file: Optional[str] = None
    file_format: str = ""  # "GeoTIFF", "LAS", "Shapefile", etc.
    data_type: str = ""  # "uint16", "float32", etc.
    nodata_value: Optional[float] = None
    spatial_resolution: Optional[float] = None
    vertical_units: str = "meters"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "layer_type": self.layer_type.value,
            "crs": self.crs,
            "extent": self.extent,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
            "source_file": self.source_file,
            "file_format": self.file_format,
            "data_type": self.data_type,
            "nodata_value": self.nodata_value,
            "spatial_resolution": self.spatial_resolution,
            "vertical_units": self.vertical_units
        }


@dataclass
class Layer:
    """Professional GIS layer with metadata and styling"""
    name: str
    layer_type: LayerType
    data: Optional[Any] = None
    metadata: Optional[LayerMetadata] = None
    style: Optional[LayerStyle] = None
    visible: bool = True
    locked: bool = False
    opacity: float = 0.8
    z_index: int = 0  # Layer stacking order
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = LayerMetadata(name=self.name, layer_type=self.layer_type)
        if self.style is None:
            self.style = LayerStyle()
    
    def get_statistics(self) -> Dict[str, float]:
        """Get layer statistics"""
        if self.data is None:
            return {}
        
        import numpy as np
        data = np.asarray(self.data).flatten()
        data = data[~np.isnan(data)]
        
        if len(data) == 0:
            return {}
        
        return {
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "median": float(np.median(data)),
            "count": int(len(data))
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer_type": self.layer_type.value,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity,
            "z_index": self.z_index,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "style": self.style.to_dict() if self.style else None,
            "statistics": self.get_statistics()
        }


class ProfessionalLayerManager:
    """
    Professional layer management system for TerraSim
    Handles multiple erosion-specific layers with full QGIS-like functionality
    """
    
    def __init__(self):
        self.layers: Dict[str, Layer] = {}
        self.layer_order: List[str] = []  # Z-order of layers
        self.active_layer: Optional[str] = None
        self.group_layers: Dict[str, List[str]] = {}  # Layer groups
    
    def add_layer(self, layer: Layer, group: Optional[str] = None) -> bool:
        """Add a layer to the manager"""
        if layer.name in self.layers:
            logger.warning(f"Layer '{layer.name}' already exists")
            return False
        
        self.layers[layer.name] = layer
        self.layer_order.append(layer.name)
        
        if group:
            if group not in self.group_layers:
                self.group_layers[group] = []
            self.group_layers[group].append(layer.name)
        
        self.active_layer = layer.name
        logger.info(f"Added layer: {layer.name} ({layer.layer_type.value})")
        return True
    
    def remove_layer(self, layer_name: str) -> bool:
        """Remove a layer"""
        if layer_name not in self.layers:
            return False
        
        del self.layers[layer_name]
        self.layer_order.remove(layer_name)
        
        # Remove from groups
        for group in self.group_layers.values():
            if layer_name in group:
                group.remove(layer_name)
        
        if self.active_layer == layer_name:
            self.active_layer = self.layer_order[-1] if self.layer_order else None
        
        logger.info(f"Removed layer: {layer_name}")
        return True
    
    def get_layer(self, layer_name: str) -> Optional[Layer]:
        """Get a layer by name"""
        return self.layers.get(layer_name)
    
    def get_all_layers(self) -> List[Layer]:
        """Get all layers in z-order"""
        return [self.layers[name] for name in self.layer_order if name in self.layers]
    
    def get_visible_layers(self) -> List[Layer]:
        """Get only visible layers"""
        return [layer for layer in self.get_all_layers() if layer.visible]
    
    def set_layer_visibility(self, layer_name: str, visible: bool) -> bool:
        """Toggle layer visibility"""
        layer = self.get_layer(layer_name)
        if not layer:
            return False
        
        layer.visible = visible
        return True
    
    def set_layer_opacity(self, layer_name: str, opacity: float) -> bool:
        """Set layer opacity (0.0 - 1.0)"""
        layer = self.get_layer(layer_name)
        if not layer:
            return False
        
        layer.opacity = max(0.0, min(1.0, opacity))
        return True
    
    def reorder_layers(self, layer_name: str, position: int) -> bool:
        """Reorder layers (0 = bottom, len-1 = top)"""
        if layer_name not in self.layer_order:
            return False
        
        self.layer_order.remove(layer_name)
        self.layer_order.insert(position, layer_name)
        return True
    
    def set_active_layer(self, layer_name: str) -> bool:
        """Set the active/selected layer"""
        if layer_name not in self.layers:
            return False
        
        self.active_layer = layer_name
        return True
    
    def update_layer_style(self, layer_name: str, style: LayerStyle) -> bool:
        """Update layer styling"""
        layer = self.get_layer(layer_name)
        if not layer:
            return False
        
        layer.style = style
        return True
    
    def get_layer_statistics(self, layer_name: str) -> Dict[str, Any]:
        """Get statistics for a layer"""
        layer = self.get_layer(layer_name)
        if not layer:
            return {}
        
        return {
            "name": layer.name,
            "type": layer.layer_type.value,
            "data_statistics": layer.get_statistics(),
            "extent": layer.metadata.extent if layer.metadata else None,
            "crs": layer.metadata.crs if layer.metadata else None,
            "file_format": layer.metadata.file_format if layer.metadata else None
        }
    
    def export_layers_metadata(self) -> Dict[str, Any]:
        """Export all layer metadata for project saving"""
        return {
            "layers": {
                name: layer.to_dict()
                for name, layer in self.layers.items()
            },
            "layer_order": self.layer_order,
            "active_layer": self.active_layer,
            "groups": self.group_layers
        }
    
    def get_extent_for_all_layers(self) -> Optional[Tuple[float, float, float, float]]:
        """Get combined extent of all visible layers"""
        extents = [
            layer.metadata.extent
            for layer in self.get_visible_layers()
            if layer.metadata and layer.metadata.extent != (0, 0, 0, 0)
        ]
        
        if not extents:
            return None
        
        xmins, ymins, xmaxs, ymaxs = zip(*extents)
        return (min(xmins), min(ymins), max(xmaxs), max(ymaxs))


class ErosionLayerGroup:
    """Specialized group for erosion analysis layers"""
    
    def __init__(self, analysis_name: str):
        self.analysis_name = analysis_name
        self.base_dem: Optional[Layer] = None
        self.comparison_dem: Optional[Layer] = None
        self.erosion_result: Optional[Layer] = None
        self.deposition_result: Optional[Layer] = None
        self.difference_map: Optional[Layer] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_base_dem(self, layer: Layer) -> bool:
        """Add base DEM"""
        if layer.layer_type != LayerType.BASE_TERRAIN:
            logger.warning("Layer is not a BASE_TERRAIN type")
        self.base_dem = layer
        return True
    
    def add_comparison_dem(self, layer: Layer) -> bool:
        """Add comparison DEM for change detection"""
        if layer.layer_type != LayerType.COMPARISON_DEM:
            logger.warning("Layer is not a COMPARISON_DEM type")
        self.comparison_dem = layer
        return True
    
    def set_results(self, erosion_layer: Layer, deposition_layer: Layer, diff_map: Layer):
        """Set analysis result layers"""
        self.erosion_result = erosion_layer
        self.deposition_result = deposition_layer
        self.difference_map = diff_map
    
    def get_all_layers(self) -> List[Layer]:
        """Get all layers in this analysis"""
        layers = []
        for layer in [self.base_dem, self.comparison_dem, self.erosion_result, 
                     self.deposition_result, self.difference_map]:
            if layer:
                layers.append(layer)
        return layers
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_name": self.analysis_name,
            "base_dem": self.base_dem.to_dict() if self.base_dem else None,
            "comparison_dem": self.comparison_dem.to_dict() if self.comparison_dem else None,
            "erosion_result": self.erosion_result.to_dict() if self.erosion_result else None,
            "deposition_result": self.deposition_result.to_dict() if self.deposition_result else None,
            "difference_map": self.difference_map.to_dict() if self.difference_map else None,
            "metadata": self.metadata
        }
