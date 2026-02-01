"""
GIS Service Integration - Connects GIS engine to TerraSim backend services.
Bridges GIS engine with existing TerraSim services (database, authentication, etc).
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from backend.models.analysis import Analysis
from backend.models.project import Project
from backend.models.pointcloud import PointCloud
from backend.models.raster import Raster
from backend.models.user import User

from .core import (
    TerraSIMGISEngine, RasterLayer, PointCloudLayer, 
    PointCloudStatistics, Extent, RasterBand
)


logger = logging.getLogger(__name__)


class GISServiceIntegration:
    """
    Bridges GIS engine with TerraSim database and services.
    """
    
    def __init__(self, engine: TerraSIMGISEngine):
        self.engine = engine
    
    # Database Integration
    def load_project_layers(self, db: Session, project_id: int) -> Dict[str, Any]:
        """Load all layers associated with a project."""
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.error(f"Project {project_id} not found")
                return {'success': False}
            
            layers_loaded = []
            
            # Load rasters
            rasters = db.query(Raster).filter(Raster.project_id == project_id).all()
            for raster in rasters:
                try:
                    layer = self.engine.load_layer(raster.file_path, name=raster.name)
                    if layer:
                        layers_loaded.append({
                            'id': layer.id,
                            'name': layer.name,
                            'type': 'raster',
                            'source_id': raster.id
                        })
                except Exception as e:
                    logger.warning(f"Failed to load raster {raster.id}: {str(e)}")
            
            # Load point clouds
            pointclouds = db.query(PointCloud).filter(PointCloud.project_id == project_id).all()
            for pc in pointclouds:
                try:
                    layer = self.engine.load_layer(pc.file_path, name=pc.name)
                    if layer:
                        layers_loaded.append({
                            'id': layer.id,
                            'name': layer.name,
                            'type': 'pointcloud',
                            'source_id': pc.id
                        })
                except Exception as e:
                    logger.warning(f"Failed to load point cloud {pc.id}: {str(e)}")
            
            return {
                'success': True,
                'project_id': project_id,
                'project_name': project.name,
                'layers_loaded': layers_loaded,
                'layer_count': len(layers_loaded)
            }
        
        except Exception as e:
            logger.error(f"Error loading project layers: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def save_analysis_results(self, db: Session, analysis_id: int, 
                            results: Dict[str, Any], user_id: int) -> bool:
        """Save analysis results to database."""
        try:
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                return False
            
            analysis.results = results
            analysis.status = 'completed'
            
            db.commit()
            logger.info(f"Saved results for analysis {analysis_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving analysis results: {str(e)}")
            db.rollback()
            return False
    
    def create_analysis_from_layers(self, db: Session, analysis_name: str,
                                   dem_layer_id: str, reference_dem_id: Optional[str],
                                   project_id: int, user_id: int) -> Optional[Analysis]:
        """Create database analysis record from loaded layers."""
        try:
            dem_layer = self.engine.get_layer(dem_layer_id)
            if not dem_layer:
                return None
            
            # Prepare analysis parameters
            params = {
                'dem_layer': dem_layer_id,
                'extent': dem_layer.extent.to_dict() if dem_layer.extent else None
            }
            
            if reference_dem_id:
                params['reference_dem'] = reference_dem_id
                analysis_type = 'erosion'
            else:
                analysis_type = 'dem_analysis'
            
            # Create database record
            analysis = Analysis(
                name=analysis_name,
                type=analysis_type,
                parameters=params,
                project_id=project_id,
                owner_id=user_id,
                status='pending'
            )
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            logger.info(f"Created analysis record: {analysis.id}")
            return analysis
        
        except Exception as e:
            logger.error(f"Error creating analysis: {str(e)}")
            db.rollback()
            return None
    
    # Conversion Methods
    def pointcloud_model_to_layer(self, pointcloud: PointCloud) -> Optional[PointCloudLayer]:
        """Convert database PointCloud model to PointCloudLayer."""
        try:
            pc_name = pointcloud.name or "Unnamed PointCloud"
            layer = PointCloudLayer(
                name=pc_name,
                source=pointcloud.file_path,
                crs=pointcloud.srs or 'EPSG:4326'
            )
            
            # Load statistics if available
            if pointcloud.pointcloud_metadata and 'statistics' in pointcloud.pointcloud_metadata:
                stats_data = pointcloud.pointcloud_metadata['statistics']
                stats = PointCloudStatistics(
                    point_count=stats_data.get('point_count', 0),
                    x_min=stats_data.get('x_min', 0),
                    x_max=stats_data.get('x_max', 0),
                    y_min=stats_data.get('y_min', 0),
                    y_max=stats_data.get('y_max', 0),
                    z_min=stats_data.get('z_min', 0),
                    z_max=stats_data.get('z_max', 0),
                    z_mean=stats_data.get('z_mean', 0),
                    z_std=stats_data.get('z_std', 0)
                )
                layer.load_statistics(stats)
            
            return layer
        except Exception as e:
            logger.error(f"Error converting PointCloud model: {str(e)}")
            return None
    
    def raster_model_to_layer(self, raster: Raster) -> Optional[RasterLayer]:
        """Convert database Raster model to RasterLayer."""
        try:
            raster_name = raster.name or "Unnamed Raster"
            # Use default dimensions if not specified
            width = getattr(raster, 'width', None) or 512
            height = getattr(raster, 'height', None) or 512
            layer = RasterLayer(
                name=raster_name,
                source=raster.file_path,
                crs=raster.srs or 'EPSG:4326',
                width=width,
                height=height
            )
            
            # Set extent if available
            if raster.bounds:
                try:
                    layer.extent = Extent.from_dict(raster.bounds)
                except Exception:
                    pass
            
            # Add band information from metadata
            if raster.raster_metadata and 'bands' in raster.raster_metadata:
                for band_info in raster.raster_metadata['bands']:
                    band = RasterBand(
                        index=band_info.get('index', 1),
                        name=band_info.get('name', 'band'),
                        data_type=band_info.get('data_type', 'float32'),
                        min_value=band_info.get('min_value', 0),
                        max_value=band_info.get('max_value', 1)
                    )
                    layer.add_band(band)
            
            return layer
        except Exception as e:
            logger.error(f"Error converting Raster model: {str(e)}")
            return None
    
    # Workflow Methods
    def run_erosion_analysis(self, db: Session, dem_before_id: str, dem_after_id: str,
                            project_id: int, user_id: int, 
                            cell_size: float = 1.0) -> Optional[Dict[str, Any]]:
        """Run erosion analysis workflow."""
        try:
            # Run analysis
            results = self.engine.analyze_erosion(dem_before_id, dem_after_id, cell_size)
            
            if not results:
                return None
            
            # Create database record
            analysis = self.create_analysis_from_layers(
                db, f"Erosion Analysis - {datetime.utcnow().isoformat()}",
                dem_before_id, dem_after_id, project_id, user_id
            )
            
            if analysis:
                self.save_analysis_results(db, analysis.id, results, user_id)
                results['analysis_id'] = analysis.id
            
            return results
        except Exception as e:
            logger.error(f"Error in erosion analysis: {str(e)}")
            return None
    
    def run_dem_processing(self, db: Session, dem_id: str, processing_type: str,
                          project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Run DEM processing workflow (derivatives, etc.)."""
        try:
            dem_layer = self.engine.get_layer(dem_id)
            if not dem_layer:
                return None
            
            if processing_type == 'derivatives':
                derivatives = self.engine.compute_dem_derivatives(dem_id)
                return {
                    'success': True,
                    'processing_type': 'derivatives',
                    'outputs': {
                        name: {'id': layer.id, 'name': layer.name}
                        for name, layer in derivatives.items()
                    }
                }
            
            return None
        except Exception as e:
            logger.error(f"Error in DEM processing: {str(e)}")
            return None
    
    # Statistics and Reporting
    def generate_project_report(self, db: Session, project_id: int) -> Dict[str, Any]:
        """Generate comprehensive project GIS report."""
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {}
            
            canvas = self.engine.get_active_canvas()
            if not canvas:
                return {}
            
            layers = self.engine.get_layers()
            
            report = {
                'project_id': project_id,
                'project_name': project.name,
                'generated_at': datetime.utcnow().isoformat(),
                'canvas': {
                    'name': canvas.name,
                    'crs': canvas.crs,
                    'extent': canvas.extent.to_dict() if canvas.extent else None,
                    'layer_count': len(layers)
                },
                'layers': [
                    {
                        'id': layer.id,
                        'name': layer.name,
                        'type': layer.layer_type.value,
                        'crs': layer.crs,
                        'extent': layer.extent.to_dict() if layer.extent else None,
                        'feature_count': layer.get_feature_count(),
                        'statistics': self.engine.calculate_layer_statistics(layer.id)
                    }
                    for layer in layers
                ],
                'algorithms_available': len(self.engine.get_processing_algorithms())
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {}


# Factory function
def create_gis_service_integration() -> GISServiceIntegration:
    """Create GIS service integration instance."""
    engine = TerraSIMGISEngine("TerraSim GIS Service")
    return GISServiceIntegration(engine)


# Module-level convenience functions
_integration_instance: Optional[GISServiceIntegration] = None

def get_gis_integration() -> GISServiceIntegration:
    """Get or create GIS service integration."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = create_gis_service_integration()
    return _integration_instance
