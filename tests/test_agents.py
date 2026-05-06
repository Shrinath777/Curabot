 
import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.symptom_normalizer import SymptomNormalizerAgent
from backend.agents.hypothesis_generator import HypothesisGeneratorAgent
from backend.agents.evidence_evaluator import EvidenceEvaluatorAgent
from backend.agents.hypothesis_reviser import HypothesisReviserAgent
from backend.agents.diagnostic_strategist import DiagnosticStrategyAgent
from backend.agents.self_critique import SelfCritiqueAgent
from backend.core.state import DiagnosticState
from backend.knowledge.disease_db import DiseaseKnowledgeBase

class TestAgents:
    @pytest.fixture
    def setup(self):
        """Setup test environment"""
        self.kb = DiseaseKnowledgeBase(persist_directory=":memory:")
        self.normalizer = SymptomNormalizerAgent()
        self.generator = HypothesisGeneratorAgent(self.kb)
        self.evaluator = EvidenceEvaluatorAgent(self.kb)
        self.reviser = HypothesisReviserAgent()
        self.strategist = DiagnosticStrategyAgent()
        self.critique = SelfCritiqueAgent()
        self.state = DiagnosticState()
        
    def test_symptom_normalizer(self, setup):
        """Test symptom normalization agent"""
        self.state.user_inputs = ["I have chest pain and shortness of breath"]
        result = self.normalizer.process(self.state)
        
        assert 'normalized_symptoms' in result
        assert len(result['normalized_symptoms']) > 0
        
        # Check if chest pain was identified
        chest_pain = next(
            (s for s in result['normalized_symptoms'] if s['concept'] == 'chest_pain'),
            None
        )
        assert chest_pain is not None
        
        # Check if dyspnea was identified
        dyspnea = next(
            (s for s in result['normalized_symptoms'] if s['concept'] == 'dyspnea'),
            None
        )
        assert dyspnea is not None
    
    def test_hypothesis_generator(self, setup):
        """Test hypothesis generation agent"""
        self.state.normalized_symptoms = [
            {'concept': 'chest_pain', 'quality': 'unspecified'},
            {'concept': 'dyspnea', 'quality': 'unspecified'}
        ]
        
        result = self.generator.process(self.state)
        
        assert 'hypotheses' in result
        assert len(result['hypotheses']) > 0
        
        # Check if MI is in hypotheses
        mi_hypothesis = next(
            (h for h in result['hypotheses'] if h.disease_name == 'Acute Myocardial Infarction'),
            None
        )
        assert mi_hypothesis is not None
        assert mi_hypothesis.confidence > 0
    
    def test_evidence_evaluator(self, setup):
        """Test evidence evaluation agent"""
        self.state.normalized_symptoms = [
            {'concept': 'chest_pain', 'quality': 'unspecified'}
        ]
        
        result = self.evaluator.process(self.state)
        
        assert 'evidence_ledger' in result
        assert len(result['evidence_ledger']) > 0
        
        # Check chest pain evidence
        chest_pain_evidence = next(
            (e for e in result['evidence_ledger'] if e.finding == 'chest_pain'),
            None
        )
        assert chest_pain_evidence is not None
        assert 'Acute Myocardial Infarction' in chest_pain_evidence.supports
    
    def test_hypothesis_reviser(self, setup):
        """Test hypothesis revision agent"""
        # Setup initial state
        from backend.core.state import Hypothesis
        
        self.state.hypotheses = [
            Hypothesis(disease_name="Test Disease 1", confidence=0.5, prior_confidence=0.5),
            Hypothesis(disease_name="Test Disease 2", confidence=0.3, prior_confidence=0.3)
        ]
        
        self.state.evidence_ledger = []  # No new evidence
        
        result = self.reviser.process(self.state)
        
        assert 'hypotheses' in result
        assert len(result['hypotheses']) == 2
    
    def test_diagnostic_strategist(self, setup):
        """Test diagnostic strategist agent"""
        from backend.core.state import Hypothesis
        
        self.state.hypotheses = [
            Hypothesis(disease_name="Acute Myocardial Infarction", confidence=0.6, prior_confidence=0.5),
            Hypothesis(disease_name="Pulmonary Embolism", confidence=0.3, prior_confidence=0.3),
            Hypothesis(disease_name="GERD", confidence=0.1, prior_confidence=0.1)
        ]
        
        result = self.strategist.process(self.state)
        
        assert 'suggested_questions' in result
        assert len(result['suggested_questions']) > 0
    
    def test_self_critique(self, setup):
        """Test self-critique agent for bias detection"""
        from backend.core.state import Hypothesis
        
        # Create state with anchoring bias (large confidence gap)
        self.state.hypotheses = [
            Hypothesis(disease_name="Acute Myocardial Infarction", confidence=0.9, prior_confidence=0.5),
            Hypothesis(disease_name="Pulmonary Embolism", confidence=0.1, prior_confidence=0.1),
            Hypothesis(disease_name="GERD", confidence=0.05, prior_confidence=0.05)
        ]
        self.state.iteration = 1
        
        result = self.critique.process(self.state)
        
        assert 'bias_flags' in result
        # Should detect anchoring bias
        anchoring_bias = next(
            (b for b in result['bias_flags'] if b.get('bias') == 'anchoring'),
            None
        )
        assert anchoring_bias is not None
    
    def test_full_agent_pipeline(self, setup):
        """Test all agents in sequence"""
        # Step 1: Normalize symptoms
        self.state.user_inputs = ["I have chest pain and shortness of breath"]
        result1 = self.normalizer.process(self.state)
        self.state.normalized_symptoms = result1['normalized_symptoms']
        
        # Step 2: Generate hypotheses
        result2 = self.generator.process(self.state)
        self.state.hypotheses = result2['hypotheses']
        
        # Step 3: Evaluate evidence
        result3 = self.evaluator.process(self.state)
        self.state.evidence_ledger = result3['evidence_ledger']
        
        # Step 4: Revise hypotheses
        result4 = self.reviser.process(self.state)
        
        # Step 5: Generate strategy
        result5 = self.strategist.process(self.state)
        
        # Step 6: Self-critique
        result6 = self.critique.process(self.state)
        
        # Verify pipeline completed
        assert len(self.state.hypotheses) > 0
        assert len(self.state.evidence_ledger) > 0
        assert len(result5['suggested_questions']) > 0
    
    def test_edge_cases(self, setup):
        """Test edge cases"""
        # Empty input
        self.state.user_inputs = []
        result = self.normalizer.process(self.state)
        assert len(result.get('normalized_symptoms', [])) == 0
        
        # Gibberish input
        self.state.user_inputs = ["asdf qwerty 12345"]
        result = self.normalizer.process(self.state)
        assert len(result.get('normalized_symptoms', [])) == 0
        assert len(result.get('ambiguous_signals', [])) > 0
        
        # No hypotheses
        self.state.hypotheses = []
        result = self.strategist.process(self.state)
        assert len(result.get('suggested_questions', [])) > 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])