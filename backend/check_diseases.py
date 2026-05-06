import json

diseases = json.load(open('data/diseases.json', 'r', encoding='utf-8'))
targets = [
    'Pulmonary Embolism', 'Rheumatoid Arthritis', 'Acute Pancreatitis',
    'Atrial Fibrillation', 'Anxiety Disorder', 'Influenza', 'Pneumothorax',
    'Type 2 Diabetes Mellitus', 'Eczema', 'Anaphylaxis',
    'Major Depressive Disorder', 'Hepatitis', 'Gastroenteritis',
    'Osteoarthritis', 'Bell\'s Palsy', 'Depression',
    'Hepatitis B'
]

name_map = {d['name']: i for i, d in enumerate(diseases)}

for t in targets:
    found = None
    if t in name_map:
        found = t
    else:
        for name in name_map:
            if t.lower() in name.lower():
                found = name
                break
    if found:
        idx = name_map[found]
        d = diseases[idx]
        syms = d.get('symptoms', {})
        diff = d.get('differentiating_features', [])
        sev = d.get('severity_class', '?')
        system = d.get('system', '?')
        if isinstance(syms, dict):
            p = syms.get('primary', [])
            s = syms.get('secondary', [])
            a = syms.get('atypical', [])
        else:
            p, s, a = [], [], []
        print(f"=== {found} ===")
        print(f"  severity={sev} | system={system}")
        print(f"  primary({len(p)}): {p}")
        print(f"  secondary({len(s)}): {s}")
        print(f"  atypical({len(a)}): {a}")
        print(f"  differentiating({len(diff)}): {diff}")
        print()
    else:
        print(f"=== MISSING: {t} ===")
        print()
