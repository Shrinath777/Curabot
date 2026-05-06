"""
CuraBot Golden Test — Offline Baseline Runner (No LLM Calls)
Runs golden test cases + external validation cases using ONLY the rule-based
fallback pipeline. This gives us a clean baseline to measure LLM improvement.

Usage:
  python -m evaluation.run_baseline_tests              # Run all (internal + external)
  python -m evaluation.run_baseline_tests --internal   # Run only 50 golden cases
  python -m evaluation.run_baseline_tests --external   # Run only 15 external cases
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator
from agents.evidence_evaluator import evidence_evaluator
from agents.hypothesis_reviser import hypothesis_reviser

# Fuzzy name matching — accounts for KB naming variations
ALIASES = {
    "copd": "chronic obstructive pulmonary disease",
    "meningitis": "bacterial meningitis",
    "depression": "major depressive disorder",
    "hepatitis b": "hepatitis",
    "bell's palsy": "bell palsy",
    "anaphylaxis": "anaphylactic shock",
    "celiac disease": "celiac",
    "acute pancreatitis": "pancreatitis",
    "gastroenteritis": "acute gastroenteritis",
    "eczema": "atopic dermatitis",
    "anxiety disorder": "generalized anxiety disorder",
}

def fuzzy_match(ground_truth: str, predicted: str) -> bool:
    """Check if ground_truth matches predicted, accounting for aliases and partial containment."""
    gt = ground_truth.lower().strip()
    pred = predicted.lower().strip()
    if gt == pred:
        return True
    # Check if one contains the other
    if gt in pred or pred in gt:
        return True
    # Check aliases
    gt_alias = ALIASES.get(gt, "")
    if gt_alias and (gt_alias in pred or pred in gt_alias):
        return True
    # Check reverse alias
    for alias_key, alias_val in ALIASES.items():
        if gt == alias_key and (alias_val in pred or pred in alias_val):
            return True
        if gt == alias_val and (alias_key in pred or pred in alias_key):
            return True
    return False



def run_offline_test(case):
    """Run a single test using only rule-based fallbacks (zero LLM calls)."""
    start = time.time()
    message = case["patient_message"]

    # Agent 1: Keyword fallback
    normalized = symptom_normalizer._keyword_fallback(message)

    # Agent 2: Heuristic fallback
    hypothesis_result = hypothesis_generator._fallback_hypotheses(normalized)
    hypotheses = hypothesis_result.get("hypotheses", [])

    # Agent 3: Rule-based evidence
    evidence = []
    for s in normalized.get("primary_symptoms", []):
        evidence.append({"type": "symptom", "finding": s.get("name", ""), "detail": ""})
    for s in normalized.get("secondary_symptoms", []):
        evidence.append({"type": "symptom", "finding": s.get("name", ""), "detail": ""})
    evidence_result = evidence_evaluator._fallback_evidence(hypotheses, evidence)

    # Agent 4: Bayesian revision
    revision = hypothesis_reviser._fallback_revision(hypotheses, evidence_result)
    revised = revision.get("revised_hypotheses", hypotheses) or hypotheses

    elapsed = time.time() - start
    top_names = [h.get("name", "") for h in revised[:5]]
    gt = case["ground_truth"]

    return {
        "case_id": case["id"],
        "ground_truth": gt,
        "severity": case["severity"],
        "difficulty": case["difficulty"],
        "predicted_top1": top_names[0] if top_names else "",
        "predicted_top3": top_names[:3],
        "top1_confidence": round(revised[0].get("confidence", 0), 1) if revised else 0,
        "top1_match": any(fuzzy_match(gt, n) for n in top_names[:1]),
        "top3_match": any(fuzzy_match(gt, n) for n in top_names[:3]),
        "top5_match": any(fuzzy_match(gt, n) for n in top_names[:5]),
        "elapsed_seconds": round(elapsed, 3),
        "symptoms_found": len(normalized.get("primary_symptoms", [])) + len(normalized.get("secondary_symptoms", [])),
    }


def print_accuracy(label: str, results: list):
    """Print accuracy metrics for a set of results."""
    total = len(results)
    if total == 0:
        return
    t1 = sum(1 for r in results if r["top1_match"])
    t3 = sum(1 for r in results if r["top3_match"])
    t5 = sum(1 for r in results if r["top5_match"])
    print(f"\n  --- {label} ({total} cases) ---")
    print(f"  Top-1 Accuracy: {t1/total*100:.1f}%  ({t1}/{total})")
    print(f"  Top-3 Accuracy: {t3/total*100:.1f}%  ({t3}/{total})")
    print(f"  Top-5 Accuracy: {t5/total*100:.1f}%  ({t5}/{total})")


def main():
    parser = argparse.ArgumentParser(description="CuraBot Baseline Benchmark")
    parser.add_argument("--internal", action="store_true", help="Run only internal golden cases")
    parser.add_argument("--external", action="store_true", help="Run only external validation cases")
    args = parser.parse_args()

    eval_dir = os.path.dirname(__file__)
    cases = []
    internal_ids = set()
    external_ids = set()

    # Load internal cases
    if not args.external:
        cases_path = os.path.join(eval_dir, "golden_test_cases.json")
        with open(cases_path, "r", encoding="utf-8") as f:
            internal_cases = json.load(f)
        cases.extend(internal_cases)
        internal_ids = {c["id"] for c in internal_cases}

    # Load external cases
    if not args.internal:
        ext_path = os.path.join(eval_dir, "external_validation_cases.json")
        if os.path.exists(ext_path):
            with open(ext_path, "r", encoding="utf-8") as f:
                external_cases = json.load(f)
            cases.extend(external_cases)
            external_ids = {c["id"] for c in external_cases}
        else:
            print("  [WARN] external_validation_cases.json not found, skipping")

    print(f"\n  Running {len(cases)} tests OFFLINE (rule-based only, no LLM)...")
    print(f"  Internal: {len(internal_ids)} | External: {len(external_ids)}\n")

    results = []
    for i, case in enumerate(cases):
        result = run_offline_test(case)
        result["source"] = "external" if case["id"] in external_ids else "internal"
        results.append(result)
        match = "TOP-1" if result["top1_match"] else ("TOP-3" if result["top3_match"] else "MISS")
        sym_count = result["symptoms_found"]
        src = "EXT" if result["source"] == "external" else "INT"
        print(f"  [{i+1:2d}/{len(cases)}] [{src}] {case['id']} {case['ground_truth']:40s} -> {result['predicted_top1']:40s} {match:5s}  ({sym_count} syms, {result['elapsed_seconds']}s)")

    # Overall Metrics
    total = len(results)
    t1 = sum(1 for r in results if r["top1_match"])
    t3 = sum(1 for r in results if r["top3_match"])
    t5 = sum(1 for r in results if r["top5_match"])

    print("\n" + "=" * 75)
    print("   CURABOT GOLDEN TEST — OFFLINE BASELINE RESULTS")
    print("=" * 75)
    print(f"  Total Cases:    {total}")
    print(f"  Top-1 Accuracy: {t1/total*100:.1f}%  ({t1}/{total})")
    print(f"  Top-3 Accuracy: {t3/total*100:.1f}%  ({t3}/{total})")
    print(f"  Top-5 Accuracy: {t5/total*100:.1f}%  ({t5}/{total})")

    # Separate internal vs external accuracy
    internal_results = [r for r in results if r["source"] == "internal"]
    external_results = [r for r in results if r["source"] == "external"]
    if internal_results:
        print_accuracy("INTERNAL (Self-Authored Golden Cases)", internal_results)
    if external_results:
        print_accuracy("EXTERNAL (Medical Textbook Validation)", external_results)

    # By severity
    sev_groups = {}
    for r in results:
        s = r["severity"]
        sev_groups.setdefault(s, []).append(r)
    print("\n  --- By Severity ---")
    for sev, group in sorted(sev_groups.items()):
        s1 = sum(1 for r in group if r["top1_match"])
        s3 = sum(1 for r in group if r["top3_match"])
        print(f"    {sev:12s}  T1: {s1/len(group)*100:5.1f}%  T3: {s3/len(group)*100:5.1f}%  ({len(group)} cases)")

    # Failed
    missed = [r for r in results if not r["top3_match"]]
    if missed:
        print(f"\n  --- Missed Top-3 ({len(missed)} cases) ---")
        for r in missed:
            src = "[EXT]" if r["source"] == "external" else "[INT]"
            print(f"    {src} {r['case_id']}: Expected '{r['ground_truth']}' -> Got {r['predicted_top3']}")

    total_time = sum(r["elapsed_seconds"] for r in results)
    print(f"\n  Total Time: {total_time:.1f}s  |  Avg: {total_time/total:.3f}s per case")
    print("=" * 75 + "\n")

    # Save
    out_path = os.path.join(eval_dir, "golden_test_baseline.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "offline_baseline",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total": total, "top1": t1, "top3": t3, "top5": t5,
                "top1_pct": round(t1/total*100, 1),
                "top3_pct": round(t3/total*100, 1),
                "top5_pct": round(t5/total*100, 1),
                "internal_total": len(internal_results),
                "internal_top1": sum(1 for r in internal_results if r["top1_match"]),
                "internal_top3": sum(1 for r in internal_results if r["top3_match"]),
                "external_total": len(external_results),
                "external_top1": sum(1 for r in external_results if r["top1_match"]),
                "external_top3": sum(1 for r in external_results if r["top3_match"]),
            },
            "results": results
        }, f, indent=2)
    print(f"  Baseline saved to: {out_path}")


if __name__ == "__main__":
    main()
