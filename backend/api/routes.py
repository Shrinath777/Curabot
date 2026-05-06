import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
import asyncio
import json

# Change from relative to absolute imports
from core.supervisor import SessionManager
from knowledge.disease_db import DiseaseKnowledgeBase
from knowledge.loader import initialize_knowledge_base

# Initialize app
app = FastAPI(
    title="CuraBot API",
    description="Agentic AI Differential Diagnosis Tutor with 6 Agents",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize knowledge base and session manager
kb = initialize_knowledge_base()
session_manager = SessionManager()
session_manager.init_graph(kb)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    hypotheses: List[dict]
    suggested_questions: List[str]
    evidence: List[dict]
    bias_flags: List[dict]
    iteration: int
    need_more_info: bool
    agent_thoughts: List[dict]
    disclaimer: str

@app.get("/")
async def root():
    return {
        "service": "CuraBot - Agentic AI Differential Diagnosis Tutor",
        "status": "operational",
        "agents": ["Symptom Normalizer", "Hypothesis Generator", "Evidence Evaluator", 
                  "Hypothesis Reviser", "Diagnostic Strategist", "Self-Critique"],
        "disclaimer": "FOR MEDICAL EDUCATION ONLY"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "CuraBot backend is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through all 6 agents"""
    try:
        response = await session_manager.process_input(
            request.message,
            request.session_id
        )
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset_session(request: dict):
    """Reset a diagnostic session"""
    session_id = request.get("session_id")
    if session_id:
        session_manager.clear_session(session_id)
    return {"status": "reset", "session_id": session_id}