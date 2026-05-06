import json, os
data = json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "diseases.json"), "r", encoding="utf-8"))
names = [d["name"] for d in data]
name_set = {n.lower() for n in names}
cases = json.load(open(os.path.join(os.path.dirname(__file__), "golden_test_cases.json"), "r", encoding="utf-8"))
for c in cases:
    gt = c["ground_truth"]
    if gt.lower() not in name_set:
        matches = [n for n in names if gt.lower() in n.lower() or n.lower() in gt.lower()]
        print(f"{c['id']}: '{gt}' NOT FOUND. Close: {matches[:3]}")
