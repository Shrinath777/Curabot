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
    msg1 = "I have a headache and a fever"
    session_state["conversation_history"].append({"role": "user", "content": msg1})
    res = await orchestrator.run_pipeline(msg1, session_state)
    print("Bot:", res["message"])
    session_state["conversation_history"].append({"role": "assistant", "content": res["message"]})
    session_state["iteration"] = res["iteration"]
    
    print("\n--- TURN 2 ---")
    msg2 = "The headache is mostly at the front"
    session_state["conversation_history"].append({"role": "user", "content": msg2})
    res = await orchestrator.run_pipeline(msg2, session_state)
    print("Bot:", res["message"])
    
if __name__ == "__main__":
    asyncio.run(run())
