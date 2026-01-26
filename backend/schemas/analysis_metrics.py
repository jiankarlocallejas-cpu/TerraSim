"""
Pydantic schemas for AnalysisMetrics
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class AnalysisMetricsBase(BaseModel):
    """Base schema for analysis metrics"""
    metric_type: str  # "sensitivity", "correlation", "uncertainty"
    metric_name: str
    methodology: str


class AnalysisMetricsCreate(AnalysisMetricsBase):
    """Schema for creating analysis metrics"""
    analysis_id: int
    project_id: int
    erosion_result_id: Optional[int] = None


class AnalysisMetricsUpdate(BaseModel):
    """Schema for updating analysis metrics"""
    metric_name: Optional[str] = None
    base_value: Optional[float] = None
    sensitivity_index: Optional[float] = None
    parameter_importance_rank: Optional[int] = None
    correlation_coefficient: Optional[float] = None
    p_value: Optional[float] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    cvar_95: Optional[float] = None
    cvar_99: Optional[float] = None
    key_finding: Optional[str] = None
    interpretation: Optional[str] = None
    recommendations: Optional[str] = None


class AnalysisMetricsInDB(AnalysisMetricsBase):
    """Schema for analysis metrics from database"""
    id: int
    analysis_id: int
    project_id: int
    owner_id: int
    erosion_result_id: Optional[int] = None
    base_value: Optional[float] = None
    perturbation_percent: Optional[float] = None
    sensitivity_index: Optional[float] = None
    parameter_importance_rank: Optional[int] = None
    correlation_coefficient: Optional[float] = None
    p_value: Optional[float] = None
    correlation_strength: Optional[str] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    cvar_95: Optional[float] = None
    cvar_99: Optional[float] = None
    monte_carlo_iterations: Optional[int] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    sample_size: Optional[int] = None
    key_finding: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisMetricsResponse(AnalysisMetricsInDB):
    """Response schema for analysis metrics"""
    pass


# Sensitivity Analysis specific
class SensitivityAnalysisRequest(BaseModel):
    """Request for sensitivity analysis"""
    parameters: Dict[str, float]  # {param_name: value}
    perturbation_percent: float = 10.0
    analysis_id: Optional[int] = None


class SensitivityAnalysisResult(BaseModel):
    """Result of sensitivity analysis"""
    parameter: str
    base_value: float
    sensitivity_index: float
    importance_rank: int
    interpretation: str


# Correlation Analysis specific
class CorrelationAnalysisRequest(BaseModel):
    """Request for correlation analysis"""
    factor1_name: str
    factor2_name: str
    values1: List[float]
    values2: List[float]
    analysis_id: Optional[int] = None


class CorrelationAnalysisResult(BaseModel):
    """Result of correlation analysis"""
    factor1: str
    factor2: str
    pearson_r: float
    p_value: float
    correlation_strength: str  # "weak", "moderate", "strong"
    is_significant: bool


# Uncertainty Quantification specific
class UncertaintyAnalysisRequest(BaseModel):
    """Request for uncertainty analysis"""
    erosion_samples: List[float]
    confidence_levels: List[float] = [0.95, 0.99]
    monte_carlo_iterations: Optional[int] = 1000


class UncertaintyAnalysisResult(BaseModel):
    """Result of uncertainty analysis"""
    var_95: float  # Value at Risk at 95%
    var_99: float  # Value at Risk at 99%
    cvar_95: float  # Conditional VaR at 95%
    cvar_99: float  # Conditional VaR at 99%
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    extreme_threshold: float
    interpretation: str
