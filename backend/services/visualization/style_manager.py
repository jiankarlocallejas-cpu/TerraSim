"""
Advanced styling system for geographic visualization.
Implements QGIS-like symbology with multiple renderer types:
- Single symbol
- Categorized (by attribute)
- Graduated (ranges)
- Rule-based
- Heatmap
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import visualization libraries
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass


class RenderType(Enum):
    """Rendering strategies for layers"""
    SINGLE_SYMBOL = "single_symbol"
    CATEGORIZED = "categorized"
    GRADUATED = "graduated"
    RULE_BASED = "rule_based"
    HEATMAP = "heatmap"


class SymbolType(Enum):
    """Types of symbols"""
    MARKER = "marker"
    LINE = "line"
    FILL = "fill"
    TEXT = "text"


class MarkerShape(Enum):
    """Marker shapes for point symbols"""
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    CROSS = "cross"
    STAR = "star"
    PENTAGON = "pentagon"


@dataclass
class Color:
    """Color representation with multiple formats"""
    r: int = 0  # 0-255
    g: int = 0  # 0-255
    b: int = 0  # 0-255
    a: int = 255  # 0-255 (alpha)
    
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> 'Color':
        """Create from RGB values"""
        return cls(r, g, b, 255)
    
    @classmethod
    def from_rgba(cls, r: int, g: int, b: int, a: int) -> 'Color':
        """Create from RGBA values"""
        return cls(r, g, b, a)
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create from hex color (#RRGGBB or #RRGGBBAA)"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return cls(r, g, b, 255)
        elif len(hex_color) == 8:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return cls(r, g, b, a)
        
        raise ValueError(f"Invalid hex color: {hex_color}")
    
    def to_rgb(self) -> Tuple[int, int, int]:
        """Convert to RGB tuple"""
        return (self.r, self.g, self.b)
    
    def to_rgba(self) -> Tuple[int, int, int, int]:
        """Convert to RGBA tuple"""
        return (self.r, self.g, self.b, self.a)
    
    def to_hex(self) -> str:
        """Convert to hex string"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def to_normalized(self) -> Tuple[float, float, float, float]:
        """Convert to normalized RGBA (0.0-1.0)"""
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a / 255.0)


class Symbol:
    """Base class for symbols"""
    
    def __init__(
        self,
        symbol_type: SymbolType,
        color: Optional[Color] = None,
        size: float = 5.0,
        opacity: float = 1.0
    ):
        self.symbol_type = symbol_type
        self.color = color or Color(0, 0, 0)
        self.size = size
        self.opacity = opacity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.symbol_type.value,
            'color': self.color.to_hex(),
            'size': self.size,
            'opacity': self.opacity,
        }


class MarkerSymbol(Symbol):
    """Marker symbol for point geometries"""
    
    def __init__(
        self,
        color: Optional[Color] = None,
        size: float = 5.0,
        shape: MarkerShape = MarkerShape.CIRCLE,
        outline_color: Optional[Color] = None,
        outline_width: float = 1.0
    ):
        super().__init__(SymbolType.MARKER, color, size)
        self.shape = shape
        self.outline_color = outline_color or Color(0, 0, 0)
        self.outline_width = outline_width
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'shape': self.shape.value,
            'outline_color': self.outline_color.to_hex(),
            'outline_width': self.outline_width,
        })
        return result


class LineSymbol(Symbol):
    """Line symbol for linestring geometries"""
    
    def __init__(
        self,
        color: Optional[Color] = None,
        width: float = 2.0,
        style: str = "solid"
    ):
        super().__init__(SymbolType.LINE, color, width)
        self.style = style  # "solid", "dashed", "dotted"
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['style'] = self.style
        return result


class FillSymbol(Symbol):
    """Fill symbol for polygon geometries"""
    
    def __init__(
        self,
        color: Optional[Color] = None,
        outline_color: Optional[Color] = None,
        outline_width: float = 1.0,
        hatch_pattern: Optional[str] = None
    ):
        super().__init__(SymbolType.FILL, color)
        self.outline_color = outline_color or Color(0, 0, 0)
        self.outline_width = outline_width
        self.hatch_pattern = hatch_pattern
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'outline_color': self.outline_color.to_hex(),
            'outline_width': self.outline_width,
            'hatch_pattern': self.hatch_pattern,
        })
        return result


class TextSymbol(Symbol):
    """Text symbol for labeling"""
    
    def __init__(
        self,
        text_field: str,
        color: Optional[Color] = None,
        font_size: float = 12.0,
        font_family: str = "Arial"
    ):
        super().__init__(SymbolType.TEXT, color, font_size)
        self.text_field = text_field
        self.font_family = font_family
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'text_field': self.text_field,
            'font_family': self.font_family,
        })
        return result


class Renderer:
    """Base class for renderers"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.render_type = None
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature"""
        raise NotImplementedError


class SingleSymbolRenderer(Renderer):
    """Render all features with same symbol"""
    
    def __init__(self, symbol: Symbol):
        super().__init__("Single Symbol")
        self.render_type = RenderType.SINGLE_SYMBOL
        self.symbol = symbol
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature"""
        return self.symbol


class CategorizedRenderer(Renderer):
    """Render features by category (attribute value)"""
    
    def __init__(self, attribute: str, symbol_map: Dict[str, Symbol], default_symbol: Optional[Symbol] = None):
        super().__init__(f"Categorized by {attribute}")
        self.render_type = RenderType.CATEGORIZED
        self.attribute = attribute
        self.symbol_map = symbol_map
        self.default_symbol = default_symbol or Symbol(SymbolType.MARKER, Color(128, 128, 128))
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature based on attribute"""
        try:
            value = None
            if hasattr(feature, 'properties') and feature.properties is not None:
                value = feature.properties.get(self.attribute) if isinstance(feature.properties, dict) else None
            elif hasattr(feature, '__getitem__'):
                try:
                    value = feature[self.attribute]
                except (KeyError, TypeError):
                    value = None
            
            if value is None:
                value = getattr(feature, self.attribute, None)
            
            # Handle None value safely
            if value is not None and value in self.symbol_map:
                return self.symbol_map[value]
            return self.default_symbol
        except Exception as e:
            logger.warning(f"Failed to get symbol: {e}")
            return self.default_symbol


class GraduatedRenderer(Renderer):
    """Render features in ranges (graduated classification)"""
    
    def __init__(
        self,
        attribute: str,
        ranges: List[Tuple[float, float, Symbol]]
    ):
        super().__init__(f"Graduated by {attribute}")
        self.render_type = RenderType.GRADUATED
        self.attribute = attribute
        self.ranges = ranges  # [(min, max, symbol), ...]
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature based on value ranges"""
        try:
            if hasattr(feature, 'properties'):
                value = feature.properties.get(self.attribute)
            elif hasattr(feature, '__getitem__'):
                value = feature[self.attribute]
            else:
                value = getattr(feature, self.attribute, None)
            
            if value is None:
                return None
            
            # Find matching range
            for min_val, max_val, symbol in self.ranges:
                if min_val <= value <= max_val:
                    return symbol
            
            # Return last range if value exceeds
            return self.ranges[-1][2] if self.ranges else None
        except Exception as e:
            logger.warning(f"Failed to get symbol: {e}")
            return None


class RuleBasedRenderer(Renderer):
    """Render features based on expression rules"""
    
    def __init__(self, rules: List[Tuple[str, Symbol]]):
        super().__init__("Rule-based")
        self.render_type = RenderType.RULE_BASED
        self.rules = rules  # [(expression, symbol), ...]
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature based on rules"""
        try:
            for expression, symbol in self.rules:
                if self._evaluate_expression(expression, feature):
                    return symbol
            
            return None
        except Exception as e:
            logger.warning(f"Failed to evaluate rules: {e}")
            return None
    
    def _evaluate_expression(self, expression: str, feature: Any) -> bool:
        """Evaluate expression against feature"""
        try:
            # Simple expression evaluator
            # In production, would use proper expression parser
            if hasattr(feature, 'properties'):
                context = feature.properties
            elif hasattr(feature, '__dict__'):
                context = feature.__dict__
            else:
                context = {}
            
            # Evaluate expression (simplified)
            return eval(expression, {"__builtins__": {}}, context)
        except:
            return False


class HeatmapRenderer(Renderer):
    """Render features as heatmap"""
    
    def __init__(
        self,
        attribute: str,
        colormap: str = "hot",
        radius: float = 10.0
    ):
        super().__init__(f"Heatmap by {attribute}")
        self.render_type = RenderType.HEATMAP
        self.attribute = attribute
        self.colormap = colormap
        self.radius = radius
    
    def get_symbol(self, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature (heatmap uses special rendering)"""
        # Heatmap doesn't use individual symbols
        return None


class StyleManager:
    """Manage styles and renderers for layers"""
    
    # Predefined color ramps
    COLOR_RAMPS = {
        'viridis': [
            Color(68, 1, 84),
            Color(59, 82, 139),
            Color(33, 145, 140),
            Color(253, 231, 37),
        ],
        'plasma': [
            Color(13, 8, 135),
            Color(204, 71, 120),
            Color(240, 175, 31),
            Color(240, 240, 39),
        ],
        'blues': [
            Color(247, 251, 255),
            Color(198, 219, 239),
            Color(67, 147, 195),
            Color(8, 48, 107),
        ],
        'reds': [
            Color(255, 247, 243),
            Color(253, 224, 220),
            Color(252, 146, 114),
            Color(222, 0, 0),
        ],
    }
    
    # Predefined layer styles
    PREDEFINED_STYLES = {
        'streets': {
            'type': SymbolType.LINE,
            'color': '#333333',
            'width': 2.0,
        },
        'buildings': {
            'type': SymbolType.FILL,
            'color': '#C0C0C0',
            'outline': '#808080',
        },
        'water': {
            'type': SymbolType.FILL,
            'color': '#0099FF',
            'outline': '#006699',
        },
        'vegetation': {
            'type': SymbolType.FILL,
            'color': '#00CC00',
            'outline': '#009900',
        },
    }
    
    def __init__(self):
        self.layer_renderers: Dict[str, Renderer] = {}
        self.layer_symbols: Dict[str, Symbol] = {}
    
    def set_layer_renderer(self, layer_name: str, renderer: Renderer) -> bool:
        """Set renderer for layer"""
        try:
            self.layer_renderers[layer_name] = renderer
            logger.info(f"Set renderer for {layer_name}: {renderer.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set renderer: {e}")
            return False
    
    def get_layer_renderer(self, layer_name: str) -> Optional[Renderer]:
        """Get renderer for layer"""
        return self.layer_renderers.get(layer_name)
    
    def get_feature_symbol(self, layer_name: str, feature: Any) -> Optional[Symbol]:
        """Get symbol for feature"""
        renderer = self.get_layer_renderer(layer_name)
        if renderer:
            return renderer.get_symbol(feature)
        
        return None
    
    def create_single_symbol_renderer(
        self,
        layer_name: str,
        symbol: Symbol
    ) -> bool:
        """Create single symbol renderer for layer"""
        renderer = SingleSymbolRenderer(symbol)
        return self.set_layer_renderer(layer_name, renderer)
    
    def create_categorized_renderer(
        self,
        layer_name: str,
        attribute: str,
        value_map: Dict[str, Symbol],
        default_symbol: Optional[Symbol] = None
    ) -> bool:
        """Create categorized renderer for layer"""
        renderer = CategorizedRenderer(attribute, value_map, default_symbol)
        return self.set_layer_renderer(layer_name, renderer)
    
    def create_graduated_renderer(
        self,
        layer_name: str,
        attribute: str,
        ranges: List[Tuple[float, float, Symbol]]
    ) -> bool:
        """Create graduated renderer for layer"""
        renderer = GraduatedRenderer(attribute, ranges)
        return self.set_layer_renderer(layer_name, renderer)
    
    def create_graduated_colors(
        self,
        layer_name: str,
        attribute: str,
        num_classes: int = 5,
        color_ramp: str = 'viridis'
    ) -> bool:
        """Create graduated renderer with color ramp"""
        try:
            colors = self.get_color_ramp(color_ramp, num_classes)
            
            # Create ranges with color symbols
            ranges = []
            # In real implementation, would query layer for min/max values
            step = 100 / num_classes
            for i, color in enumerate(colors):
                min_val = i * step
                max_val = (i + 1) * step
                symbol = MarkerSymbol(color=color)
                ranges.append((min_val, max_val, symbol))
            
            return self.create_graduated_renderer(layer_name, attribute, ranges)
        except Exception as e:
            logger.error(f"Failed to create graduated colors: {e}")
            return False
    
    def create_heatmap_renderer(
        self,
        layer_name: str,
        attribute: str,
        colormap: str = "hot"
    ) -> bool:
        """Create heatmap renderer for layer"""
        renderer = HeatmapRenderer(attribute, colormap=colormap)
        return self.set_layer_renderer(layer_name, renderer)
    
    def apply_predefined_style(self, layer_name: str, style_name: str) -> bool:
        """Apply predefined style to layer"""
        try:
            style_config = self.PREDEFINED_STYLES.get(style_name)
            if not style_config:
                logger.warning(f"Unknown style: {style_name}")
                return False
            
            # Create symbol from config
            symbol_type = style_config.get('type', SymbolType.FILL)
            color = Color.from_hex(style_config.get('color', '#000000'))
            
            if symbol_type == SymbolType.LINE:
                symbol = LineSymbol(
                    color=color,
                    width=style_config.get('width', 2.0)
                )
            elif symbol_type == SymbolType.FILL:
                outline_color = Color.from_hex(style_config.get('outline', '#000000'))
                symbol = FillSymbol(
                    color=color,
                    outline_color=outline_color
                )
            else:
                symbol = MarkerSymbol(color=color)
            
            return self.create_single_symbol_renderer(layer_name, symbol)
        except Exception as e:
            logger.error(f"Failed to apply style: {e}")
            return False
    
    def get_color_ramp(self, ramp_name: str, num_colors: int) -> List[Color]:
        """Get color ramp interpolated to num_colors"""
        try:
            colors = self.COLOR_RAMPS.get(ramp_name, self.COLOR_RAMPS['viridis'])
            
            if len(colors) == num_colors:
                return colors
            
            # Interpolate colors
            if not MATPLOTLIB_AVAILABLE:
                # Simple sampling
                step = len(colors) / num_colors
                interpolated = [colors[int(i * step)] for i in range(num_colors)]
                return interpolated
            
            # Use matplotlib for better interpolation
            try:
                import matplotlib.pyplot as plt_module
                import matplotlib.cm as cm_module
                
                # Get available colormaps safely
                try:
                    if hasattr(cm_module, 'colormaps'):
                        colormaps_func = getattr(cm_module, 'colormaps')
                        if callable(colormaps_func):
                            available_cmaps = list(colormaps_func())  # type: ignore
                        else:
                            available_cmaps = []
                    else:
                        available_cmaps = []
                except:
                    available_cmaps = []
                
                # Get colormap
                if hasattr(cm_module, 'get_cmap'):
                    try:
                        cmap = cm_module.get_cmap(ramp_name) if ramp_name in available_cmaps else cm_module.get_cmap('viridis')
                    except (AttributeError, ValueError):
                        cmap = cm_module.get_cmap('viridis')
                else:
                    cmap = plt_module.get_cmap('viridis')  # type: ignore
            except (ImportError, AttributeError, ValueError):
                # Fallback if matplotlib imports fail
                step = len(colors) / num_colors
                return [colors[int(i * step)] for i in range(num_colors)]
            
            interpolated = []
            for i in range(num_colors):
                normalized = i / (num_colors - 1) if num_colors > 1 else 0
                rgba = cmap(normalized)
                color = Color(
                    int(rgba[0] * 255),
                    int(rgba[1] * 255),
                    int(rgba[2] * 255),
                    int(rgba[3] * 255)
                )
                interpolated.append(color)
            
            return interpolated
        except Exception as e:
            logger.warning(f"Failed to get color ramp: {e}")
            return [Color(128, 128, 128)]
    
    def export_style(self, layer_name: str) -> Dict[str, Any]:
        """Export layer style to dictionary"""
        renderer = self.get_layer_renderer(layer_name)
        if not renderer:
            return {}
        
        return {
            'name': renderer.name,
            'type': renderer.render_type.value if renderer.render_type else None,
        }
