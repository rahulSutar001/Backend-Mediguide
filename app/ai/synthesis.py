"""
AI Service for synthesizing medical reports and identifying trends
"""
import json
from typing import Dict, List, Optional
from typing import Dict, List, Optional
from app.core.config import settings

class SynthesisService:
    """Service for generating comprehensive medical syntheses"""

    def __init__(self):
        from app.services.gemini_service import GeminiService
        self.gemini = GeminiService()

    def _minify_report_data(self, report: Dict) -> Dict:
        """Extract only essential data for AI processing to save tokens"""
        # Minimal parameters: name, value, unit, flag
        minified_params = []
        for p in report.get("parameters", []):
            minified_params.append({
                "n": p.get("name"), # Shorten keys
                "v": p.get("value"),
                "u": p.get("unit"),
                "f": p.get("flag")
            })
            
        return {
            "d": report.get("date") or report.get("created_at"), # d = date
            "t": report.get("type"), # t = type
            "p": minified_params # p = parameters
        }

    async def generate_synthesis(
        self, 
        current_report: Dict, 
        related_reports: List[Dict]
    ) -> Dict[str, any]:
        """
        Generate a synthesis of the current report in context of history.
        """
        
        # Prepare context data (Minified)
        history_context = [self._minify_report_data(r) for r in related_reports]
        current_data = self._minify_report_data(current_report)

        # Combined Prompt for Gemini
        prompt = f"""
        You are an expert medical AI assistant helping a doctor review patient history.
        Your goal is to synthesize the CURRENT report findings in the context of PAST reports.
        Identify what has changed, improved, or worsened.
        Input data is minified: d=date, t=type, p=parameters (n=name, v=value, u=unit, f=flag).
        
        CURRENT REPORT:
        {json.dumps(current_data, separators=(',', ':'))}

        HISTORY:
        {json.dumps(history_context, separators=(',', ':'))}

        TASK:
        1. Summarize the user's current health status based on this report.
        2. Identify key trends (e.g., "Hemoglobin has increased from 11.2 to 12.5").
        3. Write a "Doctor's Précis" - a concise, professional summary for a GP.

        RETURN STRICT JSON FORMAT:
        {{
            "status_summary": "1-2 sentences on current status",
            "key_trends": ["trend 1", "trend 2"],
            "doctor_precis": "Paragraph for the doctor"
        }}
        """

        try:
            return self.gemini.generate_json(prompt)

        except Exception as e:
            print(f"[ERROR] Synthesis generation failed: {e}")
            return {
                "status_summary": "Could not generate synthesis.",
                "key_trends": [],
                "doctor_precis": "AI Synthesis unavailable."
            }
