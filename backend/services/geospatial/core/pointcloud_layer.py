"""
Point cloud layer implementation.
Handles LAS/LAZ point cloud data for terrain analysis.
"""

from typing import Optional, Dict, Any, List, Tuple
from .layer import Layer, LayerType, Extent
from dataclasses import dataclass
import numpy as np


@dataclass
class PointCloudStatistics:
    """Point cloud statistics."""
    point_count: int = 0
    x_min: float = 0.0
    y_min: float = 0.0
    z_min: float = 0.0
    x_max: float = 0.0
    y_max: float = 0.0
    z_max: float = 0.0
    z_mean: float = 0.0
    z_std: float = 0.0
    intensity_min: float = 0.0
    intensity_max: float = 0.0
    intensity_mean: float = 0.0
    classification_distribution: Optional[Dict[int, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'point_count': self.point_count,
            'x_min': self.x_min,
            'y_min': self.y_min,
            'z_min': self.z_min,
            'x_max': self.x_max,
            'y_max': self.y_max,
            'z_max': self.z_max,
            'z_mean': self.z_mean,
            'z_std': self.z_std,
            'intensity_min': self.intensity_min,
            'intensity_max': self.intensity_max,
            'intensity_mean': self.intensity_mean,
            'classification_distribution': self.classification_distribution or {}
        }


class PointCloudLayer(Layer):
    """
    Point cloud data layer (LAS, LAZ, E57).
    Analogous to QGIS QgsPointCloudLayer.
    """
    
    def __init__(
        self,
        name: str,
        source: str,
        crs: str = "EPSG:4326",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, source, LayerType.POINT_CLOUD, crs, metadata)
        
        self._statistics: Optional[PointCloudStatistics] = None
        self._points_data: Optional[np.ndarray] = None
        self._point_format = "LAS 1.2"
        self._scale: Tuple[float, float, float] = (0.01, 0.01, 0.01)
        self._offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._voxelized: Optional[Dict] = None
    
    def load_statistics(self, stats: PointCloudStatistics):
        """Load point cloud statistics."""
        self._statistics = stats
        
        # Update extent
        self.extent = Extent(
            xmin=stats.x_min,
            ymin=stats.y_min,
            xmax=stats.x_max,
            ymax=stats.y_max,
            zmin=stats.z_min,
            zmax=stats.z_max
        )
    
    def get_statistics(self) -> Optional[PointCloudStatistics]:
        """Get point cloud statistics."""
        return self._statistics
    
    def set_point_format(self, format_str: str):
        """Set LAS point format (e.g., 'LAS 1.2', 'LAS 1.4')."""
        self._point_format = format_str
    
    def get_point_format(self) -> str:
        """Get point format."""
        return self._point_format
    
    def load_points(self, points: np.ndarray):
        """
        Load point cloud data.
        Expected shape: (n_points, n_attributes)
        Attributes: x, y, z, intensity, classification, etc.
        """
        self._points_data = points
        
        if points.shape[0] > 0:
            stats = PointCloudStatistics(
                point_count=points.shape[0],
                x_min=float(np.min(points[:, 0])),
                x_max=float(np.max(points[:, 0])),
                y_min=float(np.min(points[:, 1])),
                y_max=float(np.max(points[:, 1])),
                z_min=float(np.min(points[:, 2])),
                z_max=float(np.max(points[:, 2])),
                z_mean=float(np.mean(points[:, 2])),
                z_std=float(np.std(points[:, 2]))
            )
            self.load_statistics(stats)
    
    def get_points_in_extent(self, extent: Extent) -> np.ndarray:
        """Get points within spatial extent."""
        if self._points_data is None:
            return np.array([])
        
        mask = (
            (self._points_data[:, 0] >= extent.xmin) &
            (self._points_data[:, 0] <= extent.xmax) &
            (self._points_data[:, 1] >= extent.ymin) &
            (self._points_data[:, 1] <= extent.ymax)
        )
        return self._points_data[mask]
    
    def get_points_by_classification(self, classification: int) -> np.ndarray:
        """Get points by classification code."""
        if self._points_data is None or self._points_data.shape[1] < 5:
            return np.array([])
        
        mask = self._points_data[:, 4] == classification
        return self._points_data[mask]
    
    def compute_elevation_grid(self, resolution: float) -> np.ndarray:
        """Compute DEM grid from point cloud at specified resolution."""
        if self._points_data is None or self._statistics is None:
            return np.array([])
        
        stats = self._statistics
        x_range = np.arange(stats.x_min, stats.x_max, resolution)
        y_range = np.arange(stats.y_min, stats.y_max, resolution)
        
        grid = np.zeros((len(y_range), len(x_range)))
        
        # Simple IDW interpolation
        for i, y in enumerate(y_range):
            for j, x in enumerate(x_range):
                # Find nearest points
                distances = np.sqrt(
                    (self._points_data[:, 0] - x)**2 +
                    (self._points_data[:, 1] - y)**2
                )
                nearest_idx = np.argsort(distances)[:10]  # 10 nearest
                weights = 1.0 / (distances[nearest_idx] + 1e-10)
                grid[i, j] = np.sum(self._points_data[nearest_idx, 2] * weights) / np.sum(weights)
        
        return grid
    
    def get_feature_count(self) -> int:
        """Get point count."""
        if self._statistics:
            return self._statistics.point_count
        return 0
    
    def get_attributes(self) -> Dict[str, str]:
        """Get point attributes."""
        return {
            'x': 'float64',
            'y': 'float64',
            'z': 'float64',
            'intensity': 'uint16',
            'classification': 'uint8',
            'gps_time': 'float64',
            'red': 'uint16',
            'green': 'uint16',
            'blue': 'uint16'
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **self.get_metadata(),
            'point_format': self._point_format,
            'statistics': self._statistics.to_dict() if self._statistics else None,
            'point_count': self.get_feature_count()
        }
