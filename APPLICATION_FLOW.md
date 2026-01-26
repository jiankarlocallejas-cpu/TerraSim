# TerraSim - Complete Application Flow

**Comprehensive documentation of user flows, system logic, and technical computation**

---

## 1️⃣ USER FLOW (Front-End Perspective)

**"What does the user do?"**

```
START
  ↓
┌─────────────────────────────────────┐
│  USER OPENS TERRASIM                │
│  (Desktop or Mobile App)            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  HOME SCREEN APPEARS                │
│  • App description                  │
│  • [Start Simulation] button         │
│  • Recent projects (if any)         │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  USER NAVIGATES TO SETUP            │
│  Simulation Setup Page              │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  USER PROVIDES INPUTS               │
│                                     │
│  A. Manual Parameters:              │
│     • R (rainfall erosivity)        │
│     • K (soil erodibility)          │
│     • C (cover management)          │
│     • P (support practices)         │
│     • m, n (exponents)              │
│     • ε (deposition rate)           │
│     • Δt (time step)                │
│                                     │
│  B. Upload Spatial Data:            │
│     • DEM (GeoTIFF raster)          │
│     • Optional CSV/JSON data        │
│       - Rainfall distribution       │
│       - Soil properties             │
│       - Land cover classification   │
│                                     │
│  C. Specify Output Options:         │
│     • Resolution                    │
│     • Time period                   │
│     • Output format                 │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  USER CLICKS [RUN SIMULATION]       │
│  • Data validation begins           │
│  • Processing indicator appears     │
│  • Estimated time displayed         │
└────────────┬────────────────────────┘
             ↓
        [ COMPUTATION ]
        (See System Flow)
             ↓
┌─────────────────────────────────────┐
│  RESULTS SCREEN APPEARS             │
│                                     │
│  A. Numerical Outputs:              │
│     • Mean erosion rate (t/ha/yr)   │
│     • Peak erosion (max cell)       │
│     • Total volume (m³)             │
│     • Erosion/deposition ratio      │
│                                     │
│  B. Map Screen:                     │
│     • Erosion risk heatmap          │
│     • Risk classification overlay   │
│     • Color legend                  │
│     • Statistics summary            │
│                                     │
│  C. Comparison (if available):      │
│     • RUSLE validation              │
│     • Previous scenarios            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  USER CAN:                          │
│                                     │
│  • View Detailed Results            │
│    - Per-cell erosion values        │
│    - Spatial distribution           │
│    - Risk area breakdown            │
│                                     │
│  • Generate Report                  │
│    - PDF with maps                  │
│    - Summary statistics             │
│    - Recommendations                │
│                                     │
│  • Export Results                   │
│    - As GeoTIFF (raster)            │
│    - As Shapefile (vector)          │
│    - As CSV (tabular)               │
│    - As JSON (structured)           │
│                                     │
│  • Refine Scenario                  │
│    - Modify parameters              │
│    - Change input data              │
│    - Re-run simulation              │
│                                     │
│  • Save Project                     │
│    - For later comparison           │
│    - For sharing with team          │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  USER EXITS OR RUNS NEW SCENARIO    │
│  • Back to home                     │
│  • Start another simulation         │
│  • Compare results                  │
└────────────┬────────────────────────┘
             ↓
           END
```

---

## 2️⃣ SYSTEM FLOW (Application Logic)

**"What happens inside the app?"**

```
┌──────────────────────────┐
│    APP INITIALIZATION    │
│  • Load configuration    │
│  • Initialize UI         │
│  • Load dependencies     │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  NAVIGATION INITIALIZED  │
│  • Route setup           │
│  • Event listeners       │
│  • State management      │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  HOME SCREEN RENDERED    │
│  • Display welcome page  │
│  • Show available tools  │
│  • Display project list  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  USER INPUT COLLECTION   │
│                          │
│  Form Handlers:          │
│  • Parameter inputs      │
│  • Validation rules      │
│  • Default values        │
│  • Help text display     │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  FILE UPLOAD HANDLER     │
│                          │
│  • File type check       │
│  • Size validation       │
│  • Encoding detection    │
│  • Preview generation    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  DATA VALIDATION         │
│                          │
│  • Required fields       │
│  • Format compliance     │
│  • Range checking        │
│  • Consistency checks    │
│  • Error reporting       │
└────────────┬─────────────┘
             ↓
        [APPROVED?]
        /          \
      YES          NO → [BACK TO INPUT]
       ↓
┌──────────────────────────┐
│  DATA PARSING            │
│                          │
│  • GeoTIFF reader        │
│  • CSV/JSON parser       │
│  • Array conversion      │
│  • Projection handling   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  PROCESSING INITIATED    │
│  • Create job ID         │
│  • Start timer           │
│  • Emit progress event   │
│  • Show spinner          │
└────────────┬─────────────┘
             ↓
        [ COMPUTATION ]
        (See Data Flow)
             ↓
┌──────────────────────────┐
│  RESULT AGGREGATION      │
│  • Combine all outputs   │
│  • Calculate statistics  │
│  • Format for display    │
│  • Generate visualizations
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  RESULTS RENDERING       │
│  • Display maps          │
│  • Show statistics       │
│  • Enable export         │
│  • Store in cache        │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  USER INTERACTIONS       │
│  • Zoom/pan map          │
│  • View statistics       │
│  • Generate reports      │
│  • Export data           │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│  CLEANUP & EXIT          │
│  • Save session          │
│  • Clear temp files      │
│  • Release resources     │
└──────────────────────────┘
```

---

## 3️⃣ DATA & COMPUTATION FLOW (Technical Core)

### 📖 USPED-Based SoilModel Main Equation

The core computational model for erosion simulation:

$$
z_{t+\Delta t}(x, y)=z_{t}(x, y)-\frac{\Delta t}{\rho_{b}}\left[\frac{\partial}{\partial x}(T \cos \alpha)+\frac{\partial}{\partial y}(T \sin \alpha)+\epsilon \frac{\partial}{\partial z}(T \sin \beta)\right]
$$

Where transport capacity is:

$$
T=f\left(R, K, C, P, A^{m},(\sin \beta)^{n}, Q(I, S)\right)
$$

**Parameters:**
- $z$ = terrain elevation (m)
- $t$ = time (years)
- $\Delta t$ = time step
- $\rho_b$ = bulk soil density (kg/m³)
- $\alpha$ = aspect (flow direction)
- $\beta$ = slope angle
- $\epsilon$ = deposition coefficient
- $T$ = transport capacity (soil flux)
- $R$ = rainfall erosivity (MJ·mm/ha/h/yr)
- $K$ = soil erodibility (0-1)
- $C$ = cover management factor (0-1)
- $P$ = support practice factor (0-1)
- $A$ = upslope area (m²)
- $m, n$ = exponents (default: 1.6, 1.3)
- $Q(I,S)$ = runoff as function of infiltration and saturation

**Based on:** Mitasova & Hofierka (1993) and Mitasova et al. (1996)

---

**"What happens inside the computation engine?"**

### 🔹 Phase A: Input Layer

```
INPUT DATA
├── DEM Raster
│   ├── Format: GeoTIFF
│   ├── Bands: 1 (elevation)
│   ├── Data type: Float32
│   ├── CRS: WGS84/UTM
│   └── Resolution: User-specified
│
├── Parameter Files (Optional)
│   ├── Rainfall CSV
│   │   ├── Format: timestamp, value
│   │   ├── Units: mm/year
│   │   └── Spatial: gridded or point
│   ├── Soil Properties JSON
│   │   ├── K-factor per soil type
│   │   ├── Texture classification
│   │   └── Spatial: polygon map
│   └── Land Cover CSV
│       ├── C-factor per class
│       ├── P-factor per class
│       └── Spatial: raster or vector
│
└── Manual Parameters
    ├── R: Rainfall erosivity (0-1000)
    ├── K: Soil erodibility (0-1)
    ├── C: Cover management (0-1)
    ├── P: Support practices (0-1)
    ├── m, n: Exponents (0.5-3.0)
    ├── ε: Deposition rate (0-1)
    └── Δt: Time step (days/years)
```

### 🔹 Phase B: Data Pre-Processing

```
PRE-PROCESSING PIPELINE
         ↓
    [1] Read DEM
         • Open GeoTIFF file
         • Extract metadata (CRS, transform)
         • Load array to memory
         • Check for no-data values
         ↓
    [2] Raster to Array
         • Convert to NumPy array
         • Handle data types
         • Normalize values
         • Create coordinate grids
         ↓
    [3] Spatial Resolution Validation
         • Check pixel size
         • Verify square cells
         • Ensure consistency
         • Flag if too coarse/fine
         ↓
    [4] Data Quality Check
         • Detect missing (NaN) values
         • Count void areas
         • Check elevation range
         • Flag anomalies (slopes >90°)
         ↓
    [5] Projection Handling
         • Verify CRS matches
         • Reproject if needed
         • Create coordinate arrays
         • Compute cell areas
         ↓
    [6] Parameter Loading
         • Read K, C, P from files
         • Interpolate to DEM grid
         • Handle missing values
         • Apply default values
         ↓
    PREPROCESSED DATA READY
```

### 🔹 Phase C: Terrain Analysis

```
TERRAIN DERIVATIVES COMPUTATION
         ↓
    [1] Slope Calculation (β)
         • Method: Maximum gradient
         • Formula: tan(β) = √[(∂z/∂x)² + (∂z/∂y)²]
         • Smoothing: Optional Laplacian filter
         • Output: β in degrees or radians
         ↓
    [2] Aspect Calculation (α)
         • Method: Gradient direction
         • Formula: α = atan2(∂z/∂y, ∂z/∂x)
         • Output: α in degrees (0-360)
         ↓
    [3] Flow Direction (D8)
         • Method: Steepest descent
         • 8 directions per cell
         • Break ties: Southwest preference
         • Output: Direction grid
         ↓
    [4] Flow Accumulation (A)
         • Method: TopologicalSort + accumulation
         • Weight: Cell area (square meters)
         • Output: Upslope area in m²
         ↓
    [5] Trigonometric Pre-computation
         • Compute: sin(β), cos(β)
         • Compute: sin(α), cos(α)
         • Cache for later use
         ↓
    TERRAIN READY FOR USPED
```

### 🔹 Phase D: Transport Capacity (T)

```
TRANSPORT CAPACITY COMPUTATION
T = K · C · P · R · Q · (A^m) · (sin β)^n
         ↓
    [1] Collect Parameters
         • K: Soil erodibility
         • C: Cover management
         • P: Support practices
         • R: Rainfall erosivity
         • m, n: Exponents
         ↓
    [2] Compute Runoff (Q)
         • Method: SCS Curve Number
         • Input: Rainfall, soil, cover
         • Output: Runoff depth
         • Formula: Q = (R - Ia)² / (R - Ia + S)
         ↓
    [3] Compute Transport Capacity
         • For each cell:
           T = K · C · P · R · Q · (A^m) · (sin β)^n
         • Handle division by zero
         • Apply maximum threshold
         • Store in raster array
         ↓
    TRANSPORT CAPACITY READY
```

### 🔹 Phase E: USPED Erosion-Deposition Equation

```
USPED MODEL EXECUTION
Equation: ∂z/∂t = -∇·T + ε·∇²z
         ↓
    [1] Initialize Solution
         • Create output array (copy of DEM)
         • Set boundary conditions
         • Initialize divergence array
         ↓
    [2] Compute Divergence (∇·T)
         • For each cell:
           div_T = (T_E - T_W + T_N - T_S) / (2·dx)
         • Handle boundaries (slope condition)
         • Store in divergence grid
         ↓
    [3] Compute Laplacian (∇²z)
         • For each cell:
           lap_z = (z_E + z_W + z_N + z_S - 4·z_center) / dx²
         • Handle boundaries
         • Apply deposition coefficient ε
         ↓
    [4] Finite Difference Update
         • For each cell:
           z_new = z_old - Δt·(div_T - ε·lap_z)
         • Apply stability check (CFL condition)
         • Store new elevation
         ↓
    [5] Erosion/Deposition Map
         • erosion[i,j] = z_old[i,j] - z_new[i,j]
         • Positive = erosion
         • Negative = deposition
         ↓
    USPED COMPUTATION COMPLETE
```

### 🔹 Phase F: Output Aggregation

```
RESULT AGGREGATION
         ↓
    [1] Spatial Statistics
         • Mean erosion: mean(erosion[erosion > 0])
         • Max erosion: max(erosion)
         • Min erosion: min(erosion[erosion > 0])
         • Std deviation: std(erosion[erosion > 0])
         ↓
    [2] Volume Calculation
         • Cell area: dx × dy (m²)
         • Erosion volume: sum(erosion[erosion > 0]) × area
         • Deposition volume: sum(erosion[erosion < 0]) × area
         • Total: |erosion_vol - deposition_vol|
         ↓
    [3] Risk Classification
         • Class 1 (Very Low): erosion < 1st quartile
         • Class 2 (Low): 1st-2nd quartile
         • Class 3 (Moderate): 2nd-3rd quartile
         • Class 4 (High): 3rd-4th quartile
         • Class 5 (Very High): > 4th quartile (critical)
         ↓
    [4] Pixel Count Analysis
         • % of cells in each risk class
         • Area in each class (hectares)
         • Hotspots (connected high-risk cells)
         ↓
    [5] Erosion Index
         • Combine: spatial extent × intensity
         • Formula: Index = (high_risk_area / total_area) × mean_erosion
         • Range: 0-100 (0=stable, 100=critical)
         ↓
    AGGREGATED RESULTS READY
```

### 🔹 Phase G: Visualization Layer

```
VISUALIZATION & REPORTING
         ↓
    [1] Generate Heatmap
         • Create color ramp (blue → red)
         • Map erosion values to colors
         • Include legend with ranges
         • Overlay on base map
         ↓
    [2] Tabular Results
         • Summary statistics table
         • Risk class distribution
         • Per-zone statistics (if zones provided)
         • Comparison with RUSLE (if available)
         ↓
    [3] Report Generation
         • Title page
         • Executive summary
         • Methodology section
         • Results with maps
         • Risk recommendations
         • Appendices (parameters, equations)
         ↓
    [4] Export Options
         ├── Raster Exports
         │   ├── erosion.tif (erosion map)
         │   ├── risk_class.tif (5-tier classification)
         │   └── susceptibility.tif (index 0-100)
         ├── Vector Exports
         │   ├── hotspots.shp (high-risk polygons)
         │   └── zones.shp (risk zones)
         └── Tabular Exports
             ├── results.csv (per-cell data)
             ├── summary.json (statistics)
             └── report.pdf (full report)
         ↓
    VISUALIZATION COMPLETE
```

---

## 4️⃣ FULL ARCHITECTURAL FLOW (Complete Diagram)

```
╔════════════════════════════════════════════════════════════════════════════╗
║                        TERRASIM COMPLETE FLOW                             ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIER 1: PRESENTATION (UI)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HOME SCREEN          INPUT FORM            RESULTS SCREEN               │
│  ┌──────────────┐    ┌─────────────┐      ┌──────────────────┐          │
│  │ Welcome      │    │ Parameters  │      │ Heatmap          │          │
│  │ Start Button │───→│ File Upload │─────→│ Statistics       │          │
│  │ Projects     │    │ Validation  │      │ Export Options   │          │
│  └──────────────┘    └─────────────┘      └──────────────────┘          │
│                                                                             │
│  Layer 1 (Tkinter GUI / Web Interface)                                    │
│  • User Input Collection                                                  │
│  • File handling                                                          │
│  • Result visualization                                                   │
│  • Report generation                                                      │
│                                                                             │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIER 2: APPLICATION LOGIC (CONTROLLER)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input Validation  Data Parsing  Job Orchestration  Result Handling      │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  ┌──────────────┐    │
│  │ Type check   │  │ GeoTIFF  │  │ Queue job     │  │ Aggregate    │    │
│  │ Range check  │  │ CSV/JSON │  │ Run pipeline  │  │ Statistics   │    │
│  │ Format valid │  │ Array    │  │ Monitor       │  │ Classify     │    │
│  │ Constraints  │  │ convert  │  │ progress      │  │ Format       │    │
│  └──────────────┘  └──────────┘  └───────────────┘  └──────────────┘    │
│                                                                             │
│  Layer 2 (Application Logic - Python)                                     │
│  • Validation rules                                                       │
│  • Data transformation                                                    │
│  • Process coordination                                                   │
│  • Error handling                                                         │
│                                                                             │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                TIER 3: DATA PROCESSING (COMPUTATION ENGINE)                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ Preprocessing  │  │ Terrain      │  │ Transport    │  │ USPED      │  │
│ │                │  │ Analysis     │  │ Capacity (T) │  │ Model      │  │
│ │ • Read DEM     │  │              │  │              │  │            │  │
│ │ • Array conv   │→ │ • Slope (β)  │→ │ • Compute T  │→ │ • ∂z/∂t   │  │
│ │ • Validate     │  │ • Aspect (α) │  │ • Q runoff   │  │ • Erosion  │  │
│ │ • Load params  │  │ • Flow dir   │  │ • A^m term   │  │ • Deposi   │  │
│ │                │  │ • Accumul.   │  │              │  │            │  │
│ │ GeoTIFF        │  │              │  │              │  │ Finite     │  │
│ │ NumPy/SciPy    │  │ NumPy        │  │ NumPy/SciPy  │  │ Difference │  │
│ └────────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                                                                             │
│  Layer 3 (Scientific Computation - NumPy, SciPy, GeoPandas, Rasterio)     │
│  • Raster I/O                                                             │
│  • Array operations                                                       │
│  • Spatial analysis                                                       │
│  • Mathematical modeling                                                  │
│                                                                             │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│              TIER 4: STORAGE & PERSISTENCE (DATA LAYER)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ Input Files      │  │ Output Files     │  │ Cache/Session    │       │
│  │                  │  │                  │  │                  │       │
│  │ • dem.tif        │  │ • erosion.tif    │  │ • temp data      │       │
│  │ • params.csv     │  │ • risk_class.tif │  │ • session state  │       │
│  │ • rainfall.json  │  │ • results.csv    │  │ • user pref      │       │
│  │ • soil.gpkg      │  │ • report.pdf     │  │ • history        │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                             │
│  Layer 4 (File System & Database - SQLite/PostgreSQL)                    │
│  • GIS file formats                                                       │
│  • Metadata storage                                                       │
│  • Job history                                                            │
│  • Result caching                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5 WHAT YOUR PANEL CARES ABOUT (THESIS CHECKLIST)

### [OK] CLEAR SEPARATION OF CONCERNS

```
UI Layer (Tkinter)
    ↓
Logic Layer (Python)
    ↓
Computation Layer (NumPy/SciPy)
    ↓
Data Layer (Files/Database)

Benefits:
• Easy to modify UI without affecting computation
• Computation can be tested independently
• Scalability: Can move computation to server
• Maintainability: Each layer has clear responsibility
```

### [OK] CORRECT SCIENTIFIC WORKFLOW

```
✓ DEM input → Terrain derivatives → Transport capacity → USPED equations
✓ Follows published research (Mitasova & Hofierka, 1993)
✓ Includes RUSLE validation component
✓ Proper error handling for edge cases (flat areas, pits)
✓ Uses established numerical methods (finite differences)
```

### [OK] JUSTIFICATION FOR TECHNOLOGY CHOICES

```
Python (Scientific Computing):
  • NumPy: Fast array operations (C backend)
  • SciPy: Advanced mathematical functions
  • GeoPandas: Vector data handling
  • Rasterio: GeoTIFF I/O

Tkinter (Desktop GUI):
  • Cross-platform (Windows/Mac/Linux)
  • Built-in to Python
  • Lightweight (no external dependencies)
  • Suitable for research applications

Why NOT web-only:
  • Desktop offers better performance for large rasters
  • No internet required (field work)
  • Can work offline
  • Better file handling (local paths)
```

### [OK] DATA VALIDATION & PREPROCESSING

```
Input Validation:
  ✓ File format checking
  ✓ Raster size limits
  ✓ CRS compatibility
  ✓ Parameter range verification
  ✓ Missing data detection

Preprocessing:
  ✓ Array normalization
  ✓ Projection handling
  ✓ Resolution checking
  ✓ Interpolation where needed
  ✓ No-data value handling
```

### [OK] REPRODUCIBILITY OF RESULTS

```
Tracking:
  ✓ Store all input parameters with results
  ✓ Log computation steps (debug mode)
  ✓ Version of equations used
  ✓ Timestamp of analysis
  ✓ System information (Python version, packages)

Export:
  ✓ Results as GeoTIFF (preserves geospatial metadata)
  ✓ Parameters as JSON (machine-readable)
  ✓ Report as PDF (human-readable)
  ✓ Raw data as CSV (for external analysis)

Verification:
  ✓ Can re-run with same parameters
  ✓ Can compare with RUSLE
  ✓ Can validate against published datasets
```

### [OK] ERROR HANDLING & RECOVERY

```
Input Phase:
  → Invalid file → Show user error → Suggest correction
  → Out of range → Highlight parameter → Show valid range

Computation Phase:
  → No-data detected → Fill with interpolation
  → Division by zero → Apply safe default
  → NaN values → Flag and exclude from statistics

Output Phase:
  → Export fails → Show error → Offer alternative format
  → Report generation fails → Save raw data anyway
```

---

## DATA WORKFLOW SUMMARY

| Phase | Component | Method | Output |
|-------|-----------|--------|--------|
| **Input** | UI | Tkinter forms | Parameters + files |
| **Validation** | Validation module | Type/range checks | Approved inputs |
| **Parsing** | Data parser | GeoTIFF/CSV readers | NumPy arrays |
| **Terrain** | Terrain engine | Gradient computation | Slope, aspect, flow |
| **USPED** | Erosion model | Finite differences | Erosion/deposition |
| **Stats** | Aggregation | Statistical functions | Summary metrics |
| **Viz** | Visualization | Matplotlib/Folium | Maps + tables |
| **Export** | File writer | GeoTIFF/CSV writers | Results files |

---

## 🎓 FOR YOUR THESIS

### Document Structure

```
Chapter 1: Introduction
  → Problem: Soil erosion modeling needs
  → Solution: TerraSim application

Chapter 2: Literature Review
  → USPED model background
  → Previous implementations
  → Software tools available

Chapter 3: Methodology
  [USE THIS FLOW DOCUMENT]
  → System architecture
  → Data flow diagram
  → Computational methods
  → Validation approach

Chapter 4: Implementation
  → Technology stack
  → Software design
  → Algorithm details
  → Code examples

Chapter 5: Results
  → Test case 1 (synthetic data)
  → Test case 2 (real DEM)
  → Comparison with RUSLE
  → Performance metrics

Chapter 6: Discussion & Conclusions
```

### Key Points to Highlight

1. **Separation of UI and Computation** - Shows good software engineering
2. **Scientific Rigor** - Equations properly implemented
3. **User-Centered Design** - Clear flow from input to results
4. **Validation Strategy** - RUSLE comparison, sensitivity analysis
5. **Reproducibility** - All parameters logged, results exportable

---

**This flow document is complete and production-ready for your thesis.**

Use it to:
- Explain system architecture to committee
- Justify design decisions
- Document methodology
- Show data flow
- Demonstrate scientific rigor
