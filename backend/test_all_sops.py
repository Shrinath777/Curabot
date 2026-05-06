import json
from agents.clinical_sops_triage import (
    sop_001_triage_classification,
    sop_002_chest_pain_protocol,
    sop_003_fast_stroke_protocol,
    sop_004_respiratory_distress,
    sop_005_vital_signs_interpreter,
    sop_006_infection_risk,
    sop_007_sepsis_screening
)

from agents.clinical_sops_diagnostic import (
    sop_008_lab_value_interpreter,
    sop_009_medication_safety,
    sop_010_red_flag_scanner,
    sop_011_specialist_routing,
    sop_012_confidence_calibration,
    sop_013_demographic_adjustments,
    sop_014_pregnancy_safety,
    sop_015_follow_up
)

def print_result(sop_name, input_desc, result):
    print(f"\n{'='*80}")
    print(f"[*] {sop_name}")
    print(f"Test Situation: {input_desc}")
    print(f"Result:")
    print(json.dumps(result, indent=2))

def run_all_tests():
    print("RUNNING CURABOT CLINICAL SOP TESTS")

    # ==========================================
    # PART 1: TRIAGE & EMERGENCY PROTOCOLS
    # ==========================================

    # SOP 001
    symptoms_001 = [{"name": "severe_chest_pain"}, {"name": "diaphoresis"}]
    res_001 = sop_001_triage_classification(symptoms=symptoms_001)
    print_result("SOP-001: Triage Severity Classification", 
                 "Patient reports severe chest pain and sweating.", res_001)

    # SOP 002
    symptoms_002 = [
        {"name": "chest_pain", "character": "pressure"}, 
        {"name": "jaw_pain"}, 
        {"name": "diaphoresis"}, 
        {"name": "nausea"}
    ]
    res_002 = sop_002_chest_pain_protocol(symptoms=symptoms_002)
    print_result("SOP-002: Chest Pain Protocol (ACS Pathway)", 
                 "Patient reports chest pressure radiating to the jaw with sweating and nausea.", res_002)

    # SOP 003
    symptoms_003 = [
        {"name": "arm_weakness", "raw_text": "left arm feels heavy"}, 
        {"name": "speech_difficulty", "raw_text": "words are coming out wrong"}
    ]
    res_003 = sop_003_fast_stroke_protocol(symptoms=symptoms_003)
    print_result("SOP-003: Stroke Detection (FAST Protocol)", 
                 "Patient says 'left arm feels heavy and words are coming out wrong'.", res_003)

    # SOP 004
    symptoms_004 = [{"name": "dyspnea"}]
    vitals_004 = {"oxygen_saturation": 86}
    res_004 = sop_004_respiratory_distress(symptoms=symptoms_004, vitals=vitals_004)
    print_result("SOP-004: Respiratory Distress Protocol", 
                 "COVID patient reports shortness of breath, SpO2 is 86%.", res_004)

    # SOP 005
    vitals_005 = {"blood_pressure": "185/120"}
    res_005 = sop_005_vital_signs_interpreter(vitals=vitals_005)
    print_result("SOP-005: Vital Signs Interpreter", 
                 "User inputs Blood Pressure: 185/120.", res_005)

    # SOP 006
    symptoms_006 = [{"name": "fever"}, {"name": "cough"}]
    vitals_006 = {"temperature": 101.0} # F
    msg_016 = "my husband has COVID"
    res_006 = sop_006_infection_risk(symptoms=symptoms_006, vitals=vitals_006, raw_message=msg_016)
    print_result("SOP-006: Infection Risk Protocol", 
                 "Patient has fever (101°F), cough, and mentions 'husband has COVID'.", res_006)

    # SOP 007
    symptoms_007 = [{"name": "confusion"}]
    vitals_007 = {"respiratory_rate": 26}
    res_007 = sop_007_sepsis_screening(symptoms=symptoms_007, vitals=vitals_007)
    print_result("SOP-007: Sepsis Screening (qSOFA)", 
                 "Elderly patient is confused with a respiratory rate of 26.", res_007)


    # ==========================================
    # PART 2: DIAGNOSTIC SUPPORT & SAFETY
    # ==========================================

    # SOP 008
    rag_text_011 = "Doc said my Hb is 6.5"
    res_008 = sop_008_lab_value_interpreter(rag_text=rag_text_011)
    print_result("SOP-008: Lab Value Interpreter", 
                 "Patient uploads notes saying 'Doc said my Hb is 6.5'.", res_008)

    # SOP 009
    meds_012 = ["amoxicillin"]
    allergies_012 = ["penicillin"]
    res_009 = sop_009_medication_safety(current_medications=meds_012, allergies=allergies_012)
    print_result("SOP-009: Medication Safety Check", 
                 "Patient is allergic to Penicillin, current med is Amoxicillin.", res_009)

    # SOP 010
    symptoms_010 = []
    msg_013 = "I have the worst headache of my life and my stool looks black and tarry."
    res_010 = sop_010_red_flag_scanner(symptoms=symptoms_010, raw_message=msg_013)
    print_result("SOP-010: Red Flag Symptom Scanner", 
                 "Patient mentions 'worst headache of my life' and 'stool looks black'.", res_010)

    # SOP 011
    dx_014 = "Atrial Fibrillation"
    res_011 = sop_011_specialist_routing(diagnosis_name=dx_014)
    print_result("SOP-011: Specialist Routing", 
                 "AI hypothesized diagnosis is Atrial Fibrillation.", res_011)

    # SOP 012
    hypotheses_015 = [{"diagnosis": "Migraine", "confidence": 95}, {"diagnosis": "Tension Headache", "confidence": 60}]
    res_012 = sop_012_confidence_calibration(hypotheses=hypotheses_015, evidence_count=1, iteration=1)
    print_result("SOP-012: Confidence Calibration", 
                 "AI is 95% confident of Migraine after only 1 question and 1 piece of evidence.", res_012)

    # SOP 013
    age_018 = 1
    vitals_013 = {"heart_rate": 170}
    res_013 = sop_013_demographic_adjustments(age=age_018, vitals=vitals_013)
    print_result("SOP-013: Pediatric/Geriatric Triage Adjustments", 
                 "1-year-old infant has a Heart Rate of 170 bpm.", res_013)

    # SOP 014
    symptoms_014 = [{"name": "abdominal_pain"}]
    msg_019 = "severe lower abdominal pain"
    res_014 = sop_014_pregnancy_safety(gender="female", age=28, symptoms=symptoms_014, raw_message=msg_019)
    print_result("SOP-014: Pregnancy Safety Protocol", 
                 "28-year-old female presents with severe lower abdominal pain.", res_014)

    # SOP 015
    res_015 = sop_015_follow_up(triage_level="moderate", diagnosis_name="mild pneumonia")
    print_result("SOP-015: Follow-up Protocol", 
                 "Patient diagnosed with suspected mild pneumonia (Moderate triage).", res_015)

    print(f"\n{'='*80}")
    print("All 15 SOP tests executed successfully!")

if __name__ == "__main__":
    run_all_tests()
