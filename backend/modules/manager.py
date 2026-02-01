"""
Module Manager - Centralized management of all modules

Provides unified access to terrain analysis, data processing, export, and visualization modules.
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path
import numpy as np

from .terrain import TerrainModule, TerrainConfig
from .analysis import AnalysisModule, AnalysisConfig
from .data import DataModule, DataConfig
from .export import ExportModule, ExportConfig
from .visualization import VisualizationModule, VisualizationConfig


class ModuleManager:
    """Central manager for all TerraSim modules"""
    
    def __init__(
        self,
        terrain_config: Optional[TerrainConfig] = None,
        analysis_config: Optional[AnalysisConfig] = None,
        data_config: Optional[DataConfig] = None,
        export_config: Optional[ExportConfig] = None,
        viz_config: Optional[VisualizationConfig] = None,
    ):
        self.terrain = TerrainModule(terrain_config)
        self.analysis = AnalysisModule(analysis_config)
        self.data = DataModule(data_config)
        self.export = ExportModule(export_config)
        self.visualization = VisualizationModule(viz_config)
    
    def run_complete_analysis(
        self,
        dem_file: Union[str, Path],
        analysis_steps: int = 100,
        export_format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Run a complete analysis pipeline:
        1. Load DEM
        2. Analyze terrain
        3. Run erosion simulation
        4. Generate visualizations
        5. Export results
        """
        # Load data
        dem, metadata = self.data.load_dem(dem_file)
        
        # Analyze terrain
        terrain_analysis = self.terrain.analyze_dem(dem)
        
        # Run erosion analysis
        erosion_results = self.analysis.run_erosion_analysis(dem, analysis_steps)
        
        # Generate visualization
        viz = self.visualization.create_visualization(
            erosion_results['final_dem'],
            title='Erosion Simulation Results'
        )
        
        # Compile results
        complete_results = {
            'metadata': metadata,
            'terrain_analysis': {
                'slope_stats': {
                    'min': float(np.min(terrain_analysis['slope'])),
                    'max': float(np.max(terrain_analysis['slope'])),
                    'mean': float(np.mean(terrain_analysis['slope'])),
                },
                'aspect_stats': {
                    'min': float(np.min(terrain_analysis['aspect'])),
                    'max': float(np.max(terrain_analysis['aspect'])),
                    'mean': float(np.mean(terrain_analysis['aspect'])),
                },
            },
            'erosion_analysis': {
                'total_erosion': erosion_results['total_erosion'],
                'num_steps': len(erosion_results['steps']),
                'initial_elevation': float(np.mean(erosion_results['initial_dem'])),
                'final_elevation': float(np.mean(erosion_results['final_dem'])),
            },
            'visualization': viz,
        }
        
        return complete_results
    
    def export_analysis(
        self,
        results: Dict[str, Any],
        output_format: str = 'json',
        filename: Optional[str] = None
    ) -> Path:
        """Export analysis results in specified format"""
        return self.export.export_results(results, output_format, filename)


__all__ = ['ModuleManager']
