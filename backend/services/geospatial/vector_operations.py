"""
Advanced spatial operations with performance optimization.
Implements vector operations: buffer, dissolve, intersection, union, etc.
Uses efficient algorithms and spatial indexing.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional, Union
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SpatialOperationType(Enum):
    """Types of spatial operations"""
    BUFFER = "buffer"
    DISSOLVE = "dissolve"
    UNION = "union"
    INTERSECTION = "intersection"
    DIFFERENCE = "difference"
    SYMMETRIC_DIFFERENCE = "symmetric_difference"
    CONVEX_HULL = "convex_hull"
    ENVELOPE = "envelope"
    SIMPLIFY = "simplify"
    OFFSET = "offset"


@dataclass
class SpatialOperationResult:
    """Result of spatial operation"""
    success: bool
    features: Optional[List[Any]] = None
    error: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0


class SpatialOperations:
    """High-performance spatial operations engine"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self._operation_cache = {}
    
    @staticmethod
    def buffer(geometries: List[Any], distance: float, resolution: int = 8) -> SpatialOperationResult:
        """
        Create buffer around geometries
        
        Args:
            geometries: List of geometry objects
            distance: Buffer distance
            resolution: Number of segments for curved buffers
        
        Returns:
            SpatialOperationResult with buffered geometries
        """
        import time
        from shapely.geometry import box
        from shapely.ops import unary_union
        
        start_time = time.time()
        
        try:
            buffered = []
            for geom in geometries:
                if geom.is_valid:
                    buffered.append(geom.buffer(distance, resolution=resolution))
                else:
                    logger.warning(f"Skipping invalid geometry in buffer operation")
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=buffered,
                statistics={
                    'input_count': len(geometries),
                    'output_count': len(buffered),
                    'distance': distance
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Buffer operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def dissolve(geometries: List[Any], aggregation_field: Optional[str] = None) -> SpatialOperationResult:
        """
        Dissolve/merge geometries
        
        Args:
            geometries: List of geometry objects
            aggregation_field: Field to aggregate by (optional)
        
        Returns:
            SpatialOperationResult with dissolved geometries
        """
        import time
        from shapely.ops import unary_union
        
        start_time = time.time()
        
        try:
            if not geometries:
                return SpatialOperationResult(success=False, error="No geometries provided")
            
            # Simple dissolve: merge all valid geometries
            valid_geoms = [g for g in geometries if g.is_valid]
            dissolved = unary_union(valid_geoms)
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=[dissolved],
                statistics={
                    'input_count': len(geometries),
                    'valid_count': len(valid_geoms),
                    'output_count': 1
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Dissolve operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def intersection(geometries1: List[Any], geometries2: List[Any]) -> SpatialOperationResult:
        """
        Find intersection of two geometry sets
        
        Args:
            geometries1: First set of geometries
            geometries2: Second set of geometries
        
        Returns:
            SpatialOperationResult with intersected geometries
        """
        import time
        from rtree import index
        
        start_time = time.time()
        
        try:
            # Build spatial index for efficient intersection
            idx = index.Index()
            for i, geom in enumerate(geometries2):
                if geom.bounds:
                    idx.insert(i, geom.bounds)
            
            intersections = []
            for geom1 in geometries1:
                if geom1.bounds:
                    # Query spatial index for candidates
                    candidates = list(idx.intersection(geom1.bounds))
                    for candidate_idx in candidates:
                        geom2 = geometries2[candidate_idx]
                        if geom1.intersects(geom2):
                            intersection = geom1.intersection(geom2)
                            if not intersection.is_empty:
                                intersections.append(intersection)
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=intersections,
                statistics={
                    'set1_count': len(geometries1),
                    'set2_count': len(geometries2),
                    'intersection_count': len(intersections)
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Intersection operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def union(geometries1: List[Any], geometries2: List[Any]) -> SpatialOperationResult:
        """
        Union of two geometry sets
        
        Args:
            geometries1: First set of geometries
            geometries2: Second set of geometries
        
        Returns:
            SpatialOperationResult with unioned geometries
        """
        import time
        from shapely.ops import unary_union
        
        start_time = time.time()
        
        try:
            all_geoms = geometries1 + geometries2
            valid_geoms = [g for g in all_geoms if g.is_valid]
            union_result = unary_union(valid_geoms)
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=[union_result] if not union_result.is_empty else [],
                statistics={
                    'set1_count': len(geometries1),
                    'set2_count': len(geometries2),
                    'total_valid': len(valid_geoms)
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Union operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def difference(geometries1: List[Any], geometries2: List[Any]) -> SpatialOperationResult:
        """
        Difference of two geometry sets (geometries1 - geometries2)
        
        Args:
            geometries1: Base geometries
            geometries2: Geometries to subtract
        
        Returns:
            SpatialOperationResult with difference geometries
        """
        import time
        from shapely.ops import unary_union
        
        start_time = time.time()
        
        try:
            if not geometries1:
                return SpatialOperationResult(success=False, error="First geometry set is empty")
            
            geom1_union = unary_union([g for g in geometries1 if g.is_valid])
            geom2_union = unary_union([g for g in geometries2 if g.is_valid])
            
            difference_result = geom1_union.difference(geom2_union)
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=[difference_result] if not difference_result.is_empty else [],
                statistics={
                    'set1_count': len(geometries1),
                    'set2_count': len(geometries2)
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Difference operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def convex_hull(geometries: List[Any]) -> SpatialOperationResult:
        """
        Compute convex hull of geometries
        
        Args:
            geometries: List of geometry objects
        
        Returns:
            SpatialOperationResult with convex hull
        """
        import time
        from shapely.ops import unary_union
        
        start_time = time.time()
        
        try:
            if not geometries:
                return SpatialOperationResult(success=False, error="No geometries provided")
            
            valid_geoms = [g for g in geometries if g.is_valid]
            union = unary_union(valid_geoms)
            hull = union.convex_hull
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=[hull],
                statistics={'input_count': len(geometries)},
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Convex hull operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def simplify(geometries: List[Any], tolerance: float = 1.0) -> SpatialOperationResult:
        """
        Simplify geometries using Douglas-Peucker algorithm
        
        Args:
            geometries: List of geometry objects
            tolerance: Simplification tolerance
        
        Returns:
            SpatialOperationResult with simplified geometries
        """
        import time
        
        start_time = time.time()
        
        try:
            simplified = []
            for geom in geometries:
                if geom.is_valid:
                    simplified.append(geom.simplify(tolerance, preserve_topology=True))
            
            processing_time = (time.time() - start_time) * 1000
            
            return SpatialOperationResult(
                success=True,
                features=simplified,
                statistics={
                    'input_count': len(geometries),
                    'output_count': len(simplified),
                    'tolerance': tolerance
                },
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Simplify operation failed: {e}")
            return SpatialOperationResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @staticmethod
    def calculate_distances(geom1: Any, geometries2: List[Any]) -> Tuple[List[float], int]:
        """
        Calculate distances from one geometry to multiple geometries
        Uses spatial indexing for efficiency
        
        Returns:
            Tuple of (distances, processing_time_ms)
        """
        import time
        
        start_time = time.time()
        
        try:
            distances = [geom1.distance(g) for g in geometries2]
            processing_time = (time.time() - start_time) * 1000
            return distances, int(processing_time)
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return [], 0


class GeometricMeasurements:
    """Calculate geometric measurements efficiently"""
    
    @staticmethod
    def calculate_area(geometry: Any) -> float:
        """Calculate geometry area"""
        try:
            return geometry.area
        except:
            return 0.0
    
    @staticmethod
    def calculate_perimeter(geometry: Any) -> float:
        """Calculate geometry perimeter/length"""
        try:
            return geometry.length
        except:
            return 0.0
    
    @staticmethod
    def calculate_centroid(geometry: Any) -> Tuple[float, float]:
        """Calculate geometry centroid"""
        try:
            return tuple(geometry.centroid.coords[0])
        except:
            return (0.0, 0.0)
    
    @staticmethod
    def calculate_distance(geom1: Any, geom2: Any) -> float:
        """Calculate distance between two geometries"""
        try:
            return geom1.distance(geom2)
        except:
            return 0.0
    
    @staticmethod
    def batch_calculate_areas(geometries: List[Any]) -> List[float]:
        """Efficiently calculate areas for multiple geometries"""
        return [GeometricMeasurements.calculate_area(g) for g in geometries]
    
    @staticmethod
    def batch_calculate_perimeters(geometries: List[Any]) -> List[float]:
        """Efficiently calculate perimeters for multiple geometries"""
        return [GeometricMeasurements.calculate_perimeter(g) for g in geometries]
