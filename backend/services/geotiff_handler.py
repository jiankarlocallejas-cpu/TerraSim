"""
GeoTIFF Handler - Full support for reading all metadata, multi-band data, and auto-map generation
"""

import numpy as np
import rasterio
from rasterio.plot import show
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeoTIFFMetadata:
    """Complete GeoTIFF metadata"""
    filepath: str
    width: int
    height: int
    count: int  # Number of bands
    dtype: str
    crs: Optional[str]  # Coordinate Reference System
    transform: Optional[Dict[str, float]]  # Geospatial transform
    bounds: Optional[Tuple[float, float, float, float]]  # (left, bottom, right, top)
    nodata: Optional[float]
    band_descriptions: List[str]
    band_dtypes: List[str]
    band_statistics: List[Dict[str, float]]
    tags: Dict[str, str]
    

class GeoTIFFHandler:
    """Comprehensive GeoTIFF reader with metadata preservation and map auto-generation"""
    
    def __init__(self, filepath: str):
        """Initialize with GeoTIFF file"""
        self.filepath = filepath
        self.src = None
        self.metadata = None
        self._load_metadata()
    
    def _load_metadata(self):
        """Load complete GeoTIFF metadata"""
        try:
            with rasterio.open(self.filepath) as src:
                band_descriptions = []
                band_dtypes = []
                band_statistics = []
                
                # Extract metadata for each band
                for i in range(1, src.count + 1):
                    band = src.read(i)
                    desc = src.descriptions[i-1] if src.descriptions else f"Band {i}"
                    band_descriptions.append(desc or f"Band {i}")
                    band_dtypes.append(str(band.dtype))
                    
                    # Calculate statistics
                    valid_data = band[~np.isnan(band) & (band != src.nodata)]
                    if len(valid_data) > 0:
                        band_statistics.append({
                            'min': float(np.min(valid_data)),
                            'max': float(np.max(valid_data)),
                            'mean': float(np.mean(valid_data)),
                            'std': float(np.std(valid_data)),
                            'count': int(len(valid_data))
                        })
                    else:
                        band_statistics.append({
                            'min': 0.0, 'max': 0.0, 'mean': 0.0,
                            'std': 0.0, 'count': 0
                        })
                
                # Extract transform as dict for serialization
                transform_dict = None
                if src.transform:
                    transform_dict = {
                        'a': float(src.transform.a),  # pixel width
                        'b': float(src.transform.b),
                        'c': float(src.transform.c),  # x coordinate of upper-left
                        'd': float(src.transform.d),  # pixel height
                        'e': float(src.transform.e),
                        'f': float(src.transform.f)   # y coordinate of upper-left
                    }
                
                # Get bounds
                bounds = tuple(src.bounds) if src.bounds else None
                
                # Get all tags
                tags = src.tags()
                
                self.metadata = GeoTIFFMetadata(
                    filepath=self.filepath,
                    width=src.width,
                    height=src.height,
                    count=src.count,
                    dtype=str(src.dtypes[0]),
                    crs=str(src.crs) if src.crs else None,
                    transform=transform_dict,
                    bounds=bounds,
                    nodata=src.nodata,
                    band_descriptions=band_descriptions,
                    band_dtypes=band_dtypes,
                    band_statistics=band_statistics,
                    tags=tags
                )
                
                logger.info(f"GeoTIFF metadata loaded: {src.count} bands, {src.width}x{src.height}")
        
        except Exception as e:
            logger.error(f"Error loading GeoTIFF metadata: {e}")
            raise
    
    def get_band(self, band_index: int = 1) -> np.ndarray:
        """Get a specific band (1-indexed)"""
        with rasterio.open(self.filepath) as src:
            if band_index < 1 or band_index > src.count:
                raise ValueError(f"Band {band_index} not found. File has {src.count} bands")
            band_data = src.read(band_index).astype(np.float32)
            return band_data
    
    def get_all_bands(self) -> np.ndarray:
        """Get all bands as 3D array (bands, height, width)"""
        with rasterio.open(self.filepath) as src:
            data = src.read().astype(np.float32)
            return data
    
    def is_multispectral(self) -> bool:
        """Check if file contains multispectral data (>3 bands)"""
        return self.metadata.count > 3 if self.metadata else False
    
    def is_rgb(self) -> bool:
        """Check if file appears to be RGB (exactly 3 bands)"""
        return self.metadata.count == 3 if self.metadata else False
    
    def has_ndvi_bands(self) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Detect if file contains NIR and Red bands for NDVI calculation
        Returns: (has_ndvi, nir_band_idx, red_band_idx) - 1-indexed or None
        """
        if not self.metadata:
            return False, None, None
        
        descriptions = [d.lower() for d in self.metadata.band_descriptions]
        
        nir_idx = None
        red_idx = None
        
        for i, desc in enumerate(descriptions):
            if 'nir' in desc or 'infrared' in desc:
                nir_idx = i + 1
            elif 'red' in desc:
                red_idx = i + 1
        
        has_ndvi = nir_idx is not None and red_idx is not None
        return has_ndvi, nir_idx, red_idx
    
    def calculate_ndvi(self, nir_band: int | None = None, red_band: int | None = None) -> np.ndarray:
        """
        Calculate NDVI (Normalized Difference Vegetation Index)
        Default: assumes band order follows typical satellite imagery
        """
        if nir_band is None or red_band is None:
            has_ndvi, nir_idx, red_idx = self.has_ndvi_bands()
            if has_ndvi and nir_idx is not None and red_idx is not None:
                nir_band = nir_idx
                red_band = red_idx
            else:
                # Try common defaults
                if self.metadata and self.metadata.count >= 4:
                    nir_band = 4  # Landsat band 4 (NIR)
                    red_band = 3  # Landsat band 3 (Red)
                else:
                    raise ValueError("Cannot auto-detect NIR/Red bands. Please specify band indices.")
        
        if nir_band is None or red_band is None:
            raise ValueError("Could not determine NIR/Red bands")
        
        nir = self.get_band(nir_band).astype(np.float32)
        red = self.get_band(red_band).astype(np.float32)
        
        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = (nir - red) / (nir + red + 1e-8)
        ndvi = np.clip(ndvi, -1, 1)
        
        return ndvi
    
    def generate_rgb_composite(self, r_band: int | None = None, g_band: int | None = None, b_band: int | None = None) -> np.ndarray:
        """
        Generate RGB composite from specified bands
        Default: uses first 3 bands or tries to auto-detect R,G,B
        """
        if not self.metadata:
            raise ValueError("Metadata not loaded")
        
        if self.metadata.count < 3:
            raise ValueError(f"File has {self.metadata.count} bands, need at least 3 for RGB")
        
        if r_band is None:
            r_band = 1 if self.metadata.count >= 1 else 1
        if g_band is None:
            g_band = 2 if self.metadata.count >= 2 else 1
        if b_band is None:
            b_band = 3 if self.metadata.count >= 3 else 1
        
        # Read bands
        red = self.get_band(r_band)
        green = self.get_band(g_band)
        blue = self.get_band(b_band)
        
        # Normalize to 0-1
        red = (red - red.min()) / (red.max() - red.min() + 1e-8)
        green = (green - green.min()) / (green.max() - green.min() + 1e-8)
        blue = (blue - blue.min()) / (blue.max() - blue.min() + 1e-8)
        
        # Stack into RGB
        rgb = np.stack([red, green, blue], axis=2)
        
        return np.clip(rgb, 0, 1).astype(np.float32)
    
    def auto_generate_map(self) -> np.ndarray:
        """
        Automatically generate a map layer from multi-band data
        Strategy:
        1. If has NDVI bands: generate NDVI map
        2. Else if has RGB: generate RGB composite
        3. Else if multispectral: use first band as map
        4. Else: use single band as map
        """
        if not self.metadata:
            raise ValueError("Metadata not loaded")
        
        logger.info(f"Auto-generating map from {self.metadata.count} bands")
        
        # Strategy 1: NDVI
        has_ndvi, _, _ = self.has_ndvi_bands()
        if has_ndvi:
            logger.info("Detected NIR/Red bands, generating NDVI map")
            ndvi = self.calculate_ndvi()
            ndvi_map = (ndvi + 1) / 2  # Normalize NDVI from [-1, 1] to [0, 1]
            return np.clip(ndvi_map, 0, 1).astype(np.float32)
        
        # Strategy 2: RGB Composite
        if self.is_rgb() or self.metadata.count >= 3:
            logger.info("Generating RGB composite map")
            rgb = self.generate_rgb_composite()
            # Convert RGB to grayscale for single-band map
            gray = np.mean(rgb, axis=2)
            return np.clip(gray, 0, 1).astype(np.float32)
        
        # Strategy 3: Use first non-DEM band as map
        logger.info("Using first band as map")
        map_data = self.get_band(1)
        map_data = (map_data - map_data.min()) / (map_data.max() - map_data.min() + 1e-8)
        return np.clip(map_data, 0, 1).astype(np.float32)
    
    def get_band_info(self) -> Dict[str, Any]:
        """Get information about all bands"""
        if not self.metadata:
            return {}
        
        bands_info = []
        for i, (desc, dtype, stats) in enumerate(zip(
            self.metadata.band_descriptions,
            self.metadata.band_dtypes,
            self.metadata.band_statistics
        ), 1):
            bands_info.append({
                'index': i,
                'description': desc,
                'dtype': dtype,
                'min': stats['min'],
                'max': stats['max'],
                'mean': stats['mean'],
                'std': stats['std'],
                'valid_pixels': stats['count']
            })
        
        return {
            'filepath': self.filepath,
            'dimensions': f"{self.metadata.width}x{self.metadata.height}",
            'band_count': self.metadata.count,
            'crs': self.metadata.crs,
            'bounds': self.metadata.bounds,
            'nodata': self.metadata.nodata,
            'bands': bands_info
        }
    
    def save_metadata_to_json(self, output_path: str):
        """Export metadata to JSON"""
        import json
        
        if not self.metadata:
            raise ValueError("Metadata not loaded")
        
        metadata_dict = {
            'filepath': self.filepath,
            'width': self.metadata.width,
            'height': self.metadata.height,
            'band_count': self.metadata.count,
            'dtype': self.metadata.dtype,
            'crs': self.metadata.crs,
            'transform': self.metadata.transform,
            'bounds': self.metadata.bounds,
            'nodata': self.metadata.nodata,
            'band_descriptions': self.metadata.band_descriptions,
            'band_dtypes': self.metadata.band_dtypes,
            'band_statistics': self.metadata.band_statistics,
            'tags': self.metadata.tags
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        logger.info(f"Metadata exported to {output_path}")
