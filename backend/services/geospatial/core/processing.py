"""
Processing algorithm framework.
Similar to QGIS Processing framework for running geospatial algorithms.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import time
import logging

from .layer import Layer, Extent
from .raster_layer import RasterLayer
from .vector_layer import VectorLayer
from .pointcloud_layer import PointCloudLayer


logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Processing parameter types."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    EXTENT = "extent"
    LAYER = "layer"
    RASTER_LAYER = "raster"
    VECTOR_LAYER = "vector"
    POINTCLOUD_LAYER = "pointcloud"
    FILE = "file"
    MULTI_SELECT = "multi_select"


@dataclass
class ProcessingParameter:
    """Algorithm parameter definition."""
    name: str
    description: str
    param_type: ParameterType
    default_value: Any = None
    required: bool = True
    options: Optional[List[Any]] = None


@dataclass
class ProcessingResult:
    """Result of algorithm processing."""
    success: bool
    output_layers: Optional[Dict[str, Layer]] = None
    parameters_used: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    error_message: str = ""
    processing_time: float = 0.0
    progress: int = 100


class ProcessingAlgorithm(ABC):
    """Base class for processing algorithms."""
    
    def __init__(self, name: str, group: str = ""):
        self.name = name
        self.group = group
        self.display_name = name.replace('_', ' ').title()
        self.parameters: List[ProcessingParameter] = []
        self.outputs: List[str] = []
    
    @abstractmethod
    def define_parameters(self):
        """Define algorithm parameters."""
        pass
    
    @abstractmethod
    def process(self, parameters: Dict[str, Any]) -> ProcessingResult:
        """Execute algorithm."""
        pass
    
    def get_parameter_definitions(self) -> List[ProcessingParameter]:
        """Get parameter definitions."""
        return self.parameters
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters."""
        for param in self.parameters:
            if param.required and param.name not in parameters:
                logger.error(f"Missing required parameter: {param.name}")
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize algorithm to dictionary."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'group': self.group,
            'parameters': [
                {
                    'name': p.name,
                    'description': p.description,
                    'type': p.param_type.value,
                    'default': p.default_value,
                    'required': p.required
                }
                for p in self.parameters
            ],
            'outputs': self.outputs
        }


class HillshadeAlgorithm(ProcessingAlgorithm):
    """Generate hillshade from DEM."""
    
    def __init__(self):
        super().__init__("hillshade", "Raster Analysis")
        self.define_parameters()
    
    def define_parameters(self):
        """Define parameters."""
        self.parameters = [
            ProcessingParameter(
                "dem_layer",
                "Input DEM Layer",
                ParameterType.RASTER_LAYER,
                required=True
            ),
            ProcessingParameter(
                "azimuth",
                "Light Direction Azimuth (0-360)",
                ParameterType.NUMBER,
                default_value=315,
                required=False
            ),
            ProcessingParameter(
                "altitude",
                "Light Source Altitude (0-90)",
                ParameterType.NUMBER,
                default_value=45,
                required=False
            ),
            ProcessingParameter(
                "output",
                "Output Layer Name",
                ParameterType.STRING,
                default_value="hillshade",
                required=False
            )
        ]
        self.outputs = ["output"]
    
    def process(self, parameters: Dict[str, Any]) -> ProcessingResult:
        """Execute hillshade."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(parameters):
                return ProcessingResult(False, error_message="Invalid parameters")
            
            dem_layer = parameters['dem_layer']
            azimuth = parameters.get('azimuth', 315)
            altitude = parameters.get('altitude', 45)
            output_name = parameters.get('output', 'hillshade')
            
            if dem_layer._data_cache is None:
                return ProcessingResult(False, error_message="DEM data not loaded")
            
            # Process first band if multiband
            dem_data = dem_layer._data_cache[0] if dem_layer._data_cache.ndim == 3 else dem_layer._data_cache
            
            from .spatial_ops import RasterAnalysis
            import numpy as np
            
            hillshade_data = RasterAnalysis.hillshade(dem_data, azimuth, altitude)
            
            # Create output raster layer
            output_layer = RasterLayer(
                output_name,
                dem_layer.source,
                dem_layer.crs,
                dem_layer.width,
                dem_layer.height
            )
            
            # Add hillshade band
            from .raster_layer import RasterBand
            output_layer.add_band(RasterBand(
                index=1,
                name="hillshade",
                data_type=str(hillshade_data.dtype),
                min_value=float(np.min(hillshade_data)),
                max_value=float(np.max(hillshade_data))
            ))
            
            output_layer.load_data(hillshade_data[np.newaxis, :, :])
            output_layer.set_geotransform(dem_layer.get_geotransform())
            
            elapsed = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                output_layers={'output': output_layer},
                parameters_used=parameters,
                statistics={'processing_time': elapsed},
                processing_time=elapsed
            )
        
        except Exception as e:
            logger.error(f"Hillshade error: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )


class SlopeAlgorithm(ProcessingAlgorithm):
    """Calculate slope from DEM."""
    
    def __init__(self):
        super().__init__("slope", "Raster Analysis")
        self.define_parameters()
    
    def define_parameters(self):
        """Define parameters."""
        self.parameters = [
            ProcessingParameter(
                "dem_layer",
                "Input DEM Layer",
                ParameterType.RASTER_LAYER,
                required=True
            ),
            ProcessingParameter(
                "cell_size",
                "Cell Size (map units)",
                ParameterType.NUMBER,
                default_value=1.0,
                required=False
            ),
            ProcessingParameter(
                "output",
                "Output Layer Name",
                ParameterType.STRING,
                default_value="slope",
                required=False
            )
        ]
        self.outputs = ["output"]
    
    def process(self, parameters: Dict[str, Any]) -> ProcessingResult:
        """Execute slope calculation."""
        start_time = time.time()
        
        try:
            dem_layer = parameters['dem_layer']
            cell_size = parameters.get('cell_size', 1.0)
            output_name = parameters.get('output', 'slope')
            
            dem_data = dem_layer._data_cache[0] if dem_layer._data_cache.ndim == 3 else dem_layer._data_cache
            
            from .spatial_ops import RasterAnalysis
            import numpy as np
            
            slope_data = RasterAnalysis.slope(dem_data, cell_size)
            
            output_layer = RasterLayer(
                output_name,
                dem_layer.source,
                dem_layer.crs,
                dem_layer.width,
                dem_layer.height
            )
            
            from .raster_layer import RasterBand
            output_layer.add_band(RasterBand(
                index=1,
                name="slope",
                data_type='float32',
                min_value=float(np.min(slope_data)),
                max_value=float(np.max(slope_data))
            ))
            
            output_layer.load_data(slope_data[np.newaxis, :, :])
            output_layer.set_geotransform(dem_layer.get_geotransform())
            
            elapsed = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                output_layers={'output': output_layer},
                processing_time=elapsed
            )
        
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )


class ErosionAnalysisAlgorithm(ProcessingAlgorithm):
    """Analyze erosion/deposition from DEMs."""
    
    def __init__(self):
        super().__init__("erosion_analysis", "Terrain Analysis")
        self.define_parameters()
    
    def define_parameters(self):
        """Define parameters."""
        self.parameters = [
            ProcessingParameter(
                "dem_before",
                "DEM Before",
                ParameterType.RASTER_LAYER,
                required=True
            ),
            ProcessingParameter(
                "dem_after",
                "DEM After",
                ParameterType.RASTER_LAYER,
                required=True
            ),
            ProcessingParameter(
                "cell_size",
                "Cell Size (map units)",
                ParameterType.NUMBER,
                default_value=1.0,
                required=False
            ),
            ProcessingParameter(
                "output_change",
                "Output Change Layer Name",
                ParameterType.STRING,
                default_value="elevation_change",
                required=False
            )
        ]
        self.outputs = ["output_change"]
    
    def process(self, parameters: Dict[str, Any]) -> ProcessingResult:
        """Execute erosion analysis."""
        start_time = time.time()
        
        try:
            dem_before = parameters['dem_before']
            dem_after = parameters['dem_after']
            cell_size = parameters.get('cell_size', 1.0)
            output_name = parameters.get('output_change', 'elevation_change')
            
            dem_before_data = dem_before._data_cache[0] if dem_before._data_cache.ndim == 3 else dem_before._data_cache
            dem_after_data = dem_after._data_cache[0] if dem_after._data_cache.ndim == 3 else dem_after._data_cache
            
            from .spatial_ops import VolumeAnalysis
            import numpy as np
            
            # Calculate volume change
            volume_stats = VolumeAnalysis.calculate_volume_change(
                dem_before_data,
                dem_after_data,
                cell_size,
                dem_before.extent
            )
            
            # Calculate change grid
            change = dem_after_data - dem_before_data
            
            # Create output layer
            output_layer = RasterLayer(
                output_name,
                dem_before.source,
                dem_before.crs,
                dem_before.width,
                dem_before.height
            )
            
            from .raster_layer import RasterBand
            output_layer.add_band(RasterBand(
                index=1,
                name="elevation_change",
                data_type='float32',
                min_value=float(np.min(change)),
                max_value=float(np.max(change))
            ))
            
            output_layer.load_data(change[np.newaxis, :, :])
            output_layer.set_geotransform(dem_before.get_geotransform())
            
            elapsed = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                output_layers={'output_change': output_layer},
                statistics=volume_stats,
                processing_time=elapsed
            )
        
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )


class ProcessingRegistry:
    """Registry of available processing algorithms."""
    
    def __init__(self):
        self._algorithms: Dict[str, ProcessingAlgorithm] = {}
        self._register_builtin_algorithms()
    
    def _register_builtin_algorithms(self):
        """Register built-in algorithms."""
        algorithms = [
            HillshadeAlgorithm(),
            SlopeAlgorithm(),
            ErosionAnalysisAlgorithm()
        ]
        
        for algo in algorithms:
            self.register(algo)
    
    def register(self, algorithm: ProcessingAlgorithm):
        """Register algorithm."""
        key = f"{algorithm.group}:{algorithm.name}"
        self._algorithms[key] = algorithm
        logger.info(f"Registered algorithm: {key}")
    
    def get_algorithm(self, algorithm_id: str) -> Optional[ProcessingAlgorithm]:
        """Get algorithm by ID."""
        return self._algorithms.get(algorithm_id)
    
    def get_algorithms_by_group(self, group: str) -> List[ProcessingAlgorithm]:
        """Get algorithms in group."""
        return [algo for algo in self._algorithms.values() if algo.group == group]
    
    def get_all_algorithms(self) -> List[ProcessingAlgorithm]:
        """Get all registered algorithms."""
        return list(self._algorithms.values())
    
    def list_algorithms(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all algorithms grouped."""
        groups = {}
        for algo in self._algorithms.values():
            if algo.group not in groups:
                groups[algo.group] = []
            groups[algo.group].append(algo.to_dict())
        return groups


# Global processing registry
_processing_registry = ProcessingRegistry()

def get_processing_registry() -> ProcessingRegistry:
    """Get global processing registry."""
    return _processing_registry
