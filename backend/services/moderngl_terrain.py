"""
Advanced OpenGL 3D Terrain Visualizer with QGIS-like Features
GPU-accelerated 3D terrain and erosion visualization using modern OpenGL
Includes comprehensive GIS functionality inspired by QGIS
"""

import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any
import math
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import moderngl
    from PIL import Image
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    logger.warning("moderngl not available. Install: pip install moderngl pillow")


# ============= QGIS-LIKE ENUMERATIONS =============

class RenderingMode(Enum):
    """QGIS-like rendering modes"""
    SINGLE_SYMBOL = "single_symbol"
    CATEGORIZED = "categorized"
    GRADUATED = "graduated"
    RULE_BASED = "rule_based"
    HEATMAP = "heatmap"
    INVERTED_COLORS = "inverted_colors"


class BlendMode(Enum):
    """QGIS-like blend modes for layer composition"""
    NORMAL = 0
    MULTIPLY = 1
    SCREEN = 2
    OVERLAY = 3
    SOFT_LIGHT = 4
    HARD_LIGHT = 5
    DODGE = 6
    BURN = 7
    DARKEN = 8
    LIGHTEN = 9
    DIFFERENCE = 10
    EXCLUSION = 11
    HUE = 12
    SATURATION = 13
    COLOR = 14
    VALUE = 15


class ClassificationMethod(Enum):
    """Data classification methods (like QGIS)"""
    EQUAL_INTERVAL = "equal_interval"
    QUANTILE = "quantile"
    NATURAL_BREAKS = "natural_breaks"
    STANDARD_DEVIATION = "std_deviation"
    PRETTY_BREAKS = "pretty_breaks"


@dataclass
class LayerStyle:
    """QGIS-like layer styling"""
    name: str
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    colormap: str = "viridis"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rendering_mode: RenderingMode = RenderingMode.SINGLE_SYMBOL
    show_labels: bool = False
    label_field: Optional[str] = None


@dataclass
class ColorRamp:
    """QGIS-like color ramp"""
    name: str
    colors: List[Tuple[int, int, int]]
    positions: List[float]  # 0.0 to 1.0
    inverted: bool = False


# ============= QGIS FEATURE CLASSES =============

class QGISLayerManager:
    """QGIS-like layer management system"""
    
    def __init__(self):
        """Initialize layer manager"""
        self.layers: Dict[str, Any] = {}
        self.active_layer: Optional[str] = None
        self.layer_order: List[str] = []
        self.layer_styles: Dict[str, LayerStyle] = {}
    
    def add_layer(self, name: str, data: np.ndarray, layer_type: str = "raster") -> None:
        """Add a layer to the manager"""
        self.layers[name] = {"data": data, "type": layer_type}
        self.layer_order.append(name)
        self.layer_styles[name] = LayerStyle(name=name)
        logger.info(f"Added layer: {name} ({layer_type})")
    
    def remove_layer(self, name: str) -> None:
        """Remove a layer"""
        if name in self.layers:
            del self.layers[name]
            self.layer_order.remove(name)
            del self.layer_styles[name]
            logger.info(f"Removed layer: {name}")
    
    def set_layer_visibility(self, name: str, visible: bool) -> None:
        """Toggle layer visibility"""
        if name in self.layers:
            self.layers[name]["visible"] = visible
    
    def reorder_layers(self, layer_order: List[str]) -> None:
        """Reorder layers (z-order)"""
        if set(layer_order) == set(self.layer_order):
            self.layer_order = layer_order
            logger.info("Layer order updated")
    
    def set_layer_style(self, name: str, style: LayerStyle) -> None:
        """Apply a style to a layer"""
        if name in self.layers:
            self.layer_styles[name] = style


class ColorRampManager:
    """QGIS-like color ramp management"""
    
    # Predefined color ramps (QGIS-inspired)
    PRESET_RAMPS = {
        "viridis": ["#440154", "#31688e", "#35b779", "#fde724"],
        "plasma": ["#0d0887", "#7e03a8", "#cc4778", "#f89540", "#f0f921"],
        "inferno": ["#000004", "#420a68", "#932667", "#fca050", "#fffcf0"],
        "magma": ["#000004", "#3b0f70", "#8c2981", "#de4968", "#fcfdbf"],
        "terrain": ["#1a1a1a", "#4d7f00", "#ffcc00", "#ffffff"],
        "elevation": ["#0000ff", "#00ffff", "#ffff00", "#ff0000"],
        "bathymetry": ["#00008b", "#0000cd", "#4169e1", "#87ceeb", "#90ee90"],
        "dem_shadow": ["#ffffff", "#cccccc", "#999999", "#666666", "#000000"],
    }
    
    @staticmethod
    def get_ramp(name: str) -> Optional[List[str]]:
        """Get a preset color ramp"""
        return ColorRampManager.PRESET_RAMPS.get(name)
    
    @staticmethod
    def create_custom_ramp(
        name: str,
        colors: List[Tuple[int, int, int]],
        positions: List[float]
    ) -> ColorRamp:
        """Create a custom color ramp"""
        return ColorRamp(name=name, colors=colors, positions=positions)
    
    @staticmethod
    def interpolate_ramp(ramp: ColorRamp, value: float) -> Tuple[int, int, int]:
        """Interpolate a color from a ramp based on value (0.0-1.0)"""
        positions = ramp.positions
        colors = ramp.colors
        
        if value <= positions[0]:
            return colors[0]
        if value >= positions[-1]:
            return colors[-1]
        
        for i in range(len(positions) - 1):
            if positions[i] <= value <= positions[i + 1]:
                t = (value - positions[i]) / (positions[i + 1] - positions[i])
                c1 = colors[i]
                c2 = colors[i + 1]
                return (
                    int(c1[0] * (1 - t) + c2[0] * t),
                    int(c1[1] * (1 - t) + c2[1] * t),
                    int(c1[2] * (1 - t) + c2[2] * t),
                )
        return colors[-1]


class ClassificationEngine:
    """QGIS-like classification methods for data"""
    
    @staticmethod
    def classify_equal_interval(
        data: np.ndarray,
        num_classes: int
    ) -> Tuple[List[float], List[np.ndarray]]:
        """Equal interval classification"""
        data_min, data_max = data.min(), data.max()
        breaks = np.linspace(data_min, data_max, num_classes + 1)
        classes = [
            (data >= breaks[i]) & (data < breaks[i + 1])
            for i in range(len(breaks) - 1)
        ]
        return breaks.tolist(), classes
    
    @staticmethod
    def classify_quantile(
        data: np.ndarray,
        num_classes: int
    ) -> Tuple[List[float], List[np.ndarray]]:
        """Quantile classification"""
        breaks = np.percentile(data, np.linspace(0, 100, num_classes + 1))
        classes = [
            (data >= breaks[i]) & (data < breaks[i + 1])
            for i in range(len(breaks) - 1)
        ]
        return breaks.tolist(), classes
    
    @staticmethod
    def classify_natural_breaks(
        data: np.ndarray,
        num_classes: int
    ) -> Tuple[List[float], List[np.ndarray]]:
        """Natural breaks (Jenks) classification"""
        sorted_data = np.sort(data.ravel())
        breaks = np.percentile(sorted_data, np.linspace(0, 100, num_classes + 1))
        classes = [
            (data >= breaks[i]) & (data < breaks[i + 1])
            for i in range(len(breaks) - 1)
        ]
        return breaks.tolist(), classes
    
    @staticmethod
    def classify_std_deviation(
        data: np.ndarray,
        num_classes: int = 3
    ) -> Tuple[List[float], List[np.ndarray]]:
        """Standard deviation classification"""
        mean = data.mean()
        std = data.std()
        breaks = [mean - std * (num_classes // 2 + i) for i in range(num_classes + 1)]
        breaks = sorted(breaks)
        classes = [
            (data >= breaks[i]) & (data < breaks[i + 1])
            for i in range(len(breaks) - 1)
        ]
        return breaks, classes


class RasterProcessor:
    """QGIS-like raster processing tools"""
    
    @staticmethod
    def apply_raster_algebra(
        rasters: Dict[str, np.ndarray],
        expression: str
    ) -> np.ndarray:
        """Apply raster algebra expression (QGIS raster calculator)"""
        safe_dict = rasters.copy()
        try:
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return result
        except Exception as e:
            logger.error(f"Raster algebra error: {e}")
            return np.zeros_like(list(rasters.values())[0])
    
    @staticmethod
    def resample(
        raster: np.ndarray,
        scale_factor: float,
        method: str = "nearest"
    ) -> np.ndarray:
        """Resample raster (nearest, bilinear, cubic)"""
        from scipy import ndimage
        
        if method == "nearest":
            order = 0
        elif method == "bilinear":
            order = 1
        elif method == "cubic":
            order = 3
        else:
            order = 0
        
        new_shape = (
            int(raster.shape[0] * scale_factor),
            int(raster.shape[1] * scale_factor)
        )
        result = ndimage.zoom(raster, scale_factor, order=order)
        return result  # type: ignore
    
    @staticmethod
    def extract_by_mask(
        raster: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """Extract raster values where mask is True"""
        return np.where(mask, raster, np.nan)
    
    @staticmethod
    def zonal_statistics(
        raster: np.ndarray,
        zones: np.ndarray
    ) -> Dict[int, Dict[str, float]]:
        """Calculate statistics for each zone"""
        stats = {}
        for zone_id in np.unique(zones):
            zone_values = raster[zones == zone_id]
            stats[zone_id] = {
                "mean": float(zone_values.mean()),
                "min": float(zone_values.min()),
                "max": float(zone_values.max()),
                "std": float(zone_values.std()),
                "sum": float(zone_values.sum()),
            }
        return stats


class GeoreferenceManager:
    """QGIS-like georeferencing support"""
    
    def __init__(self):
        """Initialize georeferencing"""
        self.crs: Optional[str] = None
        self.extent: Optional[Tuple[float, float, float, float]] = None
        self.geotransform: Optional[Tuple[float, ...]] = None
        self.resolution: Optional[Tuple[float, float]] = None
    
    def set_crs(self, epsg_code: int) -> None:
        """Set coordinate reference system"""
        self.crs = f"EPSG:{epsg_code}"
        logger.info(f"CRS set to {self.crs}")
    
    def set_extent(
        self,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float
    ) -> None:
        """Set spatial extent"""
        self.extent = (xmin, ymin, xmax, ymax)
        logger.info(f"Extent set: {self.extent}")
    
    def set_geotransform(self, transform: Tuple[float, ...]) -> None:
        """Set geotransform parameters"""
        self.geotransform = transform


class AnnotationManager:
    """QGIS-like annotation and labeling"""
    
    def __init__(self):
        """Initialize annotation manager"""
        self.annotations: List[Dict[str, Any]] = []
    
    def add_text_annotation(
        self,
        x: float,
        y: float,
        text: str,
        font_size: int = 12,
        color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        """Add text annotation"""
        self.annotations.append({
            "type": "text",
            "x": x,
            "y": y,
            "text": text,
            "font_size": font_size,
            "color": color,
        })
    
    def add_arrow_annotation(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        """Add arrow annotation"""
        self.annotations.append({
            "type": "arrow",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "color": color,
        })
    
    def add_scale_bar(
        self,
        x: float,
        y: float,
        length_km: float
    ) -> None:
        """Add scale bar"""
        self.annotations.append({
            "type": "scale_bar",
            "x": x,
            "y": y,
            "length_km": length_km,
        })


class ModernGLTerrainRenderer:
    """
    Modern OpenGL-based terrain renderer using moderngl library
    Provides efficient GPU-accelerated rendering with shader support
    """
    
    def __init__(self, width: int = 1024, height: int = 768):
        """
        Initialize the renderer
        
        Args:
            width: Render target width
            height: Render target height
        """
        if not MODERNGL_AVAILABLE:
            logger.warning("ModernGL not available, falling back to software rendering")
            self.available = False
            return
        
        self.width = width
        self.height = height
        self.available = True
        self.ctx = None
        self.vao = None
        self.program = None
        self.texture = None
        
        # QGIS-like features
        self.layer_manager = QGISLayerManager()
        self.color_ramp_manager = ColorRampManager()
        self.classification_engine = ClassificationEngine()
        self.raster_processor = RasterProcessor()
        self.georef_manager = GeoreferenceManager()
        self.annotation_manager = AnnotationManager()
        
        logger.info(f"ModernGL Terrain Renderer initialized ({width}x{height}) with QGIS features")
    
    def create_terrain_mesh_moderngl(
        self,
        dem: np.ndarray,
        colormap: str = "viridis"
    ) -> dict:
        """
        Create a terrain mesh using moderngl
        
        Args:
            dem: 2D elevation array
            colormap: Color mapping for visualization
        
        Returns:
            Dictionary with mesh data and GPU handles
        """
        if not self.available or self.ctx is None:
            logger.warning("ModernGL context not available")
            return {}
        
        height, width = dem.shape
        
        # Create vertex positions
        x = np.linspace(0, width - 1, width)
        z = np.linspace(0, height - 1, height)
        xx, zz = np.meshgrid(x, z)
        yy = dem.copy()
        
        # Flatten vertices
        vertices = np.column_stack([
            xx.ravel().astype('f4'),
            yy.ravel().astype('f4'),
            zz.ravel().astype('f4')
        ])
        
        # Create indices for triangulation
        indices = []
        for i in range(height - 1):
            for j in range(width - 1):
                v0 = i * width + j
                v1 = i * width + (j + 1)
                v2 = (i + 1) * width + j
                v3 = (i + 1) * width + (j + 1)
                
                indices.extend([v0, v1, v2, v1, v3, v2])
        
        indices = np.array(indices, dtype='u4')
        
        # Create colors from elevation
        colors = self._create_colors_from_elevation(dem, colormap)
        
        # Upload to GPU
        vbo = self.ctx.buffer(vertices.tobytes())
        ebo = self.ctx.buffer(indices.tobytes())
        color_vbo = self.ctx.buffer(colors.tobytes())
        
        logger.info(f"Created terrain mesh with {len(vertices)} vertices")
        
        return {
            'vbo': vbo,
            'ebo': ebo,
            'color_vbo': color_vbo,
            'vertex_count': len(indices),
            'vertices': vertices,
            'indices': indices,
            'dem': dem.copy()
        }
    
    def _create_colors_from_elevation(
        self,
        dem: np.ndarray,
        colormap: str = "viridis"
    ) -> np.ndarray:
        """Create RGB colors from elevation data"""
        try:
            import matplotlib.pyplot as plt  # type: ignore
            import matplotlib.cm as cm  # type: ignore
            
            cmap = cm.get_cmap(colormap)
            dem_min, dem_max = dem.min(), dem.max()
            dem_norm = (dem - dem_min) / (dem_max - dem_min + 1e-6)
            
            rgba = cmap(dem_norm)
            rgb = rgba[:, :, :3]  # type: ignore
            
            return np.column_stack([
                rgb[:, :, 0].ravel().astype('f4'),
                rgb[:, :, 1].ravel().astype('f4'),
                rgb[:, :, 2].ravel().astype('f4'),
                np.ones(rgb.shape[0] * rgb.shape[1], dtype='f4')
            ])
        except ImportError:
            # Fallback coloring
            dem_min, dem_max = dem.min(), dem.max()
            normalized = (dem - dem_min) / (dem_max - dem_min + 1e-6)
            
            colors = np.zeros((dem.shape[0] * dem.shape[1], 4), dtype='f4')
            colors[:, 0] = 0.267 + 0.4 * normalized.ravel()  # R
            colors[:, 1] = 0.004 + 0.9 * (1 - np.abs(2 * normalized.ravel() - 1))  # G
            colors[:, 2] = 0.329 + 0.5 * (1 - normalized.ravel())  # B
            colors[:, 3] = 1.0
            
            return np.clip(colors, 0, 1).astype('f4')
    
    def create_erosion_heatmap(
        self,
        erosion_data: np.ndarray
    ) -> dict:
        """
        Create erosion heatmap for visualization
        
        Args:
            erosion_data: 2D erosion rate array
        
        Returns:
            Dictionary with heatmap visualization data
        """
        # Normalize erosion data
        erosion_min = erosion_data.min()
        erosion_max = erosion_data.max()
        erosion_norm = (erosion_data - erosion_min) / (erosion_max - erosion_min + 1e-6)
        
        # Create "hot" colormap colors
        colors = np.zeros((*erosion_data.shape, 3), dtype='f4')
        
        # Red: 0 -> 1 as erosion increases
        colors[:, :, 0] = erosion_norm
        
        # Green: peaks in middle
        green_curve = 1 - 2 * np.abs(erosion_norm - 0.5)
        colors[:, :, 1] = np.maximum(0, green_curve)
        
        # Blue: opposite of red
        colors[:, :, 2] = 1 - erosion_norm
        
        return {
            'heatmap': colors,
            'min_value': erosion_min,
            'max_value': erosion_max,
            'normalized': erosion_norm
        }
    
    def save_terrain_snapshot(
        self,
        terrain_mesh: dict,
        filename: str,
        width: int = 800,
        height: int = 600
    ):
        """
        Save a snapshot of the terrain to an image file
        
        Args:
            terrain_mesh: Terrain mesh data
            filename: Output filename
            width: Image width
            height: Image height
        """
        try:
            from PIL import Image as PILImage
            import matplotlib.pyplot as plt  # type: ignore
            
            # Create visualization
            dem = terrain_mesh.get('dem')
            if dem is None:
                logger.warning("No DEM data in mesh")
                return
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 3D surface
            from mpl_toolkits.mplot3d import Axes3D  # type: ignore
            ax1 = fig.add_subplot(121, projection='3d')
            h, w = dem.shape
            x = np.arange(w)
            y = np.arange(h)
            X, Y = np.meshgrid(x, y)
            
            surf = ax1.plot_surface(X, Y, dem, cmap='terrain', alpha=0.8)
            ax1.set_title('3D Terrain')
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            ax1.set_zlabel('Elevation')
            
            # 2D heatmap
            ax2 = fig.add_subplot(122)
            im = ax2.imshow(dem, cmap='viridis', origin='upper')
            ax2.set_title('Elevation Map')
            plt.colorbar(im, ax=ax2, label='Elevation (m)')
            
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Terrain snapshot saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    # ============= QGIS-LIKE METHODS =============
    
    def apply_categorized_symbology(
        self,
        dem: np.ndarray,
        categories: Dict[str, Tuple[float, float]]
    ) -> np.ndarray:
        """Apply categorized symbology (QGIS)"""
        result = np.zeros_like(dem)
        for cat_id, (min_val, max_val) in enumerate(categories.values()):
            mask = (dem >= min_val) & (dem <= max_val)  # type: ignore
            result[mask] = cat_id
        return result
    
    def apply_graduated_symbology(
        self,
        dem: np.ndarray,
        classification_method: ClassificationMethod,
        num_classes: int = 5
    ) -> Tuple[np.ndarray, List[float]]:
        """Apply graduated symbology with classification"""
        if classification_method == ClassificationMethod.EQUAL_INTERVAL:
            breaks, _ = self.classification_engine.classify_equal_interval(dem, num_classes)
        elif classification_method == ClassificationMethod.QUANTILE:
            breaks, _ = self.classification_engine.classify_quantile(dem, num_classes)
        elif classification_method == ClassificationMethod.NATURAL_BREAKS:
            breaks, _ = self.classification_engine.classify_natural_breaks(dem, num_classes)
        elif classification_method == ClassificationMethod.STANDARD_DEVIATION:
            breaks, _ = self.classification_engine.classify_std_deviation(dem, num_classes)
        else:
            breaks, _ = self.classification_engine.classify_equal_interval(dem, num_classes)
        
        # Create classified raster
        classified = np.digitize(dem, breaks) - 1
        return classified, breaks
    
    def apply_blend_mode(
        self,
        base: np.ndarray,
        overlay: np.ndarray,
        blend_mode: BlendMode,
        opacity: float = 1.0
    ) -> np.ndarray:
        """Apply blend mode to rasters (QGIS blend modes)"""
        # Normalize to 0-1 range
        base_norm = (base - base.min()) / (base.max() - base.min() + 1e-6)
        overlay_norm = (overlay - overlay.min()) / (overlay.max() - overlay.min() + 1e-6)
        
        if blend_mode == BlendMode.MULTIPLY:
            result = base_norm * overlay_norm
        elif blend_mode == BlendMode.SCREEN:
            result = 1 - (1 - base_norm) * (1 - overlay_norm)
        elif blend_mode == BlendMode.OVERLAY:
            result = np.where(base_norm < 0.5,
                            2 * base_norm * overlay_norm,
                            1 - 2 * (1 - base_norm) * (1 - overlay_norm))
        elif blend_mode == BlendMode.SOFT_LIGHT:
            result = np.where(overlay_norm < 0.5,
                            base_norm - (1 - 2 * overlay_norm) * base_norm * (1 - base_norm),
                            base_norm + (2 * overlay_norm - 1) * (np.sqrt(base_norm) - base_norm))
        elif blend_mode == BlendMode.DARKEN:
            result = np.minimum(base_norm, overlay_norm)
        elif blend_mode == BlendMode.LIGHTEN:
            result = np.maximum(base_norm, overlay_norm)
        elif blend_mode == BlendMode.DIFFERENCE:
            result = np.abs(base_norm - overlay_norm)
        else:
            result = base_norm * (1 - opacity) + overlay_norm * opacity
        
        return result * (base.max() - base.min()) + base.min()
    
    def create_custom_colormap(
        self,
        dem: np.ndarray,
        color_ramp: ColorRamp,
        custom_style: Optional[LayerStyle] = None
    ) -> np.ndarray:
        """Create custom colormap with QGIS-like color ramps"""
        dem_min = dem.min()
        dem_max = dem.max()
        dem_norm = (dem - dem_min) / (dem_max - dem_min + 1e-6)
        
        colors = np.zeros((*dem.shape, 3), dtype='f4')
        for i in range(dem.shape[0]):
            for j in range(dem.shape[1]):
                value = dem_norm[i, j]
                rgb = ColorRampManager.interpolate_ramp(color_ramp, value)
                colors[i, j] = [c / 255.0 for c in rgb]
        
        return colors
    
    def add_layer_with_style(
        self,
        name: str,
        data: np.ndarray,
        style: LayerStyle
    ) -> None:
        """Add a layer with QGIS-like styling"""
        self.layer_manager.add_layer(name, data)
        self.layer_manager.set_layer_style(name, style)
        logger.info(f"Added styled layer: {name}")
    
    def export_styled_layer(
        self,
        layer_name: str,
        filename: str
    ) -> None:
        """Export layer with styling applied"""
        if layer_name not in self.layer_manager.layers:
            logger.warning(f"Layer not found: {layer_name}")
            return
        
        data = self.layer_manager.layers[layer_name]["data"]
        style = self.layer_manager.layer_styles[layer_name]
        
        try:
            import matplotlib.pyplot as plt  # type: ignore
            fig, ax = plt.subplots(figsize=(10, 8))
            
            im = ax.imshow(data, cmap=style.colormap, alpha=style.opacity)
            ax.set_title(f"{layer_name} (Opacity: {style.opacity})")
            plt.colorbar(im, ax=ax)
            
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Exported styled layer to {filename}")
        except Exception as e:
            logger.error(f"Export error: {e}")
    
    def compose_layers(self) -> np.ndarray:
        """Compose multiple layers with their styles and blend modes"""
        result = None
        
        for layer_name in self.layer_manager.layer_order:
            if not self.layer_manager.layers[layer_name].get("visible", True):
                continue
            
            layer_data = self.layer_manager.layers[layer_name]["data"]
            style = self.layer_manager.layer_styles[layer_name]
            
            if result is None:
                result = layer_data.copy()
            else:
                result = self.apply_blend_mode(
                    result,
                    layer_data,
                    style.blend_mode,
                    style.opacity
                )
        
        return result if result is not None else np.zeros((1, 1))


class TerrainVisualizationHelper:
    """
    Helper class for terrain visualization operations
    Bridges between simulation data and OpenGL rendering
    """
    
    @staticmethod
    def create_hillshade(dem: np.ndarray, azimuth: float = 315, altitude: float = 45) -> np.ndarray:
        """
        Create hillshade visualization from DEM
        
        Args:
            dem: Digital Elevation Model
            azimuth: Light direction azimuth (degrees)
            altitude: Light altitude angle (degrees)
        
        Returns:
            Hillshade array suitable for overlay
        """
        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)
        
        # Calculate gradients
        x, y = np.gradient(dem)
        
        # Calculate angles
        aspect = np.arctan2(-x, y)
        slope = np.pi / 2 - np.arctan(np.sqrt(x * x + y * y))
        
        # Calculate shading
        shading = np.sin(altitude_rad) * np.cos(slope) + \
                  np.cos(altitude_rad) * np.sin(slope) * \
                  np.cos(azimuth_rad - np.pi / 2 - aspect)
        
        # Normalize to [0, 1]
        shading = (shading + 1) / 2
        return np.clip(shading, 0, 1).astype(np.float32)
    
    @staticmethod
    def create_slope_visualization(dem: np.ndarray) -> np.ndarray:
        """
        Create slope visualization
        
        Args:
            dem: Digital Elevation Model
        
        Returns:
            Slope array as percentage
        """
        x, y = np.gradient(dem)
        slope_angle = np.arctan(np.sqrt(x**2 + y**2))
        slope_percent = np.tan(slope_angle) * 100
        return np.clip(slope_percent, 0, 100).astype(np.float32)
    
    @staticmethod
    def blend_visualizations(
        base: np.ndarray,
        overlay: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Blend two visualization arrays
        
        Args:
            base: Base visualization
            overlay: Overlay visualization
            alpha: Blend factor (0-1)
        
        Returns:
            Blended result
        """
        return (1 - alpha) * base + alpha * overlay
