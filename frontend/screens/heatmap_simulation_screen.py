"""
Heatmap Simulation Screen - Focused erosion visualization with OpenGL rendering
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
from typing import Optional, Callable, Dict, Any
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from backend.services.opengl_tkinter import OpenGLVisualizationWidget, AnimatedOpenGLCanvas  # type: ignore
except (ImportError, ModuleNotFoundError):
    from services.opengl_tkinter import OpenGLVisualizationWidget, AnimatedOpenGLCanvas  # type: ignore

logger = logging.getLogger(__name__)


class HeatmapSimulationScreen(tk.Frame):
    """Simplified simulation screen with heatmap-only visualization"""
    
    def __init__(self, parent, dem: np.ndarray, parameters: Dict[str, Any], on_complete: Optional[Callable] = None):
        super().__init__(parent, bg='#f0f0f0')
        
        self.dem = dem.copy()
        self.current_dem = dem.copy()
        self.parameters = parameters
        self.on_complete = on_complete
        
        self.is_running = False
        self.is_paused = False
        self.current_step = 0
        self.total_steps = int(parameters.get('num_timesteps', 10))
        self.time_step_days = parameters.get('time_step_days', 1.0)
        
        # Data tracking
        self.elevation_history = [dem.copy()]
        self.erosion_history = []
        self.stats_history = {
            'mean_erosion': [],
            'peak_erosion': [],
            'cumulative_loss': [],
            'timestamp': []
        }
        
        self.simulation_thread = None
        self.start_time = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header_frame = tk.Frame(self, bg='#3498db', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="LAND EROSION HEATMAP SIMULATION",
            font=("Arial", 14, "bold"),
            bg='#3498db',
            fg='white'
        )
        title_label.pack(pady=10)
        
        # Main container
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Visualizations
        left_panel = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self._create_heatmap_panel(left_panel)
        
        # Right panel - Controls
        right_panel = tk.Frame(main_container, bg='#f0f0f0', width=280)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self._create_control_panel(right_panel)
    
    def _create_heatmap_panel(self, parent):
        """Create heatmap visualization using OpenGL"""
        # Use animated canvas for time series
        self.visualization_widget = AnimatedOpenGLCanvas(parent, self.dem)
        self.visualization_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Data tracking
        self.heatmap_data = {
            'mean_erosion': [],
            'peak_erosion': [],
            'volume_loss': [],
            'timestamps': []
        }
    
    def _create_control_panel(self, parent):
        """Create control panel"""
        # Title
        title_label = tk.Label(
            parent,
            text="SIMULATION CONTROL",
            font=("Arial", 11, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress section
        progress_frame = tk.LabelFrame(
            parent,
            text="Progress",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=self.total_steps,
            length=250,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Step: 0/0 (0%)",
            font=("Arial", 9),
            bg='#f0f0f0'
        )
        self.progress_label.pack(anchor=tk.W)
        
        self.time_label = tk.Label(
            progress_frame,
            text="Time: 0.0 days",
            font=("Arial", 9),
            bg='#f0f0f0'
        )
        self.time_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Speed control
        speed_frame = tk.LabelFrame(
            parent,
            text="Speed",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(speed_frame, text="Update (ms):", font=("Arial", 9), bg='#f0f0f0').pack(anchor=tk.W)
        
        self.speed_var = tk.IntVar(value=300)
        speed_scale = tk.Scale(
            speed_frame,
            from_=50,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            bg='#f0f0f0'
        )
        speed_scale.pack(fill=tk.X)
        
        # Control buttons
        button_frame = tk.LabelFrame(
            parent,
            text="Controls",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start",
            font=("Arial", 10, "bold"),
            bg='#27ae60',
            fg='white',
            command=self.start_simulation
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5))
        
        self.pause_button = tk.Button(
            button_frame,
            text="⏸ Pause",
            font=("Arial", 10, "bold"),
            bg='#f39c12',
            fg='white',
            command=self.pause_simulation,
            state=tk.DISABLED
        )
        self.pause_button.pack(fill=tk.X, pady=(0, 5))
        
        self.reset_button = tk.Button(
            button_frame,
            text="↻ Reset",
            font=("Arial", 10, "bold"),
            bg='#95a5a6',
            fg='white',
            command=self.reset_simulation
        )
        self.reset_button.pack(fill=tk.X)
        
        # Statistics
        stats_frame = tk.LabelFrame(
            parent,
            text="Statistics",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.stats_text = tk.Text(
            stats_frame,
            height=12,
            font=("Courier", 8),
            bg='white',
            fg='#333',
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.config(yscrollcommand=scrollbar.set)
        
        self._update_stats_display()
        
        # Export button
        export_button = tk.Button(
            parent,
            text="💾 Export",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            command=self.export_simulation
        )
        export_button.pack(fill=tk.X)
    
    def start_simulation(self):
        """Start simulation"""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.DISABLED)
        
        logger.info("Starting heatmap simulation")
        
        self.simulation_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def _run_simulation_loop(self):
        """Main simulation loop"""
        try:
            current_dem = self.dem.copy()
            cumulative_erosion = np.zeros_like(current_dem)
            
            for step in range(self.current_step, self.total_steps):
                # Check pause/cancel
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                if not self.is_running:
                    break
                
                try:
                    # Calculate terrain parameters
                    slopes = self._calculate_slopes(current_dem)
                    flow_acc = self._calculate_flow_accumulation(current_dem)
                    
                    # Calculate erosion
                    rainfall = self.parameters.get('rainfall_erosivity', 300.0)
                    soil_k = self.parameters.get('soil_erodibility', 0.35)
                    c_factor = self.parameters.get('cover_factor', 0.3)
                    p_factor = self.parameters.get('practice_factor', 0.5)
                    
                    erosion_rate = (
                        rainfall * soil_k * c_factor * p_factor *
                        (flow_acc ** 0.6) * (np.sin(slopes) ** 1.3)
                    )
                    erosion_rate = np.maximum(erosion_rate, 0)
                    
                    # Update DEM
                    elevation_change = -erosion_rate * self.time_step_days
                    current_dem += elevation_change
                    cumulative_erosion += erosion_rate * self.time_step_days
                    
                    # Store history
                    self.current_dem = current_dem.copy()
                    self.elevation_history.append(current_dem.copy())
                    self.erosion_history.append(erosion_rate.copy())
                    
                    # Calculate statistics
                    mean_erosion = np.mean(erosion_rate[erosion_rate > 0]) if np.any(erosion_rate > 0) else 0
                    peak_erosion = np.max(erosion_rate)
                    total_loss = np.sum(cumulative_erosion)
                    
                    self.stats_history['mean_erosion'].append(mean_erosion)
                    self.stats_history['peak_erosion'].append(peak_erosion)
                    self.stats_history['cumulative_loss'].append(total_loss)
                    self.stats_history['timestamp'].append(step * self.time_step_days)
                    
                    # Update UI
                    self.current_step = step + 1
                    self.after(0, self._update_ui, erosion_rate, cumulative_erosion)
                    
                    # Speed control
                    time.sleep(self.speed_var.get() / 1000.0)
                    
                except Exception as e:
                    logger.error(f"Step error: {e}")
                    self.after(0, lambda error=str(e): messagebox.showerror("Error", error))
                    self.is_running = False
                    break
            
            if self.is_running:
                self.is_running = False
                self.after(0, self._on_complete)
        
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.after(0, lambda error=str(e): messagebox.showerror("Fatal Error", error))
            self.is_running = False
    
    def _update_ui(self, erosion_rate: np.ndarray, cumulative_erosion: np.ndarray):
        """Update visualization"""
        progress_percent = (self.current_step / self.total_steps) * 100
        self.progress_var.set(self.current_step)
        self.progress_label.config(
            text=f"Step: {self.current_step}/{self.total_steps} ({progress_percent:.1f}%)"
        )
        
        simulated_time = self.current_step * self.time_step_days
        self.time_label.config(text=f"Time: {simulated_time:.1f} days")
        
        # Update OpenGL visualization
        if hasattr(self, 'visualization_widget'):
            self.visualization_widget.add_frame(self.current_dem)
        
        self._update_stats_display()
    
    def _update_stats_display(self):
        """Update statistics panel"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        if self.stats_history['timestamp']:
            content = f"""
EROSION SIMULATION STATS
{'='*30}

Current Step: {self.current_step}/{self.total_steps}
Time: {self.current_step * self.time_step_days:.1f} days

CURRENT VALUES:
{'-'*30}
Mean Erosion: {self.stats_history['mean_erosion'][-1]:.6f} m/yr
Peak Erosion: {self.stats_history['peak_erosion'][-1]:.6f} m/yr

CUMULATIVE:
{'-'*30}
Total Loss: {abs(self.stats_history['cumulative_loss'][-1]):.3e} m
Avg Rate: {np.mean(self.stats_history['mean_erosion']):.6f} m/yr
Max Peak: {np.max(self.stats_history['peak_erosion']):.6f} m/yr
"""
        else:
            content = "Waiting for simulation...\n\n(Statistics appear here)"
        
        self.stats_text.insert(1.0, content)
        self.stats_text.config(state=tk.DISABLED)
    
    def pause_simulation(self):
        """Pause/resume"""
        if self.is_paused:
            self.is_paused = False
            self.pause_button.config(text="⏸ Pause")
        else:
            self.is_paused = True
            self.pause_button.config(text="▶ Resume")
    
    def reset_simulation(self):
        """Reset"""
        if messagebox.askyesno("Reset", "Reset simulation?"):
            self.is_running = False
            self.is_paused = False
            self.current_step = 0
            self.current_dem = self.dem.copy()
            self.elevation_history = [self.dem.copy()]
            self.erosion_history = []
            self.stats_history = {
                'mean_erosion': [],
                'peak_erosion': [],
                'cumulative_loss': [],
                'timestamp': []
            }
            
            self.progress_var.set(0)
            self.progress_label.config(text="Step: 0/0 (0%)")
            self.time_label.config(text="Time: 0.0 days")
            
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.reset_button.config(state=tk.NORMAL)
            
            self._update_ui(np.zeros_like(self.dem), np.zeros_like(self.dem))
            self._update_stats_display()
    
    def _on_complete(self):
        """Simulation complete"""
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Complete",
            f"Simulation finished after {self.current_step} steps\n"
            f"Duration: {self.current_step * self.time_step_days:.1f} days"
        )
        
        if self.on_complete:
            self.on_complete()
    
    def export_simulation(self):
        """Export results"""
        from tkinter import filedialog
        import json
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        
        if file_path:
            export_data = {
                'parameters': self.parameters,
                'total_steps': self.total_steps,
                'statistics': {
                    'mean_erosion': [float(x) for x in self.stats_history['mean_erosion']],
                    'peak_erosion': [float(x) for x in self.stats_history['peak_erosion']],
                    'cumulative_loss': [float(x) for x in self.stats_history['cumulative_loss']],
                    'timestamp': self.stats_history['timestamp']
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Exported to:\n{file_path}")
    
    # ===== Helper Methods =====
    
    @staticmethod
    def _calculate_slopes(dem: np.ndarray) -> np.ndarray:
        """Calculate slopes"""
        from scipy.ndimage import convolve
        
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 8.0
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 8.0
        
        gradx = convolve(dem, sobel_x)
        grady = convolve(dem, sobel_y)
        
        slopes = np.arctan(np.sqrt(gradx**2 + grady**2))
        return np.clip(slopes, 0, np.pi/2)
    
    @staticmethod
    def _calculate_flow_accumulation(dem: np.ndarray) -> np.ndarray:
        """Calculate flow accumulation (D8)"""
        rows, cols = dem.shape
        flow = np.ones_like(dem, dtype=float)
        
        indices = np.argsort(-dem.ravel())
        
        for idx in indices:
            row, col = np.unravel_index(idx, dem.shape)
            if row == 0 or row == rows-1 or col == 0 or col == cols-1:
                continue
            
            neighbors = dem[row-1:row+2, col-1:col+2]
            center = dem[row, col]
            
            if np.all(neighbors >= center):
                continue
            
            steepest_idx = np.argmin(neighbors)
            neighbor_row = row - 1 + steepest_idx // 3
            neighbor_col = col - 1 + steepest_idx % 3
            
            if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
                flow[neighbor_row, neighbor_col] += flow[row, col]
        
        return flow
