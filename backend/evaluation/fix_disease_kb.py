"""
CuraBot Disease KB Fixer — Fixes broken entries and adds proper differentiating features
for the 30+ diseases that are currently failing in benchmark tests.

This script:
1. Fixes entries with char-split differentiating_features (Gallstones, IBS, etc.)
2. Normalizes symptom names from 'Title Case' to 'snake_case' for consistency
3. Adds proper differentiating features where missing
4. Adds missing symptom entries for key diseases
"""

import json
import os
import re

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json")

# ============================================================================
# DISEASE FIXES: Proper differentiating features + normalized symptoms
# Each entry patches the named disease in the KB
# ============================================================================

DISEASE_PATCHES = {
    "Gallstones": {
        "symptoms": {
            "primary": ["abdominal_pain", "right_upper_quadrant_pain", "nausea"],
            "secondary": ["vomiting", "postprandial_pain", "referred_shoulder_pain", "jaundice"],
            "atypical": ["epigastric_pain", "bloating", "fever"]
        },
        "differentiating_features": [
            "Right upper quadrant pain after fatty meals (biliary colic)",
            "Pain radiating to right shoulder blade (Murphy's sign)",
            "Episodic colicky pain lasting 30 minutes to 6 hours",
            "Pain triggered by fatty food intake",
            "Female, Forty, Fertile, Fat risk factors"
        ]
    },
    "Gout": {
        "symptoms": {
            "primary": ["arthralgia", "podagra", "joint_swelling"],
            "secondary": ["acute_joint_inflammation", "limited_mobility", "fever"],
            "atypical": ["tophi", "kidney_stones"]
        },
        "differentiating_features": [
            "Acute onset monoarticular pain in first MTP joint (podagra)",
            "Exquisite tenderness — even bedsheet contact is painful",
            "Red, hot, swollen joint developing overnight",
            "History of purine-rich diet (red meat, beer, shellfish)",
            "Needle-shaped negatively birefringent crystals on aspiration"
        ]
    },
    "Irritable Bowel Syndrome": {
        "symptoms": {
            "primary": ["abdominal_pain", "altered_bowel_habit", "bloating"],
            "secondary": ["abdominal_cramps", "gas", "mucus_in_stool", "urgency"],
            "atypical": ["fatigue", "anxiety", "back_pain"]
        },
        "differentiating_features": [
            "Abdominal pain relieved by defecation",
            "Alternating constipation and diarrhea pattern",
            "Symptoms worsened by psychological stress",
            "No alarm features (no weight loss, no blood in stool, no anemia)",
            "Normal blood tests, imaging, and endoscopy results",
            "Chronic symptoms for >6 months"
        ]
    },
    "Gastroesophageal Reflux Disease (GERD)": {
        "symptoms": {
            "primary": ["heartburn", "regurgitation", "chest_pain"],
            "secondary": ["dysphagia", "chronic_cough", "hoarseness", "sore_throat"],
            "atypical": ["asthma_like_symptoms", "dental_erosion", "globus_sensation"]
        },
        "differentiating_features": [
            "Burning retrosternal chest pain worsened by lying down",
            "Symptoms worse after large or spicy meals",
            "Acid taste in mouth especially at night",
            "Symptoms improve with antacids or PPIs",
            "No exertional component (unlike cardiac chest pain)"
        ]
    },
    "Allergic Rhinitis": {
        "symptoms": {
            "primary": ["sneezing", "rhinorrhea", "nasal_congestion", "pruritus"],
            "secondary": ["watery_eyes", "postnasal_drip", "headache", "fatigue"],
            "atypical": ["cough", "ear_fullness", "sore_throat"]
        },
        "differentiating_features": [
            "Paroxysmal sneezing with clear watery nasal discharge",
            "Nasal itching and eye itching (allergic salute)",
            "Seasonal pattern or triggered by specific allergens (dust, pollen)",
            "Pale boggy nasal mucosa on examination",
            "Family history of atopy (asthma, eczema)",
            "No fever (unlike infectious rhinitis)"
        ]
    },
    "Atrial Fibrillation": {
        "symptoms": {
            "primary": ["palpitations", "irregular_heartbeat", "dyspnea"],
            "secondary": ["fatigue", "dizziness", "chest_discomfort", "exercise_intolerance"],
            "atypical": ["syncope", "anxiety", "polyuria"]
        },
        "differentiating_features": [
            "Irregularly irregular pulse on palpation",
            "Heart racing with no regular pattern",
            "Palpitations with skipped or extra beats sensation",
            "Risk of stroke due to blood pooling in atria",
            "Often triggered by alcohol, caffeine, or stress"
        ]
    },
    "Influenza": {
        "symptoms": {
            "primary": ["high_fever", "myalgia", "cough", "headache"],
            "secondary": ["fatigue", "sore_throat", "rhinorrhea", "chills"],
            "atypical": ["vomiting", "diarrhea", "conjunctivitis"]
        },
        "differentiating_features": [
            "Sudden onset of high fever with severe body aches",
            "Prominent myalgia and prostration (unlike common cold)",
            "Seasonal pattern (winter months in temperate regions)",
            "Rapid onset — healthy to very ill within hours",
            "Dry cough prominent from early course"
        ]
    },
    "Kidney Stone": {
        "symptoms": {
            "primary": ["flank_pain", "hematuria", "colicky_pain"],
            "secondary": ["nausea", "vomiting", "dysuria", "urinary_frequency"],
            "atypical": ["fever", "groin_pain", "testicular_pain"]
        },
        "differentiating_features": [
            "Acute severe colicky flank pain radiating to groin",
            "Patient writhing in pain (cannot find comfortable position)",
            "Hematuria (blood in urine) — gross or microscopic",
            "Pain in waves (ureteral peristalsis against stone)",
            "History of dehydration or calcium-rich diet"
        ]
    },
    "Anaphylaxis": {
        "symptoms": {
            "primary": ["dyspnea", "throat_swelling", "urticaria", "hypotension"],
            "secondary": ["wheezing", "tachycardia", "angioedema", "nausea", "vomiting"],
            "atypical": ["abdominal_pain", "confusion", "syncope"]
        },
        "differentiating_features": [
            "Rapid onset after known allergen exposure (food, drug, sting)",
            "Simultaneous involvement of skin AND respiratory/cardiovascular systems",
            "Throat or tongue swelling causing airway compromise",
            "Urticaria (hives) with systemic symptoms",
            "Hypotension and tachycardia (anaphylactic shock)"
        ]
    },
    "Deep Vein Thrombosis": {
        "symptoms": {
            "primary": ["leg_swelling", "leg_pain", "calf_tenderness"],
            "secondary": ["localized_warmth", "redness", "distended_superficial_veins"],
            "atypical": ["fever", "tachycardia"]
        },
        "differentiating_features": [
            "Unilateral leg swelling (asymmetric calf circumference)",
            "Calf pain and tenderness on dorsiflexion (Homan's sign)",
            "Recent surgery, immobility, or long travel history",
            "Risk factors: OCP use, malignancy, pregnancy, obesity",
            "Warm and erythematous limb compared to contralateral"
        ]
    },
    "Acute Pancreatitis": {
        "symptoms": {
            "primary": ["epigastric_pain", "radiating_back_pain", "nausea"],
            "secondary": ["vomiting", "abdominal_tenderness", "fever", "tachycardia"],
            "atypical": ["jaundice", "dyspnea", "flank_ecchymosis"]
        },
        "differentiating_features": [
            "Severe epigastric pain radiating straight through to the back",
            "Pain improved by leaning forward, worsened lying flat",
            "Heavy alcohol use or gallstone history as precipitant",
            "Elevated serum amylase and lipase (>3x upper normal)",
            "Epigastric tenderness with guarding"
        ]
    },
    "Celiac Disease": {
        "symptoms": {
            "primary": ["diarrhea", "bloating", "abdominal_pain", "weight_loss"],
            "secondary": ["fatigue", "anemia", "dermatitis_herpetiformis"],
            "atypical": ["osteoporosis", "infertility", "neurological_symptoms"]
        },
        "differentiating_features": [
            "Chronic diarrhea and bloating worsened by gluten (bread, pasta)",
            "Symptoms improve with gluten-free diet",
            "Failure to thrive in children or unexplained weight loss in adults",
            "Associated dermatitis herpetiformis (itchy blistering rash)",
            "Iron deficiency anemia unresponsive to oral iron"
        ]
    },
    "Septicemia": {
        "symptoms": {
            "primary": ["high_fever", "tachycardia", "hypotension", "confusion"],
            "secondary": ["shivering", "dyspnea", "oliguria", "altered_mental_status"],
            "atypical": ["hypothermia", "cold_clammy_skin", "lactic_acidosis"]
        },
        "differentiating_features": [
            "Fever with hemodynamic instability (low BP, high HR)",
            "Identifiable source of infection (UTI, pneumonia, wound, catheter)",
            "Altered mental status disproportionate to apparent illness",
            "Warm shock early (vasodilation) -> cold shock late",
            "SIRS criteria: HR>90, RR>20, Temp>38 or <36, WBC>12k or <4k"
        ]
    },
    "Liver Cirrhosis": {
        "symptoms": {
            "primary": ["jaundice", "ascites", "fatigue"],
            "secondary": ["easy_bruising", "spider_angiomata", "palmar_erythema", "edema"],
            "atypical": ["confusion", "gynecomastia", "muscle_wasting"]
        },
        "differentiating_features": [
            "Jaundice with abdominal distension (ascites)",
            "History of chronic alcohol use or chronic hepatitis",
            "Spider angiomata on upper body and palmar erythema",
            "Easy bruising due to impaired coagulation factor synthesis",
            "Portal hypertension signs: splenomegaly, caput medusae"
        ]
    },
    "Acute Appendicitis": {
        "symptoms": {
            "primary": ["abdominal_pain", "right_lower_quadrant_pain", "nausea"],
            "secondary": ["vomiting", "fever", "loss_of_appetite", "rebound_tenderness"],
            "atypical": ["diarrhea", "urinary_symptoms", "epigastric_pain"]
        },
        "differentiating_features": [
            "Periumbilical pain migrating to right lower quadrant over 12-24 hours",
            "Point tenderness at McBurney's point (1/3 from ASIS to umbilicus)",
            "Rebound tenderness and guarding in RLQ",
            "Low-grade fever with anorexia (loss of appetite)",
            "Pain worsens with movement, coughing, or jumping"
        ]
    },
    "Peptic Ulcer Disease": {
        "symptoms": {
            "primary": ["epigastric_pain", "heartburn", "abdominal_pain"],
            "secondary": ["bloating", "nausea", "loss_of_appetite", "dark_stool"],
            "atypical": ["vomiting", "weight_loss", "anemia"]
        },
        "differentiating_features": [
            "Epigastric burning pain 2-3 hours after meals or at night",
            "Pain relieved by eating (duodenal) or worsened by eating (gastric)",
            "History of NSAID use (aspirin, ibuprofen) or H. pylori infection",
            "Melena (dark tarry stools) indicating upper GI bleeding",
            "Periodicity: symptoms come and go over weeks"
        ]
    },
    "Urinary Tract Infection": {
        "symptoms": {
            "primary": ["dysuria", "urinary_frequency", "urgency"],
            "secondary": ["suprapubic_pain", "cloudy_urine", "hematuria"],
            "atypical": ["fever", "flank_pain", "nausea"]
        },
        "differentiating_features": [
            "Burning pain during urination (dysuria)",
            "Increased urinary frequency with small volumes",
            "Suprapubic discomfort or pressure",
            "Cloudy or foul-smelling urine",
            "Positive nitrites and leukocyte esterase on dipstick"
        ]
    },
    "Malaria": {
        "symptoms": {
            "primary": ["high_fever", "chills", "sweating", "headache"],
            "secondary": ["myalgia", "fatigue", "nausea", "vomiting"],
            "atypical": ["diarrhea", "cough", "jaundice"]
        },
        "differentiating_features": [
            "Cyclical high fevers with rigors every 48-72 hours",
            "Travel to or residence in malaria-endemic area",
            "No malaria prophylaxis during travel",
            "Splenomegaly on examination",
            "Paroxysms of chills -> fever -> profuse sweating"
        ]
    },
    "Hypothyroidism": {
        "symptoms": {
            "primary": ["fatigue", "weight_gain", "cold_intolerance"],
            "secondary": ["constipation", "dry_skin", "hair_loss", "bradycardia"],
            "atypical": ["depression", "menorrhagia", "carpal_tunnel"]
        },
        "differentiating_features": [
            "Weight gain despite normal or reduced appetite",
            "Cold intolerance with dry coarse skin",
            "Fatigue with mental sluggishness and delayed reflexes",
            "Facial puffiness (myxedema) and hoarse voice",
            "Family history of autoimmune thyroid disease"
        ]
    },
    "Rheumatoid Arthritis": {
        "symptoms": {
            "primary": ["arthralgia", "joint_swelling", "morning_stiffness"],
            "secondary": ["fatigue", "rheumatoid_nodules", "decreased_grip_strength"],
            "atypical": ["dry_eyes", "pleuritis", "vasculitis"]
        },
        "differentiating_features": [
            "Symmetric polyarthritis affecting small joints of hands and feet",
            "Morning stiffness lasting >1 hour (improves with activity)",
            "MCP and PIP joints involved (spares DIP joints)",
            "Positive rheumatoid factor or anti-CCP antibodies",
            "Progressive joint deformity if untreated"
        ]
    },
}


def normalize_symptom_name(name: str) -> str:
    """Convert 'Title Case Name' to 'snake_case_name'."""
    # Already snake_case
    if '_' in name and name == name.lower():
        return name
    # Convert Title Case or space-separated to snake_case
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name.lower()


def fix_char_split_features(features) -> list:
    """Fix differentiating_features that were char-split into individual characters."""
    if not features:
        return []
    if isinstance(features, str):
        return [features]
    if isinstance(features, list) and len(features) > 20:
        # Check if it's char-split (individual characters)
        if all(len(f) <= 2 for f in features[:10]):
            # Rejoin into a single string, then split on sentence boundaries
            joined = ''.join(features)
            parts = [s.strip() for s in re.split(r'[.;]\s*', joined) if len(s.strip()) > 10]
            return parts[:6] if parts else [joined]
    return features


def apply_patches(diseases: list) -> list:
    """Apply all patches to the disease list."""
    patched_count = 0
    fixed_features_count = 0
    normalized_count = 0

    for disease in diseases:
        name = disease["name"]

        # 1. Fix char-split differentiating features
        if "differentiating_features" in disease:
            original = disease["differentiating_features"]
            fixed = fix_char_split_features(original)
            if fixed != original:
                disease["differentiating_features"] = fixed
                fixed_features_count += 1

        # 2. Normalize symptom names from Title Case to snake_case
        if isinstance(disease.get("symptoms"), dict):
            for category in ["primary", "secondary", "atypical"]:
                if category in disease["symptoms"]:
                    original_syms = disease["symptoms"][category]
                    normalized_syms = [normalize_symptom_name(s) for s in original_syms]
                    if normalized_syms != original_syms:
                        disease["symptoms"][category] = normalized_syms
                        normalized_count += 1

        # 3. Apply specific disease patches
        if name in DISEASE_PATCHES:
            patch = DISEASE_PATCHES[name]
            if "symptoms" in patch:
                disease["symptoms"] = patch["symptoms"]
            if "differentiating_features" in patch:
                disease["differentiating_features"] = patch["differentiating_features"]
            patched_count += 1

    print(f"  Patched {patched_count} diseases with improved features")
    print(f"  Fixed {fixed_features_count} char-split differentiating_features")
    print(f"  Normalized {normalized_count} symptom name categories to snake_case")
    return diseases


def main():
    print(f"\n  Loading disease KB from: {KB_PATH}")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        diseases = json.load(f)
    print(f"  Loaded {len(diseases)} diseases")

    # Create backup
    backup_path = KB_PATH + ".backup"
    if not os.path.exists(backup_path):
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(diseases, f, indent=2, ensure_ascii=False)
        print(f"  Backup saved to: {backup_path}")

    # Apply fixes
    diseases = apply_patches(diseases)

    # Save
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(diseases, f, indent=2, ensure_ascii=False)
    print(f"  Updated KB saved to: {KB_PATH}")
    print(f"  Done!\n")


if __name__ == "__main__":
    main()
