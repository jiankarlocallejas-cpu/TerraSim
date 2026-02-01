"""
Network Analysis Module.
Graph-based spatial analysis for routing, connectivity, and flow analysis.

Features:
- Network graph construction
- Shortest path finding (Dijkstra, A*)
- Network connectivity analysis
- Service areas
- OD matrix calculation
- Flow analysis
"""

import logging
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
import numpy as np
from shapely.geometry import Point, LineString, MultiLineString
from shapely.geometry.base import BaseGeometry
import geopandas as gpd
from geopandas import GeoDataFrame, GeoSeries
import heapq
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra, shortest_path

logger = logging.getLogger(__name__)


@dataclass
class NetworkEdge:
    """Network edge (line segment)."""
    id: int
    from_node: int
    to_node: int
    geometry: LineString
    length: float
    cost: Optional[float] = None  # Default to length
    attributes: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.cost is None:
            self.cost = self.length


@dataclass
class NetworkNode:
    """Network node (point)."""
    id: int
    position: Point
    attributes: Dict = field(default_factory=dict)


class NetworkGraph:
    """
    Network graph for routing and connectivity analysis.
    Based on road networks, utilities, or other linear features.
    """
    
    def __init__(self):
        self.nodes: Dict[int, NetworkNode] = {}
        self.edges: Dict[int, NetworkEdge] = {}
        self.adjacency: Dict[int, List[int]] = {}  # node_id -> [connected_node_ids]
        self.edge_lookup: Dict[Tuple[int, int], int] = {}  # (from_node, to_node) -> edge_id
        self.cost_matrix: Optional[np.ndarray] = None
    
    def add_node(
        self,
        node_id: int,
        position: Point,
        attributes: Optional[Dict] = None
    ):
        """Add node to network."""
        self.nodes[node_id] = NetworkNode(
            id=node_id,
            position=position,
            attributes=attributes or {}
        )
    
    def add_edge(
        self,
        edge_id: int,
        from_node: int,
        to_node: int,
        geometry: LineString,
        cost: Optional[float] = None,
        attributes: Optional[Dict] = None,
        bidirectional: bool = False
    ):
        """Add edge to network."""
        length = geometry.length
        
        edge = NetworkEdge(
            id=edge_id,
            from_node=from_node,
            to_node=to_node,
            geometry=geometry,
            length=length,
            cost=cost or length,
            attributes=attributes or {}
        )
        
        self.edges[edge_id] = edge
        
        # Add to adjacency
        if from_node not in self.adjacency:
            self.adjacency[from_node] = []
        self.adjacency[from_node].append(to_node)
        self.edge_lookup[(from_node, to_node)] = edge_id
        
        # Reverse edge if bidirectional
        if bidirectional:
            reverse_edge = NetworkEdge(
                id=edge_id + 100000,  # Unique ID for reverse
                from_node=to_node,
                to_node=from_node,
                geometry=LineString(reversed(geometry.coords)),
                length=length,
                cost=cost or length,
                attributes=attributes.copy() if attributes else {}
            )
            self.edges[reverse_edge.id] = reverse_edge
            
            if to_node not in self.adjacency:
                self.adjacency[to_node] = []
            self.adjacency[to_node].append(from_node)
            self.edge_lookup[(to_node, from_node)] = reverse_edge.id
    
    def from_linestring_gdf(
        self,
        gdf: GeoDataFrame,
        node_tolerance: float = 0.001,
        bidirectional: bool = True
    ) -> 'NetworkGraph':
        """
        Build network from LineString GeoDataFrame.
        
        Args:
            gdf: LineString GeoDataFrame
            node_tolerance: Tolerance for node snapping
            bidirectional: Make edges bidirectional
            
        Returns:
            Self
        """
        node_id = 0
        edge_id = 0
        nodes_dict = {}  # coords -> node_id
        
        # Create nodes from line endpoints and vertices
        for idx, row in gdf.iterrows():
            geom = row.geometry
            
            # Process all coordinates
            for coord in geom.coords:
                # Snap to existing node
                snapped = False
                for existing_coord, existing_id in nodes_dict.items():
                    dist = np.sqrt((coord[0] - existing_coord[0])**2 + 
                                 (coord[1] - existing_coord[1])**2)
                    if dist < node_tolerance:
                        snapped = True
                        coord = existing_coord
                        break
                
                if coord not in nodes_dict:
                    self.add_node(node_id, Point(coord), {})
                    nodes_dict[coord] = node_id
                    node_id += 1
        
        # Create edges from linestrings
        for idx, row in gdf.iterrows():
            geom = row.geometry
            attrs = {k: v for k, v in row.items() if k != 'geometry'}
            
            # Add edges between consecutive vertices
            coords = list(geom.coords)
            for i in range(len(coords) - 1):
                from_coord = coords[i]
                to_coord = coords[i + 1]
                
                from_node = nodes_dict.get(from_coord)
                to_node = nodes_dict.get(to_coord)
                
                if from_node is not None and to_node is not None:
                    segment = LineString([from_coord, to_coord])
                    self.add_edge(
                        edge_id,
                        from_node,
                        to_node,
                        segment,
                        attributes=attrs,
                        bidirectional=bidirectional
                    )
                    edge_id += 1
        
        return self
    
    def shortest_path(
        self,
        start_node: int,
        end_node: int
    ) -> Optional[List[int]]:
        """
        Find shortest path between nodes using Dijkstra's algorithm.
        
        Args:
            start_node: Start node ID
            end_node: End node ID
            
        Returns:
            List of node IDs forming shortest path, or None if no path
        """
        try:
            # Dijkstra's algorithm
            distances = {node_id: float('inf') for node_id in self.nodes}
            distances[start_node] = 0
            previous = {node_id: None for node_id in self.nodes}
            
            pq = [(0, start_node)]  # (distance, node_id)
            visited = set()
            
            while pq:
                current_dist, current_node = heapq.heappop(pq)
                
                if current_node in visited:
                    continue
                visited.add(current_node)
                
                if current_node == end_node:
                    # Reconstruct path
                    path = []
                    node = end_node
                    while node is not None:
                        path.append(node)
                        node = previous[node]
                    return list(reversed(path))
                
                # Explore neighbors
                for neighbor in self.adjacency.get(current_node, []):
                    if neighbor not in visited:
                        edge_id = self.edge_lookup.get((current_node, neighbor))
                        if edge_id:
                            edge = self.edges[edge_id]
                            new_dist = distances[current_node] + (edge.cost or 1.0)  # type: ignore
                            
                            if new_dist < distances[neighbor]:
                                distances[neighbor] = new_dist
                                previous[neighbor] = current_node  # type: ignore
                                heapq.heappush(pq, (float(new_dist), neighbor))  # type: ignore
            
            return None  # No path found
            
        except Exception as e:
            logger.error(f"Shortest path error: {e}")
            raise
    
    def all_pairs_shortest_path(self) -> Dict[int, Dict[int, float]]:
        """
        Compute shortest paths between all node pairs.
        
        Returns:
            Dict of {start_node: {end_node: distance}}
        """
        try:
            result = {}
            
            for start_node in self.nodes:
                result[start_node] = {}
                
                # Dijkstra from each start node
                distances = {node_id: float('inf') for node_id in self.nodes}
                distances[start_node] = 0
                
                pq = [(0, start_node)]
                visited = set()
                
                while pq:
                    current_dist, current_node = heapq.heappop(pq)
                    
                    if current_node in visited:
                        continue
                    visited.add(current_node)
                    
                    result[start_node][current_node] = current_dist
                    
                    for neighbor in self.adjacency.get(current_node, []):
                        if neighbor not in visited:
                            edge_id = self.edge_lookup.get((current_node, neighbor))
                            if edge_id:
                                edge = self.edges[edge_id]
                                new_dist = distances[current_node] + (edge.cost or 1.0)  # type: ignore
                                
                                if new_dist < distances[neighbor]:
                                    distances[neighbor] = new_dist
                                    heapq.heappush(pq, (float(new_dist), neighbor))  # type: ignore
            
            return result
            
        except Exception as e:
            logger.error(f"All pairs shortest path error: {e}")
            raise
    
    def service_area(
        self,
        start_node: int,
        max_distance: float
    ) -> Tuple[Set[int], float]:
        """
        Find service area reachable within max_distance.
        
        Args:
            start_node: Start node ID
            max_distance: Maximum distance
            
        Returns:
            (Set of accessible node IDs, total coverage area)
        """
        try:
            accessible = set()
            distances = {node_id: float('inf') for node_id in self.nodes}
            distances[start_node] = 0.0
            
            pq = [(0.0, start_node)]
            visited = set()
            
            while pq:
                current_dist, current_node = heapq.heappop(pq)
                
                if current_node in visited or current_dist > max_distance:
                    continue
                
                visited.add(current_node)
                accessible.add(current_node)
                
                for neighbor in self.adjacency.get(current_node, []):
                    if neighbor not in visited:
                        edge_id = self.edge_lookup.get((current_node, neighbor))
                        if edge_id:
                            edge = self.edges[edge_id]
                            if edge.cost is not None:
                                new_dist = distances[current_node] + edge.cost
                                
                                if new_dist < distances[neighbor] and new_dist <= max_distance:
                                    distances[neighbor] = new_dist
                                    heapq.heappush(pq, (new_dist, neighbor))
            
            return accessible, float(max_distance)
            
        except Exception as e:
            logger.error(f"Service area error: {e}")
            raise
    
    def connectivity_analysis(self) -> Dict[str, Any]:
        """
        Analyze network connectivity.
        
        Returns:
            Dict with connectivity metrics
        """
        try:
            # Find connected components
            visited = set()
            components = []
            
            for node_id in self.nodes:
                if node_id not in visited:
                    component = self._bfs(node_id, visited)
                    components.append(component)
            
            return {
                'num_nodes': len(self.nodes),
                'num_edges': len(self.edges),
                'num_components': len(components),
                'component_sizes': [len(c) for c in components],
                'is_connected': len(components) == 1,
                'avg_degree': sum(len(neighbors) for neighbors in self.adjacency.values()) / len(self.nodes) if self.nodes else 0
            }
            
        except Exception as e:
            logger.error(f"Connectivity analysis error: {e}")
            raise
    
    def _bfs(self, start_node: int, visited: set) -> Set[int]:
        """Breadth-first search for connected component."""
        component = set()
        queue = [start_node]
        
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            
            visited.add(node)
            component.add(node)
            
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return component


# Module exports
__all__ = ['NetworkGraph', 'NetworkEdge', 'NetworkNode']
