"""
Professional 3D World Machine-Style Terrain Viewer
Advanced real-time visualization with erosion analysis and animation export
"""

import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np
import logging
from typing import Optional, List, Tuple, Dict
import threading
import time
from dataclasses import dataclass

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.cm as cm
    from matplotlib.colors import Normalize
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import new World Machine visualization system
try:
    from backend.services.visualization.themes import (
        WorldMachineVisualizer,
        SimulationAnimationRenderer,
        WorldMachineColorScheme
    )
    WORLD_MACHINE_STYLE_AVAILABLE = True
except ImportError:
    WORLD_MACHINE_STYLE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class UIColors:
    """Professional color scheme"""
    primary_bg = '#0f1419'
    secondary_bg = '#1a1f2e'
    tertiary_bg = '#252d3d'
    accent = '#00d9ff'
    accent_alt = '#00ff88'
    text_primary = '#ffffff'
    text_secondary = '#a0a9b8'
    error = '#ff3366'
    success = '#00ff88'
    warning = '#ffaa00'


class WorldMachine3DViewer:
    """Professional 3D terrain viewer with World Machine-style visualization"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.colors = UIColors()
        
        # Data
        self.current_dem = None
        self.current_erosion = None
        self.animation_data: List[np.ndarray] = []
        
        # Visualization
        self.wm_visualizer = WorldMachineVisualizer() if WORLD_MACHINE_STYLE_AVAILABLE else None
        self.animation_renderer = None
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # Animation control
        self.is_animating = False
        self.current_frame = 0
        self.playback_speed = 0.5  # seconds per frame
        self.animation_thread = None
        
        # UI State
        self.selected_colorscheme = WorldMachineColorScheme.NATURAL if WORLD_MACHINE_STYLE_AVAILABLE else None
        self.show_hillshade = True
        self.show_flow = False
        self.use_advanced_rendering = WORLD_MACHINE_STYLE_AVAILABLE
        
        # Create UI
        self.main_frame = tk.Frame(parent_frame, bg=self.colors.primary_bg)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._build_interface()
        
        logger.info("Initialized Professional World Machine 3D Viewer")
        if WORLD_MACHINE_STYLE_AVAILABLE:
            logger.info("[OK] World Machine Style visualization enabled")
    
    def _build_interface(self):
        """Build the professional UI"""
        # Top toolbar
        self._create_toolbar()
        
        # Main content area
        content_frame = tk.Frame(self.main_frame, bg=self.colors.primary_bg)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Left panel - Controls
        left_panel = tk.Frame(content_frame, bg=self.colors.secondary_bg, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8))
        left_panel.pack_propagate(False)
        
        self._create_left_panel(left_panel)
        
        # Right panel - Viewer
        right_panel = tk.Frame(content_frame, bg=self.colors.primary_bg)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.viewer_frame = tk.Frame(right_panel, bg='#000000')
        self.viewer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create top toolbar"""
        toolbar = tk.Frame(self.main_frame, bg=self.colors.secondary_bg, height=50)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))
        toolbar.pack_propagate(False)
        
        # Title
        title = tk.Label(
            toolbar,
            text="⚡ World Machine 3D Terrain Viewer",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors.secondary_bg,
            fg=self.colors.accent
        )
        title.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Status indicator
        self.status_indicator = tk.Label(
            toolbar,
            text="○ Ready",
            font=("Segoe UI", 9),
            bg=self.colors.secondary_bg,
            fg=self.colors.success
        )
        self.status_indicator.pack(side=tk.LEFT, padx=20)
    
    def _create_left_panel(self, parent):
        """Create left control panel"""
        # Scrollable container
        canvas = tk.Canvas(parent, bg=self.colors.secondary_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors.secondary_bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Visualization Settings
        self._create_section(scrollable_frame, "Visualization", self._create_visualization_controls)
        
        # Color Schemes (if available)
        if WORLD_MACHINE_STYLE_AVAILABLE:
            self._create_section(scrollable_frame, "Color Schemes", self._create_colorscheme_controls)
        
        # Animation
        self._create_section(scrollable_frame, "Animation", self._create_animation_controls)
        
        # Export & Actions
        self._create_section(scrollable_frame, "Export & Actions", self._create_action_buttons)
        
        # Info
        self._create_section(scrollable_frame, "Information", self._create_info_panel)
    
    def _create_section(self, parent, title: str, content_builder):
        """Create a collapsible section"""
        section = tk.Frame(parent, bg=self.colors.secondary_bg)
        section.pack(fill=tk.X, padx=10, pady=8)
        
        # Section header
        header = tk.Frame(section, bg=self.colors.tertiary_bg)
        header.pack(fill=tk.X)
        
        header_label = tk.Label(
            header,
            text=f"▼ {title}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors.tertiary_bg,
            fg=self.colors.accent,
            justify=tk.LEFT
        )
        header_label.pack(fill=tk.X, padx=10, pady=8)
        
        # Content frame
        content = tk.Frame(section, bg=self.colors.secondary_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 5))
        
        content_builder(content)
    
    def _create_visualization_controls(self, parent):
        """Visualization options"""
        # Hillshade toggle
        self.hillshade_var = tk.BooleanVar(value=True)
        hillshade_cb = tk.Checkbutton(
            parent,
            text="Enable Hillshade",
            variable=self.hillshade_var,
            font=("Segoe UI", 9),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_primary,
            selectcolor=self.colors.tertiary_bg,
            activebackground=self.colors.tertiary_bg,
            activeforeground=self.colors.accent,
            command=self.refresh_view
        )
        hillshade_cb.pack(fill=tk.X, padx=10, pady=5)
        
        # Flow visualization toggle
        self.flow_var = tk.BooleanVar(value=False)
        flow_cb = tk.Checkbutton(
            parent,
            text="Show Water Flow",
            variable=self.flow_var,
            font=("Segoe UI", 9),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_primary,
            selectcolor=self.colors.tertiary_bg,
            activebackground=self.colors.tertiary_bg,
            activeforeground=self.colors.accent,
            command=self.refresh_view
        )
        flow_cb.pack(fill=tk.X, padx=10, pady=5)
        
        # Contrast slider
        tk.Label(
            parent,
            text="Contrast:",
            font=("Segoe UI", 8),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_secondary
        ).pack(fill=tk.X, padx=10, pady=(10, 2))
        
        self.contrast_var = tk.DoubleVar(value=1.0)
        contrast_scale = tk.Scale(
            parent,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.contrast_var,
            bg=self.colors.tertiary_bg,
            fg=self.colors.accent,
            highlightthickness=0,
            command=lambda x: self.refresh_view()
        )
        contrast_scale.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _create_colorscheme_controls(self, parent):
        """Color scheme selection"""
        schemes = [
            ("Natural Terrain", "natural"),
            ("Erosion Heat Map", "erosion_heat"),
            ("Geological", "geological"),
            ("Thermal", "thermal"),
            ("Heightmap", "heightmap")
        ]
        
        self.scheme_var = tk.StringVar(value="natural")
        
        for label, value in schemes:
            rb = tk.Radiobutton(
                parent,
                text=label,
                variable=self.scheme_var,
                value=value,
                font=("Segoe UI", 9),
                bg=self.colors.secondary_bg,
                fg=self.colors.text_primary,
                selectcolor=self.colors.tertiary_bg,
                activebackground=self.colors.tertiary_bg,
                activeforeground=self.colors.accent,
                command=self.refresh_view
            )
            rb.pack(fill=tk.X, padx=10, pady=3)
    
    def _create_animation_controls(self, parent):
        """Animation playback controls"""
        # Buttons frame
        btn_frame = tk.Frame(parent, bg=self.colors.secondary_bg)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.play_btn = self._create_button(btn_frame, "▶ Play", self.play_animation, self.colors.success)
        self.play_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.pause_btn = self._create_button(btn_frame, "⏸ Pause", self.pause_animation, self.colors.warning)
        self.pause_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.stop_btn = self._create_button(btn_frame, "⏹ Stop", self.stop_animation, self.colors.error)
        self.stop_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Playback speed
        tk.Label(
            parent,
            text="Playback Speed (s/frame):",
            font=("Segoe UI", 8),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_secondary
        ).pack(fill=tk.X, padx=10, pady=(10, 2))
        
        self.speed_var = tk.DoubleVar(value=0.5)
        speed_scale = tk.Scale(
            parent,
            from_=0.1,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            bg=self.colors.tertiary_bg,
            fg=self.colors.accent,
            highlightthickness=0
        )
        speed_scale.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Frame counter
        self.frame_label = tk.Label(
            parent,
            text="Frames: 0/0",
            font=("Segoe UI", 8),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_secondary
        )
        self.frame_label.pack(fill=tk.X, padx=10, pady=5)
    
    def _create_action_buttons(self, parent):
        """Export and action buttons"""
        self._create_button(
            parent,
            "📸 Save Screenshot",
            self.save_screenshot,
            self.colors.accent
        ).pack(fill=tk.X, padx=10, pady=5)
        
        self._create_button(
            parent,
            "🎬 Export Animation",
            self.export_animation,
            self.colors.accent
        ).pack(fill=tk.X, padx=10, pady=5)
        
        self._create_button(
            parent,
            "🔄 Reset View",
            self.reset_view,
            self.colors.accent
        ).pack(fill=tk.X, padx=10, pady=5)
    
    def _create_info_panel(self, parent):
        """Information display"""
        self.info_text = tk.Label(
            parent,
            text="No data loaded\n\nLoad a DEM to begin",
            font=("Segoe UI", 8),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_secondary,
            justify=tk.LEFT,
            wraplength=250
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_button(self, parent, text: str, command, color: Optional[str] = None) -> tk.Button:
        """Create styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg=color or self.colors.tertiary_bg,
            fg=self.colors.primary_bg if color else self.colors.text_primary,
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2"
        )
        return btn
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_bar = tk.Frame(self.main_frame, bg=self.colors.secondary_bg, height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))
        status_bar.pack_propagate(False)
        
        self.status_text = tk.Label(
            status_bar,
            text="Ready",
            font=("Segoe UI", 8),
            bg=self.colors.secondary_bg,
            fg=self.colors.text_secondary
        )
        self.status_text.pack(side=tk.LEFT, padx=10, pady=4)
    
    # ==================== DATA LOADING ====================
    
    def load_dem(self, dem: np.ndarray) -> bool:
        """Load DEM for visualization (optimized with downsampling for large files)"""
        if dem is None or dem.size == 0:
            logger.warning("Cannot load empty DEM")
            return False
        
        self.current_dem = dem.astype(np.float32)
        self._update_info_panel()
        self.update_status(f"[OK] DEM loaded: {dem.shape[0]}×{dem.shape[1]} pixels")
        
        logger.info(f"Loaded DEM: shape={dem.shape}, min={np.min(dem):.2f}, max={np.max(dem):.2f}")
        
        # For large DEMs, show quick preview first, then full render
        if max(dem.shape) > 2048:
            self.update_status(f"▶ Loading preview of large DEM...")
            # Quick preview with downsampling
            from scipy import ndimage
            preview_dem = ndimage.zoom(dem, (512/dem.shape[0], 512/dem.shape[1]), order=1)
            self.current_dem = preview_dem
            self.render_view()
            # Then render full resolution in background
            self.current_dem = dem
        else:
            self.render_view()
        
        return True
    
    def add_animation_frame(self, dem: np.ndarray):
        """Add frame to animation sequence"""
        if dem is None:
            return
        self.animation_data.append(dem.astype(np.float32))
        self.frame_label.config(text=f"Frames: 0/{len(self.animation_data)}")
        self.update_status(f"Added animation frame {len(self.animation_data)}")
        logger.info(f"Added animation frame {len(self.animation_data)}")
    
    def add_erosion_layer(self, erosion_dem: np.ndarray):
        """Add erosion result for comparison"""
        self.current_erosion = erosion_dem.astype(np.float32)
        logger.info("Added erosion layer for comparison")
    
    # ==================== RENDERING ====================
    
    def render_view(self):
        """Render current DEM in background thread to prevent UI freeze"""
        if self.current_dem is None:
            self.update_status("⚠ No DEM loaded")
            return
        
        # Check if already rendering
        if hasattr(self, '_is_rendering') and self._is_rendering:
            return
        
        self._is_rendering = True
        
        try:
            self.update_status("◆ Rendering...")
            self.parent_frame.update()
            
            # Run rendering in background thread
            render_thread = threading.Thread(
                target=self._render_in_thread,
                daemon=True
            )
            render_thread.start()
        except Exception as e:
            logger.error(f"Render error: {e}")
            self.update_status(f"✗ Render failed: {str(e)[:40]}")
            self._is_rendering = False
    
    def _render_in_thread(self):
        """Perform rendering in background thread"""
        try:
            if WORLD_MACHINE_STYLE_AVAILABLE and self.use_advanced_rendering:
                self._render_advanced()
            else:
                self._render_fallback()
            
            self.update_status("[OK] Render complete")
        except Exception as e:
            logger.error(f"Render error: {e}")
            self.update_status(f"✗ Render failed: {str(e)[:40]}")
        finally:
            self._is_rendering = False
    
    def refresh_view(self):
        """Refresh current view with new settings"""
        if self.current_dem is not None:
            self.render_view()
    
    def _render_advanced(self):
        """Render using World Machine Style visualization"""
        if not self.wm_visualizer or self.current_dem is None:
            self._render_fallback()
            return
        
        try:
            # Get selected color scheme
            scheme_value = self.scheme_var.get()
            try:
                colorscheme = WorldMachineColorScheme(scheme_value)
            except (ValueError, KeyError):
                colorscheme = WorldMachineColorScheme.NATURAL
            
            # Render frame
            dem_data = self.current_dem if self.current_dem is not None else np.zeros((1, 1))
            frame = self.wm_visualizer.render_simulation_frame(
                dem_data,
                timestep=self.current_frame,
                total_timesteps=max(len(self.animation_data), 1),
                colorscheme=colorscheme,
                show_hillshade=self.hillshade_var.get(),
                show_flow=self.flow_var.get()
            )
            
            # Apply contrast adjustment
            contrast = self.contrast_var.get()
            if contrast != 1.0:
                frame = (frame.astype(np.float32) * contrast).clip(0, 255).astype(np.uint8)
            
            # Display
            self._display_frame(frame, colorscheme.value)
            
        except Exception as e:
            logger.warning(f"Advanced render failed: {e}, falling back...")
            self._render_fallback()
    
    def _render_fallback(self):
        """Fallback to basic matplotlib rendering (optimized for speed)"""
        if self.current_dem is None:
            return
        
        try:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            # Use lower DPI for faster rendering
            dpi = 80
            self.fig = Figure(figsize=(10, 8), dpi=dpi, facecolor=self.colors.primary_bg)
            self.ax = self.fig.add_subplot(111)
            
            # Normalize DEM
            dem_display = self.current_dem
            
            # Downsample if too large for smooth interaction
            if max(dem_display.shape) > 1024:
                scale = max(dem_display.shape) / 1024
                from scipy import ndimage
                dem_display = ndimage.zoom(dem_display, (1/scale, 1/scale), order=1)
            
            dem_norm = (dem_display - np.min(dem_display)) / (np.max(dem_display) - np.min(dem_display) + 1e-8)
            
            # Create color mapping with fewer colors for speed
            im = self.ax.imshow(dem_norm, cmap='terrain', aspect='auto', interpolation='bilinear')
            
            self.ax.set_title('Terrain Visualization', color=self.colors.accent, fontsize=12, fontweight='bold')
            self.ax.axis('off')
            
            # Add colorbar
            cbar = self.fig.colorbar(im, ax=self.ax, shrink=0.8)
            cbar.ax.tick_params(colors=self.colors.text_secondary)
            
            # Create canvas with optimizations
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.viewer_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Fallback render error: {e}")
    
    def _display_frame(self, frame: np.ndarray, scheme_name: str):
        """Display rendered frame"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        self.fig = Figure(figsize=(10, 8), dpi=90, facecolor=self.colors.primary_bg)
        self.ax = self.fig.add_subplot(111)
        
        self.ax.imshow(frame)
        self.ax.set_title(f'Terrain {scheme_name.title()} Color Scheme', 
                         color=self.colors.accent, fontsize=12, fontweight='bold')
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viewer_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    # ==================== ANIMATION ====================
    
    def play_animation(self):
        """Play animation sequence"""
        if not self.animation_data:
            self.update_status("⚠ No animation frames loaded")
            return
        
        if self.is_animating:
            return
        
        self.is_animating = True
        self.current_frame = 0
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Initialize renderer for GIF export
        if WORLD_MACHINE_STYLE_AVAILABLE:
            scheme_value = self.scheme_var.get()
            try:
                colorscheme = WorldMachineColorScheme(scheme_value)
            except (ValueError, KeyError):
                colorscheme = WorldMachineColorScheme.NATURAL
            self.animation_renderer = SimulationAnimationRenderer(colorscheme=colorscheme)
        
        self.animation_thread = threading.Thread(target=self._animate_loop, daemon=True)
        self.animation_thread.start()
        self.update_status("▶ Animation playing...")
    
    def _animate_loop(self):
        """Animation loop"""
        while self.is_animating and self.current_frame < len(self.animation_data):
            dem = self.animation_data[self.current_frame]
            self.current_dem = dem
            
            # Add to renderer for export
            if self.animation_renderer:
                self.animation_renderer.add_snapshot(
                    dem,
                    timestep=self.current_frame,
                    total_timesteps=len(self.animation_data)
                )
            
            self.frame_label.config(text=f"Frames: {self.current_frame + 1}/{len(self.animation_data)}")
            self.render_view()
            self.current_frame += 1
            
            time.sleep(self.speed_var.get())
            self.parent_frame.update()
        
        if self.current_frame >= len(self.animation_data):
            self.is_animating = False
            self.play_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.update_status("[OK] Animation finished")
    
    def pause_animation(self):
        """Pause animation"""
        self.is_animating = False
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.update_status("⏸ Animation paused")
        logger.info("Animation paused")
    
    def stop_animation(self):
        """Stop animation"""
        self.is_animating = False
        self.current_frame = 0
        self.frame_label.config(text=f"Frames: 0/{len(self.animation_data)}")
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.animation_data:
            self.current_dem = self.animation_data[0]
            self.render_view()
        
        self.update_status("⏹ Animation stopped")
        logger.info("Animation stopped")
    
    # ==================== EXPORT ====================
    
    def save_screenshot(self):
        """Save current view as PNG"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        try:
            filename = f"screenshot_{int(time.time())}.png"
            if self.fig:
                self.fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor=self.colors.primary_bg)
            logger.info(f"Screenshot saved: {filename}")
            self.update_status(f"[OK] Saved: {filename}")
            messagebox.showinfo("Success", f"Screenshot saved as\n{filename}")
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            messagebox.showerror("Error", f"Failed to save screenshot: {e}")
    
    def export_animation(self):
        """Export animation as GIF"""
        if not self.animation_data:
            messagebox.showwarning("Warning", "No animation to export")
            return
        
        if not WORLD_MACHINE_STYLE_AVAILABLE or not self.animation_renderer:
            messagebox.showwarning("Notice", "Animation renderer not available")
            return
        
        try:
            filename = f"animation_{int(time.time())}.gif"
            self.update_status("[OK] Exporting GIF...")
            self.parent_frame.update()
            
            self.animation_renderer.save_animation(filename, duration_per_frame=int(self.speed_var.get() * 1000))
            
            logger.info(f"Animation exported: {filename}")
            self.update_status(f"[OK] Animation saved: {filename}")
            messagebox.showinfo("Success", f"Animation exported as\n{filename}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def export_view(self):
        """Export current view"""
        self.save_screenshot()
    
    # ==================== UTILITIES ====================
    
    def reset_view(self):
        """Reset all settings to defaults"""
        self.hillshade_var.set(True)
        self.flow_var.set(False)
        self.contrast_var.set(1.0)
        self.scheme_var.set("natural")
        self.speed_var.set(0.5)
        self.current_frame = 0
        self.frame_label.config(text=f"Frames: 0/{len(self.animation_data)}")
        self.render_view()
        self.update_status("[OK] Settings reset")
        logger.info("Settings reset to defaults")
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_text.config(text=message)
    
    def _update_info_panel(self):
        """Update information panel"""
        if self.current_dem is None:
            info = "No data loaded\n\nLoad a DEM to begin"
        else:
            h, w = self.current_dem.shape
            min_val = np.min(self.current_dem)
            max_val = np.max(self.current_dem)
            mean_val = np.mean(self.current_dem)
            
            info = f"""Terrain Data:
Size: {w}×{h}
Range: {min_val:.1f}–{max_val:.1f}m
Mean: {mean_val:.1f}m

Frames: {len(self.animation_data)}"""
        
        self.info_text.config(text=info)
    
    def get_animation_status(self) -> Dict:
        """Get animation playback status"""
        return {
            'is_playing': self.is_animating,
            'current_frame': self.current_frame,
            'total_frames': len(self.animation_data)
        }
