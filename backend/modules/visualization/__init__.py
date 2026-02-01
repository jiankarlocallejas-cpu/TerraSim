"""
Visualization Module - Heatmaps and visual outputs

Handles:
- Heatmap generation
- Color mapping
- Legend generation
- Visualization caching
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path


@dataclass
class VisualizationConfig:
    """Configuration for visualization operations"""
    colormap: str = 'viridis'
    output_format: str = 'png'
    dpi: int = 150
    cache_enabled: bool = True


class HeatmapGenerator:
    """Generates heatmap visualizations"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
    
    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1 range for visualization"""
        if data.size == 0:
            return np.array([])
        
        data_min = np.nanmin(data)
        data_max = np.nanmax(data)
        
        if data_max == data_min:
            return np.zeros_like(data)
        
        normalized = (data - data_min) / (data_max - data_min)
        normalized = np.nan_to_num(normalized, nan=0.0)
        return np.clip(normalized, 0, 1)
    
    def apply_colormap(self, data: np.ndarray, colormap: Optional[str] = None) -> np.ndarray:
        """Apply colormap to normalized data"""
        try:
            import matplotlib.pyplot as plt
            
            cmap_name = colormap or self.config.colormap
            cmap = plt.get_cmap(cmap_name)
            
            normalized = self.normalize_data(data)
            colored = cmap(normalized)
            
            # Return RGBA as 0-255 integers
            return (colored[:, :, :3] * 255).astype(np.uint8)
        
        except ImportError:
            raise RuntimeError("matplotlib not installed for visualization")
    
    def generate_heatmap_data(
        self,
        data: np.ndarray,
        colormap: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate heatmap data for transmission"""
        normalized = self.normalize_data(data)
        
        return {
            'data': normalized.tolist(),
            'min': float(np.nanmin(data)),
            'max': float(np.nanmax(data)),
            'mean': float(np.nanmean(data)),
            'colormap': colormap or self.config.colormap,
            'shape': data.shape,
        }
    
    def generate_legend(
        self,
        min_val: float,
        max_val: float,
        num_colors: int = 10
    ) -> Dict[str, Any]:
        """Generate legend data"""
        values = np.linspace(min_val, max_val, num_colors)
        
        return {
            'values': values.tolist(),
            'colors': [f'rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)})'
                      for c in self._get_colors(num_colors)]
        }
    
    def _get_colors(self, num_colors: int) -> list:
        """Get color array from colormap"""
        try:
            import matplotlib.pyplot as plt
            
            cmap = plt.get_cmap(self.config.colormap)
            indices = np.linspace(0, 1, num_colors)
            return [cmap(idx) for idx in indices]
        
        except ImportError:
            # Fallback grayscale
            indices = np.linspace(0, 1, num_colors)
            return [(idx, idx, idx, 1.0) for idx in indices]


class VisualizationModule:
    """Main visualization module"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.heatmap = HeatmapGenerator(self.config)
    
    def create_visualization(
        self,
        data: np.ndarray,
        title: str = 'Analysis Result',
        colormap: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create complete visualization data"""
        return {
            'title': title,
            'heatmap': self.heatmap.generate_heatmap_data(data, colormap),
            'legend': self.heatmap.generate_legend(
                float(np.nanmin(data)),
                float(np.nanmax(data))
            ),
            'metadata': {
                'shape': data.shape,
                'dtype': str(data.dtype),
                'invalid_count': int(np.sum(~np.isfinite(data))),
            }
        }


__all__ = ['VisualizationModule', 'HeatmapGenerator', 'VisualizationConfig']
