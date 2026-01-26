from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.user import User, UserCreate, UserUpdate
from services.user_service import (
    get_users, 
    create_user, 
    get_user, 
    update_user, 
    delete_user,
    get_user_by_email
)
from api.deps import get_current_active_superuser

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Retrieve users (admin only)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Create new user (admin only)
    """
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = create_user(db, user=user_in)
    return user


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Get a specific user by id (admin only)
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user does not exist in the system",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user_by_id(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Update a user (admin only)
    """
    user = update_user(db, user_id=user_id, user=user_in)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user does not exist in the system",
        )
    return user


@router.delete("/{user_id}")
def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Delete a user (admin only)
    """
    success = delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="The user does not exist in the system",
        )
    return {"message": "User deleted successfully"}
