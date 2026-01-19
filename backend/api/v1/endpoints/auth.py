from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from core.security import create_access_token
from core.config import settings
from db.session import get_db
from schemas.token import Token
from schemas.user import User
from services.user_service import authenticate_user, get_user_by_email, create_user
from api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register(
    email: str,
    password: str,
    full_name: str = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    # Check if user already exists
    user = get_user_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    # Create new user
    from schemas.user import UserCreate
    user_in = UserCreate(
        email=email,
        password=password,
        full_name=full_name
    )
    user = create_user(db, user=user_in)
    return user


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user
