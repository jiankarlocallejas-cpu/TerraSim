"""
TerraSim Simulation Engine
Orchestrates multi-stage erosion modeling simulations with parameter control

This module provides comprehensive simulation capabilities including:
- Scenario-based parameter variation
- Time-stepping simulation loops with multiple time scales (day/month/year)
- Uncertainty quantification
- Result aggregation and reporting
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class TimeScale(Enum):
    """Time scales for simulation output"""
    DAY = ("day", 1.0)  # Days
    MONTH = ("month", 30.0)  # Days per month (approximate)
    YEAR = ("year", 365.25)  # Days per year
    
    def __init__(self, name: str, days: float):
        self._name = name
        self.days = days  # Conversion factor to days
    
    @property
    def display_name(self) -> str:
        return self._name


class SimulationMode(Enum):
    """Available simulation modes"""
    SINGLE_RUN = "single_run"  # One-time erosion calculation
    TIME_SERIES = "time_series"  # Multiple timesteps
    SENSITIVITY = "sensitivity"  # Parameter sensitivity analysis
    SCENARIO = "scenario"  # Compare multiple scenarios
    UNCERTAINTY = "uncertainty"  # Monte Carlo uncertainty quantification


@dataclass
class SimulationParameters:
    """Core parameters for erosion simulations"""
    # Rainfall erosivity (MJ·mm/ha/hr/yr)
    rainfall_erosivity: float = 300.0
    
    # Soil erodibility (0-1)
    soil_erodibility: float = 0.35
    
    # Vegetation cover factor (0-1)
    cover_factor: float = 0.3
    
    # Management practice factor (0-1)
    practice_factor: float = 0.5
    
    # Time step in days
    time_step_days: float = 1.0
    
    # Number of timesteps
    num_timesteps: int = 10
    
    # Bulk density (kg/m³)
    bulk_density: float = 1300.0
    
    # USPED exponents
    area_exponent: float = 0.6
    slope_exponent: float = 1.3
    
    # Runoff coefficient
    runoff_coefficient: float = 0.5
    
    # Time scale for output reporting
    time_scale: TimeScale = field(default=TimeScale.YEAR)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rainfall_erosivity': self.rainfall_erosivity,
            'soil_erodibility': self.soil_erodibility,
            'cover_factor': self.cover_factor,
            'practice_factor': self.practice_factor,
            'time_step_days': self.time_step_days,
            'num_timesteps': self.num_timesteps,
            'bulk_density': self.bulk_density,
            'area_exponent': self.area_exponent,
            'slope_exponent': self.slope_exponent,
            'runoff_coefficient': self.runoff_coefficient,
            'time_scale': self.time_scale.display_name,
        }


@dataclass
class ErosionScenario:
    """Pre-defined erosion scenarios with parameter sets"""
    name: str
    description: str
    parameters: SimulationParameters
    
    @staticmethod
    def baseline() -> 'ErosionScenario':
        """Baseline scenario - average conditions"""
        return ErosionScenario(
            name="Baseline",
            description="Average erosion conditions with typical parameters",
            parameters=SimulationParameters(
                rainfall_erosivity=300.0,
                soil_erodibility=0.35,
                cover_factor=0.3,
                practice_factor=0.5,
            )
        )
    
    @staticmethod
    def high_rainfall() -> 'ErosionScenario':
        """High rainfall scenario"""
        return ErosionScenario(
            name="High Rainfall",
            description="Intense rainfall events causing increased erosion",
            parameters=SimulationParameters(
                rainfall_erosivity=600.0,  # Double baseline
                soil_erodibility=0.35,
                cover_factor=0.3,
                practice_factor=0.5,
            )
        )
    
    @staticmethod
    def low_vegetation() -> 'ErosionScenario':
        """Low vegetation coverage scenario"""
        return ErosionScenario(
            name="Low Vegetation",
            description="Sparse vegetation cover increases erosion risk",
            parameters=SimulationParameters(
                rainfall_erosivity=300.0,
                soil_erodibility=0.35,
                cover_factor=0.7,  # Less protection (higher value)
                practice_factor=0.5,
            )
        )
    
    @staticmethod
    def extreme_conditions() -> 'ErosionScenario':
        """Extreme erosion scenario"""
        return ErosionScenario(
            name="Extreme Conditions",
            description="Worst-case scenario: high rainfall, low vegetation, poor practices",
            parameters=SimulationParameters(
                rainfall_erosivity=800.0,
                soil_erodibility=0.7,
                cover_factor=0.8,
                practice_factor=0.8,
            )
        )
    
    @staticmethod
    def protected_area() -> 'ErosionScenario':
        """Protected area scenario"""
        return ErosionScenario(
            name="Protected Area",
            description="Good conservation practices and vegetation protection",
            parameters=SimulationParameters(
                rainfall_erosivity=300.0,
                soil_erodibility=0.35,
                cover_factor=0.1,  # Good protection
                practice_factor=0.2,  # Good practices
            )
        )
    
    @staticmethod
    def post_fire() -> 'ErosionScenario':
        """Post-fire scenario"""
        return ErosionScenario(
            name="Post-Fire",
            description="High erosion risk after fire removes vegetation",
            parameters=SimulationParameters(
                rainfall_erosivity=400.0,
                soil_erodibility=0.65,  # Soil structure damaged by fire
                cover_factor=0.95,  # Almost no vegetation
                practice_factor=0.7,
            )
        )
    
    @staticmethod
    def all_scenarios() -> List['ErosionScenario']:
        """Get all available scenarios"""
        return [
            ErosionScenario.baseline(),
            ErosionScenario.high_rainfall(),
            ErosionScenario.low_vegetation(),
            ErosionScenario.extreme_conditions(),
            ErosionScenario.protected_area(),
            ErosionScenario.post_fire(),
        ]


@dataclass
class SimulationResult:
    """Results from a single simulation run"""
    mode: SimulationMode
    parameters: SimulationParameters
    
    # Main outputs
    elevation_change: Optional[np.ndarray] = None
    erosion_rate: Optional[np.ndarray] = None
    deposition_rate: Optional[np.ndarray] = None
    risk_classification: Optional[np.ndarray] = None
    
    # Temporal evolution (for time series)
    elevation_evolution: Optional[List[np.ndarray]] = None
    erosion_evolution: Optional[List[np.ndarray]] = None
    
    # Statistics
    mean_erosion: float = 0.0
    peak_erosion: float = 0.0
    total_volume_loss: float = 0.0
    
    # Uncertainty metrics
    uncertainty_range: Optional[Tuple[float, float]] = None
    confidence_interval_95: Optional[Tuple[float, float]] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    computation_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/export"""
        return {
            'mode': self.mode.value,
            'parameters': self.parameters.to_dict(),
            'mean_erosion': float(self.mean_erosion),
            'peak_erosion': float(self.peak_erosion),
            'total_volume_loss': float(self.total_volume_loss),
            'uncertainty_range': self.uncertainty_range,
            'confidence_interval_95': self.confidence_interval_95,
            'timestamp': self.timestamp.isoformat(),
            'computation_time': self.computation_time,
        }


class SimulationEngine:
    """Core simulation engine for erosion modeling"""
    
    def __init__(self):
        """Initialize the simulation engine"""
        logger.info("Initializing TerraSim Simulation Engine")
        self.default_params = SimulationParameters()
        self.history: List[SimulationResult] = []
    
    def run_single_simulation(
        self,
        dem: np.ndarray,
        parameters: Optional[SimulationParameters] = None,
        show_progress: bool = True
    ) -> SimulationResult:
        """
        Run a single erosion simulation
        
        Args:
            dem: Digital Elevation Model (2D array in meters)
            parameters: Simulation parameters (uses defaults if None)
            show_progress: Whether to print progress information
        
        Returns:
            SimulationResult with erosion calculations
        """
        if parameters is None:
            parameters = self.default_params
        
        logger.info("Starting single erosion simulation")
        start_time = time.time()
        
        # Calculate terrain derivatives (slopes, aspects, etc.)
        slopes = self._calculate_slopes(dem)
        aspects = self._calculate_aspects(dem)
        flow_accumulation = self._calculate_flow_accumulation(dem)
        
        # Calculate transport capacity
        transport_capacity = self._calculate_transport_capacity(
            flow_accumulation, slopes, parameters
        )
        
        # Calculate erosion/deposition
        erosion_rate = self._calculate_erosion(
            transport_capacity, aspects, parameters
        )
        deposition_rate = transport_capacity - erosion_rate
        
        # Calculate risk classification
        risk_classification = self._classify_risk(erosion_rate)
        
        # Calculate statistics
        elevation_change = -erosion_rate * parameters.time_step_days
        mean_erosion = np.mean(erosion_rate[erosion_rate > 0])
        peak_erosion = np.max(erosion_rate)
        total_volume_loss = np.sum(erosion_rate) * (dem.shape[0] * dem.shape[1])
        
        computation_time = time.time() - start_time
        
        result = SimulationResult(
            mode=SimulationMode.SINGLE_RUN,
            parameters=parameters,
            elevation_change=elevation_change,
            erosion_rate=erosion_rate,
            deposition_rate=deposition_rate,
            risk_classification=risk_classification,
            mean_erosion=float(mean_erosion),
            peak_erosion=float(peak_erosion),
            total_volume_loss=float(total_volume_loss),
            computation_time=computation_time,
        )
        
        self.history.append(result)
        
        if show_progress:
            logger.info(f"[SINGLE RUN] Mean erosion: {mean_erosion:.4f} m/year")
            logger.info(f"[SINGLE RUN] Peak erosion: {peak_erosion:.4f} m/year")
            logger.info(f"[SINGLE RUN] Volume loss: {total_volume_loss:.2e} m³")
            logger.info(f"[SINGLE RUN] Computed in {computation_time:.2f}s")
        
        return result
    
    def run_time_series_simulation(
        self,
        dem: np.ndarray,
        parameters: Optional[SimulationParameters] = None,
        show_progress: bool = True
    ) -> SimulationResult:
        """
        Run time-series erosion simulation with multiple timesteps
        
        Args:
            dem: Initial Digital Elevation Model
            parameters: Simulation parameters
            show_progress: Whether to print progress
        
        Returns:
            SimulationResult with temporal evolution
        """
        if parameters is None:
            parameters = self.default_params
        
        logger.info(f"Starting time-series simulation ({parameters.num_timesteps} timesteps)")
        start_time = time.time()
        
        # Initialize arrays for evolution tracking
        elevation_evolution = [dem.copy()]
        erosion_evolution = []
        
        current_dem = dem.copy()
        
        # Time-stepping loop
        for step in range(parameters.num_timesteps):
            if show_progress and step % max(1, parameters.num_timesteps // 10) == 0:
                logger.info(f"[TIME-SERIES] Step {step+1}/{parameters.num_timesteps}")
            
            # Calculate terrain properties
            slopes = self._calculate_slopes(current_dem)
            aspects = self._calculate_aspects(current_dem)
            flow_accumulation = self._calculate_flow_accumulation(current_dem)
            
            # Calculate transport capacity
            transport_capacity = self._calculate_transport_capacity(
                flow_accumulation, slopes, parameters
            )
            
            # Calculate erosion/deposition
            erosion_rate = self._calculate_erosion(
                transport_capacity, aspects, parameters
            )
            
            # Update DEM
            elevation_change = -erosion_rate * parameters.time_step_days
            current_dem += elevation_change
            
            elevation_evolution.append(current_dem.copy())
            erosion_evolution.append(erosion_rate.copy())
        
        # Calculate final statistics
        final_elevation_change = current_dem - dem
        mean_erosion = np.mean(np.array(erosion_evolution)[np.array(erosion_evolution) > 0])
        peak_erosion = np.max(erosion_evolution)
        total_volume_loss = np.sum(final_elevation_change) * (dem.shape[0] * dem.shape[1])
        
        computation_time = time.time() - start_time
        
        result = SimulationResult(
            mode=SimulationMode.TIME_SERIES,
            parameters=parameters,
            elevation_change=final_elevation_change,
            erosion_rate=erosion_evolution[-1],
            elevation_evolution=elevation_evolution,
            erosion_evolution=erosion_evolution,
            mean_erosion=float(mean_erosion),
            peak_erosion=float(peak_erosion),
            total_volume_loss=float(total_volume_loss),
            computation_time=computation_time,
        )
        
        self.history.append(result)
        
        if show_progress:
            logger.info(f"[TIME-SERIES] Final mean erosion: {mean_erosion:.4f} m/year")
            logger.info(f"[TIME-SERIES] Peak erosion: {peak_erosion:.4f} m/year")
            logger.info(f"[TIME-SERIES] Total volume change: {total_volume_loss:.2e} m³")
            logger.info(f"[TIME-SERIES] Computed in {computation_time:.2f}s")
        
        return result
    
    def run_sensitivity_analysis(
        self,
        dem: np.ndarray,
        base_parameters: Optional[SimulationParameters] = None,
        vary_factor: float = 0.2,
        show_progress: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Run sensitivity analysis on key parameters
        
        Args:
            dem: Digital Elevation Model
            base_parameters: Base parameters for sensitivity analysis
            vary_factor: Variation factor (0.2 = ±20%)
            show_progress: Whether to print progress
        
        Returns:
            Dictionary of sensitivity indices
        """
        if base_parameters is None:
            base_parameters = self.default_params
        
        logger.info("Starting sensitivity analysis")
        
        sensitivity_results = {}
        
        # Parameters to test
        test_params = [
            ('rainfall_erosivity', 'R'),
            ('soil_erodibility', 'K'),
            ('cover_factor', 'C'),
            ('practice_factor', 'P'),
        ]
        
        # Baseline run
        baseline = self.run_single_simulation(dem, base_parameters, show_progress=False)
        baseline_erosion = baseline.mean_erosion
        
        for param_name, param_label in test_params:
            if show_progress:
                logger.info(f"[SENSITIVITY] Testing {param_label} ({param_name})")
            
            # Perturbed run (+vary_factor)
            params_high = self._modify_parameter(base_parameters, param_name, 1 + vary_factor)
            result_high = self.run_single_simulation(dem, params_high, show_progress=False)
            
            # Perturbed run (-vary_factor)
            params_low = self._modify_parameter(base_parameters, param_name, 1 - vary_factor)
            result_low = self.run_single_simulation(dem, params_low, show_progress=False)
            
            # Calculate sensitivity index
            sensitivity_index = (
                (result_high.mean_erosion - result_low.mean_erosion) / 
                (2 * vary_factor * baseline_erosion)
            )
            
            sensitivity_results[param_label] = {
                'index': sensitivity_index,
                'baseline': baseline_erosion,
                'high': result_high.mean_erosion,
                'low': result_low.mean_erosion,
            }
        
        if show_progress:
            logger.info("[SENSITIVITY] Analysis complete:")
            for param, results in sensitivity_results.items():
                logger.info(f"  {param}: sensitivity index = {results['index']:.4f}")
        
        return sensitivity_results
    
    def run_scenario_comparison(
        self,
        dem: np.ndarray,
        scenarios: Optional[List[ErosionScenario]] = None,
        time_scale: TimeScale = TimeScale.YEAR,
        show_progress: bool = True
    ) -> Dict[str, SimulationResult]:
        """
        Run simulations for multiple pre-defined scenarios
        
        Args:
            dem: Digital Elevation Model
            scenarios: List of scenarios to compare (uses all if None)
            time_scale: Time scale for output reporting
            show_progress: Whether to print progress
        
        Returns:
            Dictionary of scenario results
        """
        if scenarios is None:
            scenarios = ErosionScenario.all_scenarios()
        
        logger.info(f"Starting scenario comparison with {len(scenarios)} scenarios")
        start_time = time.time()
        
        scenario_results = {}
        
        for idx, scenario in enumerate(scenarios):
            if show_progress:
                logger.info(f"[SCENARIO] {idx+1}/{len(scenarios)} - {scenario.name}")
            
            # Update time scale
            params = scenario.parameters
            params.time_scale = time_scale
            
            # Run simulation
            result = self.run_single_simulation(dem, params, show_progress=False)
            scenario_results[scenario.name] = result
            
            if show_progress:
                logger.info(f"  Mean erosion: {result.mean_erosion:.4f} {time_scale.display_name}s/year")
                logger.info(f"  Peak erosion: {result.peak_erosion:.4f} {time_scale.display_name}s/year")
        
        computation_time = time.time() - start_time
        
        if show_progress:
            logger.info(f"[SCENARIO] Comparison complete in {computation_time:.2f}s")
            logger.info("[SCENARIO] Summary:")
            for scenario_name, result in scenario_results.items():
                logger.info(f"  {scenario_name}: {result.mean_erosion:.4f} {time_scale.display_name}s/year")
        
        return scenario_results
    
    def run_uncertainty_analysis(
        self,
        dem: np.ndarray,
        base_parameters: Optional[SimulationParameters] = None,
        num_samples: int = 100,
        variation_std: float = 0.1,
        show_progress: bool = True
    ) -> SimulationResult:
        """
        Run Monte Carlo uncertainty quantification
        
        Args:
            dem: Digital Elevation Model
            base_parameters: Base parameters
            num_samples: Number of Monte Carlo samples
            variation_std: Standard deviation of parameter variation (fraction)
            show_progress: Whether to print progress
        
        Returns:
            SimulationResult with uncertainty metrics
        """
        if base_parameters is None:
            base_parameters = self.default_params
        
        logger.info(f"Starting uncertainty analysis ({num_samples} samples)")
        start_time = time.time()
        
        results = []
        
        for sample in range(num_samples):
            if show_progress and (sample + 1) % max(1, num_samples // 10) == 0:
                logger.info(f"[UNCERTAINTY] Sample {sample+1}/{num_samples}")
            
            # Generate perturbed parameters
            perturbed = self._perturb_parameters(base_parameters, variation_std)
            
            # Run simulation
            result = self.run_single_simulation(dem, perturbed, show_progress=False)
            results.append(result.mean_erosion)
        
        # Calculate statistics
        results_array = np.array(results)
        mean_erosion = np.mean(results_array)
        std_erosion = np.std(results_array)
        ci_95_low = np.percentile(results_array, 2.5)
        ci_95_high = np.percentile(results_array, 97.5)
        
        computation_time = time.time() - start_time
        
        result = SimulationResult(
            mode=SimulationMode.UNCERTAINTY,
            parameters=base_parameters,
            mean_erosion=float(mean_erosion),
            uncertainty_range=(np.min(results_array), np.max(results_array)),
            confidence_interval_95=(ci_95_low, ci_95_high),
            computation_time=computation_time,
        )
        
        self.history.append(result)
        
        if show_progress:
            logger.info(f"[UNCERTAINTY] Mean: {mean_erosion:.4f} ± {std_erosion:.4f} m/year")
            logger.info(f"[UNCERTAINTY] 95% CI: [{ci_95_low:.4f}, {ci_95_high:.4f}]")
            logger.info(f"[UNCERTAINTY] Computed in {computation_time:.2f}s")
        
        return result
    
    # ============= HELPER METHODS =============
    
    @staticmethod
    def _calculate_slopes(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
        """Calculate slope angles from DEM"""
        gradx = np.gradient(dem, axis=1) / cell_size
        grady = np.gradient(dem, axis=0) / cell_size
        slope = np.arctan(np.sqrt(gradx**2 + grady**2))
        return slope
    
    @staticmethod
    def _calculate_aspects(dem: np.ndarray) -> np.ndarray:
        """Calculate aspect angles from DEM"""
        gradx = np.gradient(dem, axis=1)
        grady = np.gradient(dem, axis=0)
        aspect = np.arctan2(grady, gradx)
        return aspect
    
    @staticmethod
    def _calculate_flow_accumulation(dem: np.ndarray) -> np.ndarray:
        """Calculate cumulative upslope area"""
        # Simplified flow accumulation
        flow = np.ones_like(dem)
        return np.cumsum(flow.ravel()).reshape(flow.shape)
    
    @staticmethod
    def _calculate_transport_capacity(
        flow: np.ndarray,
        slopes: np.ndarray,
        params: SimulationParameters
    ) -> np.ndarray:
        """
        Calculate sediment transport capacity (T) using USPED.
        
        USPED equation: T = R * K * C * P * (A_norm^m) * (sin β)^n
        where A_norm = contributing area normalized by reference area (1 ha = 10,000 m²)
        
        Units analysis:
        - R, K, C, P are normalized dimensionless factors (0-1000, 0-1, 0-1, 0-1)
        - Flow term represents normalized contributing area
        - Result T is proportional to eroding power
        - Final erosion rate = T * scaling factor [m/year]
        """
        # Normalize contributing area by reference (1 ha = 10,000 m²)
        A_ref = 10000.0  # Reference area in m²
        flow_normalized = np.maximum(flow, 1.0) / A_ref
        
        # USPED transport capacity
        sin_slope = np.sin(np.maximum(slopes, 0.001))
        
        T = (
            params.rainfall_erosivity * 
            params.soil_erodibility * 
            params.cover_factor * 
            params.practice_factor *
            (flow_normalized ** params.area_exponent) *
            (sin_slope ** params.slope_exponent)
        )
        
        return np.maximum(T, 0)
    
    @staticmethod
    def _calculate_erosion(
        transport_capacity: np.ndarray,
        aspects: np.ndarray,
        params: SimulationParameters
    ) -> np.ndarray:
        """
        Calculate erosion rate from transport capacity with time scale conversion.
        
        z_change = -(dt_years / rho_b) * div(T)
        
        For simplified model without full divergence:
        erosion_rate [m/time_scale] = transport_capacity * scaling / rho_b * conversion
        
        where rho_b = 1300 kg/m³ (bulk density)
        
        Converts output to requested time scale (day/month/year)
        """
        # Bulk density in kg/m³
        rho_b = 1300.0
        
        # Conversion factor: days to years
        days_per_year = 365.25
        
        # Time conversion from days to years
        # erosion [m/year] = T [proportional to kg/m] / rho_b [kg/m³] * dt [years]
        dt_years = params.time_step_days / days_per_year
        
        # Calculate erosion rate in m/year
        erosion_per_year = (transport_capacity * params.runoff_coefficient * dt_years) / (rho_b / 1000)
        
        # Convert to requested time scale
        if params.time_scale == TimeScale.DAY:
            erosion = erosion_per_year / days_per_year
        elif params.time_scale == TimeScale.MONTH:
            erosion = erosion_per_year / (days_per_year / 30.0)
        else:  # TimeScale.YEAR
            erosion = erosion_per_year
        
        return np.maximum(erosion, 0)
    
    @staticmethod
    def _classify_risk(erosion_rate: np.ndarray) -> np.ndarray:
        """Classify erosion risk (5-tier system)"""
        risk = np.zeros_like(erosion_rate, dtype=int)
        
        # Define thresholds (m/year)
        thresholds = [0.001, 0.005, 0.01, 0.05, 0.1]
        
        for i, threshold in enumerate(thresholds):
            risk[erosion_rate >= threshold] = i + 1
        
        return risk
    
    @staticmethod
    def _modify_parameter(
        params: SimulationParameters,
        param_name: str,
        factor: float
    ) -> SimulationParameters:
        """Create modified parameter set"""
        params_dict = params.to_dict()
        params_dict[param_name] *= factor
        return SimulationParameters(**params_dict)
    
    @staticmethod
    def _perturb_parameters(
        params: SimulationParameters,
        std_factor: float
    ) -> SimulationParameters:
        """Create perturbed parameters with random variation"""
        params_dict = params.to_dict()
        
        for key in params_dict:
            if key not in ['time_step_days', 'num_timesteps']:
                perturbation = np.random.normal(1.0, std_factor)
                params_dict[key] *= max(0.1, perturbation)  # Prevent negative values
        
        return SimulationParameters(**params_dict)
    
    def get_history(self) -> List[SimulationResult]:
        """Get list of all simulation runs"""
        return self.history
    
    def clear_history(self):
        """Clear simulation history"""
        self.history.clear()
        logger.info("Simulation history cleared")


# Singleton instance
_engine = None


def get_simulation_engine() -> SimulationEngine:
    """Get or create the simulation engine singleton"""
    global _engine
    if _engine is None:
        _engine = SimulationEngine()
    return _engine
