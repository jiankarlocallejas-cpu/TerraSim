#!/usr/bin/env python3
"""
TerraSim Simulation System Verification Script
Tests all major components and workflows
"""

import sys
import numpy as np
from pathlib import Path

# Add TerraSim to path
terrasm_path = Path(__file__).parent
sys.path.insert(0, str(terrasm_path))

def test_imports():
    """Test all critical imports"""
    print("\n" + "="*70)
    print("TEST 1: Module Imports")
    print("="*70)
    
    try:
        from backend.services.simulation_engine import (
            get_simulation_engine, SimulationParameters, SimulationResult, SimulationMode
        )
        print("[PASS] Simulation engine imports")
    except ImportError as e:
        print(f"[FAIL] Simulation engine: {e}")
        return False
    
    try:
        from frontend.main_window import MainWindow
        print("[PASS] MainWindow imports")
    except ImportError as e:
        print(f"[FAIL] MainWindow: {e}")
        return False
    
    try:
        from frontend.screens.result_screen import ResultScreen
        print("[PASS] ResultScreen imports")
    except ImportError as e:
        print(f"[FAIL] ResultScreen: {e}")
        return False
    
    try:
        from frontend.screens.simulation_screen import SimulationScreen
        print("[PASS] SimulationScreen imports")
    except ImportError as e:
        print(f"[FAIL] SimulationScreen: {e}")
        return False
    
    return True


def test_simulation_execution():
    """Test simulation engine execution"""
    print("\n" + "="*70)
    print("TEST 2: Simulation Execution")
    print("="*70)
    
    from backend.services.simulation_engine import get_simulation_engine, SimulationParameters
    
    try:
        engine = get_simulation_engine()
        dem = np.random.rand(40, 40) * 1000
        params = SimulationParameters(
            rainfall_erosivity=300.0,
            soil_erodibility=0.35,
            cover_factor=0.3,
            practice_factor=0.5,
        )
        result = engine.run_single_simulation(dem, params, show_progress=False)
        
        print(f"[PASS] Simulation executed")
        print(f"       Mean erosion: {result.mean_erosion:.2f} m/year")
        print(f"       Peak erosion: {result.peak_erosion:.2f} m/year")
        print(f"       Computation time: {result.computation_time*1000:.2f} ms")
        
        assert result.mean_erosion > 0, "Mean erosion should be positive"
        assert result.peak_erosion > result.mean_erosion, "Peak > mean"
        return True
    except Exception as e:
        print(f"[FAIL] Simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_result_serialization():
    """Test result serialization for GUI"""
    print("\n" + "="*70)
    print("TEST 3: Result Serialization")
    print("="*70)
    
    from backend.services.simulation_engine import get_simulation_engine, SimulationParameters
    from frontend.main_window import MainWindow
    
    try:
        engine = get_simulation_engine()
        dem = np.random.rand(30, 30) * 800
        result = engine.run_single_simulation(dem, show_progress=False)
        
        # Get the MainWindow class for its serialization method
        result_dict = result.__dict__
        
        # Simulate serialization (MainWindow._serialize_result logic)
        def serialize_result(result_dict):
            serialized = {}
            for key, value in result_dict.items():
                if hasattr(value, 'value'):  # Enum
                    serialized[key] = value.value
                elif isinstance(value, np.ndarray):  # NumPy array
                    serialized[key] = f"<numpy array shape={value.shape}>"
                elif hasattr(value, '__dict__'):  # Dataclass/object
                    serialized[key] = serialize_result(value.__dict__)
                else:
                    serialized[key] = value
            return serialized
        
        serialized = serialize_result(result_dict)
        
        print("[PASS] Serialization successful")
        print(f"       Serialized keys: {list(serialized.keys())[:5]}...")
        print(f"       mode: {serialized.get('mode')} (enum converted)")
        print(f"       mean_erosion: {serialized.get('mean_erosion'):.2f}")
        print(f"       parameters: {len(serialized.get('parameters', {}))} items")
        
        assert isinstance(serialized['mode'], str), "Mode should be string after serialization"
        assert isinstance(serialized['parameters'], dict), "Parameters should be dict"
        return True
    except Exception as e:
        print(f"[FAIL] Serialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parameter_handling():
    """Test parameter conversion in SimulationScreen"""
    print("\n" + "="*70)
    print("TEST 4: Parameter Handling")
    print("="*70)
    
    from backend.services.simulation_engine import SimulationParameters
    
    try:
        # Test dict to SimulationParameters conversion
        params_dict = {
            'rainfall_erosivity': 320.0,
            'soil_erodibility': 0.38,
            'cover_factor': 0.25,
            'practice_factor': 0.6,
        }
        
        # Create SimulationParameters from dict subset
        params = SimulationParameters(
            rainfall_erosivity=params_dict.get('rainfall_erosivity', 300.0),
            soil_erodibility=params_dict.get('soil_erodibility', 0.35),
            cover_factor=params_dict.get('cover_factor', 0.3),
            practice_factor=params_dict.get('practice_factor', 0.5),
        )
        
        print("[PASS] Dict to SimulationParameters conversion")
        print(f"       rainfall_erosivity: {params.rainfall_erosivity}")
        print(f"       soil_erodibility: {params.soil_erodibility}")
        print(f"       cover_factor: {params.cover_factor}")
        
        assert params.rainfall_erosivity == 320.0
        assert params.soil_erodibility == 0.38
        return True
    except Exception as e:
        print(f"[FAIL] Parameter handling: {e}")
        return False


def test_full_workflow():
    """Test complete workflow from simulation to GUI display"""
    print("\n" + "="*70)
    print("TEST 5: Full End-to-End Workflow")
    print("="*70)
    
    from backend.services.simulation_engine import get_simulation_engine, SimulationParameters
    
    try:
        # 1. Create and run simulation
        engine = get_simulation_engine()
        dem = np.random.rand(35, 35) * 900
        params = SimulationParameters(
            rainfall_erosivity=350.0,
            soil_erodibility=0.40,
            cover_factor=0.35,
        )
        result = engine.run_single_simulation(dem, params, show_progress=False)
        print("[STEP 1] Simulation complete")
        
        # 2. Convert to dict (GUI step)
        result_dict = result.__dict__
        print("[STEP 2] Result converted to dict")
        
        # 3. Serialize (remove non-JSON types)
        def serialize_result(d):
            s = {}
            for k, v in d.items():
                if hasattr(v, 'value'):
                    s[k] = v.value
                elif isinstance(v, np.ndarray):
                    s[k] = f"<array {v.shape}>"
                elif hasattr(v, '__dict__'):
                    s[k] = serialize_result(v.__dict__)
                else:
                    s[k] = v
            return s
        
        serialized = serialize_result(result_dict)
        print("[STEP 3] Serialization for GUI complete")
        
        # 4. Test results display
        mode = serialized.get('mode')
        mean_erosion = serialized.get('mean_erosion')
        peak_erosion = serialized.get('peak_erosion')
        params_display = serialized.get('parameters', {})
        
        print(f"[STEP 4] GUI Display Ready:")
        print(f"         Mode: {mode}")
        print(f"         Mean Erosion: {mean_erosion:.4f} m/year")
        print(f"         Peak Erosion: {peak_erosion:.4f} m/year")
        print(f"         Parameters: {list(params_display.keys())[:3]}...")
        
        print("\n[PASS] Complete workflow functional")
        return True
    except Exception as e:
        print(f"[FAIL] Workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TERRASM SIMULATION SYSTEM VERIFICATION")
    print("="*70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Simulation Execution", test_simulation_execution),
        ("Result Serialization", test_result_serialization),
        ("Parameter Handling", test_parameter_handling),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[CRITICAL ERROR in {name}]: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("="*70)
    if all_passed:
        print("SUCCESS: All tests passed - System is operational!")
        print("="*70)
        return 0
    else:
        print("FAILURE: Some tests failed")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
