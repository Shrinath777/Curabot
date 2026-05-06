from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.disease_db import DiseaseKnowledgeBase

class DiseaseMatcher:
    """Matches patient symptoms and vitals to diseases in the database"""
    
    def __init__(self, knowledge_base: DiseaseKnowledgeBase):
        self.kb = knowledge_base
    
    def match_by_symptoms(self, symptoms: List[str], vitals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find diseases matching symptoms and vitals"""
        
        # Create query text from symptoms
        query_text = " ".join(symptoms) if symptoms else "general symptoms"
        
        # Query ChromaDB for similar diseases
        results = self.kb.query_similar_diseases(query_text, n_results=15)
        
        scored_results = []
        
        # Check if results exist
        if not results or not results.get('metadatas'):
            return []
        
        for i, metadata in enumerate(results['metadatas']):
            if not metadata:
                continue
            
            score = self._calculate_match_score(metadata, symptoms, vitals)
            
            # Get distance if available
            distance = 0.0
            if results.get('distances') and i < len(results['distances']):
                distance = results['distances'][i]
            
            scored_results.append({
                'name': str(metadata.get('name', 'Unknown')),
                'symptoms': str(metadata.get('symptoms', '')),
                'lab_tests': str(metadata.get('lab_tests', '')),
                'similarity_score': float(1 - distance) if distance else 0.5,
                'vital_match_score': float(score['vital_score']),
                'symptom_match_score': float(score['symptom_score']),
                'total_score': float(score['total']),
                'matching_symptoms': list(score['matching_symptoms']),
                'matching_vitals': list(score['matching_vitals'])
            })
        
        return sorted(scored_results, key=lambda x: x['total_score'], reverse=True)
    
    def _calculate_match_score(self, disease_meta: Dict[str, Any], symptoms: List[str], vitals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how well patient data matches a disease"""
        
        # Symptom matching
        disease_symptoms = str(disease_meta.get('symptoms', '')).lower().split(', ')
        matching_symptoms = []
        symptom_score = 0.0
        
        for patient_symptom in symptoms:
            patient_symptom_lower = patient_symptom.lower()
            for disease_symptom in disease_symptoms:
                if patient_symptom_lower in disease_symptom or disease_symptom in patient_symptom_lower:
                    matching_symptoms.append(patient_symptom)
                    symptom_score += 1.0
                    break
        
        symptom_score = (symptom_score / max(len(disease_symptoms), 1)) * 100.0
        
        # Vital signs matching
        vital_score = 0.0
        matching_vitals = []
        vital_checks = 0
        
        # Check heart rate
        if vitals.get('heart_rate') is not None:
            hr_min = disease_meta.get('hr_min')
            hr_max = disease_meta.get('hr_max')
            if hr_min is not None and hr_max is not None:
                vital_checks += 1
                hr = float(vitals['heart_rate'])
                if hr_min <= hr <= hr_max:
                    vital_score += 1.0
                    matching_vitals.append('heart_rate')
        
        # Check oxygen saturation
        if vitals.get('oxygen_saturation') is not None:
            spo2_min = disease_meta.get('spo2_min')
            spo2_max = disease_meta.get('spo2_max')
            if spo2_min is not None and spo2_max is not None:
                vital_checks += 1
                spo2 = float(vitals['oxygen_saturation'])
                if spo2_min <= spo2 <= spo2_max:
                    vital_score += 1.0
                    matching_vitals.append('oxygen_saturation')
        
        vital_score = (vital_score / max(vital_checks, 1)) * 100.0
        
        # Total score (weighted)
        total = (symptom_score * 0.6) + (vital_score * 0.4)
        
        return {
            'symptom_score': symptom_score,
            'vital_score': vital_score,
            'total': total,
            'matching_symptoms': matching_symptoms,
            'matching_vitals': matching_vitals
        }