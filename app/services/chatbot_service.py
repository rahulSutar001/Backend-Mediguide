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
from groq import Groq

# Strict System Prompt
# Derived from user requirements for safety and isolation
MEDIBOT_SYSTEM_PROMPT = """You are MediBot, a helpful AI assistant in the MediGuide app.
Goal: Help users understand medical reports based on provided data.

CONSTRAINTS:
1. ANSWER ONLY BASED ON CONTEXT.
2. Polite refusal for off-topic questions.
3. FORMATTING:
   - Use standard Markdown.
   - **NEVER** put spaces inside bold asterisks (e.g., use **Correct**, NOT ** Incorrect**).
   - If bolding causes issues, use plain text.

CONTEXT:
Metadata, Parameters (values, units, flags), and Explanations.

STRICT SAFETY RULES:
1. NOT A DOCTOR. No diagnosis or treatment advice.
2. NO "YOU HAVE". Use "This value suggests..." or "Elevated levels...".
3. NO "YOU SHOULD". No personal advice.
4. REFER TO DOCTOR for all decision-making.
5. REFUSE to answer "Do I have cancer?" etc.

TONE & STYLE:
- EXTREMELY CONCISE.
- Max 1-2 sentences per point.
- No conversational filler ("Here is the info...", "I hope this helps").
- Just the facts.

INPUT: User question + Report JSON.
OUTPUT: Short, safe text response.
"""


class ChatbotService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    async def generate_response(
        self,
        question: str,
        report_data: Dict,
        parameters: List[Dict],
        explanations: List[Dict],
    ) -> str:
        """
        Generates a safe response to the user's question given the report context using Groq.
        """

        # 1. Pre-check for obviously unsafe keywords (Rule-based safety layer)
        unsafe_keywords = [
            "prescribe",
            "medication for me",
            "diagnose me",
            "do i have cancer",
            "am i dying",
        ]
        q_lower = question.lower()
        if any(k in q_lower for k in unsafe_keywords):
            return "I am an AI assistant and cannot provide medical diagnoses or prescribe medication. Please consult a qualified doctor for personal medical advice and treatment options."

        # 2. Build Context String
        context_str = self._build_context_json(
            report_data, parameters, explanations
        )

        # 3. Call Groq
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": MEDIBOT_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{question}",
                    },
                ],
                model=settings.GROQ_MODEL,
                temperature=0.3,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Chatbot Groq Call failed: {e}")
            return "I'm having trouble connecting to my knowledge base right now. Please try again later."

    def _build_context_json(
        self, report: Dict, params: List[Dict], explanations: List[Dict]
    ) -> str:
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
            expl = next(
                (
                    e
                    for e in explanations
                    if e.get("parameter_id") == p.get("id")
                ),
                None,
            )
            if expl:
                item["explanation_meaning"] = expl.get("meaning")

            clean_params.append(item)

        context = {
            "report_metadata": {
                "type": report.get("type"),
                "date": report.get("date"),
                "lab": report.get("lab_name"),
                "overall_flag": report.get("flag_level"),
            },
            "parameters": clean_params,
        }

        return json.dumps(context, indent=2)
