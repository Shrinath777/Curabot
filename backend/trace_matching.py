"""Trace exactly why Bell's Palsy, Hepatitis B, Anxiety Disorder don't match."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator

# Load KB
diseases = json.load(open("data/diseases.json","r",encoding="utf-8"))

# Bell's Palsy test
msg = "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile on that side. I can't taste food properly. My ear was hurting yesterday. I have no arm or leg weakness."
normalized = symptom_normalizer._keyword_fallback(msg)

print("=== BELL'S PALSY TRACE ===")
print(f"Patient symptoms: {[s['name'] for s in normalized['primary_symptoms']]}")

# Find Bell's Palsy in KB
bp = next((d for d in diseases if d["name"] == "Bell's Palsy"), None)
if bp:
    print(f"KB symptoms: {bp['symptoms']}")
    score = hypothesis_generator._score_disease(bp, normalized)
    print(f"_score_disease result: {score}")
    
    # Trace the scoring manually
    patient_symps = set()
    for cat in ["primary", "secondary", "atypical", "red_flags"]:
        patient_symps.update([str(s).lower() for s in normalized.get(cat, [])])
    print(f"Patient symps (from _score_disease): {patient_symps}")
    
    dis_symps = set()
    s_dict = bp.get("symptoms", {})
    if isinstance(s_dict, dict):
        for cat in ["primary", "secondary", "atypical"]:
            dis_symps.update([str(s).lower() for s in s_dict.get(cat, [])])
    print(f"Disease symps: {dis_symps}")
    
    overlap = patient_symps.intersection(dis_symps)
    print(f"Exact overlap: {overlap}")
    
    # Check fuzzy
    for px in patient_symps:
        for dx in dis_symps:
            if px in dx or dx in px:
                print(f"  Fuzzy match: '{px}' <-> '{dx}'")

print()

# Now trace the fallback_hypotheses matching for Bell's Palsy
print("=== FALLBACK TRACE ===")
all_patient_symptoms = normalized.get("primary_symptoms", []) + normalized.get("secondary_symptoms", [])
symptom_names_normalized = [s.get("name","").lower().replace("_"," ").replace("-"," ").strip() for s in all_patient_symptoms]
print(f"Normalized symptom names: {symptom_names_normalized}")

bp_symptoms = []
if isinstance(bp.get("symptoms"), dict):
    bp_symptoms = bp["symptoms"].get("primary",[]) + bp["symptoms"].get("secondary",[]) + bp["symptoms"].get("atypical",[])
bp_normalized = [s.lower().replace("_"," ").replace("-"," ").strip() for s in bp_symptoms]
print(f"BP KB symptoms normalized: {bp_normalized}")

match_count = 0
for patient_sym in symptom_names_normalized:
    for ds_norm in bp_normalized:
        if patient_sym in ds_norm or ds_norm in patient_sym or patient_sym == ds_norm:
            match_count += 1
            print(f"  MATCH: '{patient_sym}' <-> '{ds_norm}'")
            break
print(f"Total matches: {match_count}")

print()
print("=== _score_disease for key failures ===")
# The issue: _score_disease looks at normalized.get("primary",...) etc, NOT "primary_symptoms"
# Let me check what keys exist
print(f"Keys in normalized: {list(normalized.keys())}")
print(f"  'primary' exists: {'primary' in normalized}")
print(f"  'primary_symptoms' exists: {'primary_symptoms' in normalized}")
