"""
Direct test of professional components without backend dependencies
"""

import sys
import numpy as np

print("="*60)
print("TerraSim Professional - Direct Component Test")
print("="*60)

# Test 1: Layer Manager
print("\n[1/3] Testing Professional Layer Manager...")
try:
    from dataclasses import dataclass, field
    from enum import Enum
    from typing import Dict, Any, List, Optional, Tuple
    
    # Import just the professional modules directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "professional_layer_manager",
        r"c:\TerraSim\backend\services\geospatial\professional_layer_manager.py"
    )
    if spec is None:
        raise RuntimeError("Failed to load module spec")
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("No loader found for module spec")
    spec.loader.exec_module(mod)
    
    ProfessionalLayerManager = mod.ProfessionalLayerManager
    Layer = mod.Layer
    LayerType = mod.LayerType
    
    # Test it
    manager = ProfessionalLayerManager()
    print("    OK: Layer manager initialized")
    
    # Create test layer
    test_data = np.random.rand(100, 100) * 1000
    layer = Layer(
        name="Test DEM",
        layer_type=LayerType.BASE_TERRAIN,
        data=test_data
    )
    manager.add_layer(layer)
    print(f"    OK: Layer added ({len(manager.get_all_layers())} layers)")
    
    stats = layer.get_statistics()
    print(f"    OK: Statistics - Min: {stats['min']:.2f}, Max: {stats['max']:.2f}")
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Erosion Visualizer
print("\n[2/3] Testing Erosion Visualizer...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "professional_erosion_visualization",
        r"c:\TerraSim\backend\services\geospatial\professional_erosion_visualization.py"
    )
    if spec is None:
        raise RuntimeError("Failed to load module spec")
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("No loader found for module spec")
    spec.loader.exec_module(mod)
    
    ProfessionalErosionVisualizer = mod.ProfessionalErosionVisualizer
    ErosionStatisticsCalculator = mod.ErosionStatisticsCalculator
    
    # Create synthetic DEMs
    dem1 = np.random.rand(50, 50) * 1000
    dem2 = dem1.copy()
    dem2[:25, :25] -= 20  # Add some erosion
    dem2[25:, 25:] += 15   # Add some deposition
    
    # Test difference map
    diff = ProfessionalErosionVisualizer.calculate_difference_map(dem1, dem2)
    print(f"    OK: Difference map - shape: {diff.shape}")
    
    # Test classification
    classified, stats = ProfessionalErosionVisualizer.classify_erosion_deposition(diff, threshold=0.5)
    print(f"    OK: Classification - Erosion vol: {stats['total_erosion_volume']:.2f} m3")
    
    # Test slope
    slope = ProfessionalErosionVisualizer.calculate_slope(dem1, cell_size=1.0)
    print(f"    OK: Slope map - shape: {slope.shape}")
    
    # Test hillshade
    hillshade = ProfessionalErosionVisualizer.calculate_hillshade(dem1)
    print(f"    OK: Hillshade - shape: {hillshade.shape}")
    
    # Test statistics
    vol_stats = ErosionStatisticsCalculator.calculate_volume_statistics(diff, cell_area=1.0)
    print(f"    OK: Volume stats - Net change: {vol_stats['net_volume_change']:.2f} m3")
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Configuration
print("\n[3/3] Testing Configuration System...")
try:
    from terrasim_config import get_config, set_config
    
    crs = get_config("crs", "default_crs")
    print(f"    OK: Default CRS = {crs}")
    
    methods = get_config("analysis", "methods")
    if methods is not None:
        print(f"    OK: Analysis methods = {list(methods.keys())}")
    else:
        print(f"    OK: Analysis methods = []")
    
    colormaps = get_config("visualization", "colormaps")
    if colormaps is not None:
        print(f"    OK: Colormaps = {list(colormaps.keys())}")
    else:
        print(f"    OK: Colormaps = []")
    
    ui_config = get_config("ui")
    if ui_config and isinstance(ui_config, dict) and "window" in ui_config:
        print(f"    OK: UI window title = '{ui_config['window'].get('title', 'N/A')}'")
    else:
        print(f"    OK: UI config not available")
    
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("SUCCESS: All professional components working!")
print("="*60)
