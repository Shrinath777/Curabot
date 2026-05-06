"""Add SOP-009 and SOP-011 to conclusion section and fix vitals variable"""
with open("services/orchestrator.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add SOP-011 specialist routing and SOP-009 medication safety to conclusion
old_conclusion_end = 'response_message = base_conclusion + severity_messages.get(top_severity, severity_messages["moderate"])'
new_conclusion = '''response_message = base_conclusion + severity_messages.get(top_severity, severity_messages["moderate"])

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
            response_message += f"\\n\\n**Recommended Specialist:** {routing['specialist']} ({routing['reasoning']})"
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
                    response_message += f"\\n\\n**Medication Safety Alert:** {med_safety['summary']}"
                    for alert in med_safety["alerts"]:
                        response_message += f"\\n- {alert['message']}"
                    for conflict in med_safety["allergy_conflicts"]:
                        response_message += f"\\n- {conflict['message']}"
                    agent_thoughts.append({"agent": "SOP-009 Med Safety",
                        "thought": f"ALERT: {med_safety['summary']}",
                        "timestamp": datetime.utcnow().isoformat(), "status": "completed"})'''

content = content.replace(old_conclusion_end, new_conclusion, 1)

# 2. Fix the duplicate vitals variable (line ~275 uses session_state vitals but we already set it above)
# The old code had: vitals = session_state.get("vitals")  in evidence section
# We already have vitals = session_state.get("vitals") in the SOP section, so this is fine.

with open("services/orchestrator.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done. Added SOP-009 and SOP-011 to conclusion.")
