# TerraSim GIS - Professional Geospatial Analysis Platform

**Python-native GIS application similar to QGIS/ArcGIS for spatial analysis and erosion modeling**

---

## QUICK START

### Windows
```powershell
.\run.ps1
```

### Command Line (All Platforms)
```bash
python app.py
```

**Application launches immediately** with full GIS capabilities.

---

## ✨ Features

### GIS Core Capabilities
- [OK] **Interactive Map Canvas** - Zoom, pan, and navigate spatial data
- [OK] **Vector Support** - Shapefiles, GeoJSON, GeoPackage
- [OK] **Raster Support** - GeoTIFF, Elevation Models (DEM)
- [OK] **Layer Management** - Add, remove, reorder, show/hide layers
- [OK] **Attribute Tables** - View and edit feature properties
- [OK] **Coordinate Display** - Real-time X/Y coordinate tracking

### Spatial Analysis Tools
- [OK] **Buffer Analysis** - Create buffer zones around features
- [OK] **Spatial Selection** - Select features by clicking on the map
- [OK] **Layer Statistics** - Get info about CRS, bounds, feature count
- [OK] **Spatial Join** - Combine attributes from multiple layers
- [OK] **Color Customization** - Change layer colors for better visualization

### Data Management
- [OK] **Multi-Format Import** - Support for major GIS formats
- [OK] **Export Capabilities** - Save as Shapefile, GeoJSON, GeoTIFF
- [OK] **Project Save/Load** - Preserve your work
- [OK] **Layer Properties** - Opacity, color, visibility control

### Erosion Analysis (TerraSim Extension)
- [OK] **USPED Model** - Terrain-based erosion calculation
- [OK] **RUSLE Validation** - Compare with established method
- [OK] **Raster Analysis** - DEM, slope, flow accumulation
- [OK] **Risk Classification** - 5-tier erosion risk mapping
- [OK] **Result Export** - Maps, statistics, reports

---

## SCIENTIFIC FOUNDATION - USPED EROSION MODEL

### Core Equation (Terrain Evolution)

$$z_{t+\Delta t}(x, y)=z_{t}(x, y)-\frac{\Delta t}{\rho_{b}}\left[\frac{\partial}{\partial x}(T \cos \alpha)+\frac{\partial}{\partial y}(T \sin \alpha)+\epsilon \frac{\partial}{\partial z}(T \sin \beta)\right]$$

### Transport Capacity (Sediment Flux)

$$T=f(R, K, C, P, A^{m}, (\sin \beta)^{n}, Q(I, S))$$

Where:
- $z$ = terrain elevation (m)
- $T$ = transport capacity (sediment flux in kg/m/s)
- $R$ = rainfall erosivity (MJ·mm/ha/h/yr)
- $K$ = soil erodibility (0-1)
- $C$ = cover management factor (0-1)
- $P$ = support practice factor (0-1)
- $A$ = upslope area (m²)
- $\beta$ = slope angle
- $m, n$ = exponents (1.6, 1.3)
- $\rho_b$ = bulk density (kg/m³)

**Citation:** Mitasova, H., & Hofierka, J. (1993). "Interpolation by regularized spline with tension: II. Application to terrain modeling and surface geometry analysis." *Mathematical Geology*, 25(6), 657-669.

---

## INTERFACE OVERVIEW

### Main Window Layout
```
┌─────────────────────────────────────────────────────────┐
│  Toolbar (File | Tools | Analysis)                      │
├─────────────────┬─────────────────────┬─────────────────┤
│                 │                     │                 │
│   Layers Panel  │   Interactive Map   │  Attributes    │
│   (left)        │   Canvas (center)   │  Table (right) │
│                 │                     │                 │
│  - Add Layer    │   [Map Display]     │  [Features &   │
│  - Remove       │   Zoom/Pan/Select   │   Properties]  │
│  - Properties   │   (click & scroll)  │                │
│                 │                     │                 │
├─────────────────┴─────────────────────┴─────────────────┤
│  Status Bar: Coordinates, Zoom Level, Layer Count      │
└─────────────────────────────────────────────────────────┘
```

### Left Panel - Layers
- **Layer List** - All loaded GIS layers
- **Visibility Toggle** - Show/hide layers
- **Reorder Layers** - Move layers up/down
- **Properties** - Opacity slider, color picker
- **Controls** - Add, remove, manage layers

### Center Panel - Map Canvas
- **Interactive Map** - Click to select, scroll to zoom
- **Grid Display** - Coordinate reference grid
- **Multiple Layers** - View stacked vector and raster data
- **Zoom Controls** - Zoom in/out/fit all
- **Pan Mode** - Move around the map

### Right Panel - Attributes
- **Feature Table** - View all attributes
- **Selection Details** - Selected feature information
- **Property Editing** - Modify attribute values
- **Statistics** - Summary data

---

## TOOLBAR TOOLS

### File Operations
- **Open Layer** - Load GIS data (shapefile, GeoTIFF, GeoJSON)
- **Save Project** - Save current workspace
- **Export** - Save layer in different format

### Map Tools
- **Zoom In (🔍)** - Zoom to cursor location
- **Zoom Out (🔍)** - Zoom out from cursor
- **Pan (↗)** - Move around map
- **Select (⬚)** - Click to select features
- **Fit All** - Show all layers at once

### Analysis Tools
- **Buffer** - Create buffer zones
- **Spatial Join** - Combine layers
- **Statistics** - Get layer information

---

## SUPPORTED DATA FORMATS

### Vector Formats
| Format | Extension | Support |
|--------|-----------|---------|
| Shapefile | `.shp` | [OK] Full |
| GeoJSON | `.geojson` | [OK] Full |
| GeoPackage | `.gpkg` | [OK] Full |
| GML | `.gml` | [OK] Read |

### Raster Formats
| Format | Extension | Support |
|--------|-----------|---------|
| GeoTIFF | `.tif`, `.tiff` | [OK] Full |
| DEM | `.dem` | [OK] Full |
| PNG/GeoTIFF | `.png.tif` | [OK] Full |

---

## WORKFLOW EXAMPLES

### Example 1: Viewing Spatial Data
```
1. Launch: python app.py
2. Click "Open Layer"
3. Select a shapefile or GeoTIFF
4. Click "Fit All" to center
5. Explore using Zoom, Pan, Select tools
6. Click on features to see attributes (right panel)
```

### Example 2: Erosion Analysis
```
1. Load DEM raster
2. Load soil type shapefile
3. Load vegetation cover raster
4. Run analysis: Tools → Analyze → Erosion
5. View results on map
6. Export as GeoTIFF or PDF report
```

### Example 3: Buffer Analysis
```
1. Load river shapefile
2. Select layer
3. Click "Buffer"
4. Enter buffer distance (e.g., 100 meters)
5. View buffer zones on map
6. Export results
```

---

## SAMPLE DATA

Generate sample GIS data for testing:

```bash
python create_sample_data.py
```

Creates in `sample_data/` directory:
- `cities.shp` - Point features (cities)
- `regions.shp` - Polygon features (regions)
- `dem.tif` - Elevation raster
- `slope.tif` - Slope raster

---

## PYTHON DEPENDENCIES

All included in `requirements.txt`:

```
# Core GIS Libraries
geopandas>=0.13.0
rasterio>=1.3.0
shapely>=2.0.0
pyproj>=3.6.0

# Visualization
matplotlib>=3.7.0
folium>=0.14.0

# Data Processing
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0

# API & Database
fastapi>=0.103.0
sqlalchemy>=2.0.0
```

**Install all dependencies:**
```bash
pip install -r requirements.txt
```

---

## 💾 File Structure

```
TerraSim/
├── app.py              # Main application launcher
├── gis_app.py          # Full GIS application (1000+ lines)
├── gui.py              # Pipeline GUI (deprecated)
├── create_sample_data.py  # Sample data generator
│
├── backend/
│   ├── main.py         # FastAPI server
│   └── services/
│       └── pipeline.py # USPED erosion model
│
├── requirements.txt    # Python dependencies
└── sample_data/        # Sample GIS files
    ├── cities.shp
    ├── regions.shp
    ├── dem.tif
    └── slope.tif
```

---

## ADVANCED FEATURES

### Programmatic Access
```python
from gis_app import TerraSim_GIS, Layer

# Create app instance
app = TerraSim_GIS()

# Add layers programmatically
layer = Layer("my_layer", "path/to/file.shp", "vector")
app.layers["my_layer"] = layer

# Refresh map
app.refresh_map()
```

### Custom Analysis
```python
import geopandas as gpd

# Load a layer
gdf = gpd.read_file("data.shp")

# Perform analysis
gdf['buffer'] = gdf.geometry.buffer(100)

# Save results
gdf.to_file("output.shp")
```

---

## TROUBLESHOOTING

### Layer Won't Load
- Check file format is supported (.shp, .tif, .geojson)
- Verify file path is correct
- Ensure GDAL/rasterio libraries installed

### Map Not Displaying
- Ensure at least one layer is loaded
- Click "Fit All" to auto-center view
- Check layer visibility (toggle in left panel)

### Slow Performance
- Limit number of visible layers
- Use simplified geometry for large datasets
- Consider splitting large files

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

---

## 📖 Additional Resources

- **QGIS Documentation**: https://docs.qgis.org
- **GeoPandas Guide**: https://geopandas.org
- **Rasterio Docs**: https://rasterio.readthedocs.io

---

## 📄 License & Attribution

**TerraSim GIS** - Research-driven geospatial analysis platform  
Built with: GeoPandas, Rasterio, Matplotlib, tkinter

---

## 🎓 Academic Applications

- Soil erosion modeling (USPED)
- Land-use change analysis
- Environmental impact assessment
- Terrain analysis and DEM processing
- Hydrological modeling
- Natural hazard mapping

---

## STATUS

- [OK] Vector layer support
- [OK] Raster/DEM support
- [OK] Interactive map interface
- [OK] Basic GIS tools
- [OK] Attribute viewing
- [OK] Layer management
- [OK] Export capabilities
- [IN-PROGRESS] Advanced analysis (in progress)
- [IN-PROGRESS] 3D visualization (planned)
- [IN-PROGRESS] Network analysis (planned)

---

**Version**: 2.1.0 | **Python**: 3.8+ | **Status**: Production Ready | **Updated**: January 2026
