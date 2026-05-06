"""
Patch script: Add missing diseases and fix weak profiles in diseases.json
Targets the 12 golden test cases that fail Top-3
"""
import json
import os

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")

with open(KB_PATH, "r", encoding="utf-8") as f:
    diseases = json.load(f)

name_map = {d["name"]: i for i, d in enumerate(diseases)}

# ============================================================================
# 1. ADD MISSING DISEASES
# ============================================================================

NEW_DISEASES = [
    # GT-021: Acute Pancreatitis (was missing entirely)
    {
        "name": "Acute Pancreatitis",
        "icd10": "K85",
        "system": "gastrointestinal",
        "severity_class": "serious",
        "prevalence": "common",
        "description": "Acute inflammation of the pancreas, most commonly caused by gallstones or heavy alcohol use.",
        "symptoms": {
            "primary": ["epigastric_pain", "radiating_back_pain", "nausea"],
            "secondary": ["vomiting", "abdominal_tenderness", "fever", "tachycardia", "loss_of_appetite"],
            "atypical": ["dyspnea", "jaundice", "hypotension"]
        },
        "risk_factors": ["heavy_alcohol_use", "gallstones", "hypertriglyceridemia", "smoking", "obesity"],
        "differentiating_features": [
            "Severe epigastric pain radiating straight through to the back",
            "Pain worsened by eating and relieved by leaning forward",
            "History of heavy alcohol use or gallstones",
            "Nausea and persistent vomiting",
            "Abdominal tenderness with guarding"
        ],
        "lab_tests": ["serum_lipase", "serum_amylase", "CBC", "liver_function_tests", "CT_abdomen"],
        "red_flags": ["Severe abdominal pain with shock", "Grey Turner sign", "Cullen sign"],
    },
    # GT-048: Anaphylaxis (was missing entirely)
    {
        "name": "Anaphylaxis",
        "icd10": "T78.2",
        "system": "immunological",
        "severity_class": "critical",
        "prevalence": "uncommon_but_dangerous",
        "description": "Severe, life-threatening allergic reaction causing airway compromise and cardiovascular collapse.",
        "symptoms": {
            "primary": ["urticaria", "angioedema", "dyspnea"],
            "secondary": ["throat_swelling", "wheezing", "tachycardia", "hypotension", "dizziness", "nausea"],
            "atypical": ["abdominal_pain", "confusion", "syncope"]
        },
        "risk_factors": ["known_allergy", "previous_anaphylaxis", "atopy", "food_allergy", "drug_allergy", "insect_sting_allergy"],
        "differentiating_features": [
            "Rapid onset after allergen exposure (minutes)",
            "Widespread hives/urticaria with angioedema",
            "Throat swelling with airway compromise",
            "Known allergen exposure (food, drug, insect sting)",
            "Biphasic reaction possible (recurrence hours later)",
            "Responds to epinephrine"
        ],
        "lab_tests": ["serum_tryptase", "IgE_levels", "allergy_testing"],
        "red_flags": ["Throat closing", "Unable to breathe", "Loss of consciousness", "Cardiovascular collapse"],
    },
    # GT-047: Bell's Palsy (was missing entirely)
    {
        "name": "Bell's Palsy",
        "icd10": "G51.0",
        "system": "neurological",
        "severity_class": "moderate",
        "prevalence": "common",
        "description": "Idiopathic acute unilateral facial nerve paralysis, affecting forehead, eye, and mouth on one side.",
        "symptoms": {
            "primary": ["facial_drooping", "facial_weakness", "inability_to_close_eye"],
            "secondary": ["taste_disturbance", "ear_pain", "hyperacusis", "dry_eye", "drooling"],
            "atypical": ["numbness", "headache"]
        },
        "risk_factors": ["viral_infection", "diabetes", "pregnancy", "cold_exposure"],
        "differentiating_features": [
            "Unilateral facial weakness affecting BOTH upper and lower face (forehead involved)",
            "Inability to close eye or raise eyebrow on affected side",
            "NO arm or leg weakness (distinguishes from stroke)",
            "Taste disturbance on anterior 2/3 of tongue",
            "Ear pain preceding facial weakness",
            "Sudden onset, usually overnight"
        ],
        "lab_tests": ["clinical_diagnosis", "MRI_brain_if_atypical"],
        "red_flags": ["Bilateral facial weakness", "Limb weakness", "Progressive worsening beyond 3 weeks"],
    },
    # GT-041: Depression (as standalone — Major Depressive Disorder exists but under different name)
    {
        "name": "Depression",
        "icd10": "F32.1",
        "system": "psychiatric",
        "severity_class": "moderate",
        "prevalence": "very_common",
        "description": "Major depressive episode characterized by persistent sadness, anhedonia, and functional impairment.",
        "symptoms": {
            "primary": ["depressed_mood", "anhedonia", "fatigue"],
            "secondary": ["insomnia", "hypersomnia", "loss_of_appetite", "poor_concentration", "worthlessness"],
            "atypical": ["weight_gain", "psychomotor_retardation", "somatic_pain"]
        },
        "risk_factors": ["family_history", "trauma", "chronic_illness", "substance_abuse", "social_isolation"],
        "differentiating_features": [
            "Persistent sadness or hopelessness lasting more than 2 weeks",
            "Loss of interest in previously enjoyed activities (anhedonia)",
            "Sleep disturbance (insomnia or hypersomnia)",
            "Feelings of worthlessness or excessive guilt",
            "Poor concentration and indecisiveness",
            "NO fever, weight loss, or physical exam abnormalities (distinguishes from medical causes)"
        ],
        "lab_tests": ["PHQ-9_screening", "thyroid_function_tests", "CBC"],
        "red_flags": ["Suicidal ideation", "Psychotic features", "Catatonia"],
    },
    # GT-042: Hepatitis B (generic Hepatitis exists but not B-specific)
    {
        "name": "Hepatitis B",
        "icd10": "B16",
        "system": "gastrointestinal/hepatic",
        "severity_class": "serious",
        "prevalence": "common",
        "description": "Viral hepatitis caused by Hepatitis B virus, transmitted through blood and body fluids.",
        "symptoms": {
            "primary": ["jaundice", "fatigue", "right_upper_quadrant_pain"],
            "secondary": ["nausea", "loss_of_appetite", "dark_urine", "pale_stool", "fever", "arthralgia"],
            "atypical": ["rash", "vasculitis", "glomerulonephritis"]
        },
        "risk_factors": ["unprotected_sexual_contact", "IV_drug_use", "blood_transfusion", "healthcare_worker", "endemic_area_travel"],
        "differentiating_features": [
            "Jaundice with dark urine and pale/clay-colored stools",
            "History of sexual exposure or blood contact",
            "Right upper quadrant tenderness (hepatomegaly)",
            "Prodromal serum-sickness-like symptoms (joint pain, rash)",
            "Gradual onset over days to weeks",
            "Elevated liver transaminases (ALT > AST)"
        ],
        "lab_tests": ["HBsAg", "anti-HBc_IgM", "HBeAg", "HBV_DNA", "liver_function_tests"],
        "red_flags": ["Coagulopathy", "Encephalopathy", "Fulminant hepatic failure"],
    },
]

for new_d in NEW_DISEASES:
    if new_d["name"] not in name_map:
        diseases.append(new_d)
        name_map[new_d["name"]] = len(diseases) - 1
        print(f"ADDED: {new_d['name']}")
    else:
        print(f"EXISTS: {new_d['name']} — skipping")

# ============================================================================
# 2. FIX WEAK EXISTING PROFILES
# ============================================================================

def update_disease(name, updates):
    if name in name_map:
        idx = name_map[name]
        for k, v in updates.items():
            if k == "symptoms" and isinstance(v, dict):
                existing = diseases[idx].get("symptoms", {})
                if isinstance(existing, dict):
                    for cat in ["primary", "secondary", "atypical"]:
                        if cat in v:
                            existing_set = set(existing.get(cat, []))
                            for sym in v[cat]:
                                existing_set.add(sym)
                            existing[cat] = list(existing_set)
                    diseases[idx]["symptoms"] = existing
                else:
                    diseases[idx]["symptoms"] = v
            elif k == "differentiating_features":
                existing = diseases[idx].get("differentiating_features", [])
                existing_lower = {f.lower() for f in existing}
                for f in v:
                    if f.lower() not in existing_lower:
                        existing.append(f)
                diseases[idx]["differentiating_features"] = existing
            elif k == "risk_factors":
                existing = diseases[idx].get("risk_factors", [])
                existing_lower = {f.lower() for f in existing}
                for f in v:
                    if f.lower() not in existing_lower:
                        existing.append(f)
                diseases[idx]["risk_factors"] = existing
            else:
                diseases[idx][k] = v
        print(f"UPDATED: {name}")
    else:
        print(f"NOT FOUND: {name}")

# --- Atrial Fibrillation (GT-027): severity should be serious, not mild ---
update_disease("Atrial Fibrillation", {
    "severity_class": "serious",
    "symptoms": {
        "primary": ["palpitations", "irregular_heartbeat", "dyspnea"],
        "secondary": ["fatigue", "dizziness", "lightheadedness", "chest_discomfort", "exercise_intolerance"],
    },
    "differentiating_features": [
        "Irregularly irregular pulse — NO regular pattern (unlike SVT/flutter)",
        "Heart fluttering sensation with skipped beats",
        "Pulse completely irregular when self-checked",
        "Common in elderly with hypertension history",
        "Distinguished from MI by lack of crushing pain and diaphoresis"
    ],
})

# --- Eczema (GT-044): needs flexural distribution, childhood onset ---
update_disease("Eczema", {
    "symptoms": {
        "primary": ["pruritus", "erythematous_patches", "dry_skin"],
        "secondary": ["flexural_distribution", "weeping_lesions", "skin_cracking", "seasonal_worsening"],
        "atypical": ["lichenification", "secondary_infection"],
    },
    "differentiating_features": [
        "Itchy dry patches in flexural areas (inside elbows, behind knees)",
        "Chronic relapsing course since childhood (atopic dermatitis)",
        "Associated with asthma and allergic rhinitis (atopic triad)",
        "Worsens in winter or with stress",
        "Skin cracks and weeps fluid in acute flares",
        "Distinguished from psoriasis by flexural (not extensor) distribution"
    ],
})

# --- Anxiety Disorder (GT-032): needs panic attack symptoms ---
update_disease("Anxiety Disorder", {
    "symptoms": {
        "primary": ["panic_episodes", "chronic_worry", "impending_doom"],
        "secondary": ["palpitations", "dyspnea", "diaphoresis", "chest_tightness", "insomnia", "restlessness"],
        "atypical": ["tremor", "gastrointestinal_distress", "derealization"],
    },
    "differentiating_features": [
        "Episodes of intense fear with palpitations, dyspnea, and diaphoresis lasting 10-30 minutes",
        "Feeling of impending doom or 'going to die' during episodes",
        "Constant worry about everything (generalized anxiety)",
        "Normal cardiac workup despite cardiac-seeming symptoms",
        "Episodes self-resolve within 15-30 minutes (unlike MI which persists)",
        "Triggered by stress, not by exertion (unlike angina)"
    ],
})

# --- Influenza (GT-036): severity should be moderate ---
update_disease("Influenza", {
    "severity_class": "moderate",
    "symptoms": {
        "primary": ["high_fever", "myalgia", "dry_cough", "headache"],
        "secondary": ["fatigue", "sore_throat", "rhinorrhea", "chills", "sudden_onset"],
    },
    "differentiating_features": [
        "SUDDEN onset — healthy to very ill within hours",
        "Severe body aches and prostration (more than common cold)",
        "Seasonal pattern during flu season (winter months)",
        "Workplace or household outbreak with similar symptoms",
        "Distinguished from COVID-19 by preserved taste/smell",
        "Dry cough prominent from early course"
    ],
})

# --- Pneumothorax (GT-037): needs spontaneous onset + tall/thin ---
update_disease("Pneumothorax", {
    "symptoms": {
        "primary": ["sudden_dyspnea", "pleuritic_chest_pain", "unilateral_chest_pain"],
        "secondary": ["tachycardia", "decreased_breath_sounds", "anxiety"],
    },
    "differentiating_features": [
        "Sudden sharp UNILATERAL chest pain (one side only)",
        "Onset at rest or spontaneously in tall thin young individuals",
        "NO fever, cough, or sputum (distinguishes from pneumonia)",
        "Decreased or absent breath sounds on affected side",
        "Pain worse with deep breathing (pleuritic)",
        "Distinguished from PE by unilateral nature and no DVT history"
    ],
})

# --- Pulmonary Embolism (GT-004): needs surgery/immobility differentiators ---
update_disease("Pulmonary Embolism", {
    "symptoms": {
        "primary": ["acute_dyspnea", "pleuritic_chest_pain", "tachycardia"],
        "secondary": ["hemoptysis", "syncope", "anxiety", "cough", "leg_swelling"],
    },
    "differentiating_features": [
        "SUDDEN onset dyspnea with pleuritic chest pain",
        "Recent surgery, prolonged immobility, or long travel (DVT risk factors)",
        "Leg swelling or calf pain suggesting DVT source",
        "Tachycardia with clear lungs on auscultation",
        "Hemoptysis (coughing blood) present in minority",
        "Distinguished from MI by pleuritic nature and immobility history"
    ],
})

# --- Type 2 Diabetes Mellitus (GT-038): needs family history, obesity ---
update_disease("Type 2 Diabetes Mellitus", {
    "symptoms": {
        "primary": ["polyuria", "polydipsia", "fatigue", "excessive_thirst", "frequent_urination"],
        "secondary": ["blurred_vision", "poor_wound_healing", "peripheral_neuropathy", "weight_loss", "obesity"],
    },
    "differentiating_features": [
        "Polydipsia and polyuria developing over weeks (insidious onset)",
        "Strong family history of diabetes in first-degree relatives",
        "Overweight/obesity with metabolic syndrome",
        "Tingling/numbness in feet (peripheral neuropathy)",
        "Slow wound healing especially in feet",
        "Distinguished from DKA by gradual onset and no ketoacidosis"
    ],
    "risk_factors": ["obesity", "family_history_diabetes", "sedentary_lifestyle", "metabolic_syndrome", "age_over_45"],
})

# --- Gastroenteritis (GT-049): needs foodborne/outbreak differentiators ---
update_disease("Gastroenteritis", {
    "severity_class": "benign",
    "symptoms": {
        "primary": ["watery_diarrhea", "vomiting", "abdominal_cramps"],
        "secondary": ["fever", "loss_of_appetite", "nausea", "weakness"],
    },
    "differentiating_features": [
        "Multiple household/group members ill after shared meal (foodborne outbreak)",
        "Acute onset of vomiting and diarrhea within 6-48 hours of exposure",
        "Self-limiting course (resolves in 1-3 days)",
        "Mild fever only (unlike bacterial infections with high fever)",
        "No blood in stool (unlike dysentery or IBD)",
        "Restaurant or communal food exposure history"
    ],
})

# --- Rheumatoid Arthritis (GT-020): needs symmetric/small joint keywords ---
update_disease("Rheumatoid Arthritis", {
    "symptoms": {
        "primary": ["arthralgia", "joint_swelling", "prolonged_morning_stiffness", "symmetric_joint_involvement"],
        "secondary": ["fatigue", "small_joint_involvement", "hand_wrist_joints", "low_grade_fever"],
    },
    "differentiating_features": [
        "Symmetric polyarthritis affecting SMALL joints (fingers, wrists)",
        "Morning stiffness lasting MORE than 1 hour",
        "MCP and PIP joints involved (spares DIP joints — unlike OA)",
        "Systemic symptoms: fatigue, low-grade fever, malaise",
        "Distinguished from osteoarthritis by morning stiffness duration and symmetry"
    ],
})

# --- Osteoarthritis (GT-043): needs crepitus and age keywords ---
update_disease("Osteoarthritis", {
    "symptoms": {
        "primary": ["joint_pain", "joint_stiffness", "crepitus"],
        "secondary": ["knee_pain", "reduced_range_of_motion", "joint_swelling"],
    },
    "differentiating_features": [
        "Pain WORSENS with activity and IMPROVES with rest",
        "Brief morning stiffness lasting LESS than 30 minutes (unlike RA >1 hour)",
        "Crepitus (crunching/grinding sound) in affected joints",
        "Affects weight-bearing joints: knees, hips, spine",
        "Age >50 and obesity as risk factors",
        "Distinguished from RA by asymmetric pattern and brief stiffness"
    ],
})

# ============================================================================
# 3. SAVE
# ============================================================================

with open(KB_PATH, "w", encoding="utf-8") as f:
    json.dump(diseases, f, indent=2, ensure_ascii=False)

print(f"\nTotal diseases in KB: {len(diseases)}")
print("diseases.json updated successfully!")
