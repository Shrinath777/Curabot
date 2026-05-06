import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any
from .graph import CurabotGraph
from .state import DiagnosticState
from knowledge.disease_db import DiseaseKnowledgeBase
import sqlite3
import json
from datetime import datetime

class SessionManager:
    """Manages conversation sessions and checkpointing"""
    
    def __init__(self, db_path: str = "curabot_sessions.db"):
        self.db_path = db_path
        self._init_db()
        self.graph = None
        self.active_sessions: Dict[str, DiagnosticState] = {}
    
    def _init_db(self):
        """Initialize SQLite database for session storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                last_updated TIMESTAMP,
                state_json TEXT,
                message_history TEXT
            )
        ''')
        
        # Create interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                user_input TEXT,
                agent_response TEXT,
                agent_thoughts TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_graph(self, kb: DiseaseKnowledgeBase):
        """Initialize the Curabot graph"""
        self.graph = CurabotGraph(kb)
    
    async def process_input(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process user input through all 6 agents"""
        
        if not self.graph:
            raise ValueError("Graph not initialized. Call init_graph first.")
        
        # Process through graph
        final_state = await self.graph.process_message(user_input, session_id)
        
        # Store in active sessions
        self.active_sessions[final_state.session_id] = final_state
        
        # Save to database
        self._save_session(final_state)
        
        # Format response for frontend
        response = self._format_response(final_state)
        
        return response
    
    def _save_session(self, state: DiagnosticState):
        """Save session state to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert state to JSON
        state_dict = state.dict()
        state_json = json.dumps(state_dict, default=str)
        
        # Create message history
        message_history = json.dumps(state.user_inputs)
        
        # Upsert session
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (session_id, created_at, last_updated, state_json, message_history)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            state.session_id,
            datetime.now(),
            datetime.now(),
            state_json,
            message_history
        ))
        
        conn.commit()
        conn.close()
    
    def _format_response(self, state: DiagnosticState) -> Dict[str, Any]:
        """Format state into user-friendly response for frontend"""
        
        # Format hypotheses with confidence
        hypotheses = []
        for h in state.hypotheses:
            hypotheses.append({
                'name': h.disease_name,
                'confidence': round(h.confidence * 100, 1),
                'supporting': len(h.supporting_evidence),
                'contradicting': len(h.contradicting_evidence),
                'reasoning': h.reasoning_trace[-1] if h.reasoning_trace else ""
            })
        
        # Format evidence
        evidence = []
        for e in state.evidence_ledger:
            evidence.append({
                'finding': e.finding,
                'supports': e.supports[:3],
                'contradicts': e.contradicts[:3],
                'confidence': e.confidence
            })
        
        # Format agent thoughts for streaming
        agent_thoughts = []
        for thought in state.agent_thoughts[-10:]:  # Last 10 thoughts
            agent_thoughts.append({
                'agent': thought.agent_name,
                'thought': thought.thought,
                'timestamp': thought.timestamp.isoformat() if thought.timestamp else None,
                'data': thought.data
            })
        
        return {
            'session_id': state.session_id,
            'hypotheses': hypotheses,
            'suggested_questions': state.suggested_questions,
            'evidence': evidence,
            'bias_flags': state.bias_flags,
            'iteration': state.iteration,
            'need_more_info': state.need_more_info,
            'agent_thoughts': agent_thoughts,
            'disclaimer': "⚠️ FOR MEDICAL EDUCATION ONLY - Not for clinical use"
        }
    
    def get_session(self, session_id: str) -> Optional[DiagnosticState]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]