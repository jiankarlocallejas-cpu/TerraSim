# World Machine-Style Visualization - Quick Reference

## Overview

Professional terrain visualization for your 3D simulation, designed to look and feel like World Machine - the industry-standard terrain generation software.

## Features

✅ **Natural Terrain Colors** - Realistic blue water → green grass → brown rock → white snow  
✅ **Erosion Heatmaps** - Red for erosion, Blue for deposition  
✅ **Advanced Hillshading** - Professional lighting with Sobel gradients  
✅ **Water Flow Visualization** - Shows accumulation and flow patterns  
✅ **Multiple Color Schemes** - Natural, Erosion Heat, Geological, Thermal, Heightmap  
✅ **Post-Processing Effects** - Contrast, saturation, brightness adjustment  
✅ **Animation Export** - Save simulations as GIF animations  
✅ **Frame-by-Frame Rendering** - Render individual or sequences of frames  

## Quick Start

### Render a Single Frame

```python
from backend.services.world_machine_style import WorldMachineVisualizer, WorldMachineColorScheme
import numpy as np
from PIL import Image

# Create visualizer
visualizer = WorldMachineVisualizer()

# Your DEM (Digital Elevation Model)
dem = np.array([[100, 105, 110], [102, 108, 115], [104, 112, 120]])

# Render with natural colors
frame = visualizer.render_simulation_frame(
    dem,
    timestep=0,
    total_timesteps=1,
    colorscheme=WorldMachineColorScheme.NATURAL,
    show_hillshade=True,
    show_flow=False
)

# Save to file
Image.fromarray(frame).save("terrain.png")
```

### Render Simulation Animation

```python
from backend.services.terrain_simulator import create_simulator_for_mode, SimulationMode
from backend.services.world_machine_style import SimulationAnimationRenderer, WorldMachineColorScheme

# Run simulation
simulator, params = create_simulator_for_mode(dem, SimulationMode.MEDIUM)
snapshots = simulator.run_simulation(params)

# Create animation
renderer = SimulationAnimationRenderer()
for i, snapshot in enumerate(snapshots):
    renderer.add_snapshot(
        snapshot.elevation,
        timestep=i,
        total_timesteps=len(snapshots),
        colorscheme=WorldMachineColorScheme.NATURAL
    )

# Save as GIF
renderer.save_animation("simulation.gif", duration_per_frame=200)
```

### Analyze Erosion/Deposition

```python
visualizer = WorldMachineVisualizer()

# Compare two DEMs
ero_dep = visualizer.create_erosion_deposition_map(current_dem, previous_dem)

print(f"Total erosion: {ero_dep['total_erosion']:.2f} m³")
print(f"Total deposition: {ero_dep['total_deposition']:.2f} m³")

# Visualize
Image.fromarray((ero_dep['colors'] * 255).astype(np.uint8)).save("erosion.png")
```

## Color Schemes

### NATURAL
Realistic terrain colors:
- **Blue**: Water (deep to shallow)
- **Golden**: Sandy beaches
- **Green**: Grassland
- **Gray-Brown**: Rocky foothills
- **White**: Snow peaks

### EROSION_HEAT
Shows erosion intensity:
- **Red**: High erosion areas
- **Blue**: Deposition areas
- **Green**: Transition zones

### GEOLOGICAL
Realistic geology colors with natural variation

### THERMAL
Temperature-style colors:
- **Blue**: Cool areas
- **Cyan**: Medium areas
- **Yellow/Red**: Hot areas

### HEIGHTMAP
Simple grayscale heightmap for technical use

## Advanced Usage

### Custom Lighting

```python
# Create hillshade with custom lighting
hillshade = visualizer.create_advanced_hillshade(
    dem,
    azimuth=315,      # Light direction (degrees)
    altitude=45,      # Light angle above horizon
    z_factor=2.0      # Vertical exaggeration
)
```

### Water Flow Visualization

```python
# Show where water flows and collects
flow_colors = visualizer.create_flow_visualization(dem)
```

### Post-Processing

```python
# Enhance visual quality
frame = visualizer.render_simulation_frame(dem, 0, 1, colorscheme)
enhanced = visualizer.apply_postprocessing(
    frame,
    dem,
    contrast=1.2,     # Increase contrast
    saturation=1.1,   # Increase color saturation
    brightness=1.0    # Adjust brightness
)
```

### Blend Visualizations

```python
# Combine two visualizations
blended = visualizer.blend_visualizations(
    base_colors,
    overlay_colors,
    strength=0.3  # 30% overlay strength
)
```

## File Locations

| File | Purpose |
|------|---------|
| `backend/services/world_machine_style.py` | Core visualization engine |
| `world_machine_visualization_examples.py` | 7 complete usage examples |

## API Reference

### WorldMachineVisualizer Class

**Key Methods:**
- `create_world_machine_colors(dem, colorscheme)` - Generate colors from DEM
- `create_advanced_hillshade(dem, azimuth, altitude, z_factor)` - Professional hillshade
- `create_flow_visualization(dem)` - Water flow accumulation
- `create_erosion_deposition_map(current, previous)` - Erosion/deposition analysis
- `render_simulation_frame(dem, timestep, total, colorscheme, show_hillshade, show_flow)` - Full frame render
- `apply_postprocessing(colors, dem, contrast, saturation, brightness)` - Visual enhancement
- `blend_visualizations(base, overlay, strength)` - Combine visualizations

### SimulationAnimationRenderer Class

**Key Methods:**
- `add_snapshot(dem, timestep, total_timesteps, colorscheme)` - Add frame to animation
- `save_animation(output_path, duration_per_frame)` - Export as GIF

## Running Examples

```bash
# Run all visualization examples
python world_machine_visualization_examples.py

# Outputs go to 'simulation_frames/' directory
```

### What Each Example Shows

1. **Example 1**: Single frame with natural coloring
2. **Example 2**: Erosion/deposition heatmap
3. **Example 3**: Full terrain evolution animation
4. **Example 4**: Hillshade with different lighting angles
5. **Example 5**: Water flow visualization
6. **Example 6**: Comparison of all color schemes
7. **Example 7**: Full simulation with statistics tracking

## Tips for Professional Output

### For Best Visual Quality
1. Use `colorscheme=WorldMachineColorScheme.NATURAL`
2. Enable hillshade: `show_hillshade=True`
3. Adjust z-factor based on terrain scale
4. Post-process with contrast=1.15, saturation=1.05

### For Erosion Analysis
1. Use `WorldMachineColorScheme.EROSION_HEAT` for comparison frames
2. Track `total_erosion` and `total_deposition` metrics
3. Use flow visualization to understand sediment pathways

### For Animation
1. Keep duration reasonable (100-300ms per frame)
2. Export at consistent resolution
3. Use consistent color scheme throughout
4. Include flow visualization for context

## Integration with Terrain Simulator

```python
from backend.services.terrain_simulator import create_simulator_for_mode, SimulationMode
from backend.services.world_machine_style import WorldMachineVisualizer

# Run simulation
simulator, params = create_simulator_for_mode(dem, SimulationMode.MEDIUM)
snapshots = simulator.run_simulation(params)

# Visualize results
visualizer = WorldMachineVisualizer()
for snapshot in snapshots:
    frame = visualizer.render_simulation_frame(
        snapshot.elevation,
        show_hillshade=True
    )
```

## Troubleshooting

**Q: Colors don't look right**  
A: Check the DEM value ranges. DEMs should be elevation in meters. Try different color schemes.

**Q: Animation is too fast/slow**  
A: Adjust `duration_per_frame` parameter (milliseconds per frame).

**Q: Hillshade looks flat**  
A: Increase `z_factor` in `create_advanced_hillshade()`.

**Q: Memory usage is high**  
A: Render frames individually instead of storing all in memory.

## Performance

| Operation | Time (256×256 DEM) |
|-----------|-------------------|
| Render frame | ~100ms |
| Save PNG | ~50ms |
| Full animation (50 frames) | ~10 seconds |
| Hillshade | ~20ms |
| Flow accumulation | ~100ms |

## What Makes It "World Machine Style"

1. **Natural Color Gradients** - Realistic hypsometric tints like WM
2. **Professional Hillshading** - High-quality lighting simulation
3. **Flow Visualization** - Shows sediment/water transport
4. **Multiple Presets** - Quick access to common visualizations
5. **Quality Post-Processing** - Enhances visual appeal
6. **Animation Support** - Animate terrain evolution over time

## See Also

- `backend/services/terrain_simulator.py` - Simulation engine
- `backend/services/moderngl_terrain.py` - OpenGL rendering (optional)
- `terrain_simulation_examples.py` - Simulator usage examples

---

**Version**: 1.0  
**Status**: Ready for Production  
**Last Updated**: January 28, 2026
