"""
TerraSim Main Application Window
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import logging
import os
from typing import Optional, cast, Dict, Any
from datetime import datetime

# Visualization imports for 2D and 3D
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
from matplotlib.colors import Normalize

# Additional visualization
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageTk

from .screens import CalculationScreen, ResultScreen, SimulationScreen, WorkflowScreen
from backend.services.simulation_engine import get_simulation_engine, SimulationParameters, SimulationMode, SimulationResult
from backend.services.layer_composition import LayerCompositionManager, LayerInfo
from backend.services.geotiff_handler import GeoTIFFHandler

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """Main application window for TerraSim"""
    
    def __init__(self):
        super().__init__()
        
        self.title("TerraSim - Erosion Modeling Simulation")
        self.geometry("1400x900")
        self.resizable(True, True)
        
        # Application state
        self.current_dem = None
        self.current_dem_path = None
        self.current_parameters = None
        self.current_result = None
        self.current_map = None  # Base map/raster layer
        self.current_map_path = None
        
        self.simulation_engine = get_simulation_engine()
        
        # Layer composition manager
        self.layer_manager = LayerCompositionManager(layouts_dir="map_layouts")
        
        logger.info("Initializing TerraSim Main Window")
        
        self._create_main_ui()
        self._create_menu()
    
    def _create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load DEM", command=self.load_dem)
        file_menu.add_command(label="Load Base Map", command=self.load_map)
        file_menu.add_command(label="Load Parameters", command=self.load_parameters)
        file_menu.add_separator()
        file_menu.add_command(label="Save Layout", command=self.save_layout)
        file_menu.add_command(label="Load Layout", command=self.load_layout)
        file_menu.add_command(label="Manage Layouts", command=self.manage_layouts)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Single Run", command=self.run_single_simulation)
        sim_menu.add_command(label="Time Series", command=self.run_time_series)
        sim_menu.add_command(label="Sensitivity Analysis", command=self.run_sensitivity)
        sim_menu.add_separator()
        sim_menu.add_command(label="Clear History", command=self.clear_history)
        
        # Workflow menu
        workflow_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Workflow", menu=workflow_menu)
        workflow_menu.add_command(label="USPED Workflow", command=self.run_usped_workflow)
        workflow_menu.add_command(label="Workflow Documentation", command=self.show_workflow_docs)
        
        # Visualization menu
        viz_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualization", menu=viz_menu)
        viz_menu.add_command(label="DEM 3D Surface", command=self.visualize_dem_3d)
        viz_menu.add_command(label="Erosion 3D Surface", command=self.visualize_erosion_3d)
        viz_menu.add_command(label="Interactive 3D (Plotly)", command=self.create_interactive_3d_plot)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About TerraSim", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
    
    def _create_main_ui(self):
        """Create main UI layout"""
        # Top toolbar
        toolbar_frame = tk.Frame(self, bg='#34495e', height=50)
        toolbar_frame.pack(fill=tk.X, padx=0, pady=0)
        toolbar_frame.pack_propagate(False)
        
        tk.Label(
            toolbar_frame,
            text="TerraSim - Erosion Modeling System",
            font=("Arial", 14, "bold"),
            bg='#34495e',
            fg='white'
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # Main container with sidebar and content
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sidebar
        self.sidebar = tk.Frame(main_container, bg='white', width=250, relief=tk.SUNKEN, bd=1)
        self.sidebar.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        self._create_sidebar()
        
        # Content area
        self.content_frame = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, bd=1)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Welcome screen
        self._show_welcome_screen()
    
    def _create_sidebar(self):
        """Create sidebar with quick access"""
        # Title
        title_label = tk.Label(
            self.sidebar,
            text="QUICK ACCESS",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # DEM section
        dem_frame = tk.LabelFrame(
            self.sidebar,
            text="Digital Elevation Model",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        dem_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            dem_frame,
            text="Load DEM",
            font=("Arial", 9),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=8,
            command=self.load_dem
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            dem_frame,
            text="Generate Sample",
            font=("Arial", 9),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=8,
            command=self.generate_sample_dem
        ).pack(fill=tk.X)
        
        self.dem_status = tk.Label(
            dem_frame,
            text="Status: No DEM loaded",
            font=("Arial", 8),
            bg='white',
            fg='#7f8c8d'
        )
        self.dem_status.pack(anchor=tk.W, pady=(10, 0))
        
        # Map section
        map_frame = tk.LabelFrame(
            self.sidebar,
            text="Base Map Layer",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        map_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            map_frame,
            text="Load Map",
            font=("Arial", 9),
            bg='#1abc9c',
            fg='white',
            padx=15,
            pady=8,
            command=self.load_map
        ).pack(fill=tk.X, pady=5)
        
        self.map_status = tk.Label(
            map_frame,
            text="Status: No map loaded",
            font=("Arial", 8),
            bg='white',
            fg='#7f8c8d'
        )
        self.map_status.pack(anchor=tk.W, pady=(5, 0))
        
        # Parameters section
        params_frame = tk.LabelFrame(
            self.sidebar,
            text="Simulation Parameters",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        params_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            params_frame,
            text="Load Parameters",
            font=("Arial", 9),
            bg='#9b59b6',
            fg='white',
            padx=15,
            pady=8,
            command=self.load_parameters
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            params_frame,
            text="Edit Parameters",
            font=("Arial", 9),
            bg='#8e44ad',
            fg='white',
            padx=15,
            pady=8,
            command=self.edit_parameters
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            params_frame,
            text="Default Parameters",
            font=("Arial", 9),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=8,
            command=self.load_default_parameters
        ).pack(fill=tk.X)
        
        self.params_status = tk.Label(
            params_frame,
            text="Status: Not loaded",
            font=("Arial", 8),
            bg='white',
            fg='#7f8c8d'
        )
        self.params_status.pack(anchor=tk.W, pady=(10, 0))
        
        # Quick simulations
        sim_frame = tk.LabelFrame(
            self.sidebar,
            text="Quick Simulations",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        sim_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            sim_frame,
            text="▶ Single Run",
            font=("Arial", 9, "bold"),
            bg='#27ae60',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_single_simulation
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            sim_frame,
            text="▶ Time Series",
            font=("Arial", 9, "bold"),
            bg='#2980b9',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_time_series
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            sim_frame,
            text="▶ Sensitivity",
            font=("Arial", 9, "bold"),
            bg='#e67e22',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_sensitivity
        ).pack(fill=tk.X)
        
        # USPED Workflow section
        workflow_frame = tk.LabelFrame(
            self.sidebar,
            text="USPED Workflow",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        workflow_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            workflow_frame,
            text="🔄 Run Workflow",
            font=("Arial", 9, "bold"),
            bg='#8e44ad',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_usped_workflow
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            workflow_frame,
            text="📖 Workflow Docs",
            font=("Arial", 9),
            bg='#34495e',
            fg='white',
            padx=15,
            pady=8,
            command=self.show_workflow_docs
        ).pack(fill=tk.X)
        
        # History section
        history_frame = tk.LabelFrame(
            self.sidebar,
            text="History",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        self.history_listbox = tk.Listbox(
            history_frame,
            font=("Arial", 8),
            bg='white',
            fg='#333'
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_select)
        
        tk.Button(
            history_frame,
            text="Clear History",
            font=("Arial", 8),
            bg='#e74c3c',
            fg='white',
            padx=10,
            pady=5,
            command=self.clear_history
        ).pack(fill=tk.X)
        
        # Visualization section
        viz_frame = tk.LabelFrame(
            self.sidebar,
            text="3D Visualization",
            font=("Arial", 10, "bold"),
            bg='white',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        viz_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        tk.Button(
            viz_frame,
            text="View DEM 3D",
            font=("Arial", 9),
            bg='#16a085',
            fg='white',
            padx=15,
            pady=8,
            command=self.visualize_dem_3d
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            viz_frame,
            text="View Erosion 3D",
            font=("Arial", 9),
            bg='#d35400',
            fg='white',
            padx=15,
            pady=8,
            command=self.visualize_erosion_3d
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            viz_frame,
            text="Interactive Plot",
            font=("Arial", 9),
            bg='#2980b9',
            fg='white',
            padx=15,
            pady=8,
            command=self.create_interactive_3d_plot
        ).pack(fill=tk.X)
    
    def _show_welcome_screen(self):
        """Show welcome/home screen"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        welcome_frame = tk.Frame(self.content_frame, bg='white')
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            welcome_frame,
            text="Welcome to TerraSim",
            font=("Arial", 28, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        title_label.pack(pady=(50, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            welcome_frame,
            text="Advanced Erosion Modeling and Simulation System",
            font=("Arial", 14),
            bg='white',
            fg='#7f8c8d'
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Getting started section
        getting_started_frame = tk.Frame(welcome_frame, bg='#ecf0f1', relief=tk.SUNKEN, bd=1)
        getting_started_frame.pack(fill=tk.X, padx=40, pady=20)
        
        gs_title = tk.Label(
            getting_started_frame,
            text="Getting Started",
            font=("Arial", 14, "bold"),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        gs_title.pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        steps = [
            "1. Load or generate a Digital Elevation Model (DEM)",
            "2. Configure simulation parameters (rainfall, soil properties, etc.)",
            "3. Choose a simulation type (Single Run, Time Series, or Sensitivity Analysis)",
            "4. Run the simulation and visualize results in real-time",
            "5. Export and analyze the results",
        ]
        
        for step in steps:
            step_label = tk.Label(
                getting_started_frame,
                text=step,
                font=("Arial", 11),
                bg='#ecf0f1',
                fg='#34495e',
                justify=tk.LEFT
            )
            step_label.pack(anchor=tk.W, padx=30, pady=5)
        
        tk.Frame(getting_started_frame, bg='#ecf0f1', height=15).pack()
        
        # Quick access buttons
        buttons_frame = tk.Frame(welcome_frame, bg='white')
        buttons_frame.pack(pady=40)
        
        tk.Button(
            buttons_frame,
            text="Load DEM",
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white',
            padx=30,
            pady=12,
            command=self.load_dem
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            buttons_frame,
            text="Generate Sample",
            font=("Arial", 12, "bold"),
            bg='#27ae60',
            fg='white',
            padx=30,
            pady=12,
            command=self.generate_sample_dem
        ).pack(side=tk.LEFT, padx=10)
    
    def load_dem(self):
        """Load DEM from file - supports multiple formats"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("GeoTIFF files", "*.tif *.tiff"),
                ("NumPy files", "*.npy"),
                ("ASCII Grid", "*.asc *.grd"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith('.npy'):
                    # NumPy binary format
                    self.current_dem = np.load(file_path)
                
                elif file_path.endswith(('.tif', '.tiff')):
                    # GeoTIFF format - enhanced with full metadata support
                    try:
                        handler = GeoTIFFHandler(file_path)
                        
                        # For multi-band GeoTIFFs, ask user which band to use as DEM
                        if handler.metadata and handler.metadata.count > 1:
                            self._load_geotiff_with_band_selection(handler, file_path)
                            return
                        else:
                            # Single band: use directly as DEM
                            self.current_dem = handler.get_band(1)
                            
                            # Also auto-generate map if not already loaded
                            if self.current_map is None:
                                try:
                                    self.current_map = handler.auto_generate_map()
                                    self.current_map_path = file_path
                                    self.map_status.config(
                                        text=f"Status: Auto-generated from DEM ({self.current_map.shape[0]}x{self.current_map.shape[1]})",
                                        fg='#3498db'
                                    )
                                    logger.info(f"Auto-generated map from single-band GeoTIFF")
                                except Exception as e:
                                    logger.info(f"Could not auto-generate map: {e}")
                    
                    except Exception as e:
                        logger.warning(f"GeoTIFF handler failed, falling back to basic rasterio: {e}")
                        try:
                            import rasterio
                            with rasterio.open(file_path) as src:
                                self.current_dem = src.read(1).astype(np.float32)
                        except Exception as e2:
                            raise ValueError(f"Failed to load DEM: {e2}")
                
                elif file_path.endswith(('.asc', '.grd')):
                    # ASCII Grid format
                    self.current_dem = np.loadtxt(file_path, skiprows=6)
                
                else:
                    # Try generic NumPy load for unknown formats
                    self.current_dem = np.load(file_path)
                
                # Ensure we have a 2D array
                if self.current_dem is None:
                    raise ValueError("Could not load DEM data from file")
                
                if self.current_dem.ndim != 2:
                    raise ValueError(f"Expected 2D array, got {self.current_dem.ndim}D")
                
                # Track DEM path for layout saving
                self.current_dem_path = file_path
                
                dem = cast(np.ndarray, self.current_dem)
                logger.info(f"Loaded DEM from {file_path}, shape: {dem.shape}, dtype: {dem.dtype}")
                self.dem_status.config(
                    text=f"Status: Loaded ({dem.shape[0]}x{dem.shape[1]})",
                    fg='#27ae60'
                )
                messagebox.showinfo(
                    "Success",
                    f"DEM loaded successfully!\n"
                    f"Shape: {dem.shape}\n"
                    f"Data type: {dem.dtype}\n"
                    f"Range: {dem.min():.2f} to {dem.max():.2f}"
                )
            except Exception as e:
                logger.error(f"Error loading DEM: {e}")
                messagebox.showerror("Error", f"Failed to load DEM:\n{e}")
    
    def _load_geotiff_with_band_selection(self, handler: GeoTIFFHandler, file_path: str):
        """Load multi-band GeoTIFF with user band selection"""
        # Create band selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Multi-Band GeoTIFF - Select DEM Band")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Show band information
        info = handler.get_band_info()
        
        title_label = tk.Label(
            dialog,
            text=f"GeoTIFF has {info['band_count']} bands. Select which band to use as DEM:",
            font=("Arial", 11, "bold"),
            wraplength=550
        )
        title_label.pack(pady=10, padx=10)
        
        # Create frame with scrollbar for band info
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(frame, bg='white', relief=tk.SUNKEN, bd=1)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Radio button for each band
        selected_band = tk.IntVar(value=1)
        
        for band_info in info['bands']:
            band_num = band_info['index']
            desc = band_info['description']
            stats = f"Range: {band_info['min']:.2f} - {band_info['max']:.2f}, Mean: {band_info['mean']:.2f}"
            
            frame_band = tk.Frame(scrollable_frame, bg='white', relief=tk.RAISED, bd=1)
            frame_band.pack(fill=tk.X, padx=5, pady=5)
            
            tk.Radiobutton(
                frame_band,
                text=f"Band {band_num}: {desc}\n{stats}",
                variable=selected_band,
                value=band_num,
                bg='white',
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=10, pady=8)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Also offer map auto-generation option
        map_frame = tk.LabelFrame(dialog, text="Map Generation", font=("Arial", 10, "bold"), padx=10, pady=10)
        map_frame.pack(fill=tk.X, padx=10, pady=10)
        
        gen_map_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            map_frame,
            text="Auto-generate base map from other bands (if available)",
            variable=gen_map_var,
            bg='white'
        ).pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def load_selected():
            try:
                band_idx = selected_band.get()
                self.current_dem = handler.get_band(band_idx)
                self.current_dem_path = file_path
                
                dem = cast(np.ndarray, self.current_dem)
                logger.info(f"Loaded band {band_idx} as DEM from GeoTIFF")
                self.dem_status.config(
                    text=f"Status: Loaded ({dem.shape[0]}x{dem.shape[1]}) from band {band_idx}",
                    fg='#27ae60'
                )
                
                # Auto-generate map if enabled and not already loaded
                if gen_map_var.get() and self.current_map is None:
                    try:
                        self.current_map = handler.auto_generate_map()
                        self.current_map_path = file_path
                        map_data = cast(np.ndarray, self.current_map)
                        self.map_status.config(
                            text=f"Status: Auto-generated ({map_data.shape[0]}x{map_data.shape[1]})",
                            fg='#3498db'
                        )
                        logger.info(f"Auto-generated map from multi-band GeoTIFF")
                    except Exception as e:
                        logger.info(f"Could not auto-generate map: {e}")
                
                messagebox.showinfo(
                    "Success",
                    f"DEM loaded from band {band_idx}!\n"
                    f"Shape: {dem.shape}\n"
                    f"Range: {dem.min():.2f} to {dem.max():.2f}"
                )
                dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load band:\n{e}")
                logger.error(f"Error loading band: {e}")
        
        tk.Button(
            button_frame,
            text="Load Selected Band",
            command=load_selected,
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
    
    def load_map(self):
        """Load base map/raster layer - supports raster and vector formats"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("GeoTIFF files", "*.tif *.tiff"),
                ("Shapefiles", "*.shp"),
                ("GeoJSON files", "*.geojson *.json"),
                ("NumPy files", "*.npy"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith(('.shp')):
                    # Shapefile - vector format
                    import geopandas as gpd
                    gdf = gpd.read_file(file_path)
                    
                    # Convert vector to raster for visualization
                    try:
                        from rasterio.features import geometry_mask
                        from rasterio.transform import from_bounds
                        
                        bounds = gdf.total_bounds  # (minx, miny, maxx, maxy)
                        height, width = 256, 256
                        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)
                        
                        # Create raster from geometries
                        shapes = [(geom, 1) for geom in gdf.geometry]
                        self.current_map = geometry_mask(
                            shapes, out_shape=(height, width), transform=transform, invert=True
                        ).astype(np.float32)
                        
                        logger.info(f"Loaded shapefile from {file_path}, vectorized to {self.current_map.shape}")
                    except Exception as e:
                        # If rasterization fails, use bounds box
                        bounds = gdf.total_bounds
                        self.current_map = np.ones((256, 256), dtype=np.float32)
                        logger.info(f"Loaded shapefile from {file_path} (bounds only), error: {e}")
                
                elif file_path.endswith(('.geojson', '.json')):
                    # GeoJSON - vector format
                    import geopandas as gpd
                    gdf = gpd.read_file(file_path)
                    
                    try:
                        from rasterio.features import geometry_mask
                        from rasterio.transform import from_bounds
                        
                        bounds = gdf.total_bounds  # (minx, miny, maxx, maxy)
                        height, width = 256, 256
                        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)
                        
                        shapes = [(geom, 1) for geom in gdf.geometry]
                        self.current_map = geometry_mask(
                            shapes, out_shape=(height, width), transform=transform, invert=True
                        ).astype(np.float32)
                        
                        logger.info(f"Loaded GeoJSON from {file_path}, vectorized to {self.current_map.shape}")
                    except Exception as e:
                        bounds = gdf.total_bounds
                        self.current_map = np.ones((256, 256), dtype=np.float32)
                        logger.info(f"Loaded GeoJSON from {file_path} (bounds only), error: {e}")
                
                elif file_path.endswith(('.tif', '.tiff')):
                    # GeoTIFF - raster format with full metadata support
                    try:
                        handler = GeoTIFFHandler(file_path)
                        info = handler.get_band_info()
                        
                        if handler.metadata and handler.metadata.count > 1:
                            # Multi-band GeoTIFF - use auto-generation
                            self.current_map = handler.auto_generate_map()
                            data_type = "Multi-band Auto-Generated"
                            if handler.has_ndvi_bands()[0]:
                                data_type += " (NDVI)"
                            elif handler.is_rgb():
                                data_type += " (RGB)"
                        else:
                            # Single band - use directly
                            self.current_map = handler.get_band(1)
                            data_type = "Single Band"
                        
                        self.current_map_path = file_path
                        self.current_map = cast(np.ndarray, self.current_map).astype(np.float32)
                        logger.info(f"Loaded GeoTIFF from {file_path}, shape: {self.current_map.shape}, type: {data_type}")
                        
                        # Show metadata info
                        messagebox.showinfo(
                            "GeoTIFF Loaded",
                            f"Type: {data_type}\n"
                            f"Bands: {info['band_count']}\n"
                            f"Size: {info['width']}x{info['height']}\n"
                            f"CRS: {info['crs']}"
                        )
                    except Exception as e:
                        # Fallback to basic rasterio
                        try:
                            import rasterio
                            with rasterio.open(file_path) as src:
                                self.current_map = src.read(1).astype(np.float32)
                            logger.info(f"Loaded GeoTIFF (basic) from {file_path}, shape: {self.current_map.shape}")
                        except Exception as e2:
                            raise ValueError(f"Could not load GeoTIFF: {e2}")
                
                elif file_path.endswith('.npy'):
                    # NumPy binary format
                    self.current_map = np.load(file_path).astype(np.float32)
                    logger.info(f"Loaded NumPy map from {file_path}, shape: {self.current_map.shape}")
                
                else:
                    # Try generic load
                    self.current_map = np.load(file_path).astype(np.float32)
                
                if self.current_map is None:
                    raise ValueError("Could not load map data")
                
                self.current_map_path = file_path
                
                # Normalize to 0-1 range for visualization
                map_min, map_max = self.current_map.min(), self.current_map.max()
                if map_max > map_min:
                    self.current_map = (self.current_map - map_min) / (map_max - map_min)
                
                # Get shape info for status display
                shape_str = f"{self.current_map.shape[0]}x{self.current_map.shape[1]}" if len(self.current_map.shape) >= 2 else str(self.current_map.shape)
                
                self.map_status.config(
                    text=f"Status: Loaded ({shape_str})",
                    fg='#27ae60'
                )
                messagebox.showinfo(
                    "Success",
                    f"Map loaded successfully!\n"
                    f"Shape: {self.current_map.shape}\n"
                    f"Type: {file_path.split('.')[-1].upper()}"
                )
            except Exception as e:
                logger.error(f"Error loading map: {e}")
                messagebox.showerror("Error", f"Failed to load map:\n{e}")
    def generate_sample_dem(self):
        """Generate sample DEM for testing"""
        try:
            # Create synthetic DEM with terrain features
            size = 100
            x = np.linspace(0, 10, size)
            y = np.linspace(0, 10, size)
            X, Y = np.meshgrid(x, y)
            
            # Create hillslope
            self.current_dem = (
                100 - 0.5 * np.sqrt((X - 5)**2 + (Y - 5)**2) +  # Central peak
                5 * np.sin(X) * np.cos(Y) +  # Wave pattern
                np.random.normal(0, 0.5, (size, size))  # Noise
            )
            
            logger.info(f"Generated sample DEM, shape: {self.current_dem.shape}")
            self.dem_status.config(
                text=f"Status: Generated ({self.current_dem.shape[0]}x{self.current_dem.shape[1]})",
                fg='#27ae60'
            )
            messagebox.showinfo("Success", f"Sample DEM generated!\nShape: {self.current_dem.shape}")
        except Exception as e:
            logger.error(f"Error generating DEM: {e}")
            messagebox.showerror("Error", f"Failed to generate DEM:\n{e}")
    
    def load_parameters(self):
        """Load parameters from one or multiple files"""
        file_paths = filedialog.askopenfilenames(
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("NumPy files", "*.npy"),
                ("All files", "*.*")
            ]
        )
        
        if file_paths:
            try:
                import json
                import csv
                
                # Start with defaults
                merged_params = self._get_default_parameters()
                
                # Load and merge each file
                for file_path in file_paths:
                    loaded_params = {}
                    
                    if file_path.endswith('.json'):
                        with open(file_path, 'r') as f:
                            loaded_params = json.load(f)
                    
                    elif file_path.endswith('.csv'):
                        loaded_params = self._parse_csv_parameters(file_path)
                    
                    elif file_path.endswith('.npy'):
                        params_array = np.load(file_path, allow_pickle=True).item()
                        loaded_params = params_array if isinstance(params_array, dict) else {}
                    
                    # Merge with existing parameters
                    if loaded_params:
                        merged_params.update(loaded_params)
                        logger.info(f"Loaded and merged parameters from {file_path}")
                
                self.current_parameters = merged_params
                self._refresh_params_status()
                
                missing_params = [k for k in self._get_default_parameters().keys() 
                                 if k not in self.current_parameters]
                
                if missing_params:
                    msg = f"Parameters loaded successfully!\n\nMissing parameters filled with defaults:\n" + \
                          ", ".join(missing_params)
                    messagebox.showinfo("Success", msg)
                else:
                    messagebox.showinfo("Success", "All parameters loaded successfully!")
            
            except Exception as e:
                logger.error(f"Error loading parameters: {e}")
                messagebox.showerror("Error", f"Failed to load parameters:\n{e}")
    
    def _parse_csv_parameters(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file in multiple formats"""
        import csv
        params = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read all rows first
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                return params
            
            first_row = rows[0]
            
            # Detect format based on first row and second row (if exists)
            # Format 1: Header row with values in next row
            # rainfall_erosivity,soil_erodibility,cover_factor
            # 300,0.35,0.3
            is_header_format = (len(rows) > 1 and 
                               len(first_row) > 1 and
                               any(c.isdigit() or c == '.' for c in rows[1][0]))
            
            if is_header_format:
                # Header format: keys are in first row, values in data rows
                headers = [h.strip() for h in first_row]
                for row_idx, row in enumerate(rows[1:], 1):
                    for col_idx, value in enumerate(row):
                        if col_idx < len(headers):
                            key = headers[col_idx]
                            if key and value.strip():
                                try:
                                    params[key] = float(value)
                                except ValueError:
                                    params[key] = value.strip()
            else:
                # Key-value format: first column is key, second is value
                # rainfall_erosivity,300.0
                # soil_erodibility,0.35
                for row in rows:
                    if len(row) >= 2 and row[0].strip():
                        key = row[0].strip()
                        value = row[1].strip()
                        if value:
                            try:
                                params[key] = float(value)
                            except ValueError:
                                params[key] = value
        
        except Exception as e:
            logger.warning(f"Error parsing CSV {file_path}: {e}")
        
        return params
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters"""
        return {
            'rainfall_erosivity': 300.0,
            'soil_erodibility': 0.35,
            'cover_factor': 0.3,
            'practice_factor': 0.5,
            'time_step_days': 1.0,
            'num_timesteps': 10,
            'bulk_density': 1300.0,
            'area_exponent': 0.6,
            'slope_exponent': 1.3,
            'runoff_coefficient': 0.5,
        }
    
    def load_default_parameters(self):
        """Load default parameters"""
        self.current_parameters = self._get_default_parameters()
        logger.info("Loaded default parameters")
        self._refresh_params_status()
        messagebox.showinfo("Success", "Default parameters loaded!")
    
    def _refresh_params_status(self):
        """Refresh the parameters status label"""
        if self.current_parameters is None:
            self.params_status.config(text="Status: Not loaded", fg='#e74c3c')
        else:
            param_count = len(self.current_parameters)
            self.params_status.config(
                text=f"Status: Loaded ({param_count} params)",
                fg='#27ae60'
            )
    
    def edit_parameters(self):
        """Open parameter editor dialog"""
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load or set parameters first")
            return
        
        # Create edit window
        edit_window = tk.Toplevel(self)
        edit_window.title("Edit Simulation Parameters")
        edit_window.geometry("500x600")
        
        # Create frame with scrollbar
        canvas = tk.Canvas(edit_window, bg='white')
        scrollbar = ttk.Scrollbar(edit_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add parameter inputs
        param_entries = {}
        for key, value in self.current_parameters.items():
            frame = tk.Frame(scrollable_frame, bg='white')
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                frame,
                text=f"{key}:",
                font=("Arial", 10),
                bg='white',
                fg='#2c3e50',
                width=20,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(frame, font=("Arial", 10), width=20)
            entry.insert(0, str(value))
            entry.pack(side=tk.RIGHT, padx=5)
            param_entries[key] = entry
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = tk.Frame(edit_window, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_params():
            try:
                if self.current_parameters is None:
                    self.current_parameters = {}
                
                for key, entry in param_entries.items():
                    try:
                        self.current_parameters[key] = float(entry.get())
                    except ValueError:
                        self.current_parameters[key] = entry.get()
                
                logger.info("Parameters updated")
                self._refresh_params_status()
                messagebox.showinfo("Success", "Parameters updated successfully!")
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save parameters: {e}")
        
        tk.Button(
            button_frame,
            text="Save",
            font=("Arial", 10, "bold"),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            command=save_params
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            command=edit_window.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Export to JSON",
            font=("Arial", 9),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=8,
            command=lambda: self._export_parameters(param_entries)
        ).pack(side=tk.RIGHT, padx=5)
    
    def _export_parameters(self, param_entries):
        """Export edited parameters to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("NumPy files", "*.npy"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Update parameters from entries
                export_params = {}
                for key, entry in param_entries.items():
                    try:
                        export_params[key] = float(entry.get())
                    except ValueError:
                        export_params[key] = entry.get()
                
                import json
                import csv
                
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(export_params, f, indent=2)
                
                elif file_path.endswith('.csv'):
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(export_params.keys())
                        writer.writerow(export_params.values())
                
                elif file_path.endswith('.npy'):
                    np.save(file_path, np.array([export_params], dtype=object))
                
                messagebox.showinfo("Success", f"Parameters exported to:\n{file_path}")
                logger.info(f"Parameters exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export parameters: {e}")
    
    def run_single_simulation(self):
        """Run single erosion simulation"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load parameters first")
            return
        
        logger.info("Starting single run simulation")
        
        # Show calculation screen
        self._show_screen("calculation")
        
        # Run simulation in background
        def run_sim():
            try:
                # Type narrowing - we've already checked for None above
                dem = cast(np.ndarray, self.current_dem)
                params = self.current_parameters
                # Convert dict parameters to SimulationParameters if needed
                if isinstance(params, dict):
                    params = SimulationParameters(**params)
                else:
                    params = cast(SimulationParameters, params)
                result = self.simulation_engine.run_single_simulation(
                    dem,
                    params
                )
                self.current_result = result
                self.after(0, self._on_simulation_complete)
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        import threading
        thread = threading.Thread(target=run_sim, daemon=True)
        thread.start()
    
    def run_time_series(self):
        """Run time series simulation with real-time visualization"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load parameters first")
            return
        
        logger.info("Starting time series simulation")
        
        # Clear content and show simulation screen
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        sim_screen = SimulationScreen(
            self.content_frame,
            self.current_dem,
            self.current_parameters,
            on_complete=self._on_time_series_complete,
            base_map=self.current_map
        )
        sim_screen.pack(fill=tk.BOTH, expand=True)
        sim_screen.start_simulation()
    
    def run_sensitivity(self):
        """Run sensitivity analysis"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load parameters first")
            return
        
        logger.info("Starting sensitivity analysis")
        
        # Show calculation screen
        self._show_screen("calculation")
        
        # Run analysis in background
        def run_analysis():
            try:
                if self.current_dem is None:
                    raise ValueError("DEM is not loaded")
                params = SimulationParameters(**self.current_parameters) if isinstance(self.current_parameters, dict) else self.current_parameters
                result = self.simulation_engine.run_sensitivity_analysis(
                    self.current_dem,
                    params
                )
                self.current_result = result
                self.after(0, self._on_simulation_complete)
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        import threading
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def run_usped_workflow(self):
        """Run complete USPED workflow"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load parameters first")
            return
        
        logger.info("Starting USPED workflow")
        
        # Clear content and show workflow screen
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        workflow_screen = WorkflowScreen(
            self.content_frame,
            self.current_dem,
            self.current_parameters,
            on_complete=self._on_workflow_complete
        )
        workflow_screen.pack(fill=tk.BOTH, expand=True)
    
    def _on_workflow_complete(self):
        """Called when workflow completes"""
        self._update_history()
        messagebox.showinfo("Success", "USPED workflow completed!")
    
    def show_workflow_docs(self):
        """Show workflow documentation"""
        messagebox.showinfo(
            "USPED Workflow Documentation",
            "Soil Erosion and Deposition Modeling\n"
            "Using Unified Sediment Transport and Hillslope Erosion Deposition (USPED)\n\n"
            "Step-by-step process:\n"
            "1. Load Data - Initialize with DEM and parameters\n"
            "2. Compute Slope - Calculate slope gradient\n"
            "3. Compute Aspect - Calculate flow direction\n"
            "4. Flow Accumulation - Upslope contributing area\n"
            "5. LST Factor - Topographic sediment transport capacity\n"
            "6. Sediment Flow - R*K*C*LST calculation\n"
            "7. Flow Components - X and Y decomposition\n"
            "8. Derivatives - Partial derivatives of flow\n"
            "9. Erosion/Deposition - Net E/D calculation\n"
            "10. Classification - Zone classification\n\n"
            "Based on Mitasova & Hofierka (1993)\n"
            "Mathematical Geology, Vol. 25, No. 6"
        )
    
    def _show_screen(self, screen_type: str):
        """Show a specific screen"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if screen_type == "calculation":
            calc_screen = CalculationScreen(
                self.content_frame,
                on_complete=self._on_simulation_complete
            )
            calc_screen.pack(fill=tk.BOTH, expand=True)
            calc_screen.start_simulation()
    
    def _on_simulation_complete(self):
        """Called when simulation completes"""
        self._update_history()
        self._show_result_screen()
    
    def _on_time_series_complete(self):
        """Called when time series simulation completes"""
        self._update_history()
    
    def _show_result_screen(self):
        """Display results screen"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if self.current_result:
            # Convert result to dict and serialize properly
            result_dict = (
                self.current_result.__dict__
                if hasattr(self.current_result, '__dict__')
                else self.current_result
            )
            
            # Serialize numpy arrays and enums
            serialized_result = self._serialize_result(result_dict)
            
            result_screen = ResultScreen(
                self.content_frame,
                serialized_result
            )
            result_screen.pack(fill=tk.BOTH, expand=True)
    
    def _serialize_result(self, result_dict):
        """Serialize result dict to JSON-compatible format"""
        serialized = {}
        for key, value in result_dict.items():
            if hasattr(value, 'value'):  # Enum
                serialized[key] = value.value
            elif isinstance(value, np.ndarray):  # NumPy array
                serialized[key] = f"<numpy array shape={value.shape}>"
            elif hasattr(value, '__dict__'):  # Dataclass/object
                serialized[key] = self._serialize_result(value.__dict__)
            else:
                serialized[key] = value
        return serialized
    
    def _update_history(self):
        """Update history listbox"""
        self.history_listbox.delete(0, tk.END)
        
        for i, result in enumerate(self.simulation_engine.history):
            timestamp = result.timestamp.strftime('%H:%M:%S')
            mode = result.mode.value if hasattr(result.mode, 'value') else str(result.mode)
            item_text = f"{i+1}. {timestamp} - {mode}"
            self.history_listbox.insert(tk.END, item_text)
    
    def _on_history_select(self, event):
        """Handle history selection"""
        selection = self.history_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.simulation_engine.history):
                self.current_result = self.simulation_engine.history[idx]
                self._show_result_screen()
    
    def clear_history(self):
        """Clear simulation history"""
        if messagebox.askyesno("Clear History", "Clear all simulation history?"):
            self.simulation_engine.clear_history()
            self.history_listbox.delete(0, tk.END)
            logger.info("Cleared simulation history")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About TerraSim",
            "TerraSim v1.0\n\n"
            "Advanced Erosion Modeling and Simulation System\n\n"
            "For more information, visit the documentation."
        )
    
    def show_documentation(self):
        """Show documentation"""
        messagebox.showinfo(
            "Documentation",
            "TerraSim Documentation\n\n"
            "Getting Started:\n"
            "1. Load a DEM (Digital Elevation Model)\n"
            "2. Configure simulation parameters\n"
            "3. Run your desired simulation type\n"
            "4. Analyze and export results\n\n"
            "Simulation Types:\n"
            "- Single Run: One-time erosion calculation\n"
            "- Time Series: Multi-timestep evolution\n"
            "- Sensitivity: Parameter sensitivity analysis"
        )
    
    # ============= 3D VISUALIZATION METHODS =============
    
    def visualize_dem_3d(self):
        """Display DEM in 3D surface plot"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        try:
            # Create 3D plot window
            fig = Figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111, projection='3d')
            
            # Create mesh grid
            dem_data = self.current_dem
            x = np.arange(dem_data.shape[1])
            y = np.arange(dem_data.shape[0])
            X, Y = np.meshgrid(x, y)
            
            # Plot surface
            surf = ax.plot_surface(X, Y, dem_data, cmap='terrain', alpha=0.8, edgecolor='none')
            
            # Customize plot
            ax.set_xlabel('X (pixels)', fontweight='bold')
            ax.set_ylabel('Y (pixels)', fontweight='bold')
            ax.set_zlabel('Elevation (m)', fontweight='bold')
            ax.set_title('Digital Elevation Model - 3D View', fontsize=14, fontweight='bold')
            
            # Add colorbar
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevation (m)')
            
            # Set viewing angle
            ax.view_init(elev=25, azim=45)
            
            # Create tkinter window for plot
            plot_window = tk.Toplevel(self)
            plot_window.title("3D DEM Visualization")
            plot_window.geometry("900x700")
            
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add rotation controls
            control_frame = tk.Frame(plot_window)
            control_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(control_frame, text="View Angle:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            
            def update_view(elev, azim):
                ax.view_init(elev=elev, azim=azim)
                canvas.draw()
            
            tk.Button(
                control_frame,
                text="Top View",
                command=lambda: update_view(90, 0)
            ).pack(side=tk.LEFT, padx=2)
            
            tk.Button(
                control_frame,
                text="Side View",
                command=lambda: update_view(0, 0)
            ).pack(side=tk.LEFT, padx=2)
            
            tk.Button(
                control_frame,
                text="Isometric",
                command=lambda: update_view(25, 45)
            ).pack(side=tk.LEFT, padx=2)
            
            tk.Button(
                control_frame,
                text="3D View",
                command=lambda: update_view(35, 120)
            ).pack(side=tk.LEFT, padx=2)
            
            logger.info("Opened 3D DEM visualization")
            
        except Exception as e:
            logger.error(f"Error creating 3D visualization: {e}")
            messagebox.showerror("Error", f"Failed to create 3D visualization: {str(e)}")
    
    def visualize_erosion_3d(self):
        """Display erosion results in 3D"""
        if self.current_result is None:
            messagebox.showwarning("Warning", "Please run a simulation first")
            return
        
        if not hasattr(self.current_result, 'erosion_rate') or self.current_result.erosion_rate is None:
            messagebox.showwarning("Warning", "No erosion data available")
            return
        
        try:
            # Create 3D plot window
            fig = Figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111, projection='3d')
            
            # Get erosion data
            erosion_data = self.current_result.erosion_rate
            dem_data = self.current_dem if self.current_dem is not None else np.zeros_like(erosion_data)
            
            # Create mesh grid
            x = np.arange(erosion_data.shape[1])
            y = np.arange(erosion_data.shape[0])
            X, Y = np.meshgrid(x, y)
            
            # Plot erosion as 3D surface using dem + erosion
            combined = dem_data + erosion_data * 10  # Scale erosion for visibility
            surf = ax.plot_surface(X, Y, combined, cmap='RdYlGn_r', alpha=0.8, edgecolor='none')
            
            # Customize plot
            ax.set_xlabel('X (pixels)', fontweight='bold')
            ax.set_ylabel('Y (pixels)', fontweight='bold')
            ax.set_zlabel('Elevation + Erosion (m)', fontweight='bold')
            ax.set_title('Erosion Analysis - 3D View', fontsize=14, fontweight='bold')
            
            # Add colorbar
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevation + Erosion (m)')
            
            # Set viewing angle
            ax.view_init(elev=25, azim=45)
            
            # Create tkinter window for plot
            plot_window = tk.Toplevel(self)
            plot_window.title("3D Erosion Visualization")
            plot_window.geometry("900x700")
            
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add rotation controls
            control_frame = tk.Frame(plot_window)
            control_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(control_frame, text="View Angle:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            
            def update_view(elev, azim):
                ax.view_init(elev=elev, azim=azim)
                canvas.draw()
            
            tk.Button(control_frame, text="Top View", command=lambda: update_view(90, 0)).pack(side=tk.LEFT, padx=2)
            tk.Button(control_frame, text="Side View", command=lambda: update_view(0, 0)).pack(side=tk.LEFT, padx=2)
            tk.Button(control_frame, text="Isometric", command=lambda: update_view(25, 45)).pack(side=tk.LEFT, padx=2)
            tk.Button(control_frame, text="3D View", command=lambda: update_view(35, 120)).pack(side=tk.LEFT, padx=2)
            
            logger.info("Opened 3D erosion visualization")
            
        except Exception as e:
            logger.error(f"Error creating 3D erosion visualization: {e}")
            messagebox.showerror("Error", f"Failed to create 3D visualization: {str(e)}")
    
    def create_interactive_3d_plot(self):
        """Create interactive 3D plot using Plotly"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        try:
            dem_data = self.current_dem
            
            # Create plotly 3D surface plot
            fig = go.Figure(data=[go.Surface(z=dem_data, colorscale='Terrain')])
            
            fig.update_layout(
                title='Interactive 3D DEM Visualization (Plotly)',
                scene=dict(
                    xaxis_title='X (pixels)',
                    yaxis_title='Y (pixels)',
                    zaxis_title='Elevation (m)',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
                ),
                width=1000,
                height=800
            )
            
            # Show in browser
            fig.show()
            logger.info("Opened interactive 3D Plotly visualization")
            
        except Exception as e:
            logger.error(f"Error creating Plotly visualization: {e}")
            messagebox.showerror("Error", f"Failed to create interactive visualization: {str(e)}")
    
    # ============= LAYER COMPOSITION & LAYOUT MANAGEMENT =============
    
    def save_layout(self):
        """Save current layer composition as a layout"""
        if self.current_dem is None and self.current_map is None and self.current_parameters is None:
            messagebox.showwarning("Warning", "Load at least one layer (DEM, Base Map, or Parameters) first")
            return
        
        # Ask for layout name
        dialog = tk.Toplevel(self)
        dialog.title("Save Layout")
        dialog.geometry("400x200")
        
        tk.Label(dialog, text="Layout Name:", font=("Arial", 10, "bold")).pack(pady=10)
        name_entry = tk.Entry(dialog, font=("Arial", 10), width=40)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Description (optional):", font=("Arial", 10, "bold")).pack(pady=5)
        desc_text = tk.Text(dialog, height=3, width=40, font=("Arial", 9))
        desc_text.pack(pady=5, padx=10)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a layout name")
                return
            
            description = desc_text.get("1.0", tk.END).strip()
            
            try:
                # Add layers to composition
                if self.current_dem is not None and self.current_dem_path:
                    layer_info = LayerInfo(
                        name="DEM",
                        layer_type="dem",
                        file_path=self.current_dem_path,
                        file_format=self.current_dem_path.split('.')[-1].lower(),
                        visible=True,
                        opacity=1.0
                    )
                    self.layer_manager.add_layer(layer_info)
                
                if self.current_map is not None and self.current_map_path:
                    layer_info = LayerInfo(
                        name="Base Map",
                        layer_type="base_map",
                        file_path=self.current_map_path,
                        file_format=self.current_map_path.split('.')[-1].lower(),
                        visible=True,
                        opacity=0.7
                    )
                    self.layer_manager.add_layer(layer_info)
                
                # Create and save layout
                layout = self.layer_manager.create_layout(name, description)
                filepath = self.layer_manager.save_layout(layout)
                
                messagebox.showinfo("Success", f"Layout saved to:\n{filepath}")
                logger.info(f"Layout saved: {name}")
                dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save layout:\n{e}")
                logger.error(f"Error saving layout: {e}")
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Save", command=save, bg='#27ae60', fg='white', padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, bg='#e74c3c', fg='white', padx=20, pady=8).pack(side=tk.LEFT, padx=5)
    
    def load_layout(self):
        """Load a saved layout"""
        file_path = filedialog.askopenfilename(
            initialdir="map_layouts",
            filetypes=[("Layout files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                layout = self.layer_manager.load_layout(file_path)
                
                # Load all layers from layout
                for layer_data in layout.layers:
                    layer = LayerInfo(**layer_data)
                    
                    if layer.layer_type == "dem":
                        try:
                            if layer.file_path.endswith('.npy'):
                                self.current_dem = np.load(layer.file_path)
                            elif layer.file_path.endswith(('.tif', '.tiff')):
                                import rasterio
                                with rasterio.open(layer.file_path) as src:
                                    self.current_dem = src.read(1).astype(np.float32)
                            elif layer.file_path.endswith(('.asc', '.grd')):
                                self.current_dem = np.loadtxt(layer.file_path, skiprows=6)
                            
                            if self.current_dem is not None:
                                self.current_dem_path = layer.file_path
                                dem = cast(np.ndarray, self.current_dem)
                                self.dem_status.config(
                                    text=f"Status: Loaded ({dem.shape[0]}x{dem.shape[1]})",
                                    fg='#27ae60'
                                )
                                logger.info(f"Loaded DEM from layout: {layer.file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to load DEM from layout: {e}")
                    
                    elif layer.layer_type == "base_map":
                        try:
                            if layer.file_path.endswith(('.shp')):
                                import geopandas as gpd
                                gdf = gpd.read_file(layer.file_path)
                                from rasterio.features import geometry_mask
                                from rasterio.transform import from_bounds
                                bounds = gdf.total_bounds
                                shapes = [geom for geom in gdf.geometry]
                                self.current_map = geometry_mask(shapes, out_shape=(256, 256),
                                                                transform=from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], 256, 256),
                                                                invert=True).astype(np.float32)
                                self.current_map = (self.current_map - self.current_map.min()) / (self.current_map.max() - self.current_map.min() + 1e-8)
                            elif layer.file_path.endswith(('.tif', '.tiff')):
                                import rasterio
                                with rasterio.open(layer.file_path) as src:
                                    self.current_map = src.read(1).astype(np.float32)
                                    self.current_map = (self.current_map - self.current_map.min()) / (self.current_map.max() - self.current_map.min() + 1e-8)
                            elif layer.file_path.endswith('.npy'):
                                self.current_map = np.load(layer.file_path)
                            
                            if self.current_map is not None:
                                self.current_map_path = layer.file_path
                                map_data = cast(np.ndarray, self.current_map)
                                self.map_status.config(
                                    text=f"Status: Loaded ({map_data.shape[0]}x{map_data.shape[1]})",
                                    fg='#27ae60'
                                )
                                logger.info(f"Loaded base map from layout: {layer.file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to load base map from layout: {e}")
                
                messagebox.showinfo("Success", f"Layout loaded:\n{layout.name}\n{layout.description}")
                logger.info(f"Layout loaded: {layout.name}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load layout:\n{e}")
                logger.error(f"Error loading layout: {e}")
    
    def manage_layouts(self):
        """Open layout manager dialog"""
        layouts = self.layer_manager.list_layouts()
        
        if not layouts:
            messagebox.showinfo("Info", "No saved layouts found")
            return
        
        # Create layout manager window
        mgr_window = tk.Toplevel(self)
        mgr_window.title("Manage Layouts")
        mgr_window.geometry("700x500")
        
        # Listbox with layouts
        tk.Label(mgr_window, text="Saved Layouts:", font=("Arial", 12, "bold")).pack(pady=10)
        
        frame = tk.Frame(mgr_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for layout in layouts:
            display_text = f"{layout['name']} | {layout['description'][:30] if layout['description'] else 'No description'}"
            listbox.insert(tk.END, display_text)
        
        # Buttons
        button_frame = tk.Frame(mgr_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def load_selected():
            sel = listbox.curselection()
            if sel:
                filepath = layouts[sel[0]]['filepath']
                self.load_layout_direct(filepath)
                mgr_window.destroy()
        
        def delete_selected():
            sel = listbox.curselection()
            if sel:
                filepath = layouts[sel[0]]['filepath']
                if messagebox.askyesno("Delete", f"Delete layout: {layouts[sel[0]]['name']}?"):
                    self.layer_manager.delete_layout(filepath)
                    messagebox.showinfo("Success", "Layout deleted")
                    mgr_window.destroy()
        
        tk.Button(button_frame, text="Load Selected", command=load_selected, bg='#27ae60', fg='white', padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Selected", command=delete_selected, bg='#e74c3c', fg='white', padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=mgr_window.destroy, bg='#95a5a6', fg='white', padx=15, pady=8).pack(side=tk.RIGHT, padx=5)
    
    def load_layout_direct(self, filepath: str):
        """Load layout from filepath"""
        try:
            layout = self.layer_manager.load_layout(filepath)
            
            # Load all layers from layout
            for layer_data in layout.layers:
                layer = LayerInfo(**layer_data)
                
                if layer.layer_type == "dem" and os.path.exists(layer.file_path):
                    try:
                        if layer.file_path.endswith('.npy'):
                            self.current_dem = np.load(layer.file_path)
                        elif layer.file_path.endswith(('.tif', '.tiff')):
                            import rasterio
                            with rasterio.open(layer.file_path) as src:
                                self.current_dem = src.read(1).astype(np.float32)
                        elif layer.file_path.endswith(('.asc', '.grd')):
                            self.current_dem = np.loadtxt(layer.file_path, skiprows=6)
                        
                        if self.current_dem is not None:
                            self.current_dem_path = layer.file_path
                            dem = cast(np.ndarray, self.current_dem)
                            self.dem_status.config(
                                text=f"Status: Loaded ({dem.shape[0]}x{dem.shape[1]})",
                                fg='#27ae60'
                            )
                            logger.info(f"Loaded DEM from layout: {layer.file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load DEM from layout: {e}")
                
                elif layer.layer_type == "base_map" and os.path.exists(layer.file_path):
                    try:
                        if layer.file_path.endswith(('.shp')):
                            import geopandas as gpd
                            gdf = gpd.read_file(layer.file_path)
                            from rasterio.features import geometry_mask
                            from rasterio.transform import from_bounds
                            bounds = gdf.total_bounds
                            shapes = [geom for geom in gdf.geometry]
                            self.current_map = geometry_mask(shapes, out_shape=(256, 256),
                                                            transform=from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], 256, 256),
                                                            invert=True).astype(np.float32)
                            self.current_map = (self.current_map - self.current_map.min()) / (self.current_map.max() - self.current_map.min() + 1e-8)
                        elif layer.file_path.endswith(('.tif', '.tiff')):
                            import rasterio
                            with rasterio.open(layer.file_path) as src:
                                self.current_map = src.read(1).astype(np.float32)
                                self.current_map = (self.current_map - self.current_map.min()) / (self.current_map.max() - self.current_map.min() + 1e-8)
                        elif layer.file_path.endswith('.npy'):
                            self.current_map = np.load(layer.file_path)
                        
                        if self.current_map is not None:
                            self.current_map_path = layer.file_path
                            map_data = cast(np.ndarray, self.current_map)
                            self.map_status.config(
                                text=f"Status: Loaded ({map_data.shape[0]}x{map_data.shape[1]})",
                                fg='#27ae60'
                            )
                            logger.info(f"Loaded base map from layout: {layer.file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load base map from layout: {e}")
            
            messagebox.showinfo("Success", f"Layout loaded:\n{layout.name}")
            logger.info(f"Layout loaded: {layout.name}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load layout:\n{e}")
            logger.error(f"Error loading layout: {e}")