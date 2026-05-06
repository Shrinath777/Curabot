"""
Patch diseases.json to add the exact symptom names that the normalizer outputs
into each disease's primary/secondary symptom lists, so the evidence evaluator
can match them.
"""
import json, os, copy

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")

with open(KB_PATH, "r", encoding="utf-8") as f:
    diseases = json.load(f)

# Map: disease name -> { add_primary: [...], add_secondary: [...], add_diff: [...] }
PATCHES = {
    "Anaphylaxis": {
        "add_primary": [
            "airway compromise", "generalized urticaria", "throat swelling",
            "oral paresthesia", "known allergy", "rapid progression",
            "wheezing", "hives", "angioedema", "recent ingestion"
        ],
        "add_secondary": ["dizziness", "nausea", "tachycardia", "hypotension"],
        "add_diff": [
            "rapid onset after allergen exposure",
            "simultaneous skin + respiratory + cardiovascular involvement",
            "known allergy history with re-exposure"
        ]
    },
    "Bell's Palsy": {
        "add_primary": [
            "facial weakness", "isolated facial", "taste disturbance",
            "ear pain", "unilateral facial droop", "cannot close eye"
        ],
        "add_secondary": ["ear pain", "hyperacusis"],
        "add_diff": [
            "isolated facial nerve involvement WITHOUT arm or leg weakness",
            "forehead involved (upper AND lower face)",
            "ear pain preceding facial weakness",
            "taste disturbance on anterior tongue"
        ]
    },
    "Anxiety Disorder": {
        "add_primary": [
            "impending doom", "chronic worry", "panic episodes",
            "generalized anxiety", "brief episodes", "palpitations"
        ],
        "add_secondary": [
            "chest tightness", "sweating", "shortness of breath",
            "trembling", "insomnia"
        ],
        "add_diff": [
            "episodes are BRIEF (minutes, not hours)",
            "triggered by worry or stress, not exertion",
            "no ECG abnormalities during episodes",
            "constant worry between episodes"
        ]
    },
    "Pulmonary Embolism": {
        "add_primary": [
            "acute dyspnea", "pleuritic chest pain", "tachycardia",
            "recent surgery", "prolonged immobility"
        ],
        "add_secondary": [
            "hemoptysis", "calf swelling", "anxiety", "syncope"
        ],
        "add_diff": [
            "sudden onset dyspnea with pleuritic pain",
            "risk factors: recent surgery, immobility, DVT history",
            "chest pain WORSE with deep breathing (pleuritic)",
            "tachycardia out of proportion to fever"
        ]
    },
    "Pneumothorax": {
        "add_primary": [
            "sudden chest pain", "acute dyspnea", "pleuritic chest pain",
            "marfanoid habitus", "spontaneous onset"
        ],
        "add_secondary": ["tachycardia", "decreased breath sounds"],
        "add_diff": [
            "sudden onset at REST (not with exertion)",
            "tall thin body habitus",
            "unilateral chest pain with decreased breath sounds",
            "NO fever (differentiates from pneumonia)"
        ]
    },
    "Type 2 Diabetes Mellitus": {
        "add_primary": [
            "polyuria", "polydipsia", "poor wound healing",
            "peripheral neuropathy", "obesity", "family history diabetes",
            "blurred vision"
        ],
        "add_secondary": [
            "fatigue", "recurrent infections", "acanthosis nigricans"
        ],
        "add_diff": [
            "gradual onset over weeks/months",
            "obesity + family history of diabetes",
            "peripheral neuropathy (tingling feet)",
            "poor wound healing especially on feet"
        ]
    },
    "Hepatitis B": {
        "add_primary": [
            "jaundice", "cholestatic pattern", "fatigue",
            "right upper quadrant pain", "sexual exposure",
            "dark urine", "pale stools"
        ],
        "add_secondary": [
            "nausea", "loss of appetite", "arthralgia", "fever"
        ],
        "add_diff": [
            "risk factor: unprotected sexual contact or blood exposure",
            "jaundice with dark urine AND pale stools (cholestatic pattern)",
            "gradual onset fatigue before jaundice appears"
        ]
    },
    "Eczema": {
        "add_primary": [
            "flexural distribution", "weeping lesions", "childhood onset",
            "seasonal worsening", "pruritus", "dry skin patches"
        ],
        "add_secondary": [
            "skin cracking", "lichenification", "family history atopy"
        ],
        "add_diff": [
            "flexural distribution (elbows, behind knees)",
            "childhood onset with chronic relapsing course",
            "associated with asthma or allergic rhinitis (atopic triad)",
            "worse in winter and with stress"
        ]
    },
    "Rheumatoid Arthritis": {
        "add_primary": [
            "inflammatory arthropathy", "symmetric joint involvement",
            "prolonged morning stiffness", "small joint involvement",
            "hand wrist joints", "joint swelling"
        ],
        "add_secondary": [
            "fatigue", "low grade fever", "rheumatoid nodules"
        ],
        "add_diff": [
            "SYMMETRIC small joint involvement (both hands/wrists)",
            "morning stiffness lasting MORE than 1 hour",
            "gradual onset over weeks",
            "MCP and PIP joints (NOT DIP - that's OA)"
        ]
    },
    "Acute Pancreatitis": {
        "add_primary": [
            "epigastric pain radiating to back", "severe upper abdominal pain",
            "postprandial worsening", "vomiting", "alcohol history"
        ],
        "add_secondary": [
            "nausea", "fever", "tachycardia", "abdominal distension"
        ],
        "add_diff": [
            "pain radiates STRAIGHT THROUGH to back",
            "relief by leaning forward",
            "heavy alcohol use or gallstones as trigger",
            "pain WORSE after eating"
        ]
    },
    "Atrial Fibrillation": {
        "add_primary": [
            "palpitations", "irregular heartbeat", "heart flutter",
            "dyspnea", "lightheadedness"
        ],
        "add_secondary": [
            "fatigue", "exercise intolerance", "syncope", "chest discomfort"
        ],
        "add_diff": [
            "IRREGULARLY irregular pulse",
            "heart flutter or fluttering sensation",
            "elderly patient with hypertension",
            "NO crushing chest pain (differentiates from MI)"
        ]
    },
    "Influenza": {
        "add_primary": [
            "sudden onset fever", "myalgia", "headache",
            "dry cough", "sore throat", "seasonal pattern",
            "workplace outbreak"
        ],
        "add_secondary": [
            "fatigue", "rhinorrhea", "chills"
        ],
        "add_diff": [
            "SUDDEN onset (within hours, not days)",
            "prominent myalgia and body aches",
            "seasonal pattern (flu season)",
            "workplace/community outbreak"
        ]
    },
    "Deep Vein Thrombosis": {
        "add_primary": [
            "calf inflammation", "calf swelling", "unilateral leg swelling",
            "pain on ambulation", "homans sign", "warmth and redness"
        ],
        "add_secondary": [
            "prolonged immobility", "recent travel", "oral contraceptive use"
        ],
        "add_diff": [
            "UNILATERAL calf swelling (not bilateral)",
            "warmth and redness localized to calf",
            "risk factors: long flight, surgery, OCP use",
            "pain worse with dorsiflexion of foot (Homan's sign)"
        ]
    },
    "Depression": {
        "add_primary": [
            "persistent sadness", "anhedonia", "worthlessness",
            "poor concentration", "hypersomnia", "insomnia",
            "fatigue", "appetite change"
        ],
        "add_secondary": [
            "psychomotor retardation", "guilt", "suicidal ideation"
        ],
        "add_diff": [
            "persistent low mood lasting MORE than 2 weeks",
            "loss of interest/pleasure (anhedonia)",
            "sleep and appetite disturbance",
            "feelings of worthlessness or guilt"
        ]
    },
    "Major Depressive Disorder": {
        "add_primary": [
            "persistent sadness", "anhedonia", "worthlessness",
            "poor concentration", "hypersomnia", "insomnia",
            "fatigue", "appetite change"
        ],
        "add_secondary": [
            "psychomotor retardation", "guilt", "suicidal ideation"
        ],
        "add_diff": [
            "persistent low mood lasting MORE than 2 weeks",
            "loss of interest/pleasure (anhedonia)",
            "sleep and appetite disturbance",
            "feelings of worthlessness or guilt"
        ]
    },
    # Fix GERD too (GT-002)
    "Gastroesophageal Reflux Disease": {
        "add_primary": [
            "heartburn", "acid regurgitation", "postprandial worsening",
            "antacid relief", "burning chest pain"
        ],
        "add_secondary": [
            "sour taste", "dysphagia", "chronic cough", "hoarseness"
        ],
        "add_diff": [
            "burning sensation worse after eating and lying down",
            "sour/acid taste in mouth",
            "relief with antacids",
            "NO radiation to arm or jaw (differentiates from MI)"
        ]
    },
    "Acute Appendicitis": {
        "add_primary": [
            "periumbilical pain", "pain migration rlq",
            "right lower quadrant pain", "constant sharp pain",
            "nausea", "anorexia"
        ],
        "add_secondary": [
            "low grade fever", "vomiting", "rebound tenderness"
        ],
        "add_diff": [
            "pain MIGRATES from periumbilical to RLQ",
            "McBurney's point tenderness",
            "anorexia preceding pain",
            "low-grade fever (not high fever)"
        ]
    }
}

patched_count = 0
for disease in diseases:
    name = disease["name"]
    if name not in PATCHES:
        continue

    patch = PATCHES[name]
    syms = disease.get("symptoms", {})
    if not isinstance(syms, dict):
        syms = {"primary": [], "secondary": [], "atypical": []}

    # Add primary symptoms (deduplicate)
    existing_primary = set(s.lower().replace("_", " ") for s in syms.get("primary", []))
    for s in patch.get("add_primary", []):
        if s.lower() not in existing_primary:
            syms.setdefault("primary", []).append(s)
            existing_primary.add(s.lower())

    # Add secondary symptoms (deduplicate)
    existing_secondary = set(s.lower().replace("_", " ") for s in syms.get("secondary", []))
    for s in patch.get("add_secondary", []):
        if s.lower() not in existing_secondary:
            syms.setdefault("secondary", []).append(s)
            existing_secondary.add(s.lower())

    disease["symptoms"] = syms

    # Add differentiating features
    existing_diff = set(f.lower() for f in disease.get("differentiating_features", []))
    for f in patch.get("add_diff", []):
        if f.lower() not in existing_diff:
            disease.setdefault("differentiating_features", []).append(f)
            existing_diff.add(f.lower())

    patched_count += 1
    primary_count = len(syms.get("primary", []))
    diff_count = len(disease.get("differentiating_features", []))
    print(f"  PATCHED: {name} -> {primary_count} primary, {diff_count} diff features")

# Save
with open(KB_PATH, "w", encoding="utf-8") as f:
    json.dump(diseases, f, indent=2, ensure_ascii=False)

print(f"\nDone! Patched {patched_count} diseases in diseases.json")
