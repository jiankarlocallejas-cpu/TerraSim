"""
Spatial queries and feature filtering system.
Supports spatial relationships, attribute filtering, and advanced queries.
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class SpatialRelation(Enum):
    """Spatial relationship types"""
    INTERSECTS = "intersects"
    CONTAINS = "contains"
    WITHIN = "within"
    CROSSES = "crosses"
    TOUCHES = "touches"
    OVERLAPS = "overlaps"
    EQUALS = "equals"
    DISJOINT = "disjoint"
    DISTANCE = "distance"


class FilterOperator(Enum):
    """Filter operators for attribute queries"""
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    NOT_LIKE = "not_like"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class SpatialQuery:
    """Spatial query specification"""
    relation: SpatialRelation
    geometry: Any
    distance: Optional[float] = None
    
    def execute(self, features: List[Any]) -> List[int]:
        """Execute spatial query on features"""
        results = []
        
        for i, feature in enumerate(features):
            if self._check_relation(feature.geometry):
                results.append(i)
        
        return results
    
    def _check_relation(self, geometry: Any) -> bool:
        """Check if geometry satisfies spatial relation"""
        try:
            if self.relation == SpatialRelation.INTERSECTS:
                return geometry.intersects(self.geometry)
            elif self.relation == SpatialRelation.CONTAINS:
                return geometry.contains(self.geometry)
            elif self.relation == SpatialRelation.WITHIN:
                return geometry.within(self.geometry)
            elif self.relation == SpatialRelation.CROSSES:
                return geometry.crosses(self.geometry)
            elif self.relation == SpatialRelation.TOUCHES:
                return geometry.touches(self.geometry)
            elif self.relation == SpatialRelation.OVERLAPS:
                return geometry.overlaps(self.geometry)
            elif self.relation == SpatialRelation.EQUALS:
                return geometry.equals(self.geometry)
            elif self.relation == SpatialRelation.DISJOINT:
                return geometry.disjoint(self.geometry)
            elif self.relation == SpatialRelation.DISTANCE and self.distance is not None:
                return geometry.distance(self.geometry) <= self.distance
            else:
                return False
        except Exception as e:
            logger.error(f"Spatial relation check failed: {e}")
            return False


@dataclass
class AttributeFilter:
    """Attribute-based filter"""
    field: str
    operator: FilterOperator
    value: Any = None
    
    def matches(self, feature: Dict[str, Any]) -> bool:
        """Check if feature matches filter"""
        if self.field not in feature:
            return False
        
        feature_value = feature[self.field]
        
        try:
            if self.operator == FilterOperator.EQUALS:
                return feature_value == self.value
            elif self.operator == FilterOperator.NOT_EQUALS:
                return feature_value != self.value
            elif self.operator == FilterOperator.LESS_THAN:
                return float(feature_value) < float(self.value)
            elif self.operator == FilterOperator.LESS_EQUAL:
                return float(feature_value) <= float(self.value)
            elif self.operator == FilterOperator.GREATER_THAN:
                return float(feature_value) > float(self.value)
            elif self.operator == FilterOperator.GREATER_EQUAL:
                return float(feature_value) >= float(self.value)
            elif self.operator == FilterOperator.IN:
                return feature_value in self.value
            elif self.operator == FilterOperator.NOT_IN:
                return feature_value not in self.value
            elif self.operator == FilterOperator.LIKE:
                return str(self.value).lower() in str(feature_value).lower()
            elif self.operator == FilterOperator.NOT_LIKE:
                return str(self.value).lower() not in str(feature_value).lower()
            elif self.operator == FilterOperator.IS_NULL:
                return feature_value is None
            elif self.operator == FilterOperator.IS_NOT_NULL:
                return feature_value is not None
            else:
                return False
        except (ValueError, TypeError) as e:
            logger.warning(f"Filter evaluation failed: {e}")
            return False


class QueryBuilder:
    """Build complex queries with spatial and attribute conditions"""
    
    def __init__(self):
        self.spatial_queries: List[SpatialQuery] = []
        self.attribute_filters: List[AttributeFilter] = []
        self.combine_with_and = True
    
    def add_spatial_query(self, query: SpatialQuery) -> 'QueryBuilder':
        """Add spatial query"""
        self.spatial_queries.append(query)
        return self
    
    def add_attribute_filter(self, filter: AttributeFilter) -> 'QueryBuilder':
        """Add attribute filter"""
        self.attribute_filters.append(filter)
        return self
    
    def set_combine_and(self, use_and: bool = True) -> 'QueryBuilder':
        """Set combination logic (AND/OR)"""
        self.combine_with_and = use_and
        return self
    
    def execute(self, features: List[Any], feature_data: Optional[List[Dict]] = None) -> List[int]:
        """Execute combined query"""
        if not features:
            return []
        
        # Start with all feature indices
        result_indices = set(range(len(features)))
        
        # Apply spatial queries
        for spatial_query in self.spatial_queries:
            spatial_results = set(spatial_query.execute(features))
            
            if self.combine_with_and:
                result_indices &= spatial_results
            else:
                result_indices |= spatial_results
        
        # Apply attribute filters
        if feature_data:
            for i, attr_dict in enumerate(feature_data):
                matches_all = True
                for attr_filter in self.attribute_filters:
                    if not attr_filter.matches(attr_dict):
                        matches_all = False
                        break
                
                if self.combine_with_and and not matches_all:
                    result_indices.discard(i)
                elif not self.combine_with_and and matches_all:
                    result_indices.add(i)
        
        return sorted(list(result_indices))


class FeatureFilter:
    """Feature filtering with support for complex conditions"""
    
    def __init__(self, features: List[Dict[str, Any]]):
        self.features = features
    
    def filter_by_attribute(
        self,
        field: str,
        operator: FilterOperator,
        value: Any
    ) -> List[int]:
        """Filter features by attribute"""
        results = []
        filter_obj = AttributeFilter(field, operator, value)
        
        for i, feature in enumerate(self.features):
            if filter_obj.matches(feature):
                results.append(i)
        
        return results
    
    def filter_by_condition(self, condition: Callable[[Dict[str, Any]], bool]) -> List[int]:
        """Filter features by custom condition function"""
        results = []
        
        for i, feature in enumerate(self.features):
            try:
                if condition(feature):
                    results.append(i)
            except Exception as e:
                logger.warning(f"Condition evaluation failed: {e}")
        
        return results
    
    def filter_by_range(self, field: str, min_val: float, max_val: float) -> List[int]:
        """Filter features where field value is in range"""
        results = []
        
        for i, feature in enumerate(self.features):
            try:
                value = float(feature.get(field, 0))
                if min_val <= value <= max_val:
                    results.append(i)
            except (ValueError, TypeError):
                pass
        
        return results
    
    def filter_unique(self, field: str) -> Dict[Any, List[int]]:
        """Group features by unique values of field"""
        groups: Dict[Any, List[int]] = {}
        
        for i, feature in enumerate(self.features):
            value = feature.get(field)
            if value not in groups:
                groups[value] = []
            groups[value].append(i)
        
        return groups
    
    def get_statistics(self, field: str) -> Dict[str, float]:
        """Calculate statistics for numeric field"""
        values = []
        
        for feature in self.features:
            try:
                value = float(feature.get(field, 0))
                values.append(value)
            except (ValueError, TypeError):
                pass
        
        if not values:
            return {}
        
        values_array = np.array(values)
        
        return {
            'count': len(values),
            'min': float(values_array.min()),
            'max': float(values_array.max()),
            'mean': float(values_array.mean()),
            'median': float(np.median(values_array)),
            'std_dev': float(values_array.std()),
            'sum': float(values_array.sum())
        }


class SpatialIndex:
    """Spatial index for efficient queries"""
    
    def __init__(self):
        try:
            from rtree import index as rtree_index_module
            self.idx = rtree_index_module.Index()
            self.rtree_available = True
        except ImportError:
            self.idx = None
            self.rtree_available = False
            logger.warning("rtree not available - spatial indexing disabled")
        
        self.features = []
    
    def add_feature(self, feature_id: int, bounds: Tuple[float, float, float, float]):
        """Add feature to spatial index"""
        if self.rtree_available and self.idx is not None:
            self.features.append(feature_id)
            self.idx.insert(feature_id, bounds)
    
    def query_bounds(self, bounds: Tuple[float, float, float, float]) -> List[int]:
        """Query features intersecting bounds"""
        if not self.rtree_available or self.idx is None:
            return []
        
        xmin, xmax, ymin, ymax = bounds
        return list(self.idx.intersection((xmin, ymin, xmax, ymax)))
    
    def query_point(self, x: float, y: float) -> List[int]:
        """Query features at point"""
        if not self.rtree_available or self.idx is None:
            return []
        
        return list(self.idx.intersection((x, y, x, y)))
    
    def nearest(self, x: float, y: float, count: int = 1) -> List[int]:
        """Find nearest features to point"""
        if not self.rtree_available or self.idx is None:
            return []
        
        try:
            return list(self.idx.nearest((x, y, x, y), count))
        except Exception as e:
            logger.error(f"Nearest query failed: {e}")
            return []
    
    def clear(self):
        """Clear index"""
        if self.rtree_available:
            try:
                from rtree import index as rtree_index_module
                self.idx = rtree_index_module.Index()
            except ImportError:
                self.idx = None
        self.features.clear()
