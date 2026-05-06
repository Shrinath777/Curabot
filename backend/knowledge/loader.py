 
from .disease_db import DiseaseKnowledgeBase
import json
import os

def initialize_knowledge_base():
    """Initialize and populate the knowledge base"""
    kb = DiseaseKnowledgeBase()
    
    # Check if already populated
    if kb.collection.count() == 0:
        diseases_path = os.path.join(os.path.dirname(__file__), '../data/diseases.json')
        kb.load_diseases(diseases_path)
    
    return kb

def get_disease_data():
    """Get disease data for rule-based systems"""
    with open(os.path.join(os.path.dirname(__file__), '../data/diseases.json'), 'r') as f:
        return json.load(f)