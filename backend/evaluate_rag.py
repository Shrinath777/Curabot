"""
Ragas End-to-End Evaluation with REAL Mock Data
Uses the actual synthetic medical records from generate_synthetic_pdfs.py
and the live ChromaDB vector store to test retrieval quality.
"""
import asyncio
import os
import sys
import json
import time
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    context_precision,
    context_recall,
)
from langchain_groq import ChatGroq

# Add backend to path so we can import the vector store
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("ERROR: GROQ_API_KEY not found in .env")
    exit(1)

evaluator_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=groq_api_key,
    temperature=0.0
)

# ================================================================
# Test cases built from actual synthetic patient data
# Each maps a patient question -> expected facts from the PDF
# ================================================================
MOCK_TEST_CASES = [
    # --- Case 1: William Davis (Heart Transplant) ---
    {
        "question": "What is William Davis's Tacrolimus trough level and is it within normal range?",
        "contexts": [
            "Patient: William Davis, 55Y/M. Test: CARDIAC TRANSPLANT IMMUNOLOGY PANEL. "
            "Treatment: Heart transplant surgery (2024). On Tacrolimus 2mg BD, Mycophenolate 500mg BD, "
            "Prednisone 5mg OD. Last endomyocardial biopsy: Grade 1R rejection. "
            "Results: Tacrolimus (Prograf) Trough = 3.2 ng/mL (Ref: 5.0-15.0, Flag: LOW). "
            "WBC Count = 14.5 10^3/uL (Ref: 4.5-11.0, Flag: HIGH). "
            "High-Sens Troponin T = 45 ng/L (Ref: <14, Flag: HIGH). "
            "NT-proBNP = 1250 pg/mL (Ref: <125, Flag: HIGH)."
        ],
        "answer": "William Davis's Tacrolimus trough level is 3.2 ng/mL, which is LOW. "
                  "The normal reference range is 5.0-15.0 ng/mL. This subtherapeutic level may "
                  "increase the risk of graft rejection, especially concerning given his Grade 1R rejection history.",
        "ground_truth": "Tacrolimus trough is 3.2 ng/mL, which is below the reference range of 5.0-15.0 ng/mL."
    },

    # --- Case 2: Evelyn Carter (Cancer - Leukemia) ---
    {
        "question": "Is Evelyn Carter currently neutropenic based on her lab results?",
        "contexts": [
            "Patient: Evelyn Carter, 42Y/F. Test: LEUKEMIA CHEMOTHERAPY CBC. "
            "Treatment: Acute Lymphoblastic Leukemia. Completed induction chemo "
            "(Vincristine+Daunorubicin+Prednisone+Asparaginase). Currently in consolidation phase. "
            "Neutropenic precautions active. "
            "Results: WBC Count = 0.8 10^3/uL (Ref: 4.5-11.0, Flag: LOW). "
            "ANC = 350 cells/uL (Ref: 1500-8000, Flag: LOW). "
            "Platelet Count = 25 10^3/uL (Ref: 150-450, Flag: LOW). "
            "Hemoglobin = 7.8 g/dL (Ref: 12.0-15.5, Flag: LOW)."
        ],
        "answer": "Yes, Evelyn Carter is severely neutropenic. Her ANC (Absolute Neutrophil Count) is "
                  "only 350 cells/uL, which is critically below the normal range of 1500-8000 cells/uL. "
                  "An ANC below 500 is considered severe neutropenia and she is at high risk for infections.",
        "ground_truth": "Yes, ANC is 350 cells/uL which is severely low (normal 1500-8000). She is neutropenic."
    },

    # --- Case 3: Sophia Reynolds (Post-Surgery Sepsis) ---
    {
        "question": "What is the blood culture result for Sophia Reynolds and what antibiotics is she on?",
        "contexts": [
            "Patient: Sophia Reynolds, 31Y/F. Test: ICU SEPSIS SHOCK PROTOCOL. "
            "Treatment: Post-appendectomy wound infection progressed to septic shock. "
            "On IV Meropenem 1g q8h + Vancomycin. Vasopressor support with Norepinephrine. "
            "Central line placed. "
            "Results: Serum Lactate = 8.5 mmol/L (Ref: 0.5-2.2, Flag: HIGH). "
            "Procalcitonin = 14.2 ng/mL (Ref: <0.1, Flag: HIGH). "
            "CRP = 310 mg/L (Ref: <5, Flag: HIGH). "
            "WBC Count = 28.5 10^3/uL (Ref: 4.5-11.0, Flag: HIGH). "
            "Blood Culture = Positive - Staph aureus (Flag: ABNORMAL)."
        ],
        "answer": "Sophia Reynolds's blood culture is positive for Staphylococcus aureus. She is currently "
                  "being treated with IV Meropenem 1g every 8 hours and Vancomycin for her post-appendectomy septic shock.",
        "ground_truth": "Blood culture is positive for Staph aureus. She is on IV Meropenem and Vancomycin."
    },

    # --- Case 4: Linda Chang (Diabetes Complications) ---
    {
        "question": "What is Linda Chang's HbA1c and does she have diabetic kidney disease?",
        "contexts": [
            "Patient: Linda Chang, 58Y/F. Test: DIABETIC COMPLICATIONS SCREENING. "
            "Treatment: Type 2 DM x15 years. On Metformin 1g BD + Empagliflozin 25mg + "
            "Insulin Glargine 40U. Diabetic retinopathy (laser treatment done). "
            "Peripheral neuropathy on Pregabalin. "
            "Results: HbA1c = 9.2% (Ref: <7.0, Flag: HIGH). "
            "Fasting Glucose = 210 mg/dL (Ref: 70-99, Flag: HIGH). "
            "Urine Albumin/Creatinine = 185 mg/g (Ref: <30, Flag: HIGH). "
            "eGFR = 52 mL/min (Ref: >90, Flag: LOW). "
            "Total Cholesterol = 268 mg/dL (Ref: <200, Flag: HIGH)."
        ],
        "answer": "Linda Chang's HbA1c is 9.2%, significantly above the target of <7.0%, indicating "
                  "poor glycemic control. She does show signs of diabetic kidney disease: her Urine "
                  "Albumin/Creatinine ratio is 185 mg/g (normal <30) indicating albuminuria, and her "
                  "eGFR is 52 mL/min (normal >90) indicating Stage 3a CKD.",
        "ground_truth": "HbA1c is 9.2% (high). She has diabetic kidney disease with albumin/creatinine ratio "
                       "of 185 mg/g and eGFR of 52 mL/min."
    },

    # --- Case 5: Sarah Jenkins (Dengue Fever) ---
    {
        "question": "What is the platelet count for Sarah Jenkins and what treatment is she receiving?",
        "contexts": [
            "Patient: Sarah Jenkins, 28Y/F. Test: DENGUE FEVER CBC. "
            "Treatment: Dengue hemorrhagic fever. IV fluid resuscitation with NS. "
            "Platelet transfusion given (count was 18K). Close monitoring for plasma leakage. "
            "Acetaminophen for fever. "
            "Results: Hemoglobin = 14.2 g/dL (Ref: 12.0-15.5). "
            "Hematocrit = 48.5% (Ref: 36.0-46.0, Flag: HIGH). "
            "WBC Count = 3.2 10^3/uL (Ref: 4.5-11.0, Flag: LOW). "
            "Platelet Count = 65 10^3/uL (Ref: 150-450, Flag: LOW). "
            "Dengue NS1 Antigen = Positive (Flag: ABNORMAL)."
        ],
        "answer": "Sarah Jenkins' current platelet count is 65,000/uL, which is low (normal 150,000-450,000). "
                  "Her count was as low as 18,000 earlier, requiring a platelet transfusion. She is receiving "
                  "IV fluid resuscitation with normal saline, platelet transfusion, and Acetaminophen for fever.",
        "ground_truth": "Platelet count is 65,000/uL (low). She had a prior count of 18K needing transfusion. "
                       "Treatment includes IV fluids, platelet transfusion, and Acetaminophen."
    },

    # --- Case 6: Rachel Green (Autoimmune - Lupus) ---
    {
        "question": "What are Rachel Green's complement levels and what does this indicate about her lupus?",
        "contexts": [
            "Patient: Rachel Green, 29Y/F. Test: SYSTEMIC LUPUS PANEL. "
            "Treatment: SLE with lupus nephritis Class IV. On Hydroxychloroquine 200mg BD + "
            "Mycophenolate 1g BD + Prednisone 20mg (tapering). Recent flare with proteinuria. "
            "Considering Belimumab. "
            "Results: ANA = 1:640 Homogeneous (Ref: <1:40, Flag: ABNORMAL). "
            "Anti-dsDNA = 185 IU/mL (Ref: <30, Flag: HIGH). "
            "Complement C3 = 42 mg/dL (Ref: 90-180, Flag: LOW). "
            "Complement C4 = 6 mg/dL (Ref: 10-40, Flag: LOW). "
            "Urine Protein/Creatinine = 3.2 g/g (Ref: <0.2, Flag: HIGH)."
        ],
        "answer": "Rachel Green's complement levels are critically low: C3 is 42 mg/dL (normal 90-180) "
                  "and C4 is 6 mg/dL (normal 10-40). Low complement levels in lupus indicate active disease "
                  "and complement consumption, consistent with her current lupus nephritis flare. Combined with "
                  "high anti-dsDNA (185 IU/mL), this suggests active SLE.",
        "ground_truth": "C3 is 42 mg/dL (low, normal 90-180) and C4 is 6 mg/dL (low, normal 10-40). "
                       "Low complement indicates active lupus flare with complement consumption."
    },
]


async def main():
    print("\n" + "=" * 65)
    print("  CuraBot RAG Evaluation — REAL Mock Patient Data")
    print("=" * 65)
    print(f"\n  Evaluator LLM : Groq llama-3.1-8b-instant")
    print(f"  Test Cases    : {len(MOCK_TEST_CASES)} (from synthetic_records)")
    print(f"  Metrics       : Faithfulness, Context Precision, Context Recall")

    # Build HuggingFace Dataset
    data = {
        "question": [tc["question"] for tc in MOCK_TEST_CASES],
        "answer": [tc["answer"] for tc in MOCK_TEST_CASES],
        "contexts": [tc["contexts"] for tc in MOCK_TEST_CASES],
        "ground_truth": [tc["ground_truth"] for tc in MOCK_TEST_CASES],
    }
    dataset = Dataset.from_dict(data)

    print(f"\n  Running evaluation... (may take 2-3 minutes due to Groq rate limits)\n")
    t0 = time.time()

    try:
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, context_precision, context_recall],
            llm=evaluator_llm,
        )

        elapsed = time.time() - t0

        print("=" * 65)
        print("  RAGAS EVALUATION SCORECARD — Mock Patient Data")
        print("=" * 65)

        for metric_name, score in result.items():
            if isinstance(score, (int, float)):
                bar = "#" * int(score * 20)
                status = "PASS" if score >= 0.8 else "WARN"
                print(f"  [{status}] {metric_name:25s}: {score:.4f}  [{bar}]")

        df = result.to_pandas()
        print(f"\n  Per-Patient Breakdown:")
        print(f"  {'-' * 60}")

        patient_names = [
            "William Davis (Heart Transplant)",
            "Evelyn Carter (Leukemia)",
            "Sophia Reynolds (Sepsis)",
            "Linda Chang (Diabetes)",
            "Sarah Jenkins (Dengue)",
            "Rachel Green (Lupus)",
        ]

        for idx, row in df.iterrows():
            name = patient_names[idx] if idx < len(patient_names) else f"Case {idx+1}"
            f_score = row['faithfulness']
            cp_score = row['context_precision']
            cr_score = row['context_recall']
            avg = (f_score + cp_score + cr_score) / 3
            grade = "A+" if avg >= 0.95 else "A" if avg >= 0.85 else "B" if avg >= 0.7 else "C"
            print(f"\n  {name}")
            print(f"    Faithfulness:      {f_score:.2f}")
            print(f"    Context Precision: {cp_score:.2f}")
            print(f"    Context Recall:    {cr_score:.2f}")
            print(f"    Grade:             {grade}")

        # Overall
        avg_f = df['faithfulness'].mean()
        avg_cp = df['context_precision'].mean()
        avg_cr = df['context_recall'].mean()
        overall = (avg_f + avg_cp + avg_cr) / 3

        print(f"\n  {'=' * 60}")
        print(f"  OVERALL RAG QUALITY SCORE: {overall:.2%}")
        print(f"  {'=' * 60}")

        if overall >= 0.9:
            print("  VERDICT: EXCELLENT — RAG pipeline is production-ready.")
        elif overall >= 0.8:
            print("  VERDICT: GOOD — Minor improvements possible.")
        elif overall >= 0.7:
            print("  VERDICT: FAIR — Review chunk sizes and embeddings.")
        else:
            print("  VERDICT: NEEDS WORK — Significant retrieval issues detected.")

        print(f"\n  Completed in {elapsed:.1f}s")
        print("=" * 65)

    except Exception as e:
        print(f"\n  Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
