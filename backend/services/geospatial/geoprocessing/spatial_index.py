"""
Spatial Indexing and Query Engine.
R-tree based spatial indexing for fast queries.

Features:
- R-tree spatial indexes
- Nearest neighbor queries
- Range queries
- Spatial relationship testing
- Index optimization
"""

import logging
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass
import numpy as np
from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

# Type alias for geometry types
Geometry = Union[Point, BaseGeometry]
import geopandas as gpd
from geopandas import GeoDataFrame

logger = logging.getLogger(__name__)


@dataclass
class SpatialIndex:
    """Spatial index structure."""
    tree: STRtree
    geometries: List[Geometry]
    features: Dict[int, Any]  # Feature attributes by index


class SpatialIndexer:
    """
    Advanced spatial indexing engine.
    Manages efficient spatial queries.
    """
    
    def __init__(self):
        self.indices: Dict[str, SpatialIndex] = {}
    
    def create_index(
        self,
        gdf: GeoDataFrame,
        name: str = "default"
    ) -> SpatialIndex:
        """
        Create spatial index from GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame to index
            name: Index name
            
        Returns:
            SpatialIndex object
        """
        try:
            geometries = list(gdf.geometry)
            tree = STRtree(geometries)
            
            features = {i: gdf.iloc[i].to_dict() for i in range(len(gdf))}
            
            index = SpatialIndex(
                tree=tree,
                geometries=geometries,
                features=features
            )
            
            self.indices[name] = index
            logger.info(f"Created spatial index '{name}' with {len(geometries)} geometries")
            
            return index
            
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            raise
    
    def get_index(self, name: str) -> Optional[SpatialIndex]:
        """Get spatial index by name."""
        return self.indices.get(name)
    
    def bounds_query(
        self,
        bounds: Tuple[float, float, float, float],
        index_name: str = "default"
    ) -> List[int]:
        """
        Query geometries within bounding box.
        
        Args:
            bounds: (minx, miny, maxx, maxy)
            index_name: Index name
            
        Returns:
            List of geometry indices
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            query_box = box(*bounds)
            results = list(index.tree.query(query_box))
            
            return results
            
        except Exception as e:
            logger.error(f"Bounds query error: {e}")
            raise
    
    def contains_query(
        self,
        geometry: Geometry,
        index_name: str = "default"
    ) -> List[int]:
        """
        Find geometries that contain point/geometry.
        
        Args:
            geometry: Query geometry
            index_name: Index name
            
        Returns:
            List of geometry indices
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            results = []
            candidates = list(index.tree.query(geometry, predicate='intersects'))
            
            for idx in candidates:
                if index.geometries[idx].contains(geometry):
                    results.append(idx)
            
            return results
            
        except Exception as e:
            logger.error(f"Contains query error: {e}")
            raise
    
    def within_query(
        self,
        geometry: Geometry,
        index_name: str = "default"
    ) -> List[int]:
        """
        Find geometries within geometry.
        
        Args:
            geometry: Query geometry
            index_name: Index name
            
        Returns:
            List of geometry indices
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            results = []
            candidates = list(index.tree.query(geometry, predicate='intersects'))
            
            for idx in candidates:
                if index.geometries[idx].within(geometry):
                    results.append(idx)
            
            return results
            
        except Exception as e:
            logger.error(f"Within query error: {e}")
            raise
    
    def intersects_query(
        self,
        geometry: Geometry,
        index_name: str = "default"
    ) -> List[int]:
        """
        Find geometries intersecting with geometry.
        
        Args:
            geometry: Query geometry
            index_name: Index name
            
        Returns:
            List of geometry indices
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            return list(index.tree.query(geometry, predicate='intersects'))
            
        except Exception as e:
            logger.error(f"Intersects query error: {e}")
            raise
    
    def nearest_neighbor(
        self,
        geometry: Geometry,
        k: int = 1,
        max_distance: Optional[float] = None,
        index_name: str = "default"
    ) -> List[Tuple[int, float]]:
        """
        Find k nearest neighbors.
        
        Args:
            geometry: Query geometry (usually point)
            k: Number of neighbors
            max_distance: Maximum search distance
            index_name: Index name
            
        Returns:
            List of (index, distance) tuples
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            results = []
            
            for idx, geom in enumerate(index.geometries):
                distance = geometry.distance(geom)
                
                if max_distance is None or distance <= max_distance:
                    results.append((idx, distance))
            
            # Sort by distance and take k nearest
            results.sort(key=lambda x: x[1])
            return results[:k]
            
        except Exception as e:
            logger.error(f"Nearest neighbor error: {e}")
            raise
    
    def knn_query(
        self,
        point: Point,
        k: int = 1,
        index_name: str = "default"
    ) -> GeoDataFrame:
        """
        K-nearest neighbor query returning full features.
        
        Args:
            point: Query point
            k: Number of neighbors
            index_name: Index name
            
        Returns:
            GeoDataFrame with k nearest features
        """
        try:
            neighbors = self.nearest_neighbor(point, k=k, index_name=index_name)
            index = self.get_index(index_name)
            
            features = []
            if index and index.features:
                for idx, distance in neighbors:
                    feature = index.features[idx].copy()  # type: ignore
                    feature['distance'] = distance
                    features.append(feature)
            
            return gpd.GeoDataFrame(features)
            
        except Exception as e:
            logger.error(f"KNN query error: {e}")
            raise
    
    def distance_buffer_query(
        self,
        geometry: Geometry,
        distance: float,
        index_name: str = "default"
    ) -> List[int]:
        """
        Find geometries within distance buffer.
        
        Args:
            geometry: Reference geometry
            distance: Buffer distance
            index_name: Index name
            
        Returns:
            List of geometry indices
        """
        try:
            index = self.get_index(index_name)
            if not index:
                raise ValueError(f"Index '{index_name}' not found")
            
            buffer_geom = geometry.buffer(distance)
            return list(index.tree.query(buffer_geom, predicate='intersects'))
            
        except Exception as e:
            logger.error(f"Distance buffer query error: {e}")
            raise
    
    def aggregate_nearby(
        self,
        gdf: GeoDataFrame,
        distance: float,
        index_name: str = "default"
    ) -> List[List[int]]:
        """
        Find clusters of nearby geometries.
        
        Args:
            gdf: Input GeoDataFrame
            distance: Clustering distance
            index_name: Index name
            
        Returns:
            List of clusters (each cluster is list of indices)
        """
        try:
            clusters = []
            visited = set()
            
            for idx in range(len(gdf)):
                if idx in visited:
                    continue
                
                cluster = [idx]
                visited.add(idx)
                
                neighbors = self.distance_buffer_query(
                    gdf.geometry.iloc[idx],  # type: ignore
                    distance,
                    index_name
                )
                
                for neighbor_idx in neighbors:
                    if neighbor_idx not in visited:
                        cluster.append(neighbor_idx)
                        visited.add(neighbor_idx)
                
                if len(cluster) > 1:
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Aggregate nearby error: {e}")
            raise


class SpatialQuery:
    """
    Advanced spatial query builder.
    Supports complex spatial queries with multiple conditions.
    """
    
    def __init__(self, indexer: SpatialIndexer):
        self.indexer = indexer
        self.predicates = []
    
    def add_predicate(
        self,
        geometry: Union[Point, BaseGeometry],
        predicate: str = 'intersects'
    ) -> 'SpatialQuery':
        """
        Add spatial predicate to query.
        
        Args:
            geometry: Query geometry
            predicate: 'intersects', 'contains', 'within', 'crosses'
            
        Returns:
            Self for chaining
        """
        self.predicates.append({
            'geometry': geometry,
            'predicate': predicate
        })
        return self
    
    def execute(self, index_name: str = "default") -> List[int]:
        """
        Execute query with all predicates.
        
        Args:
            index_name: Index name
            
        Returns:
            List of matching geometry indices
        """
        if not self.predicates:
            return []
        
        index = self.indexer.get_index(index_name)
        if not index or not index.geometries:
            return []
        
        results = set(range(len(index.geometries)))
        
        for pred in self.predicates:
            if pred['predicate'] == 'intersects':
                subset = set(self.indexer.intersects_query(
                    pred['geometry'], index_name
                ))
            elif pred['predicate'] == 'contains':
                subset = set(self.indexer.contains_query(
                    pred['geometry'], index_name
                ))
            elif pred['predicate'] == 'within':
                subset = set(self.indexer.within_query(
                    pred['geometry'], index_name
                ))
            else:
                continue
            
            results = results.intersection(subset)
        
        return sorted(list(results))


# Module exports
__all__ = ['SpatialIndexer', 'SpatialIndex', 'SpatialQuery']
