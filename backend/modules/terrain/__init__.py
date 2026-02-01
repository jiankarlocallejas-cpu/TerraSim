"""
Terrain Module - Core terrain simulation and modeling

Handles:
- Digital Elevation Model (DEM) processing
- Erosion simulation
- Slope and aspect calculations
- Terrain properties computation
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class TerrainConfig:
    """Configuration for terrain operations"""
    dem_resolution: float = 30.0  # meters
    slope_threshold: float = 5.0  # degrees
    aspect_bins: int = 8
    cache_enabled: bool = True


class TerrainAnalyzer:
    """Analyzes terrain properties from DEM data"""
    
    def __init__(self, config: Optional[TerrainConfig] = None):
        self.config = config or TerrainConfig()
    
    def compute_slope(self, dem: np.ndarray) -> np.ndarray:
        """Compute slope in degrees from DEM"""
        if dem.size == 0:
            return np.array([])
        
        gy, gx = np.gradient(dem)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
        return np.degrees(slope_rad)
    
    def compute_aspect(self, dem: np.ndarray) -> np.ndarray:
        """Compute aspect in degrees (0-360) from DEM"""
        if dem.size == 0:
            return np.array([])
        
        gy, gx = np.gradient(dem)
        aspect = np.arctan2(gy, -gx)
        aspect = np.degrees(aspect)
        aspect = (aspect + 180) % 360
        return aspect
    
    def compute_curvature(self, dem: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute profile and planform curvature"""
        if dem.size == 0:
            return np.array([]), np.array([])
        
        gy, gx = np.gradient(dem)
        gyy, gyx = np.gradient(gy)
        gxy, gxx = np.gradient(gx)
        
        # Profile curvature (slope direction)
        denom = (gx**2 + gy**2 + 1)**1.5
        profile = -((gx**2 * gyy - 2*gx*gy*gyx + gy**2 * gxx) / denom)
        profile = np.nan_to_num(profile, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Planform curvature (perpendicular to slope)
        planform = -(gxx * gy**2 - 2*gxy*gx*gy + gyy*gx**2) / (denom * (gx**2 + gy**2))
        planform = np.nan_to_num(planform, nan=0.0, posinf=0.0, neginf=0.0)
        
        return profile, planform


class TerrainModule:
    """Main terrain module"""
    
    def __init__(self, config: Optional[TerrainConfig] = None):
        self.config = config or TerrainConfig()
        self.analyzer = TerrainAnalyzer(self.config)
    
    def analyze_dem(self, dem: np.ndarray) -> Dict[str, Any]:
        """Comprehensive terrain analysis"""
        return {
            'slope': self.analyzer.compute_slope(dem),
            'aspect': self.analyzer.compute_aspect(dem),
            'profile_curvature': self.analyzer.compute_curvature(dem)[0],
            'planform_curvature': self.analyzer.compute_curvature(dem)[1],
            'elevation_stats': {
                'min': float(np.min(dem)),
                'max': float(np.max(dem)),
                'mean': float(np.mean(dem)),
                'std': float(np.std(dem)),
            }
        }


__all__ = ['TerrainModule', 'TerrainAnalyzer', 'TerrainConfig']
