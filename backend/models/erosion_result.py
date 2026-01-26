"""
ErosionResult model - stores USPED-based erosion simulation results
"""
from sqlalchemy import String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from .base import Base, BaseModel

if TYPE_CHECKING:
    from .analysis import Analysis
    from .project import Project
    from .user import User


class ErosionResult(Base, BaseModel):
    """
    Stores results from USPED erosion simulations.
    One result per analysis run with complete output data.
    """
    __tablename__ = "erosion_results"

    # Relationships
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Simulation metadata
    simulation_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="completed")  # completed, failed, processing
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Temporal information
    simulation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    simulation_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    simulation_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Input parameters (stored as JSON for reference)
    input_parameters: Mapped[dict] = mapped_column(String, nullable=False)  # K, C, P, R, Q, A, beta, etc.

    # Main results
    mean_sediment_transport: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # T (kg/s)
    mean_erosion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # A (Mg/ha/yr)
    max_erosion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_erosion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    std_erosion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Risk classification results
    area_very_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km² in Very Low risk
    area_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km² in Low risk
    area_moderate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km² in Moderate risk
    area_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km² in High risk
    area_very_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km² in Very High risk

    # RUSLE comparison (Ha1 hypothesis testing)
    rusle_comparison_result: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # {t_stat, p_value, rmse, mae, nse}
    ha1_supported: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "yes", "no", "pending"

    # Uncertainty metrics
    uncertainty_metrics: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # {var_95, var_99, cvar_95, cvar_99}

    # Sensitivity analysis results
    sensitivity_analysis: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # {parameter: sensitivity_index, ...}

    # Output file paths/URIs
    output_dem_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Path to output DEM
    output_risk_map_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Path to risk classification
    output_statistics_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Path to statistics file

    # Raw results (large datasets as reference)
    raw_results: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # Complete output as JSON

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", backref="erosion_results")
    project: Mapped["Project"] = relationship("Project", backref="erosion_results")
    owner: Mapped["User"] = relationship("User", backref="erosion_results")
