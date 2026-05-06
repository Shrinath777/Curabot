import json

d = json.load(open('data/diseases.json', 'r', encoding='utf-8'))
names = [x['name'].lower() for x in d]

targets = [
    'Anaphylaxis', "Bell's Palsy", 'Anxiety Disorder', 'Panic Disorder',
    'Pulmonary Embolism', 'Pneumothorax', 'Type 2 Diabetes Mellitus',
    'Hepatitis B', 'Eczema', 'Atopic Dermatitis',
    'Rheumatoid Arthritis', 'Acute Pancreatitis',
    'Atrial Fibrillation', 'Influenza', 'Deep Vein Thrombosis',
    'Depression', 'Major Depressive Disorder'
]

print("=== Knowledge Base Disease Coverage ===")
for t in targets:
    found = t.lower() in names
    # Also check partial
    partial = any(t.lower() in n or n in t.lower() for n in names)
    status = "FOUND" if found else ("PARTIAL" if partial else "MISSING")
    if found:
        idx = names.index(t.lower())
        disease = d[idx]
        primary = disease.get('primary_symptoms', [])
        print(f"  {t}: {status} (primary: {len(primary)} symptoms)")
    else:
        if partial:
            matches = [n for n in names if t.lower() in n or n in t.lower()]
            print(f"  {t}: {status} -> matched: {matches}")
        else:
            print(f"  {t}: {status}")
