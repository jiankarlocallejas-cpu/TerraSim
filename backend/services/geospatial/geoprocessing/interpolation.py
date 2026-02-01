"""
Spatial Interpolation and Analysis Tools.
IDW, Kriging, and other interpolation methods for spatial analysis.

Features:
- Inverse Distance Weighting (IDW)
- Thiessen polygons (Voronoi)
- Kernel density estimation
- Heat maps
- Contour generation
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.interpolate import griddata, Rbf
from scipy.spatial.distance import cdist
from scipy.ndimage import gaussian_filter
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import geopandas as gpd
from geopandas import GeoDataFrame, GeoSeries
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from skimage import measure

try:
    from libpysal.weights import Rook  # type: ignore[import, name]
    from esda.moran import Moran, Moran_Local  # type: ignore[import, name]
except ImportError:
    Rook = None  # type: ignore
    Moran = None  # type: ignore
    Moran_Local = None  # type: ignore

logger = logging.getLogger(__name__)


class IDWInterpolator:
    """Inverse Distance Weighting interpolation."""
    
    def __init__(self, power: float = 2.0, k: Optional[int] = None):  # type: ignore
        """
        Initialize IDW interpolator.
        
        Args:
            power: Power parameter (default 2.0)
            k: Number of nearest neighbors (None = use all)
        """
        self.power = power
        self.k = k
    
    def interpolate(
        self,
        points: np.ndarray,
        values: np.ndarray,
        grid_points: np.ndarray
    ) -> np.ndarray:
        """
        Perform IDW interpolation.
        
        Args:
            points: (n, 2) array of point coordinates
            values: (n,) array of values at points
            grid_points: (m, 2) array of grid points to interpolate
            
        Returns:
            (m,) array of interpolated values
        """
        try:
            distances = cdist(grid_points, points)
            
            if self.k:
                # Use k-nearest neighbors
                k_nearest_indices = np.argsort(distances, axis=1)[:, :self.k]
                distances_knn = np.take_along_axis(distances, k_nearest_indices, axis=1)
                values_knn = values[k_nearest_indices]
            else:
                distances_knn = distances
                values_knn = np.tile(values, (len(grid_points), 1))
            
            # Avoid division by zero
            distances_knn = np.maximum(distances_knn, 1e-10)
            
            # Calculate weights
            weights = 1.0 / (distances_knn ** self.power)
            weights_sum = np.sum(weights, axis=1, keepdims=True)
            
            # Interpolate
            interpolated = np.sum(weights * values_knn, axis=1) / weights_sum.flatten()
            
            return interpolated
            
        except Exception as e:
            logger.error(f"IDW interpolation error: {e}")
            raise


class RBFInterpolator:
    """Radial Basis Function interpolation."""
    
    def __init__(self, function: str = 'thin_plate', epsilon: Optional[float] = None):  # type: ignore
        """
        Initialize RBF interpolator.
        
        Args:
            function: RBF function type
            epsilon: Regularization parameter
        """
        self.function = function
        self.epsilon = epsilon
    
    def interpolate(
        self,
        points: np.ndarray,
        values: np.ndarray,
        grid_points: np.ndarray
    ) -> np.ndarray:
        """
        Perform RBF interpolation.
        
        Args:
            points: (n, 2) array of point coordinates
            values: (n,) array of values at points
            grid_points: (m, 2) array of grid points
            
        Returns:
            (m,) array of interpolated values
        """
        try:
            rbf = Rbf(
                points[:, 0], points[:, 1], values,
                function=self.function,
                epsilon=self.epsilon
            )
            
            interpolated = rbf(grid_points[:, 0], grid_points[:, 1])
            return interpolated
            
        except Exception as e:
            logger.error(f"RBF interpolation error: {e}")
            raise


class KernelDensity:
    """Kernel density estimation."""
    
    def __init__(self, bandwidth: float = 1.0, kernel: str = 'gaussian'):
        """
        Initialize kernel density estimator.
        
        Args:
            bandwidth: Bandwidth parameter
            kernel: Kernel type (gaussian, uniform, etc.)
        """
        self.bandwidth = bandwidth
        self.kernel = kernel
    
    def estimate(
        self,
        points: np.ndarray,
        grid_points: np.ndarray,
        weights: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Estimate density at grid points.
        
        Args:
            points: (n, 2) array of point coordinates
            grid_points: (m, 2) array of grid points
            weights: Optional weights for points
            
        Returns:
            (m,) array of density values
        """
        try:
            if weights is None:
                weights = np.ones(len(points))
            
            distances = cdist(grid_points, points)
            
            if self.kernel == 'gaussian':
                kernel_values = np.exp(-0.5 * (distances / self.bandwidth) ** 2)
            elif self.kernel == 'uniform':
                kernel_values = (distances <= self.bandwidth).astype(float)
            else:
                raise ValueError(f"Unknown kernel: {self.kernel}")
            
            # Apply weights
            density = np.sum(kernel_values * weights, axis=1)
            
            return density
            
        except Exception as e:
            logger.error(f"Kernel density estimation error: {e}")
            raise


class ContourGenerator:
    """Generate contour lines from raster data."""
    
    @staticmethod
    def generate_contours(
        raster: np.ndarray,
        levels: List[float],
        transform: Optional[Any] = None,  # type: ignore[name-defined]
        crs: str = 'EPSG:4326'
    ) -> GeoDataFrame:
        """
        Generate contour lines from raster.
        
        Args:
            raster: 2D array of values
            levels: List of contour levels
            transform: Rasterio transform
            crs: Coordinate reference system
            
        Returns:
            GeoDataFrame with contour lines
        """
        try:
            contours = []
            
            for level in levels:
                # Find contours at this level
                binary = (raster >= level).astype(int)
                
                try:
                    contour_coords = measure.find_contours(binary, 0.5)
                    
                    for coords in contour_coords:
                        if len(coords) > 2:
                            # Convert pixel coordinates to geographic
                            if transform:
                                geo_coords = [
                                    transform * (coord[1], coord[0])
                                    for coord in coords
                                ]
                            else:
                                geo_coords = coords
                            
                            line = LineString(geo_coords)
                            contours.append({
                                'geometry': line,
                                'level': level
                            })
                except Exception as e:
                    logger.debug(f"Error processing contour level {level}: {e}")
                    continue
            
            if contours:
                return GeoDataFrame(contours, crs=crs)
            else:
                return GeoDataFrame(columns=['geometry', 'level'], crs=crs)
            
        except Exception as e:
            logger.error(f"Contour generation error: {e}")
            raise
    
    @staticmethod
    def generate_heatmap(
        gdf: GeoDataFrame,
        bounds: Tuple[float, float, float, float],
        resolution: int = 100,
        kernel_bandwidth: Optional[float] = None
    ) -> Tuple[np.ndarray, Tuple]:
        """
        Generate heatmap from point data.
        
        Args:
            gdf: Point GeoDataFrame
            bounds: (minx, miny, maxx, maxy)
            resolution: Grid resolution
            kernel_bandwidth: Kernel bandwidth
            
        Returns:
            (heatmap_array, extent)
        """
        try:
            minx, miny, maxx, maxy = bounds
            
            # Create grid
            x = np.linspace(minx, maxx, resolution)
            y = np.linspace(miny, maxy, resolution)
            xx, yy = np.meshgrid(x, y)
            grid_points = np.column_stack([xx.ravel(), yy.ravel()])
            
            # Extract point coordinates
            points = np.array([(geom.centroid.x if hasattr(geom, 'centroid') else 0, geom.centroid.y if hasattr(geom, 'centroid') else 0) for geom in gdf.geometry])
            
            # Calculate density
            if kernel_bandwidth is None:
                kernel_bandwidth = (maxx - minx) / (10 * resolution)
            
            kde = KernelDensity(bandwidth=kernel_bandwidth)
            density = kde.estimate(points, grid_points)
            
            # Reshape to grid
            heatmap = density.reshape((resolution, resolution))
            
            return heatmap, (minx, maxx, miny, maxy)
            
        except Exception as e:
            logger.error(f"Heatmap generation error: {e}")
            raise


class SpatialStatistics:
    """Statistical analysis for spatial data."""
    
    @staticmethod
    def spatial_autocorrelation(
        gdf: GeoDataFrame,
        column: str,
        weights: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate Moran's I spatial autocorrelation.
        
        Args:
            gdf: GeoDataFrame
            column: Column name for values
            weights: Optional spatial weights
            
        Returns:
            Dict with I, p-value, etc.
        """
        try:
            from libpysal.weights import W  # type: ignore[import, name]
            from libpysal.weights.spatial_lag import lag_spatial  # type: ignore[import, name]
            from esda.moran import Moran  # type: ignore[import, name]
            
            # Create spatial weights if not provided
            if weights is None:
                from libpysal.weights import Queen  # type: ignore[import, name]
                weights = Queen.from_dataframe(gdf)
            
            # Calculate Moran's I
            moran = Moran(gdf[column].values, weights)
            
            return {
                'morans_i': moran.I,
                'p_value': moran.p_norm,
                'expected_i': moran.EI,
                'variance': moran.VI_norm
            }
            
        except ImportError:
            logger.warning("libpysal or esda not installed")
            return {}
        except Exception as e:
            logger.error(f"Spatial autocorrelation error: {e}")
            raise
    
    @staticmethod
    def local_spatial_autocorrelation(
        gdf: GeoDataFrame,
        column: str
    ) -> GeoDataFrame:
        """
        Calculate local Moran's I.
        
        Args:
            gdf: GeoDataFrame
            column: Column name
            
        Returns:
            GeoDataFrame with LISA values
        """
        try:
            from libpysal.weights import Queen  # type: ignore[import, name]
            from esda.moran import Local_Moran  # type: ignore[import, name]
            
            weights = Queen.from_dataframe(gdf)
            lisa = Local_Moran(gdf[column].values, weights)
            
            result = gdf.copy()
            result['local_i'] = lisa.Is
            result['p_value'] = lisa.p_sim
            result['cluster'] = lisa.q
            
            return result
            
        except ImportError:
            logger.warning("libpysal or esda not installed")
            return gdf
        except Exception as e:
            logger.error(f"Local spatial autocorrelation error: {e}")
            raise


# Module exports
__all__ = [
    'IDWInterpolator',
    'RBFInterpolator',
    'KernelDensity',
    'ContourGenerator',
    'SpatialStatistics'
]
