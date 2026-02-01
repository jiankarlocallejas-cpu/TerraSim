"""
Data providers for reading/writing various GIS formats.
Abstracts I/O operations similar to QGIS data providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import pickle
import logging
import numpy as np

from .raster_layer import RasterLayer, RasterBand
from .vector_layer import VectorLayer, Feature, Geometry, GeometryType, Attribute
from .pointcloud_layer import PointCloudLayer, PointCloudStatistics

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """Base class for data providers."""
    
    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """Check if provider can handle this data source."""
        pass
    
    @abstractmethod
    def read(self, source: str) -> Optional[Any]:
        """Read data from source."""
        pass
    
    @abstractmethod
    def write(self, layer: Any, destination: str) -> bool:
        """Write layer to destination."""
        pass


class GeoTIFFProvider(DataProvider):
    """Provider for GeoTIFF raster files."""
    
    def can_handle(self, source: str) -> bool:
        """Check for .tif, .tiff extensions."""
        return source.lower().endswith(('.tif', '.tiff', '.geotiff'))
    
    def read(self, source: str) -> Optional[RasterLayer]:
        """Read GeoTIFF file."""
        try:
            import rasterio
            
            with rasterio.open(source) as src:
                layer = RasterLayer(
                    name=Path(source).stem,
                    source=source,
                    crs=src.crs.to_string() if src.crs else 'EPSG:4326',
                    width=src.width,
                    height=src.height
                )
                
                layer.set_geotransform(src.transform[:6])
                
                # Add bands
                for i in range(1, src.count + 1):
                    data = src.read(i)
                    band = RasterBand(
                        index=i,
                        name=f"Band {i}",
                        data_type=str(data.dtype),
                        nodata_value=float(src.nodata) if src.nodata else None,
                        min_value=float(np.min(data)),
                        max_value=float(np.max(data)),
                        statistics={
                            'min': float(np.min(data)),
                            'max': float(np.max(data)),
                            'mean': float(np.mean(data)),
                            'std': float(np.std(data))
                        }
                    )
                    layer.add_band(band)
                
                # Load data
                data = np.array([src.read(i) for i in range(1, src.count + 1)])
                layer.load_data(data)
                
                return layer
        except Exception as e:
            print(f"Error reading GeoTIFF: {e}")
            return None
    
    def write(self, layer: RasterLayer, destination: str) -> bool:
        """Write RasterLayer to GeoTIFF."""
        try:
            import rasterio
            from rasterio.transform import Affine
            
            if layer._data_cache is None:
                return False
            
            transform = Affine(*layer.get_geotransform())
            
            with rasterio.open(
                destination,
                'w',
                driver='GTiff',
                height=layer.height,
                width=layer.width,
                count=layer.get_band_count(),
                dtype=layer._data_cache.dtype,
                crs=layer.crs,
                transform=transform
            ) as dst:
                for i in range(layer.get_band_count()):
                    dst.write(layer._data_cache[i], i + 1)
            
            return True
        except Exception as e:
            print(f"Error writing GeoTIFF: {e}")
            return False


class ShapefileProvider(DataProvider):
    """Provider for Shapefile vector format."""
    
    def can_handle(self, source: str) -> bool:
        """Check for .shp extension."""
        return source.lower().endswith('.shp')
    
    def read(self, source: str) -> Optional[VectorLayer]:
        """Read Shapefile."""
        try:
            try:
                try:
                    import shapefile  # type: ignore
                except ImportError:
                    import pyshp as shapefile  # type: ignore
            except ImportError:
                logger.error("shapefile package not installed")
                return None
            
            sf = shapefile.Reader(source)
            
            # Determine geometry type
            shape_type_map = {
                1: GeometryType.POINT,
                3: GeometryType.LINESTRING,
                5: GeometryType.POLYGON,
                8: GeometryType.MULTIPOINT,
                13: GeometryType.MULTILINESTRING,
                15: GeometryType.MULTIPOLYGON
            }
            
            geom_type = shape_type_map.get(sf.shapeType, GeometryType.POINT)
            
            layer = VectorLayer(
                name=Path(source).stem,
                source=source,
                geometry_type=geom_type,
                crs='EPSG:4326'
            )
            
            # Add attributes from field descriptions
            for field in sf.fields[1:]:  # Skip deletion flag field
                layer.add_attribute(Attribute(
                    name=field[0],
                    type='string' if field[1] == 'C' else 'real' if field[1] == 'F' else 'integer'
                ))
            
            # Add features
            for i, shape in enumerate(sf.shapes()):
                # Convert to WKT
                wkt = shape.__geo_interface__['type']
                
                geometry = Geometry(
                    wkt=wkt,
                    geometry_type=geom_type
                )
                
                record = sf.record(i)
                layer.add_feature(geometry, dict(zip([f[0] for f in sf.fields[1:]], record)))
            
            return layer
        except Exception as e:
            print(f"Error reading Shapefile: {e}")
            return None
    
    def write(self, layer: VectorLayer, destination: str) -> bool:
        """Write VectorLayer to Shapefile."""
        # Simplified implementation
        return False


class LASProvider(DataProvider):
    """Provider for LAS point cloud format."""
    
    def can_handle(self, source: str) -> bool:
        """Check for .las, .laz extensions."""
        return source.lower().endswith(('.las', '.laz'))
    
    def read(self, source: str) -> Optional[PointCloudLayer]:
        """Read LAS file."""
        try:
            import laspy
            
            las = laspy.read(source)
            
            layer = PointCloudLayer(
                name=Path(source).stem,
                source=source
            )
            
            # Extract point data - convert to numpy arrays
            x = np.array(las.x, dtype=np.float64)
            y = np.array(las.y, dtype=np.float64)
            z = np.array(las.z, dtype=np.float64)
            intensity = np.array(las.intensity, dtype=np.float64) if hasattr(las, 'intensity') else np.zeros(len(las), dtype=np.float64)
            classification = np.array(las.classification, dtype=np.float64) if hasattr(las, 'classification') else np.zeros(len(las), dtype=np.float64)
            
            points = np.vstack([
                x,
                y,
                z,
                intensity,
                classification
            ]).T
            
            layer.load_points(points)
            layer.set_point_format(f"LAS {las.header.version}")
            
            return layer
        except Exception as e:
            print(f"Error reading LAS: {e}")
            return None
    
    def write(self, layer: PointCloudLayer, destination: str) -> bool:
        """Write PointCloudLayer to LAS."""
        try:
            import laspy
            
            if layer._points_data is None:
                return False
            
            points = layer._points_data
            
            las = laspy.create()
            las.x = points[:, 0]
            las.y = points[:, 1]
            las.z = points[:, 2]
            
            if points.shape[1] > 3:
                las.intensity = points[:, 3].astype(np.uint16)
            if points.shape[1] > 4:
                las.classification = points[:, 4].astype(np.uint8)
            
            las.write(destination)
            return True
        except Exception as e:
            print(f"Error writing LAS: {e}")
            return False


class JSONProvider(DataProvider):
    """Provider for JSON layer export/import."""
    
    def can_handle(self, source: str) -> bool:
        """Check for .json, .geojson extensions."""
        return source.lower().endswith(('.json', '.geojson'))
    
    def read(self, source: str) -> Optional[Any]:
        """Read GeoJSON."""
        try:
            with open(source, 'r') as f:
                geojson = json.load(f)
            
            # Convert GeoJSON to VectorLayer
            layer = VectorLayer(
                name=Path(source).stem,
                source=source
            )
            
            for feature in geojson.get('features', []):
                geom = feature['geometry']
                props = feature['properties']
                
                geometry = Geometry(
                    wkt=str(geom),
                    geometry_type=GeometryType.POINT
                )
                
                layer.add_feature(geometry, props)
            
            return layer
        except Exception as e:
            print(f"Error reading JSON: {e}")
            return None
    
    def write(self, layer: Any, destination: str) -> bool:
        """Write to GeoJSON."""
        try:
            features = []
            if isinstance(layer, VectorLayer):
                for feature in layer.get_features():
                    features.append({
                        'type': 'Feature',
                        'geometry': feature.geometry.to_dict(),
                        'properties': feature.attributes
                    })
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }
            
            with open(destination, 'w') as f:
                json.dump(geojson, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error writing JSON: {e}")
            return False


class DataProviderRegistry:
    """Registry of available data providers."""
    
    def __init__(self):
        self._providers: List[DataProvider] = [
            GeoTIFFProvider(),
            ShapefileProvider(),
            LASProvider(),
            JSONProvider()
        ]
    
    def register_provider(self, provider: DataProvider):
        """Register a new data provider."""
        self._providers.append(provider)
    
    def get_provider(self, source: str) -> Optional[DataProvider]:
        """Get suitable provider for data source."""
        for provider in self._providers:
            if provider.can_handle(source):
                return provider
        return None
    
    def read(self, source: str) -> Optional[Any]:
        """Read data using appropriate provider."""
        provider = self.get_provider(source)
        if provider:
            return provider.read(source)
        return None
    
    def write(self, layer: Any, destination: str) -> bool:
        """Write layer using appropriate provider."""
        provider = self.get_provider(destination)
        if provider:
            return provider.write(layer, destination)
        return False


# Global registry instance
_provider_registry = DataProviderRegistry()

def get_provider_registry() -> DataProviderRegistry:
    """Get global data provider registry."""
    return _provider_registry
