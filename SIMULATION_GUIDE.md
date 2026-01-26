# TerraSim Calculation & Simulation Engine

## Overview

TerraSim now includes a complete calculation and simulation system for erosion modeling based on the USPED (Unit Stream Power-based Erosion Deposition) framework with RUSLE validation.

---

## Core Equation (USPED Model)

### Terrain Evolution
```
z(t+Δt) = z(t) - (Δt/ρ_b) × [∂(T cos α)/∂x + ∂(T sin α)/∂y + ε ∂(T sin β)/∂z]
```

### Transport Capacity (Sediment Flux)
```
T = f(R, K, C, P, A^m, (sin β)^n, Q(I,S))
```

### Parameters
- **R** = Rainfall erosivity (MJ·mm/ha/hr/yr) - Default: 300.0
- **K** = Soil erodibility (0-1) - Default: 0.35
- **C** = Vegetation cover factor (0-1) - Default: 0.3
- **P** = Management practice factor (0-1) - Default: 0.5
- **A** = Upslope contributing area (m²)
- **β** = Local slope angle
- **m** = Area exponent - Default: 0.6
- **n** = Slope exponent - Default: 1.3
- **ρ_b** = Bulk density (kg/m³) - Default: 1300.0

---

## Simulation Modes

### 1. SINGLE_RUN Mode
**Purpose**: One-time erosion calculation from a DEM

**Use Cases**:
- Quick erosion assessment
- Initial terrain analysis
- Rapid scenario testing

**Output**:
- Elevation change (m)
- Erosion rate (m/year)
- Deposition rate (m/year)
- Risk classification (5-tier)
- Mean and peak erosion statistics

**Example**:
```python
from backend.services.simulation_engine import get_simulation_engine
import numpy as np

engine = get_simulation_engine()
dem = np.random.rand(100, 100) * 1000  # 100x100m DEM, 0-1000m elevation

result = engine.run_single_simulation(dem)
print(f"Mean erosion: {result.mean_erosion:.4f} m/year")
print(f"Peak erosion: {result.peak_erosion:.4f} m/year")
```

---

### 2. TIME_SERIES Mode
**Purpose**: Multi-timestep simulation showing temporal evolution

**Use Cases**:
- Long-term erosion prediction
- Landform evolution analysis
- Landscape stability assessment

**Features**:
- Tracks elevation changes over multiple timesteps
- Records erosion rates at each step
- Captures progressive terrain modification
- Suitable for decade-to-century scale simulations

**Parameters**:
- `num_timesteps`: Number of simulation steps (default: 10)
- `time_step_days`: Duration of each step (default: 1.0 days)

**Output**:
- Elevation evolution (list of DEMs)
- Erosion evolution (list of erosion rate arrays)
- Final elevation change
- Total volume loss

**Example**:
```python
from backend.services.simulation_engine import (
    get_simulation_engine, 
    SimulationParameters
)

engine = get_simulation_engine()

# Custom parameters for 100-year simulation
params = SimulationParameters(
    rainfall_erosivity=350.0,  # High erosivity region
    soil_erodibility=0.4,
    num_timesteps=100,  # 100 years
    time_step_days=365.0  # 1 year per step
)

result = engine.run_time_series_simulation(dem, params)
print(f"Total elevation change: {result.mean_erosion:.2f} m")
print(f"Volume lost: {result.total_volume_loss:.2e} m³")
```

---

### 3. SENSITIVITY Mode
**Purpose**: Parameter sensitivity analysis to identify key drivers

**Use Cases**:
- Identify dominant erosion factors
- Parameter importance ranking
- Uncertainty source identification
- Model calibration guidance

**Features**:
- Systematically perturbs each parameter (±20% default)
- Calculates sensitivity indices
- Compares baseline vs. perturbed scenarios
- Quantifies parameter influence on erosion

**Output**:
- Sensitivity index for each parameter
- High/low erosion predictions
- Baseline comparison values

**Example**:
```python
sensitivity = engine.run_sensitivity_analysis(
    dem, 
    vary_factor=0.2  # ±20% variation
)

for param, results in sensitivity.items():
    print(f"{param}: sensitivity index = {results['index']:.4f}")
```

---

### 4. UNCERTAINTY Mode
**Purpose**: Monte Carlo uncertainty quantification

**Use Cases**:
- Confidence interval estimation
- Risk assessment
- Decision-making under uncertainty
- Result robustness evaluation

**Features**:
- Random parameter variation (normal distribution)
- Multiple independent runs
- Statistical aggregation
- Confidence interval calculation

**Parameters**:
- `num_samples`: Number of Monte Carlo runs (default: 100)
- `variation_std`: Parameter variation std dev (default: 0.1 = ±10%)

**Output**:
- Mean erosion with uncertainty
- 95% confidence intervals
- Uncertainty range (min-max)
- Distribution statistics

**Example**:
```python
uncertainty_result = engine.run_uncertainty_analysis(
    dem,
    num_samples=1000,  # 1000 Monte Carlo runs
    variation_std=0.15  # ±15% parameter variation
)

print(f"Erosion: {uncertainty_result.mean_erosion:.4f} m/year")
print(f"95% CI: [{uncertainty_result.confidence_interval_95[0]:.4f}, "
      f"{uncertainty_result.confidence_interval_95[1]:.4f}]")
```

---

### 5. SCENARIO Mode
**Purpose**: Compare multiple erosion scenarios

**Use Cases**:
- Land management strategy comparison
- Climate change impact assessment
- Conservation practice evaluation
- Best management practice ranking

**Features**:
- Define multiple parameter sets
- Run parallel simulations
- Compare results side-by-side
- Identify optimal scenarios

**Example**:
```python
# Define scenarios
scenarios = {
    'baseline': SimulationParameters(),
    'high_cover': SimulationParameters(cover_factor=0.7),
    'management': SimulationParameters(practice_factor=0.8),
    'worst_case': SimulationParameters(
        rainfall_erosivity=450.0,
        soil_erodibility=0.5
    )
}

results = {}
for name, params in scenarios.items():
    results[name] = engine.run_single_simulation(dem, params)

# Compare
for name, result in results.items():
    print(f"{name}: {result.mean_erosion:.4f} m/year")
```

---

## Risk Classification System

TerraSim uses a 5-tier erosion risk classification:

| Tier | Erosion Rate | Risk Level | Color | Management |
|------|--------------|-----------|-------|------------|
| 1 | < 0.001 m/yr | Very Low | Green | Minimal intervention |
| 2 | 0.001-0.005 m/yr | Low | Yellow | Monitor |
| 3 | 0.005-0.01 m/yr | Moderate | Orange | Active management |
| 4 | 0.01-0.05 m/yr | High | Red | Urgent intervention |
| 5 | > 0.05 m/yr | Very High | Dark Red | Emergency response |

---

## Simulation Workflow

### Step 1: Data Preparation
```python
import numpy as np
import geopandas as gpd
from backend.services.simulation_engine import get_simulation_engine

# Load DEM
dem = np.loadtxt('dem.asc')  # Digital Elevation Model

# Verify DEM properties
print(f"DEM shape: {dem.shape}")
print(f"Elevation range: {dem.min():.2f} - {dem.max():.2f} m")
```

### Step 2: Initialize Engine
```python
engine = get_simulation_engine()
```

### Step 3: Configure Parameters
```python
from backend.services.simulation_engine import SimulationParameters

params = SimulationParameters(
    rainfall_erosivity=320.0,    # Regional rainfall data
    soil_erodibility=0.38,       # Soil survey data
    cover_factor=0.25,           # Vegetation map
    practice_factor=0.6,         # Land management
    num_timesteps=50,
    time_step_days=365.0
)
```

### Step 4: Run Simulation
```python
result = engine.run_time_series_simulation(dem, params)
```

### Step 5: Analysis & Visualization
```python
# Extract results
erosion = result.erosion_rate
elevation_change = result.elevation_change

# Save to disk
np.save('erosion_map.npy', erosion)
np.save('elevation_change.npy', elevation_change)

# Export statistics
print(result.to_dict())
```

---

## Performance Characteristics

### Computational Requirements

| Mode | DEM Size | Runtime | Memory |
|------|----------|---------|--------|
| SINGLE_RUN | 1000×1000 | 1-5 sec | 50-100 MB |
| TIME_SERIES (10 steps) | 1000×1000 | 10-50 sec | 100-200 MB |
| SENSITIVITY | 1000×1000 | 1-2 min | 100 MB |
| UNCERTAINTY (100 samples) | 1000×1000 | 2-5 min | 150 MB |

### Optimization Tips
- Use coarser DEM resolution for initial testing
- Reduce `num_timesteps` for quick iterations
- Use `show_progress=False` for batch processing
- Run uncertainty with fewer samples first, then increase

---

## Integration with GIS Interface

The simulation engine integrates seamlessly with the TerraSim GIS interface:

### Via GUI
1. Load DEM in GIS interface
2. Click "Analysis" → "Run Erosion Model"
3. Configure parameters in dialog
4. Select simulation mode
5. Results display on map with risk classification colors

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/execute-erosion-model \
  -H "Content-Type: application/json" \
  -d '{
    "dem_id": 123,
    "parameters": {
      "rainfall_erosivity": 300.0,
      "soil_erodibility": 0.35
    },
    "simulation_mode": "single_run"
  }'
```

### Via Python Script
```python
from backend.services.simulation_engine import get_simulation_engine
import geopandas as gpd

# Load GIS data
gdf = gpd.read_file('study_area.shp')
dem = ... # Extract DEM from raster

# Run analysis
engine = get_simulation_engine()
result = engine.run_time_series_simulation(dem)

# Save results as GeoTIFF
from rasterio.transform import Affine
import rasterio

# ... save result.erosion_rate to GeoTIFF
```

---

## Validation & Uncertainty

### RUSLE Comparison
Each USPED result is compared against RUSLE predictions:
```
RUSLE: A = R × K × L × S × C × P

A = Annual soil loss (tons/ha/year)
```

### Uncertainty Components
1. Parameter uncertainty (Monte Carlo)
2. Model structural uncertainty
3. Input data uncertainty
4. Boundary condition effects

### Confidence Intervals
95% confidence intervals provided for all estimates:
- Based on 1000+ Monte Carlo runs
- Assumes normal distribution
- Percentile method for robustness

---

## Output Formats

### Native Format (NumPy)
```python
result.erosion_rate  # 2D array
result.elevation_change  # 2D array
result.risk_classification  # 2D integer array (1-5)
```

### Export to File
```python
import numpy as np
np.save('erosion.npy', result.erosion_rate)

import rasterio
# ... export as GeoTIFF
```

### JSON Export
```python
import json
with open('results.json', 'w') as f:
    json.dump(result.to_dict(), f, indent=2)
```

---

## References

1. **USPED Model**
   - Mitasova, H., & Hofierka, J. (1993). "Interpolation by regularized spline with tension: II. Application to terrain modeling and surface geometry analysis." *Mathematical Geology*, 25(6), 657-669.

2. **RUSLE**
   - Renard, K. G., et al. (1997). "Predicting soil erosion by water: a guide to conservation planning with the Revised Universal Soil Loss Equation (RUSLE)." USDA Agricultural Handbook 703.

3. **Flow Accumulation**
   - O'Callaghan, J. F., & Mark, D. M. (1984). "The extraction of drainage networks from digital elevation data." *Computer Vision, Graphics, and Image Processing*, 28(3), 323-344.

---

## Support & Documentation

- [APPLICATION_FLOW.md](APPLICATION_FLOW.md) - Complete system architecture
- [GIS_README.md](GIS_README.md) - GIS interface guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues & solutions
- [API Endpoints](README.md#api-endpoints) - REST API documentation

---

**Updated**: January 26, 2026
**Version**: 1.0
**Status**: Production Ready
