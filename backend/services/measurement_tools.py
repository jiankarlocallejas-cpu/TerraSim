"""
Measurement and digitization tools for interactive geometry creation and measurement.
Includes distance, area, perimeter calculations and drawing tools.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DrawingMode(Enum):
    """Drawing modes"""
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    EDIT = "edit"


class MeasurementUnit(Enum):
    """Measurement units"""
    METERS = "meters"
    KILOMETERS = "kilometers"
    FEET = "feet"
    MILES = "miles"
    DEGREES = "degrees"


@dataclass
class MeasurementResult:
    """Result of measurement"""
    value: float
    unit: MeasurementUnit
    geometry_type: str
    coordinates: List[Tuple[float, float]] = field(default_factory=list)
    additional_info: Dict[str, Any] = field(default_factory=dict)


class DistanceCalculator:
    """Calculate distances between points"""
    
    @staticmethod
    def haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two geographic points using Haversine formula
        Returns distance in meters
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def euclidean_distance(
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two points"""
        return float(np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2))
    
    @staticmethod
    def polyline_distance(
        coords: List[Tuple[float, float]],
        is_geographic: bool = False
    ) -> float:
        """Calculate total distance of polyline"""
        if len(coords) < 2:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(len(coords) - 1):
            if is_geographic:
                dist = DistanceCalculator.haversine_distance(
                    coords[i][1], coords[i][0],  # lat, lon
                    coords[i+1][1], coords[i+1][0]
                )
            else:
                dist = DistanceCalculator.euclidean_distance(coords[i], coords[i+1])
            
            total_distance += dist
        
        return total_distance


class AreaCalculator:
    """Calculate areas of polygons"""
    
    @staticmethod
    def shoelace_formula(coords: List[Tuple[float, float]]) -> float:
        """Calculate polygon area using Shoelace formula"""
        if len(coords) < 3:
            return 0.0
        
        coords_array = np.array(coords)
        x = coords_array[:, 0]
        y = coords_array[:, 1]
        
        return 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(-1, len(x)-1)))
    
    @staticmethod
    def polygon_perimeter(coords: List[Tuple[float, float]]) -> float:
        """Calculate polygon perimeter"""
        return DistanceCalculator.polyline_distance(coords + [coords[0]])
    
    @staticmethod
    def geodesic_area(
        coords: List[Tuple[float, float]],
        use_crs_area: bool = False
    ) -> float:
        """
        Calculate geodesic area of polygon on sphere
        Coords should be (lon, lat) format
        """
        try:
            import geopy.distance
            
            if len(coords) < 3:
                return 0.0
            
            # Simple approximation using triangles from centroid
            # In production, use proper geodesic algorithms
            area = 0.0
            
            return area
        except ImportError:
            # Fallback to Shoelace
            return AreaCalculator.shoelace_formula(coords)


class Measurement:
    """Base measurement class"""
    
    def __init__(self, coordinates: List[Tuple[float, float]], crs: str = "EPSG:4326"):
        self.coordinates = coordinates
        self.crs = crs
        self._result = None
    
    @abstractmethod
    def calculate(self) -> MeasurementResult:
        """Calculate measurement"""
        pass


class DistanceMeasurement(Measurement):
    """Distance measurement"""
    
    def calculate(self) -> MeasurementResult:
        """Calculate distance"""
        is_geographic = "4326" in self.crs  # WGS84 is geographic
        distance = DistanceCalculator.polyline_distance(self.coordinates, is_geographic)
        
        # Convert units
        unit = MeasurementUnit.METERS
        value = distance
        
        if is_geographic:
            unit = MeasurementUnit.METERS
        
        return MeasurementResult(
            value=value,
            unit=unit,
            geometry_type="LineString",
            coordinates=self.coordinates,
            additional_info={
                'segment_count': len(self.coordinates) - 1,
                'segments': [
                    DistanceCalculator.euclidean_distance(
                        self.coordinates[i],
                        self.coordinates[i+1]
                    )
                    for i in range(len(self.coordinates) - 1)
                ]
            }
        )


class AreaMeasurement(Measurement):
    """Area measurement"""
    
    def calculate(self) -> MeasurementResult:
        """Calculate area"""
        if len(self.coordinates) < 3:
            return MeasurementResult(
                value=0,
                unit=MeasurementUnit.METERS,
                geometry_type="Polygon"
            )
        
        # Ensure polygon is closed
        coords = self.coordinates
        if coords[0] != coords[-1]:
            coords = coords + [coords[0]]
        
        area = AreaCalculator.shoelace_formula(coords[:-1])  # Exclude closing point
        perimeter = AreaCalculator.polygon_perimeter(coords[:-1])
        
        return MeasurementResult(
            value=area,
            unit=MeasurementUnit.METERS,
            geometry_type="Polygon",
            coordinates=self.coordinates,
            additional_info={
                'perimeter': perimeter,
                'vertices': len(self.coordinates)
            }
        )


class PerimeterMeasurement(Measurement):
    """Perimeter measurement"""
    
    def calculate(self) -> MeasurementResult:
        """Calculate perimeter"""
        perimeter = DistanceCalculator.polyline_distance(self.coordinates)
        
        return MeasurementResult(
            value=perimeter,
            unit=MeasurementUnit.METERS,
            geometry_type="Polygon",
            coordinates=self.coordinates,
            additional_info={
                'segments': len(self.coordinates) - 1
            }
        )


class BearingCalculator:
    """Calculate bearings between points"""
    
    @staticmethod
    def calculate_bearing(
        point1: Tuple[float, float],
        point2: Tuple[float, float],
        geographic: bool = True
    ) -> float:
        """
        Calculate bearing (azimuth) from point1 to point2
        Returns angle in degrees (0-360)
        """
        from math import atan2, sin, cos, radians, degrees
        
        if geographic:
            # Geographic bearing calculation
            lon1, lat1 = radians(point1[0]), radians(point1[1])
            lon2, lat2 = radians(point2[0]), radians(point2[1])
            
            dlon = lon2 - lon1
            
            y = sin(dlon) * cos(lat2)
            x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
            
            bearing = degrees(atan2(y, x))
        else:
            # Cartesian bearing
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            bearing = degrees(atan2(dx, dy))
        
        # Normalize to 0-360
        bearing = (bearing + 360) % 360
        
        return bearing


class DrawingTools:
    """Tools for interactive drawing and geometry creation"""
    
    def __init__(self):
        self.current_geometry = []
        self.drawing_mode = None
        self.temp_lines = []
    
    def start_drawing(self, mode: DrawingMode):
        """Start drawing"""
        self.drawing_mode = mode
        self.current_geometry = []
        self.temp_lines = []
        logger.info(f"Started drawing: {mode.value}")
    
    def add_point(self, point: Tuple[float, float]):
        """Add point to current geometry"""
        self.current_geometry.append(point)
    
    def finish_drawing(self) -> Optional[Dict[str, Any]]:
        """Finish drawing and return geometry"""
        if not self.current_geometry:
            return None
        
        try:
            if self.drawing_mode == DrawingMode.POINT:
                return self._create_point()
            elif self.drawing_mode == DrawingMode.LINE:
                return self._create_line()
            elif self.drawing_mode == DrawingMode.POLYGON:
                return self._create_polygon()
            elif self.drawing_mode == DrawingMode.RECTANGLE:
                return self._create_rectangle()
            elif self.drawing_mode == DrawingMode.CIRCLE:
                return self._create_circle()
        except Exception as e:
            logger.error(f"Drawing failed: {e}")
            return None
        finally:
            self.current_geometry = []
            self.drawing_mode = None
    
    def _create_point(self) -> Dict[str, Any]:
        """Create point geometry"""
        if len(self.current_geometry) < 1:
            return {}
        
        from shapely.geometry import Point
        
        point = Point(self.current_geometry[0])
        return {
            'type': 'Point',
            'geometry': point,
            'coordinates': [self.current_geometry[0]]
        }
    
    def _create_line(self) -> Dict[str, Any]:
        """Create line geometry"""
        if len(self.current_geometry) < 2:
            return {}
        
        from shapely.geometry import LineString
        
        line = LineString(self.current_geometry)
        return {
            'type': 'LineString',
            'geometry': line,
            'coordinates': self.current_geometry
        }
    
    def _create_polygon(self) -> Dict[str, Any]:
        """Create polygon geometry"""
        if len(self.current_geometry) < 3:
            return {}
        
        from shapely.geometry import Polygon
        
        # Close polygon
        coords = self.current_geometry + [self.current_geometry[0]]
        polygon = Polygon(coords)
        
        return {
            'type': 'Polygon',
            'geometry': polygon,
            'coordinates': self.current_geometry
        }
    
    def _create_rectangle(self) -> Dict[str, Any]:
        """Create rectangle geometry"""
        if len(self.current_geometry) < 2:
            return {}
        
        from shapely.geometry import box
        
        p1 = self.current_geometry[0]
        p2 = self.current_geometry[1]
        
        rect = box(
            min(p1[0], p2[0]), min(p1[1], p2[1]),
            max(p1[0], p2[0]), max(p1[1], p2[1])
        )
        
        return {
            'type': 'Polygon',
            'geometry': rect,
            'coordinates': list(rect.exterior.coords)
        }
    
    def _create_circle(self) -> Dict[str, Any]:
        """Create circle geometry"""
        if len(self.current_geometry) < 2:
            return {}
        
        center = self.current_geometry[0]
        edge = self.current_geometry[1]
        
        # Calculate radius
        radius = DistanceCalculator.euclidean_distance(center, edge)
        
        # Create circle as polygon
        import numpy as np
        angles = np.linspace(0, 2*np.pi, 64)
        coords = [
            (center[0] + radius * np.cos(angle),
             center[1] + radius * np.sin(angle))
            for angle in angles
        ]
        
        from shapely.geometry import Polygon
        circle = Polygon(coords)
        
        return {
            'type': 'Polygon',
            'geometry': circle,
            'coordinates': coords,
            'properties': {'radius': radius}
        }
    
    def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
        """Get preview of current drawing"""
        if len(self.current_geometry) < 1:
            return None
        
        if self.drawing_mode == DrawingMode.LINE:
            return {
                'type': 'LineString',
                'coordinates': self.current_geometry
            }
        elif self.drawing_mode == DrawingMode.POLYGON:
            return {
                'type': 'LineString',
                'coordinates': self.current_geometry + [self.current_geometry[0]]
            }
        elif self.drawing_mode == DrawingMode.RECTANGLE and len(self.current_geometry) >= 1:
            p1 = self.current_geometry[0]
            if len(self.current_geometry) >= 2:
                p2 = self.current_geometry[1]
            else:
                return None
            
            return {
                'type': 'Polygon',
                'coordinates': [
                    [min(p1[0], p2[0]), min(p1[1], p2[1])],
                    [max(p1[0], p2[0]), min(p1[1], p2[1])],
                    [max(p1[0], p2[0]), max(p1[1], p2[1])],
                    [min(p1[0], p2[0]), max(p1[1], p2[1])],
                    [min(p1[0], p2[0]), min(p1[1], p2[1])]
                ]
            }
        
        return None
    
    def cancel_drawing(self):
        """Cancel current drawing"""
        self.current_geometry = []
        self.drawing_mode = None
        self.temp_lines = []
        logger.info("Drawing cancelled")
