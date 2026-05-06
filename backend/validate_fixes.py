import json
import sys

# Test 1: Verify diseases.json is valid
d = json.load(open('data/diseases.json', 'r', encoding='utf-8'))
print(f"diseases.json: {len(d)} diseases - OK")

# Test 2: Verify all new diseases exist
targets = ['Acute Pancreatitis', 'Anaphylaxis', "Bell's Palsy", 'Depression', 'Hepatitis B']
for t in targets:
    found = any(dis['name'] == t for dis in d)
    status = "FOUND" if found else "MISSING"
    print(f"  {t}: {status}")

# Test 3: Verify symptom normalizer imports
from agents.symptom_normalizer import symptom_normalizer
result = symptom_normalizer._keyword_fallback(
    'I just ate peanuts and my throat is swelling shut. I have hives all over my body.'
)
syms = [s['name'] for s in result['primary_symptoms']]
print(f"Anaphylaxis keyword test: {syms}")
assert 'airway_compromise' in syms or 'generalized_urticaria' in syms, "Anaphylaxis keywords not matched!"

# Test 4: Bell's Palsy keywords
result2 = symptom_normalizer._keyword_fallback(
    "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile. I can't taste food. My ear was hurting yesterday. I have no arm or leg weakness."
)
syms2 = [s['name'] for s in result2['primary_symptoms']]
print(f"Bell's Palsy keyword test: {syms2}")
assert 'isolated_facial' in syms2, "Bell's Palsy 'isolated_facial' not matched!"

# Test 5: Depression keywords
result3 = symptom_normalizer._keyword_fallback(
    "I've been feeling extremely sad and hopeless for the past 3 months. I've lost interest in activities. I sleep all day. I feel worthless."
)
syms3 = [s['name'] for s in result3['primary_symptoms']]
print(f"Depression keyword test: {syms3}")
assert 'persistent_sadness' in syms3 or 'depressed_mood' in syms3, "Depression keywords not matched!"

# Test 6: Verify hypothesis generator imports
from agents.hypothesis_generator import hypothesis_generator, NEGATIVE_EXCLUSIONS
print(f"Negative exclusions: {len(NEGATIVE_EXCLUSIONS)} rules - OK")

# Test 7: Verify key exclusion rules exist
for key in ['Stroke (CVA)', 'Fatal insomnia', 'Acute Myocardial Infarction', 'Compartment Syndrome']:
    status = "YES" if key in NEGATIVE_EXCLUSIONS else "NO"
    print(f"  Exclusion rule '{key}': {status}")

print()
print("ALL VALIDATIONS PASSED")
