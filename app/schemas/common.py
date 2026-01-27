"""
Common Pydantic models for error responses and shared types
"""
from pydantic import BaseModel
from typing import Optional, Literal


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool
