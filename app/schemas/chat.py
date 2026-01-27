"""
Pydantic models for chatbot requests and responses
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessageRequest(BaseModel):
    """Request model for sending chat message"""
    message: str
    report_id: str


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    id: str
    report_id: str
    user_id: str
    message: str
    response: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    messages: List[ChatMessageResponse]
    total: int
