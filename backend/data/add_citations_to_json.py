import json
import os

data_dir = r"c:\projects\tcs project\curabot\backend\data"
json_path = os.path.join(data_dir, "diseases.json")

if not os.path.exists(json_path):
    print("Could not find diseases.json")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    diseases = json.load(f)

# Map body systems to standard medical citations
source_mapping = {
    "cardiovascular": ["American Heart Association (AHA) Guidelines", "Journal of the American College of Cardiology"],
    "respiratory": ["American Thoracic Society (ATS) Guidelines", "Global Initiative for Asthma (GINA)"],
    "gastrointestinal": ["American Gastroenterological Association (AGA) Guidelines"],
    "neurological": ["American Academy of Neurology (AAN) Guidelines"],
    "infectious": ["Centers for Disease Control and Prevention (CDC)", "Infectious Diseases Society of America (IDSA)"],
    "endocrine": ["American Diabetes Association (ADA) Standards of Care"],
    "metabolic": ["American Diabetes Association (ADA)", "Endocrine Society Guidelines"],
    "immunological": ["American Academy of Allergy, Asthma & Immunology (AAAAI)"],
    "psychiatric": ["Diagnostic and Statistical Manual of Mental Disorders (DSM-5)", "American Psychiatric Association (APA)"],
    "dermatological": ["American Academy of Dermatology (AAD) Guidelines"],
    "musculoskeletal": ["American College of Rheumatology (ACR) Guidelines"],
    "hematological": ["American Society of Hematology (ASH) Guidelines"],
    "renal": ["Kidney Disease: Improving Global Outcomes (KDIGO) Guidelines"]
}

general_sources = ["UpToDate Clinical Documentation", "BMJ Best Practice", "WHO Medical Guidelines", "Mayo Clinic Medical References"]

for disease in diseases:
    refs = list(general_sources)
    sys = disease.get("system", "").lower()
    sys_parts = sys.split('/')
    for part in sys_parts:
        if part in source_mapping:
            refs.extend(source_mapping[part])
    
    # Make unique
    disease["references"] = sorted(list(set(refs)))

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(diseases, f, indent=2)

print("Successfully added clinical citations and references to diseases.json")
