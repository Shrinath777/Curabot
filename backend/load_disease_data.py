import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import hashlib
import os
from typing import Dict, Any, Optional, List, Union

def parse_range(value_str) -> Dict[str, Optional[float]]:
    """Parse range strings like '60-100' or '>100' or '<4000'"""
    result: Dict[str, Optional[float]] = {'min': None, 'max': None}
    
    if pd.isna(value_str):
        return result
    
    value_str = str(value_str).strip()
    
    try:
        if '–' in value_str:
            parts = value_str.replace('–', '-').split('-')
            if len(parts) == 2:
                result['min'] = float(parts[0].strip())
                result['max'] = float(parts[1].strip())
        elif '-' in value_str:
            parts = value_str.split('-')
            if len(parts) == 2:
                result['min'] = float(parts[0].strip())
                result['max'] = float(parts[1].strip())
        elif '>' in value_str:
            result['min'] = float(value_str.replace('>', '').strip())
            result['max'] = 999999.0
        elif '<' in value_str:
            result['max'] = float(value_str.replace('<', '').strip())
            result['min'] = 0.0
        elif '/' in value_str:
            # Handle blood pressure like "≥140/90"
            parts = value_str.replace('≥', '').replace('≤', '').split('/')
            if len(parts) == 2:
                result['min'] = float(parts[0].strip())
                result['max'] = float(parts[0].strip())
        else:
            try:
                val = float(value_str)
                result['min'] = val
                result['max'] = val
            except:
                pass
    except Exception as e:
        print(f"Warning: Could not parse value '{value_str}': {e}")
    
    return result

def parse_bp_range(bp_str) -> Dict[str, Optional[float]]:
    """Parse blood pressure like '≥140/90' or '<120/80'"""
    result: Dict[str, Optional[float]] = {
        'systolic_min': None, 'systolic_max': None,
        'diastolic_min': None, 'diastolic_max': None
    }
    
    if pd.isna(bp_str):
        return result
    
    bp_str = str(bp_str).strip()
    
    try:
        if '≥' in bp_str or '>' in bp_str:
            parts = bp_str.replace('≥', '').replace('>', '').split('/')
            if len(parts) == 2:
                result['systolic_min'] = float(parts[0].strip())
                result['diastolic_min'] = float(parts[1].strip())
                result['systolic_max'] = 300.0
                result['diastolic_max'] = 200.0
        elif '≤' in bp_str or '<' in bp_str:
            parts = bp_str.replace('≤', '').replace('<', '').split('/')
            if len(parts) == 2:
                result['systolic_max'] = float(parts[0].strip())
                result['diastolic_max'] = float(parts[1].strip())
                result['systolic_min'] = 0.0
                result['diastolic_min'] = 0.0
        elif '-' in bp_str:
            parts = bp_str.split('-')
            if len(parts) == 2:
                bp_parts = parts[0].split('/')
                if len(bp_parts) == 2:
                    result['systolic_min'] = float(bp_parts[0].strip())
                    result['diastolic_min'] = float(bp_parts[1].strip())
                bp_parts2 = parts[1].split('/')
                if len(bp_parts2) == 2:
                    result['systolic_max'] = float(bp_parts2[0].strip())
                    result['diastolic_max'] = float(bp_parts2[1].strip())
    except Exception as e:
        print(f"Warning: Could not parse BP value '{bp_str}': {e}")
    
    return result

def load_disease_data_to_chromadb():
    """Load disease data from Excel to ChromaDB"""
    
    print("=" * 60)
    print("Loading Disease Dataset into ChromaDB")
    print("=" * 60)
    
    # Read Excel file
    excel_path = os.path.join(os.path.dirname(__file__), "data", "diseases_dataset.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"Excel file not found at: {excel_path}")
        print("Please save your dataset as 'diseases_dataset.xlsx' in the data folder")
        return
    
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} diseases from Excel\n")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create embedding function - ignore type warning with comment
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
    embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=api_key)
    
    # Create or get collection - use type ignore to bypass the warning
    collection = client.get_or_create_collection(
        name="diseases",
        embedding_function=embedding_fn,  # type: ignore
        metadata={"hnsw:space": "cosine"}
    )
    
    # Clear existing data (optional)
    try:
        existing_data = collection.get()
        if existing_data and 'ids' in existing_data and existing_data['ids']:
            collection.delete(ids=existing_data['ids'])
            print("Cleared existing data from collection")
    except Exception as e:
        print(f"Note: Could not clear existing data: {e}")
    
    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []
    
    for idx, row in df.iterrows():
        disease_name = row['Disease']
        
        # Create unique ID
        doc_id = hashlib.md5(f"{disease_name}_{idx}".encode()).hexdigest()
        ids.append(doc_id)
        
        # Create rich document text for embedding
        doc_text = f"""
        DISEASE: {disease_name}
        
        SYMPTOMS: {row['Symptoms']}
        
        VITAL SIGNS:
        - Heart Rate: {row['HR']}
        - Blood Pressure: {row['BP']}
        - Oxygen Saturation: {row['SpO₂']}
        
        LABORATORY FINDINGS:
        - WBC Count: {row['WBC']}
        - RBC Count: {row['RBC']}
        - Platelets: {row['Platelets']}
        
        RECOMMENDED TESTS: {row['Lab Tests']}
        
        This disease presents with these characteristic symptoms and vital sign patterns.
        """
        documents.append(doc_text)
        
        # Parse vital ranges for metadata
        hr_range = parse_range(row['HR'])
        bp_range = parse_bp_range(row['BP'])
        spo2_range = parse_range(row['SpO₂'])
        wbc_range = parse_range(row['WBC'])
        rbc_range = parse_range(row['RBC'])
        platelets_range = parse_range(row['Platelets'])
        
        # Store metadata
        metadata_dict_raw = {
            'name': str(disease_name),
            'symptoms': str(row['Symptoms']),
            'hr_min': hr_range['min'],
            'hr_max': hr_range['max'],
            'bp_systolic_min': bp_range['systolic_min'],
            'bp_systolic_max': bp_range['systolic_max'],
            'bp_diastolic_min': bp_range['diastolic_min'],
            'bp_diastolic_max': bp_range['diastolic_max'],
            'spo2_min': spo2_range['min'],
            'spo2_max': spo2_range['max'],
            'wbc_min': wbc_range['min'],
            'wbc_max': wbc_range['max'],
            'rbc_min': rbc_range['min'],
            'rbc_max': rbc_range['max'],
            'platelets_min': platelets_range['min'],
            'platelets_max': platelets_range['max'],
            'lab_tests': str(row['Lab Tests'])
        }
        metadata_dict = {k: str(v) for k, v in metadata_dict_raw.items() if str(v) not in ('nan', 'None', '', '<NA>')}
        metadatas.append(metadata_dict)
        
        print(f"  Added: {disease_name}")
    
    # Add to ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"\nSuccessfully loaded {len(ids)} diseases into ChromaDB!")
    print(f"Database location: ./chroma_db")
    print("=" * 60)
    
    # Show sample of loaded data with proper type checking
    print("\nSample of loaded diseases:")
    try:
        result = collection.get(limit=3)
        
        # Safely check and display results
        if result and isinstance(result, dict):
            metadatas_list = result.get('metadatas', [])
            if metadatas_list and isinstance(metadatas_list, list):
                for i, metadata in enumerate(metadatas_list):
                    if metadata and isinstance(metadata, dict):
                        name = metadata.get('name', 'Unknown')
                        symptoms = metadata.get('symptoms', '')
                        symptoms_str = str(symptoms)
                        symptoms_preview = symptoms_str[:50] + '...' if len(symptoms_str) > 50 else symptoms_str
                        print(f"  {i+1}. {name}")
                        print(f"     Symptoms: {symptoms_preview}")
                    else:
                        print(f"  {i+1}. [Invalid metadata format]")
            else:
                print("  No metadata found in results")
        else:
            print("  No diseases found in database")
    except Exception as e:
        print(f"  Error displaying sample: {e}")

if __name__ == "__main__":
    load_disease_data_to_chromadb()