"""
Consolidated visualization services with unified rendering pipeline.

This module organizes visualization services for:
- GPU-accelerated rendering (ModernGL with OpenGL fallback)
- Layer management and composition
- Style and color management
- Theme and style definitions

Architecture:
- gpu_renderer: Unified GPU rendering engine with multi-backend support
- layer_manager: QGIS-like layer stack management
- style_manager: Advanced symbology and rendering styles
- themes/: Specialized visualization themes (World Machine, etc.)
"""

# GPU Rendering Engine
from .gpu_renderer import (
    RenderQuality,
    RenderStats,
    LODLevel,
    LODManager,
    VectorRasterizer,
    GPURenderEngine,
    TileRenderer,
    TkinterOpenGLCanvas,
    TerrainRenderer,
    RenderingPipeline,
)

# Layer Management
from .layer_manager import (
    LayerType,
    BlendMode,
    LayerProperties,
    Layer,
    LayerManager,
)

# Styling System
from .style_manager import (
    RenderType,
    SymbolType,
    MarkerShape,
    Color,
    Symbol,
    MarkerSymbol,
    LineSymbol,
    FillSymbol,
    TextSymbol,
    Renderer,
    SingleSymbolRenderer,
    CategorizedRenderer,
    GraduatedRenderer,
    RuleBasedRenderer,
    HeatmapRenderer,
    StyleManager,
)

# Themes
from . import themes
from .themes import (
    WorldMachineColorScheme,
    ErosionDepositionData,
    WorldMachineVisualizer,
    SimulationAnimationRenderer,
)

__all__ = [
    # GPU Rendering Engine
    'RenderQuality',
    'RenderStats',
    'LODLevel',
    'LODManager',
    'VectorRasterizer',
    'GPURenderEngine',
    'TileRenderer',
    'TkinterOpenGLCanvas',
    'TerrainRenderer',
    'RenderingPipeline',
    
    # Layer Management
    'LayerType',
    'BlendMode',
    'LayerProperties',
    'Layer',
    'LayerManager',
    
    # Styling System
    'RenderType',
    'SymbolType',
    'MarkerShape',
    'Color',
    'Symbol',
    'MarkerSymbol',
    'LineSymbol',
    'FillSymbol',
    'TextSymbol',
    'Renderer',
    'SingleSymbolRenderer',
    'CategorizedRenderer',
    'GraduatedRenderer',
    'RuleBasedRenderer',
    'HeatmapRenderer',
    'StyleManager',
    
    # Themes
    'themes',
    'WorldMachineColorScheme',
    'ErosionDepositionData',
    'WorldMachineVisualizer',
    'SimulationAnimationRenderer',
]
