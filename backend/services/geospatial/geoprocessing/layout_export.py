"""
Map Layout, Composition, and Export Engine.
Professional map templates, legends, scale bars, and multi-format export.

Features:
- Map templates
- Legend generation
- Scale bar rendering
- North arrow
- Export to PDF, PNG, SVG, etc.
- Map composition and layout
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from pathlib import Path
import geopandas as gpd
from geopandas import GeoDataFrame

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Export format types."""
    PDF = "pdf"
    PNG = "png"
    SVG = "svg"
    GeoJSON = "geojson"
    Shapefile = "shapefile"
    GeoTIFF = "geotiff"
    KML = "kml"
    CSV = "csv"


@dataclass
class MapElement:
    """Base map element."""
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MapTitle(MapElement):
    """Map title element."""
    text: str = ""
    font_size: int = 24
    font_name: str = "Arial"
    bold: bool = True


@dataclass
class MapLegend(MapElement):
    """Legend element."""
    title: str = "Legend"
    column_count: int = 1
    show_title: bool = True
    background_color: str = "#FFFFFF"
    border_color: str = "#000000"
    show_border: bool = True


@dataclass
class ScaleBar(MapElement):
    """Scale bar element."""
    length: float = 100.0
    unit: str = "m"  # m, km, ft, mi
    position: str = "bottom_left"
    style: str = "bar"  # bar, line, dual


@dataclass
class NorthArrow(MapElement):
    """North arrow element."""
    style: str = "simple"  # simple, fancy, detailed
    size: float = 40.0


class MapTemplate:
    """Map composition template."""
    
    def __init__(self, name: str, width: float = 210, height: float = 297):
        """
        Create map template (A4 default).
        
        Args:
            name: Template name
            width: Page width in mm
            height: Page height in mm
        """
        self.name = name
        self.width = width
        self.height = height
        self.title: Optional[MapTitle] = None
        self.legend: Optional[MapLegend] = None
        self.scale_bar: Optional[ScaleBar] = None
        self.north_arrow: Optional[NorthArrow] = None
        self.background_color = "#FFFFFF"
        self.margin = 10  # mm
        
        self.map_extent = Tuple[float, float, float, float]  # minx, miny, maxx, maxy
    
    def add_title(self, text: str, font_size: int = 24) -> 'MapTemplate':
        """Add title to map."""
        self.title = MapTitle(
            x=self.margin,
            y=self.margin,
            width=self.width - 2 * self.margin,
            height=20,
            text=text,
            font_size=font_size
        )
        return self
    
    def add_legend(self, title: str = "Legend") -> 'MapTemplate':
        """Add legend to map."""
        self.legend = MapLegend(
            x=self.width - 60,
            y=self.margin + 30,
            width=50,
            height=self.height - 2 * self.margin - 40,
            title=title
        )
        return self
    
    def add_scale_bar(self, position: str = "bottom_left") -> 'MapTemplate':
        """Add scale bar to map."""
        x = self.margin if position == "bottom_left" else self.width - 50
        y = self.height - 20
        
        self.scale_bar = ScaleBar(
            x=x,
            y=y,
            width=40,
            height=15,
            position=position
        )
        return self
    
    def add_north_arrow(self, position: str = "top_right") -> 'MapTemplate':
        """Add north arrow to map."""
        x = self.width - 30 if position == "top_right" else self.margin
        y = self.margin + 30
        
        self.north_arrow = NorthArrow(
            x=x,
            y=y,
            width=20,
            height=20,
            size=30
        )
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize template to dictionary."""
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'title': {'text': self.title.text, 'size': self.title.font_size} if self.title else None,
            'legend': {'title': self.legend.title} if self.legend else None,
            'scale_bar': {'position': self.scale_bar.position} if self.scale_bar else None,
            'north_arrow': {'style': self.north_arrow.style} if self.north_arrow else None,
            'background_color': self.background_color,
            'margin': self.margin
        }


class ExportManager:
    """Handle export of maps and data to various formats."""
    
    def __init__(self):
        self.format_handlers = {
            ExportFormat.GeoJSON: self._export_geojson,
            ExportFormat.Shapefile: self._export_shapefile,
            ExportFormat.CSV: self._export_csv,
            ExportFormat.KML: self._export_kml,
        }
    
    def export(
        self,
        gdf: GeoDataFrame,
        output_path: str,
        format: ExportFormat,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export GeoDataFrame to specified format.
        
        Args:
            gdf: GeoDataFrame to export
            output_path: Output file path
            format: Export format
            options: Format-specific options
            
        Returns:
            True if successful
        """
        try:
            if format not in self.format_handlers:
                raise ValueError(f"Unsupported format: {format}")
            
            handler = self.format_handlers[format]
            handler(gdf, output_path, options or {})
            
            logger.info(f"Exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise
    
    def _export_geojson(
        self,
        gdf: GeoDataFrame,
        output_path: str,
        options: Dict[str, Any]
    ):
        """Export to GeoJSON."""
        gdf.to_file(output_path, driver='GeoJSON')
    
    def _export_shapefile(
        self,
        gdf: GeoDataFrame,
        output_path: str,
        options: Dict[str, Any]
    ):
        """Export to Shapefile."""
        gdf.to_file(output_path, driver='ESRI Shapefile')
    
    def _export_csv(
        self,
        gdf: GeoDataFrame,
        output_path: str,
        options: Dict[str, Any]
    ):
        """Export to CSV."""
        include_geometry = options.get('include_geometry', False)
        
        if include_geometry:
            gdf['geometry_wkt'] = gdf.geometry.to_wkt()
        
        df = gdf.drop('geometry', axis=1)
        df.to_csv(output_path, index=False)
    
    def _export_kml(
        self,
        gdf: GeoDataFrame,
        output_path: str,
        options: Dict[str, Any]
    ):
        """Export to KML."""
        gdf.to_file(output_path, driver='KML')
    
    def export_geotiff(
        self,
        array: np.ndarray,
        output_path: str,
        transform: Any,  # rasterio.Affine
        crs: str
    ):
        """
        Export raster to GeoTIFF.
        
        Args:
            array: Raster array
            output_path: Output file path
            transform: Rasterio transform
            crs: Coordinate reference system
        """
        try:
            import rasterio
            # Import Affine if not already imported at module level
            try:
                from rasterio.transform import Affine as RasterioAffine
            except ImportError:
                # Create identity transform
                RasterioAffine = None
            
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=array.shape[0],
                width=array.shape[1],
                count=1,
                dtype=array.dtype,
                crs=crs,
                transform=transform
            ) as dst:
                dst.write(array, 1)
            
            logger.info(f"Exported GeoTIFF to {output_path}")
            
        except Exception as e:
            logger.error(f"GeoTIFF export error: {e}")
            raise


class BatchExporter:
    """Batch export multiple layers."""
    
    def __init__(self, export_manager: ExportManager):
        self.export_manager = export_manager
    
    def export_layers(
        self,
        gdfs: Dict[str, GeoDataFrame],
        output_dir: str,
        format: ExportFormat
    ) -> Dict[str, bool]:
        """
        Export multiple layers.
        
        Args:
            gdfs: Dict of {layer_name: GeoDataFrame}
            output_dir: Output directory
            format: Export format
            
        Returns:
            Dict of {layer_name: success}
        """
        results = {}
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for layer_name, gdf in gdfs.items():
            try:
                output_path = str(Path(output_dir) / f"{layer_name}.{format.value}")
                self.export_manager.export(gdf, output_path, format)
                results[layer_name] = True
            except Exception as e:
                logger.error(f"Export failed for {layer_name}: {e}")
                results[layer_name] = False
        
        return results


# Module exports
__all__ = [
    'MapTemplate',
    'ExportManager',
    'BatchExporter',
    'ExportFormat',
    'MapTitle',
    'MapLegend',
    'ScaleBar',
    'NorthArrow'
]
