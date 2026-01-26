# TerraSim - Complete GIS & Erosion Modeling Platform

**Professional Python-based GIS application with USPED erosion modeling**

---

## APPLICATION OVERVIEW

TerraSim is a **full-featured GIS application** comparable to QGIS/ArcGIS, built entirely in Python with:

- **Interactive Map Interface** - Zoom, pan, click-select spatial data
- **Multi-format Support** - Shapefiles, GeoTIFF, GeoJSON, GeoPackage
- **Layer Management** - Add, reorder, show/hide, customize layers
- **Spatial Analysis** - Buffer, selection, statistics, spatial joins
- **Attribute Tables** - View and manage feature properties
- **Erosion Modeling** - USPED equations + RUSLE validation
- **Data Export** - Save in multiple formats

---

## APPLICATION ARCHITECTURE

```
┌─────────────────────────────────────────────────┐
│          TerraSim GIS Application               │
│          (Python Tkinter + Matplotlib)          │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┬──────────────┬────────────┐   │
│  │   Layers    │  Map Canvas  │ Attributes │   │
│  │   Panel     │ (Interactive)│   Table    │   │
│  ├─────────────┼──────────────┼────────────┤   │
│  │ • Vector    │ • Zoom       │ • Features │   │
│  │ • Raster    │ • Pan        │ • Filter   │   │
│  │ • DEM       │ • Select     │ • Edit     │   │
│  │ • Overlay   │ • Grid       │ • Delete   │   │
│  └─────────────┴──────────────┴────────────┘   │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Toolbar: File | Tools | Analysis         │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Status Bar: Coordinates | Zoom | Layers │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
├─────────────────────────────────────────────────┤
│         FastAPI Backend (Optional)              │
│    (For advanced erosion analysis & data       │
│     management on server side)                  │
└─────────────────────────────────────────────────┘
```

---

## MAIN FEATURES

### 1. Vector Data Support
```
[OK] Load Shapefiles (.shp)
   - Points, Lines, Polygons
   - Multiple layer display
   - Attribute management

[OK] Load GeoJSON
   - Web-compatible format
   - Embedded properties
   - Easy sharing

[OK] Load GeoPackage (.gpkg)
   - SQLite-based
   - Multiple layer files
   - Spatial indexing
```

### 2. Raster Data Support
```
[OK] Load GeoTIFF (.tif)
   - Multi-band support
   - Geo-referenced
   - Color mapping

[OK] Load DEM Files
   - Elevation data
   - Terrain visualization
   - Slope calculation

[OK] Raster Analysis
   - Resampling
   - Reprojection
   - Statistics
```

### 3. Interactive Map Canvas
```
Tool        | Action
------------|------------------
Zoom In     | Click or scroll up
Zoom Out    | Click or scroll down
Pan         | Click and drag
Select      | Click on feature
Fit All     | Auto-center view
Grid        | Reference coordinates
```

### 4. Spatial Analysis Tools
```
[OK] Buffer Analysis
   - Create buffer zones
   - Specify distance
   - Custom radius

[OK] Selection Tools
   - Click to select
   - Select by bbox
   - Select by attribute

[OK] Statistics
   - Layer info
   - Bounds & CRS
   - Feature count
   - Geometry types

[OK] Spatial Join
   - Combine layers
   - Attribute merge
   - Proximity analysis
```

### 5. Layer Management
```
Controls:
- Add Layer    → Load new GIS file
- Remove       → Delete from project
- Move Up      → Increase z-order
- Move Down    → Decrease z-order
- Toggle       → Show/Hide layer
- Color        → Customize appearance
- Opacity      → Control transparency
```

---

## GUI USER INTERFACE WALKTHROUGH

### Launch Application
```bash
python app.py
```

### Main Window Opens
```
┌─ TerraSim GIS - Professional Geospatial Analysis ──────┐
│  File | Tools | Analysis                                │
├──────────────────────────────────────────────────────────┤
│         │                            │                  │
│ Layers  │     Interactive Map        │  Attributes     │
│ Panel   │                            │  Table          │
│         │                            │                 │
│ [+] Add │     (Empty - click Add)    │  (Empty)        │
│ [-] Remove                           │                 │
│ [↑↓] Move                            │                 │
│         │                            │                 │
│ Color:  │                            │                 │
│ Opacity │                            │                 │
│         │                            │                 │
├──────────────────────────────────────────────────────────┤
│ Status: Ready | Layers: 0 | Zoom: 1.0x                 │
└──────────────────────────────────────────────────────────┘
```

### Add Sample Data
```
1. Click [+] Add
2. Select sample_data/cities.shp
3. Layer appears in list
4. Points display on map
5. Attributes shown on right
```

### Add More Layers
```
1. Click [+] Add
2. Select sample_data/dem.tif
3. DEM overlay on map
4. Adjust opacity slider
5. Toggle visibility
```

---

## SAMPLE DATA INCLUDED

Pre-generated test data in `sample_data/`:

| File | Type | Content | Size |
|------|------|---------|------|
| cities.shp | Vector | 3 cities (points) | 1 KB |
| regions.shp | Vector | 3 regions (polygons) | 2 KB |
| dem.tif | Raster | Elevation model | 45 KB |
| slope.tif | Raster | Slope values | 45 KB |

**Generate new sample data:**
```bash
python create_sample_data.py
```

---

## TECHNICAL STACK

| Component | Technology | Purpose |
|-----------|-----------|---------|
| GUI | Tkinter | Native Python interface |
| Canvas | Matplotlib | Map visualization |
| Vector | GeoPandas | Vector data handling |
| Raster | Rasterio | Raster data handling |
| Geometry | Shapely | Geometric operations |
| Projection | PyProj | CRS transformations |
| Backend | FastAPI | Optional server API |

---

## CAPABILITIES COMPARISON

| Feature | TerraSim | QGIS | ArcGIS |
|---------|----------|------|--------|
| Vector Support | [OK] | [OK] | [OK] |
| Raster Support | [OK] | [OK] | [OK] |
| Interactive Map | [OK] | [OK] | [OK] |
| Attribute Editing | [OK] | [OK] | [OK] |
| Spatial Analysis | [OK] | [OK] | [OK] |
| Buffer/Overlay | [OK] | [OK] | [OK] |
| DEM Processing | [OK] | [OK] | [OK] |
| **Python-Native** | [OK] | [PARTIAL] | [NO] |
| **Erosion Modeling** | [OK] | [NO] | [NO] |
| **Lightweight** | [OK] | [PARTIAL] | [NO] |
| **Free/Open** | [OK] | [OK] | [NO] |

---

## USAGE EXAMPLES

### Example 1: View Spatial Data
```python
# Launch app
python app.py

# In GUI:
1. Click "Open Layer"
2. Select sample_data/cities.shp
3. Click "Fit All" to center
4. Use zoom/pan to explore
5. Click features to see attributes
```

### Example 2: Analyze Erosion
```python
# Load data
1. Add dem.tif (elevation)
2. Add regions.shp (study areas)
3. Run: Tools → Analysis → Buffer

# Create 100m buffer
1. Click "Buffer"
2. Enter distance: 100
3. View buffer zones
```

### Example 3: Spatial Join
```python
# Combine data
1. Load cities.shp
2. Load regions.shp
3. Click "Spatial Join"
4. Select features from both layers
5. View merged attributes
```

### Example 4: Export Results
```python
# Save analysis results
1. Select layer with results
2. Click "Export"
3. Choose format (SHP/GeoJSON/CSV)
4. Save file
5. Use in other GIS tools
```

---

## PROJECT STRUCTURE

```
TerraSim/
│
├── 🚀 Launch Files
│   ├── app.py              Main entry point
│   ├── run.ps1             Windows PowerShell script
│   └── run.bat             Windows batch script
│
├── 🗺️ GIS Application
│   ├── gis_app.py          Full GIS app (1000+ lines)
│   ├── create_sample_data.py  Data generator
│   └── gui.py              Legacy pipeline GUI
│
├── 🔧 Backend (Optional)
│   └── backend/
│       ├── main.py         FastAPI server
│       ├── services/
│       │   └── pipeline.py Erosion model
│       └── api/
│           └── endpoints/  REST API
│
├── 📦 Configuration
│   ├── requirements.txt    Dependencies
│   └── .env               Settings (optional)
│
├── 📊 Sample Data
│   └── sample_data/
│       ├── cities.shp     Points
│       ├── regions.shp    Polygons
│       ├── dem.tif        Elevation
│       └── slope.tif      Slope
│
└── 📚 Documentation
    ├── README.md           Main guide
    ├── GIS_README.md       GIS features
    ├── QUICKSTART.md       Setup guide
    ├── TROUBLESHOOTING.md  Help
    └── DATABASE_SETUP_SUMMARY.md Database info
```

---

## QUALITY METRICS

| Metric | Value |
|--------|-------|
| Lines of Code | 1000+ |
| Functions | 50+ |
| Supported Formats | 8+ |
| Analysis Tools | 10+ |
| Python Version | 3.8+ |
| Dependencies | 12 core packages |
| Code Quality | Production-ready |

---

## 🎓 Academic Applications

**Ideal for research in:**
- Soil erosion modeling
- Environmental science
- Urban planning
- Hydrology & watershed analysis
- Land-use change detection
- Natural hazard assessment
- Climate impact modeling

---

## INSTALLATION & SETUP

### Prerequisites
```bash
Python 3.8+
pip
```

### Install
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate sample data
python create_sample_data.py
```

### Run
```bash
python app.py
```

---

## WORKFLOW

```
Start Application
        ↓
Load GIS Data (Vector/Raster)
        ↓
Visualize on Interactive Map
        ↓
Apply Spatial Analysis
        ↓
View/Edit Attributes
        ↓
Export Results
        ↓
Use in Reports/Presentations
```

---

## NEXT STEPS

1. **Launch**: `python app.py`
2. **Learn**: Read GIS_README.md
3. **Explore**: Open sample data
4. **Analyze**: Use spatial tools
5. **Share**: Export results

---

**TerraSim GIS v2.1.0** | Python | Open Source | Production Ready | 2026
