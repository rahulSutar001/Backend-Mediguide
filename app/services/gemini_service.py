
import os
import json
import google.generativeai as genai
from PIL import Image
import io
from app.core.config import settings

class GeminiService:
    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        # User requested "2.5 flash", likely meaning 1.5 Flash (current standard) or 2.0 Flash. 
        # Using 1.5 Flash for stability.
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_json(self, prompt: str) -> dict:
        """
        Generates a JSON response from the given prompt.
        """
        try:
            # Force JSON structure in prompt if not present
            if "JSON" not in prompt:
                prompt += "\n\nReturn strict JSON."
                
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"[ERROR] Gemini JSON generation failed: {e}")
            raise e

    def generate_text(self, prompt: str) -> str:
        """
        Generates a plain text response.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[ERROR] Gemini text generation failed: {e}")
            raise e

    def validate_medical_report(self, image_bytes: bytes) -> bool:
        """
        Validates if the image is a medical lab report.
        Returns True if medical, False otherwise.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            prompt = "Is this image a medical lab report or health document? Reply strictly with YES or NO."
            
            response = self.model.generate_content([prompt, image])
            answer = response.text.strip().upper()
            
            print(f"[DEBUG] Medical Validation: {answer}")
            return "YES" in answer
        except Exception as e:
            print(f"[ERROR] Medical validation failed: {e}")
            # Fail safe: Is valid (to avoid blocking on error), or fail secure?
            # User wants strict check. Let's assume False on error to be safe, or True to not block.
            # "fail secure" -> False.
            return False

    def analyze_medical_report(self, image_bytes: bytes) -> dict:
        """
        Analyzes a medical report image using Gemini 1.5 Flash and returns structured JSON data.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = """
            You are an expert medical AI assistant. Analyze this medical lab report image and extract the following information in strict JSON format:
            
            1.  **patient_name**: Name of the patient (or "Unknown").
            2.  **date**: Date of the report (YYYY-MM-DD format required. Return null if not found or ambiguous).
            3.  **lab_name**: Name of the laboratory/hospital.
            4.  **report_type**: Type of report (e.g., "CBC", "Lipid Profile", "Thyroid Profile").
            5.  **parameters**: A list of test results, where each item has:
                -   **name**: Name of the test/parameter.
                -   **value**: Measured value.
                -   **unit**: Unit of measurement (e.g., mg/dL).
                -   **normal_range**: Reference range provided in the report.
                -   **flag**: "high", "low", or "normal" based on the value and range.
                -   **explanation**: A simplified, easy-to-understand explanation of what this result means for the patient (1 sentence).
            6.  **summary**: A brief, friendly summary of the report for the patient (2-3 sentences).
            
            Return ONLY the valid JSON object. Do not include markdown code blocks or additional text.
            """

            response = self.model.generate_content([prompt, image])
            
            # Clean up response text to ensure it's valid JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())

        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            raise e

    def chat_with_report(self, report_context: str, user_question: str) -> str:
        """
        Answers user questions based on the report context using Gemini.
        """
        try:
            prompt = f"""
            Context: The user has uploaded a medical report with the following details:
            {report_context}
            
            User Question: {user_question}
            
            Answer the user's question accurately, helpful, and empathetic manner based ONLY on the provided context. 
            If the answer is not in the report, use general medical knowledge but clarify that it's general advice.
            Keep the answer concise and easy to understand.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Gemini Chat Error: {e}")
            raise e
