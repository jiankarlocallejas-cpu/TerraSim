from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from db.session import get_db
from schemas.analysis import AnalysisCreate, AnalysisResult, ErosionAnalysisParameters, ErosionAnalysisResults
from services.analysis_service import (
    create_analysis,
    get_analyses,
    get_analysis,
    run_analysis
)
from api.deps import get_current_active_user
from schemas.user import User

router = APIRouter()


@router.post("/", response_model=AnalysisResult)
def create_new_analysis(
    analysis_in: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create and run a new analysis
    """
    analysis = create_analysis(db=db, analysis=analysis_in, owner_id=current_user.id)
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return analysis


@router.post("/erosion", response_model=AnalysisResult)
def create_erosion_analysis(
    params: ErosionAnalysisParameters,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new erosion analysis
    """
    analysis_data = AnalysisCreate(
        name=f"Erosion Analysis - Point Cloud {params.pointcloud_id}",
        description="Erosion analysis using M3C2 algorithm",
        type="erosion",
        parameters=params.dict(),
        project_id=1  # This should come from the point cloud's project
    )
    
    analysis = create_analysis(db=db, analysis=analysis_data, owner_id=current_user.id)
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return analysis


@router.get("/", response_model=List[AnalysisResult])
def list_analyses(
    skip: int = 0, 
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all analyses for the current user
    """
    analyses = get_analyses(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Filter by project if specified
    if project_id is not None:
        analyses = [a for a in analyses if a.project_id == project_id]
    
    return analyses


@router.get("/{analysis_id}", response_model=AnalysisResult)
def get_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get analysis by ID
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return analysis


@router.get("/{analysis_id}/results")
def get_analysis_results(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed analysis results
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if analysis.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    return {
        "analysis_id": analysis_id,
        "results": analysis.results,
        "parameters": analysis.parameters
    }


@router.post("/{analysis_id}/rerun")
def rerun_analysis(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Rerun an analysis
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Reset status and run again
    from services.analysis_service import update_analysis
    update_analysis(db, analysis_id, {"status": "pending", "results": {}})
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return {"message": "Analysis rerun started"}


@router.delete("/{analysis_id}")
def delete_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete analysis
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from services.analysis_service import delete_analysis
    success = delete_analysis(db, analysis_id=analysis_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete analysis")
    return {"message": "Analysis deleted successfully"}
