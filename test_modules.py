#!/usr/bin/env python3
"""
TerraSim Modules - Quick Start & Testing Guide

Run this file to verify module availability:
    python test_modules.py
"""

import sys
from pathlib import Path

def test_module_imports():
    """Test that all modules are importable"""
    print("Testing Module Imports...\n")
    
    modules_to_test = [
        ("backend.modules.terrain", "TerrainModule"),
        ("backend.modules.analysis", "AnalysisModule"),
        ("backend.modules.data", "DataModule"),
        ("backend.modules.export", "ExportModule"),
        ("backend.modules.visualization", "VisualizationModule"),
        ("backend.modules.manager", "ModuleManager"),
    ]
    
    all_passed = True
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}")
            print(f"  └─ {class_name} available")
        except Exception as e:
            print(f"✗ {module_name}")
            print(f"  └─ Error: {e}")
            all_passed = False
    
    return all_passed


def test_module_manager():
    """Test ModuleManager functionality"""
    print("\n\nTesting ModuleManager...\n")
    
    try:
        from backend.modules.manager import ModuleManager
        
        manager = ModuleManager()
        print("✓ ModuleManager initialized successfully")
        
        # Test module availability
        print("\nAvailable modules:")
        print(f"  • terrain:       {manager.terrain}")
        print(f"  • analysis:      {manager.analysis}")
        print(f"  • data:          {manager.data}")
        print(f"  • export:        {manager.export}")
        print(f"  • visualization: {manager.visualization}")
        
        return True
    except Exception as e:
        print(f"✗ ModuleManager test failed: {e}")
        return False


def test_individual_modules():
    """Test individual module functionality"""
    print("\n\nTesting Individual Modules...\n")
    
    try:
        import numpy as np
        
        # Create test data
        test_dem = np.random.rand(10, 10) * 100
        
        # Test TerrainModule
        from backend.modules.terrain import TerrainModule
        terrain = TerrainModule()
        slope = terrain.analyzer.compute_slope(test_dem)
        print(f"✓ TerrainModule - computed slope shape: {slope.shape}")
        
        # Test AnalysisModule
        from backend.modules.analysis import AnalysisModule
        analysis = AnalysisModule()
        flow = analysis.simulator.compute_flow_accumulation(test_dem)
        print(f"✓ AnalysisModule - computed flow shape: {flow.shape}")
        
        # Test VisualizationModule
        from backend.modules.visualization import VisualizationModule
        viz = VisualizationModule()
        normalized = viz.heatmap.normalize_data(test_dem)
        print(f"✓ VisualizationModule - normalized data shape: {normalized.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Individual module test failed: {e}")
        return False


def show_usage_examples():
    """Display usage examples"""
    print("\n\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70 + "\n")
    
    examples = {
        "Complete Pipeline": """
from backend.modules.manager import ModuleManager

manager = ModuleManager()
results = manager.run_complete_analysis('dem.tif', analysis_steps=100)
""",
        "Individual Modules": """
from backend.modules.terrain import TerrainModule
from backend.modules.analysis import AnalysisModule

terrain = TerrainModule()
analysis = AnalysisModule()
""",
        "Custom Configuration": """
from backend.modules.terrain import TerrainConfig, TerrainModule
from backend.modules.analysis import AnalysisConfig, AnalysisModule

terrain_config = TerrainConfig(dem_resolution=30.0, cache_enabled=True)
analysis_config = AnalysisConfig(time_steps=100, rainfall_intensity=50.0)

terrain = TerrainModule(terrain_config)
analysis = AnalysisModule(analysis_config)
""",
        "API Usage": """
# POST /api/v2/terrain/analyze
# Input: multipart/form-data with DEM file
# Output: { status, metadata, analysis }

# POST /api/v2/analysis/erosion
# Input: multipart/form-data with DEM file + analysis_steps parameter
# Output: { status, erosion_results, visualization }

# POST /api/v2/export/results
# Input: multipart/form-data with analysis data + format parameter
# Output: Downloaded file (JSON, CSV, GeoTIFF, or HTML)
""",
    }
    
    for title, code in examples.items():
        print(f"📌 {title}:")
        print(code)
        print()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TERRASIM MODULES - TEST & VERIFICATION")
    print("="*70 + "\n")
    
    # Run tests
    imports_ok = test_module_imports()
    manager_ok = test_module_manager()
    modules_ok = test_individual_modules()
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    status = {
        "Module Imports": "✓ PASSED" if imports_ok else "✗ FAILED",
        "Module Manager": "✓ PASSED" if manager_ok else "✗ FAILED",
        "Individual Modules": "✓ PASSED" if modules_ok else "✗ FAILED",
    }
    
    for test_name, result in status.items():
        print(f"{test_name:.<50} {result}")
    
    all_passed = all([imports_ok, manager_ok, modules_ok])
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Ready for integration!")
    else:
        print("✗ SOME TESTS FAILED - Review errors above")
    print("="*70 + "\n")
    
    # Show examples
    show_usage_examples()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
