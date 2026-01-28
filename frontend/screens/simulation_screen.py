"""
Simulation Screen - Interactive real-time erosion simulation with OpenGL rendering
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
from typing import Optional, Callable, Dict, Any, Union
from datetime import datetime
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


class SimulationScreen(tk.Frame):
    """Interactive simulation screen with real-time visualization"""
    
    def __init__(self, parent, dem: np.ndarray, parameters: Dict[str, Any], on_complete: Optional[Callable] = None, base_map: Optional[np.ndarray] = None):
        super().__init__(parent, bg='#f0f0f0')
        
        self.dem = dem.copy()
        self.current_dem = dem.copy()
        self.parameters = parameters
        self.on_complete = on_complete
        self.base_map = base_map.copy() if base_map is not None else None
        self.dem_opacity = 0.7  # Transparency for DEM overlay
        
        self.is_running = False
        self.is_paused = False
        self.current_step = 0
        self.total_steps = int(parameters.get('num_timesteps', 10))
        self.time_step_days = parameters.get('time_step_days', 1.0)
        
        # Auto-run feature
        self.auto_run_enabled = False
        self.auto_run_iterations = 1
        self.current_iteration = 0
        self.iteration_results = []
        
        # Time series playback
        self.is_playback_mode = False
        self.playback_frame = 0
        self.profile_x = None  # For elevation profile tracking
        self.profile_y = None
        
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
        header_frame = tk.Frame(self, bg='#3498db', height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="REAL-TIME EROSION SIMULATION",
            font=("Arial", 16, "bold"),
            bg='#3498db',
            fg='white'
        )
        title_label.pack(pady=10)
        
        time_label = tk.Label(
            header_frame,
            text=f"Total Duration: {self.total_steps * self.time_step_days:.1f} days",
            font=("Arial", 10),
            bg='#3498db',
            fg='#ecf0f1'
        )
        time_label.pack()
        
        # Main container with two panels
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Visualization
        left_panel = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self._create_visualization_panel(left_panel)
        
        # Right panel - Controls and stats
        right_panel = tk.Frame(main_container, bg='#f0f0f0', width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self._create_control_panel(right_panel)
    
    def _create_visualization_panel(self, parent):
        """Create visualization area with OpenGL rendering"""
        # Use OpenGL visualization widget
        self.visualization_widget = OpenGLVisualizationWidget(parent, self.current_dem)
        self.visualization_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Track rendering updates
        self.last_render_update = 0
        self.render_update_interval = 0.1  # Update every 100ms
    
    def _create_control_panel(self, parent):
        """Create control and statistics panel"""
        # Title
        title_label = tk.Label(
            parent,
            text="SIMULATION CONTROL",
            font=("Arial", 12, "bold"),
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
        
        # Current time display
        self.time_label = tk.Label(
            progress_frame,
            text="Simulated Time: 0 days",
            font=("Arial", 9),
            bg='#f0f0f0'
        )
        self.time_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Speed control
        speed_frame = tk.LabelFrame(
            parent,
            text="Speed Control",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(speed_frame, text="Update Interval (ms):", font=("Arial", 9), bg='#f0f0f0').pack(anchor=tk.W)
        
        self.speed_var = tk.IntVar(value=500)
        speed_scale = tk.Scale(
            speed_frame,
            from_=50,
            to=2000,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            bg='#f0f0f0'
        )
        speed_scale.pack(fill=tk.X)
        
        # Auto-run controls
        autorun_frame = tk.LabelFrame(
            parent,
            text="Auto-Run Feature",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        autorun_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.autorun_var = tk.BooleanVar(value=False)
        autorun_check = tk.Checkbutton(
            autorun_frame,
            text="Loop Simulation After Completion",
            variable=self.autorun_var,
            font=("Arial", 9),
            bg='#f0f0f0',
            command=self._toggle_autorun_options
        )
        autorun_check.pack(anchor=tk.W, pady=(0, 5))
        
        iterations_frame = tk.Frame(autorun_frame, bg='#f0f0f0')
        iterations_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(iterations_frame, text="Iterations:", font=("Arial", 9), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.iterations_var = tk.IntVar(value=1)
        iterations_spin = tk.Spinbox(
            iterations_frame,
            from_=1,
            to=100,
            textvariable=self.iterations_var,
            width=5,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        iterations_spin.pack(side=tk.LEFT, padx=5)
        self.iterations_spin = iterations_spin
        
        self.iteration_label = tk.Label(
            autorun_frame,
            text="Current: 0/0",
            font=("Arial", 9),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.iteration_label.pack(anchor=tk.W)
        
        # Time Series Playback Controls
        timeseries_frame = tk.LabelFrame(
            parent,
            text="Time Series Playback",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        timeseries_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(timeseries_frame, text="Timeline:", font=("Arial", 9), bg='#f0f0f0').pack(anchor=tk.W)
        
        self.timeline_var = tk.IntVar(value=0)
        self.timeline_slider = tk.Scale(
            timeseries_frame,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            variable=self.timeline_var,
            bg='#f0f0f0',
            command=self._on_timeline_changed,
            state=tk.DISABLED
        )
        self.timeline_slider.pack(fill=tk.X, pady=(0, 5))
        
        self.timeline_label = tk.Label(
            timeseries_frame,
            text="Frame: 0/0 | Time: 0.0 days",
            font=("Arial", 8),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.timeline_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Playback buttons
        playback_btn_frame = tk.Frame(timeseries_frame, bg='#f0f0f0')
        playback_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.playback_button = tk.Button(
            playback_btn_frame,
            text="Play Replay",
            font=("Arial", 9),
            bg='#3498db',
            fg='white',
            padx=10,
            pady=4,
            command=self._start_playback,
            state=tk.DISABLED
        )
        self.playback_button.pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            playback_btn_frame,
            text="First Frame",
            font=("Arial", 9),
            bg='#95a5a6',
            fg='white',
            padx=10,
            pady=4,
            command=lambda: self._jump_to_frame(0),
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            playback_btn_frame,
            text="Last Frame",
            font=("Arial", 9),
            bg='#95a5a6',
            fg='white',
            padx=10,
            pady=4,
            command=lambda: self._jump_to_frame(-1),
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        self.profile_var = tk.BooleanVar(value=False)
        profile_check = tk.Checkbutton(
            timeseries_frame,
            text="Show Elevation Profile Over Time",
            variable=self.profile_var,
            font=("Arial", 9),
            bg='#f0f0f0',
            state=tk.DISABLED
        )
        profile_check.pack(anchor=tk.W)
        
        # DEM Opacity Control (if base map is available)
        if self.base_map is not None:
            opacity_frame = tk.LabelFrame(
                parent,
                text="DEM Overlay Opacity",
                font=("Arial", 10, "bold"),
                bg='#f0f0f0',
                fg='#2c3e50',
                padx=10,
                pady=10
            )
            opacity_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(opacity_frame, text="DEM Transparency:", font=("Arial", 9), bg='#f0f0f0').pack(anchor=tk.W)
            
            self.opacity_var = tk.DoubleVar(value=self.dem_opacity)
            opacity_scale = tk.Scale(
                opacity_frame,
                from_=0.0,
                to=1.0,
                orient=tk.HORIZONTAL,
                variable=self.opacity_var,
                bg='#f0f0f0',
                resolution=0.1,
                command=self._update_dem_opacity
            )
            opacity_scale.pack(fill=tk.X)
        
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
            padx=20,
            pady=8,
            command=self.start_simulation
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5))
        
        self.pause_button = tk.Button(
            button_frame,
            text="⏸ Pause",
            font=("Arial", 10, "bold"),
            bg='#f39c12',
            fg='white',
            padx=20,
            pady=8,
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
            padx=20,
            pady=8,
            command=self.reset_simulation
        )
        self.reset_button.pack(fill=tk.X)
        
        # Statistics section
        stats_frame = tk.LabelFrame(
            parent,
            text="Current Statistics",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create scrollable text widget for stats
        stats_scroll = tk.Text(
            stats_frame,
            height=10,
            font=("Courier", 8),
            bg='white',
            fg='#333',
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        stats_scroll.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=stats_scroll.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        stats_scroll.config(yscrollcommand=scrollbar.set)
        
        self.stats_text = stats_scroll
        self._update_stats_display()
        
        # Export button
        export_button = tk.Button(
            parent,
            text="💾 Export Results",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=8,
            command=self.export_simulation
        )
        export_button.pack(fill=tk.X)
    
    def _toggle_autorun_options(self):
        """Enable/disable auto-run options"""
        state = tk.NORMAL if self.autorun_var.get() else tk.DISABLED
        self.iterations_spin.config(state=state)
    
    def _on_timeline_changed(self, value):
        """Handle timeline slider changes during playback"""
        if self.is_playback_mode:
            frame = int(float(value))
            self._display_frame(frame)
    
    def _start_playback(self):
        """Start time series playback"""
        if len(self.elevation_history) < 2:
            messagebox.showwarning("Playback", "No simulation data to replay.")
            return
        
        self.is_playback_mode = True
        self.playback_frame = 0
        self.playback_button.config(state=tk.DISABLED)
        
        # Auto-advance through frames
        self._advance_playback()
    
    def _advance_playback(self):
        """Advance to next frame in playback"""
        if not self.is_playback_mode or self.playback_frame >= len(self.elevation_history) - 1:
            self.is_playback_mode = False
            self.playback_button.config(state=tk.NORMAL)
            return
        
        self.playback_frame += 1
        self._display_frame(self.playback_frame)
        self.after(200, self._advance_playback)  # 200ms per frame
    
    def _display_frame(self, frame_idx):
        """Display a specific frame from history"""
        if frame_idx < 0 or frame_idx >= len(self.elevation_history):
            return
        
        # Update timeline
        self.timeline_var.set(frame_idx)
        self.timeline_label.config(
            text=f"Frame: {frame_idx}/{len(self.elevation_history)-1} | Time: {frame_idx * self.time_step_days:.1f} days"
        )
        
        # Get DEM for this frame
        dem_frame = self.elevation_history[frame_idx]
        
        # Update visualization widget
        if hasattr(self, 'visualization_widget'):
            self.visualization_widget.update_dem(dem_frame)
    
    def _jump_to_frame(self, frame_idx):
        """Jump to specific frame (use -1 for last frame)"""
        if frame_idx == -1:
            frame_idx = len(self.elevation_history) - 1
        self._display_frame(frame_idx)
    
    def _update_dem_opacity(self, value):
        """Update DEM overlay opacity"""
        self.dem_opacity = float(value)
    
    def start_simulation(self):
        """Start the simulation in a background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        
        # Setup auto-run if enabled
        if self.autorun_var.get():
            self.auto_run_enabled = True
            self.auto_run_iterations = self.iterations_var.get()
            self.current_iteration = 1
            self.iteration_results = []
            self._update_iteration_label()
        else:
            self.auto_run_enabled = False
            self.current_iteration = 0
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.DISABLED)
        self.iterations_spin.config(state=tk.DISABLED)
        
        logger.info(f"Starting real-time simulation (iteration {self.current_iteration}/{self.auto_run_iterations if self.auto_run_enabled else 1})")
        
        # Run simulation in background thread
        self.simulation_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def _run_simulation_loop(self):
        """Main simulation loop - runs in background thread"""
        try:
            from backend.services.simulation_engine import SimulationEngine
            
            engine = SimulationEngine()
            
            # Current DEM for this simulation
            current_dem = self.dem.copy()
            
            # Track UI update timing to avoid excessive redraws
            last_ui_update = time.time()
            ui_update_interval = 0.2  # Update UI max every 200ms
            
            for step in range(self.current_step, self.total_steps):
                # Check if paused
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                # Check if cancelled
                if not self.is_running:
                    break
                
                logger.info(f"Simulation step {step + 1}/{self.total_steps}")
                
                # Run single step erosion calculation
                try:
                    # Convert parameters to SimulationParameters object if needed
                    from backend.services.simulation_engine import SimulationParameters
                    if isinstance(self.parameters, dict):
                        params_obj = SimulationParameters(
                            rainfall_erosivity=self.parameters.get('rainfall_erosivity', 300.0),
                            soil_erodibility=self.parameters.get('soil_erodibility', 0.35),
                            cover_factor=self.parameters.get('cover_factor', 0.3),
                            practice_factor=self.parameters.get('practice_factor', 0.5),
                            time_step_days=self.time_step_days,
                            num_timesteps=1,
                            bulk_density=self.parameters.get('bulk_density', 1300.0),
                            area_exponent=self.parameters.get('area_exponent', 0.6),
                            slope_exponent=self.parameters.get('slope_exponent', 1.3),
                            runoff_coefficient=self.parameters.get('runoff_coefficient', 0.5),
                        )
                    else:
                        params_obj = self.parameters
                    
                    # Calculate erosion for this timestep
                    slopes = self._calculate_slopes(current_dem)
                    aspects = self._calculate_aspects(current_dem)
                    flow_accumulation = self._calculate_flow_accumulation(current_dem)
                    
                    transport_capacity = self._calculate_transport_capacity(
                        flow_accumulation, slopes, params_obj
                    )
                    
                    erosion_rate = self._calculate_erosion(
                        transport_capacity, aspects, params_obj
                    )
                    
                    # Update DEM
                    elevation_change = -erosion_rate * self.time_step_days
                    current_dem += elevation_change
                    
                    # Store history
                    self.current_dem = current_dem.copy()
                    self.elevation_history.append(current_dem.copy())
                    self.erosion_history.append(erosion_rate.copy())
                    
                    # Calculate statistics
                    mean_erosion = np.mean(erosion_rate[erosion_rate > 0]) if np.any(erosion_rate > 0) else 0
                    peak_erosion = np.max(erosion_rate)
                    cumulative_loss = np.sum(current_dem - self.dem)
                    
                    self.stats_history['mean_erosion'].append(mean_erosion)
                    self.stats_history['peak_erosion'].append(peak_erosion)
                    self.stats_history['cumulative_loss'].append(cumulative_loss)
                    self.stats_history['timestamp'].append(step * self.time_step_days)
                    
                    # Update UI with throttling to prevent excessive redraws
                    self.current_step = step + 1
                    current_time = time.time()
                    if current_time - last_ui_update >= ui_update_interval:
                        self.after(0, self._update_ui, erosion_rate)
                        last_ui_update = current_time
                    
                    # Sleep based on speed control
                    time.sleep(self.speed_var.get() / 1000.0)
                    
                except Exception as e:
                    logger.error(f"Error in simulation step {step}: {e}")
                    self.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))
                    self.is_running = False
                    break
            
            # Final UI update when complete
            self.after(0, self._update_ui, np.zeros_like(self.dem))
            
            # Simulation complete
            if self.is_running:
                self.is_running = False
                self.after(0, self._on_simulation_complete)
        
        except Exception as e:
            logger.error(f"Fatal simulation error: {e}")
            self.after(0, lambda: messagebox.showerror("Fatal Error", str(e)))
            self.is_running = False
    
    def _update_ui(self, erosion_rate: np.ndarray):
        """Update UI with current state - called from main thread"""
        # Update progress bar
        progress_percent = (self.current_step / self.total_steps) * 100
        self.progress_var.set(self.current_step)
        self.progress_label.config(
            text=f"Step: {self.current_step}/{self.total_steps} ({progress_percent:.1f}%)"
        )
        
        # Update time display
        simulated_time = self.current_step * self.time_step_days
        self.time_label.config(text=f"Simulated Time: {simulated_time:.1f} days")
        
        # Update visualizations
        self._update_visualizations(erosion_rate)
        
        # Update statistics
        self._update_stats_display()
    
    def _update_visualizations(self, erosion_rate: np.ndarray):
        """Update OpenGL visualization"""
        # Update visualization widget with current DEM
        if hasattr(self, 'visualization_widget'):
            self.visualization_widget.update_dem(self.current_dem)
    
    def _update_stats_display(self):
        """Update statistics text display"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        if self.stats_history['timestamp']:
            stats_content = f"""
SIMULATION STATISTICS
{'='*30}

Current Step:    {self.current_step}/{self.total_steps}
Simulated Time:  {self.current_step * self.time_step_days:.1f} days

CURRENT VALUES:
─────────────────────────────
Mean Erosion:    {self.stats_history['mean_erosion'][-1]:.6f} m/yr
Peak Erosion:    {self.stats_history['peak_erosion'][-1]:.6f} m/yr
Elevation Loss:  {abs(self.stats_history['cumulative_loss'][-1]):.6f} m

CUMULATIVE:
─────────────────────────────
Total Vol Loss:  {abs(np.sum(self.stats_history['cumulative_loss'])):.2e} m³
Avg Erosion:     {np.mean(self.stats_history['mean_erosion']):.6f} m/yr
Max Peak:        {np.max(self.stats_history['peak_erosion']):.6f} m/yr
"""
        else:
            stats_content = "Waiting for simulation to start...\n\n(Statistics will appear here)"
        
        self.stats_text.insert(1.0, stats_content)
        self.stats_text.config(state=tk.DISABLED)
    
    def pause_simulation(self):
        """Pause or resume simulation"""
        if self.is_paused:
            self.is_paused = False
            self.pause_button.config(text="⏸ Pause", bg='#f39c12')
        else:
            self.is_paused = True
            self.pause_button.config(text="▶ Resume", bg='#27ae60')
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        if messagebox.askyesno("Reset", "Reset simulation to initial state?"):
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
            self.time_label.config(text="Simulated Time: 0 days")
            
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.reset_button.config(state=tk.NORMAL)
            
            self._update_visualizations(np.zeros_like(self.dem))
            self._update_stats_display()
    
    def _on_simulation_complete(self):
        """Called when simulation finishes"""
        # Store results from this iteration
        iteration_data = {
            'iteration': self.current_iteration,
            'steps': self.current_step,
            'mean_erosion': np.mean(self.stats_history['mean_erosion']) if self.stats_history['mean_erosion'] else 0,
            'peak_erosion': np.max(self.stats_history['peak_erosion']) if self.stats_history['peak_erosion'] else 0,
            'total_volume_loss': abs(np.sum(self.stats_history['cumulative_loss'])) if self.stats_history['cumulative_loss'] else 0
        }
        self.iteration_results.append(iteration_data)
        
        # Check if should auto-run next iteration
        if self.auto_run_enabled and self.current_iteration < self.auto_run_iterations:
            logger.info(f"Auto-running iteration {self.current_iteration + 1}/{self.auto_run_iterations}")
            
            # Prepare for next iteration
            self.current_iteration += 1
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
            
            # Update UI
            self._update_iteration_label()
            self.progress_var.set(0)
            self.progress_label.config(text="Step: 0/0 (0%)")
            self.time_label.config(text="Simulated Time: 0 days")
            self._update_stats_display()
            
            # Restart simulation
            self.is_running = True
            self.is_paused = False
            self.pause_button.config(state=tk.NORMAL)
            self.simulation_thread = threading.Thread(target=self._run_simulation_loop, daemon=True)
            self.simulation_thread.start()
        else:
            # Final completion
            self.start_button.config(state=tk.NORMAL, text="▶ Start")
            self.pause_button.config(state=tk.DISABLED)
            self.reset_button.config(state=tk.NORMAL)
            self.iterations_spin.config(state=tk.NORMAL if self.autorun_var.get() else tk.DISABLED)
            
            # Enable time series playback controls
            self.timeline_slider.config(state=tk.NORMAL, to=len(self.elevation_history)-1)
            self.playback_button.config(state=tk.NORMAL)
            self.profile_var.set(False)
            # Update buttons in playback frame
            for child in self.timeline_slider.master.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(state=tk.NORMAL)
            
            if self.auto_run_enabled:
                # Show summary of all iterations
                summary = f"Auto-run completed!\n\nTotal iterations: {self.current_iteration}\n\n"
                summary += "Iteration Results:\n"
                for result in self.iteration_results:
                    summary += f"\n[{result['iteration']}] Mean erosion: {result['mean_erosion']:.6f} m/yr\n"
                    summary += f"    Peak erosion: {result['peak_erosion']:.6f} m/yr\n"
                    summary += f"    Volume loss: {result['total_volume_loss']:.2e} m³"
                
                messagebox.showinfo("Auto-Run Complete", summary)
                self.auto_run_enabled = False
                self.current_iteration = 0
                self.iteration_results = []
                self._update_iteration_label()
            else:
                messagebox.showinfo(
                    "Simulation Complete",
                    f"Simulation finished after {self.current_step} timesteps\n"
                    f"Total simulated time: {self.current_step * self.time_step_days:.1f} days"
                )
            
            if self.on_complete:
                self.on_complete()
    
    def _update_iteration_label(self):
        """Update iteration counter display"""
        if self.auto_run_enabled and self.auto_run_iterations > 0:
            self.iteration_label.config(
                text=f"Current: {self.current_iteration}/{self.auto_run_iterations}",
                fg='#27ae60' if self.current_iteration > 0 else '#7f8c8d'
            )
        else:
            self.iteration_label.config(text="Current: 0/0", fg='#7f8c8d')
    
    def export_simulation(self):
        """Export simulation results"""
        from tkinter import filedialog
        import json
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            export_data = {
                'parameters': self.parameters,
                'total_steps': self.total_steps,
                'time_step_days': self.time_step_days,
                'statistics': {
                    'mean_erosion': [float(x) for x in self.stats_history['mean_erosion']],
                    'peak_erosion': [float(x) for x in self.stats_history['peak_erosion']],
                    'cumulative_loss': [float(x) for x in self.stats_history['cumulative_loss']],
                    'timestamp': self.stats_history['timestamp']
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Results exported to:\n{file_path}")
    
    # ============= HELPER METHODS - Simulation Calculations =============
    
    @staticmethod
    def _calculate_slopes(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
        """Calculate slope angles using Sobel operator"""
        from scipy.ndimage import convolve
        
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 8.0
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 8.0
        
        gradx = convolve(dem, sobel_x) / cell_size
        grady = convolve(dem, sobel_y) / cell_size
        
        slope_radians = np.arctan(np.sqrt(gradx**2 + grady**2))
        return np.clip(slope_radians, 0, np.pi/2)
    
    @staticmethod
    def _calculate_aspects(dem: np.ndarray) -> np.ndarray:
        """Calculate aspect angles from DEM"""
        from scipy.ndimage import convolve
        
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 8.0
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 8.0
        
        gradx = convolve(dem, sobel_x)
        grady = convolve(dem, sobel_y)
        
        aspect = np.degrees(np.arctan2(gradx, -grady))
        aspect = (aspect + 360) % 360
        
        return aspect
    
    @staticmethod
    def _calculate_flow_accumulation(dem: np.ndarray) -> np.ndarray:
        """Calculate cumulative upslope area using D8 flow"""
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
    
    @staticmethod
    def _calculate_transport_capacity(
        flow: np.ndarray,
        slopes: np.ndarray,
        params: Any
    ) -> np.ndarray:
        """
        Calculate sediment transport capacity using USPED equation.
        
        T = R * K * C * P * (A_norm^m) * (sin β)^n
        
        Units: Result is dimensionless transport capacity factor
        Final erosion rate [m/year] is calculated in _calculate_erosion()
        """
        from backend.services.simulation_engine import SimulationParameters
        
        # Convert to dict if SimulationParameters
        if isinstance(params, SimulationParameters):
            params = params.__dict__
        
        # Normalize contributing area by 1 ha reference (10,000 m²)
        A_ref = 10000.0
        flow_normalized = np.maximum(flow, 1.0) / A_ref
        slope_safe = np.maximum(slopes, 0.001)
        sin_slope = np.sin(slope_safe)
        
        T = (
            params['rainfall_erosivity'] * 
            params['soil_erodibility'] * 
            params['cover_factor'] * 
            params['practice_factor'] *
            (flow_normalized ** params['area_exponent']) *
            (sin_slope ** params['slope_exponent'])
        )
        
        return np.maximum(T, 0)
    
    @staticmethod
    def _calculate_erosion(
        transport_capacity: np.ndarray,
        aspects: np.ndarray,
        params: Any
    ) -> np.ndarray:
        """Calculate erosion rate"""
        from backend.services.simulation_engine import SimulationParameters
        
        # Convert to dict if SimulationParameters
        if isinstance(params, SimulationParameters):
            params = params.__dict__
        
        erosion = transport_capacity * params['runoff_coefficient']
        solar_factor = 0.5 + 0.5 * np.sin(np.radians(aspects))
        erosion *= solar_factor
        
        return np.maximum(erosion, 0)