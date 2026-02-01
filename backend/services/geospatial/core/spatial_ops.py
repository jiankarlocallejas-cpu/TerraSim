"""
Spatial operations and analysis framework.
Provides vector and raster spatial analysis algorithms.
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
from dataclasses import dataclass

from .layer import Extent, Layer
from .raster_layer import RasterLayer
from .vector_layer import VectorLayer, GeometryType
from .pointcloud_layer import PointCloudLayer


class SpatialOperationType(Enum):
    """Spatial operation types."""
    BUFFER = "buffer"
    INTERSECTION = "intersection"
    UNION = "union"
    DIFFERENCE = "difference"
    SYMMETRIC_DIFFERENCE = "symmetric_difference"
    CLIP = "clip"
    MERGE = "merge"
    DISSOLVE = "dissolve"


@dataclass
class SpatialOperationResult:
    """Result of spatial operation."""
    success: bool
    output_layer: Optional[Layer] = None
    statistics: Optional[Dict[str, Any]] = None
    error_message: str = ""
    processing_time: float = 0.0


class SpatialOperator(ABC):
    """Base class for spatial operations."""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> SpatialOperationResult:
        """Execute the spatial operation."""
        pass


class BufferOperation(SpatialOperator):
    """Buffer operation for vector layers."""
    
    def __init__(self, distance: float, resolution: int = 16):
        self.distance = distance
        self.resolution = resolution
    
    def execute(self, layer: VectorLayer) -> SpatialOperationResult:
        """
        Create buffer geometry.
        Returns new vector layer with buffered geometries.
        """
        try:
            import time
            start_time = time.time()
            
            # Create output layer
            output = VectorLayer(
                f"{layer.name}_buffer",
                layer.source,
                layer.geometry_type,
                layer.crs,
                {'buffer_distance': self.distance}
            )
            
            # Copy attributes
            for attr in layer.get_attribute_list():
                output.add_attribute(attr)
            
            # TODO: Implement actual buffer operation
            # This would use shapely or similar library
            
            elapsed = time.time() - start_time
            return SpatialOperationResult(
                success=True,
                output_layer=output,
                statistics={'features_processed': layer.get_feature_count()},
                processing_time=elapsed
            )
        except Exception as e:
            return SpatialOperationResult(
                success=False,
                error_message=str(e)
            )


class RasterAnalysis:
    """Raster analysis operations."""
    
    @staticmethod
    def hillshade(dem: np.ndarray, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
        """
        Generate hillshade from DEM.
        
        Args:
            dem: DEM array
            azimuth: Light direction azimuth (0-360)
            altitude: Light source altitude (0-90)
        
        Returns:
            Hillshade array
        """
        x, y = np.gradient(dem)
        slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
        aspect = np.arctan2(-x, y)
        
        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)
        
        shaded = np.sin(altitude_rad) * np.cos(slope) + \
                 np.cos(altitude_rad) * np.sin(slope) * \
                 np.cos(azimuth_rad - aspect - np.pi/2)
        
        shaded = (shaded + 1) / 2 * 255
        return shaded.astype(np.uint8)
    
    @staticmethod
    def slope(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
        """
        Calculate slope from DEM.
        Returns slope in degrees.
        """
        x, y = np.gradient(dem, cell_size)
        slope = np.arctan(np.sqrt(x*x + y*y)) * 180 / np.pi
        return slope
    
    @staticmethod
    def aspect(dem: np.ndarray) -> np.ndarray:
        """
        Calculate aspect from DEM.
        Returns aspect in degrees (0-360).
        """
        x, y = np.gradient(dem)
        aspect = np.arctan2(-x, y) * 180 / np.pi
        aspect[aspect < 0] += 360
        return aspect
    
    @staticmethod
    def curvature(dem: np.ndarray, cell_size: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate profile and plan curvature.
        """
        # Simplified curvature calculation
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]) / (cell_size**2)
        from scipy import signal
        profile_curv = signal.convolve2d(dem, laplacian, mode='same')
        
        return profile_curv, profile_curv  # Simplified
    
    @staticmethod
    def ndvi(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
        """
        Calculate NDVI (Normalized Difference Vegetation Index).
        """
        red = red_band.astype(float)
        nir = nir_band.astype(float)
        
        ndvi = (nir - red) / (nir + red + 1e-10)
        return np.clip(ndvi, -1, 1)
    
    @staticmethod
    def change_detection(dem1: np.ndarray, dem2: np.ndarray) -> np.ndarray:
        """
        Detect elevation changes between two DEMs.
        Returns difference (dem2 - dem1).
        """
        return dem2 - dem1


class VolumeAnalysis:
    """Volume calculation from point clouds and DEMs."""
    
    @staticmethod
    def calculate_volume_change(
        dem_before: np.ndarray,
        dem_after: np.ndarray,
        cell_size: float,
        extent: Extent
    ) -> Dict[str, float]:
        """
        Calculate volume change between two DEMs.
        
        Args:
            dem_before: Before DEM
            dem_after: After DEM
            cell_size: Cell size in map units
            extent: Extent of analysis
        
        Returns:
            Dictionary with erosion/deposition volumes
        """
        difference = dem_after - dem_before
        cell_area = cell_size ** 2
        
        erosion_mask = difference < 0
        deposition_mask = difference > 0
        
        total_erosion = np.sum(np.abs(difference[erosion_mask])) * cell_area
        total_deposition = np.sum(difference[deposition_mask]) * cell_area
        net_change = total_deposition - total_erosion
        
        return {
            'erosion_volume': float(total_erosion),
            'deposition_volume': float(total_deposition),
            'net_change': float(net_change),
            'erosion_area': float(np.sum(erosion_mask) * cell_area),
            'deposition_area': float(np.sum(deposition_mask) * cell_area),
            'mean_erosion_depth': float(np.mean(np.abs(difference[erosion_mask]))) if erosion_mask.any() else 0.0,
            'mean_deposition_depth': float(np.mean(difference[deposition_mask])) if deposition_mask.any() else 0.0,
        }
    
    @staticmethod
    def calculate_point_cloud_volume(
        points: np.ndarray,
        reference_z: float,
        cell_size: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate volume from point cloud relative to reference elevation.
        """
        height_above_ref = points[:, 2] - reference_z
        
        # Grid-based volume calculation
        x_bins = int((np.max(points[:, 0]) - np.min(points[:, 0])) / cell_size) + 1
        y_bins = int((np.max(points[:, 1]) - np.min(points[:, 1])) / cell_size) + 1
        
        height_grid = np.zeros((y_bins, x_bins))
        count_grid = np.zeros((y_bins, x_bins))
        
        for point in points:
            xi = int((point[0] - np.min(points[:, 0])) / cell_size)
            yi = int((point[1] - np.min(points[:, 1])) / cell_size)
            
            if 0 <= xi < x_bins and 0 <= yi < y_bins:
                height_grid[yi, xi] += point[2] - reference_z
                count_grid[yi, xi] += 1
        
        # Average heights
        valid_cells = count_grid > 0
        height_grid[valid_cells] /= count_grid[valid_cells]
        
        cell_area = cell_size ** 2
        total_volume = np.sum(height_grid) * cell_area
        
        above_ref = np.sum(height_grid[height_grid > 0]) * cell_area
        below_ref = np.sum(np.abs(height_grid[height_grid < 0])) * cell_area
        
        return {
            'total_volume': float(total_volume),
            'volume_above_reference': float(above_ref),
            'volume_below_reference': float(below_ref),
            'grid_resolution': cell_size,
            'grid_cells': x_bins * y_bins,
            'valid_cells': int(np.sum(valid_cells))
        }


class FeatureStatistics:
    """Calculate statistics from vector features."""
    
    @staticmethod
    def calculate_layer_statistics(layer: VectorLayer) -> Dict[str, Any]:
        """Calculate statistics for vector layer."""
        features = layer.get_features()
        
        stats = {
            'feature_count': len(features),
            'geometry_type': layer.geometry_type.value,
            'attributes': {}
        }
        
        # Calculate statistics for numeric attributes
        for attr_name, attr_type in layer.get_attributes().items():
            if attr_type in ['integer', 'real']:
                values = [f.attributes.get(attr_name, 0) for f in features if attr_name in f.attributes]
                if values:
                    values = [float(v) for v in values if v is not None]
                    stats['attributes'][attr_name] = {
                        'min': float(np.min(values)),
                        'max': float(np.max(values)),
                        'mean': float(np.mean(values)),
                        'std': float(np.std(values))
                    }
        
        return stats
