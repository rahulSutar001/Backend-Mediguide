"""
Chat service for report-context aware chatbot
"""
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from app.supabase.client import get_supabase
from app.services.report_service import ReportService
from app.ai.chatbot import ChatbotService


class ChatService:
    """Service for chatbot conversations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.report_service = ReportService()
        self.chatbot_service = ChatbotService()
    
    async def send_message(
        self,
        user_id: str,
        report_id: str,
        message: str
    ) -> Dict:
        """Send a message and get chatbot response"""
        # Verify report ownership
        report = await self.report_service.get_report(report_id, user_id)
        if not report:
            raise ValueError("Report not found")
        
        # Get report parameters for context
        parameters = await self.report_service.get_report_parameters(report_id, user_id)
        parameters_summary = ", ".join([p.get("name", "") for p in parameters[:5]])
        
        # Get chat history
        history = await self.get_chat_history(report_id, user_id)
        
        # Generate response
        response_text = await self.chatbot_service.generate_response(
            message=message,
            report_id=report_id,
            report_type=report.get("type", "Unknown"),
            parameters_summary=parameters_summary,
            chat_history=history
        )
        
        # Save message and response
        message_id = str(uuid.uuid4())
        message_data = {
            "id": message_id,
            "report_id": report_id,
            "user_id": user_id,
            "message": message,
            "response": response_text,
            "created_at": datetime.now().isoformat()
        }
        
        self.supabase.table("chat_messages").insert(message_data).execute()
        
        return message_data
    
    async def get_chat_history(
        self,
        report_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get chat history for a report"""
        # Verify report ownership
        report = await self.report_service.get_report(report_id, user_id)
        if not report:
            return []
        
        # Get messages
        response = self.supabase.table("chat_messages").select("*").eq(
            "report_id", report_id
        ).eq("user_id", user_id).order(
            "created_at", desc=False
        ).limit(limit).execute()
        
        # Format for chatbot
        history = []
        for msg in (response.data or []):
            history.append({
                "role": "user",
                "content": msg.get("message", "")
            })
            history.append({
                "role": "assistant",
                "content": msg.get("response", "")
            })
        
        return history
