"""Fix orchestrator.py to use SOP-012 for confidence calibration"""
import json
import datetime

with open("services/orchestrator.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the section after run_strategist() and run_critique()
old_logic = """        should_conclude = strategy_result.get("should_conclude", False)
        next_question = strategy_result.get("next_question")
        request_vitals = strategy_result.get("request_vitals", False)
        vitals_needed = strategy_result.get("vitals_needed", [])"""

new_logic = """        # ===== SOP-012: CONFIDENCE CALIBRATION =====
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
        vitals_needed = strategy_result.get("vitals_needed", [])"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open("services/orchestrator.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully added SOP-012 to orchestrator.py")
else:
    print("Could not find the target logic block to replace.")
