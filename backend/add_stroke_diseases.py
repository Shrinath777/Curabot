"""Add Stroke (CVA) and TIA to diseases.json"""
import json

with open("data/diseases.json", "r", encoding="utf-8") as f:
    diseases = json.load(f)

stroke = {
    "name": "Stroke (CVA)",
    "icd10": "I63",
    "system": "neurological",
    "acuity": "acute",
    "prevalence": "common",
    "description": "Sudden interruption of blood supply to the brain causing neurological deficits",
    "symptoms": {
        "primary": ["facial_drooping", "arm_weakness", "speech_difficulty"],
        "secondary": ["sudden_severe_headache", "confusion", "vision_loss", "dizziness", "difficulty_walking", "numbness_one_side"],
        "atypical": ["sudden_nausea", "hiccups", "chest_pain"]
    },
    "vital_sign_patterns": {
        "heart_rate": ">100 or irregular",
        "blood_pressure": ">180/120 common",
        "oxygen_saturation": "<95 if aspiration",
        "temperature": "Normal initially"
    },
    "lab_tests": ["CT Head STAT", "MRI Brain", "CT Angiography", "CBC", "Coagulation panel", "Blood Glucose", "ECG"],
    "key_diagnostic_questions": [
        "Is one side of your face drooping or numb?",
        "Can you raise both arms equally, or is one arm weak?",
        "Is your speech slurred or are you having trouble finding words?",
        "When exactly did the symptoms start?",
        "Did the symptoms come on SUDDENLY?",
        "Do you have a severe headache unlike any before?",
        "Do you have atrial fibrillation or take blood thinners?"
    ],
    "risk_factors": ["hypertension", "atrial_fibrillation", "diabetes", "smoking", "hyperlipidemia", "age_over_55", "previous_stroke_or_tia"],
    "red_flags": ["Any FAST symptom", "Sudden worst headache of life", "Sudden vision loss", "Rapid deterioration of consciousness"],
    "severity_class": "critical",
    "differentiating_features": [
        "SUDDEN onset of focal neurological deficit",
        "FAST positive: Face drooping, Arm weakness, Speech difficulty",
        "Unilateral symptoms (one side of body)",
        "Time of onset is critical (thrombolysis window: 4.5 hours)"
    ]
}

tia = {
    "name": "Transient Ischemic Attack",
    "icd10": "G45",
    "system": "neurological",
    "acuity": "acute",
    "prevalence": "common",
    "description": "Temporary blockage of blood flow to the brain causing stroke-like symptoms that resolve within 24 hours",
    "symptoms": {
        "primary": ["transient_facial_drooping", "transient_arm_weakness", "transient_speech_difficulty"],
        "secondary": ["transient_vision_loss", "dizziness", "confusion", "numbness"],
        "atypical": ["sudden_memory_loss", "transient_difficulty_walking"]
    },
    "vital_sign_patterns": {
        "heart_rate": "May be irregular",
        "blood_pressure": "Often elevated",
        "oxygen_saturation": ">=95",
        "temperature": "Normal"
    },
    "lab_tests": ["CT Head", "MRI with Diffusion Weighting", "Carotid Doppler", "ECG", "Echocardiogram", "Lipid Panel"],
    "key_diagnostic_questions": [
        "Did the symptoms go away completely on their own?",
        "How long did the symptoms last?",
        "Did you have face drooping, arm weakness, or speech problems that resolved?",
        "Have you had episodes like this before?",
        "Do you have high blood pressure, diabetes, or atrial fibrillation?"
    ],
    "risk_factors": ["hypertension", "atrial_fibrillation", "diabetes", "smoking", "previous_tia", "carotid_stenosis"],
    "red_flags": ["Symptoms NOT resolving", "Multiple TIAs in short period", "ABCD2 score >= 4"],
    "severity_class": "serious",
    "differentiating_features": [
        "Symptoms RESOLVE completely unlike stroke",
        "Duration typically under 1 hour",
        "Same FAST symptoms as stroke but transient",
        "High risk of subsequent full stroke within 48 hours"
    ]
}

# Check if already added
existing_names = {d["name"] for d in diseases}
added = []
if stroke["name"] not in existing_names:
    diseases.append(stroke)
    added.append(stroke["name"])
if tia["name"] not in existing_names:
    diseases.append(tia)
    added.append(tia["name"])

with open("data/diseases.json", "w", encoding="utf-8") as f:
    json.dump(diseases, f, indent=2, ensure_ascii=False)

print(f"Done. Added: {added}. Total diseases: {len(diseases)}")
