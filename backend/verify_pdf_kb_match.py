"""Verify every synthetic PDF folder has matching diseases in the KB."""
import json, os

KB_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")
PDF_DIR = os.path.join(os.path.dirname(__file__), "synthetic_records")

with open(KB_PATH, "r") as f:
    kb = json.load(f)
kb_names = [d["name"].lower() for d in kb]

folder_to_kb = {
    "Heart_Transplant": ["Heart Transplant Rejection"],
    "Cancer_Treatment": ["Acute Lymphoblastic Leukemia", "Breast Cancer", "Lung Cancer", "Cervical Cancer", "Prostate Cancer"],
    "Chronic_Kidney_Failure": ["Chronic Kidney Disease"],
    "Post_Surgery_Sepsis": ["Septicemia"],
    "Severe_COPD": ["Chronic Obstructive Pulmonary Disease"],
    "Liver_Cirrhosis": ["Liver Cirrhosis", "Hepatocellular Carcinoma"],
    "Diabetes": ["Diabetic Ketoacidosis", "Type 2 Diabetes Mellitus", "Gestational Diabetes"],
    "Cardiac_Emergency": ["Acute Myocardial Infarction", "Heart Failure", "Pulmonary Embolism", "Aortic Dissection"],
    "Neurological": ["Bacterial Meningitis", "Ischemic Stroke", "Epilepsy"],
    "Thyroid_Disorders": ["Hyperthyroidism", "Hypothyroidism", "Thyroid Cancer"],
    "Infectious_Disease": ["Dengue Fever", "Malaria", "Tuberculosis", "HIV/AIDS"],
    "Autoimmune": ["Systemic Lupus Erythematosus", "Rheumatoid Arthritis", "Crohn's Disease"],
    "Respiratory": ["Community Acquired Pneumonia", "Asthma", "COVID-19"],
    "Blood_Disorders": ["Anemia", "Sickle Cell Disease", "Disseminated Intravascular Coagulation"],
    "Healthy_Baseline": [],
}

print("=" * 65)
print("  FINAL VERIFICATION: All PDF folders vs KB")
print("=" * 65)
all_ok = True
for folder, expected in folder_to_kb.items():
    folder_path = os.path.join(PDF_DIR, folder)
    pdf_count = len([f for f in os.listdir(folder_path) if f.endswith(".pdf")]) if os.path.exists(folder_path) else 0
    missing = [d for d in expected if d.lower() not in kb_names]
    status = "PASS" if not missing else "FAIL"
    if missing:
        all_ok = False
    print(f"  [{status}] {folder}/ ({pdf_count} PDFs) => {len(expected)} KB entries")
    if missing:
        for m in missing:
            print(f"        MISSING: {m}")

print("=" * 65)
if all_ok:
    print("  ALL PASSED! Every PDF disease has a matching KB entry.")
else:
    print("  SOME FAILURES! See above.")
print("=" * 65)

# Also verify each new disease has required fields
print("\n  Checking new diseases have all required fields...")
required_fields = ["name", "symptoms", "lab_tests", "key_diagnostic_questions", "risk_factors", "red_flags"]
for d in kb:
    missing_fields = [f for f in required_fields if f not in d or not d[f]]
    if missing_fields:
        print(f"  [WARN] {d['name']} missing: {missing_fields}")

print("\n  KB integrity check complete!")
print(f"  Total diseases in KB: {len(kb)}")
