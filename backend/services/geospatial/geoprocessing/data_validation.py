"""
Data Validation and Quality Assurance Module.
Topology validation, data quality checks, and repair tools.

Features:
- Geometry validation
- Topology checking
- Duplicate detection
- Attribute validation
- Data repair utilities
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate spatial data quality."""
    
    def __init__(self, gdf: GeoDataFrame):
        self.gdf = gdf
        self.issues: List[Dict[str, Any]] = []
    
    def validate_geometries(self) -> Dict[str, Any]:
        """
        Validate all geometries.
        
        Returns:
            Validation report
        """
        try:
            report = {
                'total_features': len(self.gdf),
                'valid_geometries': 0,
                'invalid_geometries': [],
                'empty_geometries': [],
                'self_intersecting': [],
                'issues': []
            }
            
            for idx, row in self.gdf.iterrows():
                geom = row.geometry
                
                # Check if empty
                if geom.is_empty:
                    report['empty_geometries'].append(idx)
                    report['issues'].append({
                        'feature_id': idx,
                        'type': 'empty_geometry',
                        'message': 'Geometry is empty'
                    })
                    continue
                
                # Check if valid
                if not geom.is_valid:
                    report['invalid_geometries'].append(idx)
                    report['issues'].append({
                        'feature_id': idx,
                        'type': 'invalid_geometry',
                        'message': f'Invalid geometry: {geom.geom_type}'
                    })
                    continue
                
                # Check self-intersection
                if geom.geom_type in ['Polygon', 'MultiPolygon']:
                    if not geom.exterior.is_ring:
                        report['self_intersecting'].append(idx)
                        report['issues'].append({
                            'feature_id': idx,
                            'type': 'self_intersecting',
                            'message': 'Geometry self-intersects'
                        })
                        continue
                
                report['valid_geometries'] += 1
            
            return report
            
        except Exception as e:
            logger.error(f"Geometry validation error: {e}")
            raise
    
    def validate_attributes(self) -> Dict[str, Any]:
        """
        Validate attribute data.
        
        Returns:
            Validation report
        """
        try:
            report = {
                'total_attributes': len(self.gdf.columns),
                'missing_values': {},
                'data_type_mismatches': [],
                'invalid_values': []
            }
            
            for column in self.gdf.columns:
                if column == 'geometry':
                    continue
                
                # Check for missing values
                null_count = self.gdf[column].isnull().sum()
                if null_count > 0:
                    report['missing_values'][column] = int(null_count)
            
            return report
            
        except Exception as e:
            logger.error(f"Attribute validation error: {e}")
            raise
    
    def check_duplicates(self) -> List[List[int]]:
        """
        Find duplicate geometries.
        
        Returns:
            List of duplicate groups (each group is list of indices)
        """
        try:
            duplicates = []
            seen = set()
            
            for i in range(len(self.gdf)):
                if i in seen:
                    continue
                
                geom_i = self.gdf.geometry.values[i]  # type: ignore
                duplicates_group = [i]
                
                for j in range(i + 1, len(self.gdf)):
                    if j not in seen:
                        geom_j = self.gdf.geometry.values[j]  # type: ignore
                        
                        # Type guard for equals method
                        if hasattr(geom_i, 'equals') and hasattr(geom_j, 'equals') and geom_i.equals(geom_j):  # type: ignore
                            duplicates_group.append(j)
                            seen.add(j)
                
                if len(duplicates_group) > 1:
                    duplicates.append(duplicates_group)
                    for idx in duplicates_group:
                        seen.add(idx)
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Duplicate detection error: {e}")
            raise
    
    def check_topology(self) -> Dict[str, Any]:
        """
        Check topology of polygon layer.
        
        Returns:
            Topology report
        """
        try:
            report = {
                'gaps': [],
                'overlaps': [],
                'slivers': [],
                'valid_polygons': 0
            }
            
            if not all(self.gdf.geometry.geom_type == 'Polygon'):
                return report
            
            # Check for gaps and overlaps
            union_geom = unary_union(self.gdf.geometry)
            total_area = sum(geom.area for geom in self.gdf.geometry)
            union_area = union_geom.area
            
            if union_area < total_area:
                report['overlaps'].append({
                    'message': 'Overlapping polygons detected',
                    'area_difference': total_area - union_area
                })
            
            # Check for slivers
            for idx, row in self.gdf.iterrows():
                geom = row.geometry
                bounds = geom.bounds
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                
                aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
                
                if aspect_ratio > 100:
                    report['slivers'].append({
                        'feature_id': idx,
                        'aspect_ratio': aspect_ratio
                    })
            
            report['valid_polygons'] = len(self.gdf) - len(report['slivers'])
            
            return report
            
        except Exception as e:
            logger.error(f"Topology check error: {e}")
            raise


class GeometryRepair:
    """Repair invalid geometries."""
    
    @staticmethod
    def fix_invalid(gdf: GeoDataFrame) -> GeoDataFrame:
        """
        Attempt to fix invalid geometries.
        
        Args:
            gdf: Input GeoDataFrame
            
        Returns:
            GeoDataFrame with repaired geometries
        """
        try:
            result = gdf.copy()
            
            fixed_geoms = [
                geom.buffer(0) if not geom.is_valid and not geom.buffer(0).is_empty
                else geom.convex_hull if not geom.is_valid and geom.buffer(0).is_empty
                else geom
                for geom in result.geometry
            ]
            result.geometry = gpd.GeoSeries(fixed_geoms, index=result.index)
            
            return result
            
        except Exception as e:
            logger.error(f"Geometry repair error: {e}")
            raise
    
    @staticmethod
    def remove_duplicates(gdf: GeoDataFrame, keep: str = 'first') -> GeoDataFrame:
        """
        Remove duplicate geometries.
        
        Args:
            gdf: Input GeoDataFrame
            keep: 'first' or 'last'
            
        Returns:
            GeoDataFrame without duplicates
        """
        try:
            result = gdf.copy()
            
            # Create WKT representation for comparison
            wkt_series = result.geometry.to_wkt()
            
            # Drop duplicates based on WKT
            keep_type = 'first' if keep == 'first' else 'last'  # type: ignore
            mask = ~wkt_series.duplicated(keep=keep_type)
            
            return result[mask].reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"Duplicate removal error: {e}")
            raise
    
    @staticmethod
    def snap_vertices(gdf: GeoDataFrame, tolerance: float) -> GeoDataFrame:
        """
        Snap vertices to grid.
        
        Args:
            gdf: Input GeoDataFrame
            tolerance: Snapping tolerance
            
        Returns:
            GeoDataFrame with snapped vertices
        """
        try:
            result = gdf.copy()
            
            def snap_geometry(geom):
                if geom.is_empty:
                    return geom
                
                if geom.geom_type == 'Point':
                    x = round(geom.x / tolerance) * tolerance
                    y = round(geom.y / tolerance) * tolerance
                    return geom.__class__(x, y)
                else:
                    # Snap all coordinates
                    coords = []
                    if hasattr(geom, 'exterior'):
                        # Polygon
                        exterior = [
                            (round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
                            for x, y in geom.exterior.coords
                        ]
                        interiors = [
                            [(round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
                             for x, y in ring.coords]
                            for ring in geom.interiors
                        ]
                        return geom.__class__(exterior, interiors)
                    else:
                        # LineString, etc.
                        snapped_coords = [
                            (round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
                            for x, y in geom.coords
                        ]
                        return geom.__class__(snapped_coords)
            
            result.geometry = result.geometry.apply(snap_geometry)
            
            return result
            
        except Exception as e:
            logger.error(f"Vertex snapping error: {e}")
            raise


# Module exports
__all__ = ['DataValidator', 'GeometryRepair']
