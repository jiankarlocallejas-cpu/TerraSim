"""
TerraSim Professional - Comprehensive Integration Example
Shows how to use all professional components together in a real workflow
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import professional components
from backend.services.geospatial.professional_layer_manager import (
    ProfessionalLayerManager,
    Layer,
    LayerType,
    LayerStyle,
    RenderingMode,
    LayerMetadata,
    ErosionLayerGroup
)

from backend.services.geospatial.professional_erosion_visualization import (
    ProfessionalErosionVisualizer,
    ErosionStatisticsCalculator
)

from backend.services.geospatial.professional_data_io import (
    ProfessionalDataImporter,
    ProfessionalDataExporter,
    DataQualityValidator
)


class TerraSimProfessionalWorkflow:
    """
    Professional workflow for erosion analysis
    Demonstrates integration of all components
    """
    
    def __init__(self):
        self.layer_manager = ProfessionalLayerManager()
        self.analysis_groups: Dict[str, ErosionLayerGroup] = {}
        logger.info("Initialized TerraSim Professional Workflow")
    
    def load_dem_data(self, file_path: str, layer_name: str) -> Optional[Layer]:
        """
        Load and validate DEM data
        
        Args:
            file_path: Path to DEM file
            layer_name: Name for the layer
        
        Returns:
            Layer object or None if validation fails
        """
        try:
            logger.info(f"Loading DEM: {file_path}")
            
            # Import
            imported = ProfessionalDataImporter.import_generic(file_path)
            dem_data = imported["data"]
            dem_metadata = imported["metadata"]
            
            # Validate
            validation = DataQualityValidator.validate_dem(dem_data)
            if not validation["valid"]:
                logger.error(f"DEM validation failed: {validation['issues']}")
                return None
            
            logger.info(f"DEM validation passed. Statistics: {validation['statistics']}")
            
            # Create layer
            layer = Layer(
                name=layer_name,
                layer_type=LayerType.BASE_TERRAIN,
                data=dem_data,
                metadata=LayerMetadata(
                    name=layer_name,
                    layer_type=LayerType.BASE_TERRAIN,
                    crs=dem_metadata.get("crs", "EPSG:4326"),
                    extent=self._get_extent_from_dem(dem_data),
                    source_file=file_path,
                    file_format=imported.get("file_format", "Unknown"),
                    spatial_resolution=dem_metadata.get("resolution", [1.0, 1.0])[0]
                ),
                style=LayerStyle(
                    colormap="terrain",
                    opacity=0.8,
                    rendering_mode=RenderingMode.ELEVATION
                )
            )
            
            # Add to manager
            self.layer_manager.add_layer(layer, group="Terrain Data")
            logger.info(f"Added DEM layer: {layer_name}")
            
            return layer
            
        except Exception as e:
            logger.error(f"Error loading DEM: {e}")
            return None
    
    @staticmethod
    def _get_extent_from_dem(dem_data: np.ndarray) -> tuple:
        """Get extent bounds from DEM"""
        h, w = dem_data.shape
        return (0, 0, w, h)  # (xmin, ymin, xmax, ymax)
    
    async def run_erosion_analysis(
        self,
        base_dem_name: str,
        comparison_dem_name: str,
        analysis_name: str,
        threshold_m: float = 0.1,
        cell_size_m: float = 1.0
    ) -> Optional[ErosionLayerGroup]:
        """
        Run complete erosion analysis workflow
        
        Args:
            base_dem_name: Name of base DEM layer
            comparison_dem_name: Name of comparison DEM layer
            analysis_name: Name for this analysis
            threshold_m: Minimum change threshold in meters
            cell_size_m: Cell size in meters
        
        Returns:
            ErosionLayerGroup with all results
        """
        logger.info(f"Starting erosion analysis: {analysis_name}")
        
        # Get layers
        base_layer = self.layer_manager.get_layer(base_dem_name)
        comparison_layer = self.layer_manager.get_layer(comparison_dem_name)
        
        if not base_layer or not comparison_layer:
            logger.error("Required DEM layers not found")
            return None
        
        base_dem = base_layer.data if base_layer else None
        comparison_dem = comparison_layer.data if comparison_layer else None
        
        if base_dem is None or comparison_dem is None:
            raise ValueError("Base and comparison DEMs are required")
        
        logger.info("Step 1: Calculating elevation difference...")
        difference = ProfessionalErosionVisualizer.calculate_difference_map(
            base_dem, comparison_dem
        )
        
        logger.info("Step 2: Classifying erosion vs deposition...")
        classified, class_stats = ProfessionalErosionVisualizer.classify_erosion_deposition(
            difference, threshold=threshold_m
        )
        
        logger.info("Step 3: Calculating volume statistics...")
        vol_stats = ErosionStatisticsCalculator.calculate_volume_statistics(
            difference, cell_area=cell_size_m**2
        )
        
        logger.info("Step 4: Calculating change statistics...")
        change_stats = ErosionStatisticsCalculator.calculate_change_statistics(difference)
        
        logger.info("Step 5: Generating visualizations...")
        
        # Erosion/Deposition visualization
        erosion_deposition_viz = ProfessionalErosionVisualizer.create_erosion_deposition_colormap(
            difference, threshold=threshold_m
        )
        
        # Slope map
        if base_dem is not None:
            slope = ProfessionalErosionVisualizer.calculate_slope(base_dem, cell_size=cell_size_m)
        else:
            slope = None
        
        # Hillshade
        if base_dem is not None:
            hillshade = ProfessionalErosionVisualizer.calculate_hillshade(
                base_dem, azimuth=315, altitude=45
            )
        else:
            hillshade = None
        
        logger.info("Step 6: Creating result layers...")
        
        # Create erosion result layer
        erosion_layer = Layer(
            name=f"{analysis_name} - Erosion Results",
            layer_type=LayerType.EROSION_RESULT,
            data=erosion_deposition_viz,
            style=LayerStyle(
                colormap="custom_erosion",
                opacity=0.8,
                rendering_mode=RenderingMode.EROSION_DEPOSITION
            ),
            analysis_results={
                "classification_stats": class_stats,
                "volume_stats": vol_stats,
                "change_stats": change_stats
            }
        )
        
        # Create difference map layer
        difference_layer = Layer(
            name=f"{analysis_name} - Difference Map",
            layer_type=LayerType.EROSION_RESULT,
            data=difference,
            style=LayerStyle(
                colormap="RdBu_r",
                opacity=0.7,
                rendering_mode=RenderingMode.DIFFERENCE
            )
        )
        
        # Create slope layer
        slope_layer = Layer(
            name=f"{analysis_name} - Slope",
            layer_type=LayerType.RASTER_DATA,
            data=slope,
            style=LayerStyle(
                colormap="hot",
                opacity=0.6,
                rendering_mode=RenderingMode.SLOPE
            )
        )
        
        # Create hillshade layer
        hillshade_layer = Layer(
            name=f"{analysis_name} - Hillshade",
            layer_type=LayerType.RASTER_DATA,
            data=hillshade,
            style=LayerStyle(
                opacity=0.5,
                rendering_mode=RenderingMode.HILLSHADE
            )
        )
        
        # Add all layers
        group = f"Analysis: {analysis_name}"
        self.layer_manager.add_layer(erosion_layer, group=group)
        self.layer_manager.add_layer(difference_layer, group=group)
        self.layer_manager.add_layer(slope_layer, group=group)
        
        # Create analysis group
        analysis_group = ErosionLayerGroup(analysis_name)
        analysis_group.add_base_dem(base_layer)
        analysis_group.add_comparison_dem(comparison_layer)
        analysis_group.set_results(erosion_layer, difference_layer, erosion_layer)
        analysis_group.metadata = {
            "threshold": threshold_m,
            "cell_size": cell_size_m,
            "classification_stats": class_stats,
            "volume_stats": vol_stats,
            "change_stats": change_stats,
            "slope_stats": {
                "min": float(np.nanmin(slope)) if slope is not None else 0,
                "max": float(np.nanmax(slope)) if slope is not None else 0,
                "mean": float(np.nanmean(slope)) if slope is not None else 0
            }
        }
        
        self.analysis_groups[analysis_name] = analysis_group
        
        logger.info(f"Erosion analysis completed: {analysis_name}")
        logger.info(f"  Erosion volume: {vol_stats.get('total_volume_eroded', 0):.2f} m³")
        logger.info(f"  Deposition volume: {vol_stats.get('total_volume_deposited', 0):.2f} m³")
        logger.info(f"  Net change: {vol_stats.get('net_change', 0):.2f} m³")
        
        return analysis_group
    
    def export_analysis_results(
        self,
        analysis_name: str,
        output_dir: str
    ) -> bool:
        """
        Export analysis results to files
        
        Args:
            analysis_name: Name of analysis group
            output_dir: Directory to save results
        
        Returns:
            True if successful
        """
        logger.info(f"Exporting analysis: {analysis_name}")
        
        analysis_group = self.analysis_groups.get(analysis_name)
        if not analysis_group:
            logger.error(f"Analysis not found: {analysis_name}")
            return False
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Export difference map
            if analysis_group.difference_map is not None:
                ProfessionalDataExporter.export_geotiff(
                    analysis_group.difference_map,
                    str(output_path / f"{analysis_name}_difference.tif"),
                    compress="lzw"
                )
            
            # Export metadata
            metadata_file = output_path / f"{analysis_name}_metadata.json"
            import json
            with open(metadata_file, 'w') as f:
                json.dump(analysis_group.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Results exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return False
    
    def get_analysis_summary(self, analysis_name: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for an analysis"""
        analysis_group = self.analysis_groups.get(analysis_name)
        if not analysis_group:
            return None
        
        return analysis_group.metadata


async def example_workflow():
    """Example complete workflow"""
    logger.info("=" * 60)
    logger.info("TerraSim Professional - Example Erosion Analysis Workflow")
    logger.info("=" * 60)
    
    # Initialize workflow
    workflow = TerraSimProfessionalWorkflow()
    
    # Create synthetic DEM data for demonstration
    logger.info("\nCreating synthetic DEM data for demonstration...")
    h, w = 256, 256
    
    # Base terrain - cone shape
    y, x = np.ogrid[0:h, 0:w]
    center = np.array([h/2, w/2])
    distance = np.sqrt((y - center[0])**2 + (x - center[1])**2)
    base_dem = 1000 - distance * 2
    base_dem = np.maximum(base_dem, 0)
    
    # Comparison terrain - slightly eroded
    comparison_dem = base_dem.copy()
    comparison_dem[:80, :80] -= np.random.rand(80, 80) * 20  # Erosion
    comparison_dem[170:220, 170:220] += np.random.rand(50, 50) * 15  # Deposition
    
    # Create temporary files for demonstration
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save synthetic DEMs (using numpy for simplicity)
        base_dem_file = Path(tmpdir) / "base_dem.npy"
        comparison_dem_file = Path(tmpdir) / "comparison_dem.npy"
        
        np.save(base_dem_file, base_dem)
        np.save(comparison_dem_file, comparison_dem)
        
        logger.info("Base DEM created")
        logger.info("Comparison DEM created")
        
        # Manually create layers from numpy files (since we're using synthetic data)
        logger.info("\nLoading DEMs into layer manager...")
        
        base_layer = Layer(
            name="Base DEM 2020",
            layer_type=LayerType.BASE_TERRAIN,
            data=base_dem,
            metadata=LayerMetadata(
                name="Base DEM 2020",
                crs="EPSG:32633",
                extent=(0, 0, w, h),
                spatial_resolution=1.0
            ),
            style=LayerStyle(colormap="terrain", rendering_mode=RenderingMode.ELEVATION)
        )
        workflow.layer_manager.add_layer(base_layer, group="Survey Data")
        
        comparison_layer = Layer(
            name="Comparison DEM 2023",
            layer_type=LayerType.COMPARISON_DEM,
            data=comparison_dem,
            metadata=LayerMetadata(
                name="Comparison DEM 2023",
                crs="EPSG:32633",
                extent=(0, 0, w, h),
                spatial_resolution=1.0
            ),
            style=LayerStyle(colormap="terrain", rendering_mode=RenderingMode.ELEVATION)
        )
        workflow.layer_manager.add_layer(comparison_layer, group="Survey Data")
        
        # Run erosion analysis
        logger.info("\nRunning erosion analysis...")
        analysis_group = await workflow.run_erosion_analysis(
            base_dem_name="Base DEM 2020",
            comparison_dem_name="Comparison DEM 2023",
            analysis_name="Hillslope Erosion 2020-2023",
            threshold_m=0.5,
            cell_size_m=1.0
        )
        
        if analysis_group:
            # Print results
            logger.info("\n" + "=" * 60)
            logger.info("ANALYSIS RESULTS")
            logger.info("=" * 60)
            summary = workflow.get_analysis_summary("Hillslope Erosion 2020-2023")
            if summary:
                print("\nVolume Statistics:")
                print(f"  Total Erosion: {summary['volume_stats']['total_volume_eroded']:.2f} m³")
                print(f"  Total Deposition: {summary['volume_stats']['total_volume_deposited']:.2f} m³")
                print(f"  Net Change: {summary['volume_stats']['net_change']:.2f} m³")
                
                print("\nChange Statistics:")
                print(f"  Min Change: {summary['change_stats']['min_change']:.4f} m")
                print(f"  Max Change: {summary['change_stats']['max_change']:.4f} m")
                print(f"  Mean Change: {summary['change_stats']['mean_change']:.4f} m")
                print(f"  Std Dev: {summary['change_stats']['std_change']:.4f} m")
                
                print("\nSlope Statistics:")
                print(f"  Min: {summary['slope_stats']['min']:.2f}°")
                print(f"  Max: {summary['slope_stats']['max']:.2f}°")
                print(f"  Mean: {summary['slope_stats']['mean']:.2f}°")
            
            # Export results
            logger.info("\n" + "=" * 60)
            logger.info("Exporting results...")
            output_dir = Path(tmpdir) / "output"
            workflow.export_analysis_results("Hillslope Erosion 2020-2023", str(output_dir))
            
            # List all layers
            logger.info("\n" + "=" * 60)
            logger.info("All Layers in Project:")
            logger.info("=" * 60)
            for layer in workflow.layer_manager.get_all_layers():
                stats = layer.get_statistics()
                logger.info(f"\n{layer.name}")
                logger.info(f"  Type: {layer.layer_type.value}")
                logger.info(f"  Visible: {layer.visible}")
                logger.info(f"  Data range: {stats.get('min', 'N/A'):.2f} - {stats.get('max', 'N/A'):.2f}")


def main():
    """Run example workflow"""
    asyncio.run(example_workflow())
    logger.info("\n" + "=" * 60)
    logger.info("Example workflow complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
