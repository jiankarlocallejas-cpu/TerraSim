"""
GIS Canvas - Interactive map visualization similar to QGIS/ArcGIS
Handles 2D map rendering, layer management, and map interactions
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import logging

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.patches as patches
    from matplotlib.colors import Normalize
    import matplotlib.cm as cm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class GISCanvas:
    """Interactive GIS canvas for map visualization and interaction"""
    
    def __init__(self, parent_frame, width=800, height=600):
        self.parent_frame = parent_frame
        self.width = width
        self.height = height
        
        # Create matplotlib figure and axes
        self.fig = Figure(figsize=(width/100, height/100), dpi=100, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        
        # Canvas setup
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Layer data storage
        self.layers = {}
        self.active_layer = None
        self.extent = [0, 100, 0, 100]  # [xmin, xmax, ymin, ymax]
        
        # Interaction state
        self.pan_data = None
        self.zoom_level = 1.0
        
        # Bind events
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        
        # Initialize empty plot
        self._init_plot()
    
    def _init_plot(self):
        """Initialize the plot"""
        self.ax.set_facecolor('#f0f0f0')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_xlabel('X (meters)')
        self.ax.set_ylabel('Y (meters)')
        self.ax.set_title('GIS Canvas')
        self.canvas.draw()
    
    def add_dem_layer(self, dem_data, name='DEM', colormap='terrain'):
        """Add a DEM raster layer"""
        if dem_data is None or len(dem_data) == 0:
            logger.warning("Cannot add empty DEM layer")
            return False
        
        try:
            self.layers[name] = {
                'type': 'raster',
                'data': dem_data,
                'colormap': colormap,
                'visible': True,
                'alpha': 0.8
            }
            self.active_layer = name
            self._update_extent_from_dem(dem_data)
            self.render()
            logger.info(f"Added DEM layer: {name}")
            return True
        except Exception as e:
            logger.error(f"Error adding DEM layer: {e}")
            return False
    
    def add_vector_layer(self, geometries, name='Vector', style=None):
        """Add a vector layer (points, lines, polygons)"""
        try:
            self.layers[name] = {
                'type': 'vector',
                'geometries': geometries,
                'visible': True,
                'style': style or {}
            }
            self.active_layer = name
            self.render()
            logger.info(f"Added vector layer: {name}")
            return True
        except Exception as e:
            logger.error(f"Error adding vector layer: {e}")
            return False
    
    def add_analysis_layer(self, data, name='Analysis', colormap='viridis'):
        """Add an analysis result layer"""
        try:
            self.layers[name] = {
                'type': 'analysis',
                'data': data,
                'colormap': colormap,
                'visible': True,
                'alpha': 0.7
            }
            self.active_layer = name
            self._update_extent_from_dem(data)
            self.render()
            logger.info(f"Added analysis layer: {name}")
            return True
        except Exception as e:
            logger.error(f"Error adding analysis layer: {e}")
            return False
    
    def remove_layer(self, name):
        """Remove a layer"""
        if name in self.layers:
            del self.layers[name]
            if self.active_layer == name:
                self.active_layer = list(self.layers.keys())[0] if self.layers else None
            self.render()
            return True
        return False
    
    def toggle_layer_visibility(self, name):
        """Toggle layer visibility"""
        if name in self.layers:
            self.layers[name]['visible'] = not self.layers[name]['visible']
            self.render()
            return self.layers[name]['visible']
        return False
    
    def set_layer_opacity(self, name, alpha):
        """Set layer opacity (0-1)"""
        if name in self.layers:
            self.layers[name]['alpha'] = max(0, min(1, alpha))
            self.render()
    
    def render(self):
        """Render all visible layers"""
        self.ax.clear()
        self.ax.set_facecolor('#f0f0f0')
        
        # Sort layers by type (raster first, then vector)
        sorted_layers = sorted(
            [(k, v) for k, v in self.layers.items() if v['visible']],
            key=lambda x: (x[1]['type'] != 'raster', k)
        )
        
        for layer_name, layer_data in sorted_layers:
            self._render_layer(layer_name, layer_data)
        
        self.ax.set_xlim(self.extent[0], self.extent[1])
        self.ax.set_ylim(self.extent[2], self.extent[3])
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_xlabel('X (meters)')
        self.ax.set_ylabel('Y (meters)')
        self.ax.set_title(f'GIS Canvas - Active: {self.active_layer}')
        self.canvas.draw()
    
    def _render_layer(self, name, layer_data):
        """Render individual layer"""
        try:
            if layer_data['type'] in ['raster', 'analysis']:
                self._render_raster(layer_data)
            elif layer_data['type'] == 'vector':
                self._render_vector(layer_data)
        except Exception as e:
            logger.error(f"Error rendering layer {name}: {e}")
    
    def _render_raster(self, layer_data):
        """Render raster layer"""
        data = layer_data['data']
        colormap = layer_data.get('colormap', 'terrain')
        alpha = layer_data.get('alpha', 0.8)
        
        im = self.ax.imshow(
            data,
            cmap=colormap,
            origin='lower',
            alpha=alpha,
            extent=(float(self.extent[0]), float(self.extent[1]), float(self.extent[2]), float(self.extent[3]))
        )
        plt.colorbar(im, ax=self.ax, label='Elevation (m)')
    
    def _render_vector(self, layer_data):
        """Render vector layer"""
        geometries = layer_data['geometries']
        style = layer_data.get('style', {})
        
        for geom in geometries:
            if hasattr(geom, 'exterior'):  # Polygon
                x, y = geom.exterior.xy
                self.ax.fill(x, y, alpha=0.3, color=style.get('color', 'blue'))
                self.ax.plot(x, y, color=style.get('color', 'blue'))
            elif hasattr(geom, 'xy'):  # Point
                x, y = geom.xy
                self.ax.plot(x, y, 'o', color=style.get('color', 'red'))
            elif hasattr(geom, 'coords'):  # LineString
                x, y = geom.xy
                self.ax.plot(x, y, color=style.get('color', 'green'))
    
    def _update_extent_from_dem(self, dem_data):
        """Update map extent from DEM data"""
        h, w = dem_data.shape
        self.extent = [0, w, 0, h]
    
    def zoom_to_fit(self):
        """Zoom to fit all layers"""
        self.zoom_level = 1.0
        self.ax.set_xlim(self.extent[0], self.extent[1])
        self.ax.set_ylim(self.extent[2], self.extent[3])
        self.canvas.draw()
    
    def zoom_in(self, factor=1.5):
        """Zoom in"""
        self.zoom_level *= factor
        self._apply_zoom()
    
    def zoom_out(self, factor=1.5):
        """Zoom out"""
        self.zoom_level /= factor
        self._apply_zoom()
    
    def _apply_zoom(self):
        """Apply zoom transformation"""
        center_x = (self.extent[0] + self.extent[1]) / 2
        center_y = (self.extent[2] + self.extent[3]) / 2
        width = (self.extent[1] - self.extent[0]) / self.zoom_level
        height = (self.extent[3] - self.extent[2]) / self.zoom_level
        
        self.ax.set_xlim(center_x - width/2, center_x + width/2)
        self.ax.set_ylim(center_y - height/2, center_y + height/2)
        self.canvas.draw()
    
    def _on_press(self, event):
        """Handle mouse press for panning"""
        if event.inaxes != self.ax or event.button != 1:
            return
        self.pan_data = (event.xdata, event.ydata)
    
    def _on_release(self, event):
        """Handle mouse release"""
        self.pan_data = None
    
    def _on_motion(self, event):
        """Handle mouse motion for panning"""
        if self.pan_data is None or event.inaxes != self.ax:
            return
        
        dx = self.pan_data[0] - event.xdata
        dy = self.pan_data[1] - event.ydata
        
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
        self.canvas.draw_idle()
    
    def _on_scroll(self, event):
        """Handle scroll wheel for zooming"""
        if event.inaxes != self.ax:
            return
        
        if event.button == 'up':
            self.zoom_in(1.2)
        elif event.button == 'down':
            self.zoom_out(1.2)
    
    def get_layer_list(self):
        """Get list of all layers"""
        return list(self.layers.keys())
    
    def get_layer_info(self, name):
        """Get information about a layer"""
        if name in self.layers:
            layer = self.layers[name]
            info = {
                'name': name,
                'type': layer['type'],
                'visible': layer['visible'],
                'alpha': layer.get('alpha', 1.0)
            }
            if layer['type'] in ['raster', 'analysis']:
                data = layer['data']
                info['shape'] = data.shape
                info['min'] = float(np.nanmin(data))
                info['max'] = float(np.nanmax(data))
                info['mean'] = float(np.nanmean(data))
            return info
        return None
    
    def export_current_view(self, filepath):
        """Export current view to image"""
        try:
            self.fig.savefig(filepath, dpi=150, bbox_inches='tight')
            logger.info(f"Exported view to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting view: {e}")
            return False
