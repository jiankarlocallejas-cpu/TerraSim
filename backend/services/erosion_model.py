"""
TerraSim Erosion Modeling Engine

PRIMARY EQUATION - USPED-Based 2.5D SoilModel:
═════════════════════════════════════════════════════════════════════════

Elevation Evolution:
    z(t+Δt) = z(t) - (Δt/ρ_b) * [∂(T cos α)/∂x + ∂(T sin α)/∂y + ε ∂(T sin β)/∂z]

Sediment Transport Capacity:
    T = f(R, K, C, P, A^m, (sin β)^n, Q(I,S))

═════════════════════════════════════════════════════════════════════════

Where:
  z(x,y,t)  = Surface elevation (m)
  Δt         = Time step (days)
  ρ_b        = Bulk density of soil (kg/m³) ≈ 1300
  T          = Sediment transport capacity (kg/s)
  α          = Aspect angle (flow direction)
  β          = Slope angle (steepness)
  ε          = Slope effect coefficient ≈ 0.01
  R          = Rainfall erosivity (MJ·mm/ha/yr)
  K          = Soil erodibility (Mg·ha·h/MJ/mm)
  C          = Cover-management factor (0-1)
  P          = Support practices factor (0-1)
  A          = Contributing area (m²)
  Q          = Runoff depth (mm/event)
  I          = Rainfall intensity (mm/hr)
  S          = Soil retention (mm)
  m          = Area exponent = 0.6
  n          = Slope exponent = 1.3

This module implements the core erosion modeling calculations based on the
USPED (Unit Stream Power-based Erosion Deposition) framework with RUSLE
validation and hydrological integration.

References:
- USPED model: Mitasova & Hofierka (1993)
- RUSLE: Revised Universal Soil Loss Equation
- SCS Curve Number method: Natural Resources Conservation Service
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class ErosionFactors:
    """Container for erosion model factors following RUSLE framework"""
    R: float  # Rainfall erosivity factor (MJ·mm/ha/hr/yr)
    K: float  # Soil erodibility factor (Mg·ha·hr/ha·MJ·mm)
    C: float  # Cover-management factor (0-1)
    P: float  # Support practices factor (0-1)
    LS: float  # Slope length and steepness factor
    A: float  # Contributing area (m²)
    beta: float  # Slope angle (radians)
    Q: float  # Runoff depth (mm)


@dataclass
class SoilModelParameters:
    """Parameters for 2.5D SoilModel computation"""
    rho_b: float = 1300  # Bulk density (kg/m³)
    m: float = 0.6  # Exponent for contributing area
    n: float = 1.3  # Exponent for slope angle
    epsilon: float = 0.01  # Vertical transport coefficient
    dt: float = 1.0  # Timestep (years)


class TerraSIMErosionModel:
    """
    TerraSim Erosion Modeling Engine implementing USPED-based 2.5D SoilModel
    
    Main equation:
    z(t+dt) = z(t) - (dt/ρ_b) * [∂(T cos α)/∂x + ∂(T sin α)/∂y + ε ∂(T sin β)/∂z]
    
    where T = f(R, K, C, P, A^m, (sin β)^n, Q(I,S))
    """
    
    def __init__(self, params: Optional[SoilModelParameters] = None):
        """Initialize erosion model with parameters"""
        self.params = params or SoilModelParameters()
        self.logger = logging.getLogger(__name__)
        
    def compute_sediment_transport(
        self,
        factors: ErosionFactors
    ) -> float:
        """
        Compute sediment transport capacity T using USPED formulation.
        
        T = K·C·P·R·Q·(A^m)·(sin β)^n
        
        Args:
            factors: ErosionFactors object with all required inputs
            
        Returns:
            Sediment transport capacity (kg/m/s or similar units)
        """
        try:
            # Base RUSLE equation component
            rusle_component = factors.K * factors.C * factors.P * factors.R
            
            # USPED enhancements
            area_component = (factors.A ** self.params.m)
            slope_component = (np.sin(factors.beta) ** self.params.n)
            runoff_component = factors.Q
            
            # Combined transport capacity
            T = rusle_component * area_component * slope_component * runoff_component
            
            return max(0, T)  # Ensure non-negative transport
        except Exception as e:
            self.logger.error(f"Error computing sediment transport: {e}")
            return 0.0
    
    def compute_erosion_deposition_divergence(
        self,
        T: float,
        dT_dx: float,
        dT_dy: float,
        dT_dz: float,
        flow_direction: float,
        slope: float
    ) -> float:
        """
        Compute erosion-deposition using divergence of transport capacity.
        
        ∇·T = ∂(T cos α)/∂x + ∂(T sin α)/∂y + ε ∂(T sin β)/∂z
        
        Args:
            T: Sediment transport capacity
            dT_dx: Spatial derivative in x direction
            dT_dy: Spatial derivative in y direction
            dT_dz: Spatial derivative in z (vertical) direction
            flow_direction: Flow direction angle (radians)
            slope: Slope angle (radians)
            
        Returns:
            Divergence of transport (erosion/deposition rate)
        """
        try:
            # Divergence components
            div_x = dT_dx * np.cos(flow_direction)
            div_y = dT_dy * np.sin(flow_direction)
            div_z = self.params.epsilon * dT_dz * np.sin(slope)
            
            divergence = div_x + div_y + div_z
            return divergence
        except Exception as e:
            self.logger.error(f"Error computing divergence: {e}")
            return 0.0
    
    def update_elevation(
        self,
        current_elevation: float,
        divergence: float
    ) -> float:
        """
        Update DEM elevation based on erosion-deposition.
        
        z(t+dt) = z(t) - (dt/ρ_b) * ∇·T
        
        Args:
            current_elevation: Current elevation (m)
            divergence: Divergence of transport capacity
            
        Returns:
            Updated elevation (m)
        """
        try:
            elevation_change = -(self.params.dt / self.params.rho_b) * divergence
            new_elevation = current_elevation + elevation_change
            return new_elevation
        except Exception as e:
            self.logger.error(f"Error updating elevation: {e}")
            return current_elevation
    
    def compute_rusle_comparison(self, factors: ErosionFactors) -> Dict[str, float]:
        """
        Compute RUSLE (Revised Universal Soil Loss Equation) for validation.
        
        A = R·K·L·S·C·P
        
        where:
        - A: Annual soil loss (Mg/ha/yr)
        - R: Rainfall erosivity
        - K: Soil erodibility
        - L·S: Topographic factor (combined from LS)
        - C: Cover-management factor
        - P: Support practices factor
        
        Args:
            factors: ErosionFactors object
            
        Returns:
            Dictionary with RUSLE components and total
        """
        try:
            # RUSLE equation
            A = factors.R * factors.K * factors.LS * factors.C * factors.P
            
            return {
                'annual_soil_loss_Mg_ha': A,
                'rainfall_erosivity_R': factors.R,
                'soil_erodibility_K': factors.K,
                'topographic_LS': factors.LS,
                'cover_management_C': factors.C,
                'support_practices_P': factors.P,
                'total_soil_loss_tons': A * 0.1  # Convert Mg/ha to tons
            }
        except Exception as e:
            self.logger.error(f"Error computing RUSLE: {e}")
            return {}
    
    def classify_erosion_risk(
        self,
        annual_soil_loss: float
    ) -> Dict[str, Any]:
        """
        Classify erosion risk based on soil loss thresholds.
        
        Based on:
        - <2 Mg/ha/yr: Very Low Risk
        - 2-5: Low Risk
        - 5-10: Moderate Risk
        - 10-20: High Risk
        - >20: Very High Risk
        
        Args:
            annual_soil_loss: Annual soil loss in Mg/ha/yr
            
        Returns:
            Risk classification with description and urgency
        """
        risk_thresholds = [
            (2, 'very_low', 'Minimal erosion concern', 1),
            (5, 'low', 'Minor erosion risk', 2),
            (10, 'moderate', 'Moderate erosion requiring monitoring', 3),
            (20, 'high', 'High erosion risk requiring intervention', 4),
            (float('inf'), 'very_high', 'Critical erosion risk requiring immediate action', 5)
        ]
        
        for threshold, risk_level, description, urgency in risk_thresholds:
            if annual_soil_loss < threshold:
                return {
                    'risk_level': risk_level,
                    'description': description,
                    'urgency': urgency,
                    'soil_loss_Mg_ha_yr': round(annual_soil_loss, 2)
                }
        
        return {
            'risk_level': 'very_high',
            'description': 'Critical erosion risk requiring immediate action',
            'urgency': 5,
            'soil_loss_Mg_ha_yr': round(annual_soil_loss, 2)
        }


class RainfallRunoffCalculator:
    """
    Calculate rainfall-runoff using SCS Curve Number method.
    
    References:
    - SCS Curve Number (CN) methodology
    - PAGASA rainfall data processing
    """
    
    # SCS curve numbers by land use and soil group
    SCS_CURVE_NUMBERS = {
        'forest': {'A': 30, 'B': 55, 'C': 70, 'D': 77},
        'grassland': {'A': 30, 'B': 58, 'C': 71, 'D': 78},
        'agriculture': {'A': 62, 'B': 71, 'C': 78, 'D': 81},
        'urban': {'A': 57, 'B': 72, 'C': 81, 'D': 86},
        'bare_soil': {'A': 77, 'B': 86, 'C': 91, 'D': 94},
        'water': {'A': 100, 'B': 100, 'C': 100, 'D': 100}
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_curve_number(
        self,
        land_use: str,
        soil_group: str
    ) -> float:
        """
        Get SCS curve number from land use and soil group.
        
        Args:
            land_use: Type of land use (forest, grassland, agriculture, etc.)
            soil_group: Soil hydrologic group (A, B, C, D)
            
        Returns:
            SCS Curve Number (0-100)
        """
        return self.SCS_CURVE_NUMBERS.get(
            land_use.lower(),
            self.SCS_CURVE_NUMBERS['bare_soil']
        ).get(soil_group.upper(), 70)
    
    def compute_runoff(
        self,
        rainfall: float,
        curve_number: float
    ) -> float:
        """
        Compute runoff depth using SCS-CN method.
        
        Q = (P - Ia)² / (P - Ia + S)
        
        where:
        - Q: Runoff depth (mm)
        - P: Rainfall depth (mm)
        - Ia: Initial abstraction = 0.2*S
        - S: Maximum potential retention = 25400/CN - 254
        
        Args:
            rainfall: Rainfall depth (mm)
            curve_number: SCS Curve Number (0-100)
            
        Returns:
            Runoff depth (mm)
        """
        try:
            if rainfall <= 0:
                return 0.0
            
            # Compute maximum potential retention
            S = (25400 / max(curve_number, 1)) - 254
            S = max(S, 0)  # Ensure non-negative
            
            # Initial abstraction
            Ia = 0.2 * S
            
            # Check if rainfall exceeds initial abstraction
            if rainfall <= Ia:
                return 0.0
            
            # SCS-CN equation
            Q = ((rainfall - Ia) ** 2) / (rainfall - Ia + S)
            
            return max(0, Q)  # Ensure non-negative
        except Exception as e:
            self.logger.error(f"Error computing runoff: {e}")
            return 0.0
    
    def compute_rainfall_erosivity(
        self,
        annual_rainfall: float,
        max_daily_rainfall: float
    ) -> float:
        """
        Compute rainfall erosivity factor (R) for RUSLE.
        
        Simplified approach:
        R = 0.0483 * P^1.61  (for tropical regions)
        
        Args:
            annual_rainfall: Annual precipitation (mm)
            max_daily_rainfall: Maximum daily rainfall (mm)
            
        Returns:
            Rainfall erosivity factor R (MJ·mm/ha/hr/yr)
        """
        try:
            # Tropical rainfall erosivity formula
            R = 0.0483 * (annual_rainfall ** 1.61)
            
            # Adjust for intense rainfall events
            intensity_factor = 1.0 + (max_daily_rainfall / annual_rainfall) * 0.1
            
            return R * intensity_factor
        except Exception as e:
            self.logger.error(f"Error computing rainfall erosivity: {e}")
            return 0.0


class SoilErodibilityCalculator:
    """
    Calculate soil erodibility factor (K) from soil properties.
    
    References:
    - USLE/RUSLE soil erodibility equations
    - Palawan Soils Laboratory data processing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_K_factor(
        self,
        sand_percent: float,
        silt_percent: float,
        clay_percent: float,
        organic_matter_percent: float,
        structure_code: int = 1
    ) -> float:
        """
        Compute soil erodibility K factor using USLE equation.
        
        K = f(M, OM, ST, P)
        
        where:
        - M = particle size parameter
        - OM = organic matter percentage
        - ST = soil structure code
        - P = soil permeability code
        
        Args:
            sand_percent: Sand content (%)
            silt_percent: Silt content (%)
            clay_percent: Clay content (%)
            organic_matter_percent: Organic matter (%)
            structure_code: Soil structure code (1-4)
            
        Returns:
            Soil erodibility K factor (Mg·ha·hr/ha·MJ·mm)
        """
        try:
            # Particle size parameter M
            M = (silt_percent + sand_percent) * (100 - clay_percent)
            
            # Organic matter effect
            OM_factor = 1.0 - (0.0256 * organic_matter_percent) / (organic_matter_percent + np.exp(3.72 - 2.95 * organic_matter_percent))
            
            # Structure effect (simplified)
            structure_factors = {1: 0.25, 2: 0.35, 3: 0.50, 4: 1.0}
            ST_factor = structure_factors.get(structure_code, 0.5)
            
            # Base K calculation
            K = (2.1e-4 * M ** 1.14 * (12 - organic_matter_percent) + 3.25 * (ST_factor - 2) + 2.5 * (0.5 - 0.1)) / 100
            
            # Apply organic matter adjustment
            K = K * OM_factor
            
            return max(0, K)
        except Exception as e:
            self.logger.error(f"Error computing K factor: {e}")
            return 0.2  # Default moderate erodibility


class UncertaintyAnalyzer:
    """
    Perform uncertainty and risk analysis using Value at Risk (VaR)
    and Conditional Value at Risk (CVaR) methods.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compute_var(
        self,
        values: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Compute Value at Risk (VaR) at specified confidence level.
        
        VaR = percentile of loss distribution
        
        Args:
            values: Array of erosion/loss values
            confidence_level: Confidence level (0-1), default 95%
            
        Returns:
            VaR value at specified confidence level
        """
        percentile = (1 - confidence_level) * 100
        return np.percentile(values, percentile)
    
    def compute_cvar(
        self,
        values: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Compute Conditional Value at Risk (CVaR) - average of worst-case scenarios.
        
        CVaR = mean of values exceeding VaR
        
        Args:
            values: Array of erosion/loss values
            confidence_level: Confidence level (0-1), default 95%
            
        Returns:
            CVaR - expected loss given worst-case scenarios
        """
        var = self.compute_var(values, confidence_level)
        return np.mean(values[values >= var]) if np.any(values >= var) else var
    
    def analyze_uncertainty(
        self,
        erosion_values: np.ndarray,
        rainfall_scenarios: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive uncertainty analysis.
        
        Args:
            erosion_values: Array of computed erosion values
            rainfall_scenarios: Dictionary of rainfall scenarios
            
        Returns:
            Uncertainty analysis report
        """
        return {
            'var_95': self.compute_var(erosion_values, 0.95),
            'var_99': self.compute_var(erosion_values, 0.99),
            'cvar_95': self.compute_cvar(erosion_values, 0.95),
            'cvar_99': self.compute_cvar(erosion_values, 0.99),
            'mean': np.mean(erosion_values),
            'std': np.std(erosion_values),
            'min': np.min(erosion_values),
            'max': np.max(erosion_values),
            'scenarios': rainfall_scenarios
        }
