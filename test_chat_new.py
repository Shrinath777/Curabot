import requests
import uuid

API_URL = "http://localhost:8000/chat"
session_id = f"test-session-{uuid.uuid4()}"

def turn(turn_num, message):
    print(f"\n=== TURN {turn_num} ===")
    print(f"User: {message}")
    resp = requests.post(API_URL, json={"message": message, "session_id": session_id})
    data = resp.json()
    print(f"Iteration: {data.get('iteration')}")
    print(f"System Question: {data.get('message')}")
    
    top_hyps = data.get('hypotheses', [])[:2]
    if top_hyps:
        hyps_str = ", ".join([f"{h['name']} ({h['confidence']}%)" for h in top_hyps])
        print(f"Top 2 Hypotheses: {hyps_str}")
        
    if data.get('should_conclude'):
        print(f"!!! DIAGNOSIS CONCLUDED !!!")

turn(1, "I have sudden pain in my forehead and high fever")
turn(2, "No, it's just normal pain")
turn(3, "I also have knee pain")
