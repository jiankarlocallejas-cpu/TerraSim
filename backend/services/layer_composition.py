"""
Layer Composition System - Save/Load map layouts with layer state
Manages persistence of map configurations including layers, visibility, opacity, and parameters
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class LayerInfo:
    """Information about a single layer"""
    name: str
    layer_type: str  # 'dem', 'base_map', 'parameters'
    file_path: str
    file_format: str  # 'tif', 'csv', 'json', 'npy', 'shp', 'geojson', etc.
    visible: bool = True
    opacity: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MapLayout:
    """Complete map layout configuration"""
    name: str
    description: str = ""
    created: str = ""
    modified: str = ""
    layers: List[Dict[str, Any]] = field(default_factory=list)
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    viewport: Dict[str, Any] = field(default_factory=dict)  # Camera/zoom state
    
    def __post_init__(self):
        if self.created == "":
            self.created = datetime.now().isoformat()
        if self.modified == "":
            self.modified = datetime.now().isoformat()


class LayerCompositionManager:
    """Manages layer compositions and map layout persistence"""
    
    def __init__(self, layouts_dir: str = "map_layouts"):
        """
        Initialize the layer composition manager
        
        Args:
            layouts_dir: Directory to store layout files
        """
        self.layouts_dir = layouts_dir
        self.current_layout: Optional[MapLayout] = None
        self.layers: Dict[str, LayerInfo] = {}
        
        # Create layouts directory if it doesn't exist
        os.makedirs(layouts_dir, exist_ok=True)
        logger.info(f"Layer composition manager initialized with layouts_dir: {layouts_dir}")
    
    def add_layer(self, layer_info: LayerInfo) -> None:
        """Add or update a layer in the composition"""
        self.layers[layer_info.name] = layer_info
        logger.info(f"Added layer: {layer_info.name} ({layer_info.layer_type})")
    
    def remove_layer(self, layer_name: str) -> bool:
        """Remove a layer from the composition"""
        if layer_name in self.layers:
            del self.layers[layer_name]
            logger.info(f"Removed layer: {layer_name}")
            return True
        return False
    
    def update_layer_visibility(self, layer_name: str, visible: bool) -> bool:
        """Update layer visibility"""
        if layer_name in self.layers:
            self.layers[layer_name].visible = visible
            return True
        return False
    
    def update_layer_opacity(self, layer_name: str, opacity: float) -> bool:
        """Update layer opacity (0.0 - 1.0)"""
        if layer_name in self.layers:
            self.layers[layer_name].opacity = max(0.0, min(1.0, opacity))
            return True
        return False
    
    def get_layer(self, layer_name: str) -> Optional[LayerInfo]:
        """Get layer information"""
        return self.layers.get(layer_name)
    
    def get_all_layers(self, layer_type: Optional[str] = None) -> List[LayerInfo]:
        """Get all layers, optionally filtered by type"""
        layers = list(self.layers.values())
        if layer_type:
            layers = [l for l in layers if l.layer_type == layer_type]
        return layers
    
    def get_visible_layers(self, layer_type: Optional[str] = None) -> List[LayerInfo]:
        """Get visible layers, optionally filtered by type"""
        layers = [l for l in self.layers.values() if l.visible]
        if layer_type:
            layers = [l for l in layers if l.layer_type == layer_type]
        return layers
    
    def create_layout(self, name: str, description: str = "") -> MapLayout:
        """Create a new layout from current layer state"""
        layout = MapLayout(
            name=name,
            description=description,
            layers=[asdict(layer) for layer in self.layers.values()]
        )
        self.current_layout = layout
        logger.info(f"Created layout: {name}")
        return layout
    
    def save_layout(self, layout: MapLayout, filename: Optional[str] = None) -> str:
        """
        Save layout to file
        
        Args:
            layout: MapLayout object to save
            filename: Optional custom filename (default: layout name + timestamp)
        
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{layout.name.replace(' ', '_')}_{timestamp}.json"
        
        filepath = os.path.join(self.layouts_dir, filename)
        
        layout.modified = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(asdict(layout), f, indent=2)
        
        logger.info(f"Saved layout to: {filepath}")
        return filepath
    
    def load_layout(self, filepath: str) -> MapLayout:
        """
        Load layout from file
        
        Args:
            filepath: Path to layout file
        
        Returns:
            Loaded MapLayout object
        """
        with open(filepath, 'r') as f:
            layout_data = json.load(f)
        
        layout = MapLayout(**layout_data)
        
        # Reconstruct layer objects
        self.layers = {}
        for layer_data in layout.layers:
            layer = LayerInfo(**layer_data)
            self.layers[layer.name] = layer
        
        self.current_layout = layout
        logger.info(f"Loaded layout from: {filepath}")
        return layout
    
    def list_layouts(self) -> List[Dict[str, str]]:
        """List all available layouts"""
        layouts = []
        if os.path.exists(self.layouts_dir):
            for filename in os.listdir(self.layouts_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.layouts_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        layouts.append({
                            'filename': filename,
                            'filepath': filepath,
                            'name': data.get('name', filename),
                            'description': data.get('description', ''),
                            'created': data.get('created', ''),
                            'modified': data.get('modified', '')
                        })
                    except Exception as e:
                        logger.warning(f"Error reading layout {filename}: {e}")
        
        return sorted(layouts, key=lambda x: x.get('modified', ''), reverse=True)
    
    def delete_layout(self, filepath: str) -> bool:
        """Delete a layout file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted layout: {filepath}")
                return True
        except Exception as e:
            logger.error(f"Error deleting layout {filepath}: {e}")
        return False
    
    def export_layout(self, layout: MapLayout, export_path: str) -> str:
        """
        Export layout with relative paths for portability
        
        Args:
            layout: Layout to export
            export_path: Path to export file
        
        Returns:
            Path to exported file
        """
        export_layout = MapLayout(
            name=layout.name,
            description=layout.description,
            layers=[]
        )
        
        # Convert absolute paths to relative
        for layer_data in layout.layers:
            layer_copy = layer_data.copy()
            try:
                rel_path = os.path.relpath(layer_data['file_path'], os.path.dirname(export_path))
                layer_copy['file_path'] = rel_path
            except ValueError:
                # If on different drives, keep absolute path
                pass
            export_layout.layers.append(layer_copy)
        
        with open(export_path, 'w') as f:
            json.dump(asdict(export_layout), f, indent=2)
        
        logger.info(f"Exported layout to: {export_path}")
        return export_path
    
    def import_layout(self, import_path: str, base_dir: Optional[str] = None) -> MapLayout:
        """
        Import layout with relative path resolution
        
        Args:
            import_path: Path to import file
            base_dir: Base directory for resolving relative paths (default: import file directory)
        
        Returns:
            Loaded MapLayout object
        """
        if base_dir is None:
            base_dir = os.path.dirname(import_path)
        
        with open(import_path, 'r') as f:
            layout_data = json.load(f)
        
        # Resolve relative paths
        for layer_data in layout_data.get('layers', []):
            file_path = layer_data['file_path']
            if not os.path.isabs(file_path):
                file_path = os.path.join(base_dir, file_path)
            layer_data['file_path'] = os.path.normpath(file_path)
        
        layout = MapLayout(**layout_data)
        
        # Reconstruct layer objects
        self.layers = {}
        for layer_data in layout.layers:
            layer = LayerInfo(**layer_data)
            self.layers[layer.name] = layer
        
        self.current_layout = layout
        logger.info(f"Imported layout from: {import_path}")
        return layout
    
    def get_layout_summary(self) -> Dict[str, Any]:
        """Get summary of current layout"""
        if not self.current_layout:
            return {}
        
        layer_summary = {
            'dem': [],
            'base_map': [],
            'parameters': []
        }
        
        for layer in self.layers.values():
            layer_type = layer.layer_type
            if layer_type in layer_summary:
                layer_summary[layer_type].append({
                    'name': layer.name,
                    'path': layer.file_path,
                    'visible': layer.visible,
                    'opacity': layer.opacity
                })
        
        return {
            'layout_name': self.current_layout.name,
            'description': self.current_layout.description,
            'created': self.current_layout.created,
            'modified': self.current_layout.modified,
            'layers': layer_summary,
            'total_layers': len(self.layers)
        }
