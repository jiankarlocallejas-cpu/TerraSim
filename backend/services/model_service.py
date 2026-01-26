import os
import json
import pickle
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User
from schemas.model import Model, ModelCreate, ModelUpdate, ModelTraining, ModelMetrics

logger = logging.getLogger(__name__)


def get_model(db: Session, model_id: int) -> Optional[Model]:
    """Get a model by ID"""
    return db.query(Model).filter(Model.id == model_id).first()


def get_models(db: Session, skip: int = 0, limit: int = 100) -> List[Model]:
    """Get a list of models"""
    return db.query(Model).offset(skip).limit(limit).all()


def create_model(db: Session, model: ModelCreate, owner_id: int) -> Model:
    """Create a new model"""
    db_model = Model(
        name=model.name,
        description=model.description,
        model_type=model.model_type,
        algorithm=model.algorithm,
        parameters=model.parameters,
        owner_id=owner_id,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def update_model(db: Session, model_id: int, model: ModelUpdate) -> Optional[Model]:
    """Update a model"""
    db_model = get_model(db, model_id=model_id)
    if not db_model:
        return None
    
    update_data = model.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, model_id: int) -> bool:
    """Delete a model"""
    db_model = get_model(db, model_id=model_id)
    if not db_model:
        return False
    
    # Delete the model file if it exists
    if db_model.model_path and os.path.exists(db_model.model_path):
        os.remove(db_model.model_path)
    
    db.delete(db_model)
    db.commit()
    return True


def train_model(model_id: int, config: Dict[str, Any]) -> bool:
    """Train a model"""
    # This is a placeholder for model training
    # In a real implementation, this would:
    # 1. Load training data
    # 2. Initialize the model based on algorithm
    # 3. Train the model with specified parameters
    # 4. Save the trained model
    # 5. Calculate and store metrics
    
    logger.info(f"Training model {model_id} with config: {config}")
    
    # Simulate training
    import time
    time.sleep(2)  # Simulate training time
    
    return True


def predict(model_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a prediction using a trained model"""
    # This is a placeholder for prediction
    # In a real implementation, this would:
    # 1. Load the trained model
    # 2. Preprocess input data
    # 3. Make prediction
    # 4. Postprocess results
    
    logger.info(f"Making prediction with model {model_id}")
    
    # Simulate prediction
    prediction = {
        "erosion_risk": 0.5,
        "sediment_yield": 100.0,
        "confidence": 0.85
    }
    
    return prediction


def save_model(model_object: Any, file_path: str) -> bool:
    """Save a trained model to disk"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            pickle.dump(model_object, f)
        return True
    except Exception as e:
        logger.error(f"Error saving model: {str(e)}")
        return False


def load_model(file_path: str) -> Optional[Any]:
    """Load a trained model from disk"""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None
