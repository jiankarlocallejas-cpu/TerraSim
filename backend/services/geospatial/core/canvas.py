"""
Canvas and Project management - analogous to QGIS QgsProject and QgsMapCanvas.
Manages layers, coordinate reference systems, and rendering context.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from .layer import Layer, Extent, LayerProperty
from .raster_layer import RasterLayer
from .vector_layer import VectorLayer
from .pointcloud_layer import PointCloudLayer


class CanvasUnit(Enum):
    """Canvas measurement units."""
    METERS = "meters"
    FEET = "feet"
    DEGREES = "degrees"
    UNKNOWN = "unknown"


@dataclass
class CanvasSettings:
    """Canvas rendering settings."""
    background_color: tuple = (255, 255, 255)
    use_antialiasing: bool = True
    use_advanced_rendering: bool = True
    render_quality: int = 2  # 0=fast, 1=medium, 2=best
    dpi: int = 96


class LayerTree:
    """Hierarchical layer tree structure."""
    
    def __init__(self):
        self._layers: List[Layer] = []
        self._layer_map: Dict[str, Layer] = {}
        self._visibility_map: Dict[str, bool] = {}
    
    def add_layer(self, layer: Layer, position: int = -1) -> bool:
        """Add layer to tree."""
        if layer.id in self._layer_map:
            return False
        
        if position < 0 or position >= len(self._layers):
            self._layers.append(layer)
        else:
            self._layers.insert(position, layer)
        
        self._layer_map[layer.id] = layer
        self._visibility_map[layer.id] = True
        return True
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove layer from tree."""
        if layer_id not in self._layer_map:
            return False
        
        layer = self._layer_map[layer_id]
        self._layers.remove(layer)
        del self._layer_map[layer_id]
        del self._visibility_map[layer_id]
        return True
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get layer by ID."""
        return self._layer_map.get(layer_id)
    
    def get_layers(self, reverse: bool = True) -> List[Layer]:
        """Get all layers (top to bottom)."""
        return self._layers[::-1] if reverse else self._layers
    
    def get_layer_by_name(self, name: str) -> Optional[Layer]:
        """Get layer by name."""
        for layer in self._layers:
            if layer.name == name:
                return layer
        return None
    
    def move_layer(self, layer_id: str, new_position: int) -> bool:
        """Move layer to new position."""
        if layer_id not in self._layer_map:
            return False
        
        layer = self._layer_map[layer_id]
        self._layers.remove(layer)
        self._layers.insert(new_position, layer)
        return True
    
    def set_visibility(self, layer_id: str, visible: bool) -> bool:
        """Set layer visibility."""
        if layer_id not in self._layer_map:
            return False
        
        self._visibility_map[layer_id] = visible
        self._layer_map[layer_id].is_visible = visible
        return True
    
    def is_visible(self, layer_id: str) -> bool:
        """Check if layer is visible."""
        return self._visibility_map.get(layer_id, False)
    
    def get_layer_count(self) -> int:
        """Get total layer count."""
        return len(self._layers)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'layer_count': len(self._layers),
            'layers': [
                {
                    'id': layer.id,
                    'name': layer.name,
                    'type': layer.layer_type.value,
                    'visible': self._visibility_map[layer.id]
                }
                for layer in self._layers
            ]
        }


class Canvas:
    """
    Map canvas for rendering and interaction.
    Analogous to QGIS QgsMapCanvas.
    """
    
    def __init__(self, name: str = "Default Canvas", crs: str = "EPSG:4326"):
        self.id = self._generate_id()
        self.name = name
        self.crs = crs
        
        self._layer_tree = LayerTree()
        self._extent = Extent(xmin=-180, ymin=-90, xmax=180, ymax=90)
        self._settings = CanvasSettings()
        self._selected_layers: List[str] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        
        self._render_callbacks = []
        self._extent_changed_callbacks = []
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique canvas ID."""
        import uuid
        return str(uuid.uuid4())
    
    # Layer management
    def add_layer(self, layer: Layer) -> bool:
        """Add layer to canvas."""
        if self._layer_tree.add_layer(layer):
            self._updated_at = datetime.utcnow()
            return True
        return False
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove layer from canvas."""
        if self._layer_tree.remove_layer(layer_id):
            if layer_id in self._selected_layers:
                self._selected_layers.remove(layer_id)
            self._updated_at = datetime.utcnow()
            return True
        return False
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get layer by ID."""
        return self._layer_tree.get_layer(layer_id)
    
    def get_layers(self) -> List[Layer]:
        """Get all layers in rendering order."""
        return self._layer_tree.get_layers()
    
    def get_visible_layers(self) -> List[Layer]:
        """Get only visible layers."""
        return [layer for layer in self.get_layers() if layer.is_visible]
    
    def get_layer_by_type(self, layer_type) -> List[Layer]:
        """Get all layers of specific type."""
        return [layer for layer in self.get_layers() if layer.layer_type == layer_type]
    
    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        """Set layer visibility."""
        return self._layer_tree.set_visibility(layer_id, visible)
    
    def reorder_layer(self, layer_id: str, new_position: int) -> bool:
        """Reorder layer position."""
        return self._layer_tree.move_layer(layer_id, new_position)
    
    def get_layer_count(self) -> int:
        """Get total layer count."""
        return self._layer_tree.get_layer_count()
    
    # Selection
    def select_layer(self, layer_id: str) -> bool:
        """Select layer."""
        if self._layer_tree.get_layer(layer_id):
            if layer_id not in self._selected_layers:
                self._selected_layers.append(layer_id)
            return True
        return False
    
    def deselect_layer(self, layer_id: str):
        """Deselect layer."""
        if layer_id in self._selected_layers:
            self._selected_layers.remove(layer_id)
    
    def get_selected_layers(self) -> List[Layer]:
        """Get selected layers."""
        return [layer for layer in [self._layer_tree.get_layer(lid) for lid in self._selected_layers] 
                if layer is not None]
    
    # Extent and navigation
    @property
    def extent(self) -> Extent:
        """Get canvas extent."""
        return self._extent
    
    @extent.setter
    def extent(self, value: Extent):
        """Set canvas extent."""
        self._extent = value
        self._trigger_extent_changed()
    
    def zoom_to_extent(self, extent: Extent):
        """Zoom canvas to extent."""
        self.extent = extent
    
    def zoom_to_layer(self, layer_id: str) -> bool:
        """Zoom to layer extent."""
        layer = self._layer_tree.get_layer(layer_id)
        if layer and layer.extent:
            self.zoom_to_extent(layer.extent)
            return True
        return False
    
    def zoom_to_all_layers(self):
        """Zoom to fit all visible layers."""
        layers = self.get_visible_layers()
        if not layers:
            return
        
        all_extents = [l.extent for l in layers if l.extent]
        if not all_extents:
            return
        
        # Calculate combined extent
        combined = Extent(
            xmin=min(e.xmin for e in all_extents),
            ymin=min(e.ymin for e in all_extents),
            xmax=max(e.xmax for e in all_extents),
            ymax=max(e.ymax for e in all_extents),
            zmin=min(e.zmin for e in all_extents),
            zmax=max(e.zmax for e in all_extents)
        )
        self.zoom_to_extent(combined)
    
    def pan(self, dx: float, dy: float):
        """Pan canvas by pixel offset."""
        extent = self._extent
        self._extent = Extent(
            xmin=extent.xmin - dx,
            ymin=extent.ymin - dy,
            xmax=extent.xmax - dx,
            ymax=extent.ymax - dy,
            zmin=extent.zmin,
            zmax=extent.zmax
        )
        self._trigger_extent_changed()
    
    def zoom(self, factor: float, center_x: Optional[float] = None, center_y: Optional[float] = None):
        """Zoom canvas."""
        if center_x is None or center_y is None:
            center_x = (self._extent.xmin + self._extent.xmax) / 2.0
            center_y = (self._extent.ymin + self._extent.ymax) / 2.0
        
        width = (self._extent.xmax - self._extent.xmin) / factor
        height = (self._extent.ymax - self._extent.ymin) / factor
        
        self._extent = Extent(
            xmin=center_x - width / 2,
            ymin=center_y - height / 2,
            xmax=center_x + width / 2,
            ymax=center_y + height / 2,
            zmin=self._extent.zmin,
            zmax=self._extent.zmax
        )
        self._trigger_extent_changed()
    
    # Settings
    @property
    def settings(self) -> CanvasSettings:
        """Get canvas settings."""
        return self._settings
    
    def set_background_color(self, r: int, g: int, b: int):
        """Set canvas background color."""
        self._settings.background_color = (r, g, b)
    
    # Callbacks/Signals
    def on_render(self, callback):
        """Register render callback."""
        self._render_callbacks.append(callback)
    
    def on_extent_changed(self, callback):
        """Register extent changed callback."""
        self._extent_changed_callbacks.append(callback)
    
    def _trigger_extent_changed(self):
        """Trigger extent changed callbacks."""
        self._updated_at = datetime.utcnow()
        for callback in self._extent_changed_callbacks:
            try:
                callback(self, self._extent)
            except Exception as e:
                print(f"Extent callback error: {e}")
    
    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'crs': self.crs,
            'extent': self._extent.to_dict(),
            'layer_tree': self._layer_tree.to_dict(),
            'layer_count': self.get_layer_count(),
            'settings': {
                'background_color': self._settings.background_color,
                'render_quality': self._settings.render_quality
            },
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat()
        }
