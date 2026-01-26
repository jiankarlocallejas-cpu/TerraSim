# TerraSim - Python-Only Erosion Modeling System

**Desktop application for soil erosion analysis using USPED model**

---

## Quick Start (One Command)

### Windows
```powershell
.\run.ps1
```

### Windows (Command Prompt)
```cmd
run.bat
```

### macOS/Linux
```bash
python app.py
```

Application starts with **Backend API** + **Tkinter GUI** automatically.

---

## What is TerraSim?

TerraSim is a 7-stage pipeline system for soil erosion analysis:

1. **Input Collection** - Gather spatial and meteorological data
2. **File Upload & Validation** - Upload DEM, auxiliary rasters, vector data
3. **Data Validation** - Verify data integrity and completeness
4. **Preprocessing** - Normalize projections, fill gaps, prepare data
5. **Terrain Analysis** - Compute slopes, flow accumulation, hillshade
6. **Erosion Computation** - Execute USPED model (with RUSLE validation)
7. **Result Aggregation** - Generate statistics, classifications, visualizations

---

## CORE EQUATION (USPED-Based SoilModel)

**Terrain Evolution:**
$$z_{t+\Delta t}(x, y)=z_{t}(x, y)-\frac{\Delta t}{\rho_{b}}\left[\frac{\partial}{\partial x}(T \cos \alpha)+\frac{\partial}{\partial y}(T \sin \alpha)+\epsilon \frac{\partial}{\partial z}(T \sin \beta)\right]$$

**Transport Capacity:**
$$T=f(R, K, C, P, A^{m}, (\sin \beta)^{n}, Q(I, S))$$

This represents sediment flux driven by water runoff, influenced by rainfall ($R$), soil ($K$), vegetation ($C$), management ($P$), topography ($A$, $\beta$), and infiltration dynamics ($Q$).

**Based on:** Mitasova & Hofierka (1993) USPED model

---

## �🛠️ Tech Stack

**100% Python - No Node.js Required**

- **Backend**: FastAPI (async REST API)
- **GUI**: Tkinter (native Python GUI)
- **Spatial**: GeoPandas, Rasterio, Shapely
- **Science**: NumPy, SciPy, Scikit-learn
- **Database**: SQLAlchemy + SQLite/PostgreSQL

---

## 🔄 Application Flow

**Complete User & System Flow Documentation**

TerraSim follows a comprehensive multi-tier architecture:

```
USER FLOW → SYSTEM FLOW → DATA FLOW → VISUALIZATION
  (UI)        (Logic)      (Compute)     (Results)
```

### User Flow (What the user does)
1. Open TerraSim application
2. Provide parameters (R, K, C, P, m, n, ε, Δt)
3. Upload spatial data (DEM, rainfall, soil data)
4. Click "Run Simulation"
5. View results (erosion map, statistics, risk classification)
6. Export or compare scenarios

### System Flow (What happens inside)
1. **Input Collection** - Parameter and file gathering
2. **Data Validation** - Type checking, format verification
3. **File Parsing** - GeoTIFF/CSV reading and array conversion
4. **Terrain Analysis** - Slope, aspect, flow computation
5. **USPED Model** - Erosion-deposition calculation
6. **Result Aggregation** - Statistics and classification
7. **Visualization** - Heatmap and report generation

### Data Flow (Technical pipeline)
```
DEM Input → Terrain Derivatives → Transport Capacity
    ↓            ↓                      ↓
  Raster      (β, α, A)            T = K·C·P·R·Q·(A^m)·sin(β)^n
                                         ↓
                                  Finite Difference Method
                                    ∂z/∂t = -∇·T + ε·∇²z
                                         ↓
                                    Erosion/Deposition
                                         ↓
                                    Result Export
```

**See [APPLICATION_FLOW.md](APPLICATION_FLOW.md) for complete flow diagrams and technical details.**

---

## GUI FEATURES

### Pipeline Tab
- Visual 7-stage interface
- Progress tracking (0-100%)
- Activity log with timestamps
- Start/Pause/Reset controls

### Results Tab
- Summary statistics
- Detailed results display
- Export: GeoTIFF, CSV, PDF, JSON

### Jobs Tab
- Project management
- Job status tracking
- Delete/archive jobs

### Settings Tab
- API configuration
- Connection status
- Documentation links

---

## PROJECT STRUCTURE

```
TerraSim/
├── app.py                  # Main entry point (backend + GUI)
├── gui.py                  # Tkinter GUI application
├── run.ps1                 # Windows PowerShell launcher
├── run.bat                 # Windows batch launcher
├── requirements.txt        # Python dependencies
│
├── backend/
│   ├── main.py            # FastAPI server
│   ├── services/
│   │   ├── pipeline.py    # Pipeline orchestrator
│   │   └── erosion_model.py  # USPED equations
│   ├── api/v1/
│   │   └── endpoints/
│   │       └── pipeline.py    # REST endpoints
│   ├── models/            # Database models
│   └── schemas/           # Data schemas
│
└── docs/
    ├── README.md          # This file
    ├── QUICKSTART.md      # Quick reference
    ├── TROUBLESHOOTING.md # Problem solving
    └── DATABASE_SETUP_SUMMARY.md
```

---

## 📦 Installation

### Automatic (Recommended)

**Windows (PowerShell):**
```powershell
.\run.ps1
```
This automatically:
- Creates virtual environment (if needed)
- Installs dependencies
- Starts backend API
- Launches GUI

### Manual Setup

1. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run application:**
```bash
python app.py
```

---

## RUNNING THE APPLICATION

### Default (Backend + GUI)
```bash
python app.py
```

### Backend Only (API Testing)
```bash
python backend/main.py
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### GUI Only (Requires separate backend)
```bash
python gui.py
```

---

## API ENDPOINTS

### Pipeline Control
- `POST /api/v1/pipeline/collect-input` - Stage 1
- `POST /api/v1/pipeline/upload-dem` - Stage 2
- `POST /api/v1/pipeline/validate-data` - Stage 3
- `POST /api/v1/pipeline/preprocess` - Stage 4
- `POST /api/v1/pipeline/analyze-terrain` - Stage 5
- `POST /api/v1/pipeline/execute-erosion-model` - Stage 6
- `POST /api/v1/pipeline/aggregate-results` - Stage 7
- `POST /api/v1/pipeline/execute` - Full pipeline
- `GET /api/v1/pipeline/status/{job_id}` - Check status

### Jobs
- `GET /api/v1/jobs` - List projects
- `GET /api/v1/jobs/{id}` - Job details
- `DELETE /api/v1/jobs/{id}` - Delete job

---

## CONFIGURATION

Edit `app.py` or use GUI Settings tab:

```python
self.API_URL = "http://localhost:8000/api/v1"  # Backend URL
```

Backend config in `backend/core/config.py`:
```python
DATABASE_URL = "sqlite:///./terrasim.db"
UPLOAD_DIR = "./uploads"
TEMP_DIR = "./temp"
```

---

## 📥 Building Standalone Executable

Create a single-file Windows executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py -n TerraSim
```

Result: `dist/TerraSim.exe`

---

## TROUBLESHOOTING

### GUI won't start
```bash
# Check Python version
python --version  # Must be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run with verbose output
python app.py
```

### Backend won't connect
```bash
# Check if port 8000 is free
netstat -ano | findstr :8000

# Test connection
curl http://localhost:8000/docs
```

### Data loading issues
- Check file formats (GeoTIFF, Shapefile)
- Verify coordinate systems
- Check disk space in `UPLOAD_DIR`

See `TROUBLESHOOTING.md` for more help.

---

## DOCUMENTATION

- [QUICKSTART.md](QUICKSTART.md) - Fast setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem solving
- [DATABASE_SETUP_SUMMARY.md](DATABASE_SETUP_SUMMARY.md) - Database reference

---

## DEVELOPMENT

### Project Structure
```
backend/services/pipeline.py (420 lines)
  ├── ProcessingPipeline class
  ├── PipelineStage enum
  ├── _stage_*() methods
  └── PipelineManager

backend/api/v1/endpoints/pipeline.py (530 lines)
  ├── /collect-input
  ├── /upload-dem
  ├── /validate-data
  ├── /preprocess
  ├── /analyze-terrain
  ├── /execute-erosion-model
  ├── /aggregate-results
  └── Background tasks

gui.py (800 lines)
  ├── Pipeline Tab
  ├── Results Tab
  ├── Jobs Tab
  └── Settings Tab
```

### Modifying the GUI
Edit `gui.py`:
- Add new tabs: Create `setup_*_tab()` method
- Modify layout: Edit tab setup methods
- Change styles: Modify ttk theme

### Adding API Endpoints
Edit `backend/api/v1/endpoints/pipeline.py`:
```python
@router.post("/your-endpoint")
async def your_endpoint():
    # Your code here
    return {"status": "success"}
```

---

## SYSTEM REQUIREMENTS

- **OS**: Windows 7+, macOS 10.14+, Linux (most distributions)
- **Python**: 3.8+
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk**: 500MB for application + data
- **Network**: For API communication

---

## KEY FEATURES

[OK] 7-stage pipeline interface
[OK] Real-time progress tracking
[OK] Erosion model computation
[OK] Multiple export formats
[OK] Job management
[OK] No Node.js required
[OK] Python-only codebase
[OK] Cross-platform (Windows/Mac/Linux)
[OK] Standalone executable build
[OK] REST API for automation

---

## LICENSE

This project is licensed under the MIT License.

---

## 📞 Support

- **Issues**: Check `TROUBLESHOOTING.md`
- **Database Help**: See `DATABASE_SETUP_SUMMARY.md`
- **API Docs**: Run backend and visit `http://localhost:8000/docs`

---

**Version**: 2.1.0 | **Status**: Python-Only | **Last Updated**: January 2026
