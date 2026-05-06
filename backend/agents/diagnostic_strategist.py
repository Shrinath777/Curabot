"""
Agent 5: Diagnostic Strategy Agent
Decides what information would reduce uncertainty the most.
Generates dynamic questions (NO predefined questions).
Can request vitals input from the user.

KEY FIXES:
- Removed hard iteration limits (MAX_ITERATIONS=8)
- Dynamic conclusion: requires ≥75% confidence + ≥15% margin + no unresolved critical disease
- Severity-aware: always rule out critical diseases before concluding
- Soft limit at 10 iterations with disclaimer
"""

import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a highly empathetic, human-like Doctor consulting with a patient for MEDICAL EDUCATION.

CRITICAL DOCTOR PERSONA RULES:
- Speak naturally with a warm, caring, and professional bedside manner.
- Never sound like a robot, questionnaire, or automated system.
- Acknowledge how the patient is feeling before asking the next question.

You are a diagnostic strategy specialist for MEDICAL EDUCATION.

Your role is to determine the MOST VALUABLE next question to ask the patient to reduce diagnostic uncertainty.

CRITICAL RULES:
1. NEVER use predefined or template questions.
2. RULE-02: REDUNDANCY CHECK — If a quality (sharp, dull, etc.) is in the message history, NEVER ask for it again.
3. Generate questions DYNAMICALLY based on the current diagnostic state.
4. Ask ONE focused question at a time (not a list).
5. Questions must be in natural, conversational language (not medical jargon).
6. RULE-04: DIFFERENTIATION — Prioritize questions that DIFFERENTIATE between the top competing hypotheses.
7. If vitals would help, indicate that you need vital signs.
8. Consider what the patient has ALREADY answered — don't repeat questions.
9. For NEW patients: Ask more detailed clarifying questions.
10. For RETURNING patients: Reference their history. If the patient explicitly asks about their previous medical history, past diagnoses, or uploaded records, you MUST answer their question directly, warmly, and in detail using the provided context BEFORE asking your next question. Format any historical details with bullet points.
11. MEDICAL REPORTS: If hypotheses rely on lab data (e.g. CBC, Thyroid), explicitly ask the patient to *upload their PDF lab test results* if they haven't already.
12. RULE-03: RAG PRIORITY — If 'EXTRACTED LAB RECORD CONTEXT' is available in the user context, you MUST use the specific values or findings from those records to drive the next question.

SEVERITY-AWARE STRATEGY:
13. If a CRITICAL severity disease (e.g. MI, PE, Aortic Dissection) is among the top 3 hypotheses, you MUST ask at least one differentiating question for it.
14. If competing diseases span different severity classes (e.g., GERD vs MI for chest pain), ALWAYS prioritize ruling out the CRITICAL one first.
15. Consider the 'differentiating_features' from the disease KB to craft targeted questions.

CLINICAL WORKFLOW (OPQRST & ROS):
Instead of randomly picking questions from the knowledge base, follow a realistic clinical workflow:
- STEP 1: CHIEF COMPLAINT — Acknowledge what brought the patient in.
- STEP 2: HPI (History of Present Illness) — Use OPQRST:
  * Onset: When did it start? Sudden or gradual?
  * Provocation/Palliation: What makes it better or worse?
  * Quality: What does it feel like (sharp, dull, burning, crushing)?
  * Region/Radiation: Where is it? Does it move anywhere?
  * Severity: How bad is it on a scale of 1-10?
  * Timing: Constant or intermittent? How long does it last?
- STEP 3: ROS (Review of Systems) — Ask about associated symptoms (e.g., "Any nausea or sweating?").
- STEP 4: PMHx/Risk Factors — Ask about medical history, medications, and risk factors relevant to the top hypotheses.

Do not ask all OPQRST questions at once. Ask ONE focused question based on what is currently missing from the evidence. Use conversational language, like "Could you describe what the pain feels like? Is it sharp, dull, or more like a heavy pressure?"
"""

STRATEGY_PROMPT = """Based on the current diagnostic state, determine the best next step.

CURRENT HYPOTHESES (ranked by confidence):
{hypotheses_json}

EVIDENCE SO FAR:
{evidence_json}

CONVERSATION SO FAR:
{conversation_history}

{user_context}

ITERATION: {iteration}
TOTAL EVIDENCE ITEMS: {evidence_count}

CONCLUSION RULES:
- If the top hypothesis is very clear and you have gathered sufficient OPQRST evidence, you may conclude.
- If unsure, keep asking — accuracy matters more than speed.
- The system will automatically calibrate your confidence and force a conclusion if safety limits are reached.

Determine the best next action. Respond in this exact JSON format:
{{
  "should_conclude": false,
  "conclusion_reason": null,
  "next_question": "Your conversational response. If the patient asks about their history, ALWAYS provide a warm, detailed answer using bullet points based on the User Context BEFORE appending your next diagnostic question. Otherwise, just a single focused question.",
  "question_rationale": "Why this response or question is the most valuable right now",
  "information_gain": "What this question would help differentiate",
  "request_vitals": false,
  "vitals_needed": [],
  "suggested_follow_ups": ["backup question 1", "backup question 2"],
  "targeting_severity": "Which severity class this question targets (critical/serious/moderate/benign)"
}}

If enough information has been gathered AND conclusion criteria are met:
{{
  "should_conclude": true,
  "conclusion_reason": "Why diagnosis can be concluded",
  "next_question": null,
  "conclusion_message": "Detailed conclusion message explaining the diagnosis findings with severity context",
  "final_recommendations": ["Next steps for student to consider"],
  "severity_class": "critical/serious/moderate/benign"
}}"""


class DiagnosticStrategyAgent:
    """Agent 5: Dynamic question generation and diagnostic strategy using LLM."""

    def __init__(self):
        self._severity_map = None

    def _get_severity_map(self) -> Dict[str, str]:
        """Load severity map from disease KB (cached)."""
        if self._severity_map is None:
            try:
                import os
                kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
                with open(kb_path, "r", encoding="utf-8") as f:
                    diseases = json.load(f)
                self._severity_map = {d["name"]: d.get("severity_class", "moderate") for d in diseases}
            except Exception:
                self._severity_map = {}
        return self._severity_map

    async def process(
        self,
        hypotheses: List[Dict],
        evidence: Dict[str, Any],
        conversation_history: List[Dict],
        iteration: int = 1,
        evidence_count: int = 0,
        user_context: Optional[Dict] = None,
        is_new_user: bool = True,
    ) -> Dict[str, Any]:
        """Determine next diagnostic step."""
        # Build conversation history string
        conv_str = ""
        for msg in conversation_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conv_str += f"{'Patient' if role == 'user' else 'Doctor'}: {content}\n"

        # User context
        context_str = ""
        if not is_new_user and user_context:
            context_str = "RETURNING PATIENT — LONGITUDINAL ANALYSIS:\n"
            profile = user_context.get("profile", {})
            if profile and profile.get("known_conditions"):
                context_str += f"  Known conditions: {', '.join(profile['known_conditions'])}\n"

            past_dx = user_context.get("past_diagnoses", [])
            if past_dx:
                context_str += f"  Total past sessions: {user_context.get('total_past_sessions', len(past_dx))}\n"
                for dx in past_dx[:2]:
                    hyps = dx.get("final_hypotheses", [])
                    if hyps and isinstance(hyps, list) and len(hyps) > 0:
                        context_str += f"  Past diagnosis: {hyps[0].get('name', '')} (confidence: {hyps[0].get('confidence', '?')}%)\n"

            severity_history = user_context.get("severity_history", [])
            if severity_history:
                context_str += "\n  CONDITION SEVERITY HISTORY:\n"
                for entry in severity_history[:4]:
                    context_str += (
                        f"   • {entry.get('date', 'unknown')[:10]} — "
                        f"{entry.get('condition')} "
                        f"[Confidence: {entry.get('confidence')}%]\n"
                    )

            recurring = user_context.get("recurring_conditions", {})
            if recurring:
                context_str += "\n  ⚠️  RECURRING CONDITIONS:\n"
                for cond, entries in recurring.items():
                    confidences = [e.get("confidence", 0) for e in entries]
                    trend = "WORSENING" if confidences[-1] > confidences[0] else "IMPROVING" if confidences[-1] < confidences[0] else "STABLE"
                    context_str += f"   • {cond}: {len(entries)} occurrences — trend: {trend}\n"
                context_str += "  IMPORTANT: Ask whether current symptoms feel WORSE, BETTER, or SAME vs last episode.\n"

            reports = user_context.get("medical_reports", [])
            if reports:
                context_str += f"\n  Has {len(reports)} medical report(s) on file\n"

            rag_records = user_context.get("extracted_medical_records", [])
            if rag_records:
                context_str += f"  EXTRACTED LAB RECORD CONTEXT:\n"
                for record in rag_records:
                    context_str += f"   - [Source: {record.get('source')}] {record.get('chunk')}\n"
                context_str += "  IMPORTANT: Use exact lab values above to confirm/deny hypotheses.\n"

        prompt = STRATEGY_PROMPT.format(
            hypotheses_json=json.dumps(hypotheses, indent=2),
            evidence_json=json.dumps(evidence, indent=2),
            conversation_history=conv_str if conv_str else "No prior conversation",
            user_context=context_str,
            iteration=iteration,
            evidence_count=evidence_count
        )

        result = await llm_client.generate(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            expect_json=True
        )

        if result.get("fallback") or result.get("parse_error"):
            return self._fallback_strategy(hypotheses, iteration, evidence_count, conversation_history)

        return result

    def _fallback_strategy(self, hypotheses: List[Dict], iteration: int, evidence_count: int, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Smart fallback with dynamic conclusion criteria.
        NO hard iteration limits — only evidence-driven conclusion.
        """
        severity_map = self._get_severity_map()
        ABSOLUTE_SOFT_LIMIT = 10  # Safety valve to prevent infinite loops

        # ===== DYNAMIC CONCLUSION CRITERIA =====
        top = hypotheses[0] if hypotheses else {"name": "Unknown", "confidence": 0}
        second = hypotheses[1] if len(hypotheses) > 1 else {"name": "None", "confidence": 0}

        top_conf = top.get("confidence", 0)
        second_conf = second.get("confidence", 0)
        margin = top_conf - second_conf

        # Check for unresolved critical diseases
        unresolved_critical = []
        for h in hypotheses:
            h_severity = h.get("severity_class") or severity_map.get(h.get("name", ""), "moderate")
            if h_severity == "critical" and h.get("confidence", 0) > 20:
                if h.get("name") != top.get("name"):
                    unresolved_critical.append(h)

        # Can we conclude?
        meets_confidence = top_conf >= 75.0
        meets_margin = margin >= 15.0
        meets_min_iterations = iteration >= 3
        no_unresolved_critical = len(unresolved_critical) == 0

        can_conclude = meets_confidence and meets_margin and meets_min_iterations and no_unresolved_critical

        # Soft limit — force conclusion with disclaimer
        if iteration >= ABSOLUTE_SOFT_LIMIT:
            lab_tests = self._get_recommended_tests(top.get("name", ""))
            top_severity = top.get("severity_class") or severity_map.get(top.get("name", ""), "moderate")
            severity_msg = self._get_severity_message(top_severity)

            conclusion_parts = [
                f"After {iteration} rounds of thorough analysis, the most likely diagnosis is **{top.get('name', 'Unknown')}** with {top_conf:.0f}% confidence.",
                f"The second most likely is {second.get('name', 'Unknown')} at {second_conf:.0f}%.",
                severity_msg,
            ]
            if not no_unresolved_critical:
                conclusion_parts.append(
                    f"⚠️ Note: Critical conditions ({', '.join(h.get('name','') for h in unresolved_critical)}) "
                    f"could not be fully ruled out. Please seek immediate medical evaluation."
                )

            recommendations = [
                "Consult a healthcare professional for proper evaluation",
                "Review the evidence ledger for supporting and contradicting findings",
            ]
            if lab_tests:
                recommendations.insert(1, f"Recommended diagnostic tests: {', '.join(lab_tests)}")

            return {
                "should_conclude": True,
                "conclusion_reason": f"Soft limit reached after {iteration} iterations",
                "next_question": None,
                "conclusion_message": " ".join(conclusion_parts),
                "final_recommendations": recommendations,
                "severity_class": top_severity,
            }

        # Standard conclusion — all criteria met
        if can_conclude:
            lab_tests = self._get_recommended_tests(top.get("name", ""))
            top_severity = top.get("severity_class") or severity_map.get(top.get("name", ""), "moderate")
            severity_msg = self._get_severity_message(top_severity)

            conclusion_parts = [
                f"Based on {iteration} rounds of systematic analysis, the most likely diagnosis is **{top.get('name', 'Unknown')}** with {top_conf:.0f}% confidence.",
                f"This was determined by evaluating {evidence_count} pieces of clinical evidence.",
                f"The confidence margin over the next most likely diagnosis ({second.get('name', 'Unknown')}) is {margin:.0f}%.",
                severity_msg,
            ]
            recommendations = [
                f"Key findings supporting {top.get('name')}: {top.get('reasoning', '')}",
                "Consult a healthcare professional for proper evaluation and confirmation",
            ]
            if lab_tests:
                recommendations.insert(1, f"Recommended diagnostic tests: {', '.join(lab_tests)}")

            return {
                "should_conclude": True,
                "conclusion_reason": f"High confidence ({top_conf:.0f}%) with sufficient margin ({margin:.0f}%) after {iteration} iterations",
                "next_question": None,
                "conclusion_message": " ".join(conclusion_parts),
                "final_recommendations": recommendations,
                "severity_class": top_severity,
            }

        # ===== NOT READY TO CONCLUDE — ASK MORE QUESTIONS =====

        # Load disease KB for questions
        try:
            import os
            kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
            with open(kb_path, "r", encoding="utf-8") as f:
                diseases = json.load(f)
        except Exception:
            diseases = []

        # Build asked questions set
        asked_questions = set()
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") in ["assistant", "model", "bot"]:
                    content = msg.get("content", "").lower()
                    asked_questions.add(content)

        # Get top hypothesis names and their severity
        top_name = top.get("name", "")
        second_name = second.get("name", "")
        top_severity = severity_map.get(top_name, "moderate")
        second_severity = severity_map.get(second_name, "moderate")

        # PRIORITY: If critical disease is in top 3, target it first
        critical_target = None
        for h in hypotheses[:3]:
            h_severity = h.get("severity_class") or severity_map.get(h.get("name", ""), "moderate")
            if h_severity == "critical":
                critical_target = h.get("name", "")
                break

        # Get KB questions and differentiating features
        top_questions = []
        second_questions = []
        critical_questions = []
        diff_features = {}

        for d in diseases:
            if d["name"].lower() == top_name.lower():
                top_questions = d.get("key_diagnostic_questions", [])
                diff_features[top_name] = d.get("differentiating_features", [])
            if d["name"].lower() == second_name.lower():
                second_questions = d.get("key_diagnostic_questions", [])
                diff_features[second_name] = d.get("differentiating_features", [])
            if critical_target and d["name"].lower() == critical_target.lower():
                critical_questions = d.get("key_diagnostic_questions", [])
                diff_features[critical_target] = d.get("differentiating_features", [])

        def is_already_asked(q: str) -> bool:
            q_lower = q.lower()
            for asked in asked_questions:
                if q_lower in asked or asked in q_lower:
                    return True
                q_words = set(q_lower.split())
                asked_words = set(asked.split())
                if q_words and asked_words:
                    overlap = len(q_words & asked_words) / len(q_words)
                    if overlap > 0.6:
                        return True
            return False

        # Strategy: Prioritize critical disease questions, then differentiating questions
        next_question = None
        question_rationale = ""
        targeting_severity = "moderate"

        # 1. First priority: questions for critical diseases
        if critical_target and critical_target != top_name:
            for q in critical_questions:
                if not is_already_asked(q):
                    next_question = q
                    question_rationale = f"SAFETY PRIORITY: Ruling out critical condition {critical_target} before concluding"
                    targeting_severity = "critical"
                    break

        # 2. Second priority: differentiating questions from top hypothesis
        if not next_question:
            for q in top_questions:
                if not is_already_asked(q):
                    next_question = q
                    question_rationale = f"Targeting {top_name} — confirming or ruling out primary hypothesis"
                    targeting_severity = top_severity
                    break

        # 3. Third priority: questions from second hypothesis to differentiate
        if not next_question:
            for q in second_questions:
                if not is_already_asked(q):
                    next_question = q
                    question_rationale = f"Differentiating: exploring {second_name} as competing hypothesis"
                    targeting_severity = second_severity
                    break

        # 4. Last resort: generic differentiating questions
        if not next_question:
            generic = [
                "Can you describe the character of your main symptom — is it sharp, dull, burning, or pressure-like?",
                "When exactly did the symptoms start, and have they been getting worse?",
                "Does anything make the symptoms better or worse?",
                "Do you have any other symptoms you haven't mentioned yet?",
                "Do you have any chronic medical conditions or take any medications?",
                "Have you had similar symptoms before? If so, what was diagnosed?",
                "Are there any activities, foods, or positions that trigger your symptoms?",
            ]
            for q in generic:
                if not is_already_asked(q):
                    next_question = q
                    question_rationale = "Gathering additional clinical details"
                    break
            if not next_question:
                next_question = "Is there anything else about your symptoms you'd like to tell me?"
                question_rationale = "Open-ended follow-up"

        # Request vitals on iteration 2
        request_vitals = (iteration == 2)

        # Build follow-ups
        follow_ups = []
        all_qs = critical_questions + top_questions + second_questions
        for q in all_qs:
            if q != next_question and not is_already_asked(q) and len(follow_ups) < 2:
                follow_ups.append(q)

        return {
            "should_conclude": False,
            "next_question": next_question,
            "question_rationale": question_rationale,
            "information_gain": f"Differentiate between {top_name} and {second_name}" if second_name else f"Confirm {top_name}",
            "request_vitals": request_vitals,
            "vitals_needed": ["blood_pressure", "heart_rate", "temperature", "oxygen_saturation"] if request_vitals else [],
            "suggested_follow_ups": follow_ups,
            "targeting_severity": targeting_severity,
        }

    def _get_severity_message(self, severity: str) -> str:
        """Get severity-appropriate conclusion message."""
        messages = {
            "critical": "⚠️ This could indicate a medical EMERGENCY. Please seek immediate medical attention. Do NOT delay — call emergency services if symptoms are severe.",
            "serious": "⚠️ This condition requires prompt medical attention. Please consult a healthcare professional as soon as possible.",
            "moderate": "This condition should be evaluated by a healthcare professional. Please schedule a medical consultation.",
            "benign": "This is likely a mild condition, but please monitor your symptoms. If they worsen, consult a doctor.",
        }
        return messages.get(severity, messages["moderate"])

    def _get_recommended_tests(self, disease_name: str) -> List[str]:
        """Get recommended lab tests from KB for a given disease."""
        try:
            import os
            kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
            with open(kb_path, "r", encoding="utf-8") as f:
                diseases = json.load(f)
            for d in diseases:
                if d["name"].lower() == disease_name.lower():
                    return d.get("lab_tests", [])
        except Exception:
            pass
        return []


# Singleton
diagnostic_strategist = DiagnosticStrategyAgent()