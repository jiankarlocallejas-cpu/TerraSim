"""
Workflow Screen - Step-by-step USPED process visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from typing import Optional, Callable, Dict, Any
import logging
import threading

logger = logging.getLogger(__name__)


class WorkflowScreen(tk.Frame):
    """
    Interactive workflow screen showing USPED process steps
    
    Steps:
    1. Load Data
    2. Compute Slope
    3. Compute Aspect
    4. Compute Flow Accumulation
    5. Compute LST (Topographic Factor)
    6. Compute Sediment Flow
    7. Compute Flow Components
    8. Compute Derivatives
    9. Compute Erosion/Deposition
    10. Classify Results
    """
    
    WORKFLOW_STEPS = [
        ("Load Data", "Load and validate input elevation data"),
        ("Compute Slope", "Calculate slope gradient from DEM"),
        ("Compute Aspect", "Calculate aspect (flow direction)"),
        ("Flow Accumulation", "Compute upslope contributing area"),
        ("LST Factor", "Compute topographic sediment transport capacity"),
        ("Sediment Flow", "Calculate sediment transport using R*K*C*LST"),
        ("Flow Components", "Decompose sediment flow to X and Y components"),
        ("Derivatives", "Compute partial derivatives of flow field"),
        ("Erosion/Deposition", "Calculate net erosion and deposition"),
        ("Classification", "Classify results into erosion/deposition zones"),
    ]
    
    def __init__(self, parent, dem: np.ndarray, parameters: Dict[str, Any], 
                 on_complete: Optional[Callable] = None):
        super().__init__(parent, bg='#f0f0f0')
        
        self.dem = dem.copy()
        self.parameters = parameters
        self.on_complete = on_complete
        
        self.current_step_idx = 0
        self.workflow_results = {}
        self.is_running = False
        self.workflow = None  # Will be initialized when needed
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header_frame = tk.Frame(self, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="USPED Workflow - Soil Erosion & Deposition Modeling",
            font=("Arial", 16, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Steps
        left_panel = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), width=250)
        left_panel.pack_propagate(False)
        
        self._create_steps_panel(left_panel)
        
        # Right panel - Content
        right_panel = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self._create_content_panel(right_panel)
    
    def _create_steps_panel(self, parent):
        """Create steps sidebar"""
        title = tk.Label(
            parent,
            text="WORKFLOW STEPS",
            font=("Arial", 11, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # Scrollable frame for steps
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create step buttons
        self.step_buttons = []
        for i, (step_name, step_desc) in enumerate(self.WORKFLOW_STEPS):
            btn_frame = tk.Frame(scrollable_frame, bg='white')
            btn_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Step number and name
            step_text = f"{i+1}. {step_name}"
            btn = tk.Button(
                btn_frame,
                text=step_text,
                font=("Arial", 9),
                bg='#ecf0f1',
                fg='#2c3e50',
                anchor=tk.W,
                justify=tk.LEFT,
                padx=10,
                pady=8,
                command=lambda idx=i: self.goto_step(idx)
            )
            btn.pack(fill=tk.X)
            
            # Description
            desc_label = tk.Label(
                btn_frame,
                text=step_desc,
                font=("Arial", 8),
                bg='white',
                fg='#7f8c8d',
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=200
            )
            desc_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
            
            self.step_buttons.append(btn)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_step_display()
    
    def _create_content_panel(self, parent):
        """Create main content panel"""
        # Step title and description
        self.title_label = tk.Label(
            parent,
            text="",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        self.title_label.pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        self.desc_label = tk.Label(
            parent,
            text="",
            font=("Arial", 10),
            bg='white',
            fg='#7f8c8d',
            justify=tk.LEFT,
            wraplength=500
        )
        self.desc_label.pack(anchor=tk.W, padx=20, pady=(0, 20))
        
        # Results frame
        self.results_frame = tk.Frame(parent, bg='#ecf0f1', relief=tk.SUNKEN, bd=1)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.results_text = tk.Text(
            self.results_frame,
            font=("Courier", 9),
            bg='#ecf0f1',
            fg='#2c3e50',
            height=15,
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(
            parent,
            variable=self.progress_var,
            maximum=len(self.WORKFLOW_STEPS),
            length=300,
            mode='determinate'
        )
        progress_bar.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Button frame
        button_frame = tk.Frame(parent, bg='white')
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.prev_button = tk.Button(
            button_frame,
            text="◀ Previous",
            font=("Arial", 10),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=8,
            command=self.previous_step,
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.run_button = tk.Button(
            button_frame,
            text="▶ Run Step",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_current_step
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(
            button_frame,
            text="Next ▶",
            font=("Arial", 10),
            bg='#27ae60',
            fg='white',
            padx=15,
            pady=8,
            command=self.next_step,
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.run_all_button = tk.Button(
            button_frame,
            text="▶▶ Run All",
            font=("Arial", 10, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=15,
            pady=8,
            command=self.run_all_steps
        )
        self.run_all_button.pack(side=tk.LEFT, padx=5)
        
        self.update_content_display()
    
    def goto_step(self, step_idx: int):
        """Go to specific step"""
        if 0 <= step_idx < len(self.WORKFLOW_STEPS):
            self.current_step_idx = step_idx
            self.update_step_display()
            self.update_content_display()
    
    def next_step(self):
        """Move to next step"""
        if self.current_step_idx < len(self.WORKFLOW_STEPS) - 1:
            self.current_step_idx += 1
            self.update_step_display()
            self.update_content_display()
    
    def previous_step(self):
        """Move to previous step"""
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self.update_step_display()
            self.update_content_display()
    
    def update_step_display(self):
        """Update step button highlighting"""
        for i, btn in enumerate(self.step_buttons):
            if i == self.current_step_idx:
                btn.config(bg='#3498db', fg='white', relief=tk.SUNKEN)
            else:
                btn.config(bg='#ecf0f1', fg='#2c3e50', relief=tk.RAISED)
        
        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_step_idx > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_step_idx < len(self.WORKFLOW_STEPS) - 1 else tk.DISABLED)
        
        # Update progress
        self.progress_var.set(self.current_step_idx + 1)
    
    def update_content_display(self):
        """Update content display for current step"""
        step_name, step_desc = self.WORKFLOW_STEPS[self.current_step_idx]
        
        self.title_label.config(text=f"Step {self.current_step_idx + 1}: {step_name}")
        self.desc_label.config(text=step_desc)
        
        # Show results if available
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        step_key = f"step_{self.current_step_idx + 1}"
        if step_key in self.workflow_results:
            results = self.workflow_results[step_key]
            display_text = self._format_results(results)
            self.results_text.insert(1.0, display_text)
        else:
            self.results_text.insert(1.0, "Not executed yet. Click 'Run Step' to execute this step.")
        
        self.results_text.config(state=tk.DISABLED)
    
    def run_current_step(self):
        """Run current workflow step"""
        if self.is_running:
            messagebox.showwarning("Warning", "Step already running")
            return
        
        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        
        def run_step():
            try:
                from backend.services.usped_workflow import USPEDWorkflow
                
                # Initialize workflow if not done
                if self.workflow is None:
                    self.workflow = USPEDWorkflow(self.dem)
                    self.workflow.set_parameters(
                        rainfall_factor=self.parameters.get('rainfall_erosivity', 270.0),
                        soil_kfac=None,
                        cover_cfac=None,
                        m_exponent=self.parameters.get('area_exponent', 1.0),
                        n_exponent=self.parameters.get('slope_exponent', 1.3)
                    )
                
                # Run appropriate step
                step_methods = [
                    self.workflow.step_1_load_data,
                    self.workflow.step_2_compute_slope,
                    self.workflow.step_3_compute_aspect,
                    self.workflow.step_4_compute_flow_accumulation,
                    self.workflow.step_5_compute_lst,
                    self.workflow.step_6_compute_sedflow,
                    self.workflow.step_7_compute_flow_components,
                    self.workflow.step_8_compute_derivatives,
                    self.workflow.step_9_compute_erosion_deposition,
                    self.workflow.step_10_classify_results,
                ]
                
                result = step_methods[self.current_step_idx]()
                step_key = f"step_{self.current_step_idx + 1}"
                self.workflow_results[step_key] = result
                
                self.after(0, self._on_step_complete)
                
            except Exception as e:
                logger.error(f"Step error: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Step failed:\n{str(e)}"))
            finally:
                self.is_running = False
                self.after(0, lambda: self.run_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_step, daemon=True)
        thread.start()
    
    def run_all_steps(self):
        """Run all workflow steps"""
        if self.is_running:
            messagebox.showwarning("Warning", "Workflow already running")
            return
        
        self.is_running = True
        self.run_all_button.config(state=tk.DISABLED)
        
        def run_workflow():
            try:
                from backend.services.usped_workflow import USPEDWorkflow
                
                workflow = USPEDWorkflow(self.dem)
                workflow.set_parameters(
                    rainfall_factor=self.parameters.get('rainfall_erosivity', 270.0),
                    soil_kfac=None,
                    cover_cfac=None,
                    m_exponent=self.parameters.get('area_exponent', 1.0),
                    n_exponent=self.parameters.get('slope_exponent', 1.3)
                )
                
                results = workflow.run_complete_workflow()
                self.workflow_results = results
                
                self.after(0, lambda: [
                    self.update_step_display(),
                    self.update_content_display(),
                    messagebox.showinfo("Success", "USPED workflow completed successfully!")
                ])
                
            except Exception as e:
                logger.error(f"Workflow error: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Workflow failed:\n{str(e)}"))
            finally:
                self.is_running = False
                self.after(0, lambda: self.run_all_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()
    
    def _on_step_complete(self):
        """Called when step completes"""
        self.update_content_display()
        messagebox.showinfo("Success", f"Step {self.current_step_idx + 1} completed successfully!")
    
    @staticmethod
    def _format_results(results: Dict[str, Any]) -> str:
        """Format results for display"""
        lines = []
        for key, value in results.items():
            if isinstance(value, (list, tuple)):
                lines.append(f"{key}: {value}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    if isinstance(v, float):
                        lines.append(f"  {k}: {v:.6e}")
                    else:
                        lines.append(f"  {k}: {v}")
            elif isinstance(value, float):
                lines.append(f"{key}: {value:.6e}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
