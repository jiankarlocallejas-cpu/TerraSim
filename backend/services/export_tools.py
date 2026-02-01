"""
Print and export functionality for maps and data.
Supports multiple formats: GeoTIFF, Shapefile, GeoJSON, PNG, PDF with layout composer.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Export formats"""
    GEOTIFF = "geotiff"
    SHAPEFILE = "shapefile"
    GEOJSON = "geojson"
    CSV = "csv"
    PNG = "png"
    JPG = "jpg"
    PDF = "pdf"
    SVG = "svg"
    GML = "gml"
    GPKG = "gpkg"


@dataclass
class ExportOptions:
    """Export options"""
    format: ExportFormat
    output_path: str
    crs: str = "EPSG:4326"
    include_styles: bool = True
    include_metadata: bool = True
    compression: Optional[str] = None  # For rasters
    resolution_dpi: int = 300
    metadata_title: str = "TerraSim Export"
    metadata_author: str = "TerraSim"
    metadata_date: str = ""
    
    def __post_init__(self):
        if not self.metadata_date:
            self.metadata_date = datetime.now().isoformat()


class ExportManager:
    """Manage data export"""
    
    def __init__(self):
        self.export_drivers = {
            ExportFormat.GEOTIFF: GeoTIFFExporter(),
            ExportFormat.SHAPEFILE: ShapefileExporter(),
            ExportFormat.GEOJSON: GeoJSONExporter(),
            ExportFormat.CSV: CSVExporter(),
            ExportFormat.GPKG: GeoPackageExporter(),
        }
        self.export_history = []
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export data"""
        try:
            if options.format not in self.export_drivers:
                return False, f"Unsupported format: {options.format}"
            
            exporter = self.export_drivers[options.format]
            success, message = exporter.export(data, options)
            
            if success:
                self.export_history.append({
                    'format': options.format,
                    'path': options.output_path,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Export successful: {options.output_path}")
            else:
                logger.error(f"Export failed: {message}")
            
            return success, message
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False, str(e)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return [fmt.value for fmt in ExportFormat]


class BaseExporter:
    """Base exporter class"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export data"""
        raise NotImplementedError


class GeoTIFFExporter(BaseExporter):
    """Export to GeoTIFF format"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export raster to GeoTIFF"""
        try:
            import rasterio
            from rasterio.transform import from_bounds
            
            # Prepare data
            if hasattr(data, '_data'):
                raster_data = data._data
            else:
                raster_data = data
            
            if raster_data is None:
                return False, "No raster data"
            
            # Get metadata
            bounds = data.get_extent() if hasattr(data, 'get_extent') else None
            if not bounds:
                bounds = [0, raster_data.shape[1], 0, raster_data.shape[0]]
            
            # Create transform
            height, width = raster_data.shape[:2]
            transform = from_bounds(bounds[0], bounds[2], bounds[1], bounds[3], width, height)
            
            # Write file
            with rasterio.open(
                options.output_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=raster_data.dtype,
                crs=options.crs,
                transform=transform,
                compress=options.compression or 'lzw'
            ) as dst:
                dst.write(raster_data, 1)
            
            return True, f"Exported to {options.output_path}"
        except ImportError:
            return False, "rasterio not installed"
        except Exception as e:
            return False, str(e)


class ShapefileExporter(BaseExporter):
    """Export to Shapefile format"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export vector to Shapefile"""
        try:
            import geopandas as gpd
            from shapely.geometry import shape
            
            # Prepare GeoDataFrame
            if isinstance(data, gpd.GeoDataFrame):
                gdf = data
            elif hasattr(data, '_data') and isinstance(data._data, gpd.GeoDataFrame):
                gdf = data._data
            else:
                return False, "Input is not GeoDataFrame"
            
            # Reproject if needed
            if gdf.crs != options.crs:
                gdf = gdf.to_crs(options.crs)
            
            # Write file
            output_dir = os.path.dirname(options.output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            gdf.to_file(options.output_path, driver='ESRI Shapefile')
            
            return True, f"Exported to {options.output_path}"
        except ImportError:
            return False, "geopandas not installed"
        except Exception as e:
            return False, str(e)


class GeoJSONExporter(BaseExporter):
    """Export to GeoJSON format"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export to GeoJSON"""
        try:
            import json
            import geopandas as gpd
            
            # Prepare GeoDataFrame
            if isinstance(data, gpd.GeoDataFrame):
                gdf = data
            elif hasattr(data, '_data') and isinstance(data._data, gpd.GeoDataFrame):
                gdf = data._data
            else:
                return False, "Input is not GeoDataFrame"
            
            # Reproject if needed
            if gdf.crs != options.crs:
                gdf = gdf.to_crs(options.crs)
            
            # Create output directory
            output_dir = os.path.dirname(options.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Add metadata
            feature_collection = {
                "type": "FeatureCollection",
                "features": json.loads(gdf.to_json())["features"]
            }
            
            if options.include_metadata:
                feature_collection["metadata"] = {
                    "title": options.metadata_title,
                    "author": options.metadata_author,
                    "date": options.metadata_date,
                    "crs": options.crs
                }
            
            # Write file
            with open(options.output_path, 'w') as f:
                json.dump(feature_collection, f, indent=2)
            
            return True, f"Exported to {options.output_path}"
        except ImportError:
            return False, "geopandas/json not available"
        except Exception as e:
            return False, str(e)


class CSVExporter(BaseExporter):
    """Export to CSV format"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export attributes to CSV"""
        try:
            import geopandas as gpd
            
            # Prepare GeoDataFrame
            if isinstance(data, gpd.GeoDataFrame):
                gdf = data
            elif hasattr(data, '_data') and isinstance(data._data, gpd.GeoDataFrame):
                gdf = data._data
            else:
                return False, "Input is not GeoDataFrame"
            
            # Create output directory
            output_dir = os.path.dirname(options.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Export non-geometry columns
            df = gdf.drop(columns=['geometry'], errors='ignore')
            df.to_csv(options.output_path, index=False)
            
            return True, f"Exported to {options.output_path}"
        except Exception as e:
            return False, str(e)


class GeoPackageExporter(BaseExporter):
    """Export to GeoPackage (GPKG) format"""
    
    def export(self, data: Any, options: ExportOptions) -> Tuple[bool, str]:
        """Export to GeoPackage"""
        try:
            import geopandas as gpd
            
            # Prepare GeoDataFrame
            if isinstance(data, gpd.GeoDataFrame):
                gdf = data
            elif hasattr(data, '_data') and isinstance(data._data, gpd.GeoDataFrame):
                gdf = data._data
            else:
                return False, "Input is not GeoDataFrame"
            
            # Reproject if needed
            if gdf.crs != options.crs:
                gdf = gdf.to_crs(options.crs)
            
            # Create output directory
            output_dir = os.path.dirname(options.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Write file
            gdf.to_file(options.output_path, driver='GPKG')
            
            return True, f"Exported to {options.output_path}"
        except ImportError:
            return False, "geopandas not installed"
        except Exception as e:
            return False, str(e)


class PrintLayoutComposer:
    """Compose map for printing"""
    
    def __init__(self, page_width_mm: float = 210, page_height_mm: float = 297):
        self.page_width_mm = page_width_mm
        self.page_height_mm = page_height_mm
        self.elements = []
        self.scale = 1.0
        self.dpi = 300
    
    def add_map(self, map_image: Any, rect: Tuple[float, float, float, float]):
        """Add map to layout"""
        self.elements.append({
            'type': 'map',
            'image': map_image,
            'rect': rect  # (x, y, width, height) in mm
        })
    
    def add_title(self, title: str, rect: Tuple[float, float, float, float], font_size: int = 24):
        """Add title to layout"""
        self.elements.append({
            'type': 'text',
            'text': title,
            'rect': rect,
            'font_size': font_size,
            'font_weight': 'bold'
        })
    
    def add_scale_bar(self, rect: Tuple[float, float, float, float]):
        """Add scale bar to layout"""
        self.elements.append({
            'type': 'scale_bar',
            'rect': rect
        })
    
    def add_north_arrow(self, rect: Tuple[float, float, float, float]):
        """Add north arrow to layout"""
        self.elements.append({
            'type': 'north_arrow',
            'rect': rect
        })
    
    def add_legend(self, layers: List[Dict[str, Any]], rect: Tuple[float, float, float, float]):
        """Add legend to layout"""
        self.elements.append({
            'type': 'legend',
            'layers': layers,
            'rect': rect
        })
    
    def add_text(self, text: str, rect: Tuple[float, float, float, float], font_size: int = 12):
        """Add text to layout"""
        self.elements.append({
            'type': 'text',
            'text': text,
            'rect': rect,
            'font_size': font_size
        })
    
    def render_pdf(self, output_path: str) -> Tuple[bool, str]:
        """Render layout to PDF"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from reportlab.lib.pagesizes import A4
            
            # Create canvas
            c = canvas.Canvas(output_path, pagesize=A4)
            
            # Render elements
            for element in self.elements:
                if element['type'] == 'text':
                    x, y, w, h = element['rect']
                    c.setFont("Helvetica", element.get('font_size', 12))
                    c.drawString(x*mm, (297-y-h)*mm, element['text'])
                elif element['type'] == 'map':
                    x, y, w, h = element['rect']
                    # Placeholder for actual image rendering
                    pass
            
            c.save()
            return True, f"PDF created: {output_path}"
        except ImportError:
            return False, "reportlab not installed"
        except Exception as e:
            return False, str(e)
    
    def render_image(self, output_path: str, format: str = "png", dpi: int = 300) -> Tuple[bool, str]:
        """Render layout to image"""
        try:
            from PIL import Image, ImageDraw
            import math
            
            # Calculate image size
            width_px = int(self.page_width_mm / 25.4 * dpi)
            height_px = int(self.page_height_mm / 25.4 * dpi)
            
            # Create image
            img = Image.new('RGB', (width_px, height_px), color='white')
            draw = ImageDraw.Draw(img)
            
            # Render elements (simplified)
            for element in self.elements:
                if element['type'] == 'text':
                    x, y, w, h = element['rect']
                    x_px = int(x / 25.4 * dpi)
                    y_px = int(y / 25.4 * dpi)
                    draw.text((x_px, y_px), element['text'], fill='black')
            
            # Save image
            img.save(output_path, format=format.upper())
            return True, f"{format.upper()} created: {output_path}"
        except ImportError:
            return False, "Pillow not installed"
        except Exception as e:
            return False, str(e)
