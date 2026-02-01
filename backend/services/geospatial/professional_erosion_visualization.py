"""
Professional Erosion Visualization Tools
Advanced rendering and visualization for erosion analysis results
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List, Sequence
from enum import Enum

logger = logging.getLogger(__name__)


class ErosionVisualizationMode(Enum):
    """Specialized visualization modes for erosion analysis"""
    ELEVATION_HEATMAP = "elevation_heatmap"
    CHANGE_MAGNITUDE = "change_magnitude"
    EROSION_DEPOSITION = "erosion_deposition"  # Red for erosion, blue for deposition
    VOLUME_CHANGE = "volume_change"
    SLOPE_MAP = "slope_map"
    HILLSHADE = "hillshade"
    CONTOURS = "contours"
    DIRECTION_ARROWS = "direction_arrows"  # Sediment transport direction


class ProfessionalErosionVisualizer:
    """Professional erosion-specific visualization engine"""
    
    # Colormaps for professional visualization
    COLORMAPS = {
        "elevation": "terrain",
        "change": "RdBu_r",  # Red-Blue reversed
        "erosion_deposition": "custom_erosion",  # Custom: Blue (deposition) to Red (erosion)
        "magnitude": "viridis",
        "slope": "hot",
        "volume": "plasma"
    }
    
    @staticmethod
    def calculate_difference_map(base_dem: np.ndarray, comparison_dem: np.ndarray) -> np.ndarray:
        """
        Calculate elevation difference map
        Positive = deposition, Negative = erosion
        """
        if base_dem.shape != comparison_dem.shape:
            raise ValueError("DEM arrays must have the same shape")
        
        difference = comparison_dem - base_dem
        return difference
    
    @staticmethod
    def classify_erosion_deposition(difference_map: np.ndarray, threshold: float = 0.1) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Classify pixels as erosion, deposition, or stable
        
        Returns:
            classified_map: 1=deposition, 0=stable, -1=erosion
            statistics: erosion/deposition volumes and areas
        """
        classified = np.zeros_like(difference_map)
        
        # Erosion (negative change > threshold)
        erosion_mask = difference_map < -threshold
        classified[erosion_mask] = -1
        
        # Deposition (positive change > threshold)
        deposition_mask = difference_map > threshold
        classified[deposition_mask] = 1
        
        # Calculate statistics
        erosion_volume = np.abs(difference_map[erosion_mask]).sum()
        deposition_volume = difference_map[deposition_mask].sum()
        
        stats = {
            "total_erosion_volume": float(erosion_volume),
            "total_deposition_volume": float(deposition_volume),
            "net_change": float(deposition_volume - erosion_volume),
            "erosion_area_pixels": int(np.sum(erosion_mask)),
            "deposition_area_pixels": int(np.sum(deposition_mask)),
            "mean_erosion_depth": float(np.mean(difference_map[erosion_mask])) if np.any(erosion_mask) else 0,
            "mean_deposition_depth": float(np.mean(difference_map[deposition_mask])) if np.any(deposition_mask) else 0
        }
        
        return classified, stats
    
    @staticmethod
    def calculate_slope(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
        """Calculate slope in degrees from DEM"""
        try:
            from scipy import ndimage
        except ImportError:
            logger.error("scipy required for slope calculation")
            return np.zeros_like(dem)
        
        # Calculate gradients
        x_gradient, y_gradient = np.gradient(dem, cell_size)
        
        # Calculate slope in radians, then convert to degrees
        slope_rad = np.arctan(np.sqrt(x_gradient**2 + y_gradient**2))
        slope_deg = np.degrees(slope_rad)
        
        return slope_deg
    
    @staticmethod
    def calculate_aspect(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
        """Calculate aspect (direction) from DEM in degrees (0-360)"""
        x_gradient, y_gradient = np.gradient(dem, cell_size)
        
        # Calculate aspect
        aspect = np.arctan2(-x_gradient, y_gradient)
        aspect = np.degrees(aspect)
        aspect[aspect < 0] += 360
        
        return aspect
    
    @staticmethod
    def calculate_hillshade(dem: np.ndarray, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
        """
        Calculate hillshade for 3D relief visualization
        
        Args:
            dem: Digital Elevation Model
            azimuth: Light source azimuth in degrees (0-360)
            altitude: Light source altitude in degrees (0-90)
        """
        # Convert angles to radians
        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)
        
        # Calculate gradients
        x, y = np.gradient(dem)
        
        # Calculate slope and aspect
        slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
        aspect = np.arctan2(-x, y)
        
        # Calculate shading
        shaded = (np.sin(altitude_rad) * np.cos(slope) +
                 np.cos(altitude_rad) * np.sin(slope) *
                 np.cos(azimuth_rad - aspect - np.pi/2))
        
        # Normalize to 0-255
        shaded = (shaded + 1) / 2 * 255
        
        return shaded.astype(np.uint8)
    
    @staticmethod
    def calculate_contours(dem: np.ndarray, interval: float = 10.0) -> Sequence[float]:
        """Generate contour levels from DEM"""
        min_elev = np.nanmin(dem)
        max_elev = np.nanmax(dem)
        
        contour_levels = np.arange(
            np.floor(min_elev / interval) * interval,
            np.ceil(max_elev / interval) * interval + interval,
            interval
        )
        
        return list(contour_levels)
    
    @staticmethod
    def normalize_for_visualization(data: np.ndarray, method: str = "minmax") -> np.ndarray:
        """
        Normalize data for visualization
        
        Args:
            data: Input data array
            method: "minmax" or "std" (standard deviation)
        """
        data_clean = data[~np.isnan(data)]
        
        if len(data_clean) == 0:
            return np.zeros_like(data)
        
        if method == "minmax":
            min_val = np.min(data_clean)
            max_val = np.max(data_clean)
            if max_val == min_val:
                return np.zeros_like(data)
            normalized = (data - min_val) / (max_val - min_val)
        
        elif method == "std":
            mean = np.mean(data_clean)
            std = np.std(data_clean)
            if std == 0:
                return np.zeros_like(data)
            normalized = (data - mean) / (3 * std)  # 3-sigma range
            normalized = np.clip(normalized, -1, 1)
            normalized = (normalized + 1) / 2  # Scale to 0-1
        
        else:
            normalized = data
        
        return normalized
    
    @staticmethod
    def create_erosion_deposition_colormap(data: np.ndarray, threshold: float = 0.1) -> np.ndarray:
        """
        Create RGB colormap for erosion (red) / deposition (blue) visualization
        
        Returns:
            RGB array (H x W x 3)
        """
        rgb = np.zeros((*data.shape, 3), dtype=np.uint8)
        
        # Normalize absolute values
        abs_data = np.abs(data)
        abs_norm = ProfessionalErosionVisualizer.normalize_for_visualization(abs_data)
        
        # Erosion = Red channel
        erosion_mask = data < -threshold
        rgb[erosion_mask, 0] = (abs_norm[erosion_mask] * 255).astype(np.uint8)
        
        # Deposition = Blue channel
        deposition_mask = data > threshold
        rgb[deposition_mask, 2] = (abs_norm[deposition_mask] * 255).astype(np.uint8)
        
        # Neutral gray for stable areas
        stable_mask = np.abs(data) <= threshold
        neutral = 128
        rgb[stable_mask] = neutral
        
        return rgb
    
    @staticmethod
    def apply_transparency_mask(rgb_array: np.ndarray, nodata_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Add alpha channel for transparency
        
        Returns:
            RGBA array (H x W x 4)
        """
        h, w = rgb_array.shape[:2]
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3] = rgb_array
        
        # Set alpha (255 = opaque, 0 = transparent)
        rgba[:, :, 3] = 255
        
        if nodata_mask is not None:
            rgba[nodata_mask, 3] = 0
        
        return rgba


class ErosionStatisticsCalculator:
    """Advanced statistics for erosion analysis results"""
    
    @staticmethod
    def calculate_volume_statistics(difference_map: np.ndarray, cell_area: float = 1.0) -> Dict[str, float]:
        """
        Calculate volume statistics from difference map
        
        Args:
            difference_map: Elevation difference (comparison - base)
            cell_area: Area of each cell in square meters
        """
        valid_data = difference_map[~np.isnan(difference_map)]
        
        if len(valid_data) == 0:
            return {}
        
        erosion_pixels = valid_data < 0
        deposition_pixels = valid_data > 0
        
        erosion_volume = np.abs(valid_data[erosion_pixels]).sum() * cell_area
        deposition_volume = valid_data[deposition_pixels].sum() * cell_area
        
        return {
            "total_volume_eroded": float(erosion_volume),
            "total_volume_deposited": float(deposition_volume),
            "net_volume_change": float(deposition_volume - erosion_volume),
            "mean_erosion_depth": float(np.mean(valid_data[erosion_pixels])) if np.any(erosion_pixels) else 0,
            "mean_deposition_depth": float(np.mean(valid_data[deposition_pixels])) if np.any(deposition_pixels) else 0,
            "std_elevation_change": float(np.std(valid_data)),
            "max_erosion": float(np.min(valid_data)),  # Most negative
            "max_deposition": float(np.max(valid_data)),  # Most positive
        }
    
    @staticmethod
    def calculate_change_statistics(difference_map: np.ndarray) -> Dict[str, Any]:
        """Calculate comprehensive change statistics"""
        valid_data = difference_map[~np.isnan(difference_map)]
        
        if len(valid_data) == 0:
            return {}
        
        return {
            "min_change": float(np.min(valid_data)),
            "max_change": float(np.max(valid_data)),
            "mean_change": float(np.mean(valid_data)),
            "median_change": float(np.median(valid_data)),
            "std_change": float(np.std(valid_data)),
            "change_percentiles": {
                "5th": float(np.percentile(valid_data, 5)),
                "25th": float(np.percentile(valid_data, 25)),
                "50th": float(np.percentile(valid_data, 50)),
                "75th": float(np.percentile(valid_data, 75)),
                "95th": float(np.percentile(valid_data, 95))
            }
        }
    
    @staticmethod
    def generate_change_histogram(difference_map: np.ndarray, bins: int = 50) -> Tuple[List[float], List[int]]:
        """Generate histogram of elevation changes"""
        valid_data = difference_map[~np.isnan(difference_map)]
        
        if len(valid_data) == 0:
            return [], []
        
        counts, bin_edges = np.histogram(valid_data, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        return bin_centers.tolist(), counts.tolist()
