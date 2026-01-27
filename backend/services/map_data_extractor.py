"""
Map Data Extractor - Extract map features from DEM
Generates colormaps, contours, slopes, aspects, and other GIS-derived products
"""

import numpy as np
from scipy import ndimage
from scipy.ndimage import sobel, gaussian_filter
import logging
from typing import Dict, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MapDataType(Enum):
    """Types of map data that can be extracted"""
    ELEVATION = "elevation"
    SLOPE = "slope"
    ASPECT = "aspect"
    HILLSHADE = "hillshade"
    CONTOUR = "contour"
    FLOW_ACCUMULATION = "flow_accumulation"
    CURVATURE = "curvature"
    TOPOGRAPHIC_POSITION = "topographic_position"


class MapDataExtractor:
    """Extract various map data and derivatives from a DEM"""
    
    def __init__(self, dem: np.ndarray, cell_size: float = 1.0):
        """
        Initialize extractor
        
        Args:
            dem: Digital elevation model array
            cell_size: Cell size in meters (default 1m)
        """
        self.dem = dem.astype(np.float32)
        self.cell_size = cell_size
        self.cache = {}
    
    def extract_slope(self, degrees: bool = True) -> np.ndarray:
        """
        Extract slope from DEM using gradient method
        
        Args:
            degrees: Return slope in degrees (else radians)
            
        Returns:
            Slope array
        """
        if 'slope' in self.cache:
            return self.cache['slope']
        
        try:
            # Calculate gradients
            gy, gx = np.gradient(self.dem, self.cell_size)
            
            # Calculate slope
            slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
            
            if degrees:
                slope = np.degrees(slope_rad)
            else:
                slope = slope_rad
            
            # Smooth edges
            slope = np.nan_to_num(slope)
            self.cache['slope'] = slope
            logger.info(f"Extracted slope: min={np.min(slope):.2f}, max={np.max(slope):.2f}")
            return slope
        except Exception as e:
            logger.error(f"Error extracting slope: {e}")
            return np.zeros_like(self.dem)
    
    def extract_aspect(self) -> np.ndarray:
        """
        Extract aspect (direction of steepest slope) from DEM
        
        Returns:
            Aspect array in degrees (0-360)
        """
        if 'aspect' in self.cache:
            return self.cache['aspect']
        
        try:
            # Calculate gradients
            gy, gx = np.gradient(self.dem, self.cell_size)
            
            # Calculate aspect
            aspect = np.arctan2(gy, -gx)  # Note: negative gx for standard geographic convention
            aspect = np.degrees(aspect)
            
            # Convert to 0-360 range
            aspect = (90.0 - aspect) % 360.0
            
            self.cache['aspect'] = aspect
            logger.info("Extracted aspect")
            return aspect
        except Exception as e:
            logger.error(f"Error extracting aspect: {e}")
            return np.zeros_like(self.dem)
    
    def extract_hillshade(self, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
        """
        Generate hillshade for 3D visualization effect
        
        Args:
            azimuth: Light direction azimuth (0-360)
            altitude: Light altitude angle (0-90)
            
        Returns:
            Hillshade array (0-255 or 0-1)
        """
        if 'hillshade' in self.cache:
            return self.cache['hillshade']
        
        try:
            # Calculate gradients
            gy, gx = np.gradient(self.dem, self.cell_size)
            
            # Normalize
            gx_norm = gx / (np.max(np.abs(gx)) + 1e-8)
            gy_norm = gy / (np.max(np.abs(gy)) + 1e-8)
            
            # Light direction
            azimuth_rad = np.radians(azimuth)
            altitude_rad = np.radians(altitude)
            
            x = np.sin(azimuth_rad) * np.cos(altitude_rad)
            y = np.cos(azimuth_rad) * np.cos(altitude_rad)
            z = np.sin(altitude_rad)
            
            # Compute shading
            norm = np.sqrt(gx_norm**2 + gy_norm**2 + 1)
            gx_norm /= norm
            gy_norm /= norm
            
            shading = gx_norm * x + gy_norm * y + 1.0/norm * z
            shading = (shading + 1) / 2  # Normalize to 0-1
            shading = np.clip(shading, 0, 1)
            
            self.cache['hillshade'] = shading
            logger.info("Extracted hillshade")
            return shading
        except Exception as e:
            logger.error(f"Error extracting hillshade: {e}")
            return np.ones_like(self.dem)
    
    def extract_curvature(self, profile: bool = True) -> np.ndarray:
        """
        Extract terrain curvature (profile or plan curvature)
        
        Args:
            profile: If True, use profile curvature, else plan curvature
            
        Returns:
            Curvature array
        """
        cache_key = 'curvature_profile' if profile else 'curvature_plan'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Second derivatives
            gy, gx = np.gradient(self.dem, self.cell_size)
            gyy, gyx = np.gradient(gy, self.cell_size)
            gxy, gxx = np.gradient(gx, self.cell_size)
            
            if profile:
                # Profile curvature (along steepest descent)
                numerator = gxx * gy**2 - 2 * gxy * gx * gy + gyy * gx**2
                denominator = (gx**2 + gy**2) ** 1.5 + 1e-8
            else:
                # Plan curvature (perpendicular to steepest descent)
                numerator = gxx * gy**2 - 2 * gxy * gx * gy + gyy * gx**2
                denominator = gx**2 + gy**2 + 1e-8
            
            curvature = numerator / denominator
            curvature = np.nan_to_num(curvature)
            
            self.cache[cache_key] = curvature
            logger.info(f"Extracted curvature: min={np.min(curvature):.6f}, max={np.max(curvature):.6f}")
            return curvature
        except Exception as e:
            logger.error(f"Error extracting curvature: {e}")
            return np.zeros_like(self.dem)
    
    def extract_flow_accumulation(self, method: str = 'd8') -> np.ndarray:
        """
        Extract flow accumulation (simplified version)
        
        Args:
            method: 'd8' (steepest descent) or 'd4' (cardinal directions)
            
        Returns:
            Flow accumulation array
        """
        if 'flow_accumulation' in self.cache:
            return self.cache['flow_accumulation']
        
        try:
            h, w = self.dem.shape
            flow = np.ones_like(self.dem, dtype=np.float32)
            accumulation = np.zeros_like(self.dem, dtype=np.float32)
            
            # D8 flow direction (8 neighbors)
            if method == 'd8':
                directions = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]
            else:  # D4
                directions = [(-1, 0), (0, -1), (0, 1), (1, 0)]
            
            # Simple flow accumulation
            for y in range(h):
                for x in range(w):
                    min_height = self.dem[y, x]
                    flow_cell = 0
                    
                    for dy, dx in directions:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            if self.dem[ny, nx] < min_height:
                                flow_cell += 1
                    
                    accumulation[y, x] = flow_cell + 1
            
            # Normalize
            accumulation = gaussian_filter(accumulation, sigma=1.0)
            accumulation = accumulation / (np.max(accumulation) + 1e-8)
            
            self.cache['flow_accumulation'] = accumulation
            logger.info("Extracted flow accumulation")
            return accumulation
        except Exception as e:
            logger.error(f"Error extracting flow accumulation: {e}")
            return np.ones_like(self.dem)
    
    def extract_topographic_position(self, radius: int = 10) -> np.ndarray:
        """
        Extract topographic position index (TPI)
        
        Args:
            radius: Neighborhood radius in cells
            
        Returns:
            TPI array
        """
        cache_key = f'tpi_{radius}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            from scipy.ndimage import uniform_filter
            
            # Neighborhood mean
            neighborhood_mean = uniform_filter(self.dem, size=radius*2+1, mode='constant')
            
            # TPI = DEM - neighborhood mean
            tpi = self.dem - neighborhood_mean
            
            self.cache[cache_key] = tpi
            logger.info(f"Extracted TPI (radius={radius})")
            return tpi
        except Exception as e:
            logger.error(f"Error extracting TPI: {e}")
            return np.zeros_like(self.dem)
    
    def extract_all(self) -> Dict[str, np.ndarray]:
        """Extract all common map layers"""
        result = {
            'elevation': self.dem,
            'slope': self.extract_slope(),
            'aspect': self.extract_aspect(),
            'hillshade': self.extract_hillshade(),
            'curvature': self.extract_curvature(),
            'flow_accumulation': self.extract_flow_accumulation(),
            'topographic_position': self.extract_topographic_position()
        }
        return result
    
    def get_statistics(self) -> Dict[str, float]:
        """Get statistics for current DEM"""
        return {
            'elevation_min': float(np.min(self.dem)),
            'elevation_max': float(np.max(self.dem)),
            'elevation_mean': float(np.mean(self.dem)),
            'elevation_std': float(np.std(self.dem)),
            'slope_mean': float(np.mean(self.extract_slope())),
            'slope_max': float(np.max(self.extract_slope())),
        }
    
    def clear_cache(self):
        """Clear computation cache"""
        self.cache.clear()
        logger.info("Cleared extractor cache")
