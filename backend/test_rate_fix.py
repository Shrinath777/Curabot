"""Quick test: send a chat message and verify the pipeline responds without 429 errors."""
import asyncio
import httpx
import time
import sys

API = "http://localhost:8000"

async def main():
    print("=" * 60)
    print("CuraBot Rate-Limit Fix Verification")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Health check
        print("\n[1/3] Health check...")
        r = await client.get(f"{API}/health")
        if r.status_code != 200:
            print(f"  ❌ Backend not reachable (status {r.status_code})")
            sys.exit(1)
        health = r.json()
        print(f"  ✅ Backend healthy  |  LLM available: {health.get('llm_available')}")

        # 2. Send a test chat message
        print("\n[2/3] Sending test chat message: 'I have a bad headache and feel dizzy'")
        t0 = time.time()
        r = await client.post(f"{API}/api/chat", json={
            "message": "I have a bad headache and feel dizzy",
            "session_id": None,
            "user_id": None
        })
        elapsed = time.time() - t0
        print(f"  Response status: {r.status_code}  |  Time: {elapsed:.1f}s")

        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Bot replied ({len(data.get('message',''))} chars)")
            print(f"  Message: {data['message'][:200]}...")
            print(f"  Hypotheses: {len(data.get('hypotheses', []))}")
            for h in data.get("hypotheses", [])[:3]:
                print(f"    - {h.get('name')}: {h.get('confidence')}%")
            print(f"  Agent thoughts: {len(data.get('agent_thoughts', []))}")
            print(f"  Iteration: {data.get('iteration')}")
            
            if elapsed < 30:
                print(f"\n  ✅ PASS — Response in {elapsed:.1f}s (under 30s target)")
            else:
                print(f"\n  ⚠️ SLOW — Response took {elapsed:.1f}s (target <30s)")
        else:
            print(f"  ❌ Error: {r.text[:300]}")

        # 3. Send a follow-up to test multi-turn
        print("\n[3/3] Sending follow-up: 'it's a throbbing pain on the left side'")
        t0 = time.time()
        r2 = await client.post(f"{API}/api/chat", json={
            "message": "it's a throbbing pain on the left side",
            "session_id": data.get("session_id") if r.status_code == 200 else None,
            "user_id": None
        })
        elapsed2 = time.time() - t0
        print(f"  Response status: {r2.status_code}  |  Time: {elapsed2:.1f}s")

        if r2.status_code == 200:
            data2 = r2.json()
            print(f"  ✅ Bot replied: {data2['message'][:200]}...")
            print(f"  Iteration: {data2.get('iteration')}")
        else:
            print(f"  ❌ Error: {r2.text[:300]}")

    print("\n" + "=" * 60)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
