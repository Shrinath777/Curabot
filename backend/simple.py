from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "CuraBot API",
        "status": "running",
        "message": "Simple test version"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "now"}

@app.post("/chat")
async def chat(request: dict):
    message = request.get("message", "")
    session_id = request.get("session_id", "new")
    
    # Simple response
    return {
        "session_id": session_id,
        "hypotheses": [
            {
                "name": "Sample Diagnosis 1",
                "confidence": random.randint(60, 90),
                "supporting": random.randint(2, 5),
                "contradicting": random.randint(0, 2)
            },
            {
                "name": "Sample Diagnosis 2",
                "confidence": random.randint(30, 50),
                "supporting": random.randint(1, 3),
                "contradicting": random.randint(1, 3)
            }
        ],
        "suggested_questions": [
            "Can you describe the pain?",
            "When did this start?",
            "Any other symptoms?"
        ],
        "evidence": [
            {
                "finding": "chest_pain",
                "supports": ["Sample Diagnosis 1"],
                "contradicts": ["Sample Diagnosis 2"],
                "confidence": 0.9
            }
        ],
        "bias_flags": [],
        "iteration": 1,
        "need_more_info": True,
        "agent_thoughts": [
            {
                "agent": "SymptomNormalizer",
                "thought": "Analyzing symptoms...",
                "timestamp": "now"
            }
        ],
        "disclaimer": "FOR MEDICAL EDUCATION ONLY"
    }

@app.post("/reset")
async def reset():
    return {"status": "reset"}

if __name__ == "__main__":
    print("Simple CuraBot Backend")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=8000)