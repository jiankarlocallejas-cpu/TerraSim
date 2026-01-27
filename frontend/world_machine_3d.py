"""
3D World Machine-like Terrain Simulator Viewer
Real-time 3D visualization of terrain evolution with erosion effects
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import logging
from typing import Optional, List, Tuple
import threading
import time

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.cm as cm
    from matplotlib.colors import Normalize
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import moderngl
    from PIL import Image
    import ctypes
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False

logger = logging.getLogger(__name__)


class WorldMachine3DViewer:
    """3D terrain viewer with World Machine-style visualization"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.current_dem = None
        self.current_erosion = None
        
        # Create main frame
        self.main_frame = tk.Frame(parent_frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controls frame
        self._create_controls_frame()
        
        # Viewer frame
        self.viewer_frame = tk.Frame(self.main_frame, bg='black')
        self.viewer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Matplotlib figure for 3D visualization
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # Animation state
        self.is_animating = False
        self.animation_data = []
        self.current_frame = 0
        
        logger.info("Initialized World Machine 3D Viewer")
    
    def _create_controls_frame(self):
        """Create control panel"""
        ctrl_frame = tk.Frame(self.main_frame, bg='#2d2d44', height=80)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        ctrl_frame.pack_propagate(False)
        
        # Left group - View controls
        left_group = tk.LabelFrame(
            ctrl_frame,
            text="View Controls",
            bg='#2d2d44',
            fg='#00d4ff',
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        )
        left_group.pack(side=tk.LEFT, padx=5, fill=tk.X)
        
        tk.Button(left_group, text="🔄 Reset View", command=self.reset_view, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(left_group, text="💾 Export", command=self.export_view, width=12).pack(side=tk.LEFT, padx=2)
        
        # Middle group - Animation controls
        mid_group = tk.LabelFrame(
            ctrl_frame,
            text="Animation",
            bg='#2d2d44',
            fg='#00d4ff',
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        )
        mid_group.pack(side=tk.LEFT, padx=5, fill=tk.X)
        
        tk.Button(mid_group, text="▶️  Play", command=self.play_animation, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(mid_group, text="⏸️  Pause", command=self.pause_animation, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(mid_group, text="⏹️  Stop", command=self.stop_animation, width=10).pack(side=tk.LEFT, padx=2)
        
        # Right group - Rendering options
        right_group = tk.LabelFrame(
            ctrl_frame,
            text="Rendering",
            bg='#2d2d44',
            fg='#00d4ff',
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        )
        right_group.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.shading_var = tk.StringVar(value="hillshade")
        tk.OptionMenu(
            right_group,
            self.shading_var,
            "elevation",
            "hillshade",
            "slope",
            "aspect"
        ).pack(side=tk.LEFT, padx=2)
        
        self.wireframe_var = tk.BooleanVar()
        tk.Checkbutton(
            right_group,
            text="Wireframe",
            variable=self.wireframe_var,
            bg='#2d2d44',
            fg='#ffffff'
        ).pack(side=tk.LEFT, padx=2)
    
    def load_dem(self, dem: np.ndarray):
        """Load DEM for visualization"""
        if dem is None or len(dem) == 0:
            logger.warning("Cannot load empty DEM")
            return False
        
        self.current_dem = dem.astype(np.float32)
        logger.info(f"Loaded DEM: shape={dem.shape}, min={np.min(dem):.2f}, max={np.max(dem):.2f}")
        self.visualize_3d()
        return True
    
    def visualize_3d(self):
        """Render 3D terrain"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        try:
            # Clear previous canvas
            if self.canvas is not None:
                self.canvas.get_tk_widget().destroy()
            
            # Create new figure
            self.fig = Figure(figsize=(8, 6), dpi=100)
            self.ax = self.fig.add_subplot(111, projection='3d')
            
            # Create mesh
            h, w = self.current_dem.shape
            x = np.arange(0, w, 1)
            y = np.arange(0, h, 1)
            x, y = np.meshgrid(x, y)
            z = self.current_dem
            
            # Apply shading
            shading_mode = self.shading_var.get()
            colors = self._get_colors(shading_mode)
            
            # Plot surface
            if self.wireframe_var.get():
                self.ax.plot_wireframe(
                    x, y, z,
                    color='cyan',
                    alpha=0.6,
                    linewidth=0.5
                )
            else:
                self.ax.plot_surface(
                    x, y, z,
                    facecolors=colors,
                    shade=False,
                    rstride=1,
                    cstride=1
                )
            
            # Setup
            self.ax.set_xlabel('X (cells)')
            self.ax.set_ylabel('Y (cells)')
            self.ax.set_zlabel('Elevation (m)')
            self.ax.set_title('3D Terrain - World Machine Simulator')
            
            # Set viewing angle
            self.ax.view_init(elev=25, azim=45)
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.viewer_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()
            
            logger.info("Rendered 3D visualization")
        except Exception as e:
            logger.error(f"Error rendering 3D: {e}")
            messagebox.showerror("Error", f"Failed to render 3D: {e}")
    
    def _get_colors(self, mode: str) -> np.ndarray:
        """Get color array based on shading mode"""
        from matplotlib.colors import Normalize
        import matplotlib.cm as cm
        h, w = self.current_dem.shape
        
        if mode == "elevation":
            # Color by elevation
            norm = Normalize(vmin=np.min(self.current_dem), vmax=np.max(self.current_dem))
            colors = cm.terrain(norm(self.current_dem))  # type: ignore
        
        elif mode == "hillshade":
            # Hillshade coloring
            from scipy.ndimage import sobel
            
            gy = sobel(self.current_dem, axis=0)
            gx = sobel(self.current_dem, axis=1)
            
            # Light direction
            x = np.sin(np.radians(315)) * np.cos(np.radians(45))
            y = np.cos(np.radians(315)) * np.cos(np.radians(45))
            z = np.sin(np.radians(45))
            
            # Normalize gradients
            gx_norm = gx / (np.sqrt(gx**2 + gy**2 + 1) + 1e-8)
            gy_norm = gy / (np.sqrt(gx**2 + gy**2 + 1) + 1e-8)
            gz_norm = 1 / (np.sqrt(gx**2 + gy**2 + 1) + 1e-8)
            
            # Compute shading
            shading = gx_norm * x + gy_norm * y + gz_norm * z
            shading = (shading + 1) / 2
            
            # Apply terrain colors with shading
            norm = Normalize(vmin=0, vmax=1)
            shading_colors = cm.Greys(norm(shading))  # type: ignore
            elevation_colors = cm.terrain(norm(self.current_dem/np.max(self.current_dem)))  # type: ignore
            
            # Blend
            colors = 0.5 * elevation_colors + 0.5 * shading_colors
        
        elif mode == "slope":
            # Color by slope
            gy, gx = np.gradient(self.current_dem)
            slope = np.arctan(np.sqrt(gx**2 + gy**2))
            norm = Normalize(vmin=0, vmax=np.pi/4)
            colors = cm.hot(norm(slope))  # type: ignore
        
        else:  # aspect
            # Color by aspect
            gy, gx = np.gradient(self.current_dem)
            aspect = np.arctan2(gy, -gx)
            aspect = (aspect + np.pi) / (2 * np.pi)
            norm = Normalize(vmin=0, vmax=1)
            colors = cm.hsv(norm(aspect))  # type: ignore
        
        return colors
    
    def add_erosion_layer(self, erosion_dem: np.ndarray):
        """Add erosion result for comparison"""
        self.current_erosion = erosion_dem.astype(np.float32)
        logger.info("Added erosion layer for comparison")
    
    def add_animation_frame(self, dem: np.ndarray):
        """Add frame to animation sequence"""
        self.animation_data.append(dem.astype(np.float32))
        logger.info(f"Added animation frame {len(self.animation_data)}")
    
    def play_animation(self):
        """Play terrain evolution animation"""
        if not self.animation_data:
            messagebox.showwarning("Warning", "No animation frames loaded")
            return
        
        self.is_animating = True
        self.current_frame = 0
        
        def animate():
            while self.is_animating and self.current_frame < len(self.animation_data):
                self.current_dem = self.animation_data[self.current_frame]
                self.visualize_3d()
                self.current_frame += 1
                time.sleep(0.5)  # 0.5s per frame
                self.parent_frame.update()
        
        thread = threading.Thread(target=animate, daemon=True)
        thread.start()
    
    def pause_animation(self):
        """Pause animation"""
        self.is_animating = False
        logger.info("Animation paused")
    
    def stop_animation(self):
        """Stop animation"""
        self.is_animating = False
        self.current_frame = 0
        if self.animation_data:
            self.current_dem = self.animation_data[0]
            self.visualize_3d()
        logger.info("Animation stopped")
    
    def reset_view(self):
        """Reset viewing angle"""
        if self.ax is not None:
            self.ax.view_init(elev=25, azim=45)
            self.canvas.draw()
    
    def export_view(self):
        """Export current view"""
        try:
            if self.canvas is not None:
                filename = f"terrain_3d_{int(time.time())}.png"
                self.fig.savefig(filename, dpi=150, bbox_inches='tight')
                logger.info(f"Exported 3D view to {filename}")
                messagebox.showinfo("Success", f"Exported to {filename}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def get_animation_status(self) -> dict:
        """Get current animation status"""
        return {
            'is_animating': self.is_animating,
            'current_frame': self.current_frame,
            'total_frames': len(self.animation_data)
        }
