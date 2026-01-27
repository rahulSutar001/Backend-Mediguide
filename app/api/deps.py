"""
Shared API dependencies
"""
from fastapi import Depends
from app.core.dependencies import get_user_id

# Re-export for convenience
__all__ = ["get_user_id"]
