import json
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import hashlib
import numpy as np

class DiseaseKnowledgeBase:
    """Vector database for disease information"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create or get collection - ignore type warning
        self.collection = self.client.get_or_create_collection(
            name="diseases",
            embedding_function=self.embedding_fn,  # type: ignore
            metadata={"hnsw:space": "cosine"}
        )
        
        # Symptom-disease mapping for rule-based matching
        self.symptom_disease_map = {
            'chest_pain': {
                'supports': ['Acute Myocardial Infarction', 'Pulmonary Embolism', 
                            'Gastroesophageal Reflux Disease', 'Aortic Stenosis',
                            'Pericarditis', 'Costochondritis'],
                'contradicts': ['Community Acquired Pneumonia', 'Bronchitis']
            },
            'dyspnea': {
                'supports': ['Community Acquired Pneumonia', 'Pulmonary Embolism',
                            'Acute Myocardial Infarction', 'Aortic Stenosis',
                            'Heart Failure', 'COPD'],
                'contradicts': ['Gastroesophageal Reflux Disease']
            },
            'fever': {
                'supports': ['Community Acquired Pneumonia', 'Influenza',
                            'COVID-19', 'Sepsis', 'Meningitis'],
                'contradicts': ['Gastroesophageal Reflux Disease', 'Aortic Stenosis']
            },
            'cough': {
                'supports': ['Community Acquired Pneumonia', 'Gastroesophageal Reflux Disease',
                            'Bronchitis', 'COVID-19', 'Asthma'],
                'contradicts': ['Acute Myocardial Infarction', 'Aortic Stenosis']
            },
            'fatigue': {
                'supports': ['Acute Myocardial Infarction', 'Community Acquired Pneumonia',
                            'Anemia', 'Hypothyroidism', 'Depression'],
                'contradicts': []
            },
            'nausea': {
                'supports': ['Acute Myocardial Infarction', 'Gastroenteritis',
                            'Pancreatitis', 'Migraine'],
                'contradicts': ['Aortic Stenosis']
            },
            'diaphoresis': {
                'supports': ['Acute Myocardial Infarction', 'Hypoglycemia',
                            'Hyperthyroidism', 'Sepsis'],
                'contradicts': ['Gastroesophageal Reflux Disease']
            },
            'heartburn': {
                'supports': ['Gastroesophageal Reflux Disease', 'Hiatal Hernia',
                            'Esophagitis'],
                'contradicts': ['Community Acquired Pneumonia']
            },
            'hemoptysis': {
                'supports': ['Pulmonary Embolism', 'Tuberculosis',
                            'Lung Cancer', 'Bronchiectasis'],
                'contradicts': ['Gastroesophageal Reflux Disease']
            },
            'syncope': {
                'supports': ['Aortic Stenosis', 'Pulmonary Embolism',
                            'Arrhythmia', 'Vasovagal Syncope'],
                'contradicts': ['Gastroesophageal Reflux Disease']
            }
        }
    
    def load_diseases(self, diseases_file: str) -> None:
        """Load diseases from JSON file into vector store"""
        with open(diseases_file, 'r') as f:
            diseases = json.load(f)
        
        ids = []
        documents = []
        metadatas = []
        
        for disease in diseases:
            # Create unique ID
            doc_id = hashlib.md5(disease['name'].encode()).hexdigest()
            ids.append(doc_id)
            
            # Create rich document text for embedding
            doc_text = f"""
            Disease: {disease['name']}
            ICD-10: {disease.get('icd10', 'Unknown')}
            System: {disease.get('system', 'Unknown')}
            Typical Symptoms: {', '.join(disease['symptoms'])}
            Risk Factors: {', '.join(disease.get('risk_factors', []))}
            Typical Findings: {disease.get('typical_findings', '')}
            Epidemiology: {disease.get('epidemiology', '')}
            """
            documents.append(doc_text)
            
            # Store metadata
            metadatas.append({
                'name': disease['name'],
                'icd10': disease.get('icd10', ''),
                'system': disease.get('system', ''),
                'prevalence': disease.get('prevalence', 'unknown'),
                'acuity': disease.get('acuity', 'unknown')
            })
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ Loaded {len(diseases)} diseases into knowledge base")
    
    def query_similar_diseases(self, symptoms: str, n_results: int = 15) -> Dict[str, Any]:
        """Find diseases matching symptom description"""
        results = self.collection.query(
            query_texts=[symptoms],
            n_results=n_results
        )
        
        # Safely extract data with proper type handling
        ids_list = []
        distances_list = []
        metadatas_list = []
        documents_list = []
        
        if results and isinstance(results, dict):
            if 'ids' in results and results['ids'] and len(results['ids']) > 0:
                ids_list = results['ids'][0] if isinstance(results['ids'][0], list) else []
            
            if 'distances' in results and results['distances'] and len(results['distances']) > 0:
                distances_list = results['distances'][0] if isinstance(results['distances'][0], list) else []
            
            if 'metadatas' in results and results['metadatas'] and len(results['metadatas']) > 0:
                metadatas_list = results['metadatas'][0] if isinstance(results['metadatas'][0], list) else []
            
            if 'documents' in results and results['documents'] and len(results['documents']) > 0:
                documents_list = results['documents'][0] if isinstance(results['documents'][0], list) else []
        
        return {
            'ids': ids_list,
            'distances': distances_list,
            'metadatas': metadatas_list,
            'documents': documents_list
        }
    
    def get_evidence_mapping(self, symptom_concept: str) -> Dict[str, List[str]]:
        """Get supporting/contradicting diseases for a symptom"""
        return self.symptom_disease_map.get(symptom_concept, {'supports': [], 'contradicts': []})
    
    def get_prevalence_prior(self, prevalence: str) -> float:
        """Get prior probability based on disease prevalence"""
        priors = {
            'very_common': 0.25,
            'common': 0.15,
            'uncommon': 0.05,
            'rare': 0.01,
            'unknown': 0.05
        }
        return priors.get(prevalence, 0.05)