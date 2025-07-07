"""
Authentication router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    LoginResponse,
    MessageResponse,
    UserResponse,
)
from app.crud import get_user_by_email, create_user, authenticate_user
from app.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password_strength,
)
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()
security = HTTPBearer()


@router.post(
    "/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    # Check if passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    # Validate password strength
    if not validate_password_strength(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character",
        )

    # Check if user already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    create_user(db=db, user=user)
    return MessageResponse(message="User registered successfully")


@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return tokens"""

    # Authenticate user
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify refresh token
        email = verify_token(credentials.credentials, token_type="refresh")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Get user from database
    user = get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    # Create new access token
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should discard tokens)"""
    return MessageResponse(message="Successfully logged out")
