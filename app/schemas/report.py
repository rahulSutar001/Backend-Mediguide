"""
Pydantic models for report-related requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# Request Models
class ReportUploadRequest(BaseModel):
    """Request model for report upload"""
    report_type: Optional[str] = Field(None, description="Report type (auto-detected if not provided)")
    # Note: image file is handled separately via FormData


class ReportListRequest(BaseModel):
    """Request model for listing reports with filters"""
    search: Optional[str] = None
    report_type: Optional[str] = None
    flag_level: Optional[Literal['green', 'yellow', 'red']] = None
    time_range: Optional[Literal['7d', '30d', '90d', 'all']] = 'all'
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class CompareReportsRequest(BaseModel):
    """Request model for comparing two reports"""
    report_id_1: str
    report_id_2: str
    parameter_name: Optional[str] = Field(None, description="Compare specific parameter (optional)")


# Response Models
class ReportResponse(BaseModel):
    """Response model for report details"""
    id: str
    user_id: str
    date: Optional[str] = None
    type: str
    lab_name: Optional[str] = None
    flag_level: Literal['green', 'yellow', 'red']
    uploaded_to_abdm: bool = False
    status: Literal['processing', 'completed', 'failed']
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestParameterResponse(BaseModel):
    """Response model for test parameter with explanation"""
    id: str
    report_id: str
    name: str
    value: str
    unit: Optional[str] = None
    normal_range: str
    range: Optional[str] = None
    flag: Literal['normal', 'high', 'low']
    explanation: Optional['ExplanationResponse'] = None
    
    class Config:
        from_attributes = True


class ExplanationResponse(BaseModel):
    """Response model for AI-generated explanation"""
    id: str
    parameter_id: str
    what: str
    meaning: str
    causes: List[str]
    next_steps: List[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ReportStatusResponse(BaseModel):
    """Response model for report processing status"""
    report_id: str
    status: Literal['processing', 'completed', 'failed']
    progress: Optional[int] = Field(None, ge=0, le=100, description="Processing progress percentage")
    error_message: Optional[str] = None


class ReportUploadResponse(BaseModel):
    """Response model for report upload"""
    report_id: str
    status: str
    message: str


# Update forward references
TestParameterResponse.model_rebuild()
ExplanationResponse.model_rebuild()
