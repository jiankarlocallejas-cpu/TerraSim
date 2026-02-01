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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from backend.services.visualization import GPURenderEngine as OpenGLVisualizationWidget


class ResultScreen(tk.Frame):
    """Screen displaying simulation results with QGIS-like interface"""
    
    def __init__(self, parent, result_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent, bg='#1e1e2e')
        self.result_data = result_data or {}
        self.current_view = "summary"
        
        # Color scheme matching main window
        self.primary_color = '#1e1e2e'
        self.secondary_color = '#2d2d44'
        self.accent_color = '#00d4ff'
        self.text_color = '#ffffff'
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create UI components with QGIS-like styling"""
        # Header with dark theme
        header_frame = tk.Frame(self, bg=self.secondary_color, height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📊 SIMULATION RESULTS",
            font=("Arial", 16, "bold"),
            bg=self.secondary_color,
            fg=self.accent_color
        )
        title_label.pack(pady=15)
        
        # Ribbon toolbar with analysis options
        ribbon_frame = tk.Frame(self, bg=self.secondary_color, height=70)
        ribbon_frame.pack(fill=tk.X, padx=0, pady=0)
        ribbon_frame.pack_propagate(False)
        
        # Add ribbon groups
        self._create_result_ribbon(ribbon_frame)
        
        # Main content with tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.primary_color)
        style.configure('TNotebook.Tab', font=("Arial", 9, "bold"), padding=[20, 10])
        
        # Summary Tab
        summary_tab = tk.Frame(notebook, bg='white')
        notebook.add(summary_tab, text='📋 Summary')
        self._create_summary_tab(summary_tab)
        
        # Statistics Tab
        stats_tab = tk.Frame(notebook, bg='white')
        notebook.add(stats_tab, text='📊 Statistics')
        self._create_stats_tab(stats_tab)
        
        # Visualization Tab
        viz_tab = tk.Frame(notebook, bg='white')
        notebook.add(viz_tab, text='📈 Visualization')
        self._create_viz_tab(viz_tab)
        
        # Parameters Tab
        params_tab = tk.Frame(notebook, bg='white')
        notebook.add(params_tab, text='⚙️  Parameters')
        self._create_params_tab(params_tab)
        
        # Export Tab
        export_tab = tk.Frame(notebook, bg='white')
        notebook.add(export_tab, text='💾 Export')
        self._create_export_tab(export_tab)
        
        # Button frame
        button_frame = tk.Frame(self, bg=self.primary_color)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        export_button = tk.Button(
            button_frame,
            text="💾 Export Results",
            font=("Arial", 10, "bold"),
            bg=self.accent_color,
            fg=self.primary_color,
            padx=20,
            pady=8,
            relief=tk.FLAT,
            command=self.export_results
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        save_button = tk.Button(
            button_frame,
            text="📄 Save Report",
            font=("Arial", 10, "bold"),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            command=self.save_report
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        close_button = tk.Button(
            button_frame,
            text="❌ Close",
            font=("Arial", 10, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            command=self.master.quit
        )
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        status_frame = tk.Frame(self, bg=self.secondary_color, height=25)
        status_frame.pack(fill=tk.X, padx=0, pady=0, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready | Results loaded",
            font=("Arial", 8),
            bg=self.secondary_color,
            fg=self.text_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _create_result_ribbon(self, parent):
        """Create ribbon toolbar for result actions"""
        ribbon_groups_frame = tk.Frame(parent, bg=self.secondary_color)
        ribbon_groups_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Analysis group
        self._create_ribbon_group(ribbon_groups_frame, "ANALYSIS", [
            ("📊 Summary", self._show_summary, 8),
            ("📈 Charts", self._show_charts, 8),
            ("🔍 Details", self._show_details, 8),
        ])
        
        # Tools group
        self._create_ribbon_group(ribbon_groups_frame, "TOOLS", [
            ("🔄 Refresh", self._refresh_stats, 8),
            ("⚡ Export", self.export_results, 8),
            ("📄 Report", self.save_report, 8),
        ])
        
        # Visualization group
        self._create_ribbon_group(ribbon_groups_frame, "DISPLAY", [
            ("🎨 Style", self._style_visualization, 8),
            ("🔍 Zoom", self._zoom_to_fit, 8),
            ("🌍 Globe", self._globe_view, 8),
        ])
    
    def _create_ribbon_group(self, parent, group_name, buttons):
        """Create a ribbon group with buttons"""
        group_frame = tk.LabelFrame(
            parent,
            text=group_name,
            font=("Arial", 7, "bold"),
            bg=self.secondary_color,
            fg=self.accent_color,
            padx=6,
            pady=4,
            relief=tk.FLAT
        )
        group_frame.pack(side=tk.LEFT, padx=2, fill=tk.BOTH)
        
        for label, command, fontsize in buttons:
            btn = tk.Button(
                group_frame,
                text=label,
                font=("Arial", fontsize),
                bg='#3d3d5c',
                fg=self.text_color,
                relief=tk.FLAT,
                padx=8,
                pady=6,
                command=command,
                wraplength=50
            )
            btn.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.accent_color, fg=self.primary_color))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#3d3d5c', fg=self.text_color))
    
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
        """Create statistics tab content with erosion metrics"""
        content_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create treeview for statistics
        tree = ttk.Treeview(
            content_frame,
            columns=('Value', 'Unit'),
            height=20,
            show='tree headings'
        )
        
        tree.column('#0', width=250, anchor=tk.W)
        tree.column('Value', width=150, anchor=tk.CENTER)
        tree.column('Unit', width=100, anchor=tk.W)
        
        tree.heading('#0', text='Parameter')
        tree.heading('Value', text='Value')
        tree.heading('Unit', text='Unit')
        
        # Get calculated erosion statistics
        erosion_stats = self._calculate_erosion_statistics()
        
        # Add erosion statistics to tree
        tree.insert('', tk.END, text='Erosion Statistics', values=('', ''))
        for stat in erosion_stats:
            tree.insert('', tk.END, text=f"  {stat[0]}", values=(stat[1], stat[2]))
        
        # Add performance metrics
        tree.insert('', tk.END, text='', values=('', ''))
        tree.insert('', tk.END, text='Performance Metrics', values=('', ''))
        tree.insert('', tk.END, text='  Computation Time', values=(f"{self.result_data.get('computation_time', 0):.2f}", 's'))
        
        # Add simulation info
        tree.insert('', tk.END, text='', values=('', ''))
        tree.insert('', tk.END, text='Simulation Information', values=('', ''))
        tree.insert('', tk.END, text='  Mode', values=(self.result_data.get('mode', 'N/A'), ''))
        tree.insert('', tk.END, text='  Timestamp', values=(self.result_data.get('timestamp', 'N/A'), ''))
        
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
        """Create editable parameters tab"""
        main_frame = tk.Frame(parent, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create two sections: Input Parameters and Erosion Statistics
        
        # Input Parameters Frame
        params_label = tk.Label(
            main_frame,
            text="Input Parameters (Editable)",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        params_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        params_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create canvas with scrollbar for parameters
        canvas = tk.Canvas(params_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(params_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store parameter entry fields for later access
        self.param_entries = {}
        
        params = self.result_data.get('parameters', {})
        if hasattr(params, 'to_dict'):
            params = params.to_dict()
        elif hasattr(params, '__dict__'):
            params = params.__dict__
        elif not isinstance(params, dict):
            params = {}
        
        for key, value in params.items():
            param_row = tk.Frame(scrollable_frame, bg='white')
            param_row.pack(fill=tk.X, padx=15, pady=8)
            
            label = tk.Label(
                param_row,
                text=f"{key}:",
                font=("Arial", 10),
                bg='white',
                fg='#34495e',
                width=25,
                anchor=tk.W
            )
            label.pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(
                param_row,
                font=("Arial", 10),
                width=30
            )
            entry.insert(0, str(value))
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            self.param_entries[key] = entry
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame for parameter actions
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        update_btn = tk.Button(
            button_frame,
            text="Update Parameters",
            font=("Arial", 10),
            bg='#3498db',
            fg='white',
            padx=15,
            pady=5,
            command=self._update_parameters
        )
        update_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(
            button_frame,
            text="Reset to Original",
            font=("Arial", 10),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=5,
            command=self._reset_parameters
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Erosion Statistics Frame
        stats_label = tk.Label(
            main_frame,
            text="Erosion Statistics (Calculated)",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        stats_label.pack(anchor=tk.W, padx=20, pady=(10, 10))
        
        stats_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        stats_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 20))
        
        # Create tree view for erosion statistics
        stats_tree = ttk.Treeview(
            stats_frame,
            columns=('Value', 'Unit'),
            height=10,
            show='tree headings'
        )
        
        stats_tree.column('#0', width=250, anchor=tk.W)
        stats_tree.column('Value', width=150, anchor=tk.CENTER)
        stats_tree.column('Unit', width=100, anchor=tk.W)
        
        stats_tree.heading('#0', text='Statistic')
        stats_tree.heading('Value', text='Value')
        stats_tree.heading('Unit', text='Unit')
        
        # Populate with erosion statistics
        erosion_stats = self._calculate_erosion_statistics()
        
        for item in erosion_stats:
            stats_tree.insert('', tk.END, values=(item[1], item[2]), text=item[0])
        
        stats_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_tree = stats_tree
    
    def _calculate_erosion_statistics(self) -> list:
        """Calculate erosion-related statistics from result data"""
        stats = []
        
        mean_erosion = self.result_data.get('mean_erosion', 0.0)
        peak_erosion = self.result_data.get('peak_erosion', 0.0)
        total_volume_loss = self.result_data.get('total_volume_loss', 0.0)
        
        # Basic statistics
        stats.append(('Mean Erosion Rate', f"{mean_erosion:.6f}", 'm/year'))
        stats.append(('Peak Erosion Rate', f"{peak_erosion:.6f}", 'm/year'))
        stats.append(('Total Volume Loss', f"{total_volume_loss:.2e}", 'm³'))
        
        # Calculated statistics
        if mean_erosion > 0:
            ratio = peak_erosion / mean_erosion if mean_erosion != 0 else 0
            stats.append(('Peak to Mean Ratio', f"{ratio:.4f}", ''))
        
        # Temporal statistics if available
        if 'temporal_evolution' in self.result_data:
            temporal = self.result_data['temporal_evolution']
            if isinstance(temporal, (list, np.ndarray)) and len(temporal) > 0:
                temporal_array = np.array(temporal)
                stats.append(('Temporal Mean', f"{np.mean(temporal_array):.6f}", 'm/year'))
                stats.append(('Temporal Std Dev', f"{np.std(temporal_array):.6f}", 'm/year'))
                stats.append(('Temporal Min', f"{np.min(temporal_array):.6f}", 'm/year'))
                stats.append(('Temporal Max', f"{np.max(temporal_array):.6f}", 'm/year'))
        
        # Spatial statistics if available
        if 'spatial_distribution' in self.result_data:
            spatial = self.result_data['spatial_distribution']
            if isinstance(spatial, (list, np.ndarray)) and len(spatial) > 0:
                spatial_array = np.array(spatial)
                stats.append(('Spatial Mean', f"{np.mean(spatial_array):.6f}", 'm/year'))
                stats.append(('Spatial Std Dev', f"{np.std(spatial_array):.6f}", 'm/year'))
                stats.append(('Spatial Min', f"{np.min(spatial_array):.6f}", 'm/year'))
                stats.append(('Spatial Max', f"{np.max(spatial_array):.6f}", 'm/year'))
        
        # Risk metrics
        if 'risk_zones' in self.result_data:
            risk_zones = self.result_data['risk_zones']
            stats.append(('High Risk Zones', f"{risk_zones.get('high', 0)}", 'count'))
            stats.append(('Medium Risk Zones', f"{risk_zones.get('medium', 0)}", 'count'))
            stats.append(('Low Risk Zones', f"{risk_zones.get('low', 0)}", 'count'))
        
        # Uncertainty metrics
        if 'uncertainty_range' in self.result_data:
            uncertainty = self.result_data['uncertainty_range']
            if isinstance(uncertainty, (tuple, list)) and len(uncertainty) == 2:
                stats.append(('Uncertainty Lower Bound', f"{uncertainty[0]:.6f}", 'm/year'))
                stats.append(('Uncertainty Upper Bound', f"{uncertainty[1]:.6f}", 'm/year'))
        
        return stats
    
    def _update_parameters(self):
        """Update parameters from entry fields and recalculate statistics"""
        try:
            updated_params = {}
            for key, entry in self.param_entries.items():
                value_str = entry.get()
                try:
                    # Try to convert to float
                    updated_params[key] = float(value_str)
                except ValueError:
                    try:
                        # Try to convert to int
                        updated_params[key] = int(value_str)
                    except ValueError:
                        # Keep as string
                        updated_params[key] = value_str
            
            self.result_data['parameters'] = updated_params
            
            # Refresh erosion statistics display
            erosion_stats = self._calculate_erosion_statistics()
            
            # Clear and repopulate the stats tree
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            
            for item in erosion_stats:
                self.stats_tree.insert('', tk.END, values=(item[1], item[2]), text=item[0])
            
            messagebox.showinfo("Success", "Parameters updated and statistics recalculated!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update parameters: {str(e)}")
    
    def _reset_parameters(self):
        """Reset parameters to original values"""
        original_params = self.result_data.get('parameters', {})
        if hasattr(original_params, 'to_dict'):
            original_params = original_params.to_dict()
        elif hasattr(original_params, '__dict__'):
            original_params = original_params.__dict__
        elif not isinstance(original_params, dict):
            original_params = {}
        
        for key, entry in self.param_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(original_params.get(key, '')))
        
        messagebox.showinfo("Reset", "Parameters reset to original values!")
    
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
    
    def _create_export_tab(self, parent):
        """Create export/sharing tab with multiple formats"""
        content_frame = tk.Frame(parent, bg='white', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(
            content_frame,
            text="Export Results in Multiple Formats",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # Export options
        export_options = tk.Frame(content_frame, bg='white')
        export_options.pack(fill=tk.X, padx=15, pady=10)
        
        exports = [
            ("📄 JSON Format", self._export_json, "Portable format for data interchange"),
            ("📊 CSV Format", self._export_csv, "Spreadsheet-compatible format"),
            ("🖼️  GeoTIFF", self._export_geotiff, "Geospatial raster format"),
            ("🌐 GeoJSON", self._export_geojson, "Web-friendly vector format"),
            ("📈 HDF5", self._export_hdf5, "Hierarchical data format"),
            ("📋 Excel", self._export_excel, "Microsoft Excel spreadsheet"),
        ]
        
        for label, command, desc in exports:
            btn_frame = tk.Frame(export_options, bg='#f5f5f5', relief=tk.RAISED, bd=1)
            btn_frame.pack(fill=tk.X, pady=5)
            
            btn = tk.Button(
                btn_frame,
                text=label,
                font=("Arial", 10, "bold"),
                bg='#3498db',
                fg='white',
                relief=tk.FLAT,
                padx=15,
                pady=10,
                command=command
            )
            btn.pack(side=tk.LEFT, padx=10, pady=8)
            
            tk.Label(
                btn_frame,
                text=desc,
                font=("Arial", 9),
                bg='#f5f5f5',
                fg='#7f8c8d'
            ).pack(side=tk.LEFT, padx=10, pady=8)
    
    def _export_json(self):
        """Export as JSON"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.result_data, f, indent=2, default=str)
            messagebox.showinfo("Success", f"Exported to:\n{file_path}")
    
    def _export_csv(self):
        """Export as CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.result_data.keys())
                    writer.writerow(self.result_data.values())
                messagebox.showinfo("Success", f"Exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")
    
    def _export_geotiff(self):
        """Export as GeoTIFF"""
        messagebox.showinfo("GeoTIFF Export", "GeoTIFF export feature coming soon!")
    
    def _export_geojson(self):
        """Export as GeoJSON"""
        messagebox.showinfo("GeoJSON Export", "GeoJSON export feature coming soon!")
    
    def _export_hdf5(self):
        """Export as HDF5"""
        messagebox.showinfo("HDF5 Export", "HDF5 export feature coming soon!")
    
    def _export_excel(self):
        """Export as Excel"""
        messagebox.showinfo("Excel Export", "Excel export feature coming soon!")
    
    def _show_summary(self):
        """Show summary view"""
        self.status_label.config(text="Showing summary statistics")
    
    def _show_charts(self):
        """Show charts and graphs"""
        self.status_label.config(text="Displaying analysis charts")
    
    def _show_details(self):
        """Show detailed information"""
        self.status_label.config(text="Displaying detailed information")
    
    def _refresh_stats(self):
        """Refresh statistics"""
        self.status_label.config(text="Statistics refreshed")
        messagebox.showinfo("Refresh", "Statistics have been recalculated")
    
    def _style_visualization(self):
        """Style visualization options"""
        dialog = tk.Toplevel(self.master)
        dialog.title("Visualization Styling")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Color Scheme:", font=("Arial", 10, "bold")).pack(pady=10)
        
        schemes = ["Viridis", "Terrain", "Jet", "RdYlGn", "Cool", "Hot"]
        for scheme in schemes:
            tk.Button(dialog, text=scheme, width=20, bg='#3498db', fg='white').pack(pady=2)
        
        tk.Button(
            dialog,
            text="Apply",
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            command=dialog.destroy
        ).pack(pady=20)
    
    def _zoom_to_fit(self):
        """Zoom to fit extent"""
        self.status_label.config(text="Zoomed to fit view")
    
    def _globe_view(self):
        """Switch to globe/3D view"""
        self.status_label.config(text="Switched to globe view")
    
    def set_result_data(self, data: Dict[str, Any]):
        """Update result data and refresh display"""
        self.result_data = data
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh all displays with new data"""
        self.update_idletasks()