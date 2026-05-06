"""
Agent 3: Evidence Evaluation Agent
Maps findings to supporting/contradicting evidence per hypothesis.
Maintains an evidence ledger with timestamps.

KEY FIXES:
- Severity-aware evidence weighting
- Differentiating features get 'strong' strength
- Absent expected symptoms tracked as contradicting evidence
"""

import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clinical evidence evaluation specialist for MEDICAL EDUCATION.

Your role is to evaluate how each piece of clinical evidence (symptoms, vitals, history) supports or contradicts each diagnostic hypothesis.

Rules:
1. Compare normalized findings against the characteristic presentation of each hypothesis.
2. RULE-03: CONTEXTUAL INTEGRATION — You MUST check for clinical evidence in 'user_context' and 'extracted_medical_records' (RAG) that supports or contradicts the current hypotheses.
3. Quantify the strength of each piece of evidence (weak, moderate, strong).
4. Clearly state why a finding supports or contradicts a specific diagnosis.
5. Identify inconsistencies between the patient's message and their past medical records.
6. Be thorough — consider each finding against EVERY hypothesis.
7. Provide confidence weights for how strongly evidence supports/contradicts.
8. Consider the SPECIFICITY of each finding (e.g., crushing chest pain is very specific to MI).
9. Consider the SENSITIVITY (e.g., chest pain is sensitive but not specific).
10. Factor in absent findings that would be expected if a diagnosis were correct.

SEVERITY-AWARE RULES:
11. Use 'differentiating_features' from the disease KB. If a symptom matches a differentiating feature, mark it as 'strong' evidence.
12. For CRITICAL severity diseases, absent key differentiating features should be marked as 'moderate' contradicting evidence (not just neutral).
13. Track which differentiating features are PRESENT vs ABSENT for each hypothesis.
14. A symptom that matches a disease's primary list but NOT its differentiating features should be marked as 'moderate' (not strong)."""

EVALUATION_PROMPT = """Evaluate the following evidence against each hypothesis.

CURRENT HYPOTHESES:
{hypotheses_json}

ALL GATHERED EVIDENCE (symptoms, vitals, answers):
{evidence_json}

{conversation_context}

EVALUATION RULES:
- If a finding matches a disease's differentiating_features, strength = "strong"
- If a finding matches primary symptoms only, strength = "moderate"
- If a finding matches secondary/atypical symptoms, strength = "weak"
- ABSENT expected key symptoms should be listed as contradicting evidence
- For critical diseases, be especially thorough about absent findings

Respond in this exact JSON format:
{{
  "evidence_ledger": [
    {{
      "finding": "symptom or finding name",
      "description": "what was found",
      "supports": [
        {{
          "hypothesis": "Disease Name",
          "strength": "strong/moderate/weak",
          "reason": "Why this finding supports this diagnosis",
          "is_differentiating": true
        }}
      ],
      "contradicts": [
        {{
          "hypothesis": "Disease Name",
          "strength": "strong/moderate/weak",
          "reason": "Why this finding argues against this diagnosis"
        }}
      ],
      "neutral_for": ["Disease names where this finding is neither for nor against"]
    }}
  ],
  "absent_evidence": [
    {{
      "finding": "Expected symptom that is ABSENT",
      "expected_for": "Disease Name",
      "severity_class": "critical/serious/moderate/benign",
      "impact": "How absence affects the hypothesis confidence"
    }}
  ],
  "missing_evidence": [
    {{
      "finding": "What finding would help differentiate",
      "would_support": "Disease Name",
      "would_contradict": "Disease Name"
    }}
  ],
  "evidence_summary": "Brief summary of the evidence landscape"
}}"""


class EvidenceEvaluatorAgent:
    """Agent 3: Evaluates evidence for/against each hypothesis using LLM."""

    def __init__(self):
        self._disease_data = None

    def _load_disease_data(self) -> List[Dict]:
        """Load full disease KB (cached)."""
        if self._disease_data is None:
            try:
                import os
                kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
                with open(kb_path, "r", encoding="utf-8") as f:
                    self._disease_data = json.load(f)
            except Exception:
                self._disease_data = []
        return self._disease_data

    async def process(
        self,
        hypotheses: List[Dict],
        normalized_symptoms: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        vitals: Optional[Dict] = None,
        user_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Evaluate evidence against hypotheses."""
        # Build evidence from all sources
        all_evidence = []

        for s in normalized_symptoms.get("primary_symptoms", []):
            all_evidence.append({
                "type": "symptom",
                "finding": s.get("name", ""),
                "detail": f"{s.get('character', '')} {s.get('severity', '')} {s.get('duration', '')}".strip(),
            })
        for s in normalized_symptoms.get("secondary_symptoms", []):
            all_evidence.append({
                "type": "symptom",
                "finding": s.get("name", ""),
                "detail": s.get("raw_text", ""),
            })

        for s in normalized_symptoms.get("absent_symptoms", []):
            all_evidence.append({
                "type": "explicitly_absent_symptom",
                "finding": s,
                "detail": "Patient explicitly denied this symptom",
            })

        if vitals:
            for key, value in vitals.items():
                if value is not None:
                    all_evidence.append({
                        "type": "vital_sign",
                        "finding": key,
                        "detail": str(value),
                    })

        if user_context and user_context.get("is_returning_user"):
            profile = user_context.get("profile", {})
            for condition in (profile.get("known_conditions") or []):
                all_evidence.append({
                    "type": "medical_history",
                    "finding": condition,
                    "detail": "Known pre-existing condition",
                })

            rag_records = user_context.get("extracted_medical_records", [])
            for r in rag_records:
                all_evidence.append({
                    "type": "medical_report_pdf",
                    "finding": f"Lab Result from {r.get('source')}",
                    "detail": r.get('chunk')
                })

        # Conversation context
        conv_context = ""
        if conversation_history:
            recent = conversation_history[-6:]
            conv_context = "RECENT CONVERSATION:\n"
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conv_context += f"- {role}: {content}\n"

        prompt = EVALUATION_PROMPT.format(
            hypotheses_json=json.dumps(hypotheses, indent=2),
            evidence_json=json.dumps(all_evidence, indent=2),
            conversation_context=conv_context
        )

        result = await llm_client.generate(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            expect_json=True
        )

        if result.get("fallback") or result.get("parse_error"):
            return self._fallback_evidence(hypotheses, all_evidence)

        return result

    def _fallback_evidence(self, hypotheses: List[Dict], evidence: List[Dict]) -> Dict[str, Any]:
        """Severity-aware KB-based evidence evaluation with differentiating features."""
        diseases = self._load_disease_data()

        # Build disease data maps
        disease_symptoms = {}
        disease_diff_features = {}
        disease_severity = {}
        for d in diseases:
            name = d["name"]
            syms = d.get("symptoms", {})
            if isinstance(syms, dict):
                disease_symptoms[name] = {
                    "primary": [s.lower().replace("_", " ") for s in syms.get("primary", [])],
                    "secondary": [s.lower().replace("_", " ") for s in syms.get("secondary", [])],
                    "atypical": [s.lower().replace("_", " ") for s in syms.get("atypical", [])],
                }
            else:
                disease_symptoms[name] = {"primary": [], "secondary": [], "atypical": []}

            disease_diff_features[name] = [f.lower() for f in d.get("differentiating_features", [])]
            disease_severity[name] = d.get("severity_class", "moderate")

        ledger = []
        for e in evidence:
            finding = e.get("finding", "").lower().replace("_", " ")
            is_absent_symptom = e.get("type") == "explicitly_absent_symptom"
            supports = []
            contradicts = []
            neutral_for = []

            for h in hypotheses:
                h_name = h.get("name", "")
                ds = disease_symptoms.get(h_name, {"primary": [], "secondary": [], "atypical": []})
                diff_feats = disease_diff_features.get(h_name, [])
                severity = disease_severity.get(h_name, "moderate")
                disease_system = next((d.get("body_system", "unknown") for d in diseases if d["name"] == h_name), "unknown")
                
                # Check if this symptom matches a differentiating feature
                is_differentiating = False
                for df in diff_feats:
                    if finding in df or any(word in df for word in finding.split() if len(word) > 3):
                        is_differentiating = True
                        break

                if is_absent_symptom:
                    if finding in ds["primary"] or any(finding in p or p in finding for p in ds["primary"]):
                        contradicts.append({
                            "hypothesis": h_name,
                            "strength": "strong",
                            "reason": f"Patient EXPLICITLY DENIES {finding}, which is a primary symptom of {h_name}"
                        })
                    elif finding in ds["secondary"] or any(finding in s or s in finding for s in ds["secondary"]):
                        contradicts.append({
                            "hypothesis": h_name,
                            "strength": "moderate",
                            "reason": f"Patient EXPLICITLY DENIES {finding}, which is a secondary symptom of {h_name}"
                        })
                    else:
                        neutral_for.append(h_name)
                    continue

                # Check symptom lists
                if finding in ds["primary"] or any(finding in p or p in finding for p in ds["primary"]):
                    strength = "strong" if is_differentiating else "moderate"
                    supports.append({
                        "hypothesis": h_name,
                        "strength": strength,
                        "reason": f"{finding} is a {'differentiating' if is_differentiating else 'primary'} symptom of {h_name}",
                        "is_differentiating": is_differentiating,
                    })
                elif finding in ds["secondary"] or any(finding in s or s in finding for s in ds["secondary"]):
                    supports.append({
                        "hypothesis": h_name,
                        "strength": "moderate" if is_differentiating else "weak",
                        "reason": f"{finding} is a secondary symptom of {h_name}",
                        "is_differentiating": is_differentiating,
                    })
                elif finding in ds["atypical"] or any(finding in a or a in finding for a in ds["atypical"]):
                    supports.append({
                        "hypothesis": h_name,
                        "strength": "weak",
                        "reason": f"{finding} is an atypical presentation of {h_name}",
                        "is_differentiating": False,
                    })
                else:
                    all_syms = ds["primary"] + ds["secondary"] + ds["atypical"]
                    if all_syms:
                        neutral_for.append(h_name)

            ledger.append({
                "finding": e.get("finding", ""),
                "description": e.get("detail", ""),
                "supports": supports,
                "contradicts": contradicts,
                "neutral_for": neutral_for
            })

        # NEW: Track absent expected symptoms as contradicting evidence
        absent_evidence = []
        found_findings = {e.get("finding", "").lower().replace("_", " ") for e in evidence}

        for h in hypotheses[:3]:  # Top 3 hypotheses
            h_name = h.get("name", "")
            ds = disease_symptoms.get(h_name, {"primary": [], "secondary": [], "atypical": []})
            severity = disease_severity.get(h_name, "moderate")

            for primary_sym in ds["primary"]:
                if primary_sym not in found_findings and not any(primary_sym in f or f in primary_sym for f in found_findings):
                    # Key symptom is absent
                    is_critical = severity == "critical"
                    absent_evidence.append({
                        "finding": primary_sym,
                        "expected_for": h_name,
                        "severity_class": severity,
                        "impact": f"Absent primary symptom weakens {h_name} hypothesis"
                    })

                    # For critical diseases, absent key symptoms are moderate contradictions
                    if is_critical:
                        ledger.append({
                            "finding": f"ABSENT: {primary_sym}",
                            "description": f"Expected primary symptom for {h_name} but not reported",
                            "supports": [],
                            "contradicts": [{
                                "hypothesis": h_name,
                                "strength": "moderate",
                                "reason": f"Key symptom '{primary_sym}' expected for {h_name} but not present"
                            }],
                            "neutral_for": []
                        })

        # Identify missing evidence that would help differentiate
        missing = []
        for h in hypotheses[:3]:
            h_name = h.get("name", "")
            ds = disease_symptoms.get(h_name, {"primary": [], "secondary": [], "atypical": []})
            for primary_sym in ds["primary"]:
                if primary_sym not in found_findings and not any(primary_sym in f or f in primary_sym for f in found_findings):
                    missing.append({
                        "finding": primary_sym,
                        "would_support": h_name,
                        "importance": "high" if disease_severity.get(h_name) in ("critical", "serious") else "medium"
                    })

        return {
            "evidence_ledger": ledger,
            "absent_evidence": absent_evidence,
            "missing_evidence": missing[:8],
            "evidence_summary": f"Evaluated {len(ledger)} findings (including absent evidence) against {len(hypotheses)} hypotheses"
        }


# Singleton
evidence_evaluator = EvidenceEvaluatorAgent()