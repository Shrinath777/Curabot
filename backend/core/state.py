 
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class EvidenceItem(BaseModel):
    """Individual piece of evidence with supporting/contradicting relationships"""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    finding: str
    finding_type: str  # 'symptom', 'vital', 'lab', 'risk_factor'
    supports: List[str] = Field(default_factory=list)  # Disease names
    contradicts: List[str] = Field(default_factory=list)  # Disease names
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)

class Hypothesis(BaseModel):
    """Diagnostic hypothesis with confidence and evidence links"""
    disease_name: str
    confidence: float
    prior_confidence: float = 0.0
    supporting_evidence: List[str] = Field(default_factory=list)  # evidence_ids
    contradicting_evidence: List[str] = Field(default_factory=list)  # evidence_ids
    last_updated: datetime = Field(default_factory=datetime.now)
    reasoning_trace: List[str] = Field(default_factory=list)

class AgentThought(BaseModel):
    """Real-time agent thoughts for streaming"""
    agent_name: str
    thought: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None

class DiagnosticState(BaseModel):
    """Complete diagnostic state managed by LangGraph"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_inputs: List[str] = Field(default_factory=list)
    
    # Normalized symptoms
    normalized_symptoms: List[Dict[str, Any]] = Field(default_factory=list)
    ambiguous_signals: List[str] = Field(default_factory=list)
    
    # Hypotheses
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    top_n: int = 5
    
    # Evidence tracking
    evidence_ledger: List[EvidenceItem] = Field(default_factory=list)
    
    # Diagnostic process
    stage: int = 1
    iteration: int = 0
    need_more_info: bool = False
    suggested_questions: List[str] = Field(default_factory=list)
    
    # Bias detection
    bias_flags: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent thoughts for streaming
    agent_thoughts: List[AgentThought] = Field(default_factory=list)
    
    # Reasoning history
    reasoning_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True