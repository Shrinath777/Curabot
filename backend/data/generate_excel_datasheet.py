import os
import json
import pandas as pd

def generate_excel():
    data_dir = os.path.dirname(__file__)
    json_path = os.path.join(data_dir, "diseases.json")
    excel_path = os.path.join(data_dir, "diseases_datasheet.xlsx")
    
    if not os.path.exists(json_path):
        print(f"Error: Could not find {json_path}")
        return
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
            
        # Process data
        processed_data = []
        for d in diseases:
            row = {
                "Disease Name": d.get("name", ""),
                "ICD-10 Code": d.get("icd10", ""),
                "System": d.get("system", ""),
                "Acuity": d.get("acuity", ""),
                "Prevalence": d.get("prevalence", ""),
                "Severity Class": d.get("severity_class", ""),
                "Description": d.get("description", ""),
                "Symptoms": ", ".join(d.get("symptoms", [])),
                "Vital Sign Patterns": str(d.get("vital_sign_patterns", {})),
                "Lab Tests": ", ".join(d.get("lab_tests", [])),
                "Risk Factors": ", ".join(d.get("risk_factors", [])),
                "Red Flags": ", ".join(d.get("red_flags", [])),
                "Key Diagnostic Questions": " | ".join(d.get("key_diagnostic_questions", [])),
                "Differentiating Features": " | ".join(d.get("differentiating_features", [])),
                "References & Citations": ", ".join(d.get("references", []))
            }
            processed_data.append(row)
            
        df = pd.DataFrame(processed_data)
        df.to_excel(excel_path, index=False)
        print(f"Successfully generated {excel_path} with {len(processed_data)} diseases.")
    except Exception as e:
        print(f"Error processing diseases.json: {e}")

if __name__ == "__main__":
    generate_excel()
