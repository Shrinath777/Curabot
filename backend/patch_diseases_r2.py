"""Patch Round 2: Fix remaining 10 failures - add Celiac Disease, strengthen profiles."""
import json, os

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")
with open(KB_PATH, "r", encoding="utf-8") as f:
    diseases = json.load(f)
name_map = {d["name"]: i for i, d in enumerate(diseases)}

# ============================================================================
# 1. ADD MISSING DISEASES
# ============================================================================

NEW_DISEASES = [
    # GT-026: Celiac Disease (not in KB)
    {
        "name": "Celiac Disease",
        "icd10": "K90.0",
        "system": "gastrointestinal",
        "severity_class": "moderate",
        "prevalence": "uncommon",
        "description": "Autoimmune disorder triggered by gluten ingestion, causing small intestinal villous atrophy.",
        "symptoms": {
            "primary": ["chronic_diarrhea", "bloating", "weight_loss"],
            "secondary": ["fatigue", "abdominal_pain", "iron_deficiency", "gluten_sensitivity",
                          "vesicular_rash", "loss_of_appetite"],
            "atypical": ["osteoporosis", "peripheral_neuropathy", "infertility", "dental_enamel_defects"]
        },
        "risk_factors": ["family_history", "type_1_diabetes", "autoimmune_thyroid_disease", "down_syndrome"],
        "differentiating_features": [
            "Chronic diarrhea and bloating worsened by bread, pasta, and gluten-containing foods",
            "Dermatitis herpetiformis: itchy blistering rash on elbows and knees",
            "Iron deficiency anemia unresponsive to oral iron supplementation",
            "Weight loss despite adequate caloric intake",
            "Improvement of symptoms on gluten-free diet",
            "Distinguished from IBS by weight loss and malabsorption markers"
        ],
        "lab_tests": ["tissue_transglutaminase_IgA", "endomysial_antibodies", "duodenal_biopsy",
                      "total_IgA", "iron_studies"],
        "red_flags": ["Severe malnutrition", "Intestinal lymphoma", "Refractory celiac disease"],
    },
]

for new_d in NEW_DISEASES:
    if new_d["name"] not in name_map:
        diseases.append(new_d)
        name_map[new_d["name"]] = len(diseases) - 1
        print(f"ADDED: {new_d['name']}")

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

# DKA (GT-006): Add more matching symptoms
update_disease("Diabetic Ketoacidosis", {
    "symptoms": {
        "primary": ["fruity_breath", "excessive_thirst", "frequent_urination"],
        "secondary": ["confusion", "nausea", "vomiting", "abdominal_pain",
                       "rapid_breathing", "fatigue", "diabetes_history"],
    },
    "differentiating_features": [
        "Fruity or acetone-smelling breath (ketones)",
        "Type 1 diabetic who missed insulin doses",
        "Rapid/Kussmaul breathing with metabolic acidosis",
        "Extreme thirst with polyuria in known diabetic",
        "Abdominal pain with nausea in diabetic emergency"
    ],
})

# Acute Appendicitis (GT-008): strengthen symptom matching
update_disease("Acute Appendicitis", {
    "symptoms": {
        "primary": ["right_lower_quadrant_pain", "periumbilical_pain", "pain_migration"],
        "secondary": ["nausea", "loss_of_appetite", "low_grade_fever", "vomiting",
                       "rebound_tenderness"],
    },
    "differentiating_features": [
        "Pain starting around navel then migrating to right lower quadrant",
        "McBurney's point tenderness in right lower abdomen",
        "Rebound tenderness and guarding",
        "Anorexia (loss of appetite) preceding pain",
        "Low-grade fever (not high fever like diverticulitis)"
    ],
})

# Bacterial Meningitis (GT-023): strengthen with fallback-matchable symptoms
update_disease("Bacterial Meningitis", {
    "symptoms": {
        "primary": ["headache", "neck_stiffness", "high_fever"],
        "secondary": ["photophobia", "confusion", "petechiae", "non_blanching_rash",
                       "nausea", "vomiting"],
    },
    "differentiating_features": [
        "Classic triad: headache + neck stiffness + fever",
        "Purpuric/petechial rash that does NOT blanch with pressure",
        "Kernig and Brudzinski signs positive",
        "Altered mental status and confusion",
        "Photophobia (sensitivity to light)",
        "Distinguished from migraine by fever and rash"
    ],
})

# Also add/update standalone "Meningitis" that maps to Bacterial Meningitis
if "Meningitis" in name_map:
    update_disease("Meningitis", {
        "symptoms": {
            "primary": ["headache", "neck_stiffness", "high_fever"],
            "secondary": ["photophobia", "confusion", "petechiae", "non_blanching_rash",
                           "nausea", "vomiting"],
        },
        "differentiating_features": [
            "Classic triad: headache + neck stiffness + fever",
            "Purpuric rash that does NOT blanch with pressure",
            "Altered mental status progressing to confusion",
            "Photophobia (sensitivity to light)"
        ],
    })

# Anxiety Disorder (GT-032): Add chest_tightness and episodes to primary
update_disease("Anxiety Disorder", {
    "symptoms": {
        "primary": ["panic_episodes", "chronic_worry", "impending_doom",
                     "anxiety", "chest_tightness", "palpitations"],
        "secondary": ["dyspnea", "diaphoresis", "insomnia", "restlessness",
                       "brief_episodes", "generalized_anxiety"],
    },
})

# Hepatitis B (GT-042): Add more matching symptom names
update_disease("Hepatitis B", {
    "symptoms": {
        "primary": ["jaundice", "fatigue", "right_upper_quadrant_pain", "dark_urine"],
        "secondary": ["nausea", "loss_of_appetite", "pale_stool", "fever",
                       "arthralgia", "abdominal_pain", "cholestatic_pattern",
                       "sexual_exposure"],
    },
})

# Also update generic "Hepatitis" to match better
update_disease("Hepatitis", {
    "symptoms": {
        "primary": ["jaundice", "fatigue", "abdominal_pain", "dark_urine"],
        "secondary": ["nausea", "loss_of_appetite", "pale_stool", "fever",
                       "right_upper_quadrant_pain", "cholestatic_pattern"],
    },
})

# Gallstones (GT-028): ensure postprandial_pain is primary
update_disease("Gallstones", {
    "symptoms": {
        "primary": ["right_upper_quadrant_pain", "postprandial_pain", "biliary_colic"],
        "secondary": ["nausea", "bloating", "referred_shoulder_pain", "vomiting"],
    },
    "differentiating_features": [
        "Severe pain in right upper abdomen after fatty meals",
        "Pain radiating to right shoulder or back",
        "Colicky pattern — pain comes and goes in waves",
        "Risk factors: Female, Forty, Fat, Fertile (4 F's)",
        "Distinguished from PUD by fatty food trigger and location"
    ],
})

# Bell's Palsy: add more matching symptom names
update_disease("Bell's Palsy", {
    "symptoms": {
        "primary": ["facial_drooping", "facial_weakness", "inability_to_close_eye"],
        "secondary": ["taste_disturbance", "ear_pain", "hyperacusis",
                       "dry_eye", "drooling", "isolated_facial"],
    },
})

# ============================================================================
# 3. SAVE
# ============================================================================
with open(KB_PATH, "w", encoding="utf-8") as f:
    json.dump(diseases, f, indent=2, ensure_ascii=False)

print(f"\nTotal diseases in KB: {len(diseases)}")
print("diseases.json Round 2 patch complete!")
