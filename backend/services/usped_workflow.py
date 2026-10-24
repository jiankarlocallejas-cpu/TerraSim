"""
USPED Workflow Manager
Implements soil erosion and deposition modeling following the USPED process
Based on: Mitasova & Hofierka (1993) and GRASS GIS/ArcGIS workflows
"""

import numpy as np
from typing import Dict, Optional, Tuple, Any
from scipy.ndimage import convolve
import logging
from enum import Enum

from .dinf_routing import route_dinf

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """USPED workflow steps"""
    LOAD_DATA = "load_data"
    COMPUTE_SLOPE = "compute_slope"
    COMPUTE_ASPECT = "compute_aspect"
    COMPUTE_FLOW = "compute_flow"
    COMPUTE_LST = "compute_lst"
    COMPUTE_SEDFLOW = "compute_sedflow"
    COMPUTE_COMPONENTS = "compute_components"
    COMPUTE_DERIVATIVES = "compute_derivatives"
    COMPUTE_EROSION = "compute_erosion"
    CLASSIFY_RESULTS = "classify_results"


class USPEDWorkflow:
    """
    Unified Sediment Transport and Hillslope Erosion Deposition (USPED) Workflow
    
    Steps:
    1. Load input layers (DEM, land cover, soil properties, etc.)
    2. Compute slope
    3. Compute aspect
    4. Compute flow accumulation
    5. Compute topographic sediment transport capacity (LST)
    6. Compute sediment flow
    7. Compute sediment flow components (x, y)
    8. Compute partial derivatives
    9. Compute erosion/deposition
    10. Classify results
    """
    
    def __init__(self, elevation: np.ndarray, cell_size: float = 1.0):
        """
        Initialize USPED workflow
        
        Args:
            elevation: Digital Elevation Model
            cell_size: Cell size in meters
        """
        self.elevation = elevation.copy()
        self.cell_size = cell_size
        self.results = {}
        self.current_step = WorkflowStep.LOAD_DATA
        
        # Input parameters
        self.rainfall_factor = 270.0  # R factor
        self.soil_kfac = None
        self.cover_cfac = None
        
        # Terrain parameters
        self.slope = None
        self.aspect = None
        self.flow_accum = None
        self.flow_direction = None
        
        # Flow parameters
        self.m_exponent = 1.0  # Flow accumulation exponent
        self.n_exponent = 1.0  # Slope exponent
        
        logger.info(f"Initialized USPED workflow with DEM shape {elevation.shape}")
    
    def set_parameters(self, 
                      rainfall_factor: float = 270.0,
                      soil_kfac: Optional[np.ndarray] = None,
                      cover_cfac: Optional[np.ndarray] = None,
                      m_exponent: float = 1.0,
                      n_exponent: float = 1.0):
        """Set workflow parameters"""
        self.rainfall_factor = rainfall_factor
        self.soil_kfac = soil_kfac if soil_kfac is not None else np.ones_like(self.elevation)
        self.cover_cfac = cover_cfac if cover_cfac is not None else np.ones_like(self.elevation)
        self.m_exponent = m_exponent
        self.n_exponent = n_exponent
        
        logger.info(f"Set parameters: R={rainfall_factor}, m={m_exponent}, n={n_exponent}")
    
    def step_1_load_data(self) -> Dict[str, Any]:
        """Step 1: Load and validate input data"""
        logger.info("Step 1: Loading data...")
        
        # Validate inputs
        if self.elevation is None:
            raise ValueError("Elevation data required")
        
        self.current_step = WorkflowStep.LOAD_DATA
        self.results['elevation'] = self.elevation
        
        return {
            'step': 'Load Data',
            'shape': self.elevation.shape,
            'min_elev': float(np.min(self.elevation)),
            'max_elev': float(np.max(self.elevation)),
            'status': 'Data loaded successfully'
        }
    
    def step_2_compute_slope(self) -> Dict[str, Any]:
        """Step 2: Compute slope map"""
        logger.info("Step 2: Computing slope...")
        
        # Compute slope using Sobel operator
        x_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / (8.0 * self.cell_size)
        y_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / (8.0 * self.cell_size)
        
        dz_dx = convolve(self.elevation, x_kernel)
        dz_dy = convolve(self.elevation, y_kernel)
        
        # Slope in degrees
        self.slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))
        
        self.current_step = WorkflowStep.COMPUTE_SLOPE
        self.results['slope'] = self.slope
        
        logger.info(f"Slope computed: min={np.min(self.slope):.2f}°, max={np.max(self.slope):.2f}°")
        
        return {
            'step': 'Compute Slope',
            'min': float(np.min(self.slope)),
            'max': float(np.max(self.slope)),
            'mean': float(np.mean(self.slope)),
            'status': 'Slope map computed'
        }
    
    def step_3_compute_aspect(self) -> Dict[str, Any]:
        """Step 3: Compute aspect map"""
        logger.info("Step 3: Computing aspect...")
        
        if self.slope is None:
            raise ValueError("Slope must be computed first")
        
        # Compute aspect using gradients
        x_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 8.0
        y_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 8.0
        
        dz_dx = convolve(self.elevation, x_kernel)
        dz_dy = convolve(self.elevation, y_kernel)
        
        # Aspect in degrees (0-360)
        self.aspect = np.degrees(np.arctan2(dz_dx, -dz_dy))
        self.aspect = (self.aspect + 360) % 360
        
        self.current_step = WorkflowStep.COMPUTE_ASPECT
        self.results['aspect'] = self.aspect
        
        logger.info(f"Aspect computed: min={np.min(self.aspect):.1f}°, max={np.max(self.aspect):.1f}°")
        
        return {
            'step': 'Compute Aspect',
            'min': float(np.min(self.aspect)),
            'max': float(np.max(self.aspect)),
            'status': 'Aspect map computed'
        }
    
    def step_4_compute_flow_accumulation(self) -> Dict[str, Any]:
        """Step 4: Compute flow accumulation"""
        logger.info("Step 4: Computing flow accumulation...")
        
        # D-infinity routing leaves depressions as explicit terminal cells.
        routing = route_dinf(self.elevation, cell_size_x=self.cell_size)
        self.flow_direction = routing.flow_direction
        self.flow_accum = routing.contributing_area
        
        self.current_step = WorkflowStep.COMPUTE_FLOW
        self.results['flow_direction'] = self.flow_direction
        self.results['flow_accum'] = self.flow_accum
        self.results['routing_terminal_mask'] = routing.terminal_mask
        
        valid_area = self.flow_accum[routing.valid_mask]
        terminal_count = int(np.count_nonzero(routing.terminal_mask))
        area_min = float(np.min(valid_area)) if valid_area.size else 0.0
        area_max = float(np.max(valid_area)) if valid_area.size else 0.0
        area_mean = float(np.mean(valid_area)) if valid_area.size else 0.0
        logger.info(
            "D-infinity contributing area computed: min=%.2f, max=%.2f, terminal cells=%d",
            area_min, area_max, terminal_count,
        )
        
        return {
            'step': 'D-infinity Flow Routing',
            'min_contributing_area': area_min,
            'max_contributing_area': area_max,
            'mean_contributing_area': area_mean,
            'terminal_cells': terminal_count,
            'status': 'D-infinity routing computed; depressions remain terminal'
        }
    
    def step_5_compute_lst(self) -> Dict[str, Any]:
        """Step 5: Compute topographic sediment transport capacity (LST)"""
        logger.info("Step 5: Computing LST (topographic factor)...")
        
        if self.slope is None or self.flow_accum is None:
            raise ValueError("Slope and flow accumulation required")
        
        # LST = contributing_area^m * (sin(slope))^n; area is in map units squared.
        # Convert slope to radians
        slope_rad = np.radians(self.slope)
        
        # D-infinity returns physical contributing area in square map units.
        upslope_area = self.flow_accum
        
        # Compute LST
        lst = np.power(upslope_area, self.m_exponent) * np.power(np.sin(slope_rad), self.n_exponent)
        
        self.results['lst'] = lst
        
        logger.info(f"LST computed: min={np.min(lst):.2e}, max={np.max(lst):.2e}")
        
        return {
            'step': 'Compute LST',
            'min': float(np.min(lst)),
            'max': float(np.max(lst)),
            'mean': float(np.mean(lst)),
            'status': 'LST (topographic factor) computed'
        }
    
    def step_6_compute_sedflow(self) -> Dict[str, Any]:
        """Step 6: Compute sediment flow"""
        logger.info("Step 6: Computing sediment flow...")
        
        if 'lst' not in self.results:
            raise ValueError("LST must be computed first")
        
        # Ensure parameters are set
        if self.soil_kfac is None or self.cover_cfac is None:
            self.set_parameters()
        
        lst = self.results['lst']
        soil_k = self.soil_kfac if self.soil_kfac is not None else np.ones_like(lst)
        cover_c = self.cover_cfac if self.cover_cfac is not None else np.ones_like(lst)
        
        # Sediment flow: Q = R * K * C * LST
        # where R = rainfall factor, K = soil erodibility, C = cover factor
        sedflow = self.rainfall_factor * soil_k * cover_c * lst
        
        self.results['sedflow'] = sedflow
        
        logger.info(f"Sediment flow computed: min={np.min(sedflow):.2e}, max={np.max(sedflow):.2e}")
        
        return {
            'step': 'Compute Sediment Flow',
            'min': float(np.min(sedflow)),
            'max': float(np.max(sedflow)),
            'mean': float(np.mean(sedflow)),
            'status': 'Sediment flow computed'
        }
    
    def step_7_compute_flow_components(self) -> Dict[str, Any]:
        """Step 7: Compute sediment flow components in x and y directions"""
        logger.info("Step 7: Computing flow components...")
        
        if 'sedflow' not in self.results or self.flow_direction is None:
            raise ValueError("Sediment flow and D-infinity direction required")
        
        sedflow = self.results['sedflow']
        
        # Direction is radians counterclockwise from east. Terminal/nodata
        # cells have NaN direction and carry no routed flux.
        valid_direction = np.isfinite(self.flow_direction)
        sedflow_x = np.where(
            valid_direction, sedflow * np.cos(self.flow_direction), 0.0
        )
        sedflow_y = np.where(
            valid_direction, sedflow * np.sin(self.flow_direction), 0.0
        )
        
        self.results['sedflow_x'] = sedflow_x
        self.results['sedflow_y'] = sedflow_y
        
        logger.info(f"Flow components computed: X range [{np.min(sedflow_x):.2e}, {np.max(sedflow_x):.2e}]")
        
        return {
            'step': 'Compute Flow Components',
            'sedflow_x_range': (float(np.min(sedflow_x)), float(np.max(sedflow_x))),
            'sedflow_y_range': (float(np.min(sedflow_y)), float(np.max(sedflow_y))),
            'status': 'Flow components computed'
        }
    
    def step_8_compute_derivatives(self) -> Dict[str, Any]:
        """Step 8: Compute partial derivatives of sediment flow"""
        logger.info("Step 8: Computing partial derivatives...")
        
        if 'sedflow_x' not in self.results or 'sedflow_y' not in self.results:
            raise ValueError("Flow components required")
        
        sedflow_x = self.results['sedflow_x']
        sedflow_y = self.results['sedflow_y']
        
        # Compute derivatives using central differences
        kernel_x = np.array([[-1, 0, 1]]) / (2.0 * self.cell_size)
        # Raster rows increase south; map-coordinate y increases north.
        kernel_y = -np.array([[-1], [0], [1]]) / (2.0 * self.cell_size)
        
        # dqsx/dx
        dqsx_dx = convolve(sedflow_x, kernel_x)
        # dqsy/dy in north-positive coordinates
        dqsy_dy = convolve(sedflow_y, kernel_y)
        
        self.results['dqsx_dx'] = dqsx_dx
        self.results['dqsy_dy'] = dqsy_dy
        
        logger.info(f"Derivatives computed: dqsx/dx range [{np.min(dqsx_dx):.2e}, {np.max(dqsx_dx):.2e}]")
        
        return {
            'step': 'Compute Derivatives',
            'dqsx_dx_range': (float(np.min(dqsx_dx)), float(np.max(dqsx_dx))),
            'dqsy_dy_range': (float(np.min(dqsy_dy)), float(np.max(dqsy_dy))),
            'status': 'Partial derivatives computed'
        }
    
    def step_9_compute_erosion_deposition(self) -> Dict[str, Any]:
        """Step 9: Compute net erosion/deposition"""
        logger.info("Step 9: Computing erosion/deposition...")
        
        if 'dqsx_dx' not in self.results or 'dqsy_dy' not in self.results:
            raise ValueError("Derivatives required")
        
        # Net erosion/deposition: E = dqsx/dx + dqsy/dy
        erosion_deposition = self.results['dqsx_dx'] + self.results['dqsy_dy']
        
        self.results['erosion_deposition'] = erosion_deposition
        
        logger.info(f"Erosion/deposition computed: range [{np.min(erosion_deposition):.2e}, {np.max(erosion_deposition):.2e}]")
        
        return {
            'step': 'Compute Erosion/Deposition',
            'min': float(np.min(erosion_deposition)),
            'max': float(np.max(erosion_deposition)),
            'mean': float(np.mean(erosion_deposition)),
            'erosion_area': float(np.sum(erosion_deposition < 0)),
            'deposition_area': float(np.sum(erosion_deposition > 0)),
            'status': 'Erosion/deposition map computed'
        }
    
    def step_10_classify_results(self, num_classes: int = 11) -> Dict[str, Any]:
        """Step 10: Classify results"""
        logger.info(f"Step 10: Classifying results into {num_classes} classes...")
        
        if 'erosion_deposition' not in self.results:
            raise ValueError("Erosion/deposition map required")
        
        data = self.results['erosion_deposition']
        
        # Create classification: negative = erosion, positive = deposition
        min_val = np.min(data)
        max_val = np.max(data)
        
        # Define breakpoints
        breakpoints = np.linspace(min_val, max_val, num_classes + 1)
        
        # Create classified map
        classified = np.digitize(data, breakpoints)
        
        self.results['classified'] = classified
        self.results['breakpoints'] = breakpoints
        
        # Classification scheme
        # Negative values (erosion): -250000 to -50, -50 to -5, -5 to -1, -1 to -0.1
        # Neutral: -0.1 to 0.1
        # Positive values (deposition): 0.1 to 1, 1 to 5, 5 to 50, 50 to 330000
        
        erosion_classes = {
            'High erosion': np.sum((data < -50)),
            'Moderate erosion': np.sum((data >= -50) & (data < -5)),
            'Low erosion': np.sum((data >= -5) & (data < -0.1)),
            'Neutral': np.sum((data >= -0.1) & (data <= 0.1)),
            'Low deposition': np.sum((data > 0.1) & (data <= 5)),
            'Moderate deposition': np.sum((data > 5) & (data <= 50)),
            'High deposition': np.sum((data > 50))
        }
        
        self.results['classification'] = erosion_classes
        self.current_step = WorkflowStep.CLASSIFY_RESULTS
        
        return {
            'step': 'Classify Results',
            'num_classes': num_classes,
            'breakpoints': breakpoints.tolist(),
            'classification': {k: int(v) for k, v in erosion_classes.items()},
            'status': 'Results classified'
        }
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """Run complete USPED workflow"""
        logger.info("Starting complete USPED workflow...")
        
        workflow_results = {}
        
        try:
            workflow_results['step_1'] = self.step_1_load_data()
            workflow_results['step_2'] = self.step_2_compute_slope()
            workflow_results['step_3'] = self.step_3_compute_aspect()
            workflow_results['step_4'] = self.step_4_compute_flow_accumulation()
            workflow_results['step_5'] = self.step_5_compute_lst()
            workflow_results['step_6'] = self.step_6_compute_sedflow()
            workflow_results['step_7'] = self.step_7_compute_flow_components()
            workflow_results['step_8'] = self.step_8_compute_derivatives()
            workflow_results['step_9'] = self.step_9_compute_erosion_deposition()
            workflow_results['step_10'] = self.step_10_classify_results()
            
            workflow_results['status'] = 'completed'
            logger.info("USPED workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
        
        return workflow_results
