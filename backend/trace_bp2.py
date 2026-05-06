"""Exact trace of why Bell's Palsy match fails in _fallback_hypotheses."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer

msg = "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile on that side. I can't taste food properly. My ear was hurting yesterday. I have no arm or leg weakness."
normalized = symptom_normalizer._keyword_fallback(msg)
primary = normalized.get("primary_symptoms", [])
secondary = normalized.get("secondary_symptoms", [])
all_patient_symptoms = primary + secondary

def normalize(name):
    return name.lower().replace("_", " ").replace("-", " ").strip()

symptom_names_normalized = [normalize(s.get("name", "")) for s in all_patient_symptoms]
print(f"Patient symptoms: {symptom_names_normalized}")

# Load diseases
diseases = json.load(open("data/diseases.json","r",encoding="utf-8"))

# Check every disease for match
bp = next((d for d in diseases if d["name"] == "Bell's Palsy"), None)
bp_symptoms = bp["symptoms"].get("primary",[]) + bp["symptoms"].get("secondary",[]) + bp["symptoms"].get("atypical",[])
bp_normalized = [normalize(ds) for ds in bp_symptoms]
print(f"BP symptoms: {bp_normalized}")

# Manual matching like _fallback_hypotheses
for patient_sym in symptom_names_normalized:
    found = False
    for ds_norm, ds_orig in zip(bp_normalized, bp_symptoms):
        if patient_sym == ds_norm:
            print(f"  EXACT: '{patient_sym}' == '{ds_norm}'")
            found = True
            break
        elif len(patient_sym) > 5 and len(ds_norm) > 5:
            shorter = min(len(patient_sym), len(ds_norm))
            longer = max(len(patient_sym), len(ds_norm))
            ratio = shorter / longer
            if (patient_sym in ds_norm or ds_norm in patient_sym) and ratio > 0.65:
                print(f"  FUZZY: '{patient_sym}' <-> '{ds_norm}' (ratio={ratio:.2f})")
                found = True
                break
    if not found:
        print(f"  NO MATCH: '{patient_sym}' (len={len(patient_sym)})")

# Check if 'facial drooping' exactly matches
ps = "facial drooping"
ds = "facial drooping"
print(f"\nDirect comparison: '{ps}' == '{ds}' -> {ps == ds}")
print(f"  len(ps)={len(ps)}, len(ds)={len(ds)}")
print(f"  repr(ps)={repr(ps)}, repr(ds)={repr(ds)}")
