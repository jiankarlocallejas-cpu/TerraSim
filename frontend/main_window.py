"""
TerraSim Main Application Window
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import logging
import os
import threading
import json
import csv
from typing import Optional, cast, Dict, Any
from datetime import datetime

# GIS and data handling
import geopandas as gpd  # type: ignore
import rasterio  # type: ignore

# Visualization imports for 2D and 3D
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # type: ignore
from matplotlib.figure import Figure  # type: ignore
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
import matplotlib.cm as cm  # type: ignore
from matplotlib.colors import Normalize  # type: ignore

# Additional visualization
try:
    import plotly.graph_objects as go
except ImportError:
    go = None  # Plotly is optional

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
    
    def _create_main_ui(self):
        """Create main UI layout with QGIS-like interface"""
        # Color scheme - Modern dark theme with cyan accents
        self.primary_color = "#63f588"
        self.secondary_color = "#0c7e09"
        self.accent_color = '#00d4ff'
        self.text_color = '#ffffff'
        self.bg_light = '#f5f5f5'
        
        # Top menu bar
        self._create_menu_bar()
        
        # Ribbon toolbar system
        self._create_ribbon_toolbar()
        
        # Main content area with panels
        main_container = tk.Frame(self, bg=self.primary_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar (Layers & Tools)
        left_panel = tk.Frame(main_container, bg=self.secondary_color, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=0, pady=0)
        left_panel.pack_propagate(False)
        self._create_left_panel(left_panel)
        
        # Center canvas area
        center_area = tk.Frame(main_container, bg=self.primary_color)
        center_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.content_frame = tk.Frame(center_area, bg='white', relief=tk.SUNKEN, bd=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self._show_welcome_screen()
        
        # Right sidebar (Properties & Inspector)
        right_panel = tk.Frame(main_container, bg=self.secondary_color, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=0, pady=0)
        right_panel.pack_propagate(False)
        self._create_right_panel(right_panel)
        
        # Status bar
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """Create modern menu bar"""
        menubar_frame = tk.Frame(self, bg=self.secondary_color, height=30)
        menubar_frame.pack(fill=tk.X, padx=0, pady=0)
        menubar_frame.pack_propagate(False)
        
        # Menu buttons
        menu_items = [
            ('File', self._create_file_menu),
            ('Data', self._create_data_menu),
            ('Simulation', self._create_simulation_menu),
            ('Analysis', self._create_analysis_menu),
            ('Visualization', self._create_visualization_menu),
            ('Tools', self._create_tools_menu),
            ('Help', self._create_help_menu),
        ]
        
        for label, menu_func in menu_items:
            self._create_menu_button(menubar_frame, label, menu_func)
    
    def _create_menu_button(self, parent, label, menu_func):
        """Create a menu button with dropdown"""
        btn = tk.Button(
            parent,
            text=label,
            font=("Arial", 9, "bold"),
            bg=self.secondary_color,
            fg=self.text_color,
            relief=tk.FLAT,
            padx=12,
            pady=5,
            command=menu_func
        )
        btn.pack(side=tk.LEFT, padx=2)
        
        btn.bind('<Enter>', lambda e: btn.config(bg=self.accent_color, fg=self.primary_color))
        btn.bind('<Leave>', lambda e: btn.config(bg=self.secondary_color, fg=self.text_color))
    
    def _create_file_menu(self):
        """Create File menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="📁 Load DEM", command=self.load_dem)
        menubar.add_command(label="📂 Load Base Map", command=self.load_map)
        menubar.add_command(label="⚙️  Load Parameters", command=self.load_parameters)
        menubar.add_command(label="✏️  Edit Parameters", command=self.edit_parameters)
        menubar.add_command(label="➕ Add Parameter", command=self.add_parameter)
        menubar.add_command(label="📋 Default Parameters", command=self.load_default_parameters)
        menubar.add_separator()
        menubar.add_command(label="💾 Save Layout", command=self.save_layout)
        menubar.add_command(label="📥 Load Layout", command=self.load_layout)
        menubar.add_separator()
        menubar.add_command(label="❌ Exit", command=self.quit)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_data_menu(self):
        """Create Data menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="� Load DEM", command=self.load_dem)
        menubar.add_command(label="�🗺️  Generate Sample DEM", command=self.generate_sample_dem)
        menubar.add_command(label="📊 Load Raster", command=self.load_map)
        menubar.add_command(label="🎯 Load Shapefile", command=self.load_shapefile)
        menubar.add_separator()
        menubar.add_command(label="🔄 Reproject", command=self.show_reproject_dialog)
        menubar.add_command(label="✂️  Clip", command=self.show_clip_dialog)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_simulation_menu(self):
        """Create Simulation menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="▶️  Single Run", command=self.run_single_simulation)
        menubar.add_command(label="📈 Time Series", command=self.run_time_series)
        menubar.add_command(label="🔬 Sensitivity Analysis", command=self.run_sensitivity)
        menubar.add_separator()
        menubar.add_command(label="🚀 USPED Workflow", command=self.run_usped_workflow)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_analysis_menu(self):
        """Create Analysis menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="📐 Slope Analysis", command=self.slope_analysis)
        menubar.add_command(label="🌊 Flow Accumulation", command=self.flow_analysis)
        menubar.add_command(label="⛰️  Aspect", command=self.aspect_analysis)
        menubar.add_separator()
        menubar.add_command(label="📊 Statistics", command=self.show_statistics)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_visualization_menu(self):
        """Create Visualization menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="🗻 DEM 3D Surface", command=self.visualize_dem_3d)
        menubar.add_command(label="🌍 Erosion 3D", command=self.visualize_erosion_3d)
        menubar.add_command(label="💫 Interactive 3D (Plotly)", command=self.create_interactive_3d_plot)
        menubar.add_separator()
        menubar.add_command(label="🎨 Styling", command=self.show_styling_dialog)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_tools_menu(self):
        """Create Tools menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="🔍 Measure", command=self.show_measure_tool)
        menubar.add_command(label="✏️  Annotate", command=self.show_annotate_tool)
        menubar.add_separator()
        menubar.add_command(label="⚙️  Preferences", command=self.show_preferences)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_help_menu(self):
        """Create Help menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="📖 Documentation", command=self.show_documentation)
        menubar.add_command(label="❓ About TerraSim", command=self.show_about)
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_parameters_menu(self):
        """Create Parameters menu"""
        menubar = tk.Menu(self, tearoff=1, bg=self.secondary_color, fg=self.text_color, activebackground=self.accent_color)
        menubar.add_command(label="📥 Load Parameters", command=self.load_parameters)
        menubar.add_command(label="⚙️  Load Defaults", command=self.load_default_parameters)
        menubar.add_command(label="✏️  Edit Parameters", command=self.edit_parameters)
        menubar.add_command(label="➕ Add Parameter", command=self.add_parameter)
        menubar.add_separator()
        menubar.add_command(label="💾 Export Parameters", command=lambda: self.export_parameters_dialog())
        menubar.post(self.winfo_pointerx(), self.winfo_pointery())
    
    def _create_ribbon_toolbar(self):
        """Create ribbon toolbar system inspired by QGIS"""
        ribbon_frame = tk.Frame(self, bg=self.secondary_color, height=100)
        ribbon_frame.pack(fill=tk.X, padx=0, pady=0)
        ribbon_frame.pack_propagate(False)
        
        # Ribbon title
        title_frame = tk.Frame(ribbon_frame, bg=self.secondary_color)
        title_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=(8, 5))
        
        tk.Label(
            title_frame,
            text="TerraSim - Advanced Erosion Modeling System",
            font=("Arial", 11, "bold"),
            bg=self.secondary_color,
            fg=self.accent_color
        ).pack(side=tk.LEFT)
        
        # Ribbon groups
        groups_frame = tk.Frame(ribbon_frame, bg=self.secondary_color)
        groups_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File & Data group
        self._create_ribbon_group(groups_frame, "FILE & DATA", [
            ("Load DEM", self.load_dem, "📁"),
            ("Load Map", self.load_map, "📂"),
            ("Sample", self.generate_sample_dem, "🎲"),
        ])
        
        # Simulation group
        self._create_ribbon_group(groups_frame, "SIMULATION", [
            ("Single Run", self.run_single_simulation, "▶️"),
            ("Time Series", self.run_time_series, "📈"),
            ("Sensitivity", self.run_sensitivity, "🔬"),
        ])
        
        # Visualization group
        self._create_ribbon_group(groups_frame, "VISUALIZATION", [
            ("DEM 3D", self.visualize_dem_3d, "🗻"),
            ("Erosion 3D", self.visualize_erosion_3d, "🌍"),
            ("Plotly", self.create_interactive_3d_plot, "💫"),
        ])
        
        # Analysis group
        self._create_ribbon_group(groups_frame, "ANALYSIS", [
            ("Slope", self.slope_analysis, "📐"),
            ("Flow", self.flow_analysis, "🌊"),
            ("Aspect", self.aspect_analysis, "⛰️"),
        ])
        
        # Parameters group
        self._create_ribbon_group(groups_frame, "PARAMETERS", [
            ("Load", self.load_parameters, "📥"),
            ("Edit", self.edit_parameters, "✏️"),
            ("Default", self.load_default_parameters, "📋"),
        ])
    
    def _create_ribbon_group(self, parent, group_name, buttons):
        """Create a ribbon group with buttons"""
        group_frame = tk.LabelFrame(
            parent,
            text=group_name,
            font=("Arial", 8, "bold"),
            bg=self.secondary_color,
            fg=self.accent_color,
            padx=8,
            pady=6,
            relief=tk.FLAT
        )
        group_frame.pack(side=tk.LEFT, padx=3, fill=tk.BOTH)
        
        for label, command, icon in buttons:
            btn = tk.Button(
                group_frame,
                text=f"{icon}\n{label}",
                font=("Arial", 7),
                bg='#3d3d5c',
                fg=self.text_color,
                relief=tk.FLAT,
                padx=12,
                pady=8,
                command=command,
                wraplength=60
            )
            btn.pack(side=tk.LEFT, padx=2, fill=tk.BOTH, expand=True)
            
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.accent_color, fg=self.primary_color))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#3d3d5c', fg=self.text_color))
    
    def _create_left_panel(self, parent):
        """Create left panel with Layers and Tools"""
        # Header
        header = tk.Frame(parent, bg=self.accent_color)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(
            header,
            text="LAYERS & TOOLS",
            font=("Arial", 9, "bold"),
            bg=self.accent_color,
            fg=self.primary_color
        ).pack(fill=tk.X, padx=10, pady=8)
        
        # Notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Style the notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.secondary_color)
        style.configure('TNotebook.Tab', font=("Arial", 8))
        
        # Layers tab
        layers_frame = tk.Frame(notebook, bg=self.secondary_color)
        notebook.add(layers_frame, text="📚 Layers")
        self._create_layers_tab(layers_frame)
        
        # Tools tab
        tools_frame = tk.Frame(notebook, bg=self.secondary_color)
        notebook.add(tools_frame, text="🔧 Tools")
        self._create_tools_tab(tools_frame)
        
        # History tab
        history_frame = tk.Frame(notebook, bg=self.secondary_color)
        notebook.add(history_frame, text="📝 History")
        self._create_history_tab(history_frame)
    
    def _create_layers_tab(self, parent):
        """Create layers panel"""
        # Add layer button
        btn_frame = tk.Frame(parent, bg=self.secondary_color)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            btn_frame,
            text="+ Add Layer",
            font=("Arial", 8, "bold"),
            bg=self.accent_color,
            fg=self.primary_color,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.load_dem
        ).pack(fill=tk.X)
        
        # Layers listbox
        self.layers_listbox = tk.Listbox(
            parent,
            bg='white',
            fg=self.primary_color,
            font=("Arial", 9),
            selectmode=tk.MULTIPLE,
            relief=tk.FLAT
        )
        self.layers_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add sample layers
        for layer in ["Base Map", "DEM", "Erosion Model", "Results"]:
            self.layers_listbox.insert(tk.END, f"  {layer}")
    
    def _create_tools_tab(self, parent):
        """Create tools panel"""
        tools_list = [
            ("🔍 Selection Tool", self.select_tool),
            ("✏️  Edit Tool", self.edit_tool),
            ("🔍 Measure Tool", self.show_measure_dialog),
            ("✋ Pan Tool", self.pan_tool),
            ("🔎 Zoom In", self.zoom_in),
            ("🔍 Zoom Out", self.zoom_out),
            ("🏠 Fit to View", self.fit_to_view),
        ]
        
        for label, command in tools_list:
            btn = tk.Button(
                parent,
                text=label,
                font=("Arial", 8),
                bg='#3d3d5c',
                fg=self.text_color,
                relief=tk.FLAT,
                padx=10,
                pady=6,
                command=command
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
            
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.accent_color, fg=self.primary_color))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#3d3d5c', fg=self.text_color))
    
    def _create_history_tab(self, parent):
        """Create history panel"""
        tk.Label(
            parent,
            text="Operation History",
            font=("Arial", 8, "bold"),
            bg=self.secondary_color,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=10, pady=10)
        
        self.history_listbox = tk.Listbox(
            parent,
            bg='white',
            fg=self.primary_color,
            font=("Arial", 8),
            relief=tk.FLAT
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _create_right_panel(self, parent):
        """Create right panel with Properties and Inspector"""
        # Header
        header = tk.Frame(parent, bg=self.accent_color)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(
            header,
            text="PROPERTIES & INSPECTOR",
            font=("Arial", 9, "bold"),
            bg=self.accent_color,
            fg=self.primary_color
        ).pack(fill=tk.X, padx=10, pady=8)
        
        # Notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Properties tab
        props_frame = tk.Frame(notebook, bg=self.secondary_color)
        notebook.add(props_frame, text="⚙️  Properties")
        self._create_properties_tab(props_frame)
        
        # Inspector tab
        inspector_frame = tk.Frame(notebook, bg=self.secondary_color)
        notebook.add(inspector_frame, text="🔍 Inspector")
        self._create_inspector_tab(inspector_frame)
    
    def _create_properties_tab(self, parent):
        """Create properties panel"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg=self.secondary_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.secondary_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Sample properties
        properties = [
            ("DEM Status:", "No DEM loaded"),
            ("Dimensions:", "Not available"),
            ("Resolution:", "N/A"),
            ("CRS:", "Unknown"),
            ("Extent:", "Not loaded"),
        ]
        
        for prop_name, prop_value in properties:
            prop_frame = tk.Frame(scrollable_frame, bg=self.secondary_color)
            prop_frame.pack(fill=tk.X, padx=10, pady=4)
            
            tk.Label(
                prop_frame,
                text=prop_name,
                font=("Arial", 8, "bold"),
                bg=self.secondary_color,
                fg=self.accent_color
            ).pack(anchor=tk.W)
            
            tk.Label(
                prop_frame,
                text=prop_value,
                font=("Arial", 8),
                bg=self.secondary_color,
                fg=self.text_color
            ).pack(anchor=tk.W, padx=(10, 0))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_inspector_tab(self, parent):
        """Create inspector panel"""
        tk.Label(
            parent,
            text="Layer Inspector",
            font=("Arial", 8, "bold"),
            bg=self.secondary_color,
            fg=self.text_color
        ).pack(anchor=tk.W, padx=10, pady=10)
        
        inspector_text = tk.Text(
            parent,
            bg='white',
            fg=self.primary_color,
            font=("Courier", 8),
            height=20,
            width=30,
            relief=tk.FLAT
        )
        inspector_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        inspector_text.insert(1.0, "Select a layer to inspect")
        inspector_text.config(state=tk.DISABLED)
    
    def _create_status_bar(self):
        """Create status bar at the bottom"""
        status_frame = tk.Frame(self, bg=self.secondary_color, height=25)
        status_frame.pack(fill=tk.X, padx=0, pady=0, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready | Zoom: 100% | Coordinates: (0.0, 0.0)",
            font=("Arial", 8),
            bg=self.secondary_color,
            fg=self.text_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Initialize status labels for data loading
        self.dem_status = tk.Label(status_frame, text="DEM: Not loaded", font=("Arial", 8), bg=self.secondary_color, fg='#e74c3c')
        self.map_status = tk.Label(status_frame, text="Map: Not loaded", font=("Arial", 8), bg=self.secondary_color, fg='#e74c3c')
        self.params_status = tk.Label(status_frame, text="Parameters: Not loaded", font=("Arial", 8), bg=self.secondary_color, fg='#e74c3c')
    
    # Tool stubs
    def select_tool(self):
        """Selection tool"""
        self.status_label.config(text="Selection tool active")
    
    def edit_tool(self):
        """Edit tool"""
        self.status_label.config(text="Edit tool active")
    
    def pan_tool(self):
        """Pan tool"""
        self.status_label.config(text="Pan tool active")
    
    def zoom_in(self):
        """Zoom in"""
        self.status_label.config(text="Zoom in | Use mouse wheel or drag to zoom")
    
    def zoom_out(self):
        """Zoom out"""
        self.status_label.config(text="Zoom out | Use mouse wheel or drag to zoom")
    
    def fit_to_view(self):
        """Fit to view"""
        self.status_label.config(text="Fitted view to current layers")
    
    def show_reproject_dialog(self):
        """Show reproject dialog"""
        messagebox.showinfo("Reproject", "Reproject dialog would open here")
    
    def show_clip_dialog(self):
        """Show clip dialog"""
        messagebox.showinfo("Clip", "Clip dialog would open here")
    
    def load_shapefile(self):
        """Load shapefile"""
        messagebox.showinfo("Load Shapefile", "Shapefile loader would open here")
    
    def slope_analysis(self):
        """Slope analysis"""
        messagebox.showinfo("Slope Analysis", "Slope analysis would be performed")
    
    def flow_analysis(self):
        """Flow accumulation analysis"""
        messagebox.showinfo("Flow Analysis", "Flow accumulation would be calculated")
    
    def aspect_analysis(self):
        """Aspect analysis"""
        messagebox.showinfo("Aspect Analysis", "Aspect analysis would be performed")
    
    def show_statistics(self):
        """Show statistics"""
        messagebox.showinfo("Statistics", "Statistics viewer would open here")
    
    def show_styling_dialog(self):
        """Show styling dialog"""
        messagebox.showinfo("Styling", "Layer styling dialog would open here")
    
    def show_measure_tool(self):
        """Show measure tool"""
        messagebox.showinfo("Measure Tool", "Measure tool is active. Use mouse to measure distances.")
    
    def show_measure_dialog(self):
        """Show measure dialog"""
        self.show_measure_tool()
    
    def show_annotate_tool(self):
        """Show annotation tool"""
        messagebox.showinfo("Annotate", "Annotation tool would open here")
    
    def show_preferences(self):
        """Show preferences"""
        messagebox.showinfo("Preferences", "Preferences dialog would open here")
    
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
    
    def _display_dem_visualization(self):
        """Display loaded DEM as a 2D heatmap in the content frame"""
        if self.current_dem is None:
            return
        
        # Clear previous content (but not the right panel)
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        dem = cast(np.ndarray, self.current_dem)
        
        # Create figure and plot
        fig = Figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Display DEM as heatmap
        im = ax.imshow(dem, cmap='terrain', aspect='auto', origin='upper')
        ax.set_title(f'Loaded DEM ({dem.shape[0]}x{dem.shape[1]})', fontsize=12, fontweight='bold')
        ax.set_xlabel('X (cells)')
        ax.set_ylabel('Y (cells)')
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, label='Elevation (m)')
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
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
                # Display the DEM in the content frame
                self._display_dem_visualization()
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
                # Display the DEM visualization
                self._display_dem_visualization()
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
            # Display the generated DEM
            self._display_dem_visualization()
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
        edit_window.geometry("550x650")
        edit_window.transient(self)
        edit_window.grab_set()
        
        # Title
        title_label = tk.Label(
            edit_window,
            text="Edit Simulation Parameters",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(fill=tk.X, padx=10, pady=10)
        
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
            frame = tk.Frame(scrollable_frame, bg='white', relief=tk.RAISED, bd=1)
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
        
        def add_param_inline():
            """Add a new parameter directly from edit dialog"""
            add_inline_dialog = tk.Toplevel(edit_window)
            add_inline_dialog.title("Add Parameter")
            add_inline_dialog.geometry("350x200")
            add_inline_dialog.transient(edit_window)
            add_inline_dialog.grab_set()
            
            tk.Label(add_inline_dialog, text="Parameter Name:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=15, pady=(10, 0))
            name_entry = tk.Entry(add_inline_dialog, font=("Arial", 10), width=30)
            name_entry.pack(padx=15, pady=5)
            name_entry.focus()
            
            tk.Label(add_inline_dialog, text="Parameter Value:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=15, pady=(5, 0))
            value_entry = tk.Entry(add_inline_dialog, font=("Arial", 10), width=30)
            value_entry.pack(padx=15, pady=5)
            
            def add_it():
                name = name_entry.get().strip()
                value = value_entry.get().strip()
                
                if not name or not value:
                    messagebox.showwarning("Warning", "Please enter both name and value")
                    return
                
                # Try to convert to float
                try:
                    converted_value = float(value)
                except ValueError:
                    converted_value = value
                
                # Add to current parameters
                if self.current_parameters is not None:
                    self.current_parameters[name] = converted_value
                    param_entries[name] = None  # Mark as new
                
                # Add to UI in scrollable frame
                frame = tk.Frame(scrollable_frame, bg='#e8f8f5', relief=tk.RAISED, bd=1)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                tk.Label(
                    frame,
                    text=f"{name}:",
                    font=("Arial", 10),
                    bg='#e8f8f5',
                    fg='#27ae60',
                    width=20,
                    anchor=tk.W
                ).pack(side=tk.LEFT, padx=5)
                
                entry = tk.Entry(frame, font=("Arial", 10), width=20)
                entry.insert(0, str(converted_value))
                entry.pack(side=tk.RIGHT, padx=5)
                param_entries[name] = entry
                
                # Refresh scroll region
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                logger.info(f"Added parameter in dialog: {name} = {converted_value}")
                messagebox.showinfo("Success", f"Parameter '{name}' added!")
                add_inline_dialog.destroy()
            
            btn_frame = tk.Frame(add_inline_dialog)
            btn_frame.pack(pady=15)
            
            tk.Button(
                btn_frame,
                text="Add",
                font=("Arial", 10, "bold"),
                bg='#27ae60',
                fg='white',
                padx=20,
                command=add_it
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                btn_frame,
                text="Cancel",
                font=("Arial", 10, "bold"),
                bg='#e74c3c',
                fg='white',
                padx=20,
                command=add_inline_dialog.destroy
            ).pack(side=tk.LEFT, padx=5)
        
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
            text="➕ Add Parameter",
            font=("Arial", 9, "bold"),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=8,
            command=add_param_inline
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Export",
            font=("Arial", 9),
            bg='#f39c12',
            fg='white',
            padx=15,
            pady=8,
            command=lambda: self._export_parameters(param_entries)
        ).pack(side=tk.RIGHT, padx=5)
    
    def add_parameter(self):
        """Add a new parameter to the current parameters"""
        if self.current_parameters is None:
            response = messagebox.askyesno(
                "No Parameters",
                "No parameters are currently loaded. Create new parameters with defaults first?"
            )
            if response:
                self.current_parameters = self._get_default_parameters()
                self._refresh_params_status()
            else:
                return
        
        # Create add parameter dialog
        add_dialog = tk.Toplevel(self)
        add_dialog.title("Add New Parameter")
        add_dialog.geometry("400x250")
        add_dialog.transient(self)
        add_dialog.grab_set()
        
        # Title
        tk.Label(
            add_dialog,
            text="Add New Simulation Parameter",
            font=("Arial", 12, "bold"),
            fg='#2c3e50'
        ).pack(pady=15, padx=10)
        
        # Parameter name
        tk.Label(add_dialog, text="Parameter Name:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(5, 0))
        name_entry = tk.Entry(add_dialog, font=("Arial", 10), width=35)
        name_entry.pack(padx=20, pady=5)
        name_entry.focus()
        
        # Parameter value
        tk.Label(add_dialog, text="Parameter Value:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 0))
        value_entry = tk.Entry(add_dialog, font=("Arial", 10), width=35)
        value_entry.pack(padx=20, pady=5)
        
        # Parameter description (optional)
        tk.Label(add_dialog, text="Description (optional):", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 0))
        desc_entry = tk.Entry(add_dialog, font=("Arial", 9), width=35)
        desc_entry.pack(padx=20, pady=5)
        
        # Buttons
        button_frame = tk.Frame(add_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def add_new_param():
            param_name = name_entry.get().strip()
            param_value = value_entry.get().strip()
            
            if not param_name:
                messagebox.showwarning("Warning", "Please enter a parameter name")
                return
            
            if not param_value:
                messagebox.showwarning("Warning", "Please enter a parameter value")
                return
            
            # Check if parameter already exists
            if self.current_parameters is not None and param_name in self.current_parameters:
                response = messagebox.askyesno(
                    "Parameter Exists",
                    f"Parameter '{param_name}' already exists. Overwrite it?"
                )
                if not response:
                    return
            
            # Try to convert to float, otherwise store as string
            if self.current_parameters is not None:
                try:
                    self.current_parameters[param_name] = float(param_value)
                except ValueError:
                    self.current_parameters[param_name] = param_value
            
            logger.info(f"Added parameter: {param_name} = {param_value}")
            self._refresh_params_status()
            messagebox.showinfo(
                "Success",
                f"Parameter '{param_name}' added successfully!\n"
                f"Value: {param_value}"
            )
            add_dialog.destroy()
        
        tk.Button(
            button_frame,
            text="Add Parameter",
            font=("Arial", 10, "bold"),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            command=add_new_param
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            command=add_dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def export_parameters_dialog(self):
        """Export parameters to file - called from menu"""
        if self.current_parameters is None:
            messagebox.showwarning("Warning", "Please load parameters first")
            return
        
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
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(self.current_parameters, f, indent=2)
                
                elif file_path.endswith('.csv'):
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(self.current_parameters.keys())
                        writer.writerow(self.current_parameters.values())
                
                elif file_path.endswith('.npy'):
                    np.save(file_path, np.array([self.current_parameters], dtype=object))
                
                messagebox.showinfo("Success", f"Parameters exported to:\n{file_path}")
                logger.info(f"Parameters exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export parameters: {e}")
    
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
    
    def _on_simulation_complete(self):
        """Called when simulation completes"""
        self._update_history()
        self._show_split_screens()
    
    def _on_time_series_complete(self):
        """Called when time series simulation completes"""
        self._update_history()
    
    def _show_split_screens(self):
        """Display calculation and results screens side by side"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create a frame to hold both screens side by side
        split_frame = tk.Frame(self.content_frame, bg='white')
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Calculation/Simulation screen
        left_frame = tk.Frame(split_frame, bg='white', relief=tk.SUNKEN, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        calc_screen = CalculationScreen(
            left_frame,
            on_complete=None  # No callback needed when displayed alongside results
        )
        calc_screen.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Results screen
        right_frame = tk.Frame(split_frame, bg='white', relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
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
                right_frame,
                serialized_result
            )
            result_screen.pack(fill=tk.BOTH, expand=True)
    
    def _show_result_screen(self):
        """Display results screen only"""
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
        """Display DEM in 3D surface plot (non-blocking)"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        def create_plot_async():
            """Create 3D plot in background to prevent UI blocking"""
            try:
                if self.current_dem is None:
                    logger.warning("No DEM loaded for 3D visualization")
                    return
                
                # Create 3D plot window
                fig = Figure(figsize=(10, 8), dpi=100)
                ax = fig.add_subplot(111, projection='3d')
                
                # Create mesh grid
                dem_data = self.current_dem
                x = np.arange(dem_data.shape[1])
                y = np.arange(dem_data.shape[0])
                X, Y = np.meshgrid(x, y)
                
                # Plot surface with improved colormap
                surf = ax.plot_surface(X, Y, dem_data, cmap='gist_earth', alpha=0.85, edgecolor='none')
                
                # Customize plot
                ax.set_xlabel('X (pixels)', fontweight='bold')
                ax.set_ylabel('Y (pixels)', fontweight='bold')
                ax.set_zlabel('Elevation (m)', fontweight='bold')
                ax.set_title('Digital Elevation Model - 3D View', fontsize=14, fontweight='bold')
                
                # Add colorbar
                fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevation (m)')
                
                # Set viewing angle
                ax.view_init(elev=25, azim=45)
                
                # Schedule UI creation on main thread
                self.after(0, lambda: self._show_dem_3d_plot(fig, ax))
                logger.info("3D DEM visualization created")
                
            except Exception as e:
                logger.error(f"Error creating 3D visualization: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to create 3D visualization: {str(e)}"))
        
        # Run plot creation in background thread
        thread = threading.Thread(target=create_plot_async, daemon=True)
        thread.start()
    
    def _show_dem_3d_plot(self, fig, ax):
        """Display DEM 3D plot window (called on main thread)"""
        # Create tkinter window for plot
        plot_window = tk.Toplevel(self)
        plot_window.title("3D DEM Visualization")
        plot_window.geometry("900x700")
        
        # Use non-blocking draw
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw_idle()  # Non-blocking draw
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add rotation controls
        control_frame = tk.Frame(plot_window)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(control_frame, text="View Angle:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        def update_view(elev, azim):
            ax.view_init(elev=elev, azim=azim)
            canvas.draw_idle()  # Non-blocking draw
        
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
    
    def visualize_erosion_3d(self):
        """Display erosion results in 3D (non-blocking)"""
        if self.current_result is None:
            messagebox.showwarning("Warning", "Please run a simulation first")
            return
        
        if not hasattr(self.current_result, 'erosion_rate') or self.current_result.erosion_rate is None:
            messagebox.showwarning("Warning", "No erosion data available")
            return
        
        def create_erosion_plot_async():
            """Create erosion 3D plot in background to prevent UI blocking"""
            try:
                if self.current_result is None or self.current_result.erosion_rate is None:
                    logger.warning("No simulation results available")
                    return
                
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
                surf = ax.plot_surface(X, Y, combined, cmap='RdYlGn', alpha=0.85, edgecolor='none')
                
                # Customize plot
                ax.set_xlabel('X (pixels)', fontweight='bold')
                ax.set_ylabel('Y (pixels)', fontweight='bold')
                ax.set_zlabel('Elevation + Erosion (m)', fontweight='bold')
                ax.set_title('Erosion Analysis - 3D View', fontsize=14, fontweight='bold')
                
                # Add colorbar
                fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Elevation + Erosion (m)')
                
                # Set viewing angle
                ax.view_init(elev=25, azim=45)
                
                # Schedule UI creation on main thread
                self.after(0, lambda: self._show_erosion_3d_plot(fig, ax))
                logger.info("3D erosion visualization created")
                
            except Exception as e:
                logger.error(f"Error creating 3D erosion visualization: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to create 3D visualization: {str(e)}"))
        
        # Run plot creation in background thread
        thread = threading.Thread(target=create_erosion_plot_async, daemon=True)
        thread.start()
    
    def _show_erosion_3d_plot(self, fig, ax):
        """Display erosion 3D plot window (called on main thread)"""
        # Create tkinter window for plot
        plot_window = tk.Toplevel(self)
        plot_window.title("3D Erosion Visualization")
        plot_window.geometry("900x700")
        
        # Use non-blocking draw
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw_idle()  # Non-blocking draw
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add rotation controls
        control_frame = tk.Frame(plot_window)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(control_frame, text="View Angle:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        def update_view(elev, azim):
            ax.view_init(elev=elev, azim=azim)
            canvas.draw_idle()  # Non-blocking draw
        
        tk.Button(control_frame, text="Top View", command=lambda: update_view(90, 0)).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Side View", command=lambda: update_view(0, 0)).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Isometric", command=lambda: update_view(25, 45)).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="3D View", command=lambda: update_view(35, 120)).pack(side=tk.LEFT, padx=2)
        
        logger.info("Opened 3D erosion visualization")
    
    def create_interactive_3d_plot(self):
        """Create interactive 3D plot using Plotly (non-blocking)"""
        if self.current_dem is None:
            messagebox.showwarning("Warning", "Please load or generate a DEM first")
            return
        
        if go is None:
            messagebox.showerror(
                "Error",
                "Plotly is not installed. Install it with: pip install plotly"
            )
            return
        
        def create_plotly_async():
            """Create Plotly visualization in background thread"""
            try:
                if go is None:
                    logger.error("Plotly not available for visualization")
                    self.after(0, lambda: messagebox.showerror("Error", "Plotly is not installed. Install it with: pip install plotly"))
                    return
                
                if self.current_dem is None:
                    logger.warning("No DEM loaded for Plotly visualization")
                    return
                
                dem_data = self.current_dem
                if dem_data is None:
                    logger.warning("DEM data is None")
                    return
                
                # Create plotly 3D surface plot with improved colorscale
                fig = go.Figure(data=[go.Surface(z=dem_data, colorscale='Viridis')])
                
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
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to create interactive visualization: {str(e)}"))
        
        # Run Plotly creation in background thread
        thread = threading.Thread(target=create_plotly_async, daemon=True)
        thread.start()
    
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