"""
TerraSim Terrain Simulation Example
Demonstrates how to use the 3D time-stepped terrain simulator (World Machine-style)
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.terrain_simulator import (
    TerrainSimulator,
    TimeStepParameters,
    SimulationMode,
    create_simulator_for_mode
)


def create_synthetic_dem(shape=(100, 100), seed=42) -> np.ndarray:
    """Create a synthetic DEM for testing."""
    np.random.seed(seed)
    
    # Base terrain
    x = np.linspace(0, 10, shape[1])
    y = np.linspace(0, 10, shape[0])
    X, Y = np.meshgrid(x, y)
    
    # Mountain-like feature
    dem = 1000 + 200 * np.exp(-((X - 5)**2 + (Y - 5)**2) / 5)
    
    # Add some roughness
    dem += np.random.normal(0, 20, shape)
    
    return dem


def example_1_basic_simulation():
    """Example 1: Basic terrain simulation with default parameters"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Terrain Simulation")
    print("="*60)
    
    # Create synthetic DEM
    dem = create_synthetic_dem()
    print(f"Created DEM: shape={dem.shape}, "
          f"elevation range=[{dem.min():.1f}, {dem.max():.1f}] m")
    
    # Create simulator
    simulator = TerrainSimulator(dem, cell_size=10.0)
    
    # Run simulation with default parameters
    params = TimeStepParameters(
        dt=1.0,
        num_timesteps=50,
        rainfall_factor=270.0
    )
    
    print(f"\nRunning simulation:")
    print(f"  Time step: {params.dt} years")
    print(f"  Number of steps: {params.num_timesteps}")
    print(f"  Total simulated time: {params.dt * params.num_timesteps} years")
    
    snapshots = simulator.run_simulation(params)
    
    # Print results
    first_snap = snapshots[0]
    last_snap = snapshots[-1]
    
    print(f"\nInitial state:")
    print(f"  Elevation: [{first_snap.min_elevation:.2f}, {first_snap.max_elevation:.2f}] m")
    print(f"  Mean elevation: {first_snap.mean_elevation:.2f} m")
    
    print(f"\nFinal state:")
    print(f"  Elevation: [{last_snap.min_elevation:.2f}, {last_snap.max_elevation:.2f}] m")
    print(f"  Mean elevation: {last_snap.mean_elevation:.2f} m")
    
    print(f"\nTerrain change:")
    print(f"  Elevation change: {last_snap.mean_elevation - first_snap.mean_elevation:.2f} m")
    print(f"  Total volume change: {last_snap.total_volume_change:.2e} m³")


def example_2_simulation_modes():
    """Example 2: Compare different simulation modes"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Comparing Simulation Modes")
    print("="*60)
    
    # Create DEM
    dem = create_synthetic_dem()
    
    modes = [
        "slow",
        "medium", 
        "fast",
        "extreme"
    ]
    
    results = {}
    
    for mode_name in modes:
        mode = SimulationMode[mode_name.upper()]
        print(f"\nRunning {mode_name} mode simulation...")
        
        # Create simulator with mode-specific parameters
        simulator, params = create_simulator_for_mode(dem.copy(), mode, cell_size=10.0)
        
        print(f"  Parameters: dt={params.dt}yr, steps={params.num_timesteps}, "
              f"rainfall={params.rainfall_factor}")
        
        # Run simulation
        snapshots = simulator.run_simulation(params)
        
        # Store results
        last_snap = snapshots[-1]
        results[mode_name] = {
            "total_time": last_snap.time_years,
            "elevation_change": last_snap.mean_elevation - snapshots[0].mean_elevation,
            "volume_change": last_snap.total_volume_change,
            "snapshots": len(snapshots)
        }
        
        print(f"  Total time simulated: {last_snap.time_years:.1f} years")
        print(f"  Elevation change: {results[mode_name]['elevation_change']:.2f} m")
    
    # Compare
    print("\n" + "-"*60)
    print("COMPARISON SUMMARY")
    print("-"*60)
    print(f"{'Mode':<12} {'Time':<12} {'Elev Change':<15} {'Volume Change':<15}")
    print("-"*60)
    
    for mode_name, data in results.items():
        print(f"{mode_name:<12} {data['total_time']:<12.1f} "
              f"{data['elevation_change']:<15.2f} {data['volume_change']:<15.2e}")


def example_3_custom_parameters():
    """Example 3: Using custom parameters for fine control"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Simulation Parameters")
    print("="*60)
    
    dem = create_synthetic_dem()
    
    # Define custom parameters
    params = TimeStepParameters(
        dt=2.0,                    # 2-year time steps
        num_timesteps=200,         # 400 years total
        rainfall_factor=400.0,     # High rainfall
        m_exponent=0.5,            # Lower flow accumulation exponent
        n_exponent=1.5,            # Higher slope exponent
        damping_factor=0.90        # More damping for stability
    )
    
    print(f"Custom parameters:")
    print(f"  Time step: {params.dt} years")
    print(f"  Total timesteps: {params.num_timesteps}")
    print(f"  Total time: {params.dt * params.num_timesteps} years")
    print(f"  Rainfall factor: {params.rainfall_factor}")
    print(f"  Flow exponent (m): {params.m_exponent}")
    print(f"  Slope exponent (n): {params.n_exponent}")
    print(f"  Damping factor: {params.damping_factor}")
    
    # Run simulation
    simulator = TerrainSimulator(dem, cell_size=10.0)
    snapshots = simulator.run_simulation(params)
    
    print(f"\nSimulation results:")
    print(f"  Total snapshots: {len(snapshots)}")
    print(f"  Initial elevation: {snapshots[0].mean_elevation:.2f} m")
    print(f"  Final elevation: {snapshots[-1].mean_elevation:.2f} m")
    print(f"  Elevation change: {snapshots[-1].mean_elevation - snapshots[0].mean_elevation:.2f} m")


def example_4_temporal_analysis():
    """Example 4: Analyze how terrain changes over time"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Temporal Analysis of Terrain Evolution")
    print("="*60)
    
    dem = create_synthetic_dem()
    
    # Create simulator
    simulator, params = create_simulator_for_mode(dem, SimulationMode.MEDIUM, cell_size=10.0)
    
    print(f"Running simulation with {params.num_timesteps} timesteps...")
    snapshots = simulator.run_simulation(params)
    
    # Get evolution series
    times, max_elevations, mean_elevations = simulator.get_evolution_series()
    
    print(f"\nTemporal evolution:")
    print(f"{'Timestep':<10} {'Time (yr)':<12} {'Max Elev':<12} {'Mean Elev':<12}")
    print("-" * 50)
    
    # Print every 10th timestep
    for i in range(0, len(snapshots), max(1, len(snapshots) // 10)):
        snap = snapshots[i]
        print(f"{i:<10} {snap.time_years:<12.1f} "
              f"{snap.max_elevation:<12.2f} {snap.mean_elevation:<12.2f}")
    
    # Final
    snap = snapshots[-1]
    print(f"{snap.timestep:<10} {snap.time_years:<12.1f} "
          f"{snap.max_elevation:<12.2f} {snap.mean_elevation:<12.2f}")


def example_5_erosion_deposition_map():
    """Example 5: Visualize cumulative erosion/deposition"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Erosion/Deposition Mapping")
    print("="*60)
    
    dem = create_synthetic_dem()
    
    # Run simulation
    simulator, params = create_simulator_for_mode(dem, SimulationMode.FAST, cell_size=10.0)
    snapshots = simulator.run_simulation(params)
    
    # Get erosion maps from last snapshot
    last_snap = snapshots[-1]
    erosion_map = last_snap.total_erosion
    
    print(f"\nErosion/Deposition statistics:")
    print(f"  Max erosion: {np.max(erosion_map):.2f} m")
    print(f"  Max deposition: {np.min(erosion_map):.2f} m")
    print(f"  Mean change: {np.mean(erosion_map):.2f} m")
    print(f"  Std deviation: {np.std(erosion_map):.2f} m")
    
    # Count pixels
    erosion_pixels = np.sum(erosion_map < -0.1)
    deposition_pixels = np.sum(erosion_map > 0.1)
    stable_pixels = np.sum(np.abs(erosion_map) <= 0.1)
    
    total_pixels = erosion_map.size
    
    print(f"\nPixel statistics:")
    print(f"  Erosion pixels: {erosion_pixels}/{total_pixels} ({100*erosion_pixels/total_pixels:.1f}%)")
    print(f"  Deposition pixels: {deposition_pixels}/{total_pixels} ({100*deposition_pixels/total_pixels:.1f}%)")
    print(f"  Stable pixels: {stable_pixels}/{total_pixels} ({100*stable_pixels/total_pixels:.1f}%)")
    
    print(f"\nFinal DEM from simulation:")
    final_dem = simulator.get_final_dem()
    print(f"  Shape: {final_dem.shape}")
    print(f"  Elevation: [{final_dem.min():.1f}, {final_dem.max():.1f}] m")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TerraSim Terrain Simulator - Examples")
    print("World Machine-style 3D terrain evolution simulation")
    print("="*60)
    
    # Run examples
    try:
        example_1_basic_simulation()
        example_2_simulation_modes()
        example_3_custom_parameters()
        example_4_temporal_analysis()
        example_5_erosion_deposition_map()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
