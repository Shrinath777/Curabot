"""Run _fallback_hypotheses and trace Bell's Palsy."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.symptom_normalizer import symptom_normalizer
from agents.hypothesis_generator import hypothesis_generator

msg = "I woke up this morning and one side of my face is completely drooping. I can't close my right eye or smile on that side. I can't taste food properly. My ear was hurting yesterday. I have no arm or leg weakness."
normalized = symptom_normalizer._keyword_fallback(msg)

result = hypothesis_generator._fallback_hypotheses(normalized)
hypotheses = result.get("hypotheses", [])

print(f"Total hypotheses generated: {len(hypotheses)}")
print(f"\nTop 10:")
for i, h in enumerate(hypotheses[:10]):
    print(f"  {i+1}. {h['name']} ({h['confidence']}%) — matches={h.get('supporting',0)}, contra={h.get('contradicting',0)}")

# Find Bell's Palsy
bp_found = None
for i, h in enumerate(hypotheses):
    if "bell" in h["name"].lower():
        bp_found = (i+1, h)
        break

if bp_found:
    rank, h = bp_found
    print(f"\nBell's Palsy found at rank #{rank}: {h}")
else:
    print(f"\nBell's Palsy NOT in hypotheses list at all! Checking all {len(hypotheses)} entries...")
    # Check all names
    all_names = [h["name"] for h in hypotheses]
    facial_related = [n for n in all_names if "facial" in n.lower() or "bell" in n.lower() or "palsy" in n.lower()]
    print(f"Facial-related diseases found: {facial_related}")
