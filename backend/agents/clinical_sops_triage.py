"""
Clinical SOPs Part 1: Triage, Emergency Protocols, and Vital Signs
SOPs 006-010: Real-time clinical protocols used in hospitals/emergency care.

These are pure Python rule-based — NO LLM calls. Zero performance impact.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# SOP-001: TRIAGE SEVERITY CLASSIFICATION (ESI-based)
# Real protocol: Emergency Severity Index used in all ERs worldwide
# =============================================================================

TRIAGE_LEVELS = {
    "emergency": {"level": 1, "color": "red", "label": "EMERGENCY — Immediate"},
    "urgent":    {"level": 2, "color": "orange", "label": "URGENT — Within hours"},
    "moderate":  {"level": 3, "color": "yellow", "label": "MODERATE — Same day"},
    "mild":      {"level": 4, "color": "green", "label": "MILD — Routine"},
    "routine":   {"level": 5, "color": "blue", "label": "ROUTINE — Self-care"},
}

def sop_001_triage_classification(
    symptoms: List[Dict],
    vitals: Optional[Dict] = None,
    red_flags: Optional[List[str]] = None,
    emergency_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    SOP-001: Classify patient urgency using ESI-based triage.
    Returns: {level, color, label, rationale, triggers}
    """
    triggers = []
    symptom_names = {s.get("name", "").lower() for s in symptoms}

    # ---- RED (Emergency) triggers ----
    # Cardiac arrest / MI indicators
    if {"chest_pain", "diaphoresis"} <= symptom_names:
        triggers.append("Chest pain with sweating — suspect ACS")
    if any(k in symptom_names for k in ["crushing_chest_pain", "severe_chest_pain"]):
        triggers.append("Severe/crushing chest pain")

    # Stroke indicators (FAST)
    fast_symptoms = {"facial_drooping", "face_drooping", "arm_weakness",
                     "speech_difficulty", "slurred_speech", "facial_weakness"}
    if fast_symptoms & symptom_names:
        triggers.append("FAST stroke symptoms detected")

    # Respiratory failure
    if vitals and vitals.get("oxygen_saturation") and vitals["oxygen_saturation"] < 90:
        triggers.append(f"Critical hypoxia: SpO2 = {vitals['oxygen_saturation']}%")

    # Severe hypotension
    if vitals and vitals.get("blood_pressure"):
        bp = _parse_blood_pressure(vitals["blood_pressure"])
        if bp and bp["systolic"] < 80:
            triggers.append(f"Severe hypotension: BP = {vitals['blood_pressure']}")

    # From emergency keywords detected by symptom normalizer
    if emergency_keywords:
        triggers.extend([f"Emergency keyword: {k}" for k in emergency_keywords])

    # Loss of consciousness / syncope
    if any(k in symptom_names for k in ["syncope", "loss_of_consciousness", "unresponsive"]):
        triggers.append("Loss of consciousness / syncope")

    if triggers:
        return {**TRIAGE_LEVELS["emergency"], "rationale": "; ".join(triggers), "triggers": triggers}

    # ---- ORANGE (Urgent) triggers ----
    urgent_triggers = []

    if vitals and vitals.get("temperature") and vitals["temperature"] >= 102.0:
        urgent_triggers.append(f"High fever: {vitals['temperature']}°F")
    # Convert Celsius if needed
    if vitals and vitals.get("temperature") and 38.9 <= vitals["temperature"] <= 45:
        urgent_triggers.append(f"High fever: {vitals['temperature']}°C")

    if vitals and vitals.get("heart_rate") and vitals["heart_rate"] > 130:
        urgent_triggers.append(f"Severe tachycardia: HR = {vitals['heart_rate']}")

    if vitals and vitals.get("oxygen_saturation") and 90 <= vitals["oxygen_saturation"] < 92:
        urgent_triggers.append(f"Low SpO2: {vitals['oxygen_saturation']}%")

    if "hemoptysis" in symptom_names:
        urgent_triggers.append("Hemoptysis (coughing blood)")

    if "chest_pain" in symptom_names:
        urgent_triggers.append("Chest pain present (needs cardiac workup)")

    # Red flags from disease KB
    if red_flags:
        urgent_triggers.extend([f"Red flag: {rf}" for rf in red_flags[:3]])

    if urgent_triggers:
        return {**TRIAGE_LEVELS["urgent"], "rationale": "; ".join(urgent_triggers), "triggers": urgent_triggers}

    # ---- YELLOW (Moderate) triggers ----
    moderate_triggers = []

    if vitals and vitals.get("temperature") and (100.4 <= vitals["temperature"] < 102.0):
        moderate_triggers.append("Moderate fever")
    if vitals and vitals.get("heart_rate") and (100 < vitals["heart_rate"] <= 130):
        moderate_triggers.append("Tachycardia")

    moderate_symptoms = {"dyspnea", "abdominal_pain", "vomiting", "severe_headache"}
    found_moderate = moderate_symptoms & symptom_names
    if found_moderate:
        moderate_triggers.append(f"Moderate symptoms: {', '.join(found_moderate)}")

    if moderate_triggers:
        return {**TRIAGE_LEVELS["moderate"], "rationale": "; ".join(moderate_triggers), "triggers": moderate_triggers}

    # ---- GREEN (Mild) ----
    mild_symptoms = {"headache", "cough", "fatigue", "nausea", "dizziness", "rash"}
    if mild_symptoms & symptom_names:
        return {**TRIAGE_LEVELS["mild"],
                "rationale": "Mild symptoms without danger signs",
                "triggers": list(mild_symptoms & symptom_names)}

    # ---- BLUE (Routine) ----
    return {**TRIAGE_LEVELS["routine"],
            "rationale": "No urgent findings identified",
            "triggers": []}


# =============================================================================
# SOP-002: CHEST PAIN PROTOCOL (ACS Pathway)
# Real protocol: Used in every ER for acute coronary syndrome screening
# =============================================================================

def sop_002_chest_pain_protocol(symptoms: List[Dict], vitals: Optional[Dict] = None) -> Dict[str, Any]:
    """
    SOP-002: ACS screening pathway for chest pain patients.
    Returns: {activated, risk_level, findings, acs_likelihood, next_actions}
    """
    symptom_names = {s.get("name", "").lower() for s in symptoms}

    if "chest_pain" not in symptom_names:
        return {"activated": False, "reason": "No chest pain reported"}

    findings = []
    acs_score = 0  # Higher = more likely ACS

    # Pain character
    characters = set()
    for s in symptoms:
        if s.get("name", "").lower() == "chest_pain":
            char = s.get("character", "").lower()
            characters.add(char)

    if any(c in characters for c in ["crushing", "squeezing", "pressure", "heavy"]):
        findings.append("Crushing/pressure-type pain — classic ACS")
        acs_score += 3
    elif any(c in characters for c in ["burning"]):
        findings.append("Burning pain — more suggestive of GERD")
        acs_score -= 1
    elif any(c in characters for c in ["sharp", "stabbing"]):
        findings.append("Sharp/stabbing — less typical for ACS, consider PE/pleurisy")
        acs_score += 0

    # Radiation
    radiation_symptoms = {"arm_pain", "jaw_pain", "back_pain", "neck_pain"}
    if radiation_symptoms & symptom_names:
        findings.append(f"Radiation present: {radiation_symptoms & symptom_names}")
        acs_score += 2

    # Associated symptoms
    if "diaphoresis" in symptom_names:
        findings.append("Diaphoresis — strong ACS indicator")
        acs_score += 3
    if "nausea" in symptom_names:
        findings.append("Nausea — associated with inferior MI")
        acs_score += 1
    if "dyspnea" in symptom_names:
        findings.append("Dyspnea with chest pain — concerning")
        acs_score += 2

    # Vitals
    if vitals:
        if vitals.get("heart_rate") and vitals["heart_rate"] > 100:
            findings.append(f"Tachycardia: HR {vitals['heart_rate']}")
            acs_score += 1
        bp = _parse_blood_pressure(vitals.get("blood_pressure", ""))
        if bp and bp["systolic"] > 180:
            findings.append(f"Hypertensive: BP {vitals['blood_pressure']}")
            acs_score += 1

    # Anti-ACS indicators
    if "heartburn" in symptom_names or "regurgitation" in symptom_names:
        findings.append("GI symptoms present — consider GERD")
        acs_score -= 2

    # Risk classification
    if acs_score >= 5:
        risk = "HIGH"
        actions = ["Immediate ECG", "Troponin levels", "Aspirin if not allergic", "Emergency referral"]
    elif acs_score >= 2:
        risk = "MODERATE"
        actions = ["ECG recommended", "Serial troponins", "Monitor closely"]
    else:
        risk = "LOW"
        actions = ["Consider non-cardiac causes", "Trial of antacids if burning"]

    return {
        "activated": True,
        "risk_level": risk,
        "acs_score": acs_score,
        "findings": findings,
        "acs_likelihood": "high" if acs_score >= 5 else "moderate" if acs_score >= 2 else "low",
        "next_actions": actions,
    }


# =============================================================================
# SOP-003: STROKE DETECTION (FAST Protocol)
# Real protocol: Face-Arm-Speech-Time — internationally recognized
# =============================================================================

FAST_KEYWORDS = {
    "face": ["facial_drooping", "face_drooping", "facial_weakness", "face_numb",
             "drooping", "facial_numbness", "one_side_face"],
    "arm":  ["arm_weakness", "arm_numbness", "cant_lift_arm", "arm_heavy",
             "weakness_one_side", "hemiparesis", "hemiplegia"],
    "speech": ["speech_difficulty", "slurred_speech", "cant_speak", "aphasia",
               "speech_slurred", "difficulty_speaking", "garbled_speech"],
}

def sop_003_fast_stroke_protocol(symptoms: List[Dict]) -> Dict[str, Any]:
    """
    SOP-003: FAST stroke detection protocol.
    Returns: {activated, fast_positive, components, urgency, message}
    """
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    raw_texts = {s.get("raw_text", "").lower() for s in symptoms}
    all_text = " ".join(raw_texts)

    components = {"face": False, "arm": False, "speech": False}

    for component, keywords in FAST_KEYWORDS.items():
        for kw in keywords:
            if kw in symptom_names or kw.replace("_", " ") in all_text:
                components[component] = True
                break

    # Also check raw text for natural language
    face_phrases = ["face droop", "face is drooping", "side of my face", "face numb", "face feels"]
    arm_phrases = ["can't lift", "arm weak", "arm is weak", "arm feels heavy", "can't move my arm"]
    speech_phrases = ["can't speak", "speech is slurred", "words come out wrong", "trouble speaking"]

    for phrase in face_phrases:
        if phrase in all_text:
            components["face"] = True
    for phrase in arm_phrases:
        if phrase in all_text:
            components["arm"] = True
    for phrase in speech_phrases:
        if phrase in all_text:
            components["speech"] = True

    positive_count = sum(components.values())
    fast_positive = positive_count >= 1  # ANY component = emergency

    if not fast_positive:
        return {"activated": False, "fast_positive": False, "reason": "No FAST symptoms detected"}

    return {
        "activated": True,
        "fast_positive": True,
        "components": components,
        "positive_count": positive_count,
        "urgency": "EMERGENCY",
        "message": f"STROKE ALERT: {positive_count}/3 FAST components positive. "
                   f"Face: {'YES' if components['face'] else 'no'}, "
                   f"Arm: {'YES' if components['arm'] else 'no'}, "
                   f"Speech: {'YES' if components['speech'] else 'no'}. "
                   f"TIME IS CRITICAL — seek emergency care immediately.",
        "time_warning": "Every minute matters. Brain tissue is lost rapidly during a stroke.",
        "next_actions": ["Call emergency services (911/108)", "Note exact time symptoms started",
                         "Do NOT give food or water", "Keep patient calm and lying down"],
    }


# =============================================================================
# SOP-004: RESPIRATORY DISTRESS PROTOCOL
# Real protocol: Used in COVID/asthma/pneumonia triage
# =============================================================================

def sop_004_respiratory_distress(symptoms: List[Dict], vitals: Optional[Dict] = None) -> Dict[str, Any]:
    """
    SOP-004: Respiratory distress assessment.
    Returns: {activated, severity, findings, next_actions}
    """
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    resp_symptoms = {"dyspnea", "wheezing", "chest_tightness", "cough",
                     "productive_cough", "dry_cough", "hemoptysis", "stridor"}

    found = resp_symptoms & symptom_names
    if not found and not (vitals and vitals.get("oxygen_saturation")):
        return {"activated": False, "reason": "No respiratory symptoms or SpO2 data"}

    findings = []
    severity = "mild"

    # SpO2 assessment
    if vitals and vitals.get("oxygen_saturation"):
        spo2 = vitals["oxygen_saturation"]
        if spo2 < 88:
            findings.append(f"CRITICAL hypoxia: SpO2 = {spo2}%")
            severity = "critical"
        elif spo2 < 92:
            findings.append(f"Significant hypoxia: SpO2 = {spo2}%")
            severity = "severe"
        elif spo2 < 95:
            findings.append(f"Mild hypoxia: SpO2 = {spo2}%")
            severity = max(severity, "moderate", key=lambda x: ["mild", "moderate", "severe", "critical"].index(x))

    # Respiratory rate
    if vitals and vitals.get("respiratory_rate"):
        rr = vitals["respiratory_rate"]
        if rr > 30:
            findings.append(f"Severe tachypnea: RR = {rr}")
            severity = "severe"
        elif rr > 24:
            findings.append(f"Tachypnea: RR = {rr}")
            severity = max(severity, "moderate", key=lambda x: ["mild", "moderate", "severe", "critical"].index(x))

    # Symptom combination assessment
    if "hemoptysis" in symptom_names:
        findings.append("Hemoptysis — consider PE, TB, or malignancy")
        severity = max(severity, "severe", key=lambda x: ["mild", "moderate", "severe", "critical"].index(x))

    if {"dyspnea", "chest_pain"} <= symptom_names:
        findings.append("Dyspnea + chest pain — consider PE, pneumonia, or cardiac cause")
        severity = max(severity, "moderate", key=lambda x: ["mild", "moderate", "severe", "critical"].index(x))

    if {"fever", "cough"} <= symptom_names or {"fever", "productive_cough"} <= symptom_names:
        findings.append("Fever + cough — infectious etiology likely (pneumonia/COVID)")

    if found:
        findings.append(f"Respiratory symptoms present: {', '.join(found)}")

    actions = {
        "critical": ["Immediate emergency care", "Supplemental oxygen", "Prepare for intubation"],
        "severe": ["Urgent medical attention", "Monitor SpO2 continuously", "Consider nebulizer/oxygen"],
        "moderate": ["Medical evaluation within hours", "Monitor SpO2", "Rest and hydration"],
        "mild": ["Monitor symptoms", "Seek care if worsening", "Avoid triggers"],
    }

    return {
        "activated": True,
        "severity": severity,
        "findings": findings,
        "next_actions": actions.get(severity, actions["mild"]),
    }


# =============================================================================
# SOP-005: VITAL SIGNS INTERPRETER
# Real protocol: Standard nursing/triage vital signs assessment
# =============================================================================

def sop_005_vital_signs_interpreter(vitals: Optional[Dict]) -> Dict[str, Any]:
    """
    SOP-005: Interpret all provided vital signs against clinical ranges.
    Returns: {has_vitals, abnormalities, summary, overall_status}
    """
    if not vitals:
        return {"has_vitals": False, "abnormalities": [], "summary": "No vitals provided",
                "overall_status": "unknown"}

    abnormalities = []
    normal_count = 0
    total_checked = 0

    # Blood Pressure
    if vitals.get("blood_pressure"):
        total_checked += 1
        bp = _parse_blood_pressure(vitals["blood_pressure"])
        if bp:
            sys, dia = bp["systolic"], bp["diastolic"]
            if sys >= 180 or dia >= 120:
                abnormalities.append({"vital": "blood_pressure", "value": vitals["blood_pressure"],
                                       "status": "critical", "interpretation": "Hypertensive crisis"})
            elif sys >= 140 or dia >= 90:
                abnormalities.append({"vital": "blood_pressure", "value": vitals["blood_pressure"],
                                       "status": "elevated", "interpretation": "Hypertension Stage 1-2"})
            elif sys < 90 or dia < 60:
                abnormalities.append({"vital": "blood_pressure", "value": vitals["blood_pressure"],
                                       "status": "low", "interpretation": "Hypotension — risk of shock"})
            else:
                normal_count += 1

    # Heart Rate
    if vitals.get("heart_rate"):
        total_checked += 1
        hr = vitals["heart_rate"]
        if hr > 150:
            abnormalities.append({"vital": "heart_rate", "value": hr,
                                   "status": "critical", "interpretation": "Severe tachycardia"})
        elif hr > 100:
            abnormalities.append({"vital": "heart_rate", "value": hr,
                                   "status": "elevated", "interpretation": "Tachycardia"})
        elif hr < 50:
            abnormalities.append({"vital": "heart_rate", "value": hr,
                                   "status": "low", "interpretation": "Bradycardia"})
        else:
            normal_count += 1

    # Temperature
    if vitals.get("temperature"):
        total_checked += 1
        temp = vitals["temperature"]
        # Handle both F and C (>45 likely Fahrenheit)
        if temp > 45:  # Fahrenheit
            if temp >= 104:
                abnormalities.append({"vital": "temperature", "value": f"{temp}F",
                                       "status": "critical", "interpretation": "Hyperpyrexia — dangerous"})
            elif temp >= 100.4:
                abnormalities.append({"vital": "temperature", "value": f"{temp}F",
                                       "status": "elevated", "interpretation": "Fever"})
            elif temp < 95:
                abnormalities.append({"vital": "temperature", "value": f"{temp}F",
                                       "status": "low", "interpretation": "Hypothermia"})
            else:
                normal_count += 1
        else:  # Celsius
            if temp >= 40:
                abnormalities.append({"vital": "temperature", "value": f"{temp}C",
                                       "status": "critical", "interpretation": "Hyperpyrexia — dangerous"})
            elif temp >= 38:
                abnormalities.append({"vital": "temperature", "value": f"{temp}C",
                                       "status": "elevated", "interpretation": "Fever"})
            elif temp < 35:
                abnormalities.append({"vital": "temperature", "value": f"{temp}C",
                                       "status": "low", "interpretation": "Hypothermia"})
            else:
                normal_count += 1

    # Oxygen Saturation
    if vitals.get("oxygen_saturation"):
        total_checked += 1
        spo2 = vitals["oxygen_saturation"]
        if spo2 < 88:
            abnormalities.append({"vital": "oxygen_saturation", "value": f"{spo2}%",
                                   "status": "critical", "interpretation": "Severe hypoxia"})
        elif spo2 < 92:
            abnormalities.append({"vital": "oxygen_saturation", "value": f"{spo2}%",
                                   "status": "low", "interpretation": "Hypoxia — supplemental O2 needed"})
        elif spo2 < 95:
            abnormalities.append({"vital": "oxygen_saturation", "value": f"{spo2}%",
                                   "status": "borderline", "interpretation": "Borderline low oxygen"})
        else:
            normal_count += 1

    # Respiratory Rate
    if vitals.get("respiratory_rate"):
        total_checked += 1
        rr = vitals["respiratory_rate"]
        if rr > 30:
            abnormalities.append({"vital": "respiratory_rate", "value": rr,
                                   "status": "critical", "interpretation": "Severe tachypnea"})
        elif rr > 20:
            abnormalities.append({"vital": "respiratory_rate", "value": rr,
                                   "status": "elevated", "interpretation": "Tachypnea"})
        elif rr < 12:
            abnormalities.append({"vital": "respiratory_rate", "value": rr,
                                   "status": "low", "interpretation": "Bradypnea"})
        else:
            normal_count += 1

    # Overall status
    critical_count = sum(1 for a in abnormalities if a["status"] == "critical")
    if critical_count > 0:
        overall = "critical"
    elif len(abnormalities) > 0:
        overall = "abnormal"
    elif total_checked > 0:
        overall = "normal"
    else:
        overall = "unknown"

    summary_parts = []
    for a in abnormalities:
        summary_parts.append(f"{a['vital'].replace('_', ' ').title()}: {a['value']} ({a['interpretation']})")

    return {
        "has_vitals": total_checked > 0,
        "abnormalities": abnormalities,
        "normal_count": normal_count,
        "total_checked": total_checked,
        "overall_status": overall,
        "summary": "; ".join(summary_parts) if summary_parts else "All vitals within normal range",
    }
# =============================================================================
# SOP-006: INFECTION RISK PROTOCOL
# Real protocol: Post-COVID isolation triage
# =============================================================================

def sop_006_infection_risk(symptoms: List[Dict], vitals: Optional[Dict] = None, raw_message: str = "") -> Dict[str, Any]:
    """
    SOP-006: Screens for contagious diseases based on symptoms and exposure.
    Returns: {activated, risk_level, findings, isolation_advice}
    """
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    message_lower = raw_message.lower()
    
    findings = []
    risk_level = "low"
    
    # Handle C and F temps
    temp = vitals.get("temperature", 0) if vitals else 0
    has_fever_temp = temp > 100.4 if temp > 45 else temp > 38.0
    
    has_fever = "fever" in symptom_names or has_fever_temp
    has_resp = any(s in symptom_names for s in ["cough", "sore_throat", "runny_nose", "anosmia"])
    has_exposure = any(kw in message_lower for kw in ["travel", "contact", "exposed", "covid", "sick person", "recently returned"])
    
    if has_fever and has_resp and has_exposure:
        findings.append("Fever + respiratory symptoms + exposure history.")
        risk_level = "high"
    elif has_fever and has_resp:
        findings.append("Fever + respiratory symptoms.")
        risk_level = "moderate"
    elif has_exposure:
        findings.append("Exposure history without active symptoms.")
        risk_level = "low_monitor"
        
    if findings:
        return {
            "activated": True,
            "risk_level": risk_level,
            "findings": findings,
            "isolation_advice": "High risk of communicable infection. Isolate immediately." if risk_level == "high" else "Standard precautions."
        }
    return {"activated": False}


# =============================================================================
# SOP-007: SEPSIS SCREENING (qSOFA)
# Real protocol: Quick Sequential Organ Failure Assessment
# =============================================================================

def sop_007_sepsis_screening(symptoms: List[Dict], vitals: Optional[Dict] = None) -> Dict[str, Any]:
    """
    SOP-007: qSOFA Sepsis criteria check.
    Returns: {activated, qsofa_score, emergency, findings}
    """
    if not vitals and not symptoms:
        return {"activated": False}
        
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    qsofa_score = 0
    findings = []
    
    # 1. Altered mental status
    ams_symptoms = {"confusion", "lethargy", "unresponsive", "delirium", "altered_mental_status"}
    if ams_symptoms & symptom_names:
        qsofa_score += 1
        findings.append("Altered mental status")
        
    # 2. Respiratory rate >= 22
    if vitals and vitals.get("respiratory_rate", 0) >= 22:
        qsofa_score += 1
        findings.append(f"Tachypnea (RR {vitals['respiratory_rate']})")
        
    # 3. Systolic BP <= 100
    if vitals and vitals.get("blood_pressure"):
        bp = _parse_blood_pressure(vitals["blood_pressure"])
        if bp and bp["systolic"] <= 100:
            qsofa_score += 1
            findings.append(f"Hypotension (sBP {bp['systolic']})")
        
    if qsofa_score >= 2:
        return {
            "activated": True,
            "qsofa_score": qsofa_score,
            "emergency": True,
            "findings": findings,
            "message": f"SEPSIS ALERT: qSOFA score {qsofa_score}/3. Immediate emergency evaluation required."
        }
        
    return {"activated": False, "qsofa_score": qsofa_score}


# =============================================================================
# HELPER: Blood pressure parser
# =============================================================================

def _parse_blood_pressure(bp_str) -> Optional[Dict[str, int]]:
    """Parse blood pressure string like '120/80' into systolic/diastolic."""
    if not bp_str or not isinstance(bp_str, str):
        return None
    match = re.match(r"(\d+)\s*/\s*(\d+)", str(bp_str))
    if match:
        return {"systolic": int(match.group(1)), "diastolic": int(match.group(2))}
    return None
