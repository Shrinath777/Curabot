import json

new_diseases = [
  {
    "name": "Peptic Ulcer Disease",
    "icd10": "K27",
    "system": "gastrointestinal",
    "acuity": "chronic_with_acute_exacerbations",
    "prevalence": "common",
    "description": "Sores that develop on the lining of the stomach, lower esophagus, or small intestine.",
    "symptoms": {
      "primary": ["upper_abdominal_pain", "heartburn"],
      "secondary": ["feeling_full", "bloating", "nausea", "intolerance_to_fatty_foods", "frequent_burping"],
      "atypical": ["unexplained_weight_loss", "appetite_changes"]
    },
    "vital_sign_patterns": {
      "heart_rate": "Normal or elevated if bleeding",
      "blood_pressure": "Normal or low if bleeding",
      "oxygen_saturation": ">=95",
      "temperature": "Normal"
    },
    "lab_tests": ["Endoscopy", "H. pylori testing (breath test/stool antigen)", "CBC (if bleeding suspected)"],
    "key_diagnostic_questions": [
      "Is the pain a burning sensation in your upper stomach?",
      "Does the pain get better or worse after eating?",
      "Does the pain wake you up in the middle of the night?",
      "Have you noticed your stool becoming dark or black?",
      "Do you frequently take painkillers like ibuprofen, naproxen, or aspirin?",
      "Do you feel full very quickly when eating?"
    ],
    "risk_factors": ["h_pylori_infection", "nsaid_use", "smoking", "alcohol", "stress"],
    "red_flags": ["Vomiting blood or coffee-ground material", "Black, tarry stools", "Sudden, severe abdominal pain (perforation)"]
  },
  {
    "name": "Migraine",
    "icd10": "G43",
    "system": "neurological",
    "acuity": "chronic_with_acute_exacerbations",
    "prevalence": "very_common",
    "description": "A neurological condition causing severe, throbbing headaches usually on one side of the head.",
    "symptoms": {
      "primary": ["throbbing_headache", "photophobia"],
      "secondary": ["phonophobia", "nausea", "vomiting", "visual_aura", "neck_stiffness"],
      "atypical": ["dizziness", "confusion", "numbness_or_tingling"]
    },
    "vital_sign_patterns": {
      "heart_rate": "Normal",
      "blood_pressure": "Normal or slightly elevated during pain",
      "oxygen_saturation": ">=95",
      "temperature": "Normal"
    },
    "lab_tests": ["Clinical Diagnosis", "MRI Brain (to rule out other causes)", "CT Scan"],
    "key_diagnostic_questions": [
      "Is the headache throbbing or pulsing?",
      "Is the pain primarily on one side of your head?",
      "Does bright light or loud noise make the headache worse?",
      "Do you feel nauseous or have you vomited during the headache?",
      "Do you see flashing lights, zig-zag lines, or blind spots before the headache starts?",
      "Does physical activity or moving around make the headache much worse?"
    ],
    "risk_factors": ["family_history", "female_sex", "stress", "sleep_changes", "certain_foods", "hormonal_changes"],
    "red_flags": ["Thunderclap headache (sudden and severe)", "Headache with fever or stiff neck", "New headache pattern after age 50", "Neurological deficits like weakness"]
  },
  {
    "name": "Osteoarthritis",
    "icd10": "M19.9",
    "system": "musculoskeletal",
    "acuity": "chronic",
    "prevalence": "very_common",
    "description": "Degenerative joint disease involving cartilage loss and bone changes.",
    "symptoms": {
      "primary": ["joint_pain", "joint_stiffness"],
      "secondary": ["loss_of_flexibility", "grating_sensation", "bone_spurs", "joint_swelling"],
      "atypical": ["referred_pain", "muscle_weakness"]
    },
    "vital_sign_patterns": {
      "heart_rate": "Normal",
      "blood_pressure": "Normal",
      "oxygen_saturation": ">=95",
      "temperature": "Normal"
    },
    "lab_tests": ["X-ray of affected joints", "MRI (if soft tissue suspected)", "Joint Fluid Analysis (to rule out infection/gout)"],
    "key_diagnostic_questions": [
      "Does the joint pain get worse after activity and better with rest?",
      "Are your joints stiff when you wake up in the morning, and does it loosen up within 30 minutes?",
      "Do you hear a clicking, cracking, or grating sound when moving the joint?",
      "Have you noticed any hard lumps forming around your joints, especially fingers?",
      "Which specific joints are hurting you the most? (e.g., knees, hips, hands)",
      "Does the pain prevent you from doing daily activities like walking or climbing stairs?"
    ],
    "risk_factors": ["older_age", "obesity", "previous_joint_injury", "repetitive_stress", "genetics", "female_sex"],
    "red_flags": ["Hot, red, and rapidly swelling joint (infection/gout)", "Inability to bear any weight on the joint", "Fever with joint pain"]
  },
  {
    "name": "Deep Vein Thrombosis",
    "icd10": "I80.2",
    "system": "cardiovascular",
    "acuity": "acute",
    "prevalence": "uncommon_but_dangerous",
    "description": "Formation of a blood clot in a deep vein, usually in the legs.",
    "symptoms": {
      "primary": ["leg_swelling", "leg_pain_or_cramping"],
      "secondary": ["red_or_discolored_skin_on_leg", "feeling_of_warmth_in_leg", "tenderness_in_calf"],
      "atypical": ["unexplained_fever", "pain_only_when_standing_or_walking"]
    },
    "vital_sign_patterns": {
      "heart_rate": "Normal or mildly elevated",
      "blood_pressure": "Normal",
      "oxygen_saturation": ">=95",
      "temperature": "Normal or low-grade fever"
    },
    "lab_tests": ["Doppler Ultrasound of the leg", "D-Dimer Test", "Venography", "MRI/CT Scan"],
    "key_diagnostic_questions": [
      "Is the swelling or pain strictly in one leg?",
      "Does the pain start in your calf and feel like cramping or a severe charley horse?",
      "Does the affected area feel warmer to the touch than the rest of your skin?",
      "Is the skin over the painful area turning red or a different color?",
      "Have you recently been on a long flight, car ride, or bed rest?",
      "Have you had any recent surgery or major injury to your legs or pelvis?",
      "Do you have a personal or family history of blood clots?"
    ],
    "risk_factors": ["recent_surgery", "prolonged_immobility", "cancer", "pregnancy", "oral_contraceptives", "obesity", "smoking", "older_age"],
    "red_flags": ["Sudden shortness of breath or chest pain (Pulmonary Embolism)", "Coughing up blood", "Rapid pulse with lightheadedness"]
  },
  {
    "name": "Hyperthyroidism",
    "icd10": "E05.9",
    "system": "endocrine",
    "acuity": "chronic",
    "prevalence": "common",
    "description": "Overactive thyroid gland producing excess thyroid hormones, accelerating metabolism.",
    "symptoms": {
      "primary": ["unintentional_weight_loss", "palpitations"],
      "secondary": ["rapid_heartbeat", "increased_appetite", "nervousness_or_anxiety", "tremor", "sweating", "heat_intolerance"],
      "atypical": ["fatigue_despite_high_metabolism", "muscle_weakness", "frequent_bowel_movements"]
    },
    "vital_sign_patterns": {
      "heart_rate": ">100 (tachycardia)",
      "blood_pressure": "Systolic hypertension",
      "oxygen_saturation": ">=95",
      "temperature": "Normal or slightly elevated"
    },
    "lab_tests": ["TSH (low)", "Free T4 and T3 (elevated)", "Thyroid Stimulating Immunoglobulin (TSI)", "Thyroid Ultrasound", "Radioactive Iodine Uptake"],
    "key_diagnostic_questions": [
      "Have you been losing weight recently without changing your diet or exercising more?",
      "Do you feel your heart racing, pounding, or fluttering (palpitations) even when resting?",
      "Do you feel anxious, nervous, or irritable more frequently than usual?",
      "Have you noticed your hands shaking or trembling?",
      "Do you feel unusually hot or sweat heavily when others are comfortable?",
      "Have you noticed any swelling or enlargement at the base of your neck?",
      "Are you having more frequent bowel movements?"
    ],
    "risk_factors": ["female_sex", "family_history_of_thyroid_disease", "autoimmune_diseases", "recent_pregnancy", "excess_iodine"],
    "red_flags": ["Thyroid storm (high fever, severe tachycardia, delirium)", "Atrial fibrillation or signs of heart failure", "Severe eye bulging or vision problems (Graves' ophthalmopathy)"]
  }
]

import os
path = "data/diseases.json"
with open(path, "r") as f:
    data = json.load(f)

# check if we already have 30 diseases
current_names = [d["name"] for d in data]
count_added = 0
for d in new_diseases:
    if d["name"] not in current_names:
        data.append(d)
        count_added += 1

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Added {count_added} diseases. Total is now {len(data)} diseases.")
