"""
Result Screen - Display and export simulation results with OpenGL visualization
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from typing import Optional, Dict, Any
import json
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.opengl_tkinter import OpenGLVisualizationWidget


class ResultScreen(tk.Frame):
    """Screen displaying simulation results"""
    
    def __init__(self, parent, result_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent, bg='#f0f0f0')
        self.result_data = result_data or {}
        self.current_view = "summary"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components"""
        # Header
        header_frame = tk.Frame(self, bg='#27ae60', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="SIMULATION RESULTS",
            font=("Arial", 18, "bold"),
            bg='#27ae60',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content with tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary Tab
        summary_tab = tk.Frame(notebook, bg='#f0f0f0')
        notebook.add(summary_tab, text='Summary')
        self._create_summary_tab(summary_tab)
        
        # Statistics Tab
        stats_tab = tk.Frame(notebook, bg='#f0f0f0')
        notebook.add(stats_tab, text='Statistics')
        self._create_stats_tab(stats_tab)
        
        # Visualization Tab
        viz_tab = tk.Frame(notebook, bg='#f0f0f0')
        notebook.add(viz_tab, text='Visualization')
        self._create_viz_tab(viz_tab)
        
        # Parameters Tab
        params_tab = tk.Frame(notebook, bg='#f0f0f0')
        notebook.add(params_tab, text='Parameters')
        self._create_params_tab(params_tab)
        
        # Button frame
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        export_button = tk.Button(
            button_frame,
            text="Export Results",
            font=("Arial", 11),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=8,
            command=self.export_results
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        save_button = tk.Button(
            button_frame,
            text="Save Report",
            font=("Arial", 11),
            bg='#9b59b6',
            fg='white',
            padx=20,
            pady=8,
            command=self.save_report
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        close_button = tk.Button(
            button_frame,
            text="Close",
            font=("Arial", 11),
            bg='#95a5a6',
            fg='white',
            padx=20,
            pady=8,
            command=self.master.quit
        )
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def _create_summary_tab(self, parent):
        """Create summary tab content"""
        content_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            content_frame,
            text="Simulation Summary",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        # Summary data
        summary_text = tk.Text(
            content_frame,
            height=15,
            font=("Courier", 10),
            bg='white',
            fg='#333',
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        summary_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Populate summary
        summary_content = f"""
SIMULATION RESULTS SUMMARY
{'='*60}

Mode:                    {self.result_data.get('mode', 'N/A')}
Timestamp:               {self.result_data.get('timestamp', 'N/A')}
Computation Time:        {self.result_data.get('computation_time', 0):.2f}s

{'='*60}
KEY METRICS
{'='*60}

Mean Erosion Rate:       {self.result_data.get('mean_erosion', 0):.6f} m/year
Peak Erosion Rate:       {self.result_data.get('peak_erosion', 0):.6f} m/year
Total Volume Loss:       {self.result_data.get('total_volume_loss', 0):.2e} m³

{'='*60}
UNCERTAINTY METRICS (if applicable)
{'='*60}

Uncertainty Range:       {self.result_data.get('uncertainty_range', ('N/A', 'N/A'))}
95% Confidence Int.:     {self.result_data.get('confidence_interval_95', ('N/A', 'N/A'))}
"""
        summary_text.insert(1.0, summary_content)
        summary_text.config(state=tk.DISABLED)
    
    def _create_stats_tab(self, parent):
        """Create statistics tab content"""
        content_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create treeview for statistics
        tree = ttk.Treeview(
            content_frame,
            columns=('Value', 'Unit'),
            height=15,
            show='tree headings'
        )
        
        tree.column('#0', width=250, anchor=tk.W)
        tree.column('Value', width=150, anchor=tk.CENTER)
        tree.column('Unit', width=100, anchor=tk.W)
        
        tree.heading('#0', text='Parameter')
        tree.heading('Value', text='Value')
        tree.heading('Unit', text='Unit')
        
        # Sample data
        stats_data = [
            ('Erosion Statistics', '', ''),
            ('  Mean Erosion', f"{self.result_data.get('mean_erosion', 0):.6f}", 'm/year'),
            ('  Peak Erosion', f"{self.result_data.get('peak_erosion', 0):.6f}", 'm/year'),
            ('  Volume Loss', f"{self.result_data.get('total_volume_loss', 0):.2e}", 'm³'),
            ('', '', ''),
            ('Performance Metrics', '', ''),
            ('  Computation Time', f"{self.result_data.get('computation_time', 0):.2f}", 's'),
        ]
        
        for item in stats_data:
            tree.insert('', tk.END, values=item)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_viz_tab(self, parent):
        """Create visualization tab"""
        # Create placeholder for matplotlib figure
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle('Erosion Analysis Results', fontsize=14, fontweight='bold')
        
        # Placeholder plots
        for ax in axes.flat:
            ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.grid(True, alpha=0.3)
        
        axes[0, 0].set_title('Erosion Rate Distribution')
        axes[0, 1].set_title('Risk Classification')
        axes[1, 0].set_title('Temporal Evolution')
        axes[1, 1].set_title('Statistical Summary')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_params_tab(self, parent):
        """Create parameters display tab"""
        content_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Parameters treeview
        tree = ttk.Treeview(
            content_frame,
            columns=('Value',),
            height=12,
            show='tree headings'
        )
        
        tree.column('#0', width=250, anchor=tk.W)
        tree.column('Value', width=150, anchor=tk.CENTER)
        
        tree.heading('#0', text='Parameter Name')
        tree.heading('Value', text='Value')
        
        params = self.result_data.get('parameters', {})
        
        # Convert params to dict if it's an object with to_dict method
        if hasattr(params, 'to_dict'):
            params = params.to_dict()
        elif hasattr(params, '__dict__'):
            params = params.__dict__
        elif not isinstance(params, dict):
            params = {}
        
        for key, value in params.items():
            tree.insert('', tk.END, text=key, values=(f"{value}",))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def export_results(self):
        """Export results as JSON"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.result_data, f, indent=2, default=str)
            messagebox.showinfo("Success", f"Results exported to:\n{file_path}")
    
    def save_report(self):
        """Save comprehensive report as PDF/TXT"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write("="*70 + "\n")
                f.write("TERRASM SIMULATION REPORT\n")
                f.write("="*70 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("SUMMARY\n")
                f.write("-"*70 + "\n")
                f.write(f"Mode: {self.result_data.get('mode', 'N/A')}\n")
                f.write(f"Computation Time: {self.result_data.get('computation_time', 0):.2f}s\n\n")
                
                f.write("RESULTS\n")
                f.write("-"*70 + "\n")
                f.write(f"Mean Erosion: {self.result_data.get('mean_erosion', 0):.6f} m/year\n")
                f.write(f"Peak Erosion: {self.result_data.get('peak_erosion', 0):.6f} m/year\n")
                f.write(f"Volume Loss: {self.result_data.get('total_volume_loss', 0):.2e} m³\n\n")
                
                f.write("PARAMETERS\n")
                f.write("-"*70 + "\n")
                for key, value in self.result_data.get('parameters', {}).items():
                    f.write(f"{key}: {value}\n")
            
            messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
    
    def set_result_data(self, data: Dict[str, Any]):
        """Update result data and refresh display"""
        self.result_data = data
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh all displays with new data"""
        self.update_idletasks()