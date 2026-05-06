"""
CuraBot — Confusion Matrix & Per-Disease Precision/Recall Generator

Reads golden_test_baseline.json and produces:
  1. Confusion matrix showing which diseases get confused with which
  2. Per-disease Precision and Recall
  3. System-level accuracy breakdown
  4. 95% confidence intervals for accuracy

Usage:
  python -m evaluation.generate_confusion_matrix
"""

import json
import os
import math
from collections import defaultdict
from datetime import datetime

def load_results(filepath: str) -> dict:
    """Load test results JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple:
    """Wilson score confidence interval for binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (round(lower * 100, 1), round(upper * 100, 1))


def generate_confusion_data(results: list) -> dict:
    """Generate confusion matrix data from test results."""
    # Track: for each ground_truth, what was predicted
    gt_to_predicted = defaultdict(list)
    pred_to_gt = defaultdict(list)
    
    for r in results:
        gt = r["ground_truth"]
        pred = r.get("predicted_top1", "")
        gt_to_predicted[gt].append(pred)
        pred_to_gt[pred].append(gt)
    
    # Confusion pairs: which diseases get confused with which
    confusion_pairs = []
    for gt, predictions in gt_to_predicted.items():
        for pred in predictions:
            if pred and pred.lower() != gt.lower():
                confusion_pairs.append({
                    "actual": gt,
                    "predicted": pred,
                    "case_id": next(
                        (r["case_id"] for r in results 
                         if r["ground_truth"] == gt and r.get("predicted_top1") == pred),
                        "unknown"
                    )
                })
    
    return {
        "gt_to_predicted": dict(gt_to_predicted),
        "pred_to_gt": dict(pred_to_gt),
        "confusion_pairs": confusion_pairs,
    }


def compute_per_disease_metrics(results: list) -> list:
    """Compute Precision and Recall per disease."""
    # Precision: Of all times we predicted X, how often was it actually X?
    # Recall: Of all actual X cases, how often did we predict X?
    
    disease_metrics = {}
    
    all_gt = [r["ground_truth"] for r in results]
    all_pred = [r.get("predicted_top1", "") for r in results]
    
    # Unique diseases from ground truth
    unique_diseases = sorted(set(all_gt))
    
    for disease in unique_diseases:
        # True Positives: predicted disease AND it was actually disease
        tp = sum(1 for gt, pred in zip(all_gt, all_pred) 
                 if gt.lower() == disease.lower() and _fuzzy_eq(pred, gt))
        
        # False Positives: predicted disease BUT it was actually something else
        fp = sum(1 for gt, pred in zip(all_gt, all_pred)
                 if _fuzzy_eq(pred, disease) and not _fuzzy_eq(gt, disease))
        
        # False Negatives: actually disease BUT predicted something else
        fn = sum(1 for gt, pred in zip(all_gt, all_pred)
                 if _fuzzy_eq(gt, disease) and not _fuzzy_eq(pred, gt))
        
        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Find actual prediction for this disease
        actual_pred = next((r.get("predicted_top1", "?") for r in results 
                           if r["ground_truth"].lower() == disease.lower()), "?")
        
        disease_metrics[disease] = {
            "disease": disease,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 1),
            "recall": round(recall, 1),
            "f1": round(f1, 1),
            "status": "CORRECT" if tp > 0 else "MISSED",
            "actual_prediction": actual_pred,
        }
    
    return sorted(disease_metrics.values(), key=lambda x: x["f1"], reverse=True)


def _fuzzy_eq(a: str, b: str) -> bool:
    """Fuzzy equality check for disease names."""
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()
    if a_lower == b_lower:
        return True
    if a_lower in b_lower or b_lower in a_lower:
        return True
    # Common aliases
    ALIASES = {
        "copd": "chronic obstructive pulmonary disease",
        "meningitis": "bacterial meningitis",
        "depression": "major depressive disorder",
        "hepatitis b": "hepatitis",
        "anaphylaxis": "anaphylactic shock",
        "celiac disease": "celiac",
        "acute pancreatitis": "pancreatitis",
        "gastroenteritis": "acute gastroenteritis",
        "eczema": "atopic dermatitis",
        "anxiety disorder": "generalized anxiety disorder",
        "iron deficiency anemia": "anemia",
    }
    for alias_key, alias_val in ALIASES.items():
        if (a_lower == alias_key and (alias_val in b_lower or b_lower in alias_val)):
            return True
        if (b_lower == alias_key and (alias_val in a_lower or a_lower in alias_val)):
            return True
    return False


def compute_system_accuracy(results: list) -> dict:
    """Accuracy breakdown by body system."""
    system_groups = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})
    
    for r in results:
        system = r.get("system", r.get("severity", "unknown"))
        system_groups[system]["total"] += 1
        if r.get("top1_match"):
            system_groups[system]["top1"] += 1
        if r.get("top3_match"):
            system_groups[system]["top3"] += 1
    
    result = {}
    for system, counts in sorted(system_groups.items()):
        total = counts["total"]
        result[system] = {
            "total": total,
            "top1_accuracy": round(counts["top1"] / total * 100, 1) if total > 0 else 0,
            "top3_accuracy": round(counts["top3"] / total * 100, 1) if total > 0 else 0,
            "top1_ci": wilson_ci(counts["top1"], total),
            "top3_ci": wilson_ci(counts["top3"], total),
        }
    
    return result


def print_report(results: list):
    """Print comprehensive analysis report."""
    total = len(results)
    t1 = sum(1 for r in results if r.get("top1_match"))
    t3 = sum(1 for r in results if r.get("top3_match"))
    t5 = sum(1 for r in results if r.get("top5_match"))
    
    t1_ci = wilson_ci(t1, total)
    t3_ci = wilson_ci(t3, total)
    
    print("\n" + "=" * 75)
    print("   CURABOT - COMPREHENSIVE DIAGNOSTIC ACCURACY ANALYSIS")
    print("=" * 75)
    
    print(f"\n  Total Cases: {total}")
    print(f"  Top-1 Accuracy: {t1/total*100:.1f}%  ({t1}/{total})  95% CI: [{t1_ci[0]}%, {t1_ci[1]}%]")
    print(f"  Top-3 Accuracy: {t3/total*100:.1f}%  ({t3}/{total})  95% CI: [{t3_ci[0]}%, {t3_ci[1]}%]")
    print(f"  Top-5 Accuracy: {t5/total*100:.1f}%  ({t5}/{total})")
    
    # Confusion matrix
    confusion = generate_confusion_data(results)
    print(f"\n  --- CONFUSION MATRIX (Misclassified Cases) ---")
    print(f"  {'Actual Disease':40s} -> {'Predicted As':40s}")
    print(f"  {'-'*85}")
    for pair in confusion["confusion_pairs"]:
        print(f"  {pair['actual']:40s} -> {pair['predicted']:40s}  [{pair['case_id']}]")
    
    # Most common false predictions (diseases that appear as wrong predictions)
    false_pred_count = defaultdict(int)
    for pair in confusion["confusion_pairs"]:
        false_pred_count[pair["predicted"]] += 1
    
    if false_pred_count:
        print(f"\n  --- MOST OVER-PREDICTED DISEASES (False Positives) ---")
        for pred, count in sorted(false_pred_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {pred:45s}  wrongly predicted {count} time(s)")
    
    # Per-disease precision/recall
    disease_metrics = compute_per_disease_metrics(results)
    print(f"\n  --- PER-DISEASE PRECISION / RECALL ---")
    print(f"  {'Disease':40s} {'Prec':>6s} {'Recall':>7s} {'F1':>6s}  {'Status':>8s}  {'Predicted As'}")
    print(f"  {'-'*110}")
    for dm in disease_metrics:
        pred_str = "" if dm["status"] == "CORRECT" else dm["actual_prediction"]
        print(f"  {dm['disease']:40s} {dm['precision']:5.1f}% {dm['recall']:6.1f}% {dm['f1']:5.1f}%  {dm['status']:>8s}  {pred_str}")
    
    # Summary stats
    correct_diseases = [d for d in disease_metrics if d["status"] == "CORRECT"]
    missed_diseases = [d for d in disease_metrics if d["status"] == "MISSED"]
    avg_precision = sum(d["precision"] for d in disease_metrics) / len(disease_metrics) if disease_metrics else 0
    avg_recall = sum(d["recall"] for d in disease_metrics) / len(disease_metrics) if disease_metrics else 0
    
    print(f"\n  Diseases correctly identified (Top-1): {len(correct_diseases)}/{len(disease_metrics)}")
    print(f"  Macro-Average Precision: {avg_precision:.1f}%")
    print(f"  Macro-Average Recall:    {avg_recall:.1f}%")
    
    # System accuracy
    system_acc = compute_system_accuracy(results)
    if system_acc:
        print(f"\n  --- ACCURACY BY BODY SYSTEM ---")
        for sys_name, metrics in system_acc.items():
            print(f"    {sys_name:30s}  T1: {metrics['top1_accuracy']:5.1f}%  T3: {metrics['top3_accuracy']:5.1f}%  ({metrics['total']} cases)")
    
    print("\n" + "=" * 75)
    
    # Save JSON report
    report = {
        "generated": datetime.utcnow().isoformat(),
        "total_cases": total,
        "top1_accuracy": round(t1/total*100, 1),
        "top3_accuracy": round(t3/total*100, 1),
        "top1_ci_95": t1_ci,
        "top3_ci_95": t3_ci,
        "confusion_pairs": confusion["confusion_pairs"],
        "per_disease_metrics": disease_metrics,
        "system_accuracy": system_acc,
        "over_predicted": dict(false_pred_count),
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "confusion_matrix_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Report saved to: {out_path}")


def main():
    eval_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try baseline results first, then golden test results
    baseline_path = os.path.join(eval_dir, "golden_test_baseline.json")
    golden_path = os.path.join(eval_dir, "golden_test_results.json")
    
    if os.path.exists(baseline_path):
        data = load_results(baseline_path)
        results = data.get("results", data.get("individual_results", []))
        print(f"  Loaded {len(results)} results from baseline")
    elif os.path.exists(golden_path):
        data = load_results(golden_path)
        results = data.get("individual_results", data.get("results", []))
        print(f"  Loaded {len(results)} results from golden tests")
    else:
        print("  ERROR: No results file found. Run baseline tests first.")
        return
    
    print_report(results)


if __name__ == "__main__":
    main()
