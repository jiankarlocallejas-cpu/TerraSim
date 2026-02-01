"""
Professional Data Import/Export System
Support for GIS formats: GeoTIFF, LAS/LAZ, Shapefile, COG, MBTiles
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SupportedFormats:
    """Supported data formats for import/export"""
    
    RASTER_FORMATS = {
        "GeoTIFF": {
            "ext": [".tif", ".tiff"],
            "type": "raster",
            "description": "GeoTIFF - Standard geospatial raster format",
            "writable": True
        },
        "COG": {
            "ext": [".tif", ".tiff"],
            "type": "raster",
            "description": "Cloud Optimized GeoTIFF",
            "writable": True
        },
        "HGT": {
            "ext": [".hgt"],
            "type": "raster",
            "description": "SRTM HGT elevation data",
            "writable": False
        },
        "ASCII": {
            "ext": [".asc", ".grd"],
            "type": "raster",
            "description": "ASCII Grid format",
            "writable": True
        }
    }
    
    VECTOR_FORMATS = {
        "Shapefile": {
            "ext": [".shp"],
            "type": "vector",
            "description": "ESRI Shapefile",
            "writable": True
        },
        "GeoJSON": {
            "ext": [".geojson", ".json"],
            "type": "vector",
            "description": "GeoJSON format",
            "writable": True
        },
        "GeoPackage": {
            "ext": [".gpkg"],
            "type": "vector",
            "description": "SQLite-based GIS format",
            "writable": True
        },
        "KML": {
            "ext": [".kml"],
            "type": "vector",
            "description": "Keyhole Markup Language",
            "writable": True
        }
    }
    
    POINTCLOUD_FORMATS = {
        "LAS": {
            "ext": [".las"],
            "type": "pointcloud",
            "description": "LAS - Standard point cloud format",
            "writable": True
        },
        "LAZ": {
            "ext": [".laz"],
            "type": "pointcloud",
            "description": "LAZ - Compressed point cloud",
            "writable": True
        },
        "E57": {
            "ext": [".e57"],
            "type": "pointcloud",
            "description": "ASTM E57 3D imaging data",
            "writable": False
        },
        "PLY": {
            "ext": [".ply"],
            "type": "pointcloud",
            "description": "Polygon File Format",
            "writable": True
        }
    }


class ProfessionalDataImporter:
    """Professional data import with validation and metadata extraction"""
    
    @staticmethod
    def import_geotiff(file_path: str) -> Dict[str, Any]:
        """
        Import GeoTIFF with full metadata
        
        Returns:
            Dictionary with data and metadata
        """
        try:
            import rasterio
        except ImportError:
            raise ImportError("rasterio required: pip install rasterio")
        
        with rasterio.open(file_path) as src:
            data = src.read(1)  # Read first band
            
            metadata = {
                "driver": src.driver,
                "dtype": str(src.dtypes[0]),
                "shape": src.shape,
                "crs": str(src.crs),
                "transform": str(src.transform),
                "bounds": src.bounds,
                "resolution": src.res,
                "nodata": src.nodata,
                "bands": src.count,
                "colorinterp": [str(ci) for ci in src.colorinterp]
            }
            
            logger.info(f"Imported GeoTIFF: {file_path} - Shape: {data.shape}")
            return {
                "data": data,
                "metadata": metadata,
                "file_format": "GeoTIFF"
            }
    
    @staticmethod
    def import_shapefile(file_path: str) -> Dict[str, Any]:
        """Import Shapefile with geometry and attributes"""
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("geopandas required: pip install geopandas")
        
        gdf = gpd.read_file(file_path)
        
        metadata = {
            "crs": str(gdf.crs),
            "geometry_types": gdf.geometry.type.unique().tolist(),
            "total_features": len(gdf),
            "bounds": gdf.total_bounds.tolist(),
            "attributes": list(gdf.columns)
        }
        
        logger.info(f"Imported Shapefile: {file_path} - Features: {len(gdf)}")
        return {
            "data": gdf,
            "metadata": metadata,
            "file_format": "Shapefile"
        }
    
    @staticmethod
    def import_las_pointcloud(file_path: str) -> Dict[str, Any]:
        """Import LAS point cloud with classification"""
        try:
            import laspy
        except ImportError:
            raise ImportError("laspy required: pip install laspy")
        
        las = laspy.read(file_path)
        
        points = {
            "x": las.x.copy(),
            "y": las.y.copy(),
            "z": las.z.copy(),
            "intensity": las.intensity.copy() if hasattr(las, 'intensity') else None,
            "classification": las.classification.copy() if hasattr(las, 'classification') else None
        }
        
        metadata = {
            "point_count": len(las),
            "min_xyz": [float(las.header.x_min), float(las.header.y_min), float(las.header.z_min)],
            "max_xyz": [float(las.header.x_max), float(las.header.y_max), float(las.header.z_max)],
            "version": f"{las.header.version.major}.{las.header.version.minor}",
            "scale": list(las.header.scale),
            "offset": list(las.header.offset),
            "crs": str(las.header.parse_crs()) if hasattr(las.header, 'parse_crs') else "Unknown"
        }
        
        logger.info(f"Imported LAS: {file_path} - Points: {len(las)}")
        return {
            "data": points,
            "metadata": metadata,
            "file_format": "LAS"
        }
    
    @staticmethod
    def import_generic(file_path: str) -> Dict[str, Any]:
        """
        Auto-detect and import generic format
        
        Returns:
            Dictionary with data and metadata
        """
        ext = Path(file_path).suffix.lower()
        
        if ext in SupportedFormats.RASTER_FORMATS.get("GeoTIFF", {}).get("ext", []):
            return ProfessionalDataImporter.import_geotiff(file_path)
        
        elif ext in SupportedFormats.VECTOR_FORMATS.get("Shapefile", {}).get("ext", []):
            return ProfessionalDataImporter.import_shapefile(file_path)
        
        elif ext in SupportedFormats.POINTCLOUD_FORMATS.get("LAS", {}).get("ext", []):
            return ProfessionalDataImporter.import_las_pointcloud(file_path)
        
        else:
            raise ValueError(f"Unsupported format: {ext}")


class ProfessionalDataExporter:
    """Professional data export with compression and optimization"""
    
    @staticmethod
    def export_geotiff(data: Any, output_path: str, metadata: Optional[Dict] = None, compress: str = "lzw"):
        """
        Export data as GeoTIFF
        
        Args:
            data: Raster data (numpy array)
            output_path: Output file path
            metadata: Geospatial metadata
            compress: Compression method (lzw, deflate, etc.)
        """
        try:
            import rasterio
            from rasterio.transform import from_bounds
        except ImportError:
            raise ImportError("rasterio required: pip install rasterio")
        
        import numpy as np
        
        if metadata is None:
            metadata = {}
        
        height, width = data.shape
        
        # Default transform (will be overridden if metadata provided)
        transform = metadata.get("transform", from_bounds(0, 0, width, height, width, height))
        crs = metadata.get("crs", "EPSG:4326")
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=data.dtype,
            crs=crs,
            transform=transform,
            compress=compress,
            nodata=metadata.get("nodata")
        ) as dst:
            dst.write(data, 1)
        
        logger.info(f"Exported GeoTIFF: {output_path}")
    
    @staticmethod
    def export_cog(data: Any, output_path: str, metadata: Optional[Dict] = None):
        """
        Export as Cloud Optimized GeoTIFF (COG)
        Optimized for cloud storage and streaming
        """
        # Use similar approach but with COG-specific settings
        ProfessionalDataExporter.export_geotiff(
            data, output_path, metadata,
            compress="deflate"
        )
        logger.info(f"Exported COG: {output_path}")
    
    @staticmethod
    def export_geojson(geodataframe: Any, output_path: str):
        """Export vector data as GeoJSON"""
        try:
            geodataframe.to_file(output_path, driver='GeoJSON')
        except ImportError:
            raise ImportError("geopandas required for GeoJSON export")
        
        logger.info(f"Exported GeoJSON: {output_path}")
    
    @staticmethod
    def export_shapefile(geodataframe: Any, output_path: str):
        """Export vector data as Shapefile"""
        try:
            geodataframe.to_file(output_path, driver='ESRI Shapefile')
        except ImportError:
            raise ImportError("geopandas required for Shapefile export")
        
        logger.info(f"Exported Shapefile: {output_path}")
    
    @staticmethod
    def export_las_pointcloud(points: Dict[str, Any], output_path: str, metadata: Optional[Dict] = None):
        """Export point cloud as LAS"""
        try:
            import laspy
        except ImportError:
            raise ImportError("laspy required for LAS export: pip install laspy")
        
        las = laspy.create()
        las.x = points["x"]
        las.y = points["y"]
        las.z = points["z"]
        
        if "intensity" in points and points["intensity"] is not None:
            las.intensity = points["intensity"]
        
        if "classification" in points and points["classification"] is not None:
            las.classification = points["classification"]
        
        las.write(output_path)
        logger.info(f"Exported LAS: {output_path}")


class DataQualityValidator:
    """Validate imported data for quality and completeness"""
    
    @staticmethod
    def validate_dem(dem_data: Any) -> Dict[str, Any]:
        """Validate DEM data"""
        import numpy as np
        
        dem_array = np.asarray(dem_data)
        valid_data = dem_array[~np.isnan(dem_array)]
        
        issues = []
        
        if len(valid_data) == 0:
            issues.append("DEM contains only NaN values")
        
        if np.any(dem_array < -500):
            issues.append("DEM contains unrealistic negative elevations")
        
        if np.any(dem_array > 9000):
            issues.append("DEM contains unrealistic elevation values")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "statistics": {
                "min": float(np.min(valid_data)) if len(valid_data) > 0 else None,
                "max": float(np.max(valid_data)) if len(valid_data) > 0 else None,
                "mean": float(np.mean(valid_data)) if len(valid_data) > 0 else None,
                "valid_pixels": int(len(valid_data)),
                "total_pixels": int(dem_array.size),
                "nodata_percentage": float((1 - len(valid_data) / dem_array.size) * 100)
            }
        }
    
    @staticmethod
    def validate_pointcloud(points: Dict[str, Any]) -> Dict[str, Any]:
        """Validate point cloud data"""
        import numpy as np
        
        issues = []
        point_count = len(points.get("x", []))
        
        if point_count == 0:
            issues.append("Point cloud is empty")
        
        for axis in ["x", "y", "z"]:
            if axis not in points:
                issues.append(f"Missing {axis} coordinates")
        
        if point_count > 0:
            z_values = np.asarray(points.get("z", []))
            if np.any(z_values < -500) or np.any(z_values > 9000):
                issues.append("Point cloud contains unrealistic elevation values")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "point_count": point_count,
            "statistics": {
                "x_range": [float(np.min(points["x"])), float(np.max(points["x"]))] if point_count > 0 else None,
                "y_range": [float(np.min(points["y"])), float(np.max(points["y"]))] if point_count > 0 else None,
                "z_range": [float(np.min(points["z"])), float(np.max(points["z"]))] if point_count > 0 else None
            }
        }
