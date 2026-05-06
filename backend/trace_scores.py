"""Check raw score of Bell's Palsy vs top diseases."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator, NEGATIVE_EXCLUSIONS
from collections import Counter

msg = "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile on that side. I can't taste food properly. My ear was hurting yesterday. I have no arm or leg weakness."
normalized = symptom_normalizer._keyword_fallback(msg)
primary = normalized.get("primary_symptoms", [])
secondary = normalized.get("secondary_symptoms", [])
all_patient_symptoms = primary + secondary

def normalize(name):
    return name.lower().replace("_", " ").replace("-", " ").strip()

symptom_names_normalized = [normalize(s.get("name", "")) for s in all_patient_symptoms]

# Get system counts
system_counts = Counter()
for s in all_patient_symptoms:
    sys_val = s.get("body_system", s.get("system", "unknown")).lower()
    if sys_val and sys_val != "unknown" and sys_val != "general":
        system_counts[sys_val] += 1

total_system_syms = sum(system_counts.values())
dominant_system = ""
dominant_system_ratio = 0.0
if system_counts:
    dominant_system, dom_count = system_counts.most_common(1)[0]
    dominant_system_ratio = dom_count / max(total_system_syms, 1)

print(f"Dominant system: {dominant_system} (ratio={dominant_system_ratio:.2f})")

diseases = json.load(open("data/diseases.json","r",encoding="utf-8"))
all_matches = []
all_disease_symptom_sets = {}

# Compute scores
for disease in diseases:
    disease_symptoms = []
    if isinstance(disease.get("symptoms"), dict):
        disease_symptoms = disease["symptoms"].get("primary",[]) + disease["symptoms"].get("secondary",[]) + disease["symptoms"].get("atypical",[])
    
    disease_symptoms_normalized = [normalize(ds) for ds in disease_symptoms]
    all_disease_symptom_sets[disease["name"]] = set(disease_symptoms_normalized)
    
    match_count = 0
    matched_symptoms = []
    for patient_sym in symptom_names_normalized:
        for ds_norm, ds_orig in zip(disease_symptoms_normalized, disease_symptoms):
            if patient_sym == ds_norm:
                match_count += 1
                matched_symptoms.append(ds_orig)
                break
            elif len(patient_sym) > 5 and len(ds_norm) > 5:
                shorter = min(len(patient_sym), len(ds_norm))
                longer = max(len(patient_sym), len(ds_norm))
                if (patient_sym in ds_norm or ds_norm in patient_sym) and shorter / longer > 0.65:
                    match_count += 1
                    matched_symptoms.append(ds_orig)
                    break
    
    if match_count > 0:
        all_matches.append({"disease": disease, "match_count": match_count, "matched_symptoms": matched_symptoms})

# Sort by match count
all_matches.sort(key=lambda x: x["match_count"], reverse=True)
print(f"\nTop 15 by match count:")
for m in all_matches[:15]:
    d = m["disease"]
    print(f"  {d['name']}: {m['match_count']} matches = {m['matched_symptoms']}")

# Now check scoring
print(f"\n=== Raw confidence scores ===")
SEVERITY_WEIGHT = {"critical": 1.08, "serious": 1.04, "moderate": 1.0, "benign": 0.92}
for m in all_matches[:15]:
    d = m["disease"]
    primary_syms = d.get("symptoms",{}).get("primary",[]) if isinstance(d.get("symptoms"),dict) else []
    total_primary = max(len(primary_syms), 1)
    total_all = max(len(all_disease_symptom_sets[d["name"]]), 1)
    match_ratio = m["match_count"] / total_primary
    base = min(match_ratio * 60, 60)
    coverage = m["match_count"] / total_all
    if coverage < 0.15 and m["match_count"] <= 1:
        base *= 0.25
    
    sev = SEVERITY_WEIGHT.get(d.get("severity_class","moderate"), 1.0)
    
    # System coherence
    ds = d.get("system","").lower()
    sys_mult = 1.0
    if dominant_system and dominant_system != "unknown":
        sys_match = ds == dominant_system or dominant_system in ds or ds in dominant_system
        if sys_match:
            sys_mult = 1.4
        elif ds and not sys_match and dominant_system_ratio >= 0.6:
            sys_mult = 0.7
    
    # Negative exclusions
    excl = NEGATIVE_EXCLUSIONS.get(d["name"], {})
    excl_count = 0
    for ex in excl.get("exclude_if_present",[]):
        ex_norm = normalize(ex)
        if ex_norm in symptom_names_normalized:
            excl_count += 1
    
    penalty = 1.0
    if excl_count > 0:
        penalty = excl.get("penalty", 0.3) ** excl_count
    
    conf = base * sev * sys_mult * penalty
    print(f"  {d['name']}: base={base:.1f} sev={sev:.2f} sys={sys_mult:.1f} penalty={penalty:.2f} -> RAW={conf:.1f} (matches={m['match_count']}, coverage={coverage:.2f})")
