"""
Fix: Add 8 missing diseases to diseases.json that exist in synthetic PDFs
but have no KB entry — causing 'unidentified disease' during severity checks.
"""
import json
import os

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")

missing_diseases = [
    {
        "name": "Cervical Cancer",
        "icd10": "C53",
        "system": "oncology/gynecological",
        "acuity": "chronic_with_acute_exacerbations",
        "prevalence": "common",
        "description": "Malignant neoplasm of the cervix uteri, often associated with HPV infection, treated with surgery, radiation, and chemotherapy.",
        "symptoms": {
            "primary": ["abnormal_vaginal_bleeding", "pelvic_pain"],
            "secondary": ["postcoital_bleeding", "vaginal_discharge", "weight_loss", "fatigue", "back_pain"],
            "atypical": ["leg_swelling", "flank_pain", "hematuria"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal or elevated if anemic",
            "blood_pressure": "Normal",
            "oxygen_saturation": ">=95",
            "temperature": "Normal or elevated if infection"
        },
        "lab_tests": ["Pap Smear", "HPV DNA Test", "Colposcopy with Biopsy", "SCC Antigen", "CA-125", "CBC", "Renal Function Tests", "CT/MRI Pelvis"],
        "key_diagnostic_questions": [
            "Have you noticed bleeding between periods or after sexual intercourse?",
            "Do you have unusual vaginal discharge that may be watery, bloody, or foul-smelling?",
            "Are you experiencing persistent pelvic or lower back pain?",
            "Have you been screened for HPV or had an abnormal Pap smear?",
            "Have you lost weight unintentionally?",
            "Do you have pain during urination or blood in your urine?"
        ],
        "risk_factors": ["hpv_infection", "smoking", "immunosuppression", "multiple_sexual_partners", "early_sexual_activity", "oral_contraceptive_use"],
        "red_flags": ["Heavy vaginal bleeding", "Renal failure from ureteral obstruction", "Deep vein thrombosis in legs", "Severe anemia"]
    },
    {
        "name": "Prostate Cancer",
        "icd10": "C61",
        "system": "oncology/urological",
        "acuity": "chronic",
        "prevalence": "very_common_in_older_men",
        "description": "Adenocarcinoma of the prostate gland, often slow-growing, detected by PSA screening and treated with surgery, radiation, or hormonal therapy.",
        "symptoms": {
            "primary": ["difficulty_urinating", "weak_urine_stream"],
            "secondary": ["frequent_urination", "nocturia", "hematuria", "erectile_dysfunction", "bone_pain"],
            "atypical": ["weight_loss", "fatigue", "lower_back_pain"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal",
            "blood_pressure": "Normal",
            "oxygen_saturation": ">=95",
            "temperature": "Normal"
        },
        "lab_tests": ["PSA (Prostate-Specific Antigen)", "Digital Rectal Exam", "Prostate Biopsy (Gleason Score)", "CT/MRI Pelvis", "Bone Scan", "Testosterone Level"],
        "key_diagnostic_questions": [
            "Are you having difficulty starting or maintaining a urine stream?",
            "Do you need to urinate more frequently, especially at night?",
            "Have you noticed blood in your urine or semen?",
            "Are you experiencing pain in your hips, back, or pelvis?",
            "Has your PSA level been checked recently, and was it elevated?",
            "Do you have a family history of prostate cancer?"
        ],
        "risk_factors": ["age_over_50", "family_history", "african_american_ethnicity", "obesity", "high_fat_diet"],
        "red_flags": ["Rising PSA after prostatectomy (biochemical recurrence)", "New bone pain suggesting metastasis", "Urinary retention", "Spinal cord compression"]
    },
    {
        "name": "Aortic Dissection",
        "icd10": "I71.0",
        "system": "cardiovascular",
        "acuity": "acute",
        "prevalence": "rare_but_life_threatening",
        "description": "Tear in the aortic wall causing blood to flow between layers, a surgical emergency with high mortality if untreated.",
        "symptoms": {
            "primary": ["sudden_severe_chest_pain", "tearing_back_pain"],
            "secondary": ["pulse_deficit", "hypotension", "syncope", "dyspnea", "diaphoresis"],
            "atypical": ["abdominal_pain", "stroke_symptoms", "limb_ischemia"]
        },
        "vital_sign_patterns": {
            "heart_rate": ">100 or variable",
            "blood_pressure": "Asymmetric (>20mmHg difference between arms)",
            "oxygen_saturation": "<95 if complications",
            "temperature": "Normal"
        },
        "lab_tests": ["CT Angiography (Gold Standard)", "D-Dimer (elevated)", "Troponin", "CBC", "Lactate", "Creatinine", "Transthoracic/Transesophageal Echo"],
        "key_diagnostic_questions": [
            "Did you experience a sudden, severe, tearing or ripping pain in your chest or back?",
            "Did the pain start abruptly at its worst intensity?",
            "Does the pain radiate to your back, between your shoulder blades?",
            "Do you have a history of high blood pressure?",
            "Have you ever been told you have a connective tissue disorder like Marfan syndrome?",
            "Do you notice any difference in pulse or blood pressure between your arms?",
            "Are you experiencing any numbness, weakness, or difficulty speaking?"
        ],
        "risk_factors": ["hypertension", "connective_tissue_disorders", "bicuspid_aortic_valve", "cocaine_use", "age_over_60", "previous_cardiac_surgery"],
        "red_flags": ["Sudden tearing chest/back pain at maximum intensity from onset", "Blood pressure asymmetry between arms", "Pulse deficit", "Signs of organ malperfusion (stroke, renal failure, limb ischemia)"]
    },
    {
        "name": "Thyroid Cancer",
        "icd10": "C73",
        "system": "oncology/endocrine",
        "acuity": "chronic",
        "prevalence": "uncommon",
        "description": "Malignant neoplasm of the thyroid gland, most commonly papillary type, treated with thyroidectomy and radioactive iodine ablation.",
        "symptoms": {
            "primary": ["thyroid_nodule", "neck_swelling"],
            "secondary": ["hoarseness", "difficulty_swallowing", "neck_pain", "enlarged_lymph_nodes"],
            "atypical": ["cough", "shortness_of_breath", "weight_changes"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal or elevated if hyperthyroid",
            "blood_pressure": "Normal",
            "oxygen_saturation": ">=95",
            "temperature": "Normal"
        },
        "lab_tests": ["Thyroid Ultrasound", "Fine Needle Aspiration Biopsy", "Thyroglobulin Level", "TSH", "Free T4", "Anti-Thyroglobulin Antibodies", "Radioactive Iodine Scan", "Calcium Level"],
        "key_diagnostic_questions": [
            "Have you noticed a lump or swelling in the front of your neck?",
            "Has your voice become hoarse or changed recently?",
            "Do you have difficulty swallowing or a feeling of something in your throat?",
            "Have you had any radiation exposure to the head or neck area?",
            "Do you have a family history of thyroid cancer or endocrine disorders?",
            "Have your thyroid levels been checked recently?"
        ],
        "risk_factors": ["radiation_exposure", "family_history", "female_sex", "age_25_to_65", "iodine_deficiency", "genetic_syndromes"],
        "red_flags": ["Rapidly growing thyroid mass", "Hoarseness with thyroid nodule (recurrent laryngeal nerve involvement)", "Fixed, hard thyroid nodule", "Rising thyroglobulin post-thyroidectomy"]
    },
    {
        "name": "Disseminated Intravascular Coagulation",
        "icd10": "D65",
        "system": "hematological",
        "acuity": "acute",
        "prevalence": "uncommon_but_life_threatening",
        "description": "Systemic activation of blood coagulation causing widespread microvascular thrombi and consumption of clotting factors, leading to simultaneous thrombosis and hemorrhage.",
        "symptoms": {
            "primary": ["bleeding_from_multiple_sites", "petechiae_purpura"],
            "secondary": ["oozing_from_iv_sites", "hematuria", "gastrointestinal_bleeding", "organ_failure"],
            "atypical": ["digital_ischemia", "skin_necrosis", "altered_mental_status"]
        },
        "vital_sign_patterns": {
            "heart_rate": ">110 (tachycardia)",
            "blood_pressure": "<90/60 if shock",
            "oxygen_saturation": "<95 if ARDS",
            "temperature": "Elevated if underlying sepsis"
        },
        "lab_tests": ["Platelet Count (decreased)", "PT/INR (prolonged)", "aPTT (prolonged)", "Fibrinogen (decreased)", "D-Dimer (markedly elevated)", "Peripheral Blood Smear (schistocytes)", "LDH"],
        "key_diagnostic_questions": [
            "Are you bleeding from multiple sites simultaneously?",
            "Have you noticed unusual bruising, tiny red spots on your skin, or oozing from wound sites?",
            "Do you have blood in your urine or stool?",
            "Have you been recently diagnosed with a severe infection (sepsis)?",
            "Have you recently undergone major surgery or trauma?",
            "Do you have a history of cancer or pregnancy complications?"
        ],
        "risk_factors": ["sepsis", "major_trauma", "cancer", "obstetric_complications", "severe_burns", "transfusion_reactions", "organ_transplant_rejection"],
        "red_flags": ["Uncontrollable bleeding from multiple sites", "Shock and organ failure", "Fibrinogen <100 mg/dL", "Platelet count <20,000"]
    },
    {
        "name": "Type 2 Diabetes Mellitus",
        "icd10": "E11",
        "system": "metabolic/endocrine",
        "acuity": "chronic",
        "prevalence": "very_common",
        "description": "Chronic metabolic disorder characterized by insulin resistance and progressive beta-cell dysfunction, causing persistent hyperglycemia and multi-organ complications.",
        "symptoms": {
            "primary": ["polyuria", "polydipsia", "fatigue"],
            "secondary": ["blurred_vision", "slow_wound_healing", "frequent_infections", "numbness_or_tingling_in_extremities", "weight_loss"],
            "atypical": ["recurrent_yeast_infections", "erectile_dysfunction", "acanthosis_nigricans"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal",
            "blood_pressure": "Often elevated (comorbid hypertension)",
            "oxygen_saturation": ">=95",
            "temperature": "Normal"
        },
        "lab_tests": ["HbA1c", "Fasting Blood Glucose", "Oral Glucose Tolerance Test (OGTT)", "Fasting Insulin", "Lipid Profile", "Urine Albumin/Creatinine Ratio", "eGFR", "Fundoscopy"],
        "key_diagnostic_questions": [
            "Are you urinating more frequently than usual, especially at night?",
            "Are you feeling excessively thirsty even after drinking water?",
            "Do you have numbness, tingling, or burning in your feet or hands?",
            "Have you noticed any wounds or cuts that are slow to heal?",
            "Do you have a family history of diabetes?",
            "Have you experienced blurred vision recently?",
            "Have you been told your blood sugar is high?",
            "Are you overweight or have you gained weight recently?"
        ],
        "risk_factors": ["obesity", "sedentary_lifestyle", "family_history", "age_over_45", "gestational_diabetes_history", "pcos", "hypertension", "dyslipidemia"],
        "red_flags": ["Diabetic foot ulcer with infection", "Sudden vision loss (retinopathy)", "Chest pain (macrovascular disease)", "Renal failure (nephropathy)", "Hyperosmolar hyperglycemic state"]
    },
    {
        "name": "Gestational Diabetes",
        "icd10": "O24.4",
        "system": "metabolic/obstetric",
        "acuity": "chronic_during_pregnancy",
        "prevalence": "common_in_pregnancy",
        "description": "Glucose intolerance first recognized during pregnancy, increasing risks of macrosomia, preeclampsia, and future Type 2 diabetes for the mother.",
        "symptoms": {
            "primary": ["elevated_blood_glucose_in_pregnancy", "increased_thirst"],
            "secondary": ["frequent_urination", "fatigue", "blurred_vision", "recurrent_infections"],
            "atypical": ["excessive_fetal_growth", "polyhydramnios"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal pregnancy range",
            "blood_pressure": "Normal or elevated (preeclampsia risk)",
            "oxygen_saturation": ">=95",
            "temperature": "Normal"
        },
        "lab_tests": ["Oral Glucose Tolerance Test (OGTT 75g)", "Fasting Blood Glucose", "HbA1c", "Fructosamine", "Fetal Ultrasound (growth monitoring)", "Biophysical Profile"],
        "key_diagnostic_questions": [
            "At how many weeks of pregnancy are you currently?",
            "Have you been told your blood sugar is high during this pregnancy?",
            "Did you have gestational diabetes in a previous pregnancy?",
            "Do you have a family history of diabetes?",
            "Have you been feeling excessively thirsty or urinating more frequently?",
            "Has your doctor mentioned that the baby is measuring larger than expected?"
        ],
        "risk_factors": ["obesity", "age_over_25", "family_history_diabetes", "previous_gestational_diabetes", "pcos", "previous_macrosomic_baby"],
        "red_flags": ["Fasting glucose >126 mg/dL (may indicate pre-existing diabetes)", "Severe hyperglycemia in third trimester", "Signs of preeclampsia", "Fetal macrosomia on ultrasound"]
    },
    {
        "name": "Hepatocellular Carcinoma",
        "icd10": "C22.0",
        "system": "oncology/hepatic",
        "acuity": "chronic_with_acute_complications",
        "prevalence": "uncommon_in_general_but_common_in_cirrhosis",
        "description": "Primary liver cancer arising from hepatocytes, most commonly occurring in the setting of chronic liver disease and cirrhosis. Treated with resection, transplant, TACE, or systemic therapy.",
        "symptoms": {
            "primary": ["abdominal_pain_right_upper_quadrant", "weight_loss"],
            "secondary": ["hepatomegaly", "ascites", "jaundice", "fatigue", "loss_of_appetite"],
            "atypical": ["paraneoplastic_syndromes", "fever_of_unknown_origin", "hypoglycemia"]
        },
        "vital_sign_patterns": {
            "heart_rate": "Normal or elevated",
            "blood_pressure": "Normal or low if decompensated",
            "oxygen_saturation": ">=95",
            "temperature": "Normal or elevated"
        },
        "lab_tests": ["AFP (Alpha-Fetoprotein)", "AFP-L3 Fraction", "Liver Function Tests (AST, ALT, Bilirubin, Albumin)", "CT/MRI Liver (Triphasic)", "Platelet Count", "INR", "Hepatitis B/C Serology"],
        "key_diagnostic_questions": [
            "Do you have a known history of liver cirrhosis or chronic hepatitis?",
            "Have you noticed pain or fullness in the upper right part of your abdomen?",
            "Have you lost weight unintentionally?",
            "Do you have yellowing of your skin or eyes?",
            "Has your abdomen become swollen with fluid?",
            "Have you been screened with liver ultrasound and AFP levels?"
        ],
        "risk_factors": ["cirrhosis", "chronic_hepatitis_b", "chronic_hepatitis_c", "alcohol_abuse", "nash", "aflatoxin_exposure", "obesity", "diabetes"],
        "red_flags": ["Rapidly rising AFP", "Tumor rupture with acute abdominal pain", "Portal vein thrombosis", "Hepatic decompensation (variceal bleed, encephalopathy)"]
    }
]

# Load existing KB
with open(KB_PATH, "r") as f:
    data = json.load(f)

existing_names = {d["name"] for d in data}
added = 0
for disease in missing_diseases:
    if disease["name"] not in existing_names:
        data.append(disease)
        added += 1
        print(f"  [+] Added: {disease['name']}")
    else:
        print(f"  [=] Already exists: {disease['name']}")

with open(KB_PATH, "w") as f:
    json.dump(data, f, indent=2)

print(f"\n{'='*60}")
print(f"  DONE! Added {added} diseases. Total is now {len(data)} diseases.")
print(f"{'='*60}")
