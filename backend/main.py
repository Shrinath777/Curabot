"""
CuraBot — Agentic AI Differential Diagnosis Tutor
Main FastAPI application with auth, chat, and diagnostic endpoints.

WARNING: FOR MEDICAL EDUCATION ONLY — Not for clinical use.
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from pathlib import Path

# Load env from backend directory with override=True to catch new API keys
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CuraBot API",
    version="2.0.0",
    description="Agentic AI Differential Diagnosis Tutor — FOR MEDICAL EDUCATION ONLY",
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") != "production" else None,
)

# ==================== RATE LIMITING ====================
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _rate_limit_available = True
    logger.info("Rate limiting enabled (slowapi)")
    # Decorator helper for rate limiting
    def rate_limit(limit_string: str):
        return limiter.limit(limit_string)
except ImportError:
    _rate_limit_available = False
    logger.warning("slowapi not installed — rate limiting DISABLED. Run: pip install slowapi")
    # No-op decorator when slowapi is not installed
    def rate_limit(limit_string: str):
        def decorator(func):
            return func
        return decorator

# ==================== SECURITY HEADERS MIDDLEWARE ====================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Add unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS — explicit origins needed when allow_credentials=True
# Build allowed origins dynamically from environment + hardcoded dev URLs
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# Add production frontend URL(s) from environment
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _cors_origins.extend([u.strip() for u in _frontend_url.split(",") if u.strip()])
# Add common deployment patterns
_cors_origins.extend([
    "https://curabot.vercel.app",
    "https://curabot.netlify.app",
    "https://curabot-xclt.vercel.app",
])
# Remove duplicates while preserving order
_cors_origins = list(dict.fromkeys(_cors_origins))

# Also allow any .vercel.app or .netlify.app subdomain via regex
import re
_cors_origin_regex = r"https://.*\.(vercel\.app|netlify\.app|onrender\.com)$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Services ====================
from services.supabase_client import supabase_service
from services.orchestrator import orchestrator
from services.user_logger import log_user_action

# ==================== In-Memory Session Cache ====================
active_sessions: Dict[str, Dict] = {}


# ==================== DATA MODELS ====================

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    known_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None

# Initialize VectorStore singleton for faster access
try:
    from knowledge.vector_store import VectorStore
    vector_store = VectorStore()
    logger.info("VectorStore initialized.")
except Exception as ve:
    logger.warning(f"Failed to initialize VectorStore: {ve}")
    vector_store = None

class VitalSigns(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    vitals: Optional[VitalSigns] = None

    @validator("message")
    def validate_message(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 5000:
            raise ValueError("Message too long (max 5000 characters)")
        return v

class ChatResponse(BaseModel):
    session_id: str
    message: str
    hypotheses: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    questions: List[str] = []
    bias_flags: List[Dict[str, Any]] = []
    agent_thoughts: List[Dict[str, Any]] = []
    iteration: int = 0
    need_more_info: bool = True
    request_vitals: bool = False
    vitals_needed: List[str] = []
    confidence_trajectory: List[Dict[str, Any]] = []
    revision_narrative: str = ""
    should_conclude: bool = False
    conclusion_message: str = ""
    final_recommendations: List[str] = []
    disclaimer: str = "WARNING: FOR MEDICAL EDUCATION ONLY — Not for clinical use"


# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/signup")
@rate_limit("5/minute")
async def signup(request: Request, signup_data: SignupRequest):
    """Register a new user."""
    result = await supabase_service.signup(
        email=signup_data.email,
        password=signup_data.password,
        full_name=signup_data.full_name
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Signup failed"))
        
    try:
        log_user_action("SIGNUP", signup_data.email, signup_data.full_name)
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")
        
    return result

@app.post("/api/auth/login")
@rate_limit("10/minute")
async def login(request: Request, login_data: LoginRequest):
    """Login and get access token."""
    result = await supabase_service.login(
        email=login_data.email,
        password=login_data.password
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid credentials"))
        
    try:
        log_user_action("LOGIN", login_data.email, "")
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")
        
    return result

@app.get("/api/auth/me")
async def get_current_user(user_id: str = Header(None, alias="x-user-id")):
    """Get current user profile."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = await supabase_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile

@app.put("/api/auth/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    user_id: str = Header(None, alias="x-user-id")
):
    """Update user profile and medical history."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = request.dict(exclude_none=True)
    success = await supabase_service.update_user_profile(user_id, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return {"status": "updated"}


# ==================== CHAT ENDPOINT ====================

@app.post("/api/chat", response_model=ChatResponse)
@rate_limit("12/minute")
async def chat(request: Request, chat_req: ChatRequest):
    """
    Main chat endpoint — processes messages through the 6-agent pipeline.
    Handles both new and returning users.
    Rate limited: 12 requests/minute per IP.
    """
    session_id = chat_req.session_id or str(uuid.uuid4())
    user_id = chat_req.user_id

    # Initialize or restore session
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "user_id": user_id,
            "iteration": 0,
            "hypotheses": [],
            "evidence": [],
            "accumulated_evidence": [],
            "conversation_history": [],
            "confidence_trajectory": [],
            "vitals": None,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Create persistent session if user is logged in
        if user_id:
            await supabase_service.create_session(user_id, session_id=session_id, title=chat_req.message[:50])

    session = active_sessions[session_id]

    # Update vitals if provided
    if chat_req.vitals:
        session["vitals"] = chat_req.vitals.dict()

    # Add user message to conversation history
    session["conversation_history"].append({
        "role": "user",
        "content": chat_req.message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Save message to persistent storage
    if user_id:
        await supabase_service.save_message(session_id, "user", chat_req.message)

    # Get user context for return users
    user_context = None
    message = chat_req.message
    if user_id:
        logger.info(f"INFO: [INTELLIGENCE] Accessing cloud history for patient ID: {user_id[:8]}...")
        user_context = await supabase_service.get_user_context(user_id)
        if user_context:
            logger.info("INFO: [INTELLIGENCE] Found patient profile and medical history in cloud.")
            try:
                # Use global vector_store singleton initialized at module level
                if vector_store:
                    # RAG: Search patient's uploaded PDF reports
                    pdf_results = vector_store.search_patient_records(user_id=user_id, query=message)
                    
                    # 1. Format the retrieved RAG chunks into a structured context block for the LLM
                    medical_context = ""
                    if pdf_results:
                        logger.info(f"INFO: [INTELLIGENCE] RAG Search: Found {len(pdf_results)} relevant findings in uploaded medical PDFs.")
                        context_chunks = "\n".join([f"- From {r['source']}: {r['chunk']}" for r in pdf_results[:3]])
                        medical_context += f"UPLOADED MEDICAL REPORTS CONTEXT:\n{context_chunks}\n\n"
                        
                        # 2. CRITICAL: Also store RAG results in structured user_context so agents see them
                        user_context["extracted_medical_records"] = pdf_results[:3]
                    else:
                        logger.info("INFO: [INTELLIGENCE] RAG Search: No relevant medical records found for this query.")
                    
                    if medical_context:
                        message = f"{medical_context}\nPatient Query: {message}"
                
            except Exception as e:
                logger.warning(f"RAG/VectorStore search failed: {e}. Proceeding without context.")

    # Run the 6-agent pipeline
    try:
        result = await orchestrator.run_pipeline(
            message=message,
            session_state=session,
            user_context=user_context,
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        # Fallback to a basic message if the pipeline fails catastrophically
        return ChatResponse(
            session_id=session_id,
            message="I'm sorry, I encountered an internal error while processing your request. Please try again or check your symptoms later.",
            iteration=session.get("iteration", 0),
            need_more_info=True
        )

    # Update session state
    session["iteration"] = result.get("iteration", session["iteration"] + 1)
    session["hypotheses"] = result.get("hypotheses", [])
    session["evidence"] = result.get("evidence", [])
    session["accumulated_evidence"] = result.get("accumulated_evidence", [])
    session["accumulated_symptoms"] = result.get("accumulated_symptoms", {})
    session["confidence_trajectory"] = result.get("confidence_trajectory", [])

    # Add bot response to conversation history
    bot_message = result.get("message", "")
    session["conversation_history"].append({
        "role": "assistant",
        "content": bot_message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Save bot message to persistent storage
    if user_id:
        metadata = {
            "hypotheses": result.get("hypotheses", []),
            "evidence": result.get("evidence", []),
            "iteration": result.get("iteration"),
        }
        await supabase_service.save_message(session_id, "assistant", bot_message, metadata)

    # Save diagnosis if concluded
    if result.get("should_conclude") and user_id:
        await supabase_service.save_diagnosis(
            session_id=session_id,
            user_id=user_id,
            hypotheses=result.get("hypotheses", []),
            evidence=result.get("evidence", []),
            confidence_trajectory=result.get("confidence_trajectory", [])
        )

    # Build response
    return ChatResponse(
        session_id=session_id,
        message=bot_message,
        hypotheses=result.get("hypotheses", []),
        evidence=result.get("evidence", []),
        questions=result.get("questions", []),
        bias_flags=result.get("bias_flags", []),
        agent_thoughts=result.get("agent_thoughts", []),
        iteration=result.get("iteration", 0),
        need_more_info=result.get("need_more_info", True),
        request_vitals=result.get("request_vitals", False),
        vitals_needed=result.get("vitals_needed", []),
        confidence_trajectory=result.get("confidence_trajectory", []),
        revision_narrative=result.get("revision_narrative", ""),
        should_conclude=result.get("should_conclude", False),
        conclusion_message=result.get("conclusion_message", ""),
        final_recommendations=result.get("final_recommendations", []),
        disclaimer="WARNING: FOR MEDICAL EDUCATION ONLY — Not for clinical use"
    )


# ==================== SESSION ENDPOINTS ====================

@app.get("/api/sessions")
async def get_user_sessions(user_id: str = Header(None, alias="x-user-id")):
    """Get all sessions for a user."""
    if not user_id:
        return {"sessions": []}
    sessions = await supabase_service.get_user_sessions(user_id)
    return {"sessions": sessions}

@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    messages = await supabase_service.get_session_messages(session_id)
    return {"messages": messages}

@app.post("/api/session/reset")
async def reset_session(session_id: str):
    """Reset a diagnostic session."""
    if session_id in active_sessions:
        del active_sessions[session_id]
    return {"status": "reset", "session_id": session_id}


# ==================== DIAGNOSIS HISTORY ====================

@app.get("/api/diagnoses")
async def get_diagnosis_history(user_id: str = Header(None, alias="x-user-id")):
    """Get diagnosis history for a user."""
    if not user_id:
        return {"diagnoses": []}
    diagnoses = await supabase_service.get_user_diagnosis_history(user_id)
    return {"diagnoses": diagnoses}


# ==================== REPORT DOWNLOAD ====================

@app.get("/api/report/json/{session_id}")
async def download_report_json(session_id: str):
    """Download diagnostic report as JSON for future reference."""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load disease KB for lab test recommendations
    import os
    kb_path = os.path.join(os.path.dirname(__file__), "data", "diseases.json")
    lab_tests_map = {}
    try:
        with open(kb_path, "r") as f:
            diseases = json.load(f)
        for d in diseases:
            lab_tests_map[d["name"]] = {
                "lab_tests": d.get("lab_tests", []),
                "red_flags": d.get("red_flags", []),
                "risk_factors": d.get("risk_factors", []),
                "vital_sign_patterns": d.get("vital_sign_patterns", {}),
                "description": d.get("description", ""),
            }
    except Exception:
        pass

    # Build comprehensive report
    hypotheses = session.get("hypotheses", [])
    top_diagnosis = hypotheses[0] if hypotheses else {"name": "Undetermined", "confidence": 0}
    top_details = lab_tests_map.get(top_diagnosis.get("name", ""), {})

    report = {
        "report_type": "CuraBot Differential Diagnosis Report",
        "disclaimer": "WARNING: FOR MEDICAL EDUCATION ONLY — Not for clinical use",
        "generated_at": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "patient_summary": {
            "total_iterations": session.get("iteration", 0),
            "total_evidence_items": len(session.get("accumulated_evidence", [])),
            "symptoms_identified": [s.get("name", "") for s in session.get("accumulated_symptoms", {}).get("primary_symptoms", [])],
        },
        "primary_diagnosis": {
            "name": top_diagnosis.get("name", "Undetermined"),
            "confidence": top_diagnosis.get("confidence", 0),
            "description": top_details.get("description", ""),
            "supporting_evidence_count": top_diagnosis.get("supporting", 0),
            "contradicting_evidence_count": top_diagnosis.get("contradicting", 0),
            "reasoning": top_diagnosis.get("reasoning", ""),
        },
        "differential_diagnoses": [
            {
                "name": h.get("name", ""),
                "confidence": h.get("confidence", 0),
                "supporting": h.get("supporting", 0),
                "contradicting": h.get("contradicting", 0),
                "reasoning": h.get("reasoning", ""),
                "recommended_tests": lab_tests_map.get(h.get("name", ""), {}).get("lab_tests", []),
            }
            for h in hypotheses
        ],
        "recommended_tests": top_details.get("lab_tests", []),
        "red_flags": top_details.get("red_flags", []),
        "vital_sign_patterns": top_details.get("vital_sign_patterns", {}),
        "evidence_ledger": session.get("evidence", []),
        "confidence_trajectory": session.get("confidence_trajectory", []),
        "conversation_history": [
            {"role": msg.get("role"), "content": msg.get("content"), "timestamp": msg.get("timestamp")}
            for msg in session.get("conversation_history", [])
        ],
    }

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=report,
        headers={
            "Content-Disposition": f"attachment; filename=curabot_report_{session_id[:8]}.json"
        }
    )


@app.get("/api/report/html/{session_id}")
async def download_report_html(session_id: str):
    """Download diagnostic report as printable HTML (print as PDF from browser)."""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load disease KB
    import os
    kb_path = os.path.join(os.path.dirname(__file__), "data", "diseases.json")
    lab_tests_map = {}
    try:
        with open(kb_path, "r") as f:
            diseases = json.load(f)
        for d in diseases:
            lab_tests_map[d["name"]] = d
    except Exception:
        pass

    hypotheses = session.get("hypotheses", [])
    top = hypotheses[0] if hypotheses else {"name": "Undetermined", "confidence": 0}
    top_details = lab_tests_map.get(top.get("name", ""), {})
    symptoms = [s.get("name", "").replace("_", " ").title() for s in session.get("accumulated_symptoms", {}).get("primary_symptoms", [])]
    conversation = session.get("conversation_history", [])
    evidence = session.get("evidence", [])
    now = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

    # Build hypothesis rows
    hyp_rows = ""
    for i, h in enumerate(hypotheses):
        details = lab_tests_map.get(h.get("name", ""), {})
        tests = ", ".join(details.get("lab_tests", [])[:4]) or "N/A"
        hyp_rows += f"""
        <tr>
          <td><strong>{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '  '} {h.get('name','')}</strong></td>
          <td style="text-align:center"><strong>{h.get('confidence',0):.1f}%</strong></td>
          <td style="text-align:center">{h.get('supporting',0)}</td>
          <td style="text-align:center">{h.get('contradicting',0)}</td>
          <td style="font-size:0.85em">{tests}</td>
        </tr>"""

    # Build evidence rows
    ev_rows = ""
    for e in evidence:
        supports = ", ".join(e.get("supports", [])[:3]) if e.get("supports") else "—"
        contradicts = ", ".join(e.get("contradicts", [])[:3]) if e.get("contradicts") else "—"
        ev_rows += f"""
        <tr>
          <td><strong>{(e.get('finding','')).replace('_',' ').title()}</strong></td>
          <td style="color:#16a34a">{supports}</td>
          <td style="color:#dc2626">{contradicts}</td>
        </tr>"""

    # Build conversation
    conv_html = ""
    for msg in conversation:
        role_label = "Patient" if msg.get("role") == "user" else "CuraBot"
        role_color = "#1e40af" if msg.get("role") == "user" else "#059669"
        conv_html += f'<p><strong style="color:{role_color}">{role_label}:</strong> {msg.get("content","")}</p>'

    # Red flags
    red_flags = top_details.get("red_flags", [])
    rf_html = "".join(f"<li>{rf}</li>" for rf in red_flags) if red_flags else "<li>None identified</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CuraBot Report — {top.get('name','')}</title>
<style>
  @media print {{ @page {{ margin: 1cm; }} body {{ -webkit-print-color-adjust: exact; }} }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1e293b; line-height: 1.6; padding: 2rem; max-width: 900px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #1e40af, #7c3aed); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
  .header p {{ opacity: 0.9; font-size: 0.9rem; }}
  .disclaimer {{ background: #fef2f2; border: 2px solid #fca5a5; border-radius: 8px; padding: 1rem; margin-bottom: 2rem; color: #991b1b; font-weight: 600; text-align: center; }}
  .section {{ margin-bottom: 2rem; }}
  .section h2 {{ font-size: 1.2rem; color: #1e40af; border-bottom: 2px solid #dbeafe; padding-bottom: 0.5rem; margin-bottom: 1rem; }}
  .primary-dx {{ background: #eff6ff; border: 2px solid #93c5fd; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }}
  .primary-dx h3 {{ font-size: 1.4rem; color: #1e40af; }}
  .primary-dx .confidence {{ font-size: 2rem; font-weight: 800; color: #16a34a; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
  th {{ background: #f1f5f9; text-align: left; padding: 0.6rem; font-size: 0.85rem; border-bottom: 2px solid #cbd5e1; }}
  td {{ padding: 0.6rem; border-bottom: 1px solid #e2e8f0; font-size: 0.85rem; }}
  .red-flags {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem; border-radius: 0 8px 8px 0; }}
  .red-flags h3 {{ color: #dc2626; }}
  .conversation {{ background: #f8fafc; border-radius: 8px; padding: 1rem; max-height: 400px; overflow: auto; }}
  .conversation p {{ margin-bottom: 0.5rem; font-size: 0.85rem; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 2px solid #e2e8f0; text-align: center; font-size: 0.8rem; color: #64748b; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .print-btn {{ background: #1e40af; color: white; border: none; padding: 0.75rem 2rem; border-radius: 8px; font-size: 1rem; cursor: pointer; margin-bottom: 1rem; }}
  .print-btn:hover {{ background: #1d4ed8; }}
  @media print {{ .print-btn {{ display: none; }} }}
</style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>

  <div class="header">
    <h1>CuraBot Diagnostic Report</h1>
    <p>Generated: {now} | Session: {session_id[:8]} | Iterations: {session.get('iteration',0)}</p>
  </div>

  <div class="disclaimer">WARNING: FOR MEDICAL EDUCATION ONLY — This is NOT a clinical diagnosis</div>

  <div class="primary-dx">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h3>Primary Diagnosis</h3>
        <div style="font-size:1.5rem;font-weight:700;margin-top:0.25rem">{top.get('name','Undetermined')}</div>
        <p style="color:#475569;margin-top:0.5rem">{top_details.get('description','')}</p>
      </div>
      <div class="confidence">{top.get('confidence',0):.1f}%</div>
    </div>
  </div>

  <div class="section">
    <h2>📋 Symptoms Identified ({len(symptoms)})</h2>
    <p>{', '.join(symptoms) if symptoms else 'None recorded'}</p>
  </div>

  <div class="section">
    <h2>📊 Differential Diagnosis Table</h2>
    <table>
      <thead><tr><th>Diagnosis</th><th>Confidence</th><th>Supporting</th><th>Contradicting</th><th>Recommended Tests</th></tr></thead>
      <tbody>{hyp_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>🔍 Evidence Ledger</h2>
    <table>
      <thead><tr><th>Finding</th><th>Supports</th><th>Contradicts</th></tr></thead>
      <tbody>{ev_rows}</tbody>
    </table>
  </div>

  <div class="section red-flags">
    <h3>🚨 Red Flags to Watch For</h3>
    <ul style="margin-top:0.5rem;padding-left:1.5rem">{rf_html}</ul>
  </div>

  <div class="section">
    <h2>🧪 Recommended Diagnostic Tests</h2>
    <p>{', '.join(top_details.get('lab_tests', [])) or 'N/A'}</p>
  </div>

  <div class="section">
    <h2>💬 Clinical Conversation</h2>
    <div class="conversation">{conv_html}</div>
  </div>

  <div class="footer">
    <p>CuraBot v2.0 — Agentic AI Differential Diagnosis Tutor | FOR MEDICAL EDUCATION ONLY</p>
    <p>This report was generated by a 6-agent AI pipeline for educational purposes and does not constitute medical advice.</p>
  </div>
</body>
</html>"""

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


# ==================== MEDICAL REPORTS ====================

@app.post("/api/upload-record")
@rate_limit("5/minute")
async def upload_record(
    request: Request,
    file: UploadFile = File(...),
    report_type: str = Form("lab_result"),
    user_id: str = Header(None, alias="x-user-id")
):
    """Upload a medical PDF, parse it, and index it for RAG"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # File size limit: 10MB max
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 10MB, got {len(content) / 1024 / 1024:.1f}MB")
        
    import pdfplumber
    import io
    
    # 1. Parse PDF text (content already read above for size check)
    try:
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse PDF file")
        
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in PDF")
        
    # 2. Upload physical file to cloud bucket (if configured)
    cloud_url = await supabase_service.upload_file_to_storage(
        file_bytes=content,
        file_name=f"{user_id}/{uuid.uuid4()}_{file.filename}",
        content_type=file.content_type or "application/pdf"
    )
    
    # 3. Save to database with physical file URL
    report_id = await supabase_service.save_medical_report(
        user_id=user_id,
        file_name=file.filename,
        report_type=report_type,
        extracted_text=extracted_text,
        parsed_data={"extracted_length": len(extracted_text)},
        file_url=cloud_url or ""
    )
    
    # 3. Chunk and embed into VectorStore for RAG
    # Using a simple chunking logic (e.g. splitting by double newlines or chunks of 500 chars)
    # This ensures exact clinical parameters stay somewhat together
    chunks = []
    current_chunk = ""
    for line in extracted_text.split('\n'):
        if len(current_chunk) + len(line) > 600:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
        
    indexing_status = "pending"
    chunk_count = 0
    
    if vector_store:
        try:
            chunk_count = vector_store.add_patient_records(
                user_id=user_id,
                report_id=report_id,
                source=file.filename,
                chunks=chunks
            )
            indexing_status = "success"
        except Exception as e:
            logger.error(f"Vector indexing failed: {e}")
            indexing_status = "failed"
    else:
        logger.warning("VectorStore not initialized, skipping indexing.")
        indexing_status = "skipped"
    
    return {
        "status": "success", 
        "report_id": report_id, 
        "filename": file.filename,
        "indexed_chunks": chunk_count,
        "indexing_status": indexing_status
    }

@app.get("/api/reports")
async def get_reports(user_id: str = Header(None, alias="x-user-id")):
    """Get medical reports for a user."""
    if not user_id:
        return {"reports": []}
    reports = await supabase_service.get_user_reports(user_id)
    return {"reports": reports}

@app.get("/api/admin/data-summary")
async def get_admin_data_summary(
    user_id: str = Header(None, alias="x-user-id")
):
    """Get counts of all data stored in the database for verification."""
    # Basic admin auth check — in production, use proper admin role verification
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not supabase_service.client:
        return {"error": "Supabase client not initialized or using local storage"}
        
    try:
        # Fetch counts directly from tables
        users_count = supabase_service.client.table('users').select('*', count='exact').limit(1).execute()
        sessions_count = supabase_service.client.table('chat_sessions').select('*', count='exact').limit(1).execute()
        messages_count = supabase_service.client.table('chat_messages').select('*', count='exact').limit(1).execute()
        reports_count = supabase_service.client.table('medical_reports').select('*', count='exact').limit(1).execute()
        diagnoses_count = supabase_service.client.table('diagnosis_history').select('*', count='exact').limit(1).execute()
        
        # We can't easily count storage bucket files via API, but we can return table counts
        return {
            "status": "success",
            "storage_provider": "Supabase",
            "counts": {
                "total_users": users_count.count,
                "total_chat_sessions": sessions_count.count,
                "total_chat_messages": messages_count.count,
                "total_uploaded_reports_metadata": reports_count.count,
                "total_completed_diagnoses": diagnoses_count.count
            },
            "dashboard_message": "To view physical PDF files, look in Storage -> medical_reports bucket in Supabase dashboard."
        }
    except Exception as e:
        return {"error": f"Failed to fetch counts: {e}"}

# ==================== HEALTH & INFO ====================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "CuraBot",
        "version": "2.0.0",
        "status": "running",
        "agents": [
            "Symptom Normalizer (LLM)",
            "Hypothesis Generator (LLM + KB)",
            "Evidence Evaluator (LLM)",
            "Hypothesis Reviser (LLM + Bayesian)",
            "Diagnostic Strategist (LLM — dynamic questions)",
            "Self-Critique & Bias Check (LLM)"
        ],
        "disclaimer": "FOR MEDICAL EDUCATION ONLY",
        "features": [
            "LLM-powered dynamic questioning",
            "New/returning user context awareness",
            "Supabase persistent storage",
            "Confidence trajectory tracking",
            "Cognitive bias detection"
        ]
    }

@app.get("/health")
async def health():
    """Health check — returns system status for monitoring."""
    from services.llm_client import llm_client
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "llm_available": llm_client.is_available,
        "active_sessions": len(active_sessions),
        "storage_mode": "supabase" if not supabase_service.use_local else "local_sqlite",
        "vector_store": "active" if vector_store else "unavailable",
        "rate_limiting": "enabled" if _rate_limit_available else "disabled",
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("CuraBot v2.0 -- Agentic AI Diagnosis Tutor")
    print("=" * 60)
    print("Server:   http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Agents:   6 LLM-Powered")
    print("   1. Symptom Normalizer (Gemini)")
    print("   2. Hypothesis Generator (Gemini + Disease KB)")
    print("   3. Evidence Evaluator (Gemini)")
    print("   4. Hypothesis Reviser (Gemini + Bayesian)")
    print("   5. Diagnostic Strategist (dynamic questions)")
    print("   6. Self-Critique & Bias Check")
    print(f"Storage:  {'Supabase' if not supabase_service.use_local else 'Local SQLite'}")
    print("WARNING: FOR MEDICAL EDUCATION ONLY")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["*.log", "*.db", "*.sqlite3", "*.sqlite3-journal", "chroma_db"]
    )