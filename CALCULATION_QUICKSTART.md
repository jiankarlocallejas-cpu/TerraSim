# TerraSim Calculation Engine - Quick Start

## Launch Application

### Windows
```batch
run.bat
```

### macOS/Linux
```bash
python app.py
```

---

## Use Calculation Engine Programmatically

### Example 1: Quick Erosion Assessment

```python
from backend.services.simulation_engine import (
    get_simulation_engine,
    SimulationParameters
)
import numpy as np

# Load or create DEM
dem = np.random.rand(100, 100) * 1000  # 100x100 grid, 0-1000m elevation

# Get engine
engine = get_simulation_engine()

# Run quick calculation
result = engine.run_single_simulation(dem)

# Access results
print(f"Mean erosion: {result.mean_erosion:.4f} m/year")
print(f"Peak erosion: {result.peak_erosion:.4f} m/year")
print(f"Volume lost: {result.total_volume_loss:.2e} m³")
```

### Example 2: Long-term Simulation

```python
# Configure for 100-year simulation
params = SimulationParameters(
    rainfall_erosivity=320.0,  # Your region's rainfall data
    soil_erodibility=0.38,
    cover_factor=0.25,
    practice_factor=0.6,
    num_timesteps=100,  # 100 timesteps
    time_step_days=365.0  # 1 year per timestep
)

# Run time-series simulation
result = engine.run_time_series_simulation(dem, params)

# Track evolution over time
for i, elevation in enumerate(result.elevation_evolution):
    change = elevation - dem
    print(f"Year {i}: Mean change = {np.mean(np.abs(change)):.4f} m")
```

### Example 3: Identify Key Parameters

```python
# Run sensitivity analysis
sensitivity = engine.run_sensitivity_analysis(dem)

# Find most important parameter
for param, indices in sensitivity.items():
    print(f"{param}: index = {indices['index']:.4f}")
```

### Example 4: Uncertainty Quantification

```python
# Run uncertainty analysis with 1000 Monte Carlo runs
result = engine.run_uncertainty_analysis(
    dem,
    num_samples=1000,
    variation_std=0.1
)

print(f"Erosion: {result.mean_erosion:.4f} m/year")
print(f"95% confidence: [{result.confidence_interval_95[0]:.4f}, "
      f"{result.confidence_interval_95[1]:.4f}]")
```

### Example 5: Compare Scenarios

```python
# Define different management scenarios
scenarios = {
    'baseline': SimulationParameters(),
    'with_cover': SimulationParameters(cover_factor=0.7),
    'with_management': SimulationParameters(practice_factor=0.8),
}

# Run all scenarios
for name, params in scenarios.items():
    result = engine.run_single_simulation(dem, params)
    print(f"{name}: {result.mean_erosion:.4f} m/year")
```

---

## Integration with GIS Interface

### Via GUI
1. Launch application with `run.bat` or `python app.py`
2. Load DEM layer in GIS interface
3. Click **Analysis** menu → **Run Erosion Model**
4. Configure parameters (R, K, C, P values)
5. Select simulation mode
6. View results overlaid on map with risk colors

### Via API
```bash
# Run erosion model via REST API
curl -X POST http://localhost:8000/api/v1/execute-erosion-model \
  -H "Content-Type: application/json" \
  -d '{
    "dem_id": 1,
    "parameters": {
      "rainfall_erosivity": 300.0,
      "soil_erodibility": 0.35
    },
    "mode": "single_run"
  }'
```

---

## Parameter Guidelines

### Rainfall Erosivity (R)
- **Definition**: Seasonal rainfall energy and intensity
- **Units**: MJ·mm/ha/hr/yr
- **Range**: 50-500 depending on climate
- **Examples**:
  - Arid regions: 50-100
  - Temperate regions: 200-400
  - Tropical regions: 300-600

### Soil Erodibility (K)
- **Definition**: Soil resistance to erosion
- **Range**: 0-1 (higher = more erodible)
- **Examples**:
  - Clay soils: 0.15-0.25
  - Silt loam: 0.35-0.45
  - Sandy soils: 0.45-0.60

### Cover Factor (C)
- **Definition**: Vegetation protection
- **Range**: 0-1 (0 = full cover, 1 = bare soil)
- **Examples**:
  - Dense forest: 0.01-0.05
  - Grassland: 0.1-0.3
  - Cropland: 0.2-0.5
  - Bare soil: 0.8-1.0

### Practice Factor (P)
- **Definition**: Conservation practices
- **Range**: 0-1 (0 = best practices, 1 = no practices)
- **Examples**:
  - Terracing: 0.1-0.3
  - Contour plowing: 0.3-0.6
  - Strip cropping: 0.4-0.8
  - No conservation: 1.0

---

## Output Files

### Save Results
```python
import numpy as np
import rasterio
from rasterio.transform import Affine

# Save as NumPy binary
np.save('erosion_rate.npy', result.erosion_rate)
np.save('elevation_change.npy', result.elevation_change)

# Save as GeoTIFF
transform = Affine.identity()
with rasterio.open(
    'erosion_risk.tif',
    'w',
    driver='GTiff',
    height=result.risk_classification.shape[0],
    width=result.risk_classification.shape[1],
    count=1,
    dtype=rasterio.uint8,
    transform=transform,
) as dst:
    dst.write(result.risk_classification, 1)

# Export as JSON
import json
with open('results.json', 'w') as f:
    json.dump(result.to_dict(), f, indent=2)
```

---

## Troubleshooting

### Engine Won't Initialize
```python
# Check dependencies
from backend.services.simulation_engine import get_simulation_engine
engine = get_simulation_engine()
print("Engine ready")
```

### Memory Issues with Large DEMs
- Use smaller DEM resolution (resample)
- Run TIME_SERIES with fewer timesteps
- Use SINGLE_RUN instead of UNCERTAINTY
- Reduce Monte Carlo samples

### Unexpected Results
- Check parameter ranges (see guidelines above)
- Verify DEM units (should be meters)
- Run SENSITIVITY analysis to identify key parameters
- Compare with RUSLE results

---

## Performance Tips

| Task | Mode | DEM Size | Runtime |
|------|------|----------|---------|
| Quick test | SINGLE_RUN | 100×100 | 0.1 sec |
| Assessment | SINGLE_RUN | 1000×1000 | 1-5 sec |
| Prediction | TIME_SERIES (10 steps) | 500×500 | 5-10 sec |
| Analysis | SENSITIVITY | 500×500 | 30-60 sec |
| Risk assessment | UNCERTAINTY (100 runs) | 500×500 | 2-5 min |

### Optimization
- Start with coarser resolution (100-200m pixel size)
- Use fewer timesteps initially
- Reduce Monte Carlo samples for testing
- Batch process with `show_progress=False`

---

## Next Steps

1. **Read Full Documentation**: [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md)
2. **Explore GIS Interface**: [GIS_README.md](GIS_README.md)
3. **Check Applications**: [APPLICATION_FLOW.md](APPLICATION_FLOW.md)
4. **Troubleshoot Issues**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Citation

When using TerraSim results in research, cite:

```bibtex
@software{terrasim2026,
  title={TerraSim: Python-Based Erosion Modeling System},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/terrasim}
}

@article{mitasova1993usped,
  title={Interpolation by regularized spline with tension: II. Application to terrain modeling and surface geometry analysis},
  author={Mitasova, Helena and Hofierka, Jaroslav},
  journal={Mathematical Geology},
  volume={25},
  number={6},
  pages={657--669},
  year={1993}
}
```

---

**Ready to begin erosion modeling? Launch with: `run.bat`**
