"""
World Machine-style 3D Terrain Visualization
Real-time simulation visualization with procedural terrain coloring and erosion effects
"""

import numpy as np
import logging
from typing import Optional, Dict, Tuple, List
from enum import Enum
import math

logger = logging.getLogger(__name__)

try:
    import moderngl
    from PIL import Image
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    logger.warning("moderngl/matplotlib not available")


class WorldMachineColorScheme(Enum):
    """World Machine-style color schemes"""
    NATURAL = "natural"           # Green valleys, brown highlands
    EROSION_HEAT = "erosion_heat" # Red=erosion, Blue=deposition
    GEOLOGICAL = "geological"     # Realistic geology colors
    THERMAL = "thermal"           # Heat-based coloring
    HEIGHTMAP = "heightmap"       # Grayscale based on elevation


class WorldMachineVisualizer:
    """
    World Machine-style terrain visualization engine
    Provides real-time, high-quality visualization of terrain evolution
    """
    
    def __init__(self):
        """Initialize the visualizer"""
        self.ctx = None
        self.quad_fs = None
        self.quad_vao = None
        self.terrain_shader = None
        self.colorscheme = WorldMachineColorScheme.NATURAL
        self.erosion_intensity = 1.0
        self.lighting_quality = "high"
        self.enable_normal_mapping = True
        self.enable_parallax = False
        
    def create_world_machine_colors(
        self,
        dem: np.ndarray,
        colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL
    ) -> np.ndarray:
        """
        Create World Machine-style colors from DEM
        
        Args:
            dem: Digital elevation model
            colorscheme: Color scheme to use
            
        Returns:
            RGBA color array for each vertex
        """
        dem_norm = (dem - dem.min()) / (dem.max() - dem.min() + 1e-6)
        h, w = dem.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        if colorscheme == WorldMachineColorScheme.NATURAL:
            colors = self._create_natural_colors(dem_norm)
        elif colorscheme == WorldMachineColorScheme.EROSION_HEAT:
            colors = self._create_erosion_heatmap(dem_norm)
        elif colorscheme == WorldMachineColorScheme.GEOLOGICAL:
            colors = self._create_geological_colors(dem_norm)
        elif colorscheme == WorldMachineColorScheme.THERMAL:
            colors = self._create_thermal_colors(dem_norm)
        elif colorscheme == WorldMachineColorScheme.HEIGHTMAP:
            colors = self._create_heightmap_colors(dem_norm)
        
        return colors.astype(np.float32)
    
    def _create_natural_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """World Machine natural terrain colors"""
        h, w = dem_norm.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        # Deep water: dark blue
        water_mask = dem_norm < 0.2
        colors[water_mask, 0] = 0.1  # R
        colors[water_mask, 1] = 0.3  # G
        colors[water_mask, 2] = 0.6  # B
        colors[water_mask, 3] = 1.0  # A
        
        # Shallow water: light blue
        shallow_mask = (dem_norm >= 0.2) & (dem_norm < 0.35)
        colors[shallow_mask, 0] = 0.2
        colors[shallow_mask, 1] = 0.5
        colors[shallow_mask, 2] = 0.8
        colors[shallow_mask, 3] = 1.0
        
        # Sandy beaches: golden tan
        beach_mask = (dem_norm >= 0.35) & (dem_norm < 0.45)
        colors[beach_mask, 0] = 0.8
        colors[beach_mask, 1] = 0.75
        colors[beach_mask, 2] = 0.4
        colors[beach_mask, 3] = 1.0
        
        # Grassland: green
        grass_mask = (dem_norm >= 0.45) & (dem_norm < 0.65)
        colors[grass_mask, 0] = 0.2 + 0.3 * dem_norm[grass_mask]
        colors[grass_mask, 1] = 0.5 + 0.2 * dem_norm[grass_mask]
        colors[grass_mask, 2] = 0.1 + 0.1 * dem_norm[grass_mask]
        colors[grass_mask, 3] = 1.0
        
        # Rocky foothills: gray-brown
        rock_mask = (dem_norm >= 0.65) & (dem_norm < 0.85)
        colors[rock_mask, 0] = 0.5 + 0.2 * dem_norm[rock_mask]
        colors[rock_mask, 1] = 0.4 + 0.15 * dem_norm[rock_mask]
        colors[rock_mask, 2] = 0.3 + 0.1 * dem_norm[rock_mask]
        colors[rock_mask, 3] = 1.0
        
        # Snow peaks: white
        snow_mask = dem_norm >= 0.85
        colors[snow_mask, 0] = 0.95
        colors[snow_mask, 1] = 0.95
        colors[snow_mask, 2] = 1.0
        colors[snow_mask, 3] = 1.0
        
        return colors
    
    def _create_erosion_heatmap(self, dem_norm: np.ndarray) -> np.ndarray:
        """Create erosion/deposition heatmap"""
        h, w = dem_norm.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        # Red for high elevation, Blue for low (shows slope)
        colors[:, :, 0] = 0.3 + 0.7 * dem_norm  # R
        colors[:, :, 1] = 0.3 * (1 - np.abs(2 * dem_norm - 1))  # G (peak in middle)
        colors[:, :, 2] = 0.3 + 0.7 * (1 - dem_norm)  # B
        colors[:, :, 3] = 1.0
        
        return colors
    
    def _create_geological_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Create realistic geological colors"""
        h, w = dem_norm.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        # Multi-layer geological coloring
        colors[:, :, 0] = 0.3 + 0.4 * dem_norm  # R
        colors[:, :, 1] = 0.4 + 0.3 * np.sin(dem_norm * np.pi)  # G (undulating)
        colors[:, :, 2] = 0.2 + 0.3 * (1 - dem_norm)  # B
        colors[:, :, 3] = 1.0
        
        return colors
    
    def _create_thermal_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Create thermal/temperature-based colors"""
        h, w = dem_norm.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        # Cool to hot: blue -> cyan -> yellow -> red
        colors[:, :, 0] = np.where(dem_norm < 0.5,
                                   0.0,
                                   (dem_norm - 0.5) * 2)  # R
        colors[:, :, 1] = dem_norm  # G
        colors[:, :, 2] = np.where(dem_norm < 0.5,
                                   1.0 - dem_norm * 2,
                                   0.0)  # B
        colors[:, :, 3] = 1.0
        
        return colors
    
    def _create_heightmap_colors(self, dem_norm: np.ndarray) -> np.ndarray:
        """Create grayscale heightmap colors"""
        h, w = dem_norm.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        colors[:, :, 0] = dem_norm  # R
        colors[:, :, 1] = dem_norm  # G
        colors[:, :, 2] = dem_norm  # B
        colors[:, :, 3] = 1.0  # A
        
        return colors
    
    def create_advanced_hillshade(
        self,
        dem: np.ndarray,
        azimuth: float = 315,
        altitude: float = 45,
        z_factor: float = 1.0
    ) -> np.ndarray:
        """
        Create advanced hillshade with World Machine quality
        
        Args:
            dem: Digital elevation model
            azimuth: Light direction (degrees)
            altitude: Light angle above horizon (degrees)
            z_factor: Vertical exaggeration
            
        Returns:
            Hillshade array
        """
        h, w = dem.shape
        
        # Apply z-factor
        dem_scaled = dem.copy()
        if z_factor != 1.0:
            dem_scaled = dem_scaled - dem_scaled.mean()
            dem_scaled = dem_scaled * z_factor
            dem_scaled = dem_scaled + dem_scaled.mean()
        
        # Calculate gradients with Sobel operator for better quality
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        
        grad_x = self._convolve2d(dem_scaled, sobel_x)
        grad_y = self._convolve2d(dem_scaled, sobel_y)
        
        # Light direction
        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)
        
        # Calculate surface normals
        normal_x = -grad_x
        normal_y = -grad_y
        normal_z = np.ones_like(grad_x)
        
        # Normalize
        magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x = normal_x / (magnitude + 1e-6)
        normal_y = normal_y / (magnitude + 1e-6)
        normal_z = normal_z / (magnitude + 1e-6)
        
        # Light vector
        light_x = np.cos(azimuth_rad) * np.cos(altitude_rad)
        light_y = np.sin(azimuth_rad) * np.cos(altitude_rad)
        light_z = np.sin(altitude_rad)
        
        # Dot product for shading
        shading = normal_x * light_x + normal_y * light_y + normal_z * light_z
        
        # Enhance contrast
        shading = (shading + 1) / 2  # Normalize to [0, 1]
        shading = np.power(shading, 0.9)  # Gamma correction
        
        return np.clip(shading, 0, 1).astype(np.float32)
    
    def _convolve2d(self, data: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Simple 2D convolution"""
        h, w = data.shape
        kh, kw = kernel.shape
        
        result = np.zeros_like(data)
        
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                region = data[i-1:i+2, j-1:j+2]
                result[i, j] = np.sum(region * kernel)
        
        return result
    
    def create_flow_visualization(
        self,
        dem: np.ndarray
    ) -> np.ndarray:
        """
        Create water flow accumulation visualization
        Shows where water flows and collects
        
        Args:
            dem: Digital elevation model
            
        Returns:
            Flow accumulation as color array
        """
        h, w = dem.shape
        
        # Calculate gradients
        grad_x, grad_y = np.gradient(dem)
        
        # Simple D8 flow accumulation
        flow_accum = np.ones((h, w))
        
        # Directions: [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for _ in range(10):  # Multiple passes for convergence
            for i in range(1, h - 1):
                for j in range(1, w - 1):
                    # Find steepest descent direction
                    neighbors = [
                        (i-1, j-1), (i-1, j), (i-1, j+1),
                        (i, j-1), (i, j+1),
                        (i+1, j-1), (i+1, j), (i+1, j+1)
                    ]
                    
                    min_elev = dem[i, j]
                    for ni, nj in neighbors:
                        if 0 <= ni < h and 0 <= nj < w:
                            min_elev = min(min_elev, dem[ni, nj])
                    
                    # Flow moves toward lower elevation
                    for ni, nj in neighbors:
                        if 0 <= ni < h and 0 <= nj < w and dem[ni, nj] < dem[i, j]:
                            flow_accum[i, j] += 0.125 * flow_accum[ni, nj]
        
        # Normalize and colorize
        flow_norm = (flow_accum - flow_accum.min()) / (flow_accum.max() - flow_accum.min() + 1e-6)
        
        # Blue colors for water flow
        colors = np.zeros((h, w, 4), dtype=np.float32)
        colors[:, :, 0] = 0.1 * flow_norm  # R
        colors[:, :, 1] = 0.3 + 0.5 * flow_norm  # G
        colors[:, :, 2] = 0.8 * (1 - flow_norm)  # B
        colors[:, :, 3] = 1.0
        
        return colors
    
    def blend_visualizations(
        self,
        base: np.ndarray,
        overlay: np.ndarray,
        strength: float = 0.3
    ) -> np.ndarray:
        """
        Blend two visualizations together
        
        Args:
            base: Base colors (RGBA)
            overlay: Overlay colors (RGBA)
            strength: Blend strength (0-1)
            
        Returns:
            Blended colors
        """
        return (1 - strength) * base + strength * overlay
    
    def apply_postprocessing(
        self,
        colors: np.ndarray,
        dem: np.ndarray,
        contrast: float = 1.2,
        saturation: float = 1.1,
        brightness: float = 1.0
    ) -> np.ndarray:
        """
        Apply post-processing effects (World Machine style)
        
        Args:
            colors: Input colors (float32, normalized to 0-1)
            dem: Digital elevation model (for effects)
            contrast: Contrast factor
            saturation: Color saturation
            brightness: Brightness factor
            
        Returns:
            Post-processed colors (float32, 0-1 range)
        """
        try:
            # Ensure input is float32
            colors = np.asarray(colors, dtype=np.float32)
            
            # Store original shape and number of channels
            h, w, c = colors.shape
            
            # Reshape for processing
            colors_flat = colors.reshape(-1, c)
            
            # Apply contrast
            colors_flat[:, :3] = (colors_flat[:, :3] - 0.5) * contrast + 0.5
            
            # Apply brightness
            colors_flat[:, :3] = colors_flat[:, :3] * brightness
            
            # Apply saturation
            gray = np.mean(colors_flat[:, :3], axis=1, keepdims=True)
            colors_flat[:, :3] = gray + saturation * (colors_flat[:, :3] - gray)
            
            # Clamp to valid range
            colors_flat = np.clip(colors_flat, 0, 1)
            
            # Reshape back
            return colors_flat.reshape(h, w, c)
        except Exception as e:
            logger.error(f"Error in apply_postprocessing: {e}")
            return colors
    
    def create_erosion_deposition_map(
        self,
        current_dem: np.ndarray,
        previous_dem: np.ndarray
    ) -> Dict:
        """
        Create erosion and deposition maps
        Shows where material is removed/added
        
        Args:
            current_dem: Current elevation model
            previous_dem: Previous elevation model
            
        Returns:
            Dictionary with erosion/deposition data and colors
        """
        # Calculate changes
        change = current_dem - previous_dem
        
        h, w = change.shape
        colors = np.zeros((h, w, 4), dtype=np.float32)
        
        # Erosion (negative change): red
        erosion_mask = change < 0
        erosion_intensity = np.abs(change[erosion_mask])
        if erosion_intensity.max() > 0:
            erosion_norm = erosion_intensity / erosion_intensity.max()
            colors[erosion_mask, 0] = 0.8 + 0.2 * erosion_norm
            colors[erosion_mask, 1] = 0.1 + 0.1 * erosion_norm
            colors[erosion_mask, 2] = 0.1 + 0.1 * erosion_norm
            colors[erosion_mask, 3] = 1.0
        
        # Deposition (positive change): blue
        deposition_mask = change > 0
        deposition_intensity = change[deposition_mask]
        if deposition_intensity.max() > 0:
            deposition_norm = deposition_intensity / deposition_intensity.max()
            colors[deposition_mask, 0] = 0.1 + 0.1 * deposition_norm
            colors[deposition_mask, 1] = 0.1 + 0.1 * deposition_norm
            colors[deposition_mask, 2] = 0.8 + 0.2 * deposition_norm
            colors[deposition_mask, 3] = 1.0
        
        return {
            'colors': colors,
            'erosion_map': (change < 0).astype(np.float32) * np.abs(change),
            'deposition_map': (change > 0).astype(np.float32) * change,
            'total_erosion': np.sum(np.abs(change[erosion_mask])) if erosion_mask.any() else 0,
            'total_deposition': np.sum(change[deposition_mask]) if deposition_mask.any() else 0,
        }
    
    def render_simulation_frame(
        self,
        dem: np.ndarray,
        timestep: int = 0,
        total_timesteps: int = 1,
        colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL,
        show_hillshade: bool = True,
        show_flow: bool = False
    ) -> np.ndarray:
        """
        Render a single frame of the simulation
        
        Args:
            dem: Digital elevation model
            timestep: Current timestep
            total_timesteps: Total timesteps in simulation
            colorscheme: Color scheme to use
            show_hillshade: Enable hillshade overlay
            show_flow: Show water flow visualization
            
        Returns:
            RGB image array (uint8, h x w x 3)
        """
        try:
            # Ensure input is valid
            dem = np.asarray(dem, dtype=np.float32)
            
            # Create base colors
            colors = self.create_world_machine_colors(dem, colorscheme)
            
            # Add hillshade
            if show_hillshade:
                hillshade = self.create_advanced_hillshade(dem)
                hillshade_rgb = np.stack([hillshade, hillshade, hillshade, np.ones_like(hillshade)], axis=-1)
                colors = self.blend_visualizations(colors, hillshade_rgb, strength=0.4)
            
            # Add flow visualization
            if show_flow:
                flow_colors = self.create_flow_visualization(dem)
                colors = self.blend_visualizations(colors, flow_colors, strength=0.2)
            
            # Post-processing
            colors = self.apply_postprocessing(colors, dem, contrast=1.15, saturation=1.05)
            
            # Convert to uint8
            colors = np.clip(colors, 0, 1)
            colors_uint8 = (colors * 255).astype(np.uint8)
            
            # Ensure RGB (remove alpha if present)
            if colors_uint8.shape[-1] == 4:
                colors_uint8 = colors_uint8[:, :, :3]
            
            return colors_uint8
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            raise
    
    def save_rendered_frame(
        self,
        dem: np.ndarray,
        timestep: int,
        total_timesteps: int,
        filename: str,
        colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL
    ):
        """
        Save a rendered frame to disk
        
        Args:
            dem: Digital elevation model
            timestep: Current timestep
            total_timesteps: Total timesteps
            filename: Output filename
            colorscheme: Color scheme to use
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Render frame
            frame = self.render_simulation_frame(dem, timestep, total_timesteps, colorscheme)
            
            # Convert to PIL Image
            img = Image.fromarray(frame[:, :, :3])
            
            # Add text overlay
            draw = ImageDraw.Draw(img)
            text = f"Timestep {timestep}/{total_timesteps}"
            draw.text((10, 10), text, fill=(255, 255, 255))
            
            # Save
            img.save(filename)
            logger.info(f"Saved frame to {filename}")
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")


class SimulationAnimationRenderer:
    """Renders terrain simulator snapshots as World Machine-style animation"""
    
    def __init__(self, colorscheme: WorldMachineColorScheme = WorldMachineColorScheme.NATURAL):
        """
        Initialize animation renderer
        
        Args:
            colorscheme: Default color scheme for all frames
        """
        self.visualizer = WorldMachineVisualizer()
        self.frames = []
        self.colorscheme = colorscheme
        self.frame_count = 0
        logger.info("SimulationAnimationRenderer initialized")
    
    def add_snapshot(
        self,
        dem: np.ndarray,
        timestep: int,
        total_timesteps: int,
        colorscheme: Optional[WorldMachineColorScheme] = None
    ):
        """
        Add a simulation snapshot to animation
        
        Args:
            dem: Digital elevation model
            timestep: Current timestep
            total_timesteps: Total timesteps
            colorscheme: Color scheme (uses default if None)
        """
        try:
            if colorscheme is None:
                colorscheme = self.colorscheme
            
            # Ensure DEM is valid
            dem = np.asarray(dem, dtype=np.float32)
            if dem.size == 0:
                raise ValueError("DEM is empty")
            
            # Render frame
            frame = self.visualizer.render_simulation_frame(
                dem, timestep, total_timesteps, colorscheme
            )
            
            if frame is None or frame.size == 0:
                raise ValueError("Rendered frame is empty")
            
            self.frames.append(frame)
            self.frame_count += 1
            logger.info(f"Added frame {self.frame_count} (timestep {timestep}/{total_timesteps})")
        except Exception as e:
            logger.error(f"Failed to add snapshot: {e}")
            raise
    
    def save_animation(
        self,
        output_path: str,
        duration_per_frame: int = 100,
        loop: int = 0
    ) -> bool:
        """
        Save animation as GIF
        
        Args:
            output_path: Output file path (.gif)
            duration_per_frame: Duration per frame in milliseconds
            loop: Number of loops (0 = infinite)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from PIL import Image
            
            # Validate frames
            if not self.frames:
                logger.warning("No frames to save")
                return False
            
            if len(self.frames) < 2:
                logger.warning("Need at least 2 frames for animation")
                return False
            
            # Ensure output path is valid
            output_path = str(output_path)
            if not output_path.lower().endswith('.gif'):
                output_path = output_path + '.gif'
            
            # Create parent directory if needed
            import os
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Convert frames to PIL Images
            logger.info(f"Converting {len(self.frames)} frames to PIL format...")
            pil_frames = []
            for i, frame in enumerate(self.frames):
                try:
                    # Ensure frame is uint8
                    if frame.dtype != np.uint8:
                        frame = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
                    
                    # Ensure RGB
                    if frame.shape[-1] == 4:
                        frame = frame[:, :, :3]
                    
                    pil_img = Image.fromarray(frame)
                    pil_frames.append(pil_img)
                except Exception as e:
                    logger.error(f"Failed to convert frame {i}: {e}")
                    raise
            
            # Save as GIF
            logger.info(f"Saving animation to {output_path}...")
            pil_frames[0].save(
                output_path,
                save_all=True,
                append_images=pil_frames[1:],
                duration=duration_per_frame,
                loop=loop,
                optimize=False
            )
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Animation saved successfully: {output_path} ({file_size / 1024:.1f} KB)")
                return True
            else:
                logger.error("Animation file was not created")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save animation: {e}")
            return False
    
    def clear_frames(self):
        """Clear all stored frames"""
        self.frames = []
        self.frame_count = 0
        logger.info("Frames cleared")
    
    def get_frame_count(self) -> int:
        """Get number of stored frames"""
        return self.frame_count
