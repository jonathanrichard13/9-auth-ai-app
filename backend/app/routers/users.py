"""
Users router
"""

from fastapi import APIRouter, Depends
from app.schemas import UserResponse
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse.model_validate(current_user)
