"""
Coordinate Reference System (CRS) management and transformations.
Supports on-the-fly projection, datum transformation, and CRS definition.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class CRSType(Enum):
    """CRS Authority types"""
    EPSG = "EPSG"
    ESRI = "ESRI"
    OGC = "OGC"
    CUSTOM = "CUSTOM"


@dataclass
class CRSDefinition:
    """CRS definition and properties"""
    code: str
    authority: CRSType
    name: str
    description: str = ""
    proj_string: str = ""
    is_geographic: bool = False
    is_projected: bool = False
    units: str = "meters"
    datum: str = ""
    ellipsoid: str = ""
    
    def __hash__(self):
        return hash(self.code)
    
    def __eq__(self, other):
        if isinstance(other, CRSDefinition):
            return self.code == other.code and self.authority == other.authority
        return False


class CRSManager:
    """High-performance CRS management and transformations"""
    
    # Common CRS definitions
    COMMON_CRS = {
        "EPSG:4326": CRSDefinition(
            code="4326",
            authority=CRSType.EPSG,
            name="WGS 84",
            description="World Geodetic System 1984 (geographic)",
            is_geographic=True,
            units="degrees",
            datum="WGS84",
            ellipsoid="WGS 84"
        ),
        "EPSG:3857": CRSDefinition(
            code="3857",
            authority=CRSType.EPSG,
            name="Web Mercator",
            description="Spherical Mercator (web mapping)",
            is_projected=True,
            units="meters",
            datum="WGS84"
        ),
        "EPSG:32633": CRSDefinition(
            code="32633",
            authority=CRSType.EPSG,
            name="WGS 84 / UTM zone 33N",
            description="Universal Transverse Mercator zone 33 North",
            is_projected=True,
            units="meters",
            datum="WGS84"
        ),
    }
    
    def __init__(self):
        self.crs_cache: Dict[str, CRSDefinition] = self.COMMON_CRS.copy()
        self.transformer_cache: Dict[Tuple[str, str], Any] = {}
        
        try:
            import pyproj
            self.pyproj_available = True
            self.pyproj = pyproj
        except ImportError:
            self.pyproj_available = False
            logger.warning("pyproj not available - CRS transformations limited")
    
    def register_crs(self, crs_code: str, crs_def: CRSDefinition) -> bool:
        """Register a new CRS definition"""
        if crs_code in self.crs_cache:
            logger.warning(f"CRS {crs_code} already registered")
            return False
        
        self.crs_cache[crs_code] = crs_def
        return True
    
    def get_crs(self, crs_code: str) -> Optional[CRSDefinition]:
        """Get CRS definition"""
        return self.crs_cache.get(crs_code)
    
    def list_crs(self, pattern: Optional[str] = None) -> List[CRSDefinition]:
        """List available CRS definitions, optionally filtered by pattern"""
        if pattern is None:
            return list(self.crs_cache.values())
        
        pattern_lower = pattern.lower()
        return [
            crs for crs in self.crs_cache.values()
            if pattern_lower in crs.code.lower() or pattern_lower in crs.name.lower()
        ]
    
    def create_transformer(self, from_crs: str, to_crs: str) -> Optional[Any]:
        """Create a coordinate transformer between two CRS"""
        if not self.pyproj_available:
            logger.error("pyproj not available for transformation")
            return None
        
        cache_key = (from_crs, to_crs)
        
        # Check cache
        if cache_key in self.transformer_cache:
            return self.transformer_cache[cache_key]
        
        try:
            transformer = self.pyproj.Transformer.from_crs(
                from_crs, to_crs, always_xy=True
            )
            self.transformer_cache[cache_key] = transformer
            return transformer
        except Exception as e:
            logger.error(f"Failed to create transformer {from_crs} -> {to_crs}: {e}")
            return None
    
    def transform_coordinates(
        self,
        coords: np.ndarray,
        from_crs: str,
        to_crs: str
    ) -> Optional[np.ndarray]:
        """
        Transform coordinates from one CRS to another
        
        Args:
            coords: Nx2 array of [x, y] or Nx3 array of [x, y, z]
            from_crs: Source CRS code
            to_crs: Target CRS code
        
        Returns:
            Transformed coordinates or None on error
        """
        if from_crs == to_crs:
            return coords
        
        transformer = self.create_transformer(from_crs, to_crs)
        if transformer is None:
            return None
        
        try:
            if coords.shape[1] == 2:
                x, y = transformer.transform(coords[:, 0], coords[:, 1])
                return np.column_stack([x, y])
            elif coords.shape[1] == 3:
                x, y, z = transformer.transform(coords[:, 0], coords[:, 1], coords[:, 2])
                return np.column_stack([x, y, z])
            else:
                logger.error("Invalid coordinate dimensions")
                return None
        except Exception as e:
            logger.error(f"Coordinate transformation failed: {e}")
            return None
    
    def transform_geometry(self, geometry: Any, from_crs: str, to_crs: str) -> Optional[Any]:
        """
        Transform a Shapely geometry from one CRS to another
        
        Args:
            geometry: Shapely geometry object
            from_crs: Source CRS code
            to_crs: Target CRS code
        
        Returns:
            Transformed geometry or None on error
        """
        if from_crs == to_crs:
            return geometry
        
        try:
            from shapely.geometry import shape, Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
            from shapely.ops import transform as shapely_transform
            
            transformer = self.create_transformer(from_crs, to_crs)
            if transformer is None:
                return None
            
            def transform_func(x, y, z=None):
                if z is None:
                    new_x, new_y = transformer.transform(x, y)
                    return new_x, new_y
                else:
                    new_x, new_y, new_z = transformer.transform(x, y, z)
                    return new_x, new_y, new_z
            
            return shapely_transform(transform_func, geometry)
        except Exception as e:
            logger.error(f"Geometry transformation failed: {e}")
            return None
    
    def transform_bounds(
        self,
        bounds: Tuple[float, float, float, float],
        from_crs: str,
        to_crs: str
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Transform bounding box from one CRS to another
        
        Args:
            bounds: (xmin, xmax, ymin, ymax)
            from_crs: Source CRS code
            to_crs: Target CRS code
        
        Returns:
            Transformed bounds
        """
        if from_crs == to_crs:
            return bounds
        
        try:
            # Create corners of bounding box
            xmin, xmax, ymin, ymax = bounds
            corners = np.array([
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax]
            ])
            
            # Transform corners
            transformed = self.transform_coordinates(corners, from_crs, to_crs)
            if transformed is None:
                return None
            
            # Get new bounds
            new_xmin = transformed[:, 0].min()
            new_xmax = transformed[:, 0].max()
            new_ymin = transformed[:, 1].min()
            new_ymax = transformed[:, 1].max()
            
            return (new_xmin, new_xmax, new_ymin, new_ymax)
        except Exception as e:
            logger.error(f"Bounds transformation failed: {e}")
            return None
    
    def get_crs_info(self, crs_code: str) -> Dict[str, Any]:
        """Get detailed information about a CRS"""
        if not self.pyproj_available:
            crs_def = self.get_crs(crs_code)
            if crs_def:
                return {
                    'code': crs_def.code,
                    'name': crs_def.name,
                    'description': crs_def.description,
                    'is_geographic': crs_def.is_geographic,
                    'is_projected': crs_def.is_projected,
                    'units': crs_def.units,
                    'datum': crs_def.datum,
                    'ellipsoid': crs_def.ellipsoid
                }
            return {}
        
        try:
            crs_obj = self.pyproj.CRS.from_string(crs_code)
            return {
                'code': crs_code,
                'name': crs_obj.to_string(),
                'is_geographic': crs_obj.is_geographic,
                'is_projected': crs_obj.is_projected,
                'to_string': crs_obj.to_string(),
                'to_authority': crs_obj.to_authority(),
                'area_of_use': str(crs_obj.area_of_use) if crs_obj.area_of_use else None
            }
        except Exception as e:
            logger.error(f"Failed to get CRS info for {crs_code}: {e}")
            return {}
    
    def auto_detect_crs(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Auto-detect CRS from file metadata"""
        try:
            # Check common metadata keys
            if 'crs' in metadata:
                crs_obj = metadata['crs']
                if hasattr(crs_obj, 'to_string'):
                    return crs_obj.to_string()
                return str(crs_obj)
            
            if 'epsg' in metadata:
                return f"EPSG:{metadata['epsg']}"
            
            if 'prj' in metadata:
                return metadata['prj']
            
            if 'wkt' in metadata:
                # Try to parse WKT
                if self.pyproj_available:
                    crs = self.pyproj.CRS.from_wkt(metadata['wkt'])
                    return crs.to_string()
            
            return None
        except Exception as e:
            logger.warning(f"Failed to auto-detect CRS: {e}")
            return None


class MeasurementCalculator:
    """Calculate measurements in specific units/CRS"""
    
    @staticmethod
    def distance_meters(geom1: Any, geom2: Any, crs: str = "EPSG:4326") -> float:
        """Calculate distance in meters"""
        try:
            if crs == "EPSG:4326":
                # Use Haversine formula for geographic coordinates
                from math import radians, sin, cos, sqrt, atan2
                
                coords1 = list(geom1.coords)[0]
                coords2 = list(geom2.coords)[0]
                
                lon1, lat1 = radians(coords1[0]), radians(coords1[1])
                lon2, lat2 = radians(coords2[0]), radians(coords2[1])
                
                R = 6371000  # Earth radius in meters
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                
                return R * c
            else:
                # Assume projected coordinates in meters
                return geom1.distance(geom2)
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def area_square_meters(geometry: Any, crs: str = "EPSG:4326") -> float:
        """Calculate area in square meters"""
        try:
            if crs == "EPSG:4326":
                # Need to project to get accurate area
                logger.warning("Area calculation for geographic CRS is approximate")
            return geometry.area
        except Exception as e:
            logger.error(f"Area calculation failed: {e}")
            return 0.0
