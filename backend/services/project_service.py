from typing import List, Optional
from sqlalchemy.orm import Session
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """Get a project by ID"""
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
    """Get a list of projects for a specific owner"""
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_project(db: Session, project: ProjectCreate, owner_id: int) -> Project:
    """Create a new project"""
    db_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        metadata=project.metadata,
        owner_id=owner_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(db: Session, project_id: int, project: ProjectUpdate) -> Optional[Project]:
    """Update a project"""
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        return None
    
    update_data = project.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """Delete a project"""
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True
