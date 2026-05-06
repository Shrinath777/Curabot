"""
Agent 6: Self-Critique & Bias Check Agent
Challenges dominant hypotheses, flags premature convergence,
and forces the system to consider alternatives.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a cognitive bias detection specialist for MEDICAL EDUCATION.

Your role is to challenge the diagnostic reasoning process and:
1. Explicitly check for cognitive biases (e.g., anchoring, premature closure).
2. RULE-05: QUALITY ASSURANCE — Ensure the final reasoning is sound and that all critical SOPs were followed during the 6-agent cycle. Identify if any red flags were missed or if RULE-02 was violated (redundant questioning).
3. Challenge the top hypothesis — what could make it incorrect?
4. Ensure the reasoning is consistent and isn't ignoring contradicting evidence.
5. Identify "missing pieces" that could change the clinical picture.
6. Force consideration of at least one alternative hypothesis.
7. Suggest what evidence would DISPROVE the current leading diagnosis.

Be constructive and educational — explain WHY each bias is dangerous in clinical reasoning."""

CRITIQUE_PROMPT = """Review the current diagnostic reasoning for cognitive biases.

CURRENT HYPOTHESES (ranked):
{hypotheses_json}

EVIDENCE EVALUATION:
{evidence_json}

ITERATION: {iteration}
NUMBER OF QUESTIONS ASKED: {questions_asked}

Analyze for biases and suggest improvements. Respond in JSON:
{{
  "biases_detected": [
    {{
      "type": "anchoring/confirmation_bias/premature_closure/availability_bias",
      "severity": "low/medium/high",
      "description": "Clear explanation of the bias",
      "affected_hypothesis": "Which diagnosis is affected",
      "mitigation": "How to counter this bias"
    }}
  ],
  "alternative_considerations": [
    {{
      "hypothesis": "Alternative diagnosis to consider",
      "reason": "Why this should not be dismissed",
      "differentiating_question": "What to ask to evaluate this alternative"
    }}
  ],
  "reasoning_quality": "good/acceptable/concerning",
  "overall_assessment": "Brief assessment of the diagnostic reasoning quality"
}}"""


class SelfCritiqueAgent:
    """Agent 6: Detects cognitive biases and forces alternative consideration."""

    async def process(
        self,
        hypotheses: List[Dict],
        evidence: Dict[str, Any],
        iteration: int = 1,
        questions_asked: int = 0,
    ) -> Dict[str, Any]:
        """
        Critique the diagnostic reasoning.

        Args:
            hypotheses: Current ranked hypotheses
            evidence: Evidence evaluation
            iteration: Current iteration
            questions_asked: Number of questions asked so far
        """
        prompt = CRITIQUE_PROMPT.format(
            hypotheses_json=json.dumps(hypotheses, indent=2),
            evidence_json=json.dumps(evidence, indent=2),
            iteration=iteration,
            questions_asked=questions_asked
        )

        result = await llm_client.generate(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            expect_json=True
        )

        if result.get("fallback") or result.get("parse_error"):
            return self._fallback_critique(hypotheses, iteration)

        return result

    def _fallback_critique(self, hypotheses: List[Dict], iteration: int, sop_findings: str = "") -> Dict[str, Any]:
        """Fallback bias detection and SOP compliance checking."""
        biases = []

        # Cognitive Bias Checking
        if len(hypotheses) >= 2:
            top_conf = hypotheses[0].get("confidence", 0)
            second_conf = hypotheses[1].get("confidence", 0)

            if top_conf - second_conf > 30:
                biases.append({
                    "type": "anchoring",
                    "severity": "high",
                    "description": f"Large confidence gap ({top_conf - second_conf:.0f}%) between top hypothesis and alternatives.",
                    "affected_hypothesis": hypotheses[0].get("name", ""),
                    "mitigation": "Consider what evidence would argue against the leading diagnosis."
                })

            if iteration <= 2 and top_conf > 70:
                biases.append({
                    "type": "premature_closure",
                    "severity": "medium",
                    "description": "High confidence reached with minimal questioning.",
                    "affected_hypothesis": hypotheses[0].get("name", ""),
                    "mitigation": "Continue gathering information before concluding."
                })

        # SOP Compliance Checking
        sop_compliance = []
        if sop_findings:
            if "TRIAGE" in sop_findings:
                sop_compliance.append("SOP-001 (Triage) successfully executed.")
            if "VITALS" in sop_findings:
                sop_compliance.append("SOP-005 (Vitals) successfully evaluated.")
            if "RED_FLAGS" in sop_findings:
                biases.append({
                    "type": "safety_check",
                    "severity": "high",
                    "description": "Red flags detected by SOP-010. Ensure these are prioritized in reasoning.",
                    "affected_hypothesis": "Any",
                    "mitigation": "Rule out critical diagnoses associated with the red flags."
                })

        return {
            "biases_detected": biases,
            "sop_compliance": sop_compliance,
            "alternative_considerations": [],
            "reasoning_quality": "acceptable" if not biases else "concerning",
            "overall_assessment": "Fallback bias and SOP compliance check completed."
        }


# Singleton
self_critique = SelfCritiqueAgent()