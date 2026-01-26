"""
AnalysisMetrics model - stores sensitivity, correlation, and uncertainty metrics
"""
from sqlalchemy import String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from .base import BaseModel

if TYPE_CHECKING:
    from .analysis import Analysis
    from .erosion_result import ErosionResult
    from .project import Project
    from .user import User


class AnalysisMetrics(BaseModel):
    """
    Stores detailed analysis metrics including:
    - Sensitivity analysis results
    - Correlation analysis between factors
    - Uncertainty quantification (VaR, CVaR)
    - Parameter importance rankings
    """
    __tablename__ = "analysis_metrics"

    # Associations
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), nullable=False, index=True)
    erosion_result_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erosion_results.id"), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Metric type
    metric_type: Mapped[str] = mapped_column(String, nullable=False, index=True)  # sensitivity, correlation, uncertainty
    metric_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "rainfall_sensitivity", "slope_correlation"

    # Sensitivity analysis (Q4)
    base_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Original parameter value
    perturbation_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 10% standard
    sensitivity_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # % change in output / % change in input
    parameter_importance_rank: Mapped[Optional[int]] = mapped_column(nullable=True)  # 1 = most important

    # Correlation analysis (Q1)
    correlation_coefficient: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Pearson r (-1 to 1)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    correlation_strength: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "weak", "moderate", "strong"
    correlated_factors: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # List of compared factors

    # Uncertainty quantification (Q4, Risk assessment)
    var_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Value at Risk 95%
    var_99: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Value at Risk 99%
    cvar_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Conditional VaR 95%
    cvar_99: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Conditional VaR 99%
    monte_carlo_iterations: Mapped[Optional[int]] = mapped_column(nullable=True)
    confidence_interval_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_interval_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Analysis details
    methodology: Mapped[str] = mapped_column(String, nullable=False)  # "one-at-a-time", "correlation", "monte-carlo"
    sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    distribution_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "normal", "lognormal", etc.

    # Results summary
    key_finding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Complete results
    detailed_data: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # Full metric output

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", backref="metrics")
    erosion_result: Mapped["ErosionResult"] = relationship("ErosionResult", backref="metrics")
    project: Mapped["Project"] = relationship("Project", backref="metrics")
    owner: Mapped["User"] = relationship("User", backref="metrics")
