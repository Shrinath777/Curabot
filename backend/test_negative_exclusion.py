import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer
from agents.evidence_evaluator import evidence_evaluator

async def main():
    message = "I have severe stomach pain, but I don't have diarrhea and no fever."
    print(f"PATIENT MESSAGE: '{message}'\n")

    print("--- 1. Agent 1: Symptom Normalization ---")
    normalized = await symptom_normalizer.process(message=message)
    print(f"Primary Symptoms: {', '.join(s['name'] for s in normalized.get('primary_symptoms', []))}")
    print(f"Absent Symptoms (Negative Exclusion): {', '.join(normalized.get('absent_symptoms', []))}")

    print("\n--- 2. Agent 3: Evidence Evaluator (Fallback mode) ---")
    # Provide dummy hypotheses
    hypotheses = [
        {"name": "Gastroenteritis", "confidence": 40},
        {"name": "Peptic Ulcer Disease", "confidence": 30}
    ]
    # We force the fallback evidence evaluator directly to test the negative exclusion logic
    # First we need to build the evidence list like Agent 3 does in `process()`
    all_evidence = []
    for s in normalized.get("primary_symptoms", []):
        all_evidence.append({
            "type": "symptom", "finding": s.get("name", ""), "detail": ""
        })
    for s in normalized.get("absent_symptoms", []):
        all_evidence.append({
            "type": "explicitly_absent_symptom", "finding": s, "detail": "Explicitly denied"
        })

    evidence = evidence_evaluator._fallback_evidence(hypotheses, all_evidence)
    for ledger in evidence.get("evidence_ledger", []):
        if ledger.get("contradicts"):
            for c in ledger.get("contradicts"):
                print(f"❌ CONTRADICTS: {c['hypothesis']} (Strength: {c['strength']}) -> {c['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
