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
        self.model = genai.GenerativeModel("gemini-2.5-flash")

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
            self.model = genai.GenerativeModel("gemini-2.5-flash")

            prompt = """
            You are an expert medical AI assistant. Analyze this medical lab report image and extract the following information in strict JSON format:
            
            1.  **patient_name**: Name of the patient. Return null if not explicitly found. DO NOT guess or return "Unknown".
            2.  **patient_age**: Age of the patient. Look for labels like "Age", "Age / Gender", "Age/Sex", "Age (Yrs)". 
                - If you see "Age / Gender : 20 Yrs / Female", extract "20 Yrs" exactly. 
                - Include the unit if present (e.g., "20 Yrs", "20 Years"). 
                - Return strictly text as seen. Return null if not explicitly found.
            3.  **patient_sex**: Sex/Gender. Look for labels like "Gender", "Sex", "Age / Gender".
                - If you see "Age / Gender : 20 Yrs / Female", extract "Female" exactly.
                - Return strictly text as seen (e.g., "Male", "Female", "M", "F"). Return null if not explicitly found.
            4.  **date**: Date of the report (YYYY-MM-DD format required. Return null if not found or ambiguous).
            5.  **lab_name**: Name of the laboratory/hospital.
            6.  **report_type**: Type of report (e.g., "CBC", "Lipid Profile", "Thyroid Profile").
            7.  **overall_health_indication**: A one-word status of the report (e.g., "Normal", "Mildly Abnormal", "Attention Required").
            8.  **clinical_summary**: A concise, holistic clinical summary of the entire report for the patient.
                - Explain the overall health indication.
                - Reassure the user where results are normal.
                - Briefly mention areas that might need attention without being alarming.
                - Use very simple English (10th-grade level).
                - Tone: Calm, professional, reassuring.
            9.  **parameters**: A list of test results, where each item has:
                -   **name**: Name of the test/parameter.
                -   **value**: Measured value.
                -   **unit**: Unit of measurement (e.g., mg/dL).
                -   **normal_range**: Reference range provided in the report.
                -   **flag**: "high", "low", or "normal" based on the value and range.
                -   **category**: The physiological system or category this test belongs to (e.g., "Blood Counts", "White Blood Cell Profile", "Liver Function", "Kidney Function").
                -   **explanation**: A conceptual explanation of the test.
                    -   Explain WHAT the test measures.
                    -   Explain WHY it is important.
                    -   Explain what a NORMAL result generally means.
                    -   MUST NOT repeat the reference range.
                    -   MUST NOT use medical jargon.
            10. **system_summaries**: A list of objects summarizing groups of parameters:
                -   **category**: The category name (e.g., "Blood Counts").
                -   **status**: "Normal" or "Attention Required".
                -   **description**: A brief (1-2 sentence) explanation of what these results mean for that system. Use reassurance for normal systems.
            11. **normal_values_summary**: A single, reassuring paragraph summarizing all the parameters that are within normal range.
                - Mention the key systems/categories that are healthy (e.g., "Your Kidney Function and Electrolytes are within normal limits").
                - Do not list every single parameter.
                - Keep it concise and encouraging. 
            12. **summary**: A brief, friendly 2-3 sentence overview for the home screen.
            
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
