"""
Test script to verify dynamic questioning and redundancy checks.
It simulates a 4-turn conversation about chest pain to see if the bot repeats itself
or uses robotic predefined templates.
"""
import asyncio
import httpx
import time

API = "http://localhost:8000"

async def main():
    print("=" * 60)
    print("Testing CuraBot Dynamic Questioning & Redundancy")
    print("=" * 60 + "\n")

    messages = [
        "I'm feeling really terrible, my chest hurts a lot.",
        "It feels like a heavy weight sitting on my chest, not sharp at all.",
        "It started about 30 minutes ago while I was climbing the stairs.",
        "No, the pain isn't moving anywhere else, it's just in the center."
    ]

    session_id = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, msg in enumerate(messages):
            print(f"Patient (Turn {i+1}): {msg}")
            
            payload = {
                "message": msg,
                "session_id": session_id,
                "user_id": None
            }
            
            t0 = time.time()
            try:
                r = await client.post(f"{API}/api/chat", json=payload)
                elapsed = time.time() - t0
                
                if r.status_code == 200:
                    data = r.json()
                    session_id = data.get("session_id")
                    
                    bot_reply = data.get("message", "").strip()
                    print(f"CuraBot (Took {elapsed:.1f}s):\n  -> {bot_reply}\n")
                    
                    # Print whether it concluded
                    if data.get("should_conclude"):
                        print("  [SYSTEM: Diagnosis Concluded]")
                        break
                else:
                    print(f"Error {r.status_code}: {r.text}")
                    break
            except Exception as e:
                print(f"Request failed: {e}")
                break

    print("=" * 60)
    print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(main())
