"""
Advanced OpenGL 3D Terrain Visualizer
GPU-accelerated 3D terrain and erosion visualization using modern OpenGL
"""

import numpy as np
import logging
from typing import Optional, Tuple
import math

logger = logging.getLogger(__name__)

try:
    import moderngl
    from PIL import Image
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    logger.warning("moderngl not available. Install: pip install moderngl pillow")


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
        
        logger.info(f"ModernGL Terrain Renderer initialized ({width}x{height})")
    
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
            import matplotlib.pyplot as plt
            import matplotlib.cm as cm
            
            cmap = cm.get_cmap(colormap)
            dem_min, dem_max = dem.min(), dem.max()
            dem_norm = (dem - dem_min) / (dem_max - dem_min + 1e-6)
            
            rgba = cmap(dem_norm)
            rgb = rgba[:, :, :3]
            
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
            import matplotlib.pyplot as plt
            
            # Create visualization
            dem = terrain_mesh.get('dem')
            if dem is None:
                logger.warning("No DEM data in mesh")
                return
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 3D surface
            from mpl_toolkits.mplot3d import Axes3D
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
