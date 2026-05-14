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
        # Fix the broken MedlinePlus URL with the correct working search endpoint
        query = urllib.parse.quote_plus(disease_name)
        # Correct official MedlinePlus search URL
        eoi_url = f"https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta?v%3Aproject=medlineplus&v%3Asources=medlineplus-bundle&query={query}"
        d['eoi_reference'] = eoi_url
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(diseases, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully fixed EOI references for {len(diseases)} diseases in diseases.json")
except Exception as e:
    print(f"Error: {e}")
