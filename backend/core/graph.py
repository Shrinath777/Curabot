import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.symptom_normalizer import SymptomNormalizer
from agents.hypothesis_generator import HypothesisGenerator
from agents.evidence_evaluator import EvidenceEvaluator
from agents.hypothesis_reviser import HypothesisReviser
from agents.diagnostic_strategist import DiagnosticStrategist
from agents.self_critique import SelfCritique
from knowledge.disease_db import DiseaseKnowledgeBase
from .state import DiagnosticState
import sqlite3

class CurabotGraph:
    """Main graph orchestrating all 6 agents"""
    
    def __init__(self, knowledge_base: DiseaseKnowledgeBase):
        self.kb = knowledge_base
        
        # Initialize all 6 agents
        self.agents = {
            'normalizer': SymptomNormalizer(),
            'generator': HypothesisGenerator(self.kb),
            'evaluator': EvidenceEvaluator(self.kb),
            'reviser': HypothesisReviser(),
            'strategist': DiagnosticStrategist(),
            'critique': SelfCritique()
        }
        
        # Build graph with checkpointing
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the agent workflow graph"""
        
        # Define node functions
        def normalize(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['normalizer'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        def generate(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['generator'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        def evaluate(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['evaluator'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        def revise(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['reviser'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        def strategize(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['strategist'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        def critique(state: DiagnosticState) -> Dict[str, Any]:
            result = self.agents['critique'].process(state)
            return {**result, 'agent_thoughts': state.agent_thoughts}
        
        # Define routing logic
        def route_after_critique(state: DiagnosticState) -> Literal['strategist', '__end__']:
            """Determine next step after critique"""
            if state.need_more_info:
                return 'strategist'  # Ask more questions
            else:
                return '__end__'  # Conclude
        
        # Build graph with checkpointing
        workflow = StateGraph(DiagnosticState)
        
        # Add nodes for all 6 agents
        workflow.add_node("normalize", normalize)
        workflow.add_node("generate", generate)
        workflow.add_node("evaluate", evaluate)
        workflow.add_node("revise", revise)
        workflow.add_node("strategize", strategize)
        workflow.add_node("critique", critique)
        
        # Add edges
        workflow.set_entry_point("normalize")
        workflow.add_edge("normalize", "generate")
        workflow.add_edge("generate", "evaluate")
        workflow.add_edge("evaluate", "revise")
        workflow.add_edge("revise", "strategize")
        workflow.add_edge("strategize", "critique")
        
        # Add conditional edge
        workflow.add_conditional_edges(
            "critique",
            route_after_critique,
            {
                "strategist": "strategize",
                "__end__": END
            }
        )
        
        # Add checkpointing
        conn = sqlite3.connect("curabot_checkpoints.db", check_same_thread=False)
        memory = SqliteSaver(conn)
        
        return workflow.compile(checkpointer=memory)
    
    async def process_message(self, message: str, session_id: str = None) -> DiagnosticState:
        """Process a user message through all 6 agents"""
        
        # Create or get state
        state = DiagnosticState()
        if session_id:
            state.session_id = session_id
        
        # Add user input
        state.user_inputs.append(message)
        state.iteration += 1
        
        # Run graph
        config = {"configurable": {"thread_id": state.session_id}}
        final_state = await self.graph.ainvoke(state, config)
        
        return final_state