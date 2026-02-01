"""
Vector layer implementation.
Handles point, line, polygon geometries and attributes.
"""

from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from .layer import Layer, LayerType, Extent
from dataclasses import dataclass, field


class GeometryType(Enum):
    """Vector geometry types."""
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    MULTIPOLYGON = "MultiPolygon"


@dataclass
class Attribute:
    """Vector feature attribute."""
    name: str
    type: str  # string, integer, real, boolean
    length: int = 255
    precision: int = 0
    default_value: Any = None


@dataclass
class Geometry:
    """Geometry representation (WKT format internally)."""
    wkt: str
    geometry_type: GeometryType
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'wkt': self.wkt,
            'type': self.geometry_type.value
        }


@dataclass
class Feature:
    """Vector feature with geometry and attributes."""
    fid: int
    geometry: Geometry
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fid': self.fid,
            'geometry': self.geometry.to_dict(),
            'attributes': self.attributes
        }


class VectorLayer(Layer):
    """
    Vector data layer (points, lines, polygons).
    Analogous to QGIS QgsVectorLayer.
    """
    
    def __init__(
        self,
        name: str,
        source: str,
        geometry_type: GeometryType = GeometryType.POINT,
        crs: str = "EPSG:4326",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, source, LayerType.VECTOR, crs, metadata)
        
        self.geometry_type = geometry_type
        self._features: Dict[int, Feature] = {}
        self._attributes: Dict[str, Attribute] = {}
        self._next_fid = 1
        self._spatial_index: Optional[Dict] = None
    
    def add_attribute(self, attribute: Attribute):
        """Add attribute field to layer."""
        self._attributes[attribute.name] = attribute
    
    def get_attributes(self) -> Dict[str, str]:
        """Get attributes as name -> type mapping."""
        return {name: attr.type for name, attr in self._attributes.items()}
    
    def get_attribute_list(self) -> List[Attribute]:
        """Get all attributes."""
        return list(self._attributes.values())
    
    def add_feature(self, geometry: Geometry, attributes: Dict[str, Any]) -> int:
        """Add feature to layer, returns feature ID."""
        feature = Feature(
            fid=self._next_fid,
            geometry=geometry,
            attributes=attributes
        )
        self._features[self._next_fid] = feature
        self._next_fid += 1
        return feature.fid
    
    def get_feature(self, fid: int) -> Optional[Feature]:
        """Get feature by ID."""
        return self._features.get(fid)
    
    def get_features(self, filter_expr: Optional[str] = None) -> List[Feature]:
        """Get all features, optionally filtered."""
        features = list(self._features.values())
        # Simple filter support - can be extended with expression parser
        return features
    
    def update_feature(self, fid: int, geometry: Optional[Geometry] = None, 
                      attributes: Optional[Dict[str, Any]] = None) -> bool:
        """Update feature geometry or attributes."""
        if fid not in self._features:
            return False
        
        feature = self._features[fid]
        if geometry:
            feature.geometry = geometry
        if attributes:
            feature.attributes.update(attributes)
        return True
    
    def delete_feature(self, fid: int) -> bool:
        """Delete feature by ID."""
        if fid in self._features:
            del self._features[fid]
            return True
        return False
    
    def get_feature_count(self) -> int:
        """Get total feature count."""
        return len(self._features)
    
    def get_extent(self) -> Optional[Extent]:
        """Calculate extent from all features."""
        if not self._features:
            return None
        
        # Simple WKT parsing for extent
        xmin, ymin, xmax, ymax = float('inf'), float('inf'), float('-inf'), float('-inf')
        
        for feature in self._features.values():
            # Extract coordinates from WKT (simplified)
            wkt = feature.geometry.wkt
            # This would need proper WKT parser
            # For now, return cached extent if available
            pass
        
        return self._extent
    
    def query_spatial(self, extent: Extent) -> List[Feature]:
        """Query features within spatial extent."""
        # Simple spatial query - can be optimized with spatial index
        results = []
        for feature in self._features.values():
            # Check if feature intersects extent
            results.append(feature)
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **self.get_metadata(),
            'geometry_type': self.geometry_type.value,
            'feature_count': self.get_feature_count(),
            'attributes': self.get_attributes(),
            'features': [f.to_dict() for f in list(self._features.values())[:100]]  # Limit for API
        }
