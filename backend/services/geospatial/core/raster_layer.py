"""
Raster layer implementation.
Handles DEM, GeoTIFF, and other raster data formats.
"""

from typing import Optional, Dict, Any, Tuple
from .layer import Layer, LayerType, Extent
import numpy as np
from dataclasses import dataclass


@dataclass
class RasterBand:
    """Represents a single raster band."""
    index: int
    name: str
    data_type: str  # uint8, float32, etc.
    nodata_value: Optional[float] = None
    min_value: float = 0.0
    max_value: float = 1.0
    statistics: Optional[Dict[str, float]] = None


class RasterLayer(Layer):
    """
    Raster data layer (DEM, satellite imagery, etc.).
    Analogous to QGIS QgsRasterLayer.
    """
    
    def __init__(
        self,
        name: str,
        source: str,
        crs: str = "EPSG:4326",
        width: int = 0,
        height: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, source, LayerType.RASTER, crs, metadata)
        
        self.width = width
        self.height = height
        self._bands: Dict[int, RasterBand] = {}
        self._data_cache: Optional[np.ndarray] = None
        self._geotransform = [0.0, 1.0, 0.0, 0.0, 0.0, -1.0]  # GDAL geotransform
        self._nodata_value = None
    
    def add_band(self, band: RasterBand):
        """Add raster band."""
        self._bands[band.index] = band
    
    def get_band(self, index: int) -> Optional[RasterBand]:
        """Get raster band by index."""
        return self._bands.get(index)
    
    def get_band_count(self) -> int:
        """Get total number of bands."""
        return len(self._bands)
    
    def get_band_names(self) -> list:
        """Get all band names."""
        return [band.name for band in sorted(self._bands.values(), key=lambda b: b.index)]
    
    def set_geotransform(self, transform: Tuple[float, float, float, float, float, float]):
        """
        Set GDAL geotransform.
        [x_origin, pixel_width, rotation_x, y_origin, rotation_y, pixel_height]
        """
        self._geotransform = list(transform)
    
    def get_geotransform(self) -> Tuple[float, ...]:
        """Get GDAL geotransform."""
        return tuple(self._geotransform)
    
    def get_pixel_value(self, x: int, y: int, band: int = 1) -> Optional[float]:
        """Get pixel value at coordinates."""
        if self._data_cache is None:
            return None
        if band not in self._bands or y >= self.height or x >= self.width:
            return None
        return float(self._data_cache[band - 1, y, x])
    
    def get_pixel_values(self, x: int, y: int) -> Dict[int, float]:
        """Get values from all bands at coordinates."""
        values = {}
        for band_idx in sorted(self._bands.keys()):
            val = self.get_pixel_value(x, y, band_idx)
            if val is not None:
                values[band_idx] = val
        return values
    
    def sample_at_coordinates(self, lon: float, lat: float) -> Optional[Dict[int, float]]:
        """Sample raster values at geographic coordinates."""
        # Convert geographic coordinates to pixel coordinates
        x = (lon - self._geotransform[0]) / self._geotransform[1]
        y = (lat - self._geotransform[3]) / self._geotransform[5]
        
        x, y = int(x), int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.get_pixel_values(x, y)
        return None
    
    def get_statistics(self, band: int) -> Optional[Dict[str, float]]:
        """Get band statistics."""
        if band in self._bands:
            return self._bands[band].statistics or {}
        return None
    
    def load_data(self, data: np.ndarray):
        """Load raster data array."""
        self._data_cache = data
        if data.ndim == 3:
            self.height, self.width = data.shape[1], data.shape[2]
        else:
            self.height, self.width = data.shape[0], data.shape[1]
    
    def get_feature_count(self) -> int:
        """Raster layers don't have features, return pixel count."""
        return self.width * self.height
    
    def get_attributes(self) -> Dict[str, str]:
        """Get raster attributes (bands)."""
        return {f"band_{i}": "float32" for i in range(1, self.get_band_count() + 1)}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **self.get_metadata(),
            'width': self.width,
            'height': self.height,
            'band_count': self.get_band_count(),
            'bands': [
                {
                    'index': band.index,
                    'name': band.name,
                    'data_type': band.data_type,
                    'nodata_value': band.nodata_value,
                    'min_value': band.min_value,
                    'max_value': band.max_value
                }
                for band in self._bands.values()
            ],
            'geotransform': self._geotransform
        }
