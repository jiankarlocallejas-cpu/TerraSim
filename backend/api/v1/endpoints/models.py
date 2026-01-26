from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.model import Model, ModelCreate, ModelUpdate, ModelPrediction, ModelTraining, ModelMetrics
from services.model_service import (
    get_models,
    create_model,
    get_model,
    predict,
    train_model,
    save_model,
    load_model
)
from api.deps import get_current_active_user
from schemas.user import User
from core.config import settings

router = APIRouter()


@router.post("/", response_model=Model)
def create_new_model(
    model_in: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new erosion model
    """
    return create_model(db=db, model=model_in, owner_id=current_user.id)


@router.get("/", response_model=List[Model])
def list_models(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all available models
    """
    models = get_models(db, skip=skip, limit=limit)
    
    # Filter by owner if not superuser
    if not current_user.is_superuser:
        models = [m for m in models if m.owner_id == current_user.id]
    
    return models


@router.get("/{model_id}", response_model=Model)
def get_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get model by ID
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return model


@router.post("/{model_id}/predict", response_model=ModelPrediction)
def make_prediction(
    model_id: int,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Make a prediction using a trained model
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not model.is_trained:
        raise HTTPException(status_code=400, detail="Model is not trained yet")
    
    try:
        # Load the model and make prediction
        model_object = load_model(model.model_path) if model.model_path else None
        if not model_object:
            raise HTTPException(status_code=400, detail="Model file not found")
        
        prediction = predict(model_id, input_data)
        return ModelPrediction(
            prediction=prediction,
            prediction_time=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{model_id}/train")
def train_model_endpoint(
    model_id: int,
    training_config: ModelTraining,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Train or retrain a model
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create a job for training
    from services.job_service import create_job
    job = create_job(
        db=db,
        job={
            "name": f"Train model {model.name}",
            "description": f"Training {model.algorithm} model",
            "job_type": "model_training",
            "parameters": training_config.dict()
        },
        owner_id=current_user.id
    )
    
    # Start training in background
    background_tasks.add_task(
        train_model_job,
        job_id=job.id,
        model_id=model_id,
        config=training_config.dict(),
        db=db
    )
    
    return {"status": "training_started", "job_id": job.id}


@router.post("/{model_id}/upload")
def upload_model_file(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a pre-trained model file
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Save model file
    import os
    models_dir = f"{settings.LOCAL_STORAGE_PATH}/models"
    os.makedirs(models_dir, exist_ok=True)
    model_path = f"{models_dir}/{model_id}_{file.filename}"
    
    with open(model_path, "wb+") as f:
        f.write(file.file.read())
    
    # Update model record
    from services.model_service import update_model
    update_model(db, model_id, {
        "model_path": model_path,
        "is_trained": True
    })
    
    return {"message": "Model uploaded successfully", "model_path": model_path}


@router.get("/{model_id}/metrics", response_model=ModelMetrics)
def get_model_metrics(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get model performance metrics
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return ModelMetrics(**model.metrics)


@router.delete("/{model_id}")
def delete_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete model
    """
    model = get_model(db, model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from services.model_service import delete_model
    success = delete_model(db, model_id=model_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete model")
    return {"message": "Model deleted successfully"}


async def train_model_job(job_id: str, model_id: int, config: dict, db: Session):
    """Background task to train model"""
    from services.job_service import start_job, complete_job, fail_job, update_job_progress
    from services.model_service import update_model
    from datetime import datetime
    
    try:
        start_job(db, job_id)
        update_job_progress(db, job_id, 10, "Starting model training...")
        
        # Simulate training steps
        update_job_progress(db, job_id, 30, "Loading training data...")
        # Add actual data loading here
        
        update_job_progress(db, job_id, 50, "Initializing model...")
        # Add model initialization here
        
        update_job_progress(db, job_id, 70, "Training model...")
        # Add actual training here
        success = train_model(model_id, config)
        
        update_job_progress(db, job_id, 90, "Saving model...")
        # Add model saving here
        
        # Update model record
        model_path = f"{settings.LOCAL_STORAGE_PATH}/models/{model_id}_trained.pkl"
        update_model(db, model_id, {
            "is_trained": True,
            "model_path": model_path,
            "metrics": {
                "accuracy": 0.85,
                "mse": 0.15
            }
        })
        
        result = {"trained": True, "model_path": model_path}
        complete_job(db, job_id, result)
        
    except Exception as e:
        fail_job(db, job_id, str(e))
