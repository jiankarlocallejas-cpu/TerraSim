"""
Calculation Screen - Real-time simulation progress display with 3D matplotlib visualization
"""

import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
from typing import Callable, Optional
import logging
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger(__name__)


class Visualization3D(tk.Frame):
    """3D visualization panel using matplotlib"""
    
    def __init__(self, parent):
        super().__init__(parent, bg='white')
        self.figure = None
        self.canvas = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Create matplotlib canvas"""
        self.figure = Figure(figsize=(6, 5), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_erosion_3d(self, erosion_rate: np.ndarray, title: str = "Erosion Rate (m/year)"):
        """Plot 3D erosion visualization"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        
        rows, cols = erosion_rate.shape
        x = np.arange(0, cols)
        y = np.arange(0, rows)
        X, Y = np.meshgrid(x, y)
        
        surf = ax.plot_surface(X, Y, erosion_rate, cmap='RdYlGn_r', alpha=0.8, edgecolor='none')
        ax.set_xlabel('X (cells)', fontsize=9)
        ax.set_ylabel('Y (cells)', fontsize=9)
        ax.set_zlabel('Erosion Rate (m/year)', fontsize=9)
        ax.set_title(title, fontsize=10, fontweight='bold')
        
        cbar = self.figure.colorbar(surf, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label('Erosion Rate', rotation=270, labelpad=12, fontsize=9)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_elevation_change_3d(self, elevation_change: np.ndarray, title: str = "Elevation Change (m)"):
        """Plot 3D elevation change visualization"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        
        rows, cols = elevation_change.shape
        x = np.arange(0, cols)
        y = np.arange(0, rows)
        X, Y = np.meshgrid(x, y)
        
        surf = ax.plot_surface(X, Y, elevation_change, cmap='coolwarm', alpha=0.8, edgecolor='none')
        ax.set_xlabel('X (cells)', fontsize=9)
        ax.set_ylabel('Y (cells)', fontsize=9)
        ax.set_zlabel('Elevation Change (m)', fontsize=9)
        ax.set_title(title, fontsize=10, fontweight='bold')
        
        cbar = self.figure.colorbar(surf, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label('Elevation', rotation=270, labelpad=12, fontsize=9)
        
        self.figure.tight_layout()
        self.canvas.draw()


class CalculationScreen(tk.Frame):
    """Screen displaying real-time simulation progress with optional 3D visualization"""
    
    def __init__(self, parent, on_complete: Optional[Callable] = None, show_3d: bool = False):
        super().__init__(parent, bg='#f0f0f0')
        self.on_complete = on_complete
        self.is_running = False
        self.progress_value = 0
        self.show_3d = show_3d
        self.viz_3d = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header_frame = tk.Frame(self, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="SIMULATION IN PROGRESS",
            font=("Arial", 18, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content frame with optional paned window
        if self.show_3d:
            # Paned window: left side for progress, right side for 3D viz
            paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Left panel (progress)
            left_frame = tk.Frame(self, bg='#f0f0f0')
            self._create_progress_widgets(left_frame)
            paned.add(left_frame, weight=1)
            
            # Right panel (3D visualization)
            right_frame = tk.Frame(self, bg='white')
            self.viz_3d = Visualization3D(right_frame)
            self.viz_3d.pack(fill=tk.BOTH, expand=True)
            paned.add(right_frame, weight=1)
        else:
            # Simple progress view without 3D
            content_frame = tk.Frame(self, bg='#f0f0f0')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
            self._create_progress_widgets(content_frame)
    
    def _create_progress_widgets(self, parent):
        """Create progress and status widgets"""
        # Progress section
        progress_label = tk.Label(
            parent,
            text="Simulation Progress",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            parent,
            length=400,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        self.progress_text = tk.Label(
            parent,
            text="0%",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#555'
        )
        self.progress_text.pack(anchor=tk.E, pady=(0, 20))
        
        # Status section
        status_label = tk.Label(
            parent,
            text="Status Information",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        status_label.pack(anchor=tk.W, pady=(20, 10))
        
        # Status frame with background
        status_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.status_text = tk.Text(
            status_frame,
            height=12,
            width=60,
            font=("Courier", 10),
            bg='white',
            fg='#333',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Stats section
        stats_label = tk.Label(
            parent,
            text="Calculation Statistics",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        stats_label.pack(anchor=tk.W, pady=(20, 10))
        
        stats_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Grid of stats
        self.elapsed_var = tk.StringVar(value="Elapsed: 0s")
        self.estimated_var = tk.StringVar(value="Estimated: --")
        self.current_step_var = tk.StringVar(value="Current Step: 0/0")
        
        tk.Label(stats_frame, textvariable=self.elapsed_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(stats_frame, textvariable=self.estimated_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(stats_frame, textvariable=self.current_step_var, bg='white', font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        
        # Button frame
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=20)
        
        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 12),
            bg='#e74c3c',
            fg='white',
            padx=30,
            pady=10,
            command=self.cancel_simulation
        )
        self.cancel_button.pack(side=tk.RIGHT)
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress bar and status"""
        self.progress_value = (current / total) * 100
        self.progress_bar['value'] = self.progress_value
        self.progress_text.config(text=f"{int(self.progress_value)}%")
        
        if message:
            self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            self.status_text.see(tk.END)
        
        self.update_idletasks()
    
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
    
    def add_status_message(self, message: str, level: str = "INFO"):
        """Add message to status log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.status_text.see(tk.END)
    
    def plot_erosion_3d(self, erosion_rate: np.ndarray):
        """Plot 3D erosion visualization"""
        if self.viz_3d:
            self.viz_3d.plot_erosion_3d(erosion_rate)
    
    def plot_elevation_change_3d(self, elevation_change: np.ndarray):
        """Plot 3D elevation change visualization"""
        if self.viz_3d:
            self.viz_3d.plot_elevation_change_3d(elevation_change)
    
    def cancel_simulation(self):
        """Cancel the simulation"""
        self.is_running = False
        self.add_status_message("Simulation cancelled by user", "WARNING")
        self.cancel_button.config(state=tk.DISABLED, text="Cancelled")
    
    def start_simulation(self):
        """Mark simulation as started"""
        self.is_running = True
        self.cancel_button.config(state=tk.NORMAL, text="Cancel")
        self.status_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.add_status_message("Simulation started", "INFO")
    
    def finish_simulation(self, success: bool = True):
        """Mark simulation as complete"""
        self.is_running = False
        self.cancel_button.config(state=tk.DISABLED)
        status = "SUCCESS" if success else "ERROR"
        self.add_status_message(f"Simulation completed - {status}", status)
        
        if self.on_complete:
            self.on_complete()