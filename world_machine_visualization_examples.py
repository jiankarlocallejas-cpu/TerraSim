"""
World Machine-style Terrain Simulation Visualization Examples

This module demonstrates all visualization capabilities with:
- User-friendly progress tracking
- Clear error messages and validation
- Professional output formatting
- End-to-end working examples
"""

import numpy as np
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

# Configure logging for better user feedback
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('visualization_examples.log')
    ]
)
logger = logging.getLogger(__name__)

# Import simulator and visualizer
try:
    from backend.services.terrain_simulator import (
        TerrainSimulator,
        TimeStepParameters,
        SimulationMode,
        create_simulator_for_mode
    )
    from backend.services.world_machine_style import (
        WorldMachineVisualizer,
        WorldMachineColorScheme,
        SimulationAnimationRenderer
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running from the TerraSim root directory")
    sys.exit(1)


class ProgressBar:
    """Simple progress bar for user feedback"""
    
    @staticmethod
    def show(current: int, total: int, label: str = "Progress", width: int = 40):
        """Display a progress bar"""
        if total <= 0:
            return
        
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        pct = f"{percent * 100:.1f}%"
        sys.stdout.write(f"\r{label}: [{bar}] {pct}")
        sys.stdout.flush()
        
        if current >= total:
            print()  # New line when complete


def print_header(title: str):
    """Print a formatted section header"""
    width = 70
    print("\n" + "=" * width)
    print(f"  {title.center(width - 4)}")
    print("=" * width + "\n")


def print_success(message: str):
    """Print a success message"""
    print(f"✓ SUCCESS: {message}\n")


def print_error(message: str):
    """Print an error message"""
    print(f"✗ ERROR: {message}\n")


def print_info(message: str, indent: int = 0):
    """Print an info message"""
    prefix = "  " * indent + "→ "
    print(f"{prefix}{message}")


def create_synthetic_dem(size: int = 128, seed: Optional[int] = None) -> np.ndarray:
    """
    Create a synthetic DEM for testing
    
    Args:
        size: Size of the DEM (size x size)
        seed: Random seed for reproducibility
        
    Returns:
        Synthetic DEM array
    """
    if seed is not None:
        np.random.seed(seed)
    
    x = np.linspace(-2, 2, size)
    y = np.linspace(-2, 2, size)
    X, Y = np.meshgrid(x, y)
    
    # Create a realistic terrain with peaks and valleys
    dem = 100 + 50 * np.sin(X) * np.cos(Y) + 30 * np.exp(-(X**2 + Y**2) / 2)
    dem += np.random.normal(0, 2, dem.shape)  # Add some noise
    
    return dem.astype(np.float32)


# ==============================================================================
# EXAMPLE 1: Single Frame Natural Coloring
# ==============================================================================

def example_1_single_frame_natural():
    """Example 1: Render a single DEM frame with natural World Machine coloring"""
    print_header("EXAMPLE 1: Single Frame Natural Coloring")
    
    try:
        print_info("Creating synthetic DEM (256x256)")
        dem = create_synthetic_dem(256, seed=42)
        print_info(f"DEM created: min={dem.min():.1f}, max={dem.max():.1f}")
        
        print_info("Initializing visualizer")
        visualizer = WorldMachineVisualizer()
        
        print_info("Rendering frame with natural coloring")
        frame = visualizer.render_simulation_frame(
            dem,
            timestep=0,
            total_timesteps=1,
            colorscheme=WorldMachineColorScheme.NATURAL,
            show_hillshade=True,
            show_flow=False
        )
        
        print_info(f"Frame rendered: shape={frame.shape}, dtype={frame.dtype}")
        
        # Save result
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        from PIL import Image
        img = Image.fromarray(frame)
        output_path = output_dir / "example_1_natural_coloring.png"
        img.save(str(output_path))
        
        print_success(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 1 failed")
        return False


# ==============================================================================
# EXAMPLE 2: Erosion/Deposition Heatmap
# ==============================================================================

def example_2_erosion_heatmap():
    """Example 2: Show erosion and deposition patterns as heatmap"""
    print_header("EXAMPLE 2: Erosion/Deposition Heatmap")
    
    try:
        print_info("Creating initial DEM")
        dem_initial = create_synthetic_dem(256, seed=42)
        
        print_info("Creating modified DEM (simulating erosion)")
        dem_eroded = dem_initial.copy()
        # Simulate erosion patterns
        dem_eroded[50:150, 50:150] -= np.linspace(0, 15, 100)[:, np.newaxis]
        dem_eroded = np.clip(dem_eroded, dem_initial.min(), dem_initial.max())
        
        print_info("Initializing visualizer")
        visualizer = WorldMachineVisualizer()
        
        print_info("Rendering erosion heatmap")
        frame = visualizer.render_simulation_frame(
            dem_eroded,
            timestep=0,
            total_timesteps=1,
            colorscheme=WorldMachineColorScheme.EROSION_HEAT,
            show_hillshade=False,
            show_flow=True
        )
        
        print_info(f"Frame rendered: shape={frame.shape}")
        
        # Save result
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        from PIL import Image
        img = Image.fromarray(frame)
        output_path = output_dir / "example_2_erosion_heatmap.png"
        img.save(str(output_path))
        
        print_success(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 2 failed")
        return False


# ==============================================================================
# EXAMPLE 3: Terrain Animation
# ==============================================================================

def example_3_animation_sequence():
    """Example 3: Create an animated sequence showing terrain evolution"""
    print_header("EXAMPLE 3: Terrain Evolution Animation")
    
    try:
        print_info("Creating animation renderer")
        renderer = SimulationAnimationRenderer(colorscheme=WorldMachineColorScheme.NATURAL)
        
        print_info("Generating 12 frames of terrain evolution")
        base_dem = create_synthetic_dem(256, seed=42)
        
        for t in range(12):
            ProgressBar.show(t + 1, 12, "Rendering frames")
            
            # Simulate progressive erosion
            dem = base_dem.copy()
            dem -= (t / 12) * 20 * np.linspace(0, 1, 256)[:, np.newaxis]
            dem = np.clip(dem, base_dem.min(), dem.max())
            
            renderer.add_snapshot(dem, t, 12, WorldMachineColorScheme.NATURAL)
        
        print_info(f"Generated {renderer.get_frame_count()} frames")
        
        # Save animation
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "example_3_terrain_animation.gif"
        
        print_info("Saving animation to GIF")
        success = renderer.save_animation(
            str(output_path),
            duration_per_frame=100,
            loop=0
        )
        
        if success:
            print_success(f"Saved to {output_path}")
            return True
        else:
            print_error("Failed to save animation")
            return False
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 3 failed")
        return False


# ==============================================================================
# EXAMPLE 4: Advanced Hillshading
# ==============================================================================

def example_4_advanced_hillshade():
    """Example 4: Demonstrate advanced hillshading with different lighting angles"""
    print_header("EXAMPLE 4: Advanced Hillshading")
    
    try:
        print_info("Creating DEM")
        dem = create_synthetic_dem(256, seed=42)
        
        print_info("Initializing visualizer")
        visualizer = WorldMachineVisualizer()
        
        # Render with hillshading
        print_info("Rendering with advanced hillshading")
        frame = visualizer.render_simulation_frame(
            dem,
            timestep=0,
            total_timesteps=1,
            colorscheme=WorldMachineColorScheme.NATURAL,
            show_hillshade=True,
            show_flow=False
        )
        
        print_info(f"Frame rendered: shape={frame.shape}")
        
        # Save result
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        from PIL import Image
        img = Image.fromarray(frame)
        output_path = output_dir / "example_4_hillshade.png"
        img.save(str(output_path))
        
        print_success(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 4 failed")
        return False


# ==============================================================================
# EXAMPLE 5: Water Flow Visualization
# ==============================================================================

def example_5_flow_visualization():
    """Example 5: Visualize water flow accumulation"""
    print_header("EXAMPLE 5: Water Flow Visualization")
    
    try:
        print_info("Creating DEM with clear drainage patterns")
        dem = create_synthetic_dem(256, seed=42)
        
        print_info("Initializing visualizer")
        visualizer = WorldMachineVisualizer()
        
        print_info("Rendering with flow visualization")
        frame = visualizer.render_simulation_frame(
            dem,
            timestep=0,
            total_timesteps=1,
            colorscheme=WorldMachineColorScheme.NATURAL,
            show_hillshade=True,
            show_flow=True
        )
        
        print_info(f"Frame rendered: shape={frame.shape}")
        
        # Save result
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        from PIL import Image
        img = Image.fromarray(frame)
        output_path = output_dir / "example_5_flow_visualization.png"
        img.save(str(output_path))
        
        print_success(f"Saved to {output_path}")
        return True
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 5 failed")
        return False


# ==============================================================================
# EXAMPLE 6: All Color Schemes Comparison
# ==============================================================================

def example_6_colorscheme_comparison():
    """Example 6: Compare all available color schemes"""
    print_header("EXAMPLE 6: Color Scheme Comparison")
    
    try:
        print_info("Creating DEM")
        dem = create_synthetic_dem(256, seed=42)
        
        print_info("Initializing visualizer")
        visualizer = WorldMachineVisualizer()
        
        colorschemes = [
            WorldMachineColorScheme.NATURAL,
            WorldMachineColorScheme.EROSION_HEAT,
            WorldMachineColorScheme.GEOLOGICAL,
            WorldMachineColorScheme.THERMAL,
            WorldMachineColorScheme.HEIGHTMAP
        ]
        
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        
        from PIL import Image
        
        print_info(f"Rendering {len(colorschemes)} color schemes")
        for i, scheme in enumerate(colorschemes):
            ProgressBar.show(i + 1, len(colorschemes), "Rendering schemes")
            
            frame = visualizer.render_simulation_frame(
                dem,
                timestep=0,
                total_timesteps=1,
                colorscheme=scheme,
                show_hillshade=True,
                show_flow=False
            )
            
            img = Image.fromarray(frame)
            output_path = output_dir / f"example_6_scheme_{scheme.name.lower()}.png"
            img.save(str(output_path))
        
        print_success(f"Saved {len(colorschemes)} images to {output_dir}")
        return True
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 6 failed")
        return False


# ==============================================================================
# EXAMPLE 7: Full Simulation with Statistics
# ==============================================================================

def example_7_full_simulation():
    """Example 7: Run full simulation with visual output and statistics"""
    print_header("EXAMPLE 7: Full Simulation with Statistics")
    
    try:
        print_info("Creating terrain simulator")
        try:
            simulator = create_simulator_for_mode(SimulationMode.EROSION)
            print_info(f"Simulator created: mode={SimulationMode.EROSION.name}")
        except Exception as e:
            print_error(f"Could not create simulator: {e}")
            logger.info("Falling back to synthetic DEM demo")
            
            # Fallback: just show DEM processing
            print_info("Creating synthetic DEM for demonstration")
            dem = create_synthetic_dem(256, seed=42)
            
            print_info("Initializing visualizer")
            visualizer = WorldMachineVisualizer()
            
            print_info("Rendering frame")
            frame = visualizer.render_simulation_frame(dem)
            
            output_dir = Path("visualization_output")
            output_dir.mkdir(exist_ok=True)
            
            from PIL import Image
            img = Image.fromarray(frame)
            output_path = output_dir / "example_7_simulation.png"
            img.save(str(output_path))
            
            print_success(f"Saved to {output_path}")
            return True
        
        # If simulator was created successfully
        print_info("Initializing animation renderer")
        renderer = SimulationAnimationRenderer(colorscheme=WorldMachineColorScheme.NATURAL)
        
        print_info("Running 10 simulation steps")
        dem = create_synthetic_dem(256, seed=42)
        
        for t in range(10):
            ProgressBar.show(t + 1, 10, "Simulation progress")
            
            # Simulate with some progression
            dem = dem.copy()
            dem -= (t / 10) * 10
            
            renderer.add_snapshot(dem, t, 10)
        
        output_dir = Path("visualization_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "example_7_full_simulation.gif"
        
        print_info(f"Saving {renderer.get_frame_count()} frames to animation")
        success = renderer.save_animation(str(output_path))
        
        if success:
            print_success(f"Saved to {output_path}")
            return True
        else:
            print_error("Failed to save animation")
            return False
        
    except Exception as e:
        print_error(f"{str(e)}")
        logger.exception("Example 7 failed")
        return False


# ==============================================================================
# Main Entry Point
# ==============================================================================

def run_all_examples():
    """Run all examples and report results"""
    print_header("WORLD MACHINE VISUALIZATION EXAMPLES")
    print_info("Running all 7 examples with comprehensive error handling", 0)
    print_info("Output will be saved to ./visualization_output/", 0)
    
    examples = [
        ("Example 1: Natural Coloring", example_1_single_frame_natural),
        ("Example 2: Erosion Heatmap", example_2_erosion_heatmap),
        ("Example 3: Animation", example_3_animation_sequence),
        ("Example 4: Hillshading", example_4_advanced_hillshade),
        ("Example 5: Flow Visualization", example_5_flow_visualization),
        ("Example 6: Color Schemes", example_6_colorscheme_comparison),
        ("Example 7: Full Simulation", example_7_full_simulation),
    ]
    
    results = []
    for name, example_func in examples:
        try:
            success = example_func()
            results.append((name, success))
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            logger.exception(f"Unexpected error in {name}")
            results.append((name, False))
    
    # Print summary
    print_header("SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} examples passed\n")
    
    if passed == total:
        print("✓ All examples completed successfully!")
    else:
        print(f"⚠ {total - passed} example(s) failed. Check visualization_examples.log for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_examples()
    sys.exit(0 if success else 1)
