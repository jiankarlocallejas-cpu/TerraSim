"""
Pydantic schemas for ErosionResult
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ErosionResultBase(BaseModel):
    """Base schema for erosion results"""
    simulation_name: str
    description: Optional[str] = None
    input_parameters: Dict[str, Any]


class ErosionResultCreate(ErosionResultBase):
    """Schema for creating erosion results"""
    analysis_id: int
    project_id: int
    status: str = "completed"


class ErosionResultUpdate(BaseModel):
    """Schema for updating erosion results"""
    simulation_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    mean_sediment_transport: Optional[float] = None
    mean_erosion_rate: Optional[float] = None
    max_erosion_rate: Optional[float] = None
    min_erosion_rate: Optional[float] = None
    std_erosion_rate: Optional[float] = None
    area_very_low: Optional[float] = None
    area_low: Optional[float] = None
    area_moderate: Optional[float] = None
    area_high: Optional[float] = None
    area_very_high: Optional[float] = None
    rusle_comparison_result: Optional[Dict[str, Any]] = None
    ha1_supported: Optional[str] = None
    uncertainty_metrics: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, float]] = None
    output_dem_path: Optional[str] = None
    output_risk_map_path: Optional[str] = None
    output_statistics_path: Optional[str] = None


class ErosionResultInDB(ErosionResultBase):
    """Schema for erosion results from database"""
    id: int
    analysis_id: int
    project_id: int
    owner_id: int
    status: str
    simulation_date: datetime
    processing_seconds: Optional[float] = None
    mean_sediment_transport: Optional[float] = None
    mean_erosion_rate: Optional[float] = None
    max_erosion_rate: Optional[float] = None
    min_erosion_rate: Optional[float] = None
    std_erosion_rate: Optional[float] = None
    area_very_low: Optional[float] = None
    area_low: Optional[float] = None
    area_moderate: Optional[float] = None
    area_high: Optional[float] = None
    area_very_high: Optional[float] = None
    rusle_comparison_result: Optional[Dict[str, Any]] = None
    ha1_supported: Optional[str] = None
    uncertainty_metrics: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class ErosionResultResponse(ErosionResultInDB):
    """Response schema for erosion results"""
    pass
