"""
Coordinate Reference System (CRS) management.
Handles EPSG codes, transformations, and spatial reference operations.
"""

from typing import Optional, Dict, Tuple, List, TYPE_CHECKING, Any
from dataclasses import dataclass
import re

if TYPE_CHECKING:
    from .layer import Extent


@dataclass
class CoordinateTransform:
    """Represents a coordinate transformation between two CRS."""
    source_crs: 'CRS'
    target_crs: 'CRS'
    accuracy: float = 0.0  # meters


class CRS:
    """
    Coordinate Reference System representation.
    Analogous to QGIS QgsCoordinateReferenceSystem.
    """
    
    # Common EPSG codes cache
    _EPSG_DEFINITIONS = {
        'EPSG:4326': {
            'name': 'WGS 84',
            'proj4': '+proj=longlat +datum=WGS84 +no_defs',
            'unit': 'degrees',
            'is_geographic': True
        },
        'EPSG:3857': {
            'name': 'Web Mercator',
            'proj4': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs',
            'unit': 'meters',
            'is_geographic': False
        },
        'EPSG:2154': {
            'name': 'Lambert 93',
            'proj4': '+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
            'unit': 'meters',
            'is_geographic': False
        },
        'EPSG:32633': {
            'name': 'WGS 84 / UTM zone 33N',
            'proj4': '+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs',
            'unit': 'meters',
            'is_geographic': False
        }
    }
    
    def __init__(self, crs_string: str):
        """
        Initialize CRS from EPSG code or WKT.
        Examples: 'EPSG:4326', 'EPSG:3857', 'WGS 84'
        """
        self.crs_string = crs_string
        self._parse_crs(crs_string)
    
    def _parse_crs(self, crs_string: str):
        """Parse CRS string."""
        if crs_string in self._EPSG_DEFINITIONS:
            self.epsg_code = crs_string
            definition = self._EPSG_DEFINITIONS[crs_string]
            self.name = definition['name']
            self.proj4 = definition['proj4']
            self.unit = definition['unit']
            self.is_geographic = definition['is_geographic']
        else:
            # Parse EPSG code
            match = re.match(r'EPSG:(\d+)', crs_string)
            if match:
                self.epsg_code = crs_string
                self.name = f"EPSG {match.group(1)}"
                self.is_geographic = self._is_geographic_epsg(int(match.group(1)))
                self.unit = 'degrees' if self.is_geographic else 'meters'
            else:
                self.epsg_code = None
                self.name = crs_string
                self.is_geographic = False
                self.unit = 'unknown'
    
    @staticmethod
    def _is_geographic_epsg(code: int) -> bool:
        """Check if EPSG code is geographic."""
        # Geographic codes are typically 4000-4999
        return 4000 <= code < 5000
    
    @staticmethod
    def from_epsg(code: int) -> 'CRS':
        """Create CRS from EPSG code."""
        return CRS(f'EPSG:{code}')
    
    @staticmethod
    def from_wkt(wkt_string: str) -> 'CRS':
        """Create CRS from WKT string."""
        from pyproj import CRS as ProjCRS
        try:
            proj_crs = ProjCRS.from_wkt(wkt_string)
            crs = CRS(proj_crs.to_string())
            return crs
        except Exception:
            crs = CRS('EPSG:4326')  # Default
            return crs
    
    def is_valid(self) -> bool:
        """Check if CRS is valid."""
        return self.epsg_code is not None
    
    def get_epsg_code(self) -> Optional[int]:
        """Get EPSG code if available."""
        if self.epsg_code:
            match = re.match(r'EPSG:(\d+)', self.epsg_code)
            if match:
                return int(match.group(1))
        return None
    
    def get_units(self) -> str:
        """Get CRS units (degrees, meters, etc.)."""
        return self.unit
    
    def is_geographical(self) -> bool:
        """Check if CRS uses geographic coordinates."""
        return self.is_geographic
    
    def can_transform_to(self, other: 'CRS') -> bool:
        """Check if transformation to another CRS is possible."""
        return True  # Simplified - real implementation would check proj4
    
    def get_transformation(self, other: 'CRS') -> Optional[CoordinateTransform]:
        """Get transformation between CRS."""
        if self.can_transform_to(other):
            return CoordinateTransform(self, other)
        return None
    
    def to_epsg_string(self) -> str:
        """Get EPSG string representation."""
        return self.epsg_code or self.crs_string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'crs_string': self.crs_string,
            'epsg_code': self.epsg_code,
            'name': self.name,
            'unit': self.unit,
            'is_geographic': self.is_geographic
        }
    
    def __repr__(self) -> str:
        return f"CRS({self.epsg_code or self.name})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CRS):
            return False
        return self.epsg_code == other.epsg_code


class CoordinateTransformer:
    """
    Transforms coordinates between different CRS.
    Analogous to QGIS QgsCoordinateTransform.
    """
    
    def __init__(self, source_crs: CRS, target_crs: CRS):
        self.source_crs = source_crs
        self.target_crs = target_crs
        self.is_valid = source_crs.is_valid() and target_crs.is_valid()
    
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a single point."""
        if not self.is_valid or self.source_crs == self.target_crs:
            return x, y
        
        # Simplified transformation - real implementation uses proj4/GDAL
        if self.source_crs.is_geographic and not self.target_crs.is_geographic:
            # Geographic to projected (simplified)
            if 'Mercator' in self.target_crs.name or 'Web' in self.target_crs.name:
                # Web Mercator approximation
                x_out = x * 20037508.34 / 180.0
                y_out = (180 / 3.14159265) * np.log(np.tan((90 + y) * 3.14159265 / 360))
                return x_out, y_out
        
        return x, y
    
    def transform_points(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Transform multiple points."""
        return [self.transform_point(x, y) for x, y in points]
    
    def transform_extent(self, extent) -> 'Extent':
        """Transform extent to target CRS."""
        from .layer import Extent
        
        corners = [
            (extent.xmin, extent.ymin),
            (extent.xmax, extent.ymax)
        ]
        transformed = self.transform_points(corners)
        
        return Extent(
            xmin=min(p[0] for p in transformed),
            ymin=min(p[1] for p in transformed),
            xmax=max(p[0] for p in transformed),
            ymax=max(p[1] for p in transformed),
            zmin=extent.zmin,
            zmax=extent.zmax
        )
    
    def __repr__(self) -> str:
        return f"CoordinateTransform({self.source_crs} -> {self.target_crs})"


import numpy as np
