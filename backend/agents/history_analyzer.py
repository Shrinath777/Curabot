from typing import Dict, Any, List
import json
from services.llm_client import llm_client

class PatientHistoryAnalyzer:
    """
    Analyzes a returning patient's past chat history, diagnoses, and severity trends 
    to establish a 'Clinical Baseline Report' before diagnosing the current issue.
    """

    def __init__(self):
        self.system_instructions = (
            "You are a clinical history analysis AI."
            "Your job is to read the patient's uploaded medical records (found in 'extracted_medical_records'), past diagnoses, and severity history."
            "First, determine if their current complaint is a recurrence, complication, or related to a past issue from their structured records or PDF lab reports. "
            "If it is related, you MUST use your medical knowledge to formulate a dynamic, disease-specific follow-up question. "
            "This question should reference specific lab values, surgical history, or past medications found in the 'extracted_medical_records' or history to make the analysis feel precise and personalized. "
            "Return a concise JSON object containing: "
            "{'is_recurrence': bool, 'suspected_recurring_condition': str or null, 'dynamic_severity_question': str or null, 'severity_change': 'worsened' | 'improved' | 'same' | 'new', 'clinical_baseline_summary': str}"
        )

    async def analyze(self, user_context: Dict[str, Any], current_message: str) -> Dict[str, Any]:
        """Generate the clinical baseline summary based on past data."""
        if not user_context or not user_context.get("is_returning_user"):
            return {
                "is_recurrence": False, 
                "suspected_recurring_condition": None, 
                "dynamic_severity_question": None,
                "severity_change": "new", 
                "clinical_baseline_summary": "First-time user or no historical context available."
            }

        past_history_str = json.dumps({
            "severity_history": user_context.get("severity_history", []),
            "recurring_conditions": user_context.get("recurring_conditions", []),
            "medical_reports": [{"type": r.get("report_type"), "date": r.get("uploaded_at")} for r in user_context.get("medical_reports", [])],
            "recent_conversations": [{"title": c["title"]} for c in user_context.get("recent_conversations", [])][:3]
        }, indent=2)

        prompt = f"""
        Analyze the patient's medical history AND uploaded medical reports against their new current message.
        Check if the symptoms mentioned now could be a recurrence, complication, or related to any past condition or recent medical test/surgery.
        
        PAST MEDICAL HISTORY / UPLOADED REPORTS:
        {past_history_str}
        
        NEW CURRENT MESSAGE:
        "{current_message}"
        
        If this is a recurrence or related to a past major condition (e.g., heart transplant, cancer, COPD), explicitly state so.
        Crucially, generate a `dynamic_severity_question` that asks for refinement based on the specific disease (e.g., asking about specific symptoms, causes, or medications related to that disease). DO NOT use a generic severity question!
        Provide a clinical baseline summary in the required JSON format.
        """

        try:
            response = await llm_client.generate(
                prompt=prompt,
                system_instruction=self.system_instructions,
                response_format="json"
            )
            data = json.loads(response)
            return data
        except Exception as e:
            return {
                "is_recurrence": False,
                "suspected_recurring_condition": None,
                "dynamic_severity_question": None,
                "severity_change": "unknown",
                "clinical_baseline_summary": f"Failed to analyze history: {str(e)}"
            }

# Singleton instance
history_analyzer = PatientHistoryAnalyzer()
