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
        """Render 2D data as heatmap"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.cm as cm
            from PIL import Image, ImageTk
            
            # Create figure
            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            
            # Plot heatmap
            im = ax.imshow(data, cmap=colormap, origin='upper')
            ax.set_title(f"Terrain/Erosion Map")
            plt.colorbar(im, ax=ax)
            
            # Convert to PIL image
            fig.canvas.draw()
            image_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)  # type: ignore
            image_data = image_data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            
            pil_image = Image.fromarray(image_data)
            pil_image = pil_image.resize((self.width, self.height))
            
            # Display on canvas
            self.image = ImageTk.PhotoImage(pil_image)
            self.create_image(0, 0, image=self.image, anchor='nw')
            
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Error rendering heatmap: {e}")
            # Fallback: simple gradient
            self._render_gradient(data)
    
    def _render_gradient(self, data: np.ndarray):
        """Fallback: render simple gradient"""
        normalized = (data - data.min()) / (data.max() - data.min() + 1e-6)
        
        # Simple colormap
        height, width = normalized.shape
        scale_x = self.width / width
        scale_y = self.height / height
        
        self.delete("all")
        
        for i in range(height):
            for j in range(width):
                value = normalized[i, j]
                # Hot colormap
                r = int(255 * min(value * 2, 1.0))
                g = int(255 * max(0, min(value * 2 - 1, 1.0)))
                b = int(255 * max(0, 1 - value * 2))
                
                color = f'#{r:02x}{g:02x}{b:02x}'
                
                x1 = j * scale_x
                y1 = i * scale_y
                x2 = x1 + scale_x + 1
                y2 = y1 + scale_y + 1
                
                self.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)


class OpenGLVisualizationWidget(tk.Frame):
    """Complete widget for OpenGL-based terrain/erosion visualization"""
    
    def __init__(self, parent, dem: np.ndarray, **kwargs):
        super().__init__(parent, bg='white', **kwargs)
        
        self.dem = dem.copy()
        self.current_dem = dem.copy()
        self.erosion_data = None
        self.is_updating = False
        
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
        self.colormap_var = tk.StringVar(value="viridis")
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
        """Handle colormap selection change"""
        self._update_visualization()
    
    def _update_visualization(self):
        """Update the canvas visualization"""
        colormap = self.colormap_var.get()
        self.canvas.update_terrain(self.current_dem, colormap)
    
    def update_dem(self, dem: np.ndarray):
        """Update DEM and redraw"""
        self.current_dem = dem.copy()
        self._update_visualization()
    
    def set_erosion_overlay(self, erosion_data: np.ndarray):
        """Set erosion data for overlay visualization"""
        self.erosion_data = erosion_data.copy()


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
        """Add a frame to the animation"""
        self.frames.append(dem.copy())
        self.frame_slider.config(to=len(self.frames) - 1)
    
    def _toggle_playback(self):
        """Toggle playback"""
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸ Pause" if self.is_playing else "▶ Play")
        
        if self.is_playing:
            self._animate()
    
    def _animate(self):
        """Animation loop"""
        if not self.is_playing or self.current_frame >= len(self.frames) - 1:
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            return
        
        self.current_frame += 1
        self.frame_slider.set(self.current_frame)
        
        self.after(self.update_rate, self._animate)
    
    def _on_frame_changed(self, value):
        """Handle frame slider change"""
        if not self.is_playing:
            self.current_frame = int(value)
            if 0 <= self.current_frame < len(self.frames):
                self.canvas.update_terrain(self.frames[self.current_frame])
                self.frame_label.config(text=f"{self.current_frame}/{len(self.frames)-1}")
    
    def _on_speed_changed(self, value):
        """Handle speed adjustment"""
        self.update_rate = 600 - int(value)  # Invert scale
