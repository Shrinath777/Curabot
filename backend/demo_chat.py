import asyncio
import json
import sys
import os

from services.orchestrator import orchestrator

async def run():
    session_state = {
        "iteration": 0,
        "conversation_history": [],
    }
    
    print("--- TURN 1 ---")
    msg1 = "I have sudden pain in my chest, it feels like pressure"
    print("User:", msg1)
    session_state["conversation_history"].append({"role": "user", "content": msg1})
    res = await orchestrator.run_pipeline(msg1, session_state)
    print("Bot:", res["message"])
    session_state["conversation_history"].append({"role": "assistant", "content": res["message"]})
    session_state["iteration"] = res["iteration"]
    
    responses = [
        "Yes, I am sweating a lot and also have trouble breathing.",
        "It radiates to my left arm.",
        "I am 55 years old and I have high blood pressure.",
        "Yes, the pain is radiating."
    ]
    
    for i, msg in enumerate(responses):
        print(f"\n--- TURN {i+2} ---")
        print("User:", msg)
        session_state["conversation_history"].append({"role": "user", "content": msg})
        res = await orchestrator.run_pipeline(msg, session_state)
        print("Bot:", res["message"])
        
        top_hyps = res.get('hypotheses', [])[:2]
        if top_hyps:
            hyps_str = ", ".join([f"{h['name']} ({h['confidence']}%)" for h in top_hyps])
            print(f"Top 2 Hypotheses: {hyps_str}")
            
        session_state["conversation_history"].append({"role": "assistant", "content": res["message"]})
        session_state["iteration"] = res["iteration"]
        
        if res.get('should_conclude'):
            print(f"\n!!! DIAGNOSIS CONCLUDED !!!\n{res.get('conclusion_message')}")
            break

if __name__ == "__main__":
    asyncio.run(run())
