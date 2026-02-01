"""
TerraSim Modules - Modular architecture for terrain analysis and simulation

Organized by domain:
- terrain: Terrain model and simulation
- analysis: Analysis tools and algorithms
- data: Data loading and processing
- export: Export and reporting
- visualization: Heatmaps and visual outputs
"""

from .terrain import TerrainModule
from .analysis import AnalysisModule
from .data import DataModule
from .export import ExportModule
from .visualization import VisualizationModule

__all__ = [
    'TerrainModule',
    'AnalysisModule',
    'DataModule',
    'ExportModule',
    'VisualizationModule',
]
