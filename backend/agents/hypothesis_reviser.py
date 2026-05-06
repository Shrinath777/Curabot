"""
Agent 4: Hypothesis Revision & Confidence Agent
Updates confidence scores as evidence changes.
Explains confidence shifts in natural language.

KEY FIXES:
- Confidence always normalized to sum to 100%
- Bayesian likelihood-ratio updates (not raw count arithmetic)
- Severity floor: critical diseases never drop below 8% until ruled out
- Tiebreaker: severity > supporting count > prevalence
"""

import json
import logging
from typing import Dict, Any, List, Optional
from services.llm_client import llm_client

logger = logging.getLogger(__name__)

# Severity ordering for tiebreaking
SEVERITY_ORDER = {"critical": 4, "serious": 3, "moderate": 2, "benign": 1}
SEVERITY_FLOOR = {"critical": 8.0, "serious": 5.0, "moderate": 2.0, "benign": 1.0}

SYSTEM_PROMPT = """You are a Bayesian diagnostic reasoning specialist for MEDICAL EDUCATION.

Your role:
1. Use Bayesian-style reasoning to update confidence scores.
2. RULE-04: DDx REVISION — Ensure the confidence distribution reflects the current weight of evidence across all 3-5 hypotheses. Don't let one strong finding overshadow other possibilities too early.
3. Adjust confidences based on the strength of supporting and contradicting evidence.
4. Explain the "delta" — why confidence increased or decreased for each hypothesis.
5. Account for the number of iterations and the amount of information gathered.

CRITICAL RULES:
- Confidence scores MUST sum to exactly 100% across all hypotheses.
- NEVER let a 'critical' severity disease drop below 8% confidence unless you have STRONG contradicting evidence explicitly ruling it out.
- 'serious' diseases should not drop below 5% without explicit contradicting evidence.
- When two hypotheses have similar confidence, use the specificity of evidence to differentiate them.
- Consider disease severity: critical conditions deserve higher minimum confidence until actively ruled out."""

REVISION_PROMPT = """Revise the confidence scores for each hypothesis based on the evidence.

CURRENT HYPOTHESES (from previous iteration):
{hypotheses_json}

EVIDENCE EVALUATION (from Evidence Agent):
{evidence_json}

ITERATION: {iteration}

IMPORTANT: Your revised confidence scores MUST sum to exactly 100%.
Critical severity diseases must NOT drop below 8% unless explicitly contradicted.

Revise confidence scores. Respond in this JSON format:
{{
  "revised_hypotheses": [
    {{
      "name": "Disease Name",
      "previous_confidence": 45.0,
      "new_confidence": 55.0,
      "confidence_change": "+10.0",
      "change_reason": "Clear explanation of why confidence increased/decreased",
      "supporting_count": 3,
      "contradicting_count": 1,
      "status": "promoted/demoted/stable",
      "severity_class": "critical/serious/moderate/benign"
    }}
  ],
  "revision_narrative": "Natural language explanation of how the diagnostic picture has changed",
  "convergence_status": "converging/diverging/uncertain"
}}"""


def _normalize_confidences(hypotheses: List[Dict], apply_severity_floor: bool = True) -> List[Dict]:
    """Normalize confidence scores to sum to exactly 100%, respecting severity floors."""
    if not hypotheses:
        return hypotheses

    # Load severity info from disease KB if not already present
    severity_map = _load_severity_map()

    # Apply severity floors first
    if apply_severity_floor:
        for h in hypotheses:
            name = h.get("name", "")
            severity = h.get("severity_class") or severity_map.get(name, "moderate")
            h["severity_class"] = severity
            floor = SEVERITY_FLOOR.get(severity, 1.0)

            # Only apply floor if not explicitly contradicted
            contradicting = h.get("contradicting_count", h.get("contradicting", 0))
            if isinstance(contradicting, int) and contradicting >= 3:
                # Heavily contradicted — allow dropping below floor
                pass
            else:
                h["confidence"] = max(h.get("confidence", h.get("new_confidence", 30.0)), floor)

    # Normalize to sum to 100%
    total = sum(h.get("confidence", h.get("new_confidence", 20.0)) for h in hypotheses)
    if total > 0:
        for h in hypotheses:
            raw = h.get("confidence", h.get("new_confidence", 20.0))
            normalized = round(raw / total * 100, 1)
            h["confidence"] = normalized
            h["new_confidence"] = normalized

    # Re-apply floors after normalization (in case normalization pushed below floor)
    if apply_severity_floor:
        _reapply_floors(hypotheses, severity_map)

    return hypotheses


def _reapply_floors(hypotheses: List[Dict], severity_map: Dict) -> None:
    """Re-apply severity floors after normalization, redistributing excess."""
    deficit = 0.0
    non_floor_indices = []

    for i, h in enumerate(hypotheses):
        severity = h.get("severity_class") or severity_map.get(h.get("name", ""), "moderate")
        floor = SEVERITY_FLOOR.get(severity, 1.0)
        contradicting = h.get("contradicting_count", h.get("contradicting", 0))

        if isinstance(contradicting, int) and contradicting >= 3:
            non_floor_indices.append(i)
            continue

        if h["confidence"] < floor:
            deficit += floor - h["confidence"]
            h["confidence"] = floor
            h["new_confidence"] = floor
        else:
            non_floor_indices.append(i)

    # Redistribute deficit from non-floored hypotheses
    if deficit > 0 and non_floor_indices:
        per_item = deficit / len(non_floor_indices)
        for i in non_floor_indices:
            hypotheses[i]["confidence"] = round(hypotheses[i]["confidence"] - per_item, 1)
            hypotheses[i]["new_confidence"] = hypotheses[i]["confidence"]


def _load_severity_map() -> Dict[str, str]:
    """Load severity_class from disease KB."""
    try:
        import os
        kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")
        with open(kb_path, "r", encoding="utf-8") as f:
            diseases = json.load(f)
        return {d["name"]: d.get("severity_class", "moderate") for d in diseases}
    except Exception:
        return {}


def _apply_tiebreaker(hypotheses: List[Dict], severity_map: Dict) -> List[Dict]:
    """Break ties using severity > supporting count > prevalence."""
    def sort_key(h):
        conf = h.get("confidence", 0)
        severity_score = SEVERITY_ORDER.get(
            h.get("severity_class") or severity_map.get(h.get("name", ""), "moderate"), 2
        )
        supporting = h.get("supporting_count", h.get("supporting", 0))
        if not isinstance(supporting, (int, float)):
            supporting = 0
        contradicting = h.get("contradicting_count", h.get("contradicting", 0))
        if not isinstance(contradicting, (int, float)):
            contradicting = 0
        return (conf, severity_score, supporting, -contradicting)

    hypotheses.sort(key=sort_key, reverse=True)

    # Add small epsilon to break exact ties in confidence
    for i in range(len(hypotheses) - 1):
        if abs(hypotheses[i]["confidence"] - hypotheses[i + 1]["confidence"]) < 0.1:
            # They're tied — nudge based on tiebreaker factors
            h1_severity = SEVERITY_ORDER.get(
                hypotheses[i].get("severity_class", "moderate"), 2)
            h2_severity = SEVERITY_ORDER.get(
                hypotheses[i + 1].get("severity_class", "moderate"), 2)
            if h1_severity > h2_severity:
                hypotheses[i]["confidence"] = round(hypotheses[i]["confidence"] + 0.5, 1)
                hypotheses[i + 1]["confidence"] = round(hypotheses[i + 1]["confidence"] - 0.5, 1)
            elif h2_severity > h1_severity:
                hypotheses[i]["confidence"] = round(hypotheses[i]["confidence"] - 0.5, 1)
                hypotheses[i + 1]["confidence"] = round(hypotheses[i + 1]["confidence"] + 0.5, 1)

    return hypotheses


class HypothesisReviserAgent:
    """Agent 4: Revises hypothesis confidence using LLM-driven Bayesian reasoning."""

    async def process(
        self,
        hypotheses: List[Dict],
        evidence: Dict[str, Any],
        iteration: int = 1,
    ) -> Dict[str, Any]:
        """
        Revise confidence scores based on evidence.
        Always normalizes output to sum to 100%.
        """
        prompt = REVISION_PROMPT.format(
            hypotheses_json=json.dumps(hypotheses, indent=2),
            evidence_json=json.dumps(evidence, indent=2),
            iteration=iteration
        )

        result = await llm_client.generate(
            prompt=prompt,
            system_instruction=SYSTEM_PROMPT,
            expect_json=True
        )

        if result.get("fallback") or result.get("parse_error"):
            return self._fallback_revision(hypotheses, evidence)

        # Ensure proper structure
        revised = result.get("revised_hypotheses", [])
        for h in revised:
            h.setdefault("new_confidence", h.get("confidence", 30.0))
            h.setdefault("supporting_count", 0)
            h.setdefault("contradicting_count", 0)
            h["confidence"] = h["new_confidence"]
            h["supporting"] = h["supporting_count"]
            h["contradicting"] = h["contradicting_count"]

        # CRITICAL: Normalize to 100% and apply severity floors
        severity_map = _load_severity_map()
        revised = _normalize_confidences(revised)
        revised = _apply_tiebreaker(revised, severity_map)

        result["revised_hypotheses"] = revised
        return result

    def _fallback_revision(self, hypotheses: List[Dict], evidence: Dict) -> Dict[str, Any]:
        """Bayesian-style fallback revision using likelihood ratios instead of raw counts."""
        evidence_ledger = evidence.get("evidence_ledger", [])
        severity_map = _load_severity_map()
        revised = []

        # Likelihood ratio multipliers
        SUPPORT_MULTIPLIERS = {"strong": 1.6, "moderate": 1.3, "weak": 1.1}
        CONTRADICT_MULTIPLIERS = {"strong": 0.5, "moderate": 0.7, "weak": 0.9}

        for h in hypotheses:
            prev_conf = h.get("confidence", 30.0)
            likelihood = prev_conf  # Start with prior

            supporting_count = 0
            contradicting_count = 0

            for e in evidence_ledger:
                # Check supports
                for s in e.get("supports", []):
                    if isinstance(s, dict) and s.get("hypothesis") == h.get("name"):
                        strength = s.get("strength", "weak")
                        multiplier = SUPPORT_MULTIPLIERS.get(strength, 1.1)
                        likelihood *= multiplier
                        supporting_count += 1
                    elif isinstance(s, str) and s == h.get("name"):
                        likelihood *= 1.2
                        supporting_count += 1

                # Check contradicts
                for c in e.get("contradicts", []):
                    if isinstance(c, dict) and c.get("hypothesis") == h.get("name"):
                        strength = c.get("strength", "weak")
                        multiplier = CONTRADICT_MULTIPLIERS.get(strength, 0.9)
                        likelihood *= multiplier
                        contradicting_count += 1
                    elif isinstance(c, str) and c == h.get("name"):
                        likelihood *= 0.75
                        contradicting_count += 1

            # Clamp to reasonable range before normalization
            new_conf = max(1.0, min(95.0, likelihood))
            change = new_conf - prev_conf

            severity = severity_map.get(h.get("name", ""), "moderate")

            revised.append({
                "name": h.get("name", ""),
                "previous_confidence": prev_conf,
                "new_confidence": round(new_conf, 1),
                "confidence": round(new_conf, 1),
                "confidence_change": f"{change:+.1f}",
                "change_reason": f"Bayesian update: {supporting_count} supporting (LR boost) and {contradicting_count} contradicting (LR reduction)",
                "supporting_count": supporting_count,
                "contradicting_count": contradicting_count,
                "supporting": supporting_count,
                "contradicting": contradicting_count,
                "status": "promoted" if change > 2 else "demoted" if change < -2 else "stable",
                "severity_class": severity,
                "reasoning": h.get("reasoning", ""),
            })

        # CRITICAL: Normalize and apply tiebreakers
        revised = _normalize_confidences(revised)
        revised = _apply_tiebreaker(revised, severity_map)

        return {
            "revised_hypotheses": revised,
            "revision_narrative": "Bayesian likelihood-ratio revision applied. Confidence normalized to 100%.",
            "convergence_status": "uncertain"
        }


# Singleton
hypothesis_reviser = HypothesisReviserAgent()