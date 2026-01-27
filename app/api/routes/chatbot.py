"""
Chatbot API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.chatbot_service import ChatbotService
from app.services.report_service import ReportService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    report_id: str
    question: str

class ChatResponse(BaseModel):
    response: str

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    payload: ChatRequest,
    request: Request,

    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    """
    Ask MediBot a question about a report.
    """
    # 1. Initialize Services
    report_service = ReportService(request)
    chatbot_service = ChatbotService()
    
    # 2. Verify Access & Fetch Data
    # get_report checks ownership/family access internally
    report = await report_service.get_report(payload.report_id, user_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Report not found or you do not have permission to view it"
        )
        
    # 3. Fetch Context (Parameters & Explanations)
    # Note: Optimization - we could make a dedicated method in ReportService to fetch all in one DB call,
    # but for v1 reusing existing methods is safer and cleaner as requested ("Do NOT refactor existing code")
    parameters = await report_service.get_report_parameters(payload.report_id, user_id)
    explanations = await report_service.get_report_explanations(payload.report_id, user_id)
    
    # 4. Generate Response
    answer = await chatbot_service.generate_response(
        question=payload.question,
        report_data=report,
        parameters=parameters,
        explanations=explanations
    )
    
    return ChatResponse(response=answer)
