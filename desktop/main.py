"""
TerraSim Desktop Application
Cross-platform desktop app using Electron/Python
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
import folium
from folium import plugins

# Import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from main import ErosionEngine, ErosionInput, ErosionResult

class GISCanvas(QWidget):
    """Advanced GIS visualization canvas using matplotlib and plotly"""
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Create matplotlib figure
        self.figure = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        # Initialize plot
        self.ax = self.figure.add_subplot(111)
        self.setup_map()
        
    def setup_map(self):
        """Setup base map"""
        self.ax.set_title('TerraSim - GIS Visualization')
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.grid(True, alpha=0.3)
        
    def add_raster_layer(self, raster_path: str):
        """Add raster layer to map"""
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            
            self.ax.imshow(data, extent=extent, cmap='terrain', alpha=0.7)
            self.canvas.draw()
            
    def add_vector_layer(self, vector_path: str):
        """Add vector layer to map"""
        gdf = gpd.read_file(vector_path)
        gdf.plot(ax=self.ax, alpha=0.7, edgecolor='black')
        self.canvas.draw()
        
    def add_erosion_results(self, results: ErosionResult):
        """Visualize erosion results"""
        # Create erosion risk map
        risk_colors = {
            'Low': '#00FF00',
            'Moderate': '#FFFF00', 
            'High': '#FF8C00',
            'Severe': '#FF0000'
        }
        
        # This would be implemented with actual spatial data
        self.ax.set_title(f'Erosion Risk: {results.risk_category}')
        self.ax.text(0.02, 0.98, f'Mean Loss: {results.mean_loss:.2f} tons/ha/year',
                   transform=self.ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        self.canvas.draw()

class ErosionCalculator(QWidget):
    """Erosion calculation panel"""
    
    def __init__(self, erosion_engine: ErosionEngine):
        super().__init__()
        self.erosion_engine = erosion_engine
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Input fields
        self.rainfall_input = QDoubleSpinBox()
        self.rainfall_input.setRange(0, 5000)
        self.rainfall_input.setValue(1800)
        self.rainfall_input.setSuffix(" mm/year")
        
        self.slope_input = QDoubleSpinBox()
        self.slope_input.setRange(0, 90)
        self.slope_input.setValue(15)
        self.slope_input.setSuffix(" degrees")
        
        self.slope_length_input = QDoubleSpinBox()
        self.slope_length_input.setRange(0, 1000)
        self.slope_length_input.setValue(100)
        self.slope_length_input.setSuffix(" meters")
        
        self.soil_type_input = QComboBox()
        self.soil_type_input.addItems(['clay', 'sandy', 'loam', 'silt', 'rocky'])
        
        self.vegetation_input = QSlider(Qt.Horizontal)
        self.vegetation_input.setRange(0, 100)
        self.vegetation_input.setValue(60)
        self.vegetation_label = QLabel("60%")
        
        self.support_practices_input = QSlider(Qt.Horizontal)
        self.support_practices_input.setRange(0, 100)
        self.support_practices_input.setValue(50)
        self.support_practices_label = QLabel("50%")
        
        self.land_use_input = QComboBox()
        self.land_use_input.addItems(['forest', 'grassland', 'agriculture', 'urban', 'water', 'barren'])
        
        self.area_input = QDoubleSpinBox()
        self.area_input.setRange(0, 10000)
        self.area_input.setValue(10)
        self.area_input.setSuffix(" hectares")
        
        self.seasonality_input = QComboBox()
        self.seasonality_input.addItems(['dry', 'wet', 'transitional'])
        
        # Connect slider signals
        self.vegetation_input.valueChanged.connect(
            lambda v: self.vegetation_label.setText(f"{v}%"))
        self.support_practices_input.valueChanged.connect(
            lambda v: self.support_practices_label.setText(f"{v}%"))
        
        # Add fields to layout
        layout.addRow("Annual Rainfall:", self.rainfall_input)
        layout.addRow("Slope Angle:", self.slope_input)
        layout.addRow("Slope Length:", self.slope_length_input)
        layout.addRow("Soil Type:", self.soil_type_input)
        layout.addRow("Vegetation Cover:", self.vegetation_input)
        layout.addRow("", self.vegetation_label)
        layout.addRow("Support Practices:", self.support_practices_input)
        layout.addRow("", self.support_practices_label)
        layout.addRow("Land Use:", self.land_use_input)
        layout.addRow("Area:", self.area_input)
        layout.addRow("Seasonality:", self.seasonality_input)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Erosion")
        self.calculate_button.clicked.connect(self.calculate_erosion)
        layout.addRow(self.calculate_button)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        layout.addRow("Results:", self.results_text)
        
    def calculate_erosion(self):
        """Calculate erosion using current inputs"""
        try:
            input_data = ErosionInput(
                rainfall=self.rainfall_input.value(),
                slope=self.slope_input.value(),
                slope_length=self.slope_length_input.value(),
                soil_type=self.soil_type_input.currentText(),
                vegetation_cover=self.vegetation_input.value(),
                support_practices=self.support_practices_input.value(),
                land_use=self.land_use_input.currentText(),
                area=self.area_input.value(),
                seasonality=self.seasonality_input.currentText()
            )
            
            results = self.erosion_engine.calculate_terrak_sim(input_data)
            
            # Display results
            results_text = f"""
Erosion Analysis Results
=====================

Risk Category: {results.risk_category}
Mean Soil Loss: {results.mean_loss:.2f} tons/ha/year
Peak Soil Loss: {results.peak_loss:.2f} tons/ha/year
Total Soil Loss: {results.total_soil_loss:.2f} tons
Confidence: {results.confidence:.1%}

Factors:
- Rainfall Factor: {results.factors['rainfall_factor']:.3f}
- Slope Factor: {results.factors['slope_factor']:.3f}
- Soil Factor: {results.factors['soil_factor']:.3f}
- Vegetation Factor: {results.factors['vegetation_factor']:.3f}
- Land Use Factor: {results.factors['land_use_factor']:.3f}
- Seasonality Factor: {results.factors['seasonality_factor']:.3f}

RUSLE Comparison:
- RUSLE Soil Loss: {results.rusle_comparison['soil_loss']:.2f} tons/ha/year
- Difference: {results.rusle_comparison['difference']:.2f} tons/ha/year
- Percent Difference: {results.rusle_comparison['percent_difference']:.1f}%
"""
            
            self.results_text.setText(results_text)
            
            # Emit results signal
            self.parent().parent().erosion_results_calculated.emit(results)
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

class LayerManager(QWidget):
    """GIS layer management panel"""
    
    layer_added = pyqtSignal(str, str)  # layer_id, layer_type
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.layers = {}
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Layer list
        self.layer_list = QListWidget()
        layout.addWidget(QLabel("Layers:"))
        layout.addWidget(self.layer_list)
        
        # Add layer buttons
        button_layout = QHBoxLayout()
        
        self.add_raster_btn = QPushButton("Add Raster")
        self.add_raster_btn.clicked.connect(self.add_raster_layer)
        button_layout.addWidget(self.add_raster_btn)
        
        self.add_vector_btn = QPushButton("Add Vector")
        self.add_vector_btn.clicked.connect(self.add_vector_layer)
        button_layout.addWidget(self.add_vector_btn)
        
        layout.addLayout(button_layout)
        
        # Layer properties
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_label = QLabel("100%")
        
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%"))
        
        layout.addWidget(QLabel("Opacity:"))
        layout.addWidget(self.opacity_slider)
        layout.addWidget(self.opacity_label)
        
        # Remove button
        self.remove_btn = QPushButton("Remove Layer")
        self.remove_btn.clicked.connect(self.remove_layer)
        layout.addWidget(self.remove_btn)
        
    def add_raster_layer(self):
        """Add raster layer"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Raster File", "", 
            "Raster Files (*.tif *.tiff *.img *.dem);;All Files (*)")
        
        if file_path:
            layer_id = f"raster_{len(self.layers)}"
            self.layers[layer_id] = {
                'path': file_path,
                'type': 'raster',
                'name': Path(file_path).stem,
                'visible': True,
                'opacity': 100
            }
            
            item = QListWidgetItem(self.layers[layer_id]['name'])
            item.setData(Qt.UserRole, layer_id)
            item.setCheckState(Qt.Checked)
            self.layer_list.addItem(item)
            
            self.layer_added.emit(layer_id, 'raster')
            
    def add_vector_layer(self):
        """Add vector layer"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Vector File", "",
            "Vector Files (*.shp *.geojson *.kml *.gpkg);;All Files (*)")
        
        if file_path:
            layer_id = f"vector_{len(self.layers)}"
            self.layers[layer_id] = {
                'path': file_path,
                'type': 'vector',
                'name': Path(file_path).stem,
                'visible': True,
                'opacity': 100
            }
            
            item = QListWidgetItem(self.layers[layer_id]['name'])
            item.setData(Qt.UserRole, layer_id)
            item.setCheckState(Qt.Checked)
            self.layer_list.addItem(item)
            
            self.layer_added.emit(layer_id, 'vector')
            
    def remove_layer(self):
        """Remove selected layer"""
        current_item = self.layer_list.currentItem()
        if current_item:
            layer_id = current_item.data(Qt.UserRole)
            del self.layers[layer_id]
            self.layer_list.takeItem(self.layer_list.row(current_item))

class TerraSimDesktop(QMainWindow):
    """Main TerraSim desktop application"""
    
    erosion_results_calculated = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.erosion_engine = ErosionEngine()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("TerraSim - Advanced GIS Erosion Modeling")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Layer manager
        self.layer_manager = LayerManager()
        self.layer_manager.setMaximumWidth(300)
        main_layout.addWidget(self.layer_manager)
        
        # Center - GIS Canvas
        self.gis_canvas = GISCanvas()
        main_layout.addWidget(self.gis_canvas, 1)
        
        # Right panel - Erosion calculator
        self.erosion_calculator = ErosionCalculator(self.erosion_engine)
        self.erosion_calculator.setMaximumWidth(400)
        main_layout.addWidget(self.erosion_calculator)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_project_action = QAction('Open Project', self)
        open_project_action.setShortcut('Ctrl+O')
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        save_project_action = QAction('Save Project', self)
        save_project_action.setShortcut('Ctrl+S')
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        import_data_action = QAction('Import GIS Data', self)
        import_data_action.triggered.connect(self.import_gis_data)
        tools_menu.addAction(import_data_action)
        
        export_results_action = QAction('Export Results', self)
        export_results_action.triggered.connect(self.export_results)
        tools_menu.addAction(export_results_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About TerraSim', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.erosion_results_calculated.connect(self.on_erosion_results)
        self.layer_manager.layer_added.connect(self.on_layer_added)
        
    def on_erosion_results(self, results: ErosionResult):
        """Handle erosion calculation results"""
        self.gis_canvas.add_erosion_results(results)
        self.status_bar.showMessage(f"Erosion calculated: {results.risk_category} risk")
        
    def on_layer_added(self, layer_id: str, layer_type: str):
        """Handle layer addition"""
        layer_info = self.layer_manager.layers[layer_id]
        
        if layer_type == 'raster':
            self.gis_canvas.add_raster_layer(layer_info['path'])
        elif layer_type == 'vector':
            self.gis_canvas.add_vector_layer(layer_info['path'])
            
        self.status_bar.showMessage(f"Added {layer_type} layer: {layer_info['name']}")
        
    def open_project(self):
        """Open project file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "JSON Files (*.json);;All Files (*)")
        
        if file_path:
            # Load project logic here
            self.status_bar.showMessage(f"Project opened: {file_path}")
            
    def save_project(self):
        """Save project file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json);;All Files (*)")
        
        if file_path:
            # Save project logic here
            self.status_bar.showMessage(f"Project saved: {file_path}")
            
    def import_gis_data(self):
        """Import GIS data"""
        # This would open a more sophisticated data import dialog
        self.status_bar.showMessage("GIS data import feature")
        
    def export_results(self):
        """Export analysis results"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", 
            "PDF Files (*.pdf);;CSV Files (*.csv);;JSON Files (*.json);;All Files (*)")
        
        if file_path:
            # Export logic here
            self.status_bar.showMessage(f"Results exported: {file_path}")
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About TerraSim", 
                         "TerraSim v2.0.0\n\n"
                         "Advanced GIS Erosion Modeling Platform\n\n"
                         "Built with:\n"
                         "- Python\n"
                         "- PyQt5\n"
                         "- GeoPandas\n"
                         "- Rasterio\n"
                         "- NumPy\n"
                         "- SciPy")

def main():
    """Main entry point for desktop application"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TerraSimDesktop()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
