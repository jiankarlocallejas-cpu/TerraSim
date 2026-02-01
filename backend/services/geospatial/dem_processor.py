"""
TerraSim Spatial Data Processing Module

Handles DEM processing, terrain derivation, and GIS data preprocessing
for the erosion modeling framework.

Key functions:
- DEM processing and terrain parameter extraction
- Flow routing and accumulation
- Slope and aspect derivation
- Land-cover and soil data integration
"""

import numpy as np
import logging
from typing import Dict, Tuple, Optional, Any
from scipy import ndimage
from scipy.ndimage import convolve
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class DEMProcessor:
    """
    Process Digital Elevation Model (DEM) data and derive terrain parameters.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fill_sinks(self, dem: np.ndarray, iterations: int = 5) -> np.ndarray:
        """
        Fill sinks (depressions) in DEM for proper flow routing.
        
        Args:
            dem: Digital Elevation Model array
            iterations: Number of fill iterations
            
        Returns:
            DEM with filled sinks
        """
        try:
            filled_dem = dem.copy()
            for i in range(iterations):
                # Create morphological closing to fill small depressions
                minimum_filter = ndimage.minimum_filter(filled_dem, size=3)
                filled_dem = np.maximum(filled_dem, minimum_filter)
            return filled_dem
        except Exception as e:
            self.logger.error(f"Error filling sinks: {e}")
            return dem
    
    def compute_slope(
        self,
        dem: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute slope gradient from DEM.
        
        Uses Zevenbergen-Thorne method for 3x3 kernel:
        slope_percent = sqrt((∂z/∂x)² + (∂z/∂y)²) * 100
        
        Args:
            dem: Digital Elevation Model array
            cell_size: Cell size in meters
            
        Returns:
            Slope array (percent gradient)
        """
        try:
            # Zevenbergen-Thorne finite difference coefficients
            x_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            y_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
            
            # Compute gradients
            dz_dx = convolve(dem, x_kernel) / (8 * cell_size)
            dz_dy = convolve(dem, y_kernel) / (8 * cell_size)
            
            # Compute slope
            slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
            slope_percent = np.tan(slope_rad) * 100
            
            return np.clip(slope_percent, 0, None)
        except Exception as e:
            self.logger.error(f"Error computing slope: {e}")
            return np.zeros_like(dem)
    
    def compute_aspect(
        self,
        dem: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute aspect (flow direction) from DEM.
        
        Aspect is the direction of slope, where 0° = north, 90° = east, etc.
        
        Args:
            dem: Digital Elevation Model array
            cell_size: Cell size in meters
            
        Returns:
            Aspect array (degrees, 0-360)
        """
        try:
            x_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            y_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
            
            dz_dx = convolve(dem, x_kernel) / (8 * cell_size)
            dz_dy = convolve(dem, y_kernel) / (8 * cell_size)
            
            # Compute aspect (0-360 degrees, clockwise from north)
            aspect = np.arctan2(-dz_dx, dz_dy)
            aspect_degrees = np.degrees(aspect)
            aspect_degrees = np.where(aspect_degrees < 0, aspect_degrees + 360, aspect_degrees)
            
            return aspect_degrees
        except Exception as e:
            self.logger.error(f"Error computing aspect: {e}")
            return np.zeros_like(dem)
    
    def compute_flow_direction(self, slope: np.ndarray) -> np.ndarray:
        """
        Compute flow direction using D8 algorithm.
        
        Returns directions: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE
        
        Args:
            slope: Slope array
            
        Returns:
            Flow direction array with values 1,2,4,8,16,32,64,128
        """
        try:
            flow_dir = np.zeros_like(slope, dtype=np.int32)
            
            # D8 neighbor offsets and their codes
            dy_arr = [-1, -1, 0, 1, 1, 1, 0, -1]
            dx_arr = [0, 1, 1, 1, 0, -1, -1, -1]
            code_arr = [64, 128, 1, 2, 4, 8, 16, 32]
            
            # For each cell, find direction of steepest descent
            for i in range(1, slope.shape[0]-1):
                for j in range(1, slope.shape[1]-1):
                    max_slope = 0
                    max_dir = 0
                    
                    for k in range(8):
                        neighbor_slope = slope[i + dy_arr[k], j + dx_arr[k]]
                        if neighbor_slope > max_slope:
                            max_slope = neighbor_slope
                            max_dir = code_arr[k]
                    
                    flow_dir[i, j] = max_dir if max_slope > 0 else 0
            
            return flow_dir
        except Exception as e:
            self.logger.error(f"Error computing flow direction: {e}")
            return np.zeros_like(slope, dtype=np.int32)
    
    def compute_flow_accumulation(
        self,
        flow_dir: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute cumulative flow accumulation (contributing area).
        
        Args:
            flow_dir: Flow direction array (D8 codes)
            cell_size: Cell size in meters
            
        Returns:
            Flow accumulation array (number of cells or area)
        """
        try:
            height, width = flow_dir.shape
            accumulation = np.ones((height, width), dtype=np.float32)
            
            # D8 neighbor offset mappings
            dir_to_offset = {
                1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
                16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
            }
            
            # Iterative accumulation routing
            for iteration in range(min(height, width)):
                for i in range(height):
                    for j in range(width):
                        if flow_dir[i, j] > 0:
                            di, dj = dir_to_offset.get(flow_dir[i, j], (0, 0))
                            ni, nj = i + di, j + dj
                            
                            if 0 <= ni < height and 0 <= nj < width:
                                accumulation[ni, nj] += accumulation[i, j]
            
            # Convert to area
            area = accumulation * (cell_size ** 2)
            return area
        except Exception as e:
            self.logger.error(f"Error computing flow accumulation: {e}")
            return np.ones_like(flow_dir, dtype=np.float32)
    
    def compute_LS_factor(
        self,
        flow_accum: np.ndarray,
        slope: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute topographic LS (Length-Slope) factor for RUSLE.
        
        LS = (A/22.13)^m * (sin(β)/0.0896)^n
        
        where m=0.6, n=1.3 for RUSLE
        
        Args:
            flow_accum: Flow accumulation (contributing area)
            slope: Slope in degrees
            cell_size: Cell size in meters
            
        Returns:
            LS factor array
        """
        try:
            # Convert slope to radians
            slope_rad = np.radians(slope)
            
            # Compute slope length factor (L)
            # Simplified: use flow accumulation as proxy for slope length
            L = np.sqrt(flow_accum / (cell_size ** 2))
            L = np.clip(L, 0.5, None)  # Minimum slope length
            
            # Compute steepness factor (S)
            S = 0.065 + 4.56 * np.sin(slope_rad) + 65.41 * (np.sin(slope_rad) ** 2)
            
            # Combine L and S
            LS = L * S
            
            return np.clip(LS, 0.2, 100)
        except Exception as e:
            self.logger.error(f"Error computing LS factor: {e}")
            return np.ones_like(slope)
    
    def extract_terrain_params(
        self,
        dem: np.ndarray,
        cell_size: float
    ) -> Dict[str, np.ndarray]:
        """
        Extract all terrain parameters from DEM.
        
        Args:
            dem: Digital Elevation Model
            cell_size: Cell size in meters
            
        Returns:
            Dictionary with terrain parameters
        """
        try:
            # Fill sinks
            filled_dem = self.fill_sinks(dem)
            
            # Compute basic terrain parameters
            slope = self.compute_slope(filled_dem, cell_size)
            aspect = self.compute_aspect(filled_dem, cell_size)
            flow_dir = self.compute_flow_direction(slope)
            flow_accum = self.compute_flow_accumulation(flow_dir, cell_size)
            
            # Compute topographic factor
            LS = self.compute_LS_factor(flow_accum, slope, cell_size)
            
            # Compute curvature
            profile_curv = self.compute_profile_curvature(filled_dem, cell_size)
            plan_curv = self.compute_plan_curvature(filled_dem, cell_size)
            
            return {
                'dem': filled_dem,
                'slope': slope,
                'aspect': aspect,
                'flow_direction': flow_dir,
                'flow_accumulation': flow_accum,
                'LS_factor': LS,
                'profile_curvature': profile_curv,
                'plan_curvature': plan_curv
            }
        except Exception as e:
            self.logger.error(f"Error extracting terrain parameters: {e}")
            return {}
    
    def compute_profile_curvature(
        self,
        dem: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute profile curvature (vertical curvature).
        
        Indicates acceleration/deceleration of water flow.
        """
        try:
            z_kernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])
            y_kernel = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
            
            dz_dx = convolve(dem, z_kernel) / (8 * cell_size)
            dz_dy = convolve(dem, y_kernel) / (8 * cell_size)
            d2z_dx2 = convolve(dz_dx, z_kernel) / (8 * cell_size)
            
            profile_curv = d2z_dx2 / (1 + dz_dx**2 + dz_dy**2)
            return profile_curv
        except Exception as e:
            self.logger.error(f"Error computing profile curvature: {e}")
            return np.zeros_like(dem)
    
    def compute_plan_curvature(
        self,
        dem: np.ndarray,
        cell_size: float
    ) -> np.ndarray:
        """
        Compute plan curvature (horizontal curvature).
        
        Indicates flow convergence/divergence.
        """
        try:
            z_kernel = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]])
            y_kernel = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
            
            dz_dx = convolve(dem, z_kernel) / (8 * cell_size)
            dz_dy = convolve(dem, y_kernel) / (8 * cell_size)
            d2z_dy2 = convolve(dz_dy, y_kernel) / (8 * cell_size)
            
            plan_curv = d2z_dy2 / (1 + dz_dx**2 + dz_dy**2)
            return plan_curv
        except Exception as e:
            self.logger.error(f"Error computing plan curvature: {e}")
            return np.zeros_like(dem)


class LandCoverProcessor:
    """
    Process land-cover and land-use data for erosion modeling.
    """
    
    # Default C (cover-management) factors by land use class
    COVER_FACTORS = {
        'forest': 0.001,
        'shrubland': 0.01,
        'grassland': 0.05,
        'cultivated': 0.3,
        'urban': 0.5,
        'bare_soil': 0.95,
        'water': 0.0
    }
    
    # Default P (support practices) factors
    PRACTICE_FACTORS = {
        'none': 1.0,
        'contour_plowing': 0.75,
        'strip_cropping': 0.5,
        'terracing': 0.25,
        'conservation_practices': 0.1
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def reclassify_landcover(
        self,
        lulc_raster: np.ndarray,
        classification_map: Dict[int, str]
    ) -> np.ndarray:
        """
        Reclassify land-cover raster to standard classes.
        
        Args:
            lulc_raster: Land-use/land-cover raster
            classification_map: Mapping from raster values to classes
            
        Returns:
            Reclassified raster with standard classes
        """
        try:
            reclassified = np.zeros_like(lulc_raster, dtype=object)
            for old_val, new_class in classification_map.items():
                reclassified[lulc_raster == old_val] = new_class
            return reclassified
        except Exception as e:
            self.logger.error(f"Error reclassifying land cover: {e}")
            return lulc_raster.astype(str)
    
    def compute_C_factor(
        self,
        lulc_classes: np.ndarray,
        vegetation_index: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute cover-management (C) factor from land-cover classification.
        
        Args:
            lulc_classes: Land-use/land-cover classes
            vegetation_index: Optional NDVI or similar vegetation index
            
        Returns:
            C factor raster
        """
        try:
            C_factor = np.zeros_like(lulc_classes, dtype=float)
            
            for lulc_class, c_value in self.COVER_FACTORS.items():
                mask = lulc_classes == lulc_class
                C_factor[mask] = c_value
            
            # Adjust C factor based on vegetation index if available
            if vegetation_index is not None:
                # Higher NDVI = lower C factor
                ndvi_normalized = (vegetation_index + 1) / 2  # Normalize to 0-1
                C_factor = C_factor * (1 - ndvi_normalized * 0.8)
            
            return np.clip(C_factor, 0, 1)
        except Exception as e:
            self.logger.error(f"Error computing C factor: {e}")
            return np.full_like(lulc_classes, 0.3, dtype=float)
    
    def compute_P_factor(
        self,
        practice_map: np.ndarray
    ) -> np.ndarray:
        """
        Compute support practices (P) factor.
        
        Args:
            practice_map: Map of conservation practices
            
        Returns:
            P factor raster
        """
        try:
            P_factor = np.ones_like(practice_map, dtype=float)
            
            for practice, p_value in self.PRACTICE_FACTORS.items():
                mask = practice_map == practice
                P_factor[mask] = p_value
            
            return P_factor
        except Exception as e:
            self.logger.error(f"Error computing P factor: {e}")
            return np.ones_like(practice_map, dtype=float)


class SoilDataProcessor:
    """
    Process soil property data for erosion modeling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def interpolate_soil_data(
        self,
        soil_points: np.ndarray,
        coordinates: np.ndarray,
        dem_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Interpolate point soil data to grid using inverse distance weighting.
        
        Args:
            soil_points: Array of soil property values at points
            coordinates: Coordinates of soil sample points
            dem_shape: Shape of output grid
            
        Returns:
            Interpolated soil property grid
        """
        try:
            from scipy.spatial import KDTree
            
            # Create output grid
            output = np.zeros(dem_shape)
            y_indices, x_indices = np.meshgrid(
                np.arange(dem_shape[0]),
                np.arange(dem_shape[1]),
                indexing='ij'
            )
            
            grid_points = np.column_stack([y_indices.ravel(), x_indices.ravel()])
            
            # Build KDTree for efficiency
            tree = KDTree(coordinates)
            distances, indices = tree.query(grid_points, k=4)
            
            # Inverse distance weighting interpolation
            weights = 1.0 / np.maximum(distances, 1e-10)
            weights /= np.sum(weights, axis=1, keepdims=True)
            
            interpolated = np.sum(
                soil_points[indices] * weights,
                axis=1
            )
            
            return interpolated.reshape(dem_shape)
        except Exception as e:
            self.logger.error(f"Error interpolating soil data: {e}")
            return np.full(dem_shape, np.nanmean(soil_points))
