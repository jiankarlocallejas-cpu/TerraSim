"""
Core Layer abstraction - analogous to QGIS QgsMapLayer.
Provides base layer functionality for all layer types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json


class LayerType(Enum):
    """Layer type enumeration."""
    RASTER = "raster"
    VECTOR = "vector"
    POINT_CLOUD = "pointcloud"
    MESH = "mesh"
    ANNOTATION = "annotation"


class LayerProperty(Enum):
    """Layer property enumerations for signals/updates."""
    VISIBILITY = "visibility"
    OPACITY = "opacity"
    NAME = "name"
    CRS = "crs"
    EXTENT = "extent"
    STATUS = "status"


@dataclass
class Extent:
    """Geographic extent (bounding box)."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    zmin: float = 0.0
    zmax: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'xmin': self.xmin, 'ymin': self.ymin,
            'xmax': self.xmax, 'ymax': self.ymax,
            'zmin': self.zmin, 'zmax': self.zmax
        }
    
    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'Extent':
        return Extent(**data)


@dataclass
class LayerStyle:
    """Layer styling configuration."""
    name: str = "default"
    opacity: float = 1.0
    visible: bool = True
    blending_mode: str = "normal"
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'opacity': self.opacity,
            'visible': self.visible,
            'blending_mode': self.blending_mode,
            'properties': self.properties
        }


class Layer(ABC):
    """
    Base class for all map layers.
    Analogous to QGIS QgsMapLayer.
    """
    
    def __init__(
        self,
        name: str,
        source: str,
        layer_type: LayerType,
        crs: str = "EPSG:4326",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = self._generate_id()
        self.name = name
        self.source = source
        self.layer_type = layer_type
        self.crs = crs
        self.metadata = metadata or {}
        
        self._extent: Optional[Extent] = None
        self._style = LayerStyle()
        self._visible = True
        self._opacity = 1.0
        self._status = "ready"
        self._error_message = ""
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        
        self._property_changed_callbacks: Dict[LayerProperty, List] = {}
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique layer ID."""
        import uuid
        return str(uuid.uuid4())
    
    # Properties
    @property
    def extent(self) -> Optional[Extent]:
        """Get layer geographic extent."""
        return self._extent
    
    @extent.setter
    def extent(self, value: Extent):
        """Set layer geographic extent."""
        self._extent = value
        self._trigger_property_changed(LayerProperty.EXTENT)
    
    @property
    def style(self) -> LayerStyle:
        """Get layer style."""
        return self._style
    
    @property
    def is_visible(self) -> bool:
        """Check if layer is visible."""
        return self._visible
    
    @is_visible.setter
    def is_visible(self, value: bool):
        """Set layer visibility."""
        self._visible = value
        self._trigger_property_changed(LayerProperty.VISIBILITY)
    
    @property
    def opacity(self) -> float:
        """Get layer opacity (0.0-1.0)."""
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: float):
        """Set layer opacity."""
        self._opacity = max(0.0, min(1.0, value))
        self._trigger_property_changed(LayerProperty.OPACITY)
    
    @property
    def status(self) -> str:
        """Get layer status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        """Set layer status."""
        self._status = value
        self._trigger_property_changed(LayerProperty.STATUS)
    
    @property
    def error_message(self) -> str:
        """Get error message if status is error."""
        return self._error_message
    
    def set_error(self, message: str):
        """Set error state with message."""
        self._status = "error"
        self._error_message = message
    
    # Abstract methods
    @abstractmethod
    def get_feature_count(self) -> int:
        """Get total feature count for this layer."""
        pass
    
    @abstractmethod
    def get_attributes(self) -> Dict[str, str]:
        """Get attribute names and types."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize layer to dictionary."""
        pass
    
    # Signal/callback system
    def on_property_changed(self, prop: LayerProperty, callback):
        """Register callback for property changes."""
        if prop not in self._property_changed_callbacks:
            self._property_changed_callbacks[prop] = []
        self._property_changed_callbacks[prop].append(callback)
    
    def _trigger_property_changed(self, prop: LayerProperty):
        """Trigger property change callbacks."""
        self._updated_at = datetime.utcnow()
        if prop in self._property_changed_callbacks:
            for callback in self._property_changed_callbacks[prop]:
                try:
                    callback(self, prop)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    # Serialization
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), default=str)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get layer metadata."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.layer_type.value,
            'crs': self.crs,
            'visible': self._visible,
            'opacity': self._opacity,
            'status': self._status,
            'extent': self._extent.to_dict() if self._extent else None,
            'style': self._style.to_dict(),
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'metadata': self.metadata
        }
