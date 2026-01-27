"""
FastAPI dependencies for dependency injection
"""
from fastapi import Depends, HTTPException, status
from typing import Optional
from app.core.security import get_current_user, get_supabase_client
from app.services.premium_service import PremiumService


async def get_user_id(user: dict = Depends(get_current_user)) -> str:
    """Extract user_id from authenticated user"""
    return user["user_id"]


async def require_premium(
    user_id: str = Depends(get_user_id)
) -> bool:
    """
    Dependency to enforce premium subscription requirement
    
    Raises:
        HTTPException: 403 if user is not premium
    """
    premium_service = PremiumService()
    is_premium = await premium_service.check_subscription(user_id)
    
    if not is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PREMIUM_REQUIRED",
                "message": "This feature requires a premium subscription",
                "code": "PREMIUM_REQUIRED"
            }
        )
    
    return True


def get_supabase_dependency(use_service_role: bool = False):
    """Dependency to get Supabase client"""
    return get_supabase_client(use_service_role=use_service_role)
