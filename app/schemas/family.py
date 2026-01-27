"""
Pydantic models for family connection requests and responses
"""
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class FamilyMemberResponse(BaseModel):
    """Response model for family member"""
    connection_id: str
    user_id: str
    display_name: Optional[str] = None
    profile_name: Optional[str] = None
    phone: Optional[str] = None
    status: str
    connection_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class InviteFamilyRequest(BaseModel):
    """Request model for inviting family member"""
    email: Optional[str] = None
    phone_number: Optional[str] = None
    nickname: Optional[str] = None


class AcceptConnectionRequest(BaseModel):
    """Request model for accepting connection"""
    display_name: Optional[str] = None


class RenameConnectionRequest(BaseModel):
    """Request model for renaming a connection"""
    display_name: str
