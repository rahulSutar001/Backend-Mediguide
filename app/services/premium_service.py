"""
Premium subscription service
Handles subscription checks and usage tracking
"""
from typing import Optional
from datetime import datetime, timedelta
from app.supabase.client import get_supabase
from app.core.config import settings


class PremiumService:
    """Service for premium subscription management"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def check_subscription(self, user_id: str) -> bool:
        """
        Check if user has active premium subscription
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has premium, False otherwise
        """
        try:
            # Query subscriptions table
            response = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").limit(1).execute()
            
            if response.data and len(response.data) > 0:
                subscription = response.data[0]
                expires_at = subscription.get("expires_at")
                
                # Check if subscription hasn't expired
                if expires_at:
                    expires = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires < datetime.now(expires.tzinfo):
                        return False
                
                return True
            
            return False
        
        except Exception:
            # If subscription table doesn't exist or query fails, default to free
            return False
    
    async def get_usage_stats(self, user_id: str) -> dict:
        """
        Get usage statistics for current month
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with usage stats
        """
        is_premium = await self.check_subscription(user_id)
        
        # Get current month start
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Count reports created this month
            reports_response = self.supabase.table("reports").select(
                "id", count="exact"
            ).eq("user_id", user_id).gte(
                "created_at", month_start.isoformat()
            ).execute()
            
            reports_count = reports_response.count if reports_response.count else 0
            
            # Count family members
            family_response = self.supabase.table("family_connections").select(
                "id", count="exact"
            ).or_(
                f"user_id.eq.{user_id},connected_user_id.eq.{user_id}"
            ).eq("status", "connected").execute()
            
            family_count = family_response.count if family_response.count else 0
            
            return {
                "is_premium": is_premium,
                "reports_used_this_month": reports_count,
                "reports_limit": None if is_premium else settings.FREE_TIER_REPORTS_PER_MONTH,
                "family_members_count": family_count,
                "family_members_limit": None if is_premium else settings.FREE_TIER_FAMILY_MEMBERS,
            }
        
        except Exception as e:
            # Default values if query fails
            return {
                "is_premium": is_premium,
                "reports_used_this_month": 0,
                "reports_limit": None if is_premium else settings.FREE_TIER_REPORTS_PER_MONTH,
                "family_members_count": 0,
                "family_members_limit": None if is_premium else settings.FREE_TIER_FAMILY_MEMBERS,
            }
    
    async def check_report_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can create a new report (free tier limit)
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (can_create, error_message)
        """
        is_premium = await self.check_subscription(user_id)
        
        if is_premium:
            return (True, None)
        
        stats = await self.get_usage_stats(user_id)
        
        if stats["reports_used_this_month"] >= settings.FREE_TIER_REPORTS_PER_MONTH:
            return (
                False,
                f"Free tier limit reached ({settings.FREE_TIER_REPORTS_PER_MONTH} reports/month). Upgrade to premium for unlimited reports."
            )
        
        return (True, None)
    
    async def check_family_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can add a new family member (free tier limit)
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (can_add, error_message)
        """
        is_premium = await self.check_subscription(user_id)
        
        if is_premium:
            return (True, None)
        
        stats = await self.get_usage_stats(user_id)
        
        if stats["family_members_count"] >= settings.FREE_TIER_FAMILY_MEMBERS:
            return (
                False,
                f"Free tier limit reached ({settings.FREE_TIER_FAMILY_MEMBERS} family members). Upgrade to premium for unlimited family members."
            )
        
        return (True, None)
