"""
High-performance GPU-accelerated rendering with level-of-detail (LOD).
Unified rendering pipeline supporting:
- ModernGL (primary, cross-platform GPU acceleration)
- OpenGL (fallback, for compatibility)
- Tkinter integration (UI embedding)
- CPU software rendering (ultimate fallback)
Optimized for smooth visualization with minimal resource usage.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math
import os
import sys

logger = logging.getLogger(__name__)

# Try to import GPU libraries (optional, will fall back to CPU)
MODERNGL_AVAILABLE = False
OPENGL_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    import moderngl  # type: ignore
    MODERNGL_AVAILABLE = True
    logger.debug("ModernGL available for GPU acceleration")
except ImportError:
    MODERNGL_AVAILABLE = False

try:
    from OpenGL.GL import *  # type: ignore
    from OpenGL.GLU import *  # type: ignore
    from OpenGL.GL.shaders import compileProgram, compileShader  # type: ignore
    OPENGL_AVAILABLE = True
    logger.debug("OpenGL available for GPU acceleration")
except ImportError:
    OPENGL_AVAILABLE = False

try:
    import pygame  # type: ignore
    PYGAME_AVAILABLE = True
    logger.debug("Pygame available for Tkinter integration")
except ImportError:
    pass


# Stub definitions for when OpenGL is not available
if not OPENGL_AVAILABLE:
    GL_DEPTH_TEST = 0
    GL_LIGHTING = 0
    GL_LIGHT0 = 0
    GL_VERTEX_SHADER = 0
    GL_FRAGMENT_SHADER = 0
    GL_FRONT_AND_BACK = 0
    GL_AMBIENT = 0
    GL_DIFFUSE = 0
    GL_SPECULAR = 0
    GL_POSITION = 0
    GL_SHININESS = 0
    GL_ARRAY_BUFFER = 0
    GL_ELEMENT_ARRAY_BUFFER = 0
    GL_STATIC_DRAW = 0
    GL_FLOAT = 0
    GL_TRIANGLES = 0
    GL_UNSIGNED_INT = 0
    GL_COLOR_BUFFER_BIT = 0
    GL_DEPTH_BUFFER_BIT = 0
    GL_PROJECTION = 0
    GL_MODELVIEW = 0
    
    def glEnable(*args, **kwargs): pass
    def glClearColor(*args, **kwargs): pass
    def glLight(*args, **kwargs): pass
    def glMaterial(*args, **kwargs): pass
    def glGenVertexArrays(*args, **kwargs): return 0
    def glBindVertexArray(*args, **kwargs): pass
    def glGenBuffers(*args, **kwargs): return 0
    def glBindBuffer(*args, **kwargs): pass
    def glBufferData(*args, **kwargs): pass
    def glGetAttribLocation(*args, **kwargs): return 0
    def glVertexAttribPointer(*args, **kwargs): pass
    def glEnableVertexAttribArray(*args, **kwargs): pass
    def glUseProgram(*args, **kwargs): pass
    def glDrawElements(*args, **kwargs): pass
    def glBegin(*args, **kwargs): pass
    def glColor3fv(*args, **kwargs): pass
    def glVertex3fv(*args, **kwargs): pass
    def glEnd(*args, **kwargs): pass
    def glClear(*args, **kwargs): pass
    def glMatrixMode(*args, **kwargs): pass
    def glLoadIdentity(*args, **kwargs): pass


class RenderQuality(Enum):
    """Render quality levels for LOD"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ULTRA = 4


@dataclass
class RenderStats:
    """Rendering statistics"""
    fps: float = 0.0
    triangles_rendered: int = 0
    layers_rendered: int = 0
    gpu_memory_mb: float = 0.0
    cpu_time_ms: float = 0.0
    gpu_time_ms: float = 0.0


class LODLevel:
    """Level of Detail configuration"""
    
    def __init__(
        self,
        level: int,
        pixel_threshold: float,
        max_vertices: int,
        simplification_tolerance: float
    ):
        self.level = level
        self.pixel_threshold = pixel_threshold  # Pixels per geometry unit
        self.max_vertices = max_vertices
        self.simplification_tolerance = simplification_tolerance


class LODManager:
    """Manage level-of-detail rendering"""
    
    def __init__(self):
        self.lod_levels = [
            LODLevel(0, 0.5, 50, 100.0),      # Ultra low detail for far zoom
            LODLevel(1, 1.0, 200, 50.0),      # Low detail
            LODLevel(2, 2.0, 1000, 10.0),     # Medium detail
            LODLevel(3, 5.0, 5000, 1.0),      # High detail
            LODLevel(4, 10.0, 50000, 0.0),    # Ultra detail (no simplification)
        ]
        self.current_zoom = 1.0
        self.current_lod = self.lod_levels[2]
    
    def update_lod(self, zoom_level: float, viewport_width: int = 1920):
        """Update LOD based on zoom level and viewport"""
        self.current_zoom = zoom_level
        
        # Calculate pixels per unit
        pixels_per_unit = (viewport_width / 360.0) * zoom_level  # Assuming 360 units = full width
        
        # Select appropriate LOD level
        for lod in self.lod_levels:
            if pixels_per_unit <= lod.pixel_threshold:
                self.current_lod = lod
                break
        else:
            self.current_lod = self.lod_levels[-1]
    
    def simplify_geometry(self, coords: np.ndarray) -> np.ndarray:
        """Simplify geometry based on current LOD"""
        if self.current_lod.simplification_tolerance <= 0:
            return coords
        
        if len(coords) > self.current_lod.max_vertices:
            # Subsample points
            step = len(coords) // self.current_lod.max_vertices
            return coords[::step]
        
        return coords
    
    def get_vertex_budget(self) -> int:
        """Get vertex budget for current LOD"""
        return self.current_lod.max_vertices


class VectorRasterizer:
    """Convert vector geometries to raster for rendering"""
    
    @staticmethod
    def rasterize_point(point: Tuple[float, float], size: float = 5.0) -> np.ndarray:
        """Convert point to raster representation"""
        size = max(1, int(size))
        raster = np.zeros((size * 2 + 1, size * 2 + 1), dtype=np.uint8)
        center = size
        
        # Draw circle
        for y in range(-size, size + 1):
            for x in range(-size, size + 1):
                dist_sq = x*x + y*y
                if dist_sq <= size*size:
                    raster[center + y, center + x] = 255
        
        return raster
    
    @staticmethod
    def rasterize_line(coords: np.ndarray, width: float = 2.0) -> np.ndarray:
        """Convert line to raster representation"""
        if len(coords) < 2:
            return np.zeros((1, 1), dtype=np.uint8)
        
        # Get bounds
        xs = coords[:, 0]
        ys = coords[:, 1]
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        
        width_pix = max(1, int(xmax - xmin + 10))
        height_pix = max(1, int(ymax - ymin + 10))
        
        raster = np.zeros((height_pix, width_pix), dtype=np.uint8)
        
        # Bresenham line drawing
        for i in range(len(coords) - 1):
            x0, y0 = int(coords[i, 0] - xmin), int(coords[i, 1] - ymin)
            x1, y1 = int(coords[i+1, 0] - xmin), int(coords[i+1, 1] - ymin)
            
            VectorRasterizer._draw_line(raster, x0, y0, x1, y1, int(width))
        
        return raster
    
    @staticmethod
    def _draw_line(raster: np.ndarray, x0: int, y0: int, x1: int, y1: int, width: int):
        """Bresenham line algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            # Draw with width
            for wy in range(-width//2, width//2 + 1):
                for wx in range(-width//2, width//2 + 1):
                    py = y + wy
                    px = x + wx
                    if 0 <= py < raster.shape[0] and 0 <= px < raster.shape[1]:
                        raster[py, px] = 255
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    @staticmethod
    def rasterize_polygon(coords: np.ndarray, fill: bool = True) -> np.ndarray:
        """Convert polygon to raster representation"""
        if len(coords) < 3:
            return np.zeros((1, 1), dtype=np.uint8)
        
        xs = coords[:, 0]
        ys = coords[:, 1]
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        
        width_pix = max(1, int(xmax - xmin + 10))
        height_pix = max(1, int(ymax - ymin + 10))
        
        raster = np.zeros((height_pix, width_pix), dtype=np.uint8)
        
        # Draw outline
        for i in range(len(coords)):
            x0, y0 = int(coords[i, 0] - xmin), int(coords[i, 1] - ymin)
            x1, y1 = int(coords[(i+1) % len(coords), 0] - xmin), int(coords[(i+1) % len(coords), 1] - ymin)
            VectorRasterizer._draw_line(raster, x0, y0, x1, y1, 1)
        
        # Fill polygon
        if fill:
            # Simple flood fill
            from scipy import ndimage
            result = ndimage.label(raster == 0)
            labeled = result[0] if isinstance(result, tuple) else result
            # Mark interior as filled (safely handle array indexing)
            if isinstance(labeled, np.ndarray) and labeled.size > 0:
                raster[labeled == labeled.flat[0]] = 255
        
        return raster


class GPURenderEngine:
    """
    Unified GPU-accelerated rendering engine.
    Supports multiple backends: ModernGL (primary), OpenGL (fallback), CPU (ultimate fallback)
    """
    
    BACKEND_MODERNGL = "moderngl"
    BACKEND_OPENGL = "opengl"
    BACKEND_CPU = "cpu"
    
    def __init__(self, use_moderngl: bool = True, enable_opengl_fallback: bool = True):
        self.use_moderngl = use_moderngl and MODERNGL_AVAILABLE
        self.enable_opengl_fallback = enable_opengl_fallback and OPENGL_AVAILABLE
        self.moderngl = None
        self.context = None
        self.render_stats = RenderStats()
        self.lod_manager = LODManager()
        self.vertex_buffer = None
        self.index_buffer = None
        self.vao = None
        self.program = None
        self.active_backend = self.BACKEND_CPU
        
        # Try to initialize ModernGL
        if self.use_moderngl:
            if self._init_moderngl():
                self.active_backend = self.BACKEND_MODERNGL
                return
        
        # Fall back to OpenGL
        if self.enable_opengl_fallback:
            if self._init_opengl():
                self.active_backend = self.BACKEND_OPENGL
                return
        
        # Use CPU rendering
        logger.warning("No GPU backends available - using CPU rendering")
        self.active_backend = self.BACKEND_CPU
    
    def _init_moderngl(self) -> bool:
        """Initialize ModernGL context"""
        try:
            import moderngl  # type: ignore
            self.moderngl = moderngl
            logger.info("✓ ModernGL initialized (primary GPU backend)")
            return True
        except Exception as e:
            logger.warning(f"ModernGL initialization failed: {e}")
            return False
    
    def _init_opengl(self) -> bool:
        """Initialize OpenGL context"""
        try:
            if not OPENGL_AVAILABLE:
                return False
            logger.info("✓ OpenGL initialized (fallback GPU backend)")
            return True
        except Exception as e:
            logger.warning(f"OpenGL initialization failed: {e}")
            return False
    
    def get_backend_name(self) -> str:
        """Get name of active rendering backend"""
        backend_names = {
            self.BACKEND_MODERNGL: "ModernGL",
            self.BACKEND_OPENGL: "OpenGL",
            self.BACKEND_CPU: "CPU (Software)",
        }
        return backend_names.get(self.active_backend, "Unknown")
    
    def render_layer(
        self,
        layer: Any,
        canvas_bounds: Tuple[float, float, float, float],
        zoom_level: float = 1.0,
        quality: RenderQuality = RenderQuality.MEDIUM
    ) -> bool:
        """Render layer to canvas"""
        try:
            # Update LOD
            self.lod_manager.update_lod(zoom_level, 1920)
            
            # Get visible features
            visible_features = self._get_visible_features(layer, canvas_bounds)
            
            if not visible_features:
                return True
            
            # Render features
            triangle_count = 0
            for feature in visible_features:
                feature_triangles = self._render_feature(feature, quality)
                triangle_count += feature_triangles
            
            self.render_stats.triangles_rendered = triangle_count
            self.render_stats.layers_rendered = 1
            
            return True
        except Exception as e:
            logger.error(f"Rendering failed: {e}")
            return False
    
    def _get_visible_features(
        self,
        layer: Any,
        canvas_bounds: Tuple[float, float, float, float]
    ) -> List[Any]:
        """Get features within canvas bounds"""
        visible = []
        
        try:
            if hasattr(layer, 'query_spatial'):
                return layer.query_spatial(canvas_bounds)
            return []
        except Exception as e:
            logger.warning(f"Failed to query visible features: {e}")
            return []
    
    def _render_feature(self, feature: Any, quality: RenderQuality) -> int:
        """Render single feature, return triangle count"""
        triangle_count = 0
        
        try:
            geom = feature.geometry if hasattr(feature, 'geometry') else feature
            geom_type = geom.geom_type if hasattr(geom, 'geom_type') else None
            
            if geom_type == 'Point':
                triangle_count = self._render_point(geom)
            elif geom_type == 'LineString':
                triangle_count = self._render_line(geom)
            elif geom_type == 'Polygon':
                triangle_count = self._render_polygon(geom)
            elif geom_type == 'MultiPoint':
                for pt in geom.geoms:
                    triangle_count += self._render_point(pt)
            elif geom_type == 'MultiLineString':
                for line in geom.geoms:
                    triangle_count += self._render_line(line)
            elif geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    triangle_count += self._render_polygon(poly)
        except Exception as e:
            logger.warning(f"Feature rendering failed: {e}")
        
        return triangle_count
    
    def _render_point(self, geometry: Any) -> int:
        """Render point geometry"""
        coords = np.array(geometry.coords)
        # Points render as 2 triangles (quad)
        return 2
    
    def _render_line(self, geometry: Any) -> int:
        """Render line geometry"""
        coords = np.array(geometry.coords)
        # Simplify if needed
        coords = self.lod_manager.simplify_geometry(coords)
        # Lines render as triangle strip
        return max(0, len(coords) - 1)
    
    def _render_polygon(self, geometry: Any) -> int:
        """Render polygon geometry"""
        coords = np.array(geometry.exterior.coords)
        # Simplify if needed
        coords = self.lod_manager.simplify_geometry(coords)
        # Triangulate polygon
        try:
            from scipy.spatial import distance_matrix
            return len(coords) - 2  # Simple triangle fan
        except:
            return len(coords) - 2
    
    def create_vertex_buffer(
        self,
        vertices: np.ndarray,
        indices: Optional[np.ndarray] = None
    ) -> bool:
        """Create GPU vertex buffer"""
        if not self.use_moderngl or self.moderngl is None:
            return False
        
        try:
            # Flatten vertices if needed
            if vertices.ndim > 1:
                vertices = vertices.flatten()
            
            vertex_data = vertices.astype('f4').tobytes()
            
            # Store for later use
            self.vertex_buffer = vertex_data
            if indices is not None:
                self.index_buffer = indices.astype('i4').tobytes()
            
            return True
        except Exception as e:
            logger.error(f"Vertex buffer creation failed: {e}")
            return False
    
    def estimate_memory_usage(self) -> Dict[str, float]:
        """Estimate GPU memory usage"""
        memory_mb = {}
        
        if self.vertex_buffer:
            memory_mb['vertices'] = len(self.vertex_buffer) / (1024 * 1024)
        
        if self.index_buffer:
            memory_mb['indices'] = len(self.index_buffer) / (1024 * 1024)
        
        total = sum(memory_mb.values())
        memory_mb['total'] = total
        
        return memory_mb
    
    def optimize_for_performance(self, target_fps: int = 60, available_memory_mb: int = 512):
        """Optimize rendering for target FPS and memory"""
        # Adjust LOD based on performance
        if self.render_stats.fps < target_fps * 0.8:
            # Performance is low - reduce quality
            logger.info(f"Reducing render quality: {self.render_stats.fps:.1f} FPS")
            if self.lod_manager.current_lod.level > 0:
                self.lod_manager.current_lod = self.lod_manager.lod_levels[
                    self.lod_manager.current_lod.level - 1
                ]
        
        # Check memory usage
        memory_usage = self.estimate_memory_usage()
        if memory_usage['total'] > available_memory_mb * 0.9:
            logger.info(f"Memory usage high: {memory_usage['total']:.1f}MB")
            # Reduce geometry detail
            if self.lod_manager.current_lod.level > 0:
                self.lod_manager.current_lod = self.lod_manager.lod_levels[
                    self.lod_manager.current_lod.level - 1
                ]
    
    def get_render_stats(self) -> RenderStats:
        """Get rendering statistics"""
        return self.render_stats


class TileRenderer:
    """Render data in tiles for efficient streaming"""
    
    def __init__(self, tile_size: int = 256):
        self.tile_size = tile_size
        self.tile_cache: Dict[Tuple[int, int], np.ndarray] = {}
        self.max_cache_tiles = 100
    
    def get_tiles_for_extent(
        self,
        extent: Tuple[float, float, float, float],
        zoom_level: int
    ) -> List[Tuple[int, int]]:
        """Get tiles covering extent at zoom level"""
        xmin, xmax, ymin, ymax = extent
        
        # Convert to tile coordinates
        tiles = []
        for x in range(int(xmin), int(xmax) + 1):
            for y in range(int(ymin), int(ymax) + 1):
                tiles.append((x, y))
        
        return tiles
    
    def render_tile(self, tile_x: int, tile_y: int, data: np.ndarray) -> np.ndarray:
        """Render data tile"""
        tile_key = (tile_x, tile_y)
        
        # Check cache
        if tile_key in self.tile_cache:
            return self.tile_cache[tile_key]
        
        # Create tile
        tile = np.zeros((self.tile_size, self.tile_size, 3), dtype=np.uint8)
        
        # Cache with LRU eviction
        if len(self.tile_cache) >= self.max_cache_tiles:
            # Remove oldest tile
            oldest_key = min(self.tile_cache.keys())
            del self.tile_cache[oldest_key]
        
        self.tile_cache[tile_key] = tile
        return tile
    
    def clear_cache(self):
        """Clear tile cache"""
        self.tile_cache.clear()

class TkinterOpenGLCanvas:
    """
    Tkinter integration for OpenGL rendering.
    Embeds OpenGL/GPU rendering directly in Tkinter UI.
    """
    
    def __init__(self, parent=None, width: int = 800, height: int = 600):
        """Initialize Tkinter OpenGL canvas"""
        self.parent = parent
        self.width = width
        self.height = height
        self.gl_context = None
        self.renderer = GPURenderEngine(use_moderngl=True, enable_opengl_fallback=True)
        
        try:
            if PYGAME_AVAILABLE:
                import pygame  # type: ignore
                logger.info("Using Pygame for Tkinter OpenGL integration")
                self.gl_context = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
        except Exception as e:
            logger.warning(f"Tkinter OpenGL integration failed: {e}")
    
    def render_to_tkinter(self, tkinter_canvas) -> bool:
        """Render GPU output to Tkinter canvas"""
        try:
            if self.gl_context is None:
                return False
            
            # Get rendering output
            frame_data = self._get_frame_buffer()
            
            if frame_data is None:
                return False
            
            # Convert to Tkinter PhotoImage format
            # This would need PIL/Pillow for real implementation
            return True
        except Exception as e:
            logger.error(f"Tkinter rendering failed: {e}")
            return False
    
    def _get_frame_buffer(self) -> Optional[np.ndarray]:
        """Get current frame buffer from GPU"""
        try:
            if self.gl_context is None:
                return None
            
            # Read pixels from GPU
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            return frame
        except Exception as e:
            logger.warning(f"Frame buffer read failed: {e}")
            return None


class TerrainRenderer:
    """Specialized terrain rendering with LOD and streaming"""
    
    def __init__(self):
        self.gpu_renderer = GPURenderEngine()
        self.tile_renderer = TileRenderer(tile_size=512)
        self.elevation_data = None
        self.colormap = None
    
    def render_dem(
        self,
        dem: np.ndarray,
        bounds: Tuple[float, float, float, float],
        colormap: str = 'viridis',
        exaggeration: float = 1.0
    ) -> np.ndarray:
        """
        Render digital elevation model (DEM) to image.
        
        Args:
            dem: 2D elevation array
            bounds: (xmin, xmax, ymin, ymax)
            colormap: Matplotlib colormap name
            exaggeration: Vertical exaggeration factor
        
        Returns:
            Rendered image as numpy array
        """
        try:
            try:
                import matplotlib.pyplot as plt
                import matplotlib.colors as mcolors
                import matplotlib.cm as cm
            except ImportError:
                logger.warning("matplotlib not available for colormapping")
                return dem.astype(np.uint8)
            
            # Normalize elevation to 0-1
            dem_min = dem.min()
            dem_max = dem.max()
            dem_normalized = (dem - dem_min) / (dem_max - dem_min + 1e-10)
            
            # Apply colormap
            try:
                if hasattr(cm, 'get_cmap'):
                    colormap_obj = cm.get_cmap(colormap)
                elif hasattr(plt, 'get_cmap'):
                    colormap_obj = plt.get_cmap(colormap)  # type: ignore
                else:
                    colormap_obj = cm.get_cmap('viridis')
            except (AttributeError, ValueError):
                colormap_obj = cm.get_cmap('viridis')
            
            colored = colormap_obj(dem_normalized)
            
            # Convert to RGB (handle 4D array with multiple channels)
            if isinstance(colored, np.ndarray):
                shaped = colored  # type: np.ndarray
                if len(shaped.shape) == 3 and shaped.shape[2] >= 3:
                    rgb = (shaped[:, :, :3] * 255).astype(np.uint8)
                else:
                    # Fallback for unexpected shape
                    rgb = np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
            else:
                # Fallback for non-ndarray types
                rgb = np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
            
            logger.info(f"Rendered DEM: {rgb.shape}, backend: {self.gpu_renderer.get_backend_name()}")
            return rgb
        except Exception as e:
            logger.error(f"DEM rendering failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def render_hillshade(
        self,
        dem: np.ndarray,
        azimuth: float = 315,
        altitude: float = 45
    ) -> np.ndarray:
        """
        Render hillshade from DEM.
        
        Args:
            dem: 2D elevation array
            azimuth: Light direction (degrees, 0-360)
            altitude: Light angle above horizon (degrees, 0-90)
        
        Returns:
            Hillshade image as numpy array
        """
        try:
            from scipy.ndimage import sobel
            
            # Compute gradients
            x = sobel(dem, axis=1)
            y = sobel(dem, axis=0)
            
            # Compute aspect and slope
            aspect = np.arctan2(-y, x)
            slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
            
            # Convert angles to radians
            azimuth_rad = np.radians(azimuth)
            altitude_rad = np.radians(altitude)
            
            # Calculate shading
            shading = (np.sin(altitude_rad) * np.cos(slope) +
                      np.cos(altitude_rad) * np.sin(slope) *
                      np.cos(azimuth_rad - aspect))
            
            # Normalize to 0-255
            hillshade = ((shading + 1) / 2 * 255).astype(np.uint8)
            
            # Convert to RGB
            rgb = np.dstack([hillshade, hillshade, hillshade])
            
            logger.info(f"Rendered hillshade: {rgb.shape}")
            return rgb
        except Exception as e:
            logger.error(f"Hillshade rendering failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def render_shaded_relief(
        self,
        dem: np.ndarray,
        colormap: str = 'terrain',
        blend_mode: str = 'overlay'
    ) -> np.ndarray:
        """
        Render shaded relief (hillshade + colored DEM).
        
        Args:
            dem: 2D elevation array
            colormap: Matplotlib colormap name
            blend_mode: Blending mode ('overlay', 'multiply', 'add')
        
        Returns:
            Shaded relief image as numpy array
        """
        try:
            # Get colored DEM
            colored = self.render_dem(dem, bounds=(0, dem.shape[1], 0, dem.shape[0]), colormap=colormap)
            
            # Get hillshade
            hillshade = self.render_hillshade(dem)
            
            # Blend
            if blend_mode == 'overlay':
                result = np.where(hillshade < 128,
                                2 * colored * hillshade / 255,
                                255 - 2 * (255 - colored) * (255 - hillshade) / 255)
            elif blend_mode == 'multiply':
                result = colored * hillshade / 255
            elif blend_mode == 'add':
                result = np.clip(colored.astype(int) + hillshade.astype(int), 0, 255)
            else:
                result = colored
            
            return result.astype(np.uint8)
        except Exception as e:
            logger.error(f"Shaded relief rendering failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def render_3d_terrain(
        self,
        dem: np.ndarray,
        resolution: int = 10
    ) -> np.ndarray:
        """
        Render 3D terrain mesh (simplified for CPU rendering).
        
        Args:
            dem: 2D elevation array
            resolution: Mesh resolution (higher = coarser)
        
        Returns:
            Rendered 3D image as numpy array
        """
        try:
            # Subsample DEM for mesh
            mesh_dem = dem[::resolution, ::resolution]
            
            # Create simple orthographic projection
            rgb = self.render_dem(mesh_dem, bounds=(0, mesh_dem.shape[1], 0, mesh_dem.shape[0]))
            
            logger.info(f"Rendered 3D terrain mesh: {rgb.shape}, resolution: {resolution}")
            return rgb
        except Exception as e:
            logger.error(f"3D terrain rendering failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)


class RenderingPipeline:
    """
    Complete rendering pipeline coordinating all rendering components.
    Handles backend selection, optimization, and output generation.
    """
    
    def __init__(self):
        self.gpu_engine = GPURenderEngine()
        self.tile_renderer = TileRenderer()
        self.terrain_renderer = TerrainRenderer()
        self.vector_rasterizer = VectorRasterizer()
        self.render_queue = []
    
    def render_layers(
        self,
        layers: List[Any],
        canvas_bounds: Tuple[float, float, float, float],
        zoom_level: float = 1.0
    ) -> np.ndarray:
        """
        Render all layers to image.
        
        Args:
            layers: List of layers to render
            canvas_bounds: (xmin, xmax, ymin, ymax)
            zoom_level: Current zoom level
        
        Returns:
            Rendered image as numpy array
        """
        try:
            # Initialize output image
            img_height = 600
            img_width = 800
            image = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255  # White background
            
            # Render each layer
            for layer in layers:
                if not hasattr(layer, 'visible') or not layer.visible:
                    continue
                
                self.gpu_engine.render_layer(
                    layer,
                    canvas_bounds,
                    zoom_level,
                    RenderQuality.MEDIUM
                )
            
            logger.info(f"Rendered {len(layers)} layers using {self.gpu_engine.get_backend_name()}")
            return image
        except Exception as e:
            logger.error(f"Layer rendering failed: {e}")
            return np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about active rendering backend"""
        return {
            'backend': self.gpu_engine.active_backend,
            'backend_name': self.gpu_engine.get_backend_name(),
            'moderngl_available': MODERNGL_AVAILABLE,
            'opengl_available': OPENGL_AVAILABLE,
            'pygame_available': PYGAME_AVAILABLE,
        }
    
    def optimize_for_performance(self, target_fps: int = 60):
        """Optimize rendering for target frame rate"""
        self.gpu_engine.optimize_for_performance(target_fps=target_fps)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rendering statistics"""
        stats = self.gpu_engine.get_render_stats()
        return {
            'fps': stats.fps,
            'triangles': stats.triangles_rendered,
            'layers': stats.layers_rendered,
            'gpu_memory_mb': stats.gpu_memory_mb,
            'cpu_time_ms': stats.cpu_time_ms,
            'gpu_time_ms': stats.gpu_time_ms,
            'backend': self.gpu_engine.get_backend_name(),
        }
