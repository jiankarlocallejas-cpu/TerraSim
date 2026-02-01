"""
Advanced Styling and Symbology System.
Professional map styling with graduated colors, categorized symbols, SVG markers, heatmaps.

Features:
- Categorized styling
- Graduated color schemes
- SVG markers and symbols
- Heatmap styling
- Label rendering
- Style templates
"""

import logging
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import colorsys
import json
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry.base import BaseGeometry
import geopandas as gpd
from geopandas import GeoDataFrame

logger = logging.getLogger(__name__)


class SymbolType(Enum):
    """Available symbol types."""
    MARKER = "marker"
    STROKE = "stroke"
    FILL = "fill"
    SVG = "svg"
    ICON = "icon"


class ColorScheme(Enum):
    """Color scheme presets."""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    COOL = "cool"
    WARM = "warm"
    REDS = "reds"
    BLUES = "blues"
    GREENS = "greens"
    GREYS = "greys"
    TERRAIN = "terrain"
    RAINBOW = "rainbow"


@dataclass
class Color:
    """Color representation (RGBA)."""
    red: int = 0
    green: int = 0
    blue: int = 0
    alpha: int = 255
    
    def to_hex(self) -> str:
        """Convert to hex color string."""
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"
    
    def to_rgb(self) -> Tuple[int, int, int]:
        """Get RGB tuple."""
        return (self.red, self.green, self.blue)
    
    def to_rgba(self) -> Tuple[int, int, int, int]:
        """Get RGBA tuple."""
        return (self.red, self.green, self.blue, self.alpha)
    
    @staticmethod
    def from_hex(hex_color: str) -> 'Color':
        """Create from hex string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16) if len(hex_color) == 8 else 255
        return Color(r, g, b, a)
    
    @staticmethod
    def interpolate(color1: 'Color', color2: 'Color', factor: float) -> 'Color':
        """Interpolate between two colors."""
        r = int(color1.red + (color2.red - color1.red) * factor)
        g = int(color1.green + (color2.green - color1.green) * factor)
        b = int(color1.blue + (color2.blue - color1.blue) * factor)
        a = int(color1.alpha + (color2.alpha - color1.alpha) * factor)
        return Color(r, g, b, a)


@dataclass
class Symbol:
    """Vector symbol definition."""
    type: SymbolType
    size: float = 5.0
    color: Color = field(default_factory=lambda: Color(0, 0, 0))
    outline_color: Color = field(default_factory=lambda: Color(255, 255, 255))
    outline_width: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    svg_path: Optional[str] = None  # For SVG symbols
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': self.type.value,
            'size': self.size,
            'color': self.color.to_hex(),
            'outline_color': self.outline_color.to_hex(),
            'outline_width': self.outline_width,
            'rotation': self.rotation,
            'opacity': self.opacity,
            'svg_path': self.svg_path,
            'properties': self.properties
        }


@dataclass
class Label:
    """Label styling."""
    label_field: str  # Field to label
    font_name: str = "Arial"
    font_size: int = 10
    font_color: Color = field(default_factory=lambda: Color(0, 0, 0))
    background_color: Optional[Color] = None
    halo_color: Optional[Color] = None
    halo_width: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    placement: str = "over"  # over, under, left, right
    anchor: str = "center"  # center, top, bottom, left, right
    angle: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)


class LayerStyle:
    """Complete layer styling configuration."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.symbol: Optional[Symbol] = None
        self.label: Optional[Label] = None
        self.opacity: float = 1.0
        self.blend_mode: str = "normal"
        self.effect_enabled: bool = False
        self.effect_type: str = "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'symbol': self.symbol.to_dict() if self.symbol else None,
            'label': {
                'field': self.label.label_field,
                'font_name': self.label.font_name,
                'font_size': self.label.font_size,
                'color': self.label.font_color.to_hex(),
            } if self.label else None,
            'opacity': self.opacity,
            'blend_mode': self.blend_mode,
            'effect_enabled': self.effect_enabled,
            'effect_type': self.effect_type
        }


class StyleRenderer:
    """Renders features with styling."""
    
    def __init__(self):
        self.color_schemes = self._init_color_schemes()
    
    def _init_color_schemes(self) -> Dict[str, List[Tuple[int, int, int]]]:
        """Initialize color scheme palettes."""
        return {
            'viridis': [(68, 1, 84), (59, 82, 139), (33, 145, 140), (253, 231, 37)],
            'plasma': [(12, 7, 134), (126, 3, 168), (245, 59, 42), (240, 240, 124)],
            'cool': [(0, 0, 255), (0, 255, 255), (0, 255, 0)],
            'warm': [(255, 0, 0), (255, 128, 0), (255, 255, 0)],
            'reds': [(255, 245, 240), (254, 224, 144), (253, 174, 97), (215, 48, 39)],
            'blues': [(247, 251, 255), (198, 219, 239), (107, 174, 214), (8, 81, 156)],
            'greens': [(247, 252, 245), (199, 237, 204), (81, 200, 126), (0, 100, 0)],
        }
    
    def create_categorized_style(
        self,
        gdf: GeoDataFrame,
        column: str,
        colors: Optional[List[str]] = None
    ) -> Dict[str, Symbol]:
        """
        Create categorized styling based on column values.
        
        Args:
            gdf: GeoDataFrame
            column: Column name for categorization
            colors: List of hex colors
            
        Returns:
            Dict of {category_value: Symbol}
        """
        try:
            categories = gdf[column].unique()
            
            if colors is None:
                # Generate colors
                colors = self._generate_palette(len(categories), ColorScheme.VIRIDIS)
            
            styles = {}
            for i, category in enumerate(categories):
                color = Color.from_hex(colors[i % len(colors)])
                symbol = Symbol(
                    type=self._get_symbol_type(gdf),
                    color=color,
                    size=8.0
                )
                styles[str(category)] = symbol
            
            return styles
            
        except Exception as e:
            logger.error(f"Categorized style error: {e}")
            raise
    
    def create_graduated_style(
        self,
        gdf: GeoDataFrame,
        column: str,
        method: str = 'equal_interval',
        num_classes: int = 5,
        color_scheme: ColorScheme = ColorScheme.VIRIDIS
    ) -> Dict[Tuple[float, float], Symbol]:
        """
        Create graduated color styling for numeric column.
        
        Args:
            gdf: GeoDataFrame
            column: Column name
            method: 'equal_interval', 'quantile', 'natural_breaks'
            num_classes: Number of classes
            color_scheme: Color scheme
            
        Returns:
            Dict of {(min, max): Symbol}
        """
        try:
            values = gdf[column].values
            
            # Convert ExtensionArray to numpy array
            values_array = np.asarray(values, dtype=np.float64)
            min_val = float(values_array.min())
            max_val = float(values_array.max())
            breaks = np.percentile(values_array, np.linspace(0, 100, num_classes + 1))
            
            # Get color palette
            colors = self._generate_palette(num_classes, color_scheme)
            
            # Create styles
            styles = {}
            for i in range(len(breaks) - 1):
                color = Color.from_hex(colors[i])
                symbol = Symbol(
                    type=self._get_symbol_type(gdf),
                    color=color,
                    size=6.0
                )
                styles[(breaks[i], breaks[i + 1])] = symbol
            
            return styles
            
        except Exception as e:
            logger.error(f"Graduated style error: {e}")
            raise
    
    def create_heatmap_style(
        self,
        gdf: GeoDataFrame,
        column: str,
        color_scheme: ColorScheme = ColorScheme.TERRAIN
    ) -> Callable:
        """
        Create heatmap styling based on value intensity.
        
        Args:
            gdf: GeoDataFrame
            column: Column name
            color_scheme: Color scheme
            
        Returns:
            Function that returns color for value
        """
        try:
            values = gdf[column].values
            
            # Convert ExtensionArray to numpy array for min/max
            values_array = np.asarray(values, dtype=np.float64)
            min_val = float(values_array.min())
            max_val = float(values_array.max())
            
            colors = self._generate_palette(256, color_scheme)
            
            def get_color(value: float) -> str:
                if value < min_val or value > max_val:
                    return colors[0]
                
                normalized = (value - min_val) / (max_val - min_val)
                index = int(normalized * (len(colors) - 1))
                return colors[index]
            
            return get_color
            
        except Exception as e:
            logger.error(f"Heatmap style error: {e}")
            raise
    
    def _get_symbol_type(self, gdf: GeoDataFrame) -> SymbolType:
        """Determine symbol type from geometry."""
        geom_type = gdf.geometry.geom_type.values[0]
        
        if geom_type == 'Point':
            return SymbolType.MARKER
        elif geom_type in ['LineString', 'MultiLineString']:
            return SymbolType.STROKE
        else:
            return SymbolType.FILL
    
    def _generate_palette(
        self,
        n: int,
        scheme: ColorScheme
    ) -> List[str]:
        """Generate color palette."""
        scheme_colors = self.color_schemes.get(scheme.value, self.color_schemes['viridis'])
        
        # Interpolate colors
        palette = []
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0.5
            
            # Find two colors to interpolate between
            index = t * (len(scheme_colors) - 1)
            lower_idx = int(np.floor(index))
            upper_idx = int(np.ceil(index))
            
            if lower_idx == upper_idx:
                color_tuple = scheme_colors[lower_idx]
            else:
                factor = index - lower_idx
                c1 = scheme_colors[lower_idx]
                c2 = scheme_colors[upper_idx]
                color_tuple = tuple(
                    int(c1[j] + (c2[j] - c1[j]) * factor)
                    for j in range(3)
                )
            
            hex_color = f"#{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}"
            palette.append(hex_color)
        
        return palette


class SVGMarkerLibrary:
    """Library of SVG marker symbols."""
    
    @staticmethod
    def circle(radius: float = 5, fill: str = "black", stroke: str = "white") -> str:
        """Create circle SVG."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
            <circle cx="10" cy="10" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>
        </svg>'''
    
    @staticmethod
    def square(size: float = 10, fill: str = "black", stroke: str = "white") -> str:
        """Create square SVG."""
        offset = size / 2
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
            <rect x="{10-offset}" y="{10-offset}" width="{size}" height="{size}" 
                  fill="{fill}" stroke="{stroke}" stroke-width="1"/>
        </svg>'''
    
    @staticmethod
    def triangle(size: float = 8, fill: str = "black", stroke: str = "white") -> str:
        """Create triangle SVG."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
            <polygon points="10,2 18,18 2,18" fill="{fill}" stroke="{stroke}" stroke-width="1"/>
        </svg>'''
    
    @staticmethod
    def star(points: int = 5, fill: str = "gold", stroke: str = "orange") -> str:
        """Create star SVG."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
            <polygon points="10,2 13,10 21,10 15,15 18,23 10,18 2,23 5,15 -1,10 7,10" 
                     fill="{fill}" stroke="{stroke}" stroke-width="1"/>
        </svg>'''


# Module exports
__all__ = [
    'StyleRenderer',
    'SVGMarkerLibrary',
    'Symbol',
    'Color',
    'Label',
    'LayerStyle',
    'ColorScheme',
    'SymbolType'
]
