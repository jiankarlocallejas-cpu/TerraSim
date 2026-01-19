from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str  # erosion, sediment, etc.
    algorithm: str  # random_forest, neural_network, etc.
    parameters: Dict[str, Any] = {}


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    algorithm: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_trained: Optional[bool] = None


class Model(ModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_trained: bool = False
    model_path: Optional[str] = None
    metrics: Dict[str, float] = {}
    owner_id: int

    class Config:
        orm_mode = True


class ModelPrediction(BaseModel):
    prediction: Dict[str, Any]
    confidence: Optional[float] = None
    prediction_time: datetime


class ModelTraining(BaseModel):
    training_data_path: str
    validation_data_path: Optional[str] = None
    training_parameters: Dict[str, Any] = {}
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None


class ModelMetrics(BaseModel):
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    custom_metrics: Dict[str, float] = {}
