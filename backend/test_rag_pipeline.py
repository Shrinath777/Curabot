import requests
import sys
import json
import time

BASE_URL = "http://127.0.0.1:8001"
USER_ID = "rag_test_user_001"
SESSION_ID = "rag_session_001"

print("="*50)
print("1. SIMULATING PDF RAG UPLOAD")
print("="*50)

# 1. Upload the Diabetic Ketoacidosis synthetic report
pdf_path = "synthetic_records/James_Smith_BASIC.pdf"
try:
    files = {"file": open(pdf_path, "rb")}
except FileNotFoundError:
    print(f"Error: Could not find {pdf_path}")
    sys.exit(1)

upload_url = f"{BASE_URL}/api/upload-record"
headers = {"x-user-id": USER_ID}
data = {"report_type": "lab_result"}

try:
    print(f"Uploading {pdf_path} to {upload_url}...")
    res = requests.post(upload_url, headers=headers, files=files, data=data)
    print("Upload Status:", res.status_code)
    print("Upload Response:", res.json())
except Exception as e:
    print("Upload failed:", e)
    sys.exit(1)

print("\n" + "="*50)
print("2. SIMULATING DIAGNOSTIC CHAT FOR THIS PATIENT")
print("="*50)

# 2. Initiate chat conversation with symptoms typical of DKA
chat_url = f"{BASE_URL}/api/chat"
payload = {
    "session_id": SESSION_ID,
    "message": "I've been extremely thirsty lately, peeing all the time. I also feel confused and dizzy when standing up.",
    "context": {"age": 19, "gender": "Male"}
}

try:
    print("Sending symptoms to agent orchestrator...")
    chat_res = requests.post(chat_url, headers=headers, json=payload, timeout=60)
    print("Chat Request Status:", chat_res.status_code)
    
    response_data = chat_res.json()
    print("\n---------------- AGENT RESPONSE ----------------")
    print(response_data.get("response", "No response found"))
    print("\n---------------- HYPOTHESES TRACKED ----------------")
    hyps = response_data.get("debug_info", {}).get("hypotheses", [])
    if isinstance(hyps, list):
        for h in hyps[:3]:
            print(f"- {h.get('name')}: {h.get('confidence')}% (Reason: {h.get('reasoning')})")
    
except Exception as e:
    print("Chat simulation failed:", e)
