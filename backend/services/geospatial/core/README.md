# TerraSim GIS Engine - QGIS-Like Geospatial Framework

A comprehensive, production-grade geospatial framework for TerraSim inspired by QGIS architecture. Provides professional GIS capabilities for terrain analysis, erosion modeling, and spatial operations.

## Architecture Overview

### Core Components

#### 1. **Layer System** (`core/layer.py`)
- Base `Layer` class with common functionality
- `RasterLayer` - DEM, satellite imagery, raster data
- `VectorLayer` - Points, lines, polygons, attributes
- `PointCloudLayer` - LAS/LAZ point cloud data
- Layer properties: visibility, opacity, style, extent, CRS

#### 2. **Canvas & Project Management** (`core/canvas.py`)
- `Canvas` - Map rendering and layer composition
- `LayerTree` - Hierarchical layer organization
- Navigation: zoom, pan, extent management
- Rendering settings and callbacks

#### 3. **Coordinate Reference Systems** (`core/crs.py`)
- `CRS` - Coordinate reference system management
- EPSG code support (4326, 3857, 2154, 32633, etc.)
- `CoordinateTransformer` - Transform coordinates between CRS
- Projection handling

#### 4. **Data I/O Framework** (`core/data_providers.py`)
- Pluggable data provider system
- GeoTIFF raster reader/writer
- Shapefile vector reader/writer
- LAS/LAZ point cloud reader/writer
- GeoJSON reader/writer
- Easy to extend for custom formats

#### 5. **Spatial Operations** (`core/spatial_ops.py`)
- `RasterAnalysis`:
  - Hillshade generation
  - Slope calculation
  - Aspect calculation
  - Curvature analysis
  - Change detection
- `VolumeAnalysis`:
  - Elevation change calculation
  - Erosion/deposition volume estimation
  - Point cloud volume calculation
- `FeatureStatistics`: Vector layer statistics

#### 6. **Processing Framework** (`core/processing.py`)
- Algorithm framework similar to QGIS Processing
- Built-in algorithms:
  - HillshadeAlgorithm
  - SlopeAlgorithm
  - ErosionAnalysisAlgorithm
- `ProcessingRegistry` for extensibility
- Parameter validation and result handling

#### 7. **GIS Engine** (`core/gis_engine.py`)
- `TerraSIMGISEngine` - Main orchestrator
- Canvas management
- Layer lifecycle management
- Algorithm execution
- Spatial analysis
- Layer caching

#### 8. **REST API** (`gis_api_service.py`)
- FastAPI endpoints for all GIS operations
- Canvas CRUD and navigation
- Layer management
- Data I/O
- Processing algorithm execution
- Analysis workflows

## Key Features

### Layer Management
```python
engine = TerraSIMGISEngine()
canvas = engine.create_canvas("Main Map", crs="EPSG:4326")

# Load layer from file
dem_layer = engine.load_layer("data/dem.tif", name="Digital Elevation Model")

# Add to canvas
engine.add_layer(dem_layer)

# Set properties
dem_layer.opacity = 0.8
dem_layer.is_visible = True
```

### Spatial Analysis
```python
# Calculate DEM derivatives
derivatives = engine.compute_dem_derivatives(dem_layer.id)
# Returns: slope, aspect, hillshade layers

# Analyze erosion between two DEMs
erosion_stats = engine.analyze_erosion(dem_before_id, dem_after_id, cell_size=1.0)
# Returns: erosion volume, deposition volume, area statistics
```

### Processing Algorithms
```python
# List available algorithms
algorithms = engine.get_processing_algorithms()

# Run algorithm
params = {
    'dem_layer': dem_layer,
    'azimuth': 315,
    'altitude': 45,
    'output': 'hillshade_output'
}
result = engine.run_algorithm('Raster Analysis:hillshade', params)
```

### Coordinate Transformation
```python
transformer = engine.create_coordinate_transformer('EPSG:4326', 'EPSG:3857')
x_out, y_out = transformer.transform_point(2.3522, 48.8566)
```

### Canvas Navigation
```python
canvas = engine.get_active_canvas()

# Zoom to layer extent
canvas.zoom_to_layer(layer.id)

# Zoom to all visible layers
canvas.zoom_to_all_layers()

# Zoom in/out
canvas.zoom(2.0)  # Zoom in 2x

# Pan
canvas.pan(100, 50)  # Pixels

# Set extent
extent = Extent(xmin=-180, ymin=-90, xmax=180, ymax=90)
canvas.zoom_to_extent(extent)
```

## API Endpoints

### Canvas Management
```
POST   /api/gis/canvases                      - Create canvas
GET    /api/gis/canvases                      - List canvases
GET    /api/gis/canvases/{canvas_id}          - Get canvas details
POST   /api/gis/canvases/{canvas_id}/active   - Set active canvas
DELETE /api/gis/canvases/{canvas_id}          - Delete canvas
```

### Layer Operations
```
POST   /api/gis/layers/load                   - Load layer from file
GET    /api/gis/layers                        - List layers
GET    /api/gis/layers/{layer_id}             - Get layer details
POST   /api/gis/layers/{layer_id}/visibility  - Set visibility
POST   /api/gis/layers/{layer_id}/opacity     - Set opacity
POST   /api/gis/layers/{layer_id}/save        - Save layer to file
DELETE /api/gis/layers/{layer_id}             - Delete layer
GET    /api/gis/layers/{layer_id}/statistics  - Get layer statistics
```

### Canvas Navigation
```
POST   /api/gis/canvases/{canvas_id}/extent                  - Set extent
POST   /api/gis/canvases/{canvas_id}/zoom-to-layer/{layer_id} - Zoom to layer
POST   /api/gis/canvases/{canvas_id}/zoom-to-all             - Zoom to all layers
POST   /api/gis/canvases/{canvas_id}/zoom                    - Zoom in/out
```

### Processing
```
GET    /api/gis/processing/algorithms         - List algorithms
POST   /api/gis/processing/run/{algorithm_id} - Run algorithm
```

### Analysis
```
POST   /api/gis/analysis/dem-derivatives/{dem_id} - Compute DEM derivatives
POST   /api/gis/analysis/erosion                  - Analyze erosion
```

### Coordinate Systems
```
POST   /api/gis/crs/transform                 - Transform coordinates
```

## File Structure

```
backend/services/geospatial/
├── core/
│   ├── __init__.py
│   ├── layer.py                 # Base layer abstractions
│   ├── raster_layer.py          # Raster layer implementation
│   ├── vector_layer.py          # Vector layer implementation
│   ├── pointcloud_layer.py      # Point cloud layer implementation
│   ├── canvas.py                # Canvas and project management
│   ├── crs.py                   # Coordinate reference systems
│   ├── spatial_ops.py           # Spatial operations and analysis
│   ├── data_providers.py        # Data I/O framework
│   ├── processing.py            # Algorithm framework
│   └── gis_engine.py            # Main orchestrator
├── gis_api_service.py           # REST API (FastAPI)
├── README.md                    # This file
└── ...existing files
```

## Extending the Framework

### Adding a New Data Format
```python
from backend.services.geospatial.core.data_providers import DataProvider

class NetCDFProvider(DataProvider):
    def can_handle(self, source: str) -> bool:
        return source.lower().endswith('.nc')
    
    def read(self, source: str):
        # Implementation
        pass
    
    def write(self, layer, destination: str) -> bool:
        # Implementation
        pass

# Register
registry = get_provider_registry()
registry.register_provider(NetCDFProvider())
```

### Adding a New Processing Algorithm
```python
from backend.services.geospatial.core.processing import ProcessingAlgorithm

class CustomAlgorithm(ProcessingAlgorithm):
    def __init__(self):
        super().__init__("custom", "Custom Analysis")
        self.define_parameters()
    
    def define_parameters(self):
        self.parameters = [
            # Define parameters
        ]
    
    def process(self, parameters):
        # Implementation
        return ProcessingResult(success=True, ...)

# Register
registry = get_processing_registry()
registry.register(CustomAlgorithm())
```

## Performance Considerations

- **Layer Caching**: Layers are cached in memory for quick access
- **Lazy Loading**: Data is loaded on-demand, not preloaded
- **Spatial Indexing**: Support for spatial indices (extensible)
- **Vectorized Operations**: NumPy for fast raster processing
- **Streaming**: Large files can be processed in chunks

## Dependencies

- numpy - Array operations
- rasterio - GeoTIFF I/O
- shapely - Vector geometry
- shapefile - Shapefile I/O
- laspy - LAS/LAZ point cloud I/O
- GDAL - (optional) Advanced geospatial operations
- FastAPI - REST API framework
- Pydantic - Data validation

## Usage Example

```python
from backend.services.geospatial.core import TerraSIMGISEngine

# Initialize
engine = TerraSIMGISEngine("TerraSim")

# Create canvas
canvas = engine.create_canvas("Project 1", crs="EPSG:32633")

# Load data
dem = engine.load_layer("data/dem.tif", name="Elevation")
orthophoto = engine.load_layer("data/ortho.tif", name="Orthophoto")
rivers = engine.load_layer("data/rivers.shp", name="Rivers")

# Add to canvas
engine.add_layer(dem)
engine.add_layer(orthophoto)
engine.add_layer(rivers)

# Analyze
stats = engine.calculate_layer_statistics(dem.id)
derivatives = engine.compute_dem_derivatives(dem.id)

# Export
engine.save_layer(derivatives['slope'].id, "output/slope.tif")

# Get status
status = engine.get_status()
print(status)
```

## License

TerraSim GIS Engine - Part of TerraSim project
