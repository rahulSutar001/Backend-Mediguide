"""
Pydantic models for premium subscription
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Literal



class PremiumStatusResponse(BaseModel):
    """Response model for premium subscription status"""
    is_premium: bool
    subscription_tier: Literal['free', 'premium']
    expires_at: Optional[datetime] = None
    reports_used_this_month: int
    reports_limit: int
    family_members_count: int
    family_members_limit: int
