"""
Orchestrator — Manages the 6-agent diagnostic pipeline + 10 Clinical SOPs.
Handles new vs old user detection, session state, and agent coordination.

PIPELINE FLOW (v2.1 with Clinical SOPs):
  Symptom Normalizer -> Red Flag Scanner (SOP-010) -> Triage (SOP-001)
  -> Chest Pain/Stroke Protocol (SOP-002/008) -> Vital Signs (SOP-005)
  -> Lab Interpreter (SOP-008) -> Hypothesis Generator -> Evidence Evaluator
  -> Hypothesis Reviser -> Diagnostic Strategist -> Self-Critique
  -> Medication Safety (SOP-009) -> Specialist Routing (SOP-011)

SOPs are pure Python rule-based — ZERO additional LLM calls.
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator
from agents.evidence_evaluator import evidence_evaluator
from agents.hypothesis_reviser import hypothesis_reviser
from agents.diagnostic_strategist import diagnostic_strategist
from agents.self_critique import self_critique
from agents.medical_citations import medical_citations

# Clinical SOPs (pure Python — no LLM calls)
from agents.clinical_sops_triage import (
    sop_001_triage_classification,
    sop_002_chest_pain_protocol,
    sop_003_fast_stroke_protocol,
    sop_004_respiratory_distress,
    sop_005_vital_signs_interpreter,
#     sop_006_infection_risk,
#     sop_007_sepsis_screening,
)
from agents.clinical_sops_diagnostic import (
    sop_008_lab_value_interpreter,
    sop_009_medication_safety,
    sop_010_red_flag_scanner,
    sop_011_specialist_routing,
    sop_012_confidence_calibration,
#     sop_013_demographic_adjustments,
#     sop_014_pregnancy_safety,
#     sop_015_follow_up,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the 6-agent diagnostic pipeline with parallel execution."""

    async def run_pipeline(
        self,
        message: str,
        session_state: Dict[str, Any],
        user_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Run the 6-agent pipeline on a patient message.
        Optimized with parallel agent execution where possible.
        """
        is_new_user = not (user_context and user_context.get("is_returning_user"))
        iteration = session_state.get("iteration", 0) + 1
        conversation_history = session_state.get("conversation_history", [])
        agent_thoughts = []
        timestamp = datetime.utcnow().isoformat()

        # ===== STAGE 0: Patient History Analyzer (Returning users only, iteration 1) =====
        dynamic_severity_question = None
        ask_for_records = False
        if iteration == 1 and (not user_context or not user_context.get("medical_reports")):
            ask_for_records = True

        if not is_new_user and iteration == 1:
            agent_thoughts.append({
                "agent": "Patient History Analyzer", "thought": "Reviewing past chats and medical severity...",
                "timestamp": timestamp, "status": "processing"
            })
            try:
                from agents.history_analyzer import history_analyzer
                history_report = await history_analyzer.analyze(user_context, message)
                
                # Inject the history report explicitly into the message so down-stream agents see it
                if history_report.get("is_recurrence") or history_report.get("severity_change") not in ["new", "unknown"]:
                    dynamic_severity_question = history_report.get("dynamic_severity_question")
                    injection = f"\n\n--- CLINICAL BASELINE REPORT (From Agent) ---\n{history_report.get('clinical_baseline_summary', '')}\nSeverity Change: {history_report.get('severity_change')}\nRecurrence: {history_report.get('suspected_recurring_condition')}\n--- END BASELINE ---"
                    message = message + injection
                
                agent_thoughts.append({
                    "agent": "Patient History Analyzer", "thought": f"Severity: {history_report.get('severity_change', 'new')}. {history_report.get('suspected_recurring_condition') or ''}",
                    "timestamp": datetime.utcnow().isoformat(), "status": "completed"
                })
            except Exception as e:
                logger.error(f"Patient History Analyzer error: {e}")

        # ===== STAGE 1: Symptom Normalizer (must run first) =====
        agent_thoughts.append({
            "agent": "Symptom Normalizer", "thought": "Analyzing patient message...",
            "timestamp": timestamp, "status": "processing"
        })

        try:
            normalized = await symptom_normalizer.process(
                message=message,
                conversation_history=conversation_history,
                user_context=user_context,
            )
        except Exception as e:
            logger.error(f"Symptom Normalizer error: {e}")
            normalized = symptom_normalizer._keyword_fallback(message)

        symptom_summary = normalized.get("summary", "Symptoms extracted")
        agent_thoughts.append({
            "agent": "Symptom Normalizer", "thought": f"Identified: {symptom_summary}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # ===== Accumulate symptoms across conversation turns =====
        accumulated_symptoms = session_state.get("accumulated_symptoms", {
            "primary_symptoms": [], "secondary_symptoms": []
        })
        # Merge new symptoms (avoid duplicates by name)
        existing_names = {s.get("name") for s in accumulated_symptoms["primary_symptoms"]}
        existing_names.update(s.get("name") for s in accumulated_symptoms["secondary_symptoms"])
        for s in normalized.get("primary_symptoms", []):
            if s.get("name") and s["name"] not in existing_names:
                accumulated_symptoms["primary_symptoms"].append(s)
                existing_names.add(s["name"])
        for s in normalized.get("secondary_symptoms", []):
            if s.get("name") and s["name"] not in existing_names:
                accumulated_symptoms["secondary_symptoms"].append(s)
                existing_names.add(s["name"])
        
        # Use full accumulated symptoms for hypothesis generation
        full_normalized = {
            "primary_symptoms": accumulated_symptoms["primary_symptoms"],
            "secondary_symptoms": accumulated_symptoms["secondary_symptoms"],
            "ambiguous_signals": normalized.get("ambiguous_signals", []),
            "vital_signs_mentioned": normalized.get("vital_signs_mentioned", {}),
            "summary": f"Accumulated {len(accumulated_symptoms['primary_symptoms'])} primary + {len(accumulated_symptoms['secondary_symptoms'])} secondary symptoms across {iteration} turns"
        }

        # ===== CLINICAL SOP PIPELINE (pure Python - no LLM calls) =====
        emergency_flags = normalized.get("emergency_red_flags", [])
        vitals = session_state.get("vitals")
        
        # Demographics from context
        age = None
        gender = ""
        if user_context and user_context.get("profile"):
            age = user_context["profile"].get("age")
            gender = user_context["profile"].get("gender", "")

        # SOP-007: Sepsis Screening (qSOFA) - COMMENTED OUT FOR FUTURE USE
        # sepsis_result = sop_007_sepsis_screening(full_normalized.get("primary_symptoms", []), vitals)
        # if sepsis_result.get("activated"):
        #     agent_thoughts.append({"agent": "SOP-007 Sepsis", "thought": sepsis_result["message"],
        #         "timestamp": datetime.utcnow().isoformat(), "status": "completed"})
        #     if sepsis_result.get("emergency"):
        #         emergency_flags.append("sepsis")

        # SOP-010: Red Flag Scanner
        red_flag_result = sop_010_red_flag_scanner(full_normalized.get("primary_symptoms", []), message)
        if red_flag_result["count"] > 0:
            agent_thoughts.append({"agent": "SOP-010 Red Flags", "thought": red_flag_result["summary"],
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-001: Triage Classification
        triage_result = sop_001_triage_classification(
            symptoms=full_normalized.get("primary_symptoms", []), vitals=vitals,
            red_flags=[f["concern"] for f in red_flag_result.get("flags_found", [])],
            emergency_keywords=emergency_flags)
            
        # SOP-013: Pediatric/Geriatric Triage Adjustments - COMMENTED OUT FOR FUTURE USE
        # demo_result = sop_013_demographic_adjustments(age, vitals)
        # if demo_result.get("activated"):
        #     agent_thoughts.append({"agent": "SOP-013 Demographics", "thought": demo_result["message"],
        #         "timestamp": datetime.utcnow().isoformat(), "status": "completed"})
        #     # Escalate triage if vulnerable
        #     if triage_result["color"] in ["yellow", "green", "blue"] and demo_result["risk_modifier"] > 0:
        #         triage_result["color"] = "orange"
        #         triage_result["label"] = "URGENT (Age Adjusted)"
        #         triage_result["rationale"] += " | Escalated due to age vulnerability"

        agent_thoughts.append({"agent": "SOP-001 Triage",
            "thought": f"Triage: {triage_result['label']} | {triage_result['rationale']}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-003: FAST Stroke Check
        fast_result = sop_003_fast_stroke_protocol(full_normalized.get("primary_symptoms", []))
        if fast_result.get("fast_positive"):
            agent_thoughts.append({"agent": "SOP-003 FAST Stroke", "thought": fast_result["message"],
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})
            routing = sop_011_specialist_routing("Stroke (CVA)", "neurological")
            return {
                "message": f"**STROKE ALERT:** {fast_result['message']}\n\nRefer to: **{routing['specialist']}**",
                "hypotheses": [{"name": "Stroke (CVA)", "confidence": 95.0, "supporting": fast_result["positive_count"],
                    "contradicting": 0, "severity_class": "critical", "reasoning": fast_result["message"]}],
                "evidence": [], "questions": [], "bias_flags": [], "agent_thoughts": agent_thoughts,
                "need_more_info": False, "request_vitals": False, "vitals_needed": [], "iteration": iteration,
                "confidence_trajectory": session_state.get("confidence_trajectory", []),
                "accumulated_evidence": session_state.get("accumulated_evidence", []),
                "accumulated_symptoms": accumulated_symptoms, "revision_narrative": "FAST Stroke Protocol",
                "should_conclude": True, "conclusion_message": fast_result["message"],
                "final_recommendations": fast_result["next_actions"], "triage": triage_result,
            }

        # RED triage emergency override
        if triage_result["color"] == "red":
            return {
                "message": f"**EMERGENCY:** {triage_result['rationale']}. Seek immediate medical attention.",
                "hypotheses": [], "evidence": [], "questions": [], "bias_flags": [],
                "agent_thoughts": agent_thoughts, "need_more_info": False, "request_vitals": False,
                "vitals_needed": [], "iteration": iteration,
                "confidence_trajectory": session_state.get("confidence_trajectory", []),
                "accumulated_evidence": session_state.get("accumulated_evidence", []),
                "accumulated_symptoms": accumulated_symptoms,
                "revision_narrative": "Emergency Override by SOP-001",
                "should_conclude": True, "conclusion_message": triage_result["rationale"],
                "final_recommendations": ["Call Emergency Services immediately", "Seek ER"],
                "triage": triage_result,
            }

        # SOP-002: Chest Pain Protocol
        chest_pain_result = sop_002_chest_pain_protocol(full_normalized.get("primary_symptoms", []), vitals)
        if chest_pain_result.get("activated"):
            agent_thoughts.append({"agent": "SOP-002 Chest Pain",
                "thought": f"ACS Risk: {chest_pain_result['risk_level']}",
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-004: Respiratory Distress
        resp_result = sop_004_respiratory_distress(full_normalized.get("primary_symptoms", []), vitals)
        if resp_result.get("activated"):
            agent_thoughts.append({"agent": "SOP-004 Respiratory",
                "thought": f"Severity: {resp_result['severity']}",
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-005: Vital Signs Interpreter
        vitals_result = sop_005_vital_signs_interpreter(vitals)
        if vitals_result.get("has_vitals") and vitals_result["abnormalities"]:
            agent_thoughts.append({"agent": "SOP-005 Vitals",
                "thought": f"{vitals_result['overall_status'].upper()}: {vitals_result['summary']}",
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-006: Infection Risk - COMMENTED OUT FOR FUTURE USE
        # infection_result = sop_006_infection_risk(full_normalized.get("primary_symptoms", []), vitals, message)
        # if infection_result.get("activated"):
        #     agent_thoughts.append({"agent": "SOP-006 Infection",
        #         "thought": f"Risk: {infection_result['risk_level'].upper()} | {infection_result['isolation_advice']}",
        #         "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-014: Pregnancy Safety - COMMENTED OUT FOR FUTURE USE
        # meds = user_context.get("profile", {}).get("medications", []) if user_context else []
        # pregnancy_result = sop_014_pregnancy_safety(gender, age, full_normalized.get("primary_symptoms", []), meds, message)
        # if pregnancy_result.get("activated"):
        #     agent_thoughts.append({"agent": "SOP-014 Pregnancy",
        #         "thought": pregnancy_result["message"],
        #         "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # SOP-008: Lab Value Interpreter
        lab_result = {"findings": [], "abnormal_count": 0}
        if user_context and user_context.get("extracted_medical_records"):
            rag_text = " ".join(r.get("chunk", "") for r in user_context["extracted_medical_records"])
            lab_result = sop_008_lab_value_interpreter(rag_text)
            if lab_result["abnormal_count"] > 0:
                agent_thoughts.append({"agent": "SOP-008 Labs",
                    "thought": f"{lab_result['abnormal_count']} abnormal: {lab_result['summary']}",
                    "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

        # Build compact SOP context for downstream LLM agents
        sop_parts = []
        # if sepsis_result.get("activated"):
        #     sop_parts.append(f"SEPSIS:{sepsis_result['qsofa_score']}/3")
        if triage_result["color"] not in ("blue", "green"):
            sop_parts.append(f"TRIAGE:{triage_result['label']}")
        if chest_pain_result.get("activated"):
            sop_parts.append(f"ACS:{chest_pain_result['risk_level']}")
        if resp_result.get("activated"):
            sop_parts.append(f"RESP:{resp_result['severity']}")
        if vitals_result.get("has_vitals") and vitals_result["abnormalities"]:
            sop_parts.append(f"VITALS:{vitals_result['summary']}")
        if lab_result["abnormal_count"] > 0:
            sop_parts.append(f"LABS:{lab_result['summary']}")
        if red_flag_result["count"] > 0:
            sop_parts.append(f"FLAGS:{red_flag_result['summary']}")
        # if infection_result.get("activated"):
        #     sop_parts.append(f"INFECTION:{infection_result['risk_level']}")
        # if pregnancy_result.get("activated") and pregnancy_result.get("emergency"):
        #     sop_parts.append(f"PREGNANCY:EMERGENCY")
            
        if sop_parts:
            full_normalized["sop_findings"] = " | ".join(sop_parts)



        # ===== STAGE 2: Hypothesis Generator =====
        agent_thoughts.append({
            "agent": "Hypothesis Generator", "thought": "Generating differential diagnosis...",
            "timestamp": datetime.utcnow().isoformat(), "status": "processing"
        })

        # Always re-run hypothesis generator to incorporate new evidence from answers
        try:
            hypothesis_result = await hypothesis_generator.process(
                normalized_symptoms=full_normalized,
                user_context=user_context,
                is_new_user=is_new_user,
            )
        except Exception as e:
            logger.error(f"Hypothesis Generator error: {e}")
            hypothesis_result = hypothesis_generator._fallback_hypotheses(full_normalized)
        hypotheses = hypothesis_result.get("hypotheses", [])

        agent_thoughts.append({
            "agent": "Hypothesis Generator",
            "thought": f"{'Generated' if iteration == 1 else 'Updated'} {len(hypotheses)} hypotheses. Top: {hypotheses[0].get('name', 'N/A') if hypotheses else 'None'}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # ===== STAGE 3: Evidence Evaluator (LOCAL FALLBACK — saves LLM call) =====
        agent_thoughts.append({
            "agent": "Evidence Evaluator", "thought": "Evaluating evidence (rule-based)...",
            "timestamp": datetime.utcnow().isoformat(), "status": "processing"
        })

        vitals = session_state.get("vitals")
        try:
            # Build evidence list locally (same as what process() does internally)
            all_evidence = []
            for s in full_normalized.get("primary_symptoms", []):
                all_evidence.append({
                    "type": "symptom",
                    "finding": s.get("name", ""),
                    "detail": f"{s.get('character', '')} {s.get('severity', '')} {s.get('duration', '')}".strip(),
                })
            for s in full_normalized.get("secondary_symptoms", []):
                all_evidence.append({
                    "type": "symptom",
                    "finding": s.get("name", ""),
                    "detail": s.get("raw_text", ""),
                })
            if vitals:
                for key, value in vitals.items():
                    if value is not None:
                        all_evidence.append({"type": "vital_sign", "finding": key, "detail": str(value)})
            if user_context and user_context.get("is_returning_user"):
                profile = user_context.get("profile", {})
                for condition in (profile.get("known_conditions") or []):
                    all_evidence.append({"type": "medical_history", "finding": condition, "detail": "Known pre-existing condition"})
                for r in user_context.get("extracted_medical_records", []):
                    all_evidence.append({"type": "medical_report_pdf", "finding": f"Lab Result from {r.get('source')}", "detail": r.get('chunk')})

            evidence_result = evidence_evaluator._fallback_evidence(hypotheses, all_evidence)
        except Exception as e:
            logger.error(f"Evidence Evaluator error: {e}")
            evidence_result = {"evidence_ledger": [], "missing_evidence": [], "evidence_summary": "Error in evaluation"}

        evidence_ledger = evidence_result.get("evidence_ledger", [])
        agent_thoughts.append({
            "agent": "Evidence Evaluator", "thought": f"Evaluated {len(evidence_ledger)} evidence items",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # ===== STAGE 4: Hypothesis Reviser (LOCAL FALLBACK — saves LLM call) =====
        agent_thoughts.append({
            "agent": "Hypothesis Reviser", "thought": "Updating confidence scores (Bayesian)...",
            "timestamp": datetime.utcnow().isoformat(), "status": "processing"
        })

        try:
            revision_result = hypothesis_reviser._fallback_revision(hypotheses, evidence_result)
        except Exception as e:
            logger.error(f"Hypothesis Reviser error: {e}")
            revision_result = hypothesis_reviser._fallback_revision(hypotheses, evidence_result)

        revised_hypotheses = revision_result.get("revised_hypotheses", hypotheses) or hypotheses
        revision_narrative = revision_result.get("revision_narrative", "")
        agent_thoughts.append({
            "agent": "Hypothesis Reviser",
            "thought": (revision_narrative[:150] if revision_narrative else "Confidence scores updated"),
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # ===== STAGE 5+6: Diagnostic Strategist + Self-Critique (RUN IN PARALLEL) =====
        agent_thoughts.append({
            "agent": "Diagnostic Strategist", "thought": "Determining next diagnostic step...",
            "timestamp": datetime.utcnow().isoformat(), "status": "processing"
        })
        agent_thoughts.append({
            "agent": "Self-Critique", "thought": "Checking for cognitive biases...",
            "timestamp": datetime.utcnow().isoformat(), "status": "processing"
        })

        async def run_strategist():
            try:
                return await diagnostic_strategist.process(
                    hypotheses=revised_hypotheses,
                    evidence=evidence_result,
                    conversation_history=conversation_history,
                    iteration=iteration,
                    evidence_count=len(evidence_ledger) + len(session_state.get("accumulated_evidence", [])),
                    user_context=user_context,
                    is_new_user=is_new_user,
                )
            except Exception as e:
                logger.error(f"Diagnostic Strategist error: {e}")
                return diagnostic_strategist._fallback_strategy(revised_hypotheses, iteration, len(evidence_ledger), conversation_history)

        async def run_critique():
            """Self-Critique uses local fallback (saves LLM call)."""
            sop_findings = full_normalized.get("sop_findings", "")
            try:
                return self_critique._fallback_critique(revised_hypotheses, iteration, sop_findings)
            except Exception as e:
                logger.error(f"Self-Critique error: {e}")
                return self_critique._fallback_critique(revised_hypotheses, iteration, sop_findings)

        # Run strategist (LLM) and critique (local) sequentially
        strategy_result = await run_strategist()
        critique_result = await run_critique()

        # ===== SOP-012: CONFIDENCE CALIBRATION =====
        has_vitals = vitals is not None and len(vitals) > 0
        has_labs = user_context and user_context.get("extracted_medical_records") and len(user_context.get("extracted_medical_records")) > 0
        
        confidence_result = sop_012_confidence_calibration(
            hypotheses=revised_hypotheses,
            evidence_count=len(evidence_ledger),
            iteration=iteration,
            vitals_provided=has_vitals,
            lab_data_available=has_labs,
        )
        
        agent_thoughts.append({
            "agent": "SOP-012 Confidence",
            "thought": f"Quality Score: {confidence_result['evidence_quality_score']} | Band: {confidence_result['confidence_band'].upper()} | {confidence_result['reasoning']}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # Override conclusion logic with calibrated SOP-012 result
        should_conclude = confidence_result["can_conclude"]
        next_question = strategy_result.get("next_question")
        request_vitals = strategy_result.get("request_vitals", False)
        vitals_needed = strategy_result.get("vitals_needed", [])

        # When SOP-012 triggers conclusion but the LLM strategist didn't,
        # we need to generate the conclusion_message and final_recommendations ourselves
        if should_conclude and not strategy_result.get("conclusion_message"):
            top_h = revised_hypotheses[0] if revised_hypotheses else {"name": "Unknown", "confidence": 0}
            second_h = revised_hypotheses[1] if len(revised_hypotheses) > 1 else {"name": "None", "confidence": 0}
            margin = top_h.get("confidence", 0) - second_h.get("confidence", 0)

            # Get severity from KB
            severity_map = {}
            try:
                import os as _os2
                _kb2 = _os2.path.join(_os2.path.dirname(_os2.path.dirname(__file__)), "data", "diseases.json")
                with open(_kb2, "r", encoding="utf-8") as _f2:
                    for _d2 in json.load(_f2):
                        severity_map[_d2["name"]] = _d2.get("severity_class", "moderate")
            except Exception:
                pass

            top_severity = top_h.get("severity_class") or severity_map.get(top_h.get("name", ""), "moderate")
            severity_msgs = {
                "critical": "This could indicate a medical EMERGENCY. Please seek immediate medical attention.",
                "serious": "This condition requires prompt medical attention. Please consult a healthcare professional as soon as possible.",
                "moderate": "This condition should be evaluated by a healthcare professional.",
                "benign": "This is likely a mild condition, but please monitor your symptoms.",
            }

            # Get recommended tests
            rec_tests = []
            try:
                for _d3 in json.load(open(_kb2, "r", encoding="utf-8")):
                    if _d3["name"].lower() == top_h.get("name", "").lower():
                        rec_tests = _d3.get("lab_tests", [])
                        break
            except Exception:
                pass

            strategy_result["conclusion_message"] = (
                f"Based on {iteration} rounds of systematic analysis, the most likely diagnosis is "
                f"**{top_h.get('name', 'Unknown')}** with {top_h.get('confidence', 0):.1f}% confidence. "
                f"This was determined by evaluating {len(evidence_ledger)} pieces of clinical evidence. "
                f"The confidence margin over the next most likely diagnosis "
                f"({second_h.get('name', 'Unknown')}) is {margin:.1f}%. "
                f"{severity_msgs.get(top_severity, severity_msgs['moderate'])}"
            )
            strategy_result["severity_class"] = top_severity
            strategy_result["final_recommendations"] = [
                f"Key findings supporting {top_h.get('name', '')}: {top_h.get('reasoning', 'Multiple supporting clinical features')}",
                f"Recommended diagnostic tests: {', '.join(rec_tests[:5])}" if rec_tests else "Confirm with appropriate diagnostic testing",
                "Consult a healthcare professional for proper evaluation and confirmation",
                "Review the evidence ledger for supporting and contradicting findings",
            ]

        agent_thoughts.append({
            "agent": "Diagnostic Strategist",
            "thought": "Diagnosis concluded" if should_conclude else f"Next question prepared. {'Requesting vitals.' if request_vitals else ''}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        biases = critique_result.get("biases_detected", [])
        agent_thoughts.append({
            "agent": "Self-Critique",
            "thought": f"Found {len(biases)} potential bias{'es' if len(biases) != 1 else ''}. Quality: {critique_result.get('reasoning_quality', 'acceptable')}",
            "timestamp": datetime.utcnow().isoformat(), "status": "completed"
        })

        # ===== BUILD RESPONSE =====
        if should_conclude:
            base_conclusion = strategy_result.get("conclusion_message",
                f"Based on the evidence, the most likely diagnosis is {revised_hypotheses[0].get('name', 'Unknown')}.")
            
            # Add severity-based messaging
            top_severity = strategy_result.get("severity_class", "moderate")
            if not top_severity and revised_hypotheses:
                top_severity = revised_hypotheses[0].get("severity_class", "moderate")
            severity_messages = {
                "critical": "\n\n⚠️ **EMERGENCY WARNING**: This could indicate a medical EMERGENCY. Please seek immediate medical attention. Do NOT delay.",
                "serious": "\n\n⚠️ **IMPORTANT**: This condition requires prompt medical attention. Please consult a healthcare professional as soon as possible.",
                "moderate": "\n\nPlease consult a healthcare professional for proper evaluation and treatment.",
                "benign": "\n\nThis is likely a mild condition, but please monitor your symptoms and consult a doctor if they worsen.",
            }
            response_message = base_conclusion + severity_messages.get(top_severity, severity_messages["moderate"])

            # SOP-011: Specialist Routing
            top_name = revised_hypotheses[0].get("name", "") if revised_hypotheses else ""
            top_system = ""
            try:
                import os as _os
                _kb_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "data", "diseases.json")
                with open(_kb_path, "r", encoding="utf-8") as _f:
                    for _d in json.load(_f):
                        if _d["name"] == top_name:
                            top_system = _d.get("system", "")
                            break
            except Exception:
                pass
            routing = sop_011_specialist_routing(top_name, top_system)
            response_message += f"\n\n**Recommended Specialist:** {routing['specialist']} ({routing['reasoning']})"
            agent_thoughts.append({"agent": "SOP-011 Specialist",
                "thought": f"Refer to: {routing['specialist']}",
                "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

            # SOP-009: Medication Safety Check
            if user_context and user_context.get("is_returning_user"):
                profile = user_context.get("profile", {})
                med_safety = sop_009_medication_safety(
                    current_medications=profile.get("medications"),
                    allergies=profile.get("allergies"),
                    hypotheses=revised_hypotheses)
                if not med_safety["safe"]:
                    response_message += f"\n\n**Medication Safety Alert:** {med_safety['summary']}"
                    for alert in med_safety["alerts"]:
                        response_message += f"\n- {alert['message']}"
                    for conflict in med_safety["allergy_conflicts"]:
                        response_message += f"\n- {conflict['message']}"
                    agent_thoughts.append({"agent": "SOP-009 Med Safety",
                        "thought": f"ALERT: {med_safety['summary']}",
                        "timestamp": datetime.utcnow().isoformat(), "status": "completed"})

            # SOP-015: Follow Up Protocol - COMMENTED OUT FOR FUTURE USE
            # follow_up = sop_015_follow_up(triage_result["color"], top_name)
            # response_message += f"\n\n{follow_up['message']}"
            # agent_thoughts.append({"agent": "SOP-015 Follow-Up",
            #     "thought": f"Timeline: {follow_up['timeline']}",
            #     "timestamp": datetime.utcnow().isoformat(), "status": "completed"})
                
            # Pregnancy warnings if applicable - COMMENTED OUT FOR FUTURE USE
            # if pregnancy_result.get("activated"):
            #     response_message += f"\n\n**Pregnancy Warning:** {pregnancy_result['message']}"

            # Infection warnings if applicable - COMMENTED OUT FOR FUTURE USE
            # if infection_result.get("activated") and infection_result.get("risk_level") in ["high", "moderate"]:
            #     response_message += f"\n\n**Infection Control:** {infection_result['isolation_advice']}"

        else:
            response_message = next_question or "Could you tell me more about your symptoms?"
            
            # Override response with dynamic disease-specific question from history AI
            if iteration == 1 and dynamic_severity_question:
                response_message = f"{dynamic_severity_question}\n\n(Also: {response_message})"
            elif iteration == 1 and ask_for_records:
                proactive_msg = "Before we continue, I notice you don't have any medical records in your profile. Do you have any pre-existing medical conditions, past diagnoses, or recent lab reports? If so, please upload them via the frontend so I can securely store them in the cloud under your patient details and provide a safer, more accurate diagnosis."
                response_message = f"{response_message}\n\n**{proactive_msg}**"

        # Confidence trajectory
        confidence_snapshot = [{
            "name": h.get("name", ""), "confidence": h.get("confidence", 0), "iteration": iteration
        } for h in revised_hypotheses]

        trajectory = session_state.get("confidence_trajectory", [])
        trajectory.append({
            "iteration": iteration, "hypotheses": confidence_snapshot,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Accumulate evidence
        accumulated = session_state.get("accumulated_evidence", [])
        accumulated.extend(evidence_ledger)

        # Format evidence for frontend
        formatted_evidence = []
        for e in evidence_ledger:
            supports_list, contradicts_list = [], []
            for s in (e.get("supports", []) or []):
                supports_list.append(s.get("hypothesis", s) if isinstance(s, dict) else str(s))
            for c in (e.get("contradicts", []) or []):
                contradicts_list.append(c.get("hypothesis", c) if isinstance(c, dict) else str(c))
            formatted_evidence.append({
                "finding": e.get("finding", e.get("description", "")),
                "supports": supports_list, "contradicts": contradicts_list, "confidence": 0.85
            })

        # Format hypotheses for frontend — includes severity_class
        formatted_hypotheses = [{
            "name": h.get("name", "Unknown"),
            "confidence": round(h.get("confidence", h.get("new_confidence", 0)), 1),
            "supporting": h.get("supporting", h.get("supporting_count", 0)),
            "contradicting": h.get("contradicting", h.get("contradicting_count", 0)),
            "reasoning": h.get("reasoning", h.get("change_reason", "")),
            "status": h.get("status", "stable"),
            "severity_class": h.get("severity_class", "moderate"),
            "differentiating_factor": h.get("differentiating_factor", ""),
        } for h in revised_hypotheses]

        # Format bias flags
        formatted_biases = [{
            "type": b.get("type", "unknown"),
            "bias": b.get("type", "unknown").replace("_", " ").title(),
            "description": b.get("description", ""),
            "severity": b.get("severity", "low"),
            "mitigation": b.get("mitigation", "")
        } for b in biases]

        # ===== MEDICAL EVIDENCE CITATIONS (Proof Package) =====
        proof_package = {}
        if should_conclude:
            try:
                proof_package = medical_citations.generate_diagnosis_proof_package(
                    hypotheses=revised_hypotheses,
                    evidence_ledger=evidence_ledger,
                )
                agent_thoughts.append({
                    "agent": "Medical Citation Engine",
                    "thought": f"Generated proof package: {proof_package.get('total_evidence_cited', 0)} evidence citations across {proof_package.get('total_diseases_referenced', 0)} diseases. ICD-10 codes: {', '.join(proof_package.get('icd10_codes_used', []))}",
                    "timestamp": datetime.utcnow().isoformat(), "status": "completed"
                })

                # Append citation summary to the conclusion message
                if proof_package.get("hypothesis_citations"):
                    top_cite = proof_package["hypothesis_citations"][0]
                    response_message += (
                        f"\n\n**Medical Reference:**\n"
                        f"- ICD-10 Code: **{top_cite.get('icd10_code', 'N/A')}** ({top_cite.get('icd10_classification', '')})\n"
                        f"- Clinical Authority: {top_cite.get('clinical_authority', 'N/A')}\n"
                        f"- Confirmatory Tests: {', '.join(top_cite.get('confirmatory_tests', [])[:5])}\n"
                        f"- {top_cite.get('verification_note', '')}"
                    )
            except Exception as e:
                logger.error(f"Medical Citation Engine error: {e}")

        return {
            "message": response_message,
            "hypotheses": formatted_hypotheses,
            "evidence": formatted_evidence,
            "questions": [next_question] if next_question and not should_conclude else [],
            "bias_flags": formatted_biases,
            "agent_thoughts": agent_thoughts,
            "need_more_info": not should_conclude,
            "request_vitals": request_vitals,
            "vitals_needed": vitals_needed,
            "iteration": iteration,
            "confidence_trajectory": trajectory,
            "accumulated_evidence": accumulated,
            "accumulated_symptoms": accumulated_symptoms,
            "revision_narrative": revision_narrative,
            "should_conclude": should_conclude,
            "conclusion_message": strategy_result.get("conclusion_message", "") if should_conclude else "",
            "final_recommendations": strategy_result.get("final_recommendations", []) if should_conclude else [],
            "medical_citations": proof_package if should_conclude else {},
        }


# Singleton
orchestrator = AgentOrchestrator()
