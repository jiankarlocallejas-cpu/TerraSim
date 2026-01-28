"""
Revamped TerraSim Main Window - GIS-Style Interface
Integrates GIS canvas, map data extraction, and 3D World Machine simulator
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import logging
import threading
from typing import Optional
from datetime import datetime

# Import custom components
from .gis_canvas import GISCanvas
from .world_machine_3d import WorldMachine3DViewer
from backend.services.map_data_extractor import MapDataExtractor, MapDataType
from backend.services.simulation_engine import get_simulation_engine, SimulationParameters, SimulationMode
from backend.services.terrain_simulator import TerrainSimulator, TimeStepParameters

logger = logging.getLogger(__name__)


class TerraSim_GIS(tk.Tk):
    """Revamped TerraSim with GIS-style interface"""
    
    def __init__(self):
        super().__init__()
        
        self.title("TerraSim - GIS Terrain Simulation System")
        self.geometry("1600x1000")
        self.resizable(True, True)
        
        # State
        self.current_dem = None
        self.current_dem_path = None
        self.map_extractor = None
        self.sim_engine = get_simulation_engine()
        
        # Color scheme
        self.primary_bg = '#1e1e2e'
        self.secondary_bg = '#2d2d44'
        self.accent_color = '#00d4ff'
        self.text_color = '#ffffff'
        
        logger.info("Initializing TerraSim GIS Interface")
        self._create_interface()
    
    def _create_interface(self):
        """Create main GIS interface"""
        self.configure(bg=self.primary_bg)
        
        # Top menu
        self._create_menu_bar()
        
        # Main layout - Left sidebar, center content, right inspector
        main_container = tk.Frame(self, bg=self.primary_bg)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ==================== LEFT SIDEBAR ====================
        left_sidebar = tk.Frame(main_container, bg=self.secondary_bg, width=250)
        left_sidebar.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_sidebar.pack_propagate(False)
        
        # Layer panel
        self._create_layer_panel(left_sidebar)
        
        # ==================== CENTER AREA ====================
        center_area = tk.Frame(main_container)
        center_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Tabbed interface
        self.notebook = ttk.Notebook(center_area)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: 2D GIS Map
        map_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(map_frame, text="🗺️  2D Map")
        self.gis_canvas = GISCanvas(map_frame, width=800, height=600)
        
        # Tab 2: 3D World Machine Viewer
        viewer_frame = tk.Frame(self.notebook, bg='black')
        self.notebook.add(viewer_frame, text="🗻 3D Simulator")
        self.world_machine_viewer = WorldMachine3DViewer(viewer_frame)
        
        # Tab 3: Analysis Results
        analysis_frame = tk.Frame(self.notebook, bg=self.primary_bg)
        self.notebook.add(analysis_frame, text="📊 Analysis")
        self._create_analysis_tab(analysis_frame)
        
        # ==================== RIGHT SIDEBAR ====================
        right_sidebar = tk.Frame(main_container, bg=self.secondary_bg, width=300)
        right_sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_sidebar.pack_propagate(False)
        
        # Inspector/Properties panel
        self._create_inspector_panel(right_sidebar)
        
        # Status bar
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """Create menu bar with all options"""
        menubar = tk.Menu(self, bg=self.secondary_bg, fg=self.text_color)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="📁 Load DEM", command=self.load_dem)
        file_menu.add_command(label="📂 Load Shapefile", command=self.load_shapefile)
        file_menu.add_separator()
        file_menu.add_command(label="💾 Export Map", command=self.export_map)
        file_menu.add_command(label="📤 Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="🎲 Generate Sample DEM", command=self.generate_sample_dem)
        data_menu.add_command(label="📊 Extract Map Data", command=self.extract_map_data)
        data_menu.add_separator()
        data_menu.add_command(label="🔄 Reproject", command=self.show_reproject_dialog)
        data_menu.add_command(label="✂️  Clip", command=self.show_clip_dialog)
        
        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="▶️  Quick Run", command=self.run_quick_simulation)
        sim_menu.add_command(label="📈 Time Series", command=self.run_time_series)
        sim_menu.add_command(label="🔬 Sensitivity", command=self.run_sensitivity)
        sim_menu.add_separator()
        sim_menu.add_command(label="⚙️  Parameters", command=self.show_parameters_dialog)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="📐 Slope", command=self.compute_slope)
        analysis_menu.add_command(label="🌊 Flow Accumulation", command=self.compute_flow)
        analysis_menu.add_command(label="⛰️  Aspect", command=self.compute_aspect)
        analysis_menu.add_command(label="📏 Curvature", command=self.compute_curvature)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="📋 Statistics", command=self.show_statistics)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="🔍 Measure", command=self.show_measure_tool)
        tools_menu.add_separator()
        tools_menu.add_command(label="⚙️  Preferences", command=self.show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.secondary_bg, fg=self.text_color)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📖 About", command=self.show_about)
    
    def _create_layer_panel(self, parent):
        """Create layer management panel"""
        panel = tk.LabelFrame(
            parent,
            text="Layers",
            bg=self.secondary_bg,
            fg=self.accent_color,
            font=("Arial", 9, "bold"),
            padx=5,
            pady=5
        )
        panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Layer listbox
        self.layer_listbox = tk.Listbox(
            panel,
            bg='#1e1e2e',
            fg=self.text_color,
            selectmode=tk.SINGLE,
            height=15
        )
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind('<<ListboxSelect>>', self._on_layer_select)
        
        # Layer controls
        ctrl_frame = tk.Frame(panel, bg=self.secondary_bg)
        ctrl_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            ctrl_frame,
            text="➕ Add",
            command=self.add_layer_dialog,
            bg='#3d3d5c',
            fg=self.text_color,
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            ctrl_frame,
            text="❌ Remove",
            command=self.remove_layer,
            bg='#3d3d5c',
            fg=self.text_color,
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            ctrl_frame,
            text="👁️  Toggle",
            command=self.toggle_layer_visibility,
            bg='#3d3d5c',
            fg=self.text_color,
            width=8
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_inspector_panel(self, parent):
        """Create properties/inspector panel"""
        # Info panel
        info_panel = tk.LabelFrame(
            parent,
            text="DEM Information",
            bg=self.secondary_bg,
            fg=self.accent_color,
            font=("Arial", 9, "bold"),
            padx=5,
            pady=5
        )
        info_panel.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.info_text = tk.Text(
            info_panel,
            bg='#1e1e2e',
            fg=self.text_color,
            height=10,
            width=30,
            font=("Courier", 8)
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Layer properties
        props_panel = tk.LabelFrame(
            parent,
            text="Layer Properties",
            bg=self.secondary_bg,
            fg=self.accent_color,
            font=("Arial", 9, "bold"),
            padx=5,
            pady=5
        )
        props_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(
            props_panel,
            text="Opacity:",
            bg=self.secondary_bg,
            fg=self.text_color
        ).pack(anchor=tk.W, pady=(5, 0))
        
        self.opacity_scale = tk.Scale(
            props_panel,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            bg='#3d3d5c',
            fg=self.text_color,
            command=self._on_opacity_change
        )
        self.opacity_scale.set(80)
        self.opacity_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Quick stats
        stats_frame = tk.Frame(props_panel, bg=self.secondary_bg)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = tk.Text(
            stats_frame,
            bg='#1e1e2e',
            fg=self.text_color,
            height=8,
            width=30,
            font=("Courier", 8)
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_analysis_tab(self, parent):
        """Create analysis results tab"""
        frame = tk.Frame(parent, bg=self.primary_bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(
            frame,
            text="Analysis Results",
            bg=self.primary_bg,
            fg=self.accent_color,
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.analysis_text = tk.Text(
            frame,
            bg='#1e1e2e',
            fg=self.text_color,
            font=("Courier", 9)
        )
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = tk.Frame(self, bg=self.secondary_bg, height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            bg=self.secondary_bg,
            fg=self.text_color,
            font=("Arial", 9),
            anchor=tk.W,
            padx=10
        )
        self.status_label.pack(fill=tk.BOTH, expand=True)
    
    # ==================== FILE OPERATIONS ====================
    
    def load_dem(self):
        """Load DEM from file"""
        filepath = filedialog.askopenfilename(
            title="Load DEM",
            filetypes=[("GeoTIFF", "*.tif"), ("NumPy", "*.npy"), ("All", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.tif'):
                import rasterio
                with rasterio.open(filepath) as src:
                    self.current_dem = src.read(1).astype(np.float32)
            else:  # .npy
                self.current_dem = np.load(filepath).astype(np.float32)
            
            self.current_dem_path = filepath
            self.map_extractor = MapDataExtractor(self.current_dem)
            
            # Update UI
            self.gis_canvas.add_dem_layer(self.current_dem, 'DEM')
            self.world_machine_viewer.load_dem(self.current_dem)
            self._update_info_panel()
            
            self._set_status(f"Loaded DEM: {filepath}")
            logger.info(f"Loaded DEM from {filepath}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DEM: {e}")
            logger.error(f"Error loading DEM: {e}")
    
    def load_shapefile(self):
        """Load shapefile"""
        filepath = filedialog.askopenfilename(
            title="Load Shapefile",
            filetypes=[("Shapefiles", "*.shp")]
        )
        
        if not filepath:
            return
        
        try:
            import geopandas as gpd
            gdf = gpd.read_file(filepath)
            layer_name = str(gdf.name) if gdf.name is not None else 'Vector'
            self.gis_canvas.add_vector_layer(gdf.geometry, name=layer_name)
            self._set_status(f"Loaded Shapefile: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shapefile: {e}")
    
    def export_map(self):
        """Export map view"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        
        if filepath:
            self.gis_canvas.export_current_view(filepath)
            self._set_status(f"Exported map to {filepath}")
    
    def export_data(self):
        """Export analysis data"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".npy",
            filetypes=[("NumPy", "*.npy"), ("GeoTIFF", "*.tif")]
        )
        
        if filepath:
            np.save(filepath, self.current_dem)
            self._set_status(f"Exported data to {filepath}")
    
    # ==================== DATA OPERATIONS ====================
    
    def generate_sample_dem(self):
        """Generate sample DEM"""
        try:
            from scipy.ndimage import gaussian_filter
            
            size = 256
            dem = np.random.rand(size, size) * 100
            dem = gaussian_filter(dem, sigma=10)
            
            self.current_dem = dem.astype(np.float32)
            self.map_extractor = MapDataExtractor(self.current_dem)
            
            self.gis_canvas.add_dem_layer(self.current_dem, 'Sample DEM')
            self.world_machine_viewer.load_dem(self.current_dem)
            self._update_info_panel()
            
            self._set_status("Generated sample DEM")
            logger.info("Generated sample DEM")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate DEM: {e}")
    
    def extract_map_data(self):
        """Extract all map layers from DEM"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        try:
            self._set_status("Extracting map data...")
            self.update()
            
            if self.map_extractor is None:
                self.map_extractor = MapDataExtractor(self.current_dem)
            
            # Extract data
            slope = self.map_extractor.extract_slope()
            aspect = self.map_extractor.extract_aspect()
            hillshade = self.map_extractor.extract_hillshade()
            curvature = self.map_extractor.extract_curvature()
            tpi = self.map_extractor.extract_topographic_position()
            
            # Add to canvas
            self.gis_canvas.add_analysis_layer(slope, 'Slope', 'hot')
            self.gis_canvas.add_analysis_layer(aspect, 'Aspect', 'hsv')
            self.gis_canvas.add_analysis_layer(hillshade, 'Hillshade', 'gray')
            self.gis_canvas.add_analysis_layer(curvature, 'Curvature', 'RdBu')
            self.gis_canvas.add_analysis_layer(tpi, 'TPI', 'terrain')
            
            # Update layer list
            self._update_layer_list()
            
            self._set_status("Map data extracted successfully")
            messagebox.showinfo("Success", "All map layers extracted!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed: {e}")
            logger.error(f"Error extracting map data: {e}")
    
    # ==================== SIMULATION OPERATIONS ====================
    
    def run_quick_simulation(self):
        """Run quick simulation"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        try:
            self._set_status("Running simulation...")
            self.update()
            
            # Simple simulation
            from backend.services.terrain_simulator import TerrainSimulator
            simulator = TerrainSimulator(self.current_dem, cell_size=1.0)
            results = simulator.run_simulation()
            
            if results and len(results) > 0:
                # Add all frames to animation viewer
                for snapshot in results:
                    self.world_machine_viewer.add_animation_frame(snapshot.elevation)
                
                # Add final erosion result to 3D viewer
                final_snapshot = results[-1]
                self.world_machine_viewer.add_erosion_layer(final_snapshot.elevation)
                
                # Render initial frame
                self.world_machine_viewer.render_view()
                
                self._set_status(f"✓ Simulation complete ({len(results)} frames)")
                messagebox.showinfo("Success", f"Simulation completed!\n{len(results)} frames captured")
            
        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {e}")
            logger.error(f"Error running simulation: {e}")
    
    def run_time_series(self):
        """Run time series simulation"""
        messagebox.showinfo("Info", "Time series simulation coming soon")
    
    def run_sensitivity(self):
        """Run sensitivity analysis"""
        messagebox.showinfo("Info", "Sensitivity analysis coming soon")
    
    # ==================== ANALYSIS OPERATIONS ====================
    
    def compute_slope(self):
        """Compute and display slope"""
        if self.map_extractor is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        slope = self.map_extractor.extract_slope()
        self.gis_canvas.add_analysis_layer(slope, 'Slope', 'hot')
        self._update_layer_list()
        self._set_status("Slope computed")
    
    def compute_aspect(self):
        """Compute and display aspect"""
        if self.map_extractor is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        aspect = self.map_extractor.extract_aspect()
        self.gis_canvas.add_analysis_layer(aspect, 'Aspect', 'hsv')
        self._update_layer_list()
        self._set_status("Aspect computed")
    
    def compute_flow(self):
        """Compute flow accumulation"""
        if self.map_extractor is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        flow = self.map_extractor.extract_flow_accumulation()
        self.gis_canvas.add_analysis_layer(flow, 'Flow Accumulation', 'Blues')
        self._update_layer_list()
        self._set_status("Flow accumulation computed")
    
    def compute_curvature(self):
        """Compute curvature"""
        if self.map_extractor is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        curvature = self.map_extractor.extract_curvature()
        self.gis_canvas.add_analysis_layer(curvature, 'Curvature', 'RdBu')
        self._update_layer_list()
        self._set_status("Curvature computed")
    
    def show_statistics(self):
        """Show DEM statistics"""
        if self.map_extractor is None:
            messagebox.showwarning("Warning", "No DEM loaded")
            return
        
        stats = self.map_extractor.get_statistics()
        
        text = "=== DEM Statistics ===\n\n"
        text += f"Elevation (m):\n"
        text += f"  Min: {stats['elevation_min']:.2f}\n"
        text += f"  Max: {stats['elevation_max']:.2f}\n"
        text += f"  Mean: {stats['elevation_mean']:.2f}\n"
        text += f"  Std Dev: {stats['elevation_std']:.2f}\n\n"
        text += f"Slope (degrees):\n"
        text += f"  Mean: {stats['slope_mean']:.2f}\n"
        text += f"  Max: {stats['slope_max']:.2f}\n"
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, text)
        self.stats_text.config(state=tk.DISABLED)
    
    # ==================== DIALOGS ====================
    
    def add_layer_dialog(self):
        """Show add layer dialog"""
        messagebox.showinfo("Info", "Use menu options to add layers")
    
    def remove_layer(self):
        """Remove selected layer"""
        selection = self.layer_listbox.curselection()
        if selection:
            idx = selection[0]
            layer_name = self.layer_listbox.get(idx)
            self.gis_canvas.remove_layer(layer_name)
            self._update_layer_list()
    
    def toggle_layer_visibility(self):
        """Toggle selected layer visibility"""
        selection = self.layer_listbox.curselection()
        if selection:
            idx = selection[0]
            layer_name = self.layer_listbox.get(idx)
            self.gis_canvas.toggle_layer_visibility(layer_name)
            self.gis_canvas.render()
    
    def show_parameters_dialog(self):
        """Show simulation parameters dialog"""
        messagebox.showinfo("Info", "Parameters dialog coming soon")
    
    def show_reproject_dialog(self):
        """Show reprojection dialog"""
        messagebox.showinfo("Info", "Reprojection coming soon")
    
    def show_clip_dialog(self):
        """Show clip dialog"""
        messagebox.showinfo("Info", "Clipping coming soon")
    
    def show_measure_tool(self):
        """Show measure tool"""
        messagebox.showinfo("Info", "Measure tool coming soon")
    
    def show_preferences(self):
        """Show preferences"""
        messagebox.showinfo("Info", "Preferences coming soon")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """TerraSim - GIS Terrain Simulation System
        
Advanced erosion modeling with GIS-style interface
- 2D map visualization
- 3D World Machine-like simulator
- Comprehensive analysis tools
- Real-time terrain evolution

Version 2.0 - 2026"""
        messagebox.showinfo("About TerraSim", about_text)
    
    # ==================== UTILITY METHODS ====================
    
    def _update_layer_list(self):
        """Update layer listbox"""
        layers = self.gis_canvas.get_layer_list()
        self.layer_listbox.delete(0, tk.END)
        for layer in layers:
            self.layer_listbox.insert(tk.END, layer)
    
    def _on_layer_select(self, event):
        """Handle layer selection"""
        selection = self.layer_listbox.curselection()
        if selection:
            layer_name = self.layer_listbox.get(selection[0])
            info = self.gis_canvas.get_layer_info(layer_name)
            if info:
                self._update_stats_display(info)
    
    def _update_info_panel(self):
        """Update DEM info panel"""
        if self.current_dem is None:
            return
        
        text = "=== DEM Information ===\n\n"
        text += f"Shape: {self.current_dem.shape}\n"
        text += f"Min: {np.min(self.current_dem):.2f} m\n"
        text += f"Max: {np.max(self.current_dem):.2f} m\n"
        text += f"Mean: {np.mean(self.current_dem):.2f} m\n"
        text += f"Std Dev: {np.std(self.current_dem):.2f} m\n"
        text += f"\nLoaded: {self.current_dem_path or 'Generated'}\n"
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.config(state=tk.DISABLED)
    
    def _update_stats_display(self, info):
        """Update stats display for selected layer"""
        text = f"=== {info['name']} ===\n\n"
        text += f"Type: {info['type']}\n"
        text += f"Visible: {info['visible']}\n"
        text += f"Opacity: {info.get('alpha', 1.0):.2%}\n"
        
        if 'shape' in info:
            text += f"\nShape: {info['shape']}\n"
            text += f"Min: {info['min']:.2f}\n"
            text += f"Max: {info['max']:.2f}\n"
            text += f"Mean: {info['mean']:.2f}\n"
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, text)
        self.stats_text.config(state=tk.DISABLED)
    
    def _on_opacity_change(self, value):
        """Handle opacity slider change"""
        selection = self.layer_listbox.curselection()
        if selection:
            layer_name = self.layer_listbox.get(selection[0])
            opacity = int(value) / 100.0
            self.gis_canvas.set_layer_opacity(layer_name, opacity)
    
    def _set_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        logger.info(message)


if __name__ == "__main__":
    import logging.config
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = TerraSim_GIS()
    app.mainloop()
