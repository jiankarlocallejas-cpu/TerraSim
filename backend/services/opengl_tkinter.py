"""
OpenGL-Tkinter Integration
Provides an OpenGL rendering canvas embedded in Tkinter windows
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import logging
from typing import Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)

try:
    from OpenGL.GL import *  # type: ignore
    from OpenGL.GLU import *  # type: ignore
    from OpenGL.GL.shaders import compileProgram, compileShader
    import OpenGL
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    logger.warning("OpenGL not available")


class TkinterOpenGLCanvas(tk.Canvas):
    """
    Tkinter canvas that renders OpenGL content
    Lightweight alternative to full window context
    """
    
    def __init__(self, parent, width: int = 800, height: int = 600, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#1a1a1a', **kwargs)
        
        self.width = width
        self.height = height
        self.terrain_data = None
        self.erosion_data = None
        self.is_updating = False
        
        # For software rendering (fallback when OpenGL unavailable)
        self.use_software_rendering = not OPENGL_AVAILABLE
        
        # Performance optimization: cache colormaps to avoid repeated lookups
        self._colormap_cache = {}
        self._last_image = None  # Prevent garbage collection
        
        logger.info(f"TkinterOpenGLCanvas created ({width}x{height}, {'OpenGL' if not self.use_software_rendering else 'Software'})")
    
    def update_terrain(self, dem: np.ndarray, colormap: str = "viridis"):
        """Update terrain visualization"""
        self.terrain_data = dem.copy()
        self._render_heatmap(dem, colormap)
    
    def update_erosion(self, erosion_data: np.ndarray):
        """Update erosion heatmap"""
        self.erosion_data = erosion_data.copy()
        self._render_heatmap(erosion_data, "hot")
    
    def _render_heatmap(self, data: np.ndarray, colormap: str = "viridis"):
        """Render 2D data as heatmap using efficient NumPy-based approach (non-blocking)"""
        try:
            from PIL import Image, ImageTk
            import matplotlib.cm as cm  # type: ignore
            
            # Quick validation check
            if data.size == 0 or not np.any(np.isfinite(data)):
                self._render_gradient_fast(data)
                return
            
            # Normalize data to 0-1 range
            data_min = np.nanmin(data)
            data_max = np.nanmax(data)
            if data_max <= data_min:
                data_max = data_min + 1e-6
            
            normalized = (data - data_min) / (data_max - data_min)
            normalized = np.clip(normalized, 0, 1)
            
            # OPTIMIZATION: Cache colormaps to avoid repeated lookups
            if colormap not in self._colormap_cache:
                try:
                    self._colormap_cache[colormap] = cm.get_cmap(colormap)
                except:
                    self._colormap_cache[colormap] = cm.get_cmap('viridis')
            
            cmap = self._colormap_cache[colormap]
            
            # Apply colormap to normalized data efficiently
            # This is MUCH faster than matplotlib rendering
            rgba_data = cmap(normalized)  # Returns (H, W, 4) array with values 0-1
            
            # Convert to 0-255 uint8 for PIL
            rgba_uint8 = (rgba_data * 255).astype(np.uint8)
            
            # Resize to canvas dimensions using PIL for efficiency
            pil_image = Image.fromarray(rgba_uint8, 'RGBA')
            pil_image = pil_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Store image reference to prevent garbage collection
            self.image = ImageTk.PhotoImage(pil_image)
            self._last_image = self.image  # Double reference for extra safety
            self.delete("all")  # Clear previous content
            self.create_image(0, 0, image=self.image, anchor='nw')
            
        except Exception as e:
            logger.error(f"Error rendering heatmap: {e}")
            # Fallback: simple gradient (still efficient)
            self._render_gradient_fast(data)
    
    def _render_gradient(self, data: np.ndarray):
        """Legacy fallback - use _render_gradient_fast instead"""
        self._render_gradient_fast(data)
    
    def _render_gradient_fast(self, data: np.ndarray):
        """Fast fallback: render heatmap using NumPy+PIL (no per-pixel operations)"""
        try:
            from PIL import Image, ImageTk
            
            # Normalize data
            data_min = np.nanmin(data)
            data_max = np.nanmax(data)
            if data_max <= data_min:
                data_max = data_min + 1e-6
            
            normalized = (data - data_min) / (data_max - data_min)
            normalized = np.clip(normalized, 0, 1)
            
            # Create hot colormap using NumPy (no per-pixel loops!)
            # Hot colormap: black -> red -> yellow -> white
            height, width = normalized.shape
            
            # Create RGB array directly
            rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Apply hot colormap using vectorized operations
            # Red channel: 0 at bottom, 255 at top
            rgb_data[:, :, 0] = (normalized * 255).astype(np.uint8)
            
            # Green channel: 0 at bottom, 255 in middle, 255 at top
            green = np.clip(normalized * 2, 0, 1)
            green = np.where(green > 1, 1, green)
            rgb_data[:, :, 1] = (green * 255).astype(np.uint8)
            
            # Blue channel: 0 at bottom, 0 in middle, 255 at top
            blue = np.clip((normalized - 0.5) * 2, 0, 1)
            rgb_data[:, :, 2] = (blue * 255).astype(np.uint8)
            
            # Convert to PIL and resize
            pil_image = Image.fromarray(rgb_data, 'RGB')
            pil_image = pil_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Update canvas
            self.image = ImageTk.PhotoImage(pil_image)
            self.delete("all")
            self.create_image(0, 0, image=self.image, anchor='nw')
            
        except Exception as e:
            logger.error(f"Error in fast gradient rendering: {e}")
            # Final fallback: solid color
            self.delete("all")
            self.create_rectangle(0, 0, self.width, self.height, fill='#cccccc')


class OpenGLVisualizationWidget(tk.Frame):
    """Complete widget for OpenGL-based terrain/erosion visualization"""
    
    def __init__(self, parent, dem: np.ndarray, **kwargs):
        super().__init__(parent, bg='white', **kwargs)
        
        # Optimization: Store reference instead of copying DEM data
        self.dem = dem
        self.current_dem = dem
        self.erosion_data = None
        self.is_updating = False
        
        # Cache colormap for performance
        self._colormap = "viridis"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header = tk.Frame(self, bg='#2c3e50', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="3D Terrain Visualization",
            font=("Arial", 14, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title.pack(pady=10)
        
        # Canvas
        self.canvas = TkinterOpenGLCanvas(self, width=900, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Colormap selector
        tk.Label(control_frame, text="Colormap:", bg='white').pack(side=tk.LEFT, padx=5)
        self.colormap_var = tk.StringVar(value=self._colormap)
        colormap_combo = ttk.Combobox(
            control_frame,
            textvariable=self.colormap_var,
            values=["viridis", "terrain", "cool", "hot", "RdYlBu"],
            state="readonly",
            width=15
        )
        colormap_combo.pack(side=tk.LEFT, padx=5)
        colormap_combo.bind("<<ComboboxSelected>>", self._on_colormap_changed)
        
        # Update button
        tk.Button(
            control_frame,
            text="Update Visualization",
            command=self._update_visualization
        ).pack(side=tk.LEFT, padx=5)
        
        # Display initial terrain
        self._update_visualization()
    
    def _on_colormap_changed(self, event=None):
        """Handle colormap selection change - optimized"""
        self._colormap = self.colormap_var.get()
        self._update_visualization()
    
    def _update_visualization(self):
        """Update the canvas visualization - optimized"""
        self.canvas.update_terrain(self.current_dem, self._colormap)
    
    def update_dem(self, dem: np.ndarray):
        """Update DEM and redraw - optimized with reference storage"""
        self.current_dem = dem
        self._update_visualization()
    
    def set_erosion_overlay(self, erosion_data: np.ndarray):
        """Set erosion data for overlay visualization - optimized"""
        self.erosion_data = erosion_data


class AnimatedOpenGLCanvas(tk.Frame):
    """OpenGL canvas with animation support for time-series data"""
    
    def __init__(self, parent, initial_dem: np.ndarray, **kwargs):
        super().__init__(parent, bg='white', **kwargs)
        
        self.initial_dem = initial_dem.copy()
        self.frames = [initial_dem.copy()]
        self.current_frame = 0
        self.is_playing = False
        self.update_rate = 100  # milliseconds
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create animation widget"""
        # Header
        header = tk.Frame(self, bg='#34495e')
        header.pack(fill=tk.X)
        
        title = tk.Label(
            header,
            text="Time-Series Animation",
            font=("Arial", 12, "bold"),
            bg='#34495e',
            fg='white'
        )
        title.pack(pady=5)
        
        # Canvas
        self.canvas = TkinterOpenGLCanvas(self, width=800, height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls
        control_frame = tk.Frame(self, bg='white')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Play/Pause button
        self.play_button = tk.Button(
            control_frame,
            text="▶ Play",
            command=self._toggle_playback,
            width=10
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Frame slider
        tk.Label(control_frame, text="Frame:").pack(side=tk.LEFT, padx=5)
        self.frame_slider = tk.Scale(
            control_frame,
            from_=0,
            to=0,
            orient=tk.HORIZONTAL,
            command=self._on_frame_changed,
            length=300
        )
        self.frame_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.frame_label = tk.Label(control_frame, text="0/0", width=8)
        self.frame_label.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        tk.Label(control_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_scale = tk.Scale(
            control_frame,
            from_=50,
            to=500,
            orient=tk.HORIZONTAL,
            command=self._on_speed_changed,
            length=100
        )
        self.speed_scale.set(100)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Initial render
        self.canvas.update_terrain(self.initial_dem)
    
    def add_frame(self, dem: np.ndarray):
        """Add a frame to the animation - optimized frame management"""
        # Store reference instead of copy to save memory
        self.frames.append(dem)
        self.frame_slider.config(to=len(self.frames) - 1)
    
    def _toggle_playback(self):
        """Toggle playback with optimized state management"""
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸ Pause" if self.is_playing else "▶ Play")
        
        if self.is_playing:
            self._animate()
    
    def _animate(self):
        """Animation loop with optimized frame handling"""
        if not self.is_playing or self.current_frame >= len(self.frames) - 1:
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            return
        
        try:
            self.current_frame += 1
            self.frame_slider.set(self.current_frame)
            
            # Schedule next frame - use optimized update rate
            self.after(self.update_rate, self._animate)
        except Exception as e:
            logger.error(f"Animation error: {e}")
            self.is_playing = False
            self.play_button.config(text="▶ Play")
    
    def _on_frame_changed(self, value):
        """Handle frame slider change - optimized bounds checking"""
        if not self.is_playing:
            frame_idx = int(float(value))
            num_frames = len(self.frames)
            # Optimized bounds check
            if 0 <= frame_idx < num_frames:
                self.current_frame = frame_idx
                self.canvas.update_terrain(self.frames[frame_idx])
                self.frame_label.config(text=f"{frame_idx}/{num_frames - 1}")
    
    def _on_speed_changed(self, value):
        """Handle speed adjustment - optimized conversion"""
        # Clamp and convert value to int for efficiency
        self.update_rate = max(50, min(500, 600 - int(float(value))))  # Invert scale with bounds
