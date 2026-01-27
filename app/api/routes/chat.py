"""
Chatbot API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_user_id
from app.services.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/reports/{report_id}/message", response_model=ChatMessageResponse)
async def send_message(
    report_id: str,
    request: ChatMessageRequest,
    user_id: str = Depends(get_user_id)
):
    """Send a message to the chatbot"""
    if request.report_id != report_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report ID mismatch"
        )
    
    service = ChatService()
    try:
        message_data = await service.send_message(
            user_id=user_id,
            report_id=report_id,
            message=request.message
        )
        return ChatMessageResponse(**message_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/reports/{report_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    report_id: str,
    user_id: str = Depends(get_user_id)
):
    """Get chat history for a report"""
    service = ChatService()
    history = await service.get_chat_history(report_id, user_id)
    
    return ChatHistoryResponse(
        messages=[ChatMessageResponse(**msg) for msg in history],
        total=len(history)
    )
