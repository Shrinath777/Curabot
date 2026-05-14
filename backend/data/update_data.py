import json
import urllib.parse
import os

data_dir = r"C:\projects\tcs project\curabot\backend\data"
json_path = os.path.join(data_dir, "diseases.json")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
        
    for d in diseases:
        disease_name = d.get('name', '')
        # Create a legitimate URL reference using NIH's MedlinePlus or PubMed
        # For a more robust "EOI Reference" (Evidence of Information / Expression of Interest)
        query = urllib.parse.quote_plus(disease_name)
        eoi_url = f"https://medlineplus.gov/search.html?query={query}"
        d['eoi_reference'] = eoi_url
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(diseases, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully added EOI references to {len(diseases)} diseases in diseases.json")
except Exception as e:
    print(f"Error: {e}")
