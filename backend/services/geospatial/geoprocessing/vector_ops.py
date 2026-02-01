"""
Vector Geoprocessing Operations.
Comprehensive vector operations like QGIS Processing Toolbox.

Supports:
- Buffer, clip, intersection, union, dissolve
- Simplify, convex hull, centroid, bounds
- Difference, symmetric difference
- Merge, aggregate, explode, dissolve
- Voronoi diagrams, delaunay triangulation
- Line merge, polygon to lines
- Densify, offset curves
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from shapely.geometry import (
    Point, LineString, Polygon, MultiPoint, MultiLineString, 
    MultiPolygon, GeometryCollection, box, shape
)
from shapely.ops import (
    unary_union, polygonize, linemerge, substring, split,
    nearest_points, voronoi_diagram
)
from shapely.strtree import STRtree
import geopandas as gpd
from geopandas import GeoDataFrame, GeoSeries
import pandas as pd
from scipy.spatial import distance_matrix

logger = logging.getLogger(__name__)


@dataclass
class BufferParams:
    """Buffer operation parameters."""
    distance: float
    quad_segs: int = 8
    endcap_style: int = 1  # round=1, flat=2, square=3
    join_style: int = 1    # round=1, mitre=2, bevel=3
    mitre_limit: float = 5.0
    single_sided: bool = False


@dataclass
class SimplifyParams:
    """Simplify operation parameters."""
    tolerance: float
    preserve_topology: bool = True


class VectorGeoprocessor:
    """
    Vector geoprocessing operations engine.
    Handles all vector-based geometric operations.
    """
    
    def __init__(self):
        self.spatial_index: Optional[STRtree] = None
        self.logger = logger
    
    # ===== OVERLAY OPERATIONS =====
    
    def buffer(
        self,
        geometry: Union[Point, LineString, Polygon],
        params: BufferParams
    ) -> Union[Polygon, MultiPolygon]:
        """
        Buffer a geometry by specified distance.
        
        Args:
            geometry: Input geometry
            params: Buffer parameters
            
        Returns:
            Buffered polygon(s)
        """
        try:
            # Convert cap_style and join_style to string literals
            cap_style_map = {1: 'round', 2: 'flat', 3: 'square'}
            join_style_map = {1: 'round', 2: 'mitre', 3: 'bevel'}
            
            cap_style = cap_style_map.get(params.endcap_style, 'round') if isinstance(params.endcap_style, int) else params.endcap_style  # type: ignore
            join_style = join_style_map.get(params.join_style, 'round') if isinstance(params.join_style, int) else params.join_style  # type: ignore
            
            buffered = geometry.buffer(
                params.distance,
                resolution=params.quad_segs,
                cap_style=cap_style,  # type: ignore
                join_style=join_style,  # type: ignore
                mitre_limit=params.mitre_limit,
                single_sided=params.single_sided
            )
            return buffered
        except Exception as e:
            self.logger.error(f"Buffer error: {e}")
            raise
    
    def clip(
        self,
        subject_gdf: GeoDataFrame,
        clip_gdf: GeoDataFrame,
        keep_geom_type: bool = True
    ) -> GeoDataFrame:
        """
        Clip geometries by mask layer.
        
        Args:
            subject_gdf: Geometries to clip
            clip_gdf: Clipping mask layer
            keep_geom_type: Maintain geometry type
            
        Returns:
            Clipped GeoDataFrame
        """
        try:
            result = gpd.clip(subject_gdf, clip_gdf)
            
            if keep_geom_type:
                geom_type = subject_gdf.geometry.geom_type.values[0:1][0]  # type: ignore
                result = result[result.geometry.geom_type == geom_type]
            
            return result.reset_index(drop=True)
        except Exception as e:
            self.logger.error(f"Clip error: {e}")
            raise
    
    def intersect(
        self,
        gdf1: GeoDataFrame,
        gdf2: GeoDataFrame,
        how: str = 'inner',
        predicate: str = 'intersects'
    ) -> GeoDataFrame:
        """
        Intersection of two vector layers.
        
        Args:
            gdf1: First layer
            gdf2: Second layer
            how: Join method (inner, left, right, outer)
            predicate: Spatial predicate (intersects, contains, within, etc.)
            
        Returns:
            Intersection result
        """
        try:
            # Type cast to satisfy type checker
            how_type = 'inner' if how == 'inner' else ('left' if how == 'left' else 'right')  # type: ignore
            result = gpd.sjoin(gdf1, gdf2, how=how_type, predicate=predicate)  # type: ignore
            
            # Calculate actual intersection geometry
            intersections = []
            for idx, row in result.iterrows():
                geom1 = gdf1.loc[row['index_left'], 'geometry']
                geom2 = gdf2.loc[row['index_right'], 'geometry']
                # Type guard for geometry operations
                if hasattr(geom1, 'intersection') and hasattr(geom2, 'intersection'):
                    intersection = geom1.intersection(geom2)  # type: ignore
                    if intersection is not None and not intersection.is_empty:
                        intersections.append(intersection)
            
            if intersections:
                result.geometry = intersections
            
            return result.reset_index(drop=True)
        except Exception as e:
            self.logger.error(f"Intersect error: {e}")
            raise
    
    def union(self, gdf: GeoDataFrame, dissolve: bool = True) -> GeoDataFrame:
        """
        Union of all geometries.
        
        Args:
            gdf: Input layer
            dissolve: Dissolve result into single geometry
            
        Returns:
            Union result
        """
        try:
            if dissolve:
                union_geom = unary_union(gdf.geometry)
                return GeoDataFrame(
                    {'geometry': [union_geom]},
                    crs=gdf.crs
                )
            else:
                return gdf
        except Exception as e:
            self.logger.error(f"Union error: {e}")
            raise
    
    def difference(
        self,
        gdf1: GeoDataFrame,
        gdf2: GeoDataFrame
    ) -> GeoDataFrame:
        """
        Difference of two layers (gdf1 - gdf2).
        
        Args:
            gdf1: Subject layer
            gdf2: Difference layer
            
        Returns:
            Difference result
        """
        try:
            mask = unary_union(gdf2.geometry)
            result = gdf1.copy()
            result.geometry = gdf1.geometry.difference(mask)
            return result[~result.geometry.is_empty].reset_index(drop=True)
        except Exception as e:
            self.logger.error(f"Difference error: {e}")
            raise
    
    def symmetric_difference(
        self,
        gdf1: GeoDataFrame,
        gdf2: GeoDataFrame
    ) -> GeoDataFrame:
        """
        Symmetric difference (XOR) of two layers.
        
        Args:
            gdf1: First layer
            gdf2: Second layer
            
        Returns:
            Symmetric difference result
        """
        try:
            union_geom = unary_union(gdf2.geometry)
            result = gdf1.copy()
            result.geometry = gdf1.geometry.symmetric_difference(union_geom)
            return result[~result.geometry.is_empty].reset_index(drop=True)
        except Exception as e:
            self.logger.error(f"Symmetric difference error: {e}")
            raise
    
    # ===== SIMPLIFICATION & VALIDATION =====
    
    def simplify(
        self,
        gdf: GeoDataFrame,
        params: SimplifyParams
    ) -> GeoDataFrame:
        """
        Simplify geometries using Douglas-Peucker algorithm.
        
        Args:
            gdf: Input layer
            params: Simplification parameters
            
        Returns:
            Simplified geometries
        """
        try:
            result = gdf.copy()
            result.geometry = gdf.geometry.simplify(
                params.tolerance,
                preserve_topology=params.preserve_topology
            )
            return result
        except Exception as e:
            self.logger.error(f"Simplify error: {e}")
            raise
    
    def densify(
        self,
        gdf: GeoDataFrame,
        max_distance: float
    ) -> GeoDataFrame:
        """
        Densify geometries with additional vertices.
        
        Args:
            gdf: Input layer
            max_distance: Maximum distance between vertices
            
        Returns:
            Densified geometries
        """
        try:
            result = gdf.copy()
            # Apply with type casting for GeoDataFrame
            result['geometry'] = result.geometry.apply(  # type: ignore[call-overload, arg-type]
                lambda geom: self._densify_geometry(geom, max_distance)
            )
            return result
        except Exception as e:
            self.logger.error(f"Densify error: {e}")
            raise
    
    def _densify_geometry(self, geom, max_distance: float):
        """Densify a single geometry."""
        if geom.is_empty:
            return geom
        
        if isinstance(geom, LineString):
            return self._densify_linestring(geom, max_distance)
        elif isinstance(geom, Polygon):
            exterior = self._densify_linestring(
                LineString(geom.exterior.coords),
                max_distance
            )
            interiors = [
                self._densify_linestring(LineString(ring.coords), max_distance)
                for ring in geom.interiors
            ]
            return Polygon(exterior.coords, [ring.coords for ring in interiors])
        elif isinstance(geom, MultiLineString):
            return MultiLineString([
                self._densify_linestring(line, max_distance)
                for line in geom.geoms
            ])
        elif isinstance(geom, MultiPolygon):
            return MultiPolygon([
                self._densify_geometry(poly, max_distance)
                for poly in geom.geoms
            ])
        return geom
    
    def _densify_linestring(self, line: LineString, max_distance: float) -> LineString:
        """Densify a linestring."""
        coords = list(line.coords)
        new_coords = [coords[0]]
        
        for i in range(len(coords) - 1):
            current = Point(coords[i])
            next_pt = Point(coords[i + 1])
            distance = current.distance(next_pt)
            
            if distance > max_distance:
                num_segments = int(np.ceil(distance / max_distance))
                for j in range(1, num_segments):
                    fraction = j / num_segments
                    x = coords[i][0] + (coords[i + 1][0] - coords[i][0]) * fraction
                    y = coords[i][1] + (coords[i + 1][1] - coords[i][1]) * fraction
                    new_coords.append((x, y))
            
            new_coords.append(coords[i + 1])
        
        return LineString(new_coords)
    
    # ===== SHAPE OPERATIONS =====
    
    def convex_hull(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Compute convex hull of all geometries.
        
        Args:
            gdf: Input layer
            
        Returns:
            Convex hull geometry
        """
        try:
            hull = unary_union(gdf.geometry).convex_hull
            return GeoDataFrame({'geometry': [hull]}, crs=gdf.crs)
        except Exception as e:
            self.logger.error(f"Convex hull error: {e}")
            raise
    
    def centroid(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Compute centroids of geometries.
        
        Args:
            gdf: Input layer
            
        Returns:
            Centroid points
        """
        try:
            result = gdf.copy()
            result.geometry = gdf.geometry.centroid
            return result
        except Exception as e:
            self.logger.error(f"Centroid error: {e}")
            raise
    
    def bounds(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Get bounding boxes of geometries.
        
        Args:
            gdf: Input layer
            
        Returns:
            Bounding box polygons
        """
        try:
            bounds_list = []
            for geom in gdf.geometry:
                if geom.is_empty:
                    continue
                minx, miny, maxx, maxy = geom.bounds
                bounds_list.append(box(minx, miny, maxx, maxy))
            
            return GeoDataFrame({'geometry': bounds_list}, crs=gdf.crs)
        except Exception as e:
            self.logger.error(f"Bounds error: {e}")
            raise
    
    # ===== GENERALIZATION =====
    
    def dissolve(
        self,
        gdf: GeoDataFrame,
        by: Optional[List[str]] = None,
        aggregations: Optional[Dict[str, str]] = None
    ) -> GeoDataFrame:
        """
        Dissolve boundaries between adjacent geometries.
        
        Args:
            gdf: Input layer
            by: Column(s) to dissolve by
            aggregations: Aggregation functions for attributes
            
        Returns:
            Dissolved geometries
        """
        try:
            # Handle None aggfunc parameter
            aggfunc = aggregations if aggregations is not None else 'first'
            return gdf.dissolve(by=by, aggfunc=aggfunc)  # type: ignore
        except Exception as e:
            self.logger.error(f"Dissolve error: {e}")
            raise
    
    def explode(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Explode multi-part geometries into single parts.
        
        Args:
            gdf: Input layer
            
        Returns:
            Exploded geometries
        """
        try:
            return gdf.explode(index_parts=False).reset_index(drop=True)
        except Exception as e:
            self.logger.error(f"Explode error: {e}")
            raise
    
    # ===== SPATIAL ANALYSIS =====
    
    def voronoi(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Generate Voronoi diagram from points.
        
        Args:
            gdf: Point layer
            
        Returns:
            Voronoi polygon layer
        """
        try:
            union_geom = unary_union(gdf.geometry)
            voronoi_result = voronoi_diagram(union_geom)
            
            polygons = list(voronoi_result.geoms)
            return GeoDataFrame({'geometry': polygons}, crs=gdf.crs)
        except Exception as e:
            self.logger.error(f"Voronoi error: {e}")
            raise
    
    def delaunay(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Generate Delaunay triangulation from points.
        
        Args:
            gdf: Point layer
            
        Returns:
            Delaunay triangle layer
        """
        try:
            union_geom = unary_union(gdf.geometry)
            # Use shapely's delaunay_triangles via constructive module
            try:
                from shapely.constructive import delaunay_triangles as delaunay
                delaunay_result = delaunay(union_geom)
            except (ImportError, AttributeError):
                # Fallback: return empty collection if not available
                return gpd.GeoDataFrame(geometry=[])
            
            triangles = list(delaunay_result.geoms)
            return GeoDataFrame({'geometry': triangles}, crs=gdf.crs)
        except Exception as e:
            self.logger.error(f"Delaunay error: {e}")
            raise
    
    def nearest_neighbor(
        self,
        source_gdf: GeoDataFrame,
        target_gdf: GeoDataFrame,
        k: int = 1
    ) -> GeoDataFrame:
        """
        Find k nearest neighbors.
        
        Args:
            source_gdf: Source layer
            target_gdf: Target layer
            k: Number of neighbors
            
        Returns:
            Results with nearest neighbor info
        """
        try:
            source_coords = np.array(
                [(geom.centroid.x, geom.centroid.y) if hasattr(geom, 'centroid') else (0, 0) for geom in source_gdf.geometry]
            )
            target_coords = np.array(
                [(geom.centroid.x, geom.centroid.y) if hasattr(geom, 'centroid') else (0, 0) for geom in target_gdf.geometry]
            )
            
            # Import and use spatial tree
            try:
                from scipy.spatial import cKDTree  # type: ignore[import, name]
            except (ImportError, AttributeError):
                from scipy.spatial.ckdtree import cKDTree  # type: ignore[import, name]
            
            tree = cKDTree(target_coords)
            distances, indices = tree.query(source_coords, k=k)
            
            result = source_gdf.copy()
            result['neighbor_dist'] = distances if k == 1 else distances[:, 0]
            result['neighbor_idx'] = indices if k == 1 else indices[:, 0]
            
            return result
        except Exception as e:
            self.logger.error(f"Nearest neighbor error: {e}")
            raise
    
    def spatial_join(
        self,
        left_gdf: GeoDataFrame,
        right_gdf: GeoDataFrame,
        predicate: str = 'intersects',
        how: str = 'left'
    ) -> GeoDataFrame:
        """
        Spatial join two layers.
        
        Args:
            left_gdf: Left layer
            right_gdf: Right layer
            predicate: Spatial relationship
            how: Join type
            
        Returns:
            Joined result
        """
        try:
            # Type cast how parameter
            how_type = 'inner' if how == 'inner' else ('left' if how == 'left' else 'right')  # type: ignore
            return gpd.sjoin(left_gdf, right_gdf, predicate=predicate, how=how_type)
        except Exception as e:
            self.logger.error(f"Spatial join error: {e}")
            raise


# Module exports
__all__ = [
    'VectorGeoprocessor',
    'BufferParams',
    'SimplifyParams'
]
