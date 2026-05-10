"""
Clinical SOPs Part 2: Lab Values, Medication Safety, Red Flags, Specialist Routing, Confidence
SOPs 011-015: Diagnostic support protocols.

These are pure Python rule-based — NO LLM calls. Zero performance impact.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# SOP-008: LAB VALUE INTERPRETER
# Real protocol: Standard clinical reference ranges
# =============================================================================

# Common lab reference ranges
LAB_REFERENCE_RANGES = {
    "hemoglobin": {"unit": "g/dL", "low": 12.0, "high": 17.5,
                   "critical_low": 7.0, "critical_high": 20.0,
                   "low_meaning": "Anemia", "high_meaning": "Polycythemia"},
    "hb": {"unit": "g/dL", "low": 12.0, "high": 17.5,
           "critical_low": 7.0, "critical_high": 20.0,
           "low_meaning": "Anemia", "high_meaning": "Polycythemia"},
    "glucose": {"unit": "mg/dL", "low": 70, "high": 100,
                "critical_low": 40, "critical_high": 400,
                "low_meaning": "Hypoglycemia", "high_meaning": "Diabetes risk"},
    "blood_sugar": {"unit": "mg/dL", "low": 70, "high": 140,
                    "critical_low": 40, "critical_high": 400,
                    "low_meaning": "Hypoglycemia", "high_meaning": "Diabetes risk"},
    "fasting_glucose": {"unit": "mg/dL", "low": 70, "high": 100,
                        "critical_low": 40, "critical_high": 400,
                        "low_meaning": "Hypoglycemia", "high_meaning": "Diabetes"},
    "hba1c": {"unit": "%", "low": 4.0, "high": 5.7,
              "critical_low": 3.0, "critical_high": 14.0,
              "low_meaning": "Low glycation", "high_meaning": "Poor diabetic control"},
    "cholesterol": {"unit": "mg/dL", "low": 0, "high": 200,
                    "critical_low": 0, "critical_high": 300,
                    "low_meaning": "Normal", "high_meaning": "Hypercholesterolemia"},
    "ldl": {"unit": "mg/dL", "low": 0, "high": 100,
            "critical_low": 0, "critical_high": 190,
            "low_meaning": "Normal", "high_meaning": "High LDL — cardiovascular risk"},
    "hdl": {"unit": "mg/dL", "low": 40, "high": 100,
            "critical_low": 20, "critical_high": 100,
            "low_meaning": "Low HDL — cardiovascular risk", "high_meaning": "Protective"},
    "triglycerides": {"unit": "mg/dL", "low": 0, "high": 150,
                      "critical_low": 0, "critical_high": 500,
                      "low_meaning": "Normal", "high_meaning": "Hypertriglyceridemia"},
    "creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.2,
                   "critical_low": 0.3, "critical_high": 10.0,
                   "low_meaning": "Low muscle mass", "high_meaning": "Kidney dysfunction"},
    "wbc": {"unit": "cells/mcL", "low": 4000, "high": 11000,
            "critical_low": 2000, "critical_high": 30000,
            "low_meaning": "Leukopenia — infection risk", "high_meaning": "Leukocytosis — infection/inflammation"},
    "platelet": {"unit": "cells/mcL", "low": 150000, "high": 400000,
                 "critical_low": 50000, "critical_high": 1000000,
                 "low_meaning": "Thrombocytopenia — bleeding risk", "high_meaning": "Thrombocytosis"},
    "platelets": {"unit": "cells/mcL", "low": 150000, "high": 400000,
                  "critical_low": 50000, "critical_high": 1000000,
                  "low_meaning": "Thrombocytopenia — bleeding risk", "high_meaning": "Thrombocytosis"},
    "tsh": {"unit": "mIU/L", "low": 0.4, "high": 4.0,
            "critical_low": 0.01, "critical_high": 10.0,
            "low_meaning": "Hyperthyroidism", "high_meaning": "Hypothyroidism"},
    "troponin": {"unit": "ng/mL", "low": 0, "high": 0.04,
                 "critical_low": 0, "critical_high": 0.1,
                 "low_meaning": "Normal", "high_meaning": "Myocardial injury — suspect MI"},
    "d_dimer": {"unit": "ng/mL", "low": 0, "high": 500,
                "critical_low": 0, "critical_high": 5000,
                "low_meaning": "Normal", "high_meaning": "Elevated — consider PE/DVT"},
    "crp": {"unit": "mg/L", "low": 0, "high": 10,
            "critical_low": 0, "critical_high": 200,
            "low_meaning": "Normal", "high_meaning": "Inflammation/infection"},
    "esr": {"unit": "mm/hr", "low": 0, "high": 20,
            "critical_low": 0, "critical_high": 100,
            "low_meaning": "Normal", "high_meaning": "Inflammation"},
}

import re as _re

def sop_008_lab_value_interpreter(rag_text: str) -> Dict[str, Any]:
    """
    SOP-008: Parse and interpret lab values from RAG-extracted text.
    Returns: {findings, abnormal_count, summary}
    """
    if not rag_text:
        return {"findings": [], "abnormal_count": 0, "summary": "No lab data available"}

    findings = []
    text_lower = rag_text.lower()

    for lab_name, ref in LAB_REFERENCE_RANGES.items():
        # Try to find patterns like "hemoglobin: 10.5" or "Hb = 8.2"
        patterns = [
            rf"{lab_name}\s*[:=]\s*([\d.]+)",
            rf"{lab_name}\s+(?:is|was|level|count|value)\s*[:=]?\s*([\d.]+)",
        ]
        for pattern in patterns:
            match = _re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    status = "normal"
                    interpretation = "Within normal range"

                    if value <= ref["critical_low"]:
                        status = "critical_low"
                        interpretation = f"CRITICAL LOW — {ref['low_meaning']}"
                    elif value < ref["low"]:
                        status = "low"
                        interpretation = ref["low_meaning"]
                    elif value >= ref["critical_high"]:
                        status = "critical_high"
                        interpretation = f"CRITICAL HIGH — {ref['high_meaning']}"
                    elif value > ref["high"]:
                        status = "high"
                        interpretation = ref["high_meaning"]

                    findings.append({
                        "lab": lab_name,
                        "value": value,
                        "unit": ref["unit"],
                        "status": status,
                        "interpretation": interpretation,
                        "reference_range": f"{ref['low']}-{ref['high']} {ref['unit']}",
                    })
                except (ValueError, IndexError):
                    pass
                break

    abnormal = [f for f in findings if f["status"] != "normal"]
    summary_parts = [f"{f['lab'].upper()}: {f['value']} ({f['interpretation']})" for f in abnormal]

    return {
        "findings": findings,
        "abnormal_count": len(abnormal),
        "normal_count": len(findings) - len(abnormal),
        "summary": "; ".join(summary_parts) if summary_parts else "All lab values within normal range",
    }


# =============================================================================
# SOP-009: MEDICATION SAFETY CHECK
# Real protocol: Drug-drug interaction and allergy screening
# =============================================================================

# Common high-risk drug interactions (simplified for education)
DRUG_INTERACTIONS = {
    "warfarin": ["aspirin", "ibuprofen", "naproxen", "clopidogrel"],
    "aspirin": ["warfarin", "ibuprofen", "naproxen", "clopidogrel"],
    "metformin": ["contrast_dye"],
    "ace_inhibitor": ["potassium_supplement", "spironolactone"],
    "enalapril": ["potassium_supplement", "spironolactone"],
    "lisinopril": ["potassium_supplement", "spironolactone"],
    "ssri": ["maoi", "tramadol", "triptans"],
    "fluoxetine": ["maoi", "tramadol"],
    "sertraline": ["maoi", "tramadol"],
    "digoxin": ["amiodarone", "verapamil"],
    "statin": ["gemfibrozil", "cyclosporine"],
    "atorvastatin": ["gemfibrozil", "cyclosporine"],
    "simvastatin": ["gemfibrozil", "amlodipine"],
}

# Common drug-allergy cross-reactivities
CROSS_ALLERGIES = {
    "penicillin": ["amoxicillin", "ampicillin", "cephalosporin"],
    "sulfa": ["sulfamethoxazole", "trimethoprim", "celecoxib"],
    "nsaid": ["ibuprofen", "naproxen", "aspirin", "diclofenac"],
    "aspirin": ["nsaid", "ibuprofen", "naproxen"],
}

def sop_009_medication_safety(
    current_medications: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    hypotheses: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    SOP-009: Check for drug interactions and allergy conflicts.
    Returns: {alerts, interaction_count, allergy_conflicts, safe}
    """
    if not current_medications and not allergies:
        return {"alerts": [], "interaction_count": 0, "allergy_conflicts": [], "safe": True,
                "summary": "No medications or allergies on file"}

    alerts = []
    meds_lower = [m.lower().strip() for m in (current_medications or [])]
    allergies_lower = [a.lower().strip() for a in (allergies or [])]

    # Check drug-drug interactions among current medications
    for i, med1 in enumerate(meds_lower):
        interactions = DRUG_INTERACTIONS.get(med1, [])
        for med2 in meds_lower[i+1:]:
            if med2 in interactions or med1 in DRUG_INTERACTIONS.get(med2, []):
                alerts.append({
                    "type": "drug_interaction",
                    "severity": "high",
                    "drug1": med1,
                    "drug2": med2,
                    "message": f"Potential interaction between {med1} and {med2}",
                })

    # Check allergy cross-reactivities against current medications
    allergy_conflicts = []
    for allergy in allergies_lower:
        cross = CROSS_ALLERGIES.get(allergy, [])
        for med in meds_lower:
            if med in cross or allergy == med:
                allergy_conflicts.append({
                    "allergy": allergy,
                    "medication": med,
                    "message": f"ALERT: Patient allergic to {allergy}, currently on {med}",
                })

    return {
        "alerts": alerts,
        "interaction_count": len(alerts),
        "allergy_conflicts": allergy_conflicts,
        "safe": len(alerts) == 0 and len(allergy_conflicts) == 0,
        "summary": f"{len(alerts)} interactions, {len(allergy_conflicts)} allergy conflicts"
                   if alerts or allergy_conflicts else "No safety concerns identified",
    }


# =============================================================================
# SOP-010: RED FLAG SYMPTOM SCANNER
# Real protocol: Universal red flags every doctor checks
# =============================================================================

UNIVERSAL_RED_FLAGS = [
    {"symptom": "sudden_severe_headache", "keywords": ["worst headache", "thunderclap", "sudden severe headache"],
     "concern": "Subarachnoid hemorrhage / meningitis", "urgency": "emergency"},
    {"symptom": "blood_in_stool", "keywords": ["blood in stool", "bloody stool", "rectal bleeding", "melena"],
     "concern": "GI bleeding / colorectal pathology", "urgency": "urgent"},
    {"symptom": "blood_in_urine", "keywords": ["blood in urine", "hematuria", "red urine"],
     "concern": "Renal/urological pathology", "urgency": "urgent"},
    {"symptom": "unexplained_weight_loss", "keywords": ["losing weight", "weight loss", "lost weight", "unintentional weight"],
     "concern": "Malignancy / chronic disease / hyperthyroidism", "urgency": "urgent"},
    {"symptom": "sudden_vision_loss", "keywords": ["can't see", "vision loss", "sudden blindness", "lost vision"],
     "concern": "Retinal detachment / stroke / optic neuritis", "urgency": "emergency"},
    {"symptom": "coughing_blood", "keywords": ["coughing blood", "blood in cough", "hemoptysis", "bloody sputum"],
     "concern": "PE / TB / lung cancer", "urgency": "urgent"},
    {"symptom": "severe_abdominal_pain", "keywords": ["severe stomach pain", "worst abdominal", "unbearable pain"],
     "concern": "Appendicitis / perforation / ectopic pregnancy", "urgency": "urgent"},
    {"symptom": "neck_stiffness_fever", "keywords": ["stiff neck", "neck stiffness", "can't bend neck"],
     "concern": "Meningitis", "urgency": "emergency"},
    {"symptom": "new_seizure", "keywords": ["seizure", "convulsion", "fitting", "fits"],
     "concern": "Epilepsy / brain pathology / metabolic emergency", "urgency": "emergency"},
    {"symptom": "suicidal_thoughts", "keywords": ["want to die", "kill myself", "suicidal", "end my life", "no reason to live"],
     "concern": "Psychiatric emergency", "urgency": "emergency"},
]

def sop_010_red_flag_scanner(symptoms: List[Dict], raw_message: str = "") -> Dict[str, Any]:
    """
    SOP-010: Scan for universal red flag symptoms.
    Returns: {flags_found, count, urgency_level, details}
    """
    flags_found = []
    message_lower = raw_message.lower()
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    raw_texts = " ".join(s.get("raw_text", "").lower() for s in symptoms)

    search_text = f"{message_lower} {raw_texts}"

    for rf in UNIVERSAL_RED_FLAGS:
        triggered = False
        # Check symptom names
        if rf["symptom"] in symptom_names:
            triggered = True
        # Check keywords in raw text
        if not triggered:
            for kw in rf["keywords"]:
                if kw in search_text:
                    triggered = True
                    break

        if triggered:
            flags_found.append({
                "flag": rf["symptom"],
                "concern": rf["concern"],
                "urgency": rf["urgency"],
            })

    # Determine overall urgency
    if any(f["urgency"] == "emergency" for f in flags_found):
        urgency = "emergency"
    elif flags_found:
        urgency = "urgent"
    else:
        urgency = "none"

    return {
        "flags_found": flags_found,
        "count": len(flags_found),
        "urgency_level": urgency,
        "summary": f"{len(flags_found)} red flag(s) detected" if flags_found else "No red flags",
    }


# =============================================================================
# SOP-011: SPECIALIST ROUTING
# Real protocol: Standard referral pathways
# =============================================================================

SPECIALIST_MAP = {
    "cardiovascular": {"specialist": "Cardiologist", "conditions": ["Acute Myocardial Infarction", "Heart Failure", "Hypertension", "Aortic Dissection", "Atrial Fibrillation"]},
    "respiratory": {"specialist": "Pulmonologist", "conditions": ["Community Acquired Pneumonia", "Asthma", "COPD", "Pulmonary Embolism", "Tuberculosis", "COVID-19"]},
    "neurological": {"specialist": "Neurologist", "conditions": ["Stroke", "Transient Ischemic Attack", "Migraine", "Epilepsy", "Meningitis"]},
    "gastrointestinal": {"specialist": "Gastroenterologist", "conditions": ["Gastroesophageal Reflux Disease", "Peptic Ulcer Disease", "Cholera", "Hepatitis", "Pancreatitis"]},
    "infectious": {"specialist": "Infectious Disease Specialist", "conditions": ["Dengue Fever", "Typhoid Fever", "Malaria", "COVID-19", "Tuberculosis", "HIV"]},
    "endocrine": {"specialist": "Endocrinologist", "conditions": ["Diabetic Ketoacidosis", "Hypothyroidism", "Hyperthyroidism", "Diabetes Mellitus"]},
    "renal": {"specialist": "Nephrologist", "conditions": ["Chronic Kidney Disease", "Acute Kidney Injury", "Urinary Tract Infection"]},
    "musculoskeletal": {"specialist": "Rheumatologist / Orthopedist", "conditions": ["Rheumatoid Arthritis", "Osteoarthritis", "Gout"]},
    "psychiatric": {"specialist": "Psychiatrist", "conditions": ["Depression", "Anxiety Disorder", "Panic Disorder"]},
    "emergency": {"specialist": "Emergency Medicine", "conditions": ["Anaphylaxis", "Sepsis", "Shock"]},
}

def sop_011_specialist_routing(diagnosis_name: str, system: str = "") -> Dict[str, Any]:
    """
    SOP-011: Route to appropriate specialist based on diagnosis.
    Returns: {specialist, department, reasoning}
    """
    diagnosis_lower = diagnosis_name.lower()

    # Direct condition match
    for dept, info in SPECIALIST_MAP.items():
        for condition in info["conditions"]:
            if condition.lower() in diagnosis_lower or diagnosis_lower in condition.lower():
                return {
                    "specialist": info["specialist"],
                    "department": dept,
                    "reasoning": f"{diagnosis_name} requires {info['specialist']} evaluation",
                }

    # System-based fallback
    system_lower = system.lower() if system else ""
    for dept, info in SPECIALIST_MAP.items():
        if dept in system_lower:
            return {
                "specialist": info["specialist"],
                "department": dept,
                "reasoning": f"Based on {system} system involvement",
            }

    return {
        "specialist": "General Physician / Internal Medicine",
        "department": "general",
        "reasoning": "Initial evaluation by general physician recommended",
    }


# =============================================================================
# SOP-012: CONFIDENCE CALIBRATION
# Evidence-quality-weighted confidence assessment
# =============================================================================

def sop_012_confidence_calibration(
    hypotheses: List[Dict],
    evidence_count: int,
    iteration: int,
    vitals_provided: bool = False,
    lab_data_available: bool = False,
) -> Dict[str, Any]:
    """
    SOP-012: Calibrate diagnostic confidence based on evidence quality.
    Returns: {calibrated_action, confidence_band, reasoning, can_conclude}
    """
    if not hypotheses:
        return {"calibrated_action": "ask_more", "confidence_band": "insufficient",
                "reasoning": "No hypotheses generated", "can_conclude": False}

    top = hypotheses[0]
    top_conf = top.get("confidence", 0)
    second_conf = hypotheses[1].get("confidence", 0) if len(hypotheses) > 1 else 0
    margin = top_conf - second_conf

    # Evidence quality score
    quality_score = 0
    quality_score += min(evidence_count * 5, 30)  # Up to 30 pts for evidence count
    quality_score += min(iteration * 5, 25)        # Up to 25 pts for iterations
    if vitals_provided:
        quality_score += 15                         # 15 pts for having vitals
    if lab_data_available:
        quality_score += 20                         # 20 pts for lab data

    # Combined confidence = top confidence weighted by evidence quality
    # Use 0.7 base (not 0.5) so evidence quality boosts more realistically
    effective_confidence = top_conf * (0.7 + quality_score / 200)
    effective_confidence = min(effective_confidence, 99)

    # Safety net: After 7+ iterations with meaningful evidence, always allow conclusion
    max_iterations_reached = iteration >= 7 and evidence_count >= 8 and top_conf >= 30

    # Determine action band
    if effective_confidence < 40 and not max_iterations_reached:
        band = "insufficient"
        action = "ask_more"
        reasoning = "Not enough evidence to form a conclusion. Need more clinical information."
        can_conclude = False
    elif effective_confidence < 60 or (max_iterations_reached and effective_confidence < 60):
        band = "low"
        action = "suggest_possibilities"
        reasoning = "Some evidence gathered but significant uncertainty remains. Consider top 2-3 diagnoses."
        can_conclude = (iteration >= 5 and margin >= 10) or max_iterations_reached
    elif effective_confidence < 75:
        band = "moderate"
        action = "suggest_with_caveats"
        reasoning = "Moderate confidence. Can suggest likely diagnosis but important differentials remain."
        can_conclude = (iteration >= 4 and margin >= 15) or (iteration >= 3 and margin >= 40)
    else:
        band = "high"
        action = "conclude"
        reasoning = "High confidence with sufficient evidence quality to support conclusion."
        can_conclude = iteration >= 3 and margin >= 10

    return {
        "calibrated_action": action,
        "confidence_band": band,
        "effective_confidence": round(effective_confidence, 1),
        "evidence_quality_score": quality_score,
        "reasoning": reasoning,
        "can_conclude": can_conclude,
        "top_confidence": top_conf,
        "margin": margin,
    }


# =============================================================================
# SOP-013: PEDIATRIC/GERIATRIC TRIAGE ADJUSTMENTS
# Real protocol: Age-adjusted vital thresholds
# =============================================================================

def sop_013_demographic_adjustments(age: Optional[int], vitals: Optional[Dict] = None) -> Dict[str, Any]:
    """
    SOP-013: Adjusts risk calculations based on vulnerable age groups.
    """
    if not age:
        return {"activated": False}
        
    findings = []
    risk_modifier = 0
    
    if age < 2:
        findings.append("Infant/Toddler - High vulnerability.")
        risk_modifier = 1
        if vitals and vitals.get("heart_rate", 0) > 160:
            findings.append("Pediatric Tachycardia (HR > 160)")
            risk_modifier += 1
    elif age > 65:
        findings.append("Geriatric - Higher baseline risk.")
        risk_modifier = 1
            
    if risk_modifier > 0:
        return {
            "activated": True,
            "findings": findings,
            "risk_modifier": risk_modifier,
            "message": "Age-related risk factors identified. Escalating triage priority."
        }
        
    return {"activated": False}

# =============================================================================
# SOP-014: PREGNANCY SAFETY PROTOCOL
# Real protocol: Teratogen and ectopic screening
# =============================================================================

def sop_014_pregnancy_safety(
    gender: str, 
    age: Optional[int], 
    symptoms: List[Dict], 
    current_medications: Optional[List[str]] = None,
    raw_message: str = ""
) -> Dict[str, Any]:
    """
    SOP-014: Screens for pregnancy-related emergencies and teratogenic drugs.
    """
    message_lower = raw_message.lower()
    is_pregnant = "pregnant" in message_lower or "pregnancy" in message_lower
    childbearing_age = gender.lower() in ["female", "f"] and (age is None or 12 <= age <= 50)
    
    if not is_pregnant and not childbearing_age:
        return {"activated": False}
        
    findings = []
    emergency = False
    
    # 1. Ectopic pregnancy check
    symptom_names = {s.get("name", "").lower() for s in symptoms}
    if "abdominal_pain" in symptom_names or "pelvic_pain" in symptom_names or "severe lower abdominal pain" in message_lower:
        findings.append("Abdominal/Pelvic pain in female of childbearing age - Rule out Ectopic Pregnancy.")
        emergency = True
        
    # 2. Teratogen check
    teratogens = {"ace_inhibitor", "lisinopril", "enalapril", "warfarin", "isotretinoin", "methotrexate", "valproic_acid", "tetracycline"}
    meds_lower = [m.lower().strip() for m in (current_medications or [])]
    
    for med in meds_lower:
        if med in teratogens:
            findings.append(f"WARNING: {med} is a known teratogen. Highly contraindicated if pregnant.")
            
    if findings or is_pregnant:
        return {
            "activated": True,
            "is_pregnant": is_pregnant,
            "emergency": emergency,
            "findings": findings,
            "message": "PREGNANCY ALERT: " + " ".join(findings) if findings else "Patient noted as pregnant."
        }
        
    return {"activated": False}


# =============================================================================
# SOP-015: FOLLOW-UP PROTOCOL
# Real protocol: Continuity of care
# =============================================================================

def sop_015_follow_up(triage_level: str, diagnosis_name: str) -> Dict[str, Any]:
    """
    SOP-015: Recommends timeline for follow-up based on severity and condition.
    """
    level = triage_level.lower() if triage_level else "routine"
    timeline = "Routine as needed"
    reason = "General monitoring"
    
    if level in ["emergency", "red", "immediate"]:
        timeline = "IMMEDIATE"
        reason = "Emergency condition requires immediate stabilization."
    elif level in ["urgent", "orange", "high"]:
        timeline = "Within 24-48 hours"
        reason = "Urgent condition requires prompt evaluation to prevent deterioration."
    elif level in ["moderate", "yellow"]:
        timeline = "Within 1 week"
        reason = "Condition requires formal outpatient evaluation."
    elif "infection" in diagnosis_name.lower() or "pneumonia" in diagnosis_name.lower() or "covid" in diagnosis_name.lower():
        timeline = "48-72 hours"
        reason = "Monitor infection progression and treatment response."
        
    return {
        "activated": True,
        "timeline": timeline,
        "reasoning": reason,
        "message": f"FOLLOW-UP RECOMMENDATION: {timeline} - {reason}"
    }
