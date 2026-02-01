"""
Export Module - Data export and reporting

Handles:
- GeoTIFF export
- Report generation (HTML, PDF, JSON, CSV)
- Visualization exports
- Shapefile export
"""

from typing import Dict, Any, Optional, Union, BinaryIO
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import numpy as np
import json


@dataclass
class ExportConfig:
    """Configuration for export operations"""
    output_dir: Path = Path('./exports')
    include_metadata: bool = True
    compression: str = 'lzw'  # For GeoTIFF


class ExportManager:
    """Manages data export in various formats"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_geotiff(
        self,
        data: np.ndarray,
        filepath: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Export data as GeoTIFF"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import rasterio
            from rasterio.transform import Affine
            
            height, width = data.shape
            
            # Default transform (1m pixel, origin at 0,0)
            transform = Affine.identity()
            
            with rasterio.open(
                filepath,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=data.dtype,
                crs='EPSG:4326',
                transform=transform,
                compress=self.config.compression
            ) as dst:
                dst.write(data, 1)
            
            return filepath
        
        except ImportError:
            raise RuntimeError("rasterio not installed for GeoTIFF export")
    
    def export_json(
        self,
        data: Dict[str, Any],
        filepath: Union[str, Path]
    ) -> Path:
        """Export analysis results as JSON"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        json_data = self._make_serializable(data)
        
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        return filepath
    
    def export_csv(
        self,
        data: np.ndarray,
        filepath: Union[str, Path],
        column_names: Optional[list] = None
    ) -> Path:
        """Export data as CSV"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        np.savetxt(filepath, data, delimiter=',', header=','.join(column_names or []))
        return filepath
    
    def generate_html_report(
        self,
        title: str,
        content: Dict[str, Any],
        filepath: Optional[Union[str, Path]] = None
    ) -> Union[str, Path]:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .section {{ margin: 20px 0; padding: 10px; border-left: 4px solid #0066cc; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
        """
        
        for section_name, section_data in content.items():
            html += f'<div class="section"><h2>{section_name}</h2>'
            
            if isinstance(section_data, dict):
                html += '<table>'
                for key, value in section_data.items():
                    html += f'<tr><td><b>{key}</b></td><td>{value}</td></tr>'
                html += '</table>'
            elif isinstance(section_data, list):
                html += '<ul>'
                for item in section_data:
                    html += f'<li>{item}</li>'
                html += '</ul>'
            
            html += '</div>'
        
        html += '</body></html>'
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(html)
            return filepath
        
        return html
    
    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """Convert numpy types to Python types for JSON serialization"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: ExportManager._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ExportManager._make_serializable(item) for item in obj]
        return obj


class ExportModule:
    """Main export module"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.manager = ExportManager(self.config)
    
    def export_results(
        self,
        results: Dict[str, Any],
        output_format: str = 'json',
        filename: Optional[str] = None
    ) -> Path:
        """Export analysis results"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'analysis_{timestamp}'
        
        filepath = self.config.output_dir / f'{filename}.{output_format}'
        
        if output_format == 'json':
            return self.manager.export_json(results, filepath)
        elif output_format == 'csv':
            if 'data' in results:
                return self.manager.export_csv(results['data'], filepath)
        elif output_format == 'html':
            return self.manager.generate_html_report('Analysis Report', results, filepath)
        
        raise ValueError(f"Unsupported export format: {output_format}")


__all__ = ['ExportModule', 'ExportManager', 'ExportConfig']
