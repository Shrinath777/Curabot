"""Diagnose the 10 remaining golden test failures by tracing symptom extraction + scoring."""
import json, os, sys, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator
from agents.evidence_evaluator import evidence_evaluator
from agents.hypothesis_reviser import hypothesis_reviser

FAILING_IDS = ["GT-006","GT-008","GT-023","GT-026","GT-027","GT-028","GT-032","GT-037","GT-042","GT-047"]

cases_path = os.path.join(os.path.dirname(__file__), "evaluation", "golden_test_cases.json")
with open(cases_path, "r", encoding="utf-8") as f:
    all_cases = json.load(f)

cases = [c for c in all_cases if c["id"] in FAILING_IDS]

async def diagnose(case):
    cid = case["id"]
    gt = case["ground_truth"]
    msg = case["patient_message"]
    
    print(f"\n{'='*70}")
    print(f"  {cid}: Expected = {gt}")
    print(f"  Message: {msg[:100]}...")
    
    # Step 1: Keyword extraction
    normalized = symptom_normalizer._keyword_fallback(msg)
    syms = [s["name"] for s in normalized["primary_symptoms"]]
    systems = [s.get("body_system","?") for s in normalized["primary_symptoms"]]
    print(f"  Extracted symptoms ({len(syms)}): {syms}")
    print(f"  Systems: {list(set(systems))}")
    
    # Step 2: Hypothesis generation
    hyp_result = hypothesis_generator._fallback_hypotheses(normalized)
    hypotheses = hyp_result.get("hypotheses", [])
    print(f"  Top-5 hypotheses:")
    for i, h in enumerate(hypotheses[:5]):
        print(f"    {i+1}. {h['name']} ({h['confidence']}%) — {h.get('reasoning','')[:80]}")
    
    # Check if ground truth appears at all
    all_hyps = hyp_result.get("hypotheses", [])
    gt_found = None
    for i, h in enumerate(all_hyps):
        if gt.lower() in h["name"].lower() or h["name"].lower() in gt.lower():
            gt_found = (i+1, h["name"], h["confidence"])
            break
    
    if gt_found:
        print(f"  >>> Ground truth found at rank #{gt_found[0]}: '{gt_found[1]}' ({gt_found[2]}%)")
    else:
        print(f"  >>> Ground truth '{gt}' NOT FOUND in ANY hypothesis!")
        # Check what disease KB names might match
        diseases = json.load(open("data/diseases.json","r",encoding="utf-8"))
        matches = [d["name"] for d in diseases if gt.lower().replace("(afib)","").strip() in d["name"].lower() or d["name"].lower() in gt.lower()]
        if matches:
            print(f"  >>> KB has similar: {matches}")
            # Check their symptom overlap
            for m in matches:
                d = next(dd for dd in diseases if dd["name"] == m)
                dsyms = d.get("symptoms",{})
                if isinstance(dsyms, dict):
                    all_d = dsyms.get("primary",[]) + dsyms.get("secondary",[])
                else:
                    all_d = []
                overlap = set(s.lower().replace("_"," ") for s in syms) & set(s.lower().replace("_"," ") for s in all_d)
                print(f"      '{m}' primary+secondary: {all_d}")
                print(f"      Overlap with patient: {overlap}")
        else:
            print(f"  >>> No matching disease name found in KB!")

async def main():
    for c in cases:
        await diagnose(c)

asyncio.run(main())
