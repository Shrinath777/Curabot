import asyncio
import os
import sys

# Add backend dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.orchestrator import orchestrator

async def test_emergency():
    print("--- TESTING EMERGENCY SCENARIO ---")
    response = await orchestrator.run_pipeline(
        message="I have crushing chest pain and I can't breathe",
        session_state={"conversation_history": [], "accumulated_symptoms": {"primary_symptoms": [], "secondary_symptoms": []}, "iteration": 1, "is_new_user": True},
        user_context={}
    )
    print("Emergency response message:", response.get("message"))
    print("Should conclude:", response.get("should_conclude"))
    print("Agent thoughts:")
    for thought in response.get("agent_thoughts", []):
        print(f"  [{thought['agent']}] {thought['thought']}")
    
async def test_normal():
    print("\n--- TESTING NORMAL SCENARIO ---")
    response = await orchestrator.run_pipeline(
        message="I have a mild headache for the past two days",
        session_state={"conversation_history": [], "accumulated_symptoms": {"primary_symptoms": [], "secondary_symptoms": []}, "iteration": 1, "is_new_user": True},
        user_context={}
    )
    print("Normal response message:", response.get("message"))
    print("Should conclude:", response.get("should_conclude"))
    print("Agent thoughts:")
    for thought in response.get("agent_thoughts", []):
        print(f"  [{thought['agent']}] {thought['thought']}")

if __name__ == "__main__":
    asyncio.run(test_emergency())
    asyncio.run(test_normal())
