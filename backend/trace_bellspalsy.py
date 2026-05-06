"""Trace why Bell's Palsy, Hepatitis B, Anxiety Disorder are not appearing in fallback."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator

# Bell's Palsy test
msg = "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile on that side. I can't taste food properly. My ear was hurting yesterday. I have no arm or leg weakness."
normalized = symptom_normalizer._keyword_fallback(msg)

# Manually trace the fallback
primary = normalized.get("primary_symptoms", [])
secondary = normalized.get("secondary_symptoms", [])
all_patient_symptoms = primary + secondary

def normalize(name):
    return name.lower().replace("_", " ").replace("-", " ").strip()

symptom_names_normalized = [normalize(s.get("name", "")) for s in all_patient_symptoms]
print(f"Patient symptoms: {symptom_names_normalized}")

# Find Bell's Palsy in KB
diseases = json.load(open("data/diseases.json","r",encoding="utf-8"))
bp = next((d for d in diseases if d["name"] == "Bell's Palsy"), None)

bp_symptoms = []
if isinstance(bp.get("symptoms"), dict):
    bp_symptoms = (
        bp["symptoms"].get("primary", []) +
        bp["symptoms"].get("secondary", []) +
        bp["symptoms"].get("atypical", [])
    )
bp_normalized = [normalize(ds) for ds in bp_symptoms]
print(f"BP KB symptoms: {bp_normalized}")

# Match
match_count = 0
matched_symptoms = []
for patient_sym in symptom_names_normalized:
    for ds_norm, ds_orig in zip(bp_normalized, bp_symptoms):
        if patient_sym in ds_norm or ds_norm in patient_sym or patient_sym == ds_norm:
            match_count += 1
            matched_symptoms.append(ds_orig)
            break

print(f"Bell's Palsy matches: {match_count}, matched: {matched_symptoms}")

# Now let's check what the body system is
from collections import Counter
system_counts = Counter()
for s in all_patient_symptoms:
    sys_val = s.get("body_system", s.get("system", "unknown")).lower()
    if sys_val and sys_val != "unknown" and sys_val != "general":
        system_counts[sys_val] += 1

print(f"System counts: {dict(system_counts)}")
dominant_system = system_counts.most_common(1)[0][0] if system_counts else ""
print(f"Dominant system: {dominant_system}")
print(f"Bell's Palsy system: {bp.get('system','?')}")

# The body_system coherence check — is this penalizing Bell's Palsy?
bp_system = bp.get("system", "").lower()
if dominant_system and bp_system != dominant_system:
    print(f">>> MISMATCH: Bell's Palsy system='{bp_system}' != dominant='{dominant_system}' → PENALTY applied!")
else:
    print(f">>> MATCH: system coherence OK")

# Check if "weakness" substring matching is inflating other diseases
print(f"\nChecking which diseases match 'weakness'...")
for d in diseases:
    dsyms = []
    if isinstance(d.get("symptoms"), dict):
        dsyms = d["symptoms"].get("primary",[]) + d["symptoms"].get("secondary",[])
    for ds in dsyms:
        ds_norm = normalize(ds)
        if "weakness" in ds_norm:
            print(f"  '{d['name']}' has symptom '{ds}' matching 'weakness'")
            break
