"""
Premium subscription API routes
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_user_id
from app.services.premium_service import PremiumService
from app.schemas.premium import PremiumStatusResponse

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/status", response_model=PremiumStatusResponse)
async def get_premium_status(
    user_id: str = Depends(get_user_id)
):
    """Get premium subscription status and usage"""
    service = PremiumService()
    is_premium = await service.check_subscription(user_id)
    stats = await service.get_usage_stats(user_id)
    
    return PremiumStatusResponse(
        is_premium=is_premium,
        subscription_tier="premium" if is_premium else "free",
        expires_at=None,  # Could be fetched from subscription table
        reports_used_this_month=stats["reports_used_this_month"],
        reports_limit=stats["reports_limit"],
        family_members_count=stats["family_members_count"],
        family_members_limit=stats["family_members_limit"]
    )
