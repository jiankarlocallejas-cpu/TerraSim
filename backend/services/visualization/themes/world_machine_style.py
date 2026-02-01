"""
World Machine-style terrain visualization.
Implements terrain coloring schemes, erosion visualization, and animation rendering.
Compatible with simulation outputs and procedural terrain generation.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import visualization libraries
PIL_AVAILABLE = False
SCIPY_AVAILABLE = False
MATPLOTLIB_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    pass

try:
    from scipy import ndimage, interpolate
    SCIPY_AVAILABLE = True
except ImportError:
    pass

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass


class WorldMachineColorScheme(Enum):
    """Color schemes compatible with World Machine output"""
    NATURAL = "natural"          # Realistic terrain colors
    EROSION_HEAT = "erosion_heat"  # Heat-based erosion visualization
    GEOLOGICAL = "geological"     # Geological strata colors
    THERMAL = "thermal"           # Thermal coloring
    HEIGHTMAP = "heightmap"       # Simple grayscale heightmap


@dataclass
class ErosionDepositionData:
    """Erosion and deposition visualization data"""
    erosion_amount: np.ndarray  # Negative for erosion
    deposition_amount: np.ndarray  # Positive for deposition
    sediment_flux: np.ndarray  # Sediment movement


class WorldMachineVisualizer:
    """Terrain visualization compatible with World Machine style outputs"""
    
    def __init__(self):
        self.color_schemes = {
            WorldMachineColorScheme.NATURAL: self._natural_colors,
            WorldMachineColorScheme.EROSION_HEAT: self._erosion_heat_colors,
            WorldMachineColorScheme.GEOLOGICAL: self._geological_colors,
            WorldMachineColorScheme.THERMAL: self._thermal_colors,
            WorldMachineColorScheme.HEIGHTMAP: self._heightmap_colors,
        }
    
    def create_world_machine_colors(
        self,
        dem: np.ndarray,
        colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL
    ) -> np.ndarray:
        """
        Create World Machine-style colored terrain.
        
        Args:
            dem: 2D elevation array
            colorscheme: Color scheme to use
        
        Returns:
            RGB image array
        """
        try:
            # Normalize elevation to 0-1
            dem_min = dem.min()
            dem_max = dem.max()
            dem_norm = (dem - dem_min) / (dem_max - dem_min + 1e-10)
            
            # Get color function
            color_func = self.color_schemes.get(
                colorscheme,
                self._natural_colors
            )
            
            # Apply coloring
            rgb = color_func(dem_norm)
            
            logger.info(f"Created World Machine colors: {rgb.shape}, scheme: {colorscheme.value}")
            return rgb
        except Exception as e:
            logger.error(f"Failed to create World Machine colors: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def _natural_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Natural terrain coloring (low=blue water, high=white mountain peaks)"""
        rgb = np.zeros(dem_norm.shape + (3,), dtype=np.uint8)
        
        # Water (deep)
        mask = dem_norm < 0.2
        rgb[mask] = [10, 60, 150]
        
        # Water (shallow)
        mask = (dem_norm >= 0.2) & (dem_norm < 0.3)
        rgb[mask] = [50, 120, 200]
        
        # Beach/Sand
        mask = (dem_norm >= 0.3) & (dem_norm < 0.4)
        rgb[mask] = [200, 180, 100]
        
        # Grass/Plains
        mask = (dem_norm >= 0.4) & (dem_norm < 0.6)
        r = int(50 + (dem_norm[mask] - 0.4) * 200)
        g = int(120 + (dem_norm[mask] - 0.4) * 80)
        b = int(50 + (dem_norm[mask] - 0.4) * 50)
        rgb[mask] = np.dstack([r, g, b])
        
        # Forest
        mask = (dem_norm >= 0.6) & (dem_norm < 0.75)
        rgb[mask] = [34, 139, 34]
        
        # Rocky
        mask = (dem_norm >= 0.75) & (dem_norm < 0.9)
        rgb[mask] = [150, 150, 150]
        
        # Snow peaks
        mask = dem_norm >= 0.9
        rgb[mask] = [255, 255, 255]
        
        return rgb
    
    def _erosion_heat_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Heat-based erosion visualization"""
        rgb = np.zeros(dem_norm.shape + (3,), dtype=np.uint8)
        
        # Cool (low erosion)
        r = (dem_norm * 255).astype(np.uint8)
        g = ((1 - dem_norm) * 100).astype(np.uint8)
        b = ((1 - dem_norm) * 255).astype(np.uint8)
        
        rgb[:, :, 0] = r
        rgb[:, :, 1] = g
        rgb[:, :, 2] = b
        
        return rgb
    
    def _geological_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Geological strata coloring"""
        rgb = np.zeros(dem_norm.shape + (3,), dtype=np.uint8)
        
        # Sedimentary layers
        colors = [
            (139, 69, 19),      # Brown - sandstone
            (105, 105, 105),    # Gray - limestone
            (128, 0, 0),        # Maroon - shale
            (192, 192, 192),    # Silver - chalk
            (210, 180, 140),    # Tan - mudstone
        ]
        
        num_layers = len(colors)
        for i, (r, g, b) in enumerate(colors):
            low = i / num_layers
            high = (i + 1) / num_layers
            mask = (dem_norm >= low) & (dem_norm < high)
            rgb[mask] = [r, g, b]
        
        return rgb
    
    def _thermal_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Thermal coloring (cool to hot)"""
        rgb = np.zeros(dem_norm.shape + (3,), dtype=np.uint8)
        
        # Thermal gradient
        r = (dem_norm * 255).astype(np.uint8)
        g = ((1 - abs(dem_norm - 0.5) * 2) * 255).astype(np.uint8)
        b = ((1 - dem_norm) * 255).astype(np.uint8)
        
        rgb[:, :, 0] = r
        rgb[:, :, 1] = g
        rgb[:, :, 2] = b
        
        return rgb
    
    def _heightmap_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Simple grayscale heightmap"""
        gray = (dem_norm * 255).astype(np.uint8)
        rgb = np.dstack([gray, gray, gray])
        return rgb
    
    def create_advanced_hillshade(
        self,
        dem: np.ndarray,
        azimuth: float = 315,
        altitude: float = 45,
        z_factor: float = 1.0,
        gamma: float = 1.0
    ) -> np.ndarray:
        """
        Create advanced hillshade with z-factor and gamma correction.
        
        Args:
            dem: 2D elevation array
            azimuth: Light direction (degrees, 0-360)
            altitude: Light angle above horizon (degrees, 0-90)
            z_factor: Vertical exaggeration
            gamma: Gamma correction
        
        Returns:
            Hillshade image
        """
        try:
            if not SCIPY_AVAILABLE:
                logger.warning("SciPy not available for advanced hillshade")
                return np.zeros((dem.shape[0], dem.shape[1]), dtype=np.uint8)
            
            from scipy.ndimage import sobel
            
            # Apply z-factor
            dem_scaled = dem * z_factor
            
            # Compute gradients
            x = sobel(dem_scaled, axis=1)
            y = sobel(dem_scaled, axis=0)
            
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
            
            # Normalize to 0-1
            shading = (shading + 1) / 2
            
            # Apply gamma correction
            if gamma != 1.0:
                shading = np.power(shading, 1.0 / gamma)
            
            # Normalize to 0-255
            hillshade = (shading * 255).astype(np.uint8)
            
            logger.info(f"Created advanced hillshade: {hillshade.shape}, z_factor: {z_factor}")
            return hillshade
        except Exception as e:
            logger.error(f"Advanced hillshade creation failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1]), dtype=np.uint8)
    
    def create_flow_visualization(
        self,
        dem: np.ndarray,
        colormap: str = 'Blues'
    ) -> np.ndarray:
        """
        Visualize water flow direction on terrain.
        
        Args:
            dem: 2D elevation array
            colormap: Matplotlib colormap
        
        Returns:
            Flow visualization image
        """
        try:
            if not SCIPY_AVAILABLE:
                logger.warning("SciPy not available for flow visualization")
                return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
            
            from scipy.ndimage import sobel
            
            # Compute gradients (flow direction)
            gradient_x = sobel(dem, axis=1)
            gradient_y = sobel(dem, axis=0)
            
            # Compute flow magnitude
            flow_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
            
            # Normalize
            flow_norm = flow_magnitude / (flow_magnitude.max() + 1e-10)
            
            # Colorize
            if MATPLOTLIB_AVAILABLE:
                try:
                    import matplotlib.cm as cm
                    if hasattr(cm, 'get_cmap'):
                        cmap = cm.get_cmap(colormap)
                    else:
                        import matplotlib.pyplot as plt_mod
                        cmap = plt_mod.get_cmap(colormap)
                    rgba = cmap(flow_norm)
                    # Handle array shape properly
                    if len(rgba.shape) == 3 and rgba.shape[2] >= 3:
                        rgb = (rgba[:, :, :3] * 255).astype(np.uint8)
                    else:
                        # Fallback for unexpected shape
                        rgb = np.dstack([
                            (flow_norm * 255).astype(np.uint8),
                            ((1 - flow_norm) * 255).astype(np.uint8),
                            np.zeros_like(flow_norm, dtype=np.uint8)
                        ])
                except (ImportError, AttributeError, ValueError):
                    # Fallback
                    rgb = np.dstack([
                        (flow_norm * 255).astype(np.uint8),
                        ((1 - flow_norm) * 255).astype(np.uint8),
                        np.zeros_like(flow_norm, dtype=np.uint8)
                    ])
            else:
                # Simple gradient
                rgb = np.dstack([
                    (flow_norm * 255).astype(np.uint8),
                    ((1 - flow_norm) * 255).astype(np.uint8),
                    np.zeros_like(flow_norm, dtype=np.uint8)
                ])
            
            logger.info(f"Created flow visualization: {rgb.shape}")
            return rgb
        except Exception as e:
            logger.error(f"Flow visualization failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def create_erosion_deposition_map(
        self,
        dem: np.ndarray,
        erosion_map: np.ndarray,
        deposition_map: np.ndarray
    ) -> np.ndarray:
        """
        Create erosion/deposition visualization.
        
        Args:
            dem: 2D elevation array
            erosion_map: Areas and amounts of erosion (negative values)
            deposition_map: Areas and amounts of deposition (positive values)
        
        Returns:
            Visualization image (red=erosion, blue=deposition, neutral=stable)
        """
        try:
            # Normalize maps
            max_erosion = np.abs(erosion_map).max()
            max_deposition = deposition_map.max()
            
            erosion_norm = np.abs(erosion_map) / (max_erosion + 1e-10)
            deposition_norm = deposition_map / (max_deposition + 1e-10)
            
            # Create RGB image
            rgb = np.zeros(dem.shape + (3,), dtype=np.uint8)
            
            # Red for erosion
            rgb[:, :, 0] = (erosion_norm * 255).astype(np.uint8)
            
            # Blue for deposition
            rgb[:, :, 2] = (deposition_norm * 255).astype(np.uint8)
            
            # Green for stable areas
            stable = 1 - (erosion_norm + deposition_norm) / 2
            rgb[:, :, 1] = (stable * 100).astype(np.uint8)
            
            logger.info(f"Created erosion/deposition map: {rgb.shape}")
            return rgb
        except Exception as e:
            logger.error(f"Erosion/deposition mapping failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)
    
    def render_simulation_frame(
        self,
        dem: np.ndarray,
        timestep: int,
        colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL,
        show_hillshade: bool = True,
        blend_factor: float = 0.7
    ) -> np.ndarray:
        """
        Render single simulation frame with optional hillshade blending.
        
        Args:
            dem: 2D elevation array at timestep
            timestep: Current simulation timestep
            colorscheme: Color scheme to use
            show_hillshade: Whether to blend with hillshade
            blend_factor: Blend factor (0.0-1.0) for hillshade
        
        Returns:
            Rendered frame
        """
        try:
            # Create colored terrain
            colored = self.create_world_machine_colors(dem, colorscheme)
            
            if show_hillshade and blend_factor > 0:
                # Create hillshade
                hillshade = self.create_advanced_hillshade(dem)
                
                # Normalize hillshade to 0-1
                hillshade_norm = hillshade.astype(np.float32) / 255.0
                
                # Blend: darken highlights, brighten shadows
                for c in range(3):
                    colored[:, :, c] = (
                        colored[:, :, c] * (1 - blend_factor) +
                        colored[:, :, c] * hillshade_norm * blend_factor
                    ).astype(np.uint8)
            
            logger.info(f"Rendered simulation frame: timestep={timestep}, shape={colored.shape}")
            return colored
        except Exception as e:
            logger.error(f"Frame rendering failed: {e}")
            return np.zeros((dem.shape[0], dem.shape[1], 3), dtype=np.uint8)


class SimulationAnimationRenderer:
    """Render simulation frames as animation"""
    
    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.visualizer = WorldMachineVisualizer()
    
    def add_snapshot(
        self,
        dem: np.ndarray,
        timestep: int,
        total_timesteps: int,
        colorscheme: Optional[WorldMachineColorScheme] = None
    ) -> bool:
        """
        Add simulation frame to animation.
        
        Args:
            dem: 2D elevation array
            timestep: Current timestep
            total_timesteps: Total timesteps
            colorscheme: Color scheme
        
        Returns:
            Success status
        """
        try:
            if colorscheme is None:
                colorscheme = WorldMachineColorScheme.NATURAL
            
            # Render frame
            frame = self.visualizer.render_simulation_frame(
                dem,
                timestep,
                colorscheme,
                show_hillshade=True
            )
            
            self.frames.append(frame)
            
            progress = (timestep + 1) / total_timesteps * 100
            logger.debug(f"Added animation frame: timestep={timestep}, progress={progress:.1f}%")
            
            return True
        except Exception as e:
            logger.error(f"Failed to add snapshot: {e}")
            return False
    
    def save_animation(
        self,
        output_path: str,
        duration_per_frame: int = 100
    ) -> bool:
        """
        Save animation as GIF or video.
        
        Args:
            output_path: Output file path (.gif or .mp4)
            duration_per_frame: Duration per frame in milliseconds
        
        Returns:
            Success status
        """
        try:
            if not self.frames:
                logger.error("No frames to save")
                return False
            
            if output_path.endswith('.gif'):
                return self._save_as_gif(output_path, duration_per_frame)
            elif output_path.endswith(('.mp4', '.avi', '.mov')):
                return self._save_as_video(output_path, duration_per_frame)
            else:
                logger.error(f"Unsupported format: {output_path}")
                return False
        except Exception as e:
            logger.error(f"Animation saving failed: {e}")
            return False
    
    def _save_as_gif(self, output_path: str, duration_per_frame: int) -> bool:
        """Save frames as GIF"""
        try:
            if not PIL_AVAILABLE:
                logger.error("PIL not available for GIF export")
                return False
            
            from PIL import Image
            
            # Convert numpy arrays to PIL Images
            images = []
            for frame in self.frames:
                img = Image.fromarray(frame.astype(np.uint8))
                images.append(img)
            
            # Save as GIF
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_per_frame,
                loop=0
            )
            
            logger.info(f"Saved animation as GIF: {output_path}")
            return True
        except Exception as e:
            logger.error(f"GIF export failed: {e}")
            return False
    
    def _save_as_video(self, output_path: str, duration_per_frame: int) -> bool:
        """Save frames as video (requires OpenCV or similar)"""
        try:
            # Note: Would need OpenCV (cv2) for this
            # For now, just save as GIF with .mp4 extension warning
            logger.warning("Video export requires OpenCV - falling back to GIF")
            
            # Convert to GIF path
            gif_path = output_path.replace(output_path.split('.')[-1], 'gif')
            return self._save_as_gif(gif_path, duration_per_frame)
        except Exception as e:
            logger.error(f"Video export failed: {e}")
            return False
    
    def clear(self):
        """Clear all frames"""
        self.frames.clear()
        logger.info("Cleared animation frames")
    
    def get_frame_count(self) -> int:
        """Get number of frames"""
        return len(self.frames)
    
    def export_frame(self, frame_index: int, output_path: str) -> bool:
        """Export single frame as image"""
        try:
            if not PIL_AVAILABLE:
                logger.error("PIL not available for image export")
                return False
            
            if frame_index < 0 or frame_index >= len(self.frames):
                logger.error(f"Invalid frame index: {frame_index}")
                return False
            
            from PIL import Image
            img = Image.fromarray(self.frames[frame_index].astype(np.uint8))
            img.save(output_path)
            
            logger.info(f"Exported frame {frame_index}: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Frame export failed: {e}")
            return False
