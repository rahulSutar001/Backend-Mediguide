"""
Chatbot Service - Core logic for MediBot
Highlights:
- Context assembly from report data
- Strict safety prompt construction
- Gemini interaction
"""
import json
from typing import Dict, List, Optional
from app.core.config import settings

# Strict System Prompt
# Derived from user requirements for safety and isolation
MEDIBOT_SYSTEM_PROMPT = """You are MediBot, a helpful and strictly informational AI assistant inside the MediGuide app.
Your goal is help users understand their medical reports based on the provided structured data.

CONSTRAINTS:
1. ANSWER ONLY BASED ON THE PROVIDED CONTEXT. Do not use outside knowledge unless it is general medical definition.
2. If the user asks about something not in the report, politely refuse.

CONTEXT:
You will be provided with:
1. REPORT_METADATA: Type of report, date, lab name.
2. PARAMETERS: A list of medical result values, units, flags (High/Low/Normal), and reference ranges.
3. EXPLANATIONS: Pre-generated educational explanations for these parameters.

STRICT SAFETY RULES (NON-NEGOTIABLE):
1. NOT A DOCTOR: You are an AI, not a medical professional. Do NOT diagnose medical conditions. Do NOT prescribe medications or treatments.
2. NO "YOU HAVE": Never say "You have [condition]". Instead say "This value suggests..." or "Elevated levels can be associated with...".
3. NO "YOU SHOULD": Never give personal medical advice (e.g., "You should take iron supplements"). Instead say "Standard treatments for this often include... but consult your doctor."
4. REFER TO DOCTOR: For any decision-making, diagnosis, or treatment question, explicitly advise the user to consult a doctor.
5. REFUSAL: If the user asks "Do I have cancer?" or "What medicine should I take?", you MUST refuse to answer and redirect to a professional.

TONE:
- Professional, empathetic, simplified, and educational.
- Avoid jargon where possible, or explain it.

INPUT:
The user's question and the JSON context of the report.

OUTPUT:
A clear, safe text response.
"""

class ChatbotService:
    def __init__(self):
        from app.services.gemini_service import GeminiService
        self.gemini = GeminiService()

    async def generate_response(
        self, 
        question: str, 
        report_data: Dict, 
        parameters: List[Dict], 
        explanations: List[Dict]
    ) -> str:
        """
        Generates a safe response to the user's question given the report context using Gemini.
        """
        
        # 1. Pre-check for obviously unsafe keywords (Rule-based safety layer)
        unsafe_keywords = ["prescribe", "medication for me", "diagnose me", "do i have cancer", "am i dying"]
        q_lower = question.lower()
        if any(k in q_lower for k in unsafe_keywords):
            return "I am an AI assistant and cannot provide medical diagnoses or prescribe medication. Please consult a qualified doctor for personal medical advice and treatment options."

        # 2. Build Context String
        context_str = self._build_context_json(report_data, parameters, explanations)
        
        # 3. Call Gemini
        # We enforce the system prompt by prepending it to the context or relying on GeminiService's internal handling.
        # Ideally, we pass the system prompt to GeminiService, but GeminiService.chat_with_report currently takes context + question.
        # Let's rely on chat_with_report but passing the strict system prompt as part of the context block or modifying GeminiService.
        # Given constraints, I'll prepend the system prompt to the context being sent.
        
        full_prompt = f"{MEDIBOT_SYSTEM_PROMPT}\n\nCONTEXT:\n{context_str}"
        
        try:
            return self.gemini.chat_with_report(full_prompt, question)
        except Exception as e:
            print(f"[ERROR] Chatbot Gemini Call failed: {e}")
            return "I'm having trouble connecting to my knowledge base right now. Please try again later."

    def _build_context_json(self, report: Dict, params: List[Dict], explanations: List[Dict]) -> str:
        """Helper to format data for the LLM"""
        
        # Contextualize: Map explanations to parameters if possible
        clean_params = []
        for p in params:
            item = {
                "name": p.get("name"),
                "value": p.get("value"),
                "unit": p.get("unit"),
                "ref_range": p.get("range") or p.get("normal_range"),
                "flag": p.get("flag"),
            }
            # Try to find explanation
            expl = next((e for e in explanations if e.get("parameter_id") == p.get("id")), None)
            if expl:
                item["explanation_meaning"] = expl.get("meaning")
            
            clean_params.append(item)
            
        context = {
            "report_metadata": {
                "type": report.get("type"),
                "date": report.get("date"),
                "lab": report.get("lab_name"),
                "overall_flag": report.get("flag_level")
            },
            "parameters": clean_params
        }
        
        return json.dumps(context, indent=2)

    def _build_context_json(self, report: Dict, params: List[Dict], explanations: List[Dict]) -> str:
        """Helper to format data for the LLM"""
        
        # Contextualize: Map explanations to parameters if possible
        # note: param dicts might already have expanded info if fetched via get_report_parameters
        
        clean_params = []
        for p in params:
            # Check if explanation is already embedded (if service layer did it) or try to match
            # For simplicity, we create a flat list of param info
            item = {
                "name": p.get("name"),
                "value": p.get("value"),
                "unit": p.get("unit"),
                "ref_range": p.get("range") or p.get("normal_range"),
                "flag": p.get("flag"),
            }
            # Try to find explanation
            # Explanation list usually has parameter_id
            expl = next((e for e in explanations if e.get("parameter_id") == p.get("id")), None)
            if expl:
                item["explanation_meaning"] = expl.get("meaning")
            
            clean_params.append(item)
            
        context = {
            "report_metadata": {
                "type": report.get("type"),
                "date": report.get("date"),
                "lab": report.get("lab_name"),
                "overall_flag": report.get("flag_level")
            },
            "parameters": clean_params
        }
        
        return json.dumps(context, indent=2)
