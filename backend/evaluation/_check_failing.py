import json, os
d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'diseases.json'), 'r', encoding='utf-8'))
failing = ['Gastroesophageal Reflux Disease','Acute Appendicitis','Peptic Ulcer Disease',
    'Malaria','Urinary Tract Infection','Hypothyroidism','Rheumatoid Arthritis',
    'Acute Pancreatitis','Deep Vein Thrombosis','Bacterial Meningitis','Celiac Disease',
    'Atrial Fibrillation','Gallstones','Liver Cirrhosis','Gout','Influenza',
    'Allergic Rhinitis','Septicemia','Hepatitis','Irritable Bowel Syndrome',
    'Anaphylaxis','Acute Gastroenteritis','Depression','Kidney Stone','Bell']
for x in d:
    for f in failing:
        if f.lower() in x['name'].lower():
            df = x.get('differentiating_features', [])
            ps = x.get('symptoms', {}).get('primary', []) if isinstance(x.get('symptoms'), dict) else []
            ss = x.get('symptoms', {}).get('secondary', []) if isinstance(x.get('symptoms'), dict) else []
            print(f"{x['name']:45s} | diff_feats={len(df):2d} | primary={ps} | secondary={ss[:3]}")
            break
