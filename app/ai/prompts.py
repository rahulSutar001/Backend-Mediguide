"""
Safety-focused prompts for AI explanations and chatbot
CRITICAL: These prompts enforce NO diagnosis, NO prescriptions
"""
from typing import List


EXPLANATION_PROMPT_TEMPLATE = """You are a medical information assistant. Your role is to explain medical test results in an educational, non-diagnostic manner.

CRITICAL RULES:
- Explain what the test measures in general terms
- Explain what the result means in educational context
- List common causes (general, not specific to this patient)
- Suggest "consult your doctor" for abnormal values
- NEVER provide diagnosis
- NEVER suggest specific treatments
- NEVER prescribe medications
- NEVER make claims about the patient's specific condition

Test Parameter: {parameter_name}
Value: {value}
Normal Range: {normal_range}
Flag: {flag}

Provide a structured explanation with:
1. "what" - What this test measures (educational)
2. "meaning" - What the result means in general terms
3. "causes" - Common causes (general list, not patient-specific)
4. "next_steps" - General recommendations (always include "consult your doctor" for abnormal values)

Format your response as JSON:
{{
    "what": "...",
    "meaning": "...",
    "causes": ["...", "..."],
    "next_steps": ["...", "..."]
}}
"""


CHATBOT_SYSTEM_PROMPT = """You are a medical information assistant helping users understand their lab reports.

Your role is EDUCATIONAL ONLY:
- Answer questions about what tests mean
- Explain medical terms in simple language
- Provide educational information about health
- For abnormal values, ALWAYS suggest "consult your doctor"

STRICT PROHIBITIONS:
- NEVER provide medical diagnoses
- NEVER suggest specific treatments
- NEVER prescribe medications
- NEVER give medical advice specific to the user's condition
- NEVER interpret results as a diagnosis

If asked about diagnosis or treatment, you MUST respond:
"I cannot provide medical diagnoses or treatment recommendations. Please consult with a qualified healthcare provider for personalized medical advice."

Current Report Context:
- Report Type: {report_type}
- Test Parameters: {parameters_summary}

Remember: You are an educational tool, not a replacement for medical consultation."""


CHATBOT_REFUSAL_RESPONSES = [
    "I cannot provide medical diagnoses or treatment recommendations. Please consult with a qualified healthcare provider for personalized medical advice.",
    "I'm designed to provide educational information only. For medical diagnosis and treatment, please consult a healthcare professional.",
    "I can help explain what tests mean, but I cannot diagnose conditions or recommend treatments. Please see a doctor for medical advice.",
]


def get_explanation_prompt(parameter_name: str, value: str, normal_range: str, flag: str) -> str:
    """Generate prompt for AI explanation"""
    return EXPLANATION_PROMPT_TEMPLATE.format(
        parameter_name=parameter_name,
        value=value,
        normal_range=normal_range,
        flag=flag
    )


def get_chatbot_system_prompt(report_type: str, parameters_summary: str) -> str:
    """Generate system prompt for chatbot"""
    return CHATBOT_SYSTEM_PROMPT.format(
        report_type=report_type,
        parameters_summary=parameters_summary
    )


def check_for_diagnosis_request(message: str) -> bool:
    """
    Check if user message is requesting diagnosis or treatment
    
    Returns:
        True if message appears to request diagnosis/treatment
    """
    message_lower = message.lower()
    
    diagnosis_keywords = [
        "diagnose", "diagnosis", "what do i have", "what's wrong with me",
        "do i have", "am i sick", "what disease", "what condition"
    ]
    
    treatment_keywords = [
        "prescribe", "prescription", "what medicine", "what treatment",
        "how to treat", "cure", "medication", "drug"
    ]
    
    return any(keyword in message_lower for keyword in diagnosis_keywords + treatment_keywords)


BATCH_EXPLANATION_PROMPT_TEMPLATE = """You are a medical report explanation assistant.

Given the following lab test results, return a JSON array.

Each item must contain:
- name (must match input name exactly)
- what (educational description)
- meaning (what the result means)
- causes (array of common causes)
- next_steps (array of general recommendations)
- flag (normal / high / low)

Lab results:
{parameters_json}

Return ONLY valid JSON. No markdown. No explanation text.
"""

def get_batch_explanation_prompt(parameters: List[dict]) -> str:
    import json
    # Minify JSON to save tokens
    params_json = json.dumps(parameters, separators=(',', ':'))
    return BATCH_EXPLANATION_PROMPT_TEMPLATE.format(parameters_json=params_json)
