from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithDetails
from services.project_service import (
    get_projects,
    create_project,
    get_project,
    update_project,
    delete_project
)
from api.deps import get_current_active_user
from schemas.user import User

router = APIRouter()


@router.get("/", response_model=List[Project])
def read_projects(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve projects
    """
    projects = get_projects(db, owner_id=current_user.id, skip=skip, limit=limit)
    return projects


@router.post("/", response_model=Project)
def create_new_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create new project
    """
    return create_project(db=db, project=project_in, owner_id=current_user.id)


@router.get("/{project_id}", response_model=Project)
def read_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get project by ID
    """
    project = get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return project


@router.get("/{project_id}/details", response_model=ProjectWithDetails)
def read_project_details(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get project with all related data
    """
    project = get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    # Get related data
    from services.pointcloud_service import get_pointclouds
    from services.raster_service import get_rasters
    from services.analysis_service import get_analyses
    
    pointclouds = get_pointclouds(db, owner_id=current_user.id)
    rasters = get_rasters(db, owner_id=current_user.id)
    analyses = get_analyses(db, owner_id=current_user.id)
    
    return ProjectWithDetails(
        **project.__dict__,
        pointclouds=[pc.__dict__ for pc in pointclouds if pc.project_id == project_id],
        rasters=[r.__dict__ for r in rasters if r.project_id == project_id],
        analyses=[a.__dict__ for a in analyses if a.project_id == project_id]
    )


@router.put("/{project_id}", response_model=Project)
def update_project_by_id(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update project
    """
    project = get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    project = update_project(db, project_id=project_id, project=project_in)
    return project


@router.delete("/{project_id}")
def delete_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete project
    """
    project = get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    success = delete_project(db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete project")
    return {"message": "Project deleted successfully"}
