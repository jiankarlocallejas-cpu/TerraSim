"""
Enhanced Calculation Screen - Parameters, simulation progress, and 3D visualization
"""

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, Any
import logging
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger(__name__)


class ParametersPanel(tk.Frame):
    """Panel for editing simulation parameters"""
    
    # Default parameter ranges
    PARAM_RANGES = {
        'rainfall_erosivity': (50, 1000, 300),      # (min, max, default)
        'soil_erodibility': (0.01, 1.0, 0.35),
        'cover_factor': (0.0, 1.0, 0.3),
        'practice_factor': (0.0, 1.0, 0.5),
        'time_step_days': (0.1, 10, 1),
        'num_timesteps': (1, 100, 10),
        'bulk_density': (800, 2000, 1300),
        'area_exponent': (0.1, 2.0, 0.6),
        'slope_exponent': (0.1, 2.0, 1.3),
        'runoff_coefficient': (0.0, 1.0, 0.5),
    }
    
    def __init__(self, parent):
        super().__init__(parent, bg='#f5f5f5')
        self.parameters: Dict[str, float] = {}
        self._create_widgets()
    
    def _create_widgets(self):
        """Create parameter sliders"""
        # Header
        header = tk.Label(
            self,
            text="Simulation Parameters",
            font=("Arial", 12, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        header.pack(fill=tk.X, padx=0, pady=0)
        
        # Scrollable frame
        canvas = tk.Canvas(self, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f5')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create sliders
        self.sliders: Dict[str, tk.Scale] = {}
        self.value_labels: Dict[str, tk.Label] = {}
        
        for param_name, (min_val, max_val, default_val) in self.PARAM_RANGES.items():
            param_frame = tk.Frame(scrollable_frame, bg='#f5f5f5')
            param_frame.pack(fill=tk.X, padx=10, pady=8)
            
            # Label with value
            label_frame = tk.Frame(param_frame, bg='#f5f5f5')
            label_frame.pack(fill=tk.X)
            
            label = tk.Label(
                label_frame,
                text=self._format_param_name(param_name),
                font=("Arial", 10),
                bg='#f5f5f5'
            )
            label.pack(side=tk.LEFT)
            
            self.value_labels[param_name] = tk.Label(
                label_frame,
                text=f"{default_val}",
                font=("Arial", 10, "bold"),
                bg='#f5f5f5',
                fg='#2c3e50'
            )
            self.value_labels[param_name].pack(side=tk.RIGHT)
            
            # Slider
            slider = tk.Scale(
                param_frame,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                bg='#f5f5f5',
                highlightthickness=0,
                length=200,
                command=lambda val, pn=param_name: self._on_slider_change(pn, float(val))
            )
            slider.set(default_val)
            slider.pack(fill=tk.X)
            self.sliders[param_name] = slider
            self.parameters[param_name] = default_val
        
        # Buttons
        button_frame = tk.Frame(scrollable_frame, bg='#f5f5f5')
        button_frame.pack(fill=tk.X, padx=10, pady=15)
        
        tk.Button(
            button_frame,
            text="Reset to Defaults",
            bg='#95a5a6',
            fg='white',
            command=self.reset_to_defaults,
            padx=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Export Parameters",
            bg='#3498db',
            fg='white',
            command=self.export_parameters,
            padx=10
        ).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    @staticmethod
    def _format_param_name(name: str) -> str:
        """Format parameter name for display"""
        words = name.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    def _on_slider_change(self, param_name: str, value: float):
        """Update parameter value"""
        self.parameters[param_name] = value
        
        # Format value display (show decimals for small numbers, integers for large)
        if value < 10:
            display_val = f"{value:.2f}"
        else:
            display_val = f"{int(value) if value == int(value) else value}"
        
        self.value_labels[param_name].config(text=display_val)
    
    def reset_to_defaults(self):
        """Reset all parameters to defaults"""
        for param_name, (_, _, default_val) in self.PARAM_RANGES.items():
            self.sliders[param_name].set(default_val)
            self.parameters[param_name] = default_val
        logger.info("Parameters reset to defaults")
    
    def export_parameters(self):
        """Export current parameters"""
        logger.info(f"Current parameters: {self.parameters}")
    
    def get_parameters(self) -> Dict[str, float]:
        """Get current parameters"""
        return self.parameters.copy()


class Visualization3D(tk.Frame):
    """3D visualization using matplotlib"""
    
    def __init__(self, parent):
        super().__init__(parent, bg='white')
        self.figure: Figure
        self.canvas: FigureCanvasTkAgg
        self.ax: Optional[Axes3D] = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Create matplotlib canvas"""
        # Header
        header = tk.Label(
            self,
            text="3D Erosion Visualization",
            font=("Arial", 12, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        header.pack(fill=tk.X, padx=0, pady=0)
        
        # Canvas frame
        canvas_frame = tk.Frame(self, bg='white')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_erosion_3d(self, dem: np.ndarray, erosion_rate: np.ndarray, title: str = "Erosion Rate (m/year)"):
        """Plot 3D erosion visualization"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Create meshgrid
        rows, cols = dem.shape
        x = np.arange(0, cols)
        y = np.arange(0, rows)
        X, Y = np.meshgrid(x, y)
        
        # Plot erosion rate as 3D surface
        surf = self.ax.plot_surface(
            X, Y, erosion_rate,
            cmap='RdYlGn_r',
            alpha=0.8,
            edgecolor='none'
        )
        
        self.ax.set_xlabel('X (cells)')
        self.ax.set_ylabel('Y (cells)')
        self.ax.set_zlabel('Erosion Rate (m/year)')
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Add colorbar
        cbar = self.figure.colorbar(surf, ax=self.ax, pad=0.1, shrink=0.8)
        cbar.set_label('Erosion Rate', rotation=270, labelpad=15)
        
        self.figure.tight_layout()
        self.canvas.draw()
        logger.info("3D erosion visualization updated")
    
    def plot_elevation_change_3d(self, elevation_change: np.ndarray, title: str = "Elevation Change (m)"):
        """Plot 3D elevation change visualization"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        rows, cols = elevation_change.shape
        x = np.arange(0, cols)
        y = np.arange(0, rows)
        X, Y = np.meshgrid(x, y)
        
        # Plot elevation change
        surf = self.ax.plot_surface(
            X, Y, elevation_change,
            cmap='coolwarm',
            alpha=0.8,
            edgecolor='none'
        )
        
        self.ax.set_xlabel('X (cells)')
        self.ax.set_ylabel('Y (cells)')
        self.ax.set_zlabel('Elevation Change (m)')
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        
        cbar = self.figure.colorbar(surf, ax=self.ax, pad=0.1, shrink=0.8)
        cbar.set_label('Elevation Change', rotation=270, labelpad=15)
        
        self.figure.tight_layout()
        self.canvas.draw()
        logger.info("3D elevation change visualization updated")
    
    def clear_plot(self):
        """Clear the plot"""
        self.figure.clear()
        self.canvas.draw()


class EnhancedCalculationScreen(tk.Frame):
    """Enhanced calculation screen with parameters and 3D visualization"""
    
    def __init__(self, parent, on_complete: Optional[Callable] = None):
        super().__init__(parent, bg='#f0f0f0')
        self.on_complete = on_complete
        self.is_running = False
        self.progress_value = 0
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header_frame = tk.Frame(self, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="SIMULATION CONTROL & VISUALIZATION",
            font=("Arial", 18, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content with paned window (left: parameters, right: visualization+progress)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Parameters
        left_frame = tk.Frame(self, bg='#f5f5f5')
        self.params_panel = ParametersPanel(left_frame)
        self.params_panel.pack(fill=tk.BOTH, expand=True)
        paned.add(left_frame, weight=1)
        
        # Right panel: Visualization and Progress
        right_frame = tk.Frame(self, bg='#f0f0f0')
        
        # Notebook for tabs
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: 3D Visualization
        viz_frame = tk.Frame(notebook, bg='white')
        notebook.add(viz_frame, text="3D Visualization")
        self.viz_3d = Visualization3D(viz_frame)
        self.viz_3d.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: Progress & Status
        progress_frame = tk.Frame(notebook, bg='#f0f0f0')
        notebook.add(progress_frame, text="Progress")
        
        # Progress section
        progress_label = tk.Label(
            progress_frame,
            text="Simulation Progress",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        progress_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=400,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress_text = tk.Label(
            progress_frame,
            text="0%",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#555'
        )
        self.progress_text.pack(anchor=tk.E, padx=20, pady=(0, 20))
        
        # Status section
        status_label = tk.Label(
            progress_frame,
            text="Status Log",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        status_label.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        status_frame = tk.Frame(progress_frame, bg='white', relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.status_text = tk.Text(
            status_frame,
            height=12,
            width=60,
            font=("Courier", 9),
            bg='white',
            fg='#333',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Stats section
        stats_label = tk.Label(
            progress_frame,
            text="Statistics",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        stats_label.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        stats_frame = tk.Frame(progress_frame, bg='white', relief=tk.SUNKEN, bd=1)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.elapsed_var = tk.StringVar(value="Elapsed: 0s")
        self.estimated_var = tk.StringVar(value="Estimated: --")
        self.current_step_var = tk.StringVar(value="Current Step: 0/0")
        
        tk.Label(stats_frame, textvariable=self.elapsed_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(stats_frame, textvariable=self.estimated_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(stats_frame, textvariable=self.current_step_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        
        # Button frame
        button_frame = tk.Frame(progress_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.start_button = tk.Button(
            button_frame,
            text="Start Simulation",
            font=("Arial", 11),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            command=self.start_simulation_action
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 11),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            command=self.cancel_simulation,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        paned.add(right_frame, weight=2)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameters"""
        return self.params_panel.get_parameters()
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress bar and status"""
        self.progress_value = (current / total) * 100
        self.progress_bar['value'] = self.progress_value
        self.progress_text.config(text=f"{int(self.progress_value)}%")
        
        if message:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.status_text.see(tk.END)
        
        self.update_idletasks()
    
    def add_status_message(self, message: str, level: str = "INFO"):
        """Add message to status log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.status_text.see(tk.END)
    
    def update_stats(self, elapsed: float, estimated: float, current_step: int, total_steps: int):
        """Update statistics display"""
        self.elapsed_var.set(f"Elapsed: {self._format_time(elapsed)}")
        self.estimated_var.set(f"Estimated: {self._format_time(estimated)}")
        self.current_step_var.set(f"Current Step: {current_step}/{total_steps}")
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to readable time"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def plot_3d_erosion(self, dem: np.ndarray, erosion_rate: np.ndarray):
        """Plot 3D erosion visualization"""
        self.viz_3d.plot_erosion_3d(dem, erosion_rate)
    
    def plot_3d_elevation_change(self, elevation_change: np.ndarray):
        """Plot 3D elevation change visualization"""
        self.viz_3d.plot_elevation_change_3d(elevation_change)
    
    def start_simulation_action(self):
        """Start simulation callback"""
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.add_status_message("Simulation started with current parameters", "INFO")
    
    def cancel_simulation(self):
        """Cancel the simulation"""
        self.is_running = False
        self.cancel_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.add_status_message("Simulation cancelled by user", "WARNING")
    
    def finish_simulation(self, success: bool = True):
        """Mark simulation as complete"""
        self.is_running = False
        self.cancel_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        status_msg = "Simulation completed successfully" if success else "Simulation failed"
        self.add_status_message(status_msg, "SUCCESS" if success else "ERROR")
