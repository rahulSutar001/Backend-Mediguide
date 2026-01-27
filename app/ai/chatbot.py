"""
Chatbot service for report-context aware Q&A
Strict safety constraints: NO diagnosis, NO prescriptions
"""
import json
from typing import List, Dict, Optional
from openai import OpenAI
from app.core.config import settings
from app.ai.prompts import (
    get_chatbot_system_prompt,
    check_for_diagnosis_request,
    CHATBOT_REFUSAL_RESPONSES
)
import random


class ChatbotService:
    """Service for chatbot conversations with safety constraints"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_response(
        self,
        message: str,
        report_id: str,
        report_type: str,
        parameters_summary: str,
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate chatbot response with safety checks
        
        Args:
            message: User message
            report_id: Report ID for context
            report_type: Type of report
            parameters_summary: Summary of test parameters
            chat_history: Previous conversation messages
        
        Returns:
            Bot response (safe, educational only)
        """
        # CRITICAL SAFETY CHECK: Refuse diagnosis/treatment requests
        if check_for_diagnosis_request(message):
            return random.choice(CHATBOT_REFUSAL_RESPONSES)
        
        # Build conversation context
        system_prompt = get_chatbot_system_prompt(report_type, parameters_summary)
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history if available
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": "user" if msg.get("role") == "user" else "assistant",
                    "content": msg.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                # Add safety constraints
                stop=["diagnosis", "prescribe", "treatment for you"]  # Stop if these words appear
            )
            
            bot_response = response.choices[0].message.content
            
            # Post-process: Additional safety check
            bot_response = self._sanitize_response(bot_response)
            
            return bot_response
        
        except Exception as e:
            # Fallback response
            return "I apologize, I'm having trouble processing your question. Please consult your doctor for medical advice."
    
    def _sanitize_response(self, response: str) -> str:
        """
        Sanitize response to remove any diagnosis/treatment language
        
        Args:
            response: Bot response
        
        Returns:
            Sanitized response
        """
        response_lower = response.lower()
        
        # Check for forbidden phrases
        forbidden_phrases = [
            "you have",
            "you are diagnosed",
            "you should take",
            "prescribe",
            "treatment is",
            "you need medication"
        ]
        
        for phrase in forbidden_phrases:
            if phrase in response_lower:
                # Replace with safe alternative
                return random.choice(CHATBOT_REFUSAL_RESPONSES)
        
        return response
