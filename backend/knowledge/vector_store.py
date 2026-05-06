import json
import hashlib
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Hotfix for PyTorch 2.0.1 and newer transformers library
import torch
if not hasattr(torch, 'compiler'):
    class DummyCompiler:
        def disable(self, *args, **kwargs):
            return lambda f: f
    torch.compiler = DummyCompiler()
if not hasattr(torch, 'float8_e4m3fn'):
    torch.float8_e4m3fn = None
    torch.float8_e5m2 = None

from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
class DummyEmbeddingFunction(EmbeddingFunction):
    """Fallback embedding function that prevents ChromaDB from trying to download models."""
    def __call__(self, input: Documents) -> Embeddings:
        return [[0.0] * 384 for _ in input]

# Imported after the torch hotfix
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class VectorStore:
    """Vector database for storing and retrieving disease embeddings"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.is_active = False 
        
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
                self.embedding_fn = GoogleGenerativeAiEmbeddingFunction(api_key=api_key)
            else:
                logger.warning("No API key found, falling back to dummy embedding.")
                self.embedding_fn = DummyEmbeddingFunction()
            
        except Exception as e:
            logger.error(f"⚠️ VectorStore Fatal Error ({e}).")
            self.embedding_fn = DummyEmbeddingFunction()

            
        # Create or get collections (only if client is active)
        if hasattr(self, 'client'):
            self.diseases_collection = self._get_or_create_collection("diseases")
            self.symptoms_collection = self._get_or_create_collection("symptoms")
            self.cases_collection = self._get_or_create_collection("cases")
            self.patient_records_collection = self._get_or_create_collection("patient_records")
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one with fallback support"""
        try:
            return self.client.get_collection(
                name=name,
                embedding_function=self.embedding_fn
            )
        except Exception:
            # Fallback for when embedding model is missing
            return self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_fn if self.embedding_fn else DummyEmbeddingFunction(),
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_diseases(self, diseases: List[Dict[str, Any]]):
        """Add diseases to vector store"""
        ids = []
        documents = []
        metadatas = []
        
        for disease in diseases:
            # Create unique ID
            doc_id = hashlib.md5(disease['name'].encode()).hexdigest()
            ids.append(doc_id)
            
            # Create document text for embedding
            doc_text = f"""
            Disease: {disease['name']}
            ICD-10: {disease.get('icd10', 'Unknown')}
            System: {disease.get('system', 'Unknown')}
            Symptoms: {', '.join(disease.get('symptoms', []))}
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
        self.diseases_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(ids)
    
    def add_symptoms(self, symptoms: List[Dict[str, Any]]):
        """Add symptom mappings to vector store"""
        ids = []
        documents = []
        metadatas = []
        
        for symptom in symptoms:
            doc_id = hashlib.md5(symptom['concept'].encode()).hexdigest()
            ids.append(doc_id)
            
            doc_text = f"""
            Symptom: {symptom['concept']}
            Description: {symptom.get('description', '')}
            Associated Diseases: {', '.join(symptom.get('associated_diseases', []))}
            """
            documents.append(doc_text)
            
            metadatas.append({
                'concept': symptom['concept'],
                'system': symptom.get('system', 'unknown'),
                'quality': symptom.get('quality', 'unspecified')
            })
        
        self.symptoms_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def add_cases(self, cases: List[Dict[str, Any]]):
        """Add synthetic cases to vector store"""
        ids = []
        documents = []
        metadatas = []
        
        for case in cases:
            doc_id = hashlib.md5(case['id'].encode()).hexdigest()
            ids.append(doc_id)
            
            doc_text = f"""
            Case: {case['name']}
            Ground Truth: {case['ground_truth']}
            Symptoms: {', '.join([s['input'] for s in case.get('stages', [])])}
            """
            documents.append(doc_text)
            
            metadatas.append({
                'id': case['id'],
                'name': case['name'],
                'ground_truth': case['ground_truth']
            })
        
        self.cases_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def add_patient_records(self, user_id: str, report_id: str, source: str, chunks: List[str]):
        """Add parsed PDF chunks to patient_records collection for RAG"""
        if not chunks:
            return 0
            
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID for chunk
            doc_id = hashlib.md5(f"{report_id}_{i}".encode()).hexdigest()
            ids.append(doc_id)
            documents.append(chunk)
            
            # Store metadata linking back to user and report
            metadatas.append({
                'user_id': user_id,
                'report_id': report_id,
                'source': source,
                'chunk_index': i
            })
            
        # Add to collection
        self.patient_records_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(ids)
    
    def search_patient_records(self, user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search medical records scoped by user_id"""
        try:
            results = self.patient_records_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id}
            )
            
            formatted_results = []
            if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    formatted_results.append({
                        'chunk': results['documents'][0][i],
                        'source': metadata.get('source', 'Unknown report'),
                        'similarity': 1 - (results['distances'][0][i] if results.get('distances') else 0)
                    })
            return formatted_results
        except Exception as e:
            return []
    
    def search_diseases(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search for diseases similar to query"""
        results = self.diseases_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results and results['metadatas'][0]:
            for i, metadata in enumerate(results['metadatas'][0]):
                formatted_results.append({
                    'name': metadata['name'],
                    'icd10': metadata.get('icd10', ''),
                    'system': metadata.get('system', ''),
                    'prevalence': metadata.get('prevalence', 'unknown'),
                    'similarity': 1 - (results['distances'][0][i] if results['distances'] else 0),
                    'metadata': metadata
                })
        
        return formatted_results
    
    def search_symptoms(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for symptoms similar to query"""
        results = self.symptoms_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results and results['metadatas'][0]:
            for i, metadata in enumerate(results['metadatas'][0]):
                formatted_results.append({
                    'concept': metadata['concept'],
                    'system': metadata.get('system', ''),
                    'similarity': 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        return formatted_results
    
    def get_disease_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get disease by exact name match"""
        results = self.diseases_collection.query(
            query_texts=[name],
            n_results=1
        )
        
        if results and results['metadatas'][0]:
            return results['metadatas'][0][0]
        return None
    
    def get_all_diseases(self) -> List[Dict[str, Any]]:
        """Get all diseases from vector store"""
        results = self.diseases_collection.get()
        
        diseases = []
        if results and results['metadatas']:
            for i, metadata in enumerate(results['metadatas']):
                diseases.append(metadata)
        
        return diseases
    
    def delete_collection(self, name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(name)
            return True
        except ValueError:
            return False
    
    def reset(self):
        """Reset the vector store (for testing)"""
        self.client.reset()
        self.diseases_collection = self._get_or_create_collection("diseases")
        self.symptoms_collection = self._get_or_create_collection("symptoms")
        self.cases_collection = self._get_or_create_collection("cases")
        self.patient_records_collection = self._get_or_create_collection("patient_records")
    
    def count_diseases(self) -> int:
        """Get count of diseases in store"""
        return self.diseases_collection.count()
    
    def count_symptoms(self) -> int:
        """Get count of symptoms in store"""
        return self.symptoms_collection.count()
    
    def health_check(self) -> bool:
        """Check if vector store is healthy"""
        try:
            self.client.heartbeat()
            return True
        except:
            return False