import asyncio
import os
import json
from services.supabase_client import supabase_service
from services.llm_client import llm_client
from services.orchestrator import orchestrator

async def verify_aura_reliability():
    """
    Verification script for Cloud Connectivity and Doctor-Like Logic.
    """
    print("=" * 60)
    print("AURA RELIABILITY & CLOUD VERIFICATION")
    print("=" * 60)

    # 1. Verify Cloud (Supabase) Connection
    print("\n[STEP 1] Testing Cloud (Supabase) Connectivity...")
    is_local = supabase_service.use_local
    if is_local:
        print("  ❌ WARNING: System is running in LOCAL mode (SQLite).")
        print("     To enable Cloud, ensure SUPABASE_URL and SUPABASE_ANON_KEY are in .env")
    else:
        print(f"  ✅ SUCCESS: System is connected to CLOUD (Supabase).")
        print(f"     URL: {supabase_service.supabase_url}")
        
    # 2. Verify Cloud Persistence (Write/Read Test)
    print("\n[STEP 2] Verifying Cloud Persistence...")
    test_user_id = "test-verification-user"
    test_session_id = f"test-session-{int(asyncio.get_event_loop().time())}"
    
    try:
        # Create a test session
        await supabase_service.create_session(user_id=test_user_id, session_id=test_session_id, title="Aura Verification Test")
        # Save a test message
        msg_id = await supabase_service.save_message(test_session_id, "user", "I have sharp chest pain.")
        # Retrieve the message
        messages = await supabase_service.get_session_messages(test_session_id)
        
        if any(m['content'] == "I have sharp chest pain." for m in messages):
            print(f"  ✅ SUCCESS: Cloud Write/Read verified (Msg ID: {msg_id})")
        else:
            print("  ❌ FAILURE: Message not found in cloud.")
    except Exception as e:
        print(f"  ❌ FAILURE: Cloud test error: {e}")

    # 3. Verify Realistic Doctor Logic (RULE-02: Redundancy & RULE-04: Differentiation)
    print("\n[STEP 3] Verifying 'Doctor-Like' Questioning (SOPs)...")
    print("  Input: 'i am feeling sharp sudden pain in the chest'")
    
    try:
        # Simulate a message process
        # We'll mock the session to reset for this test
        session_state = {
            "conversation_history": [],
            "vitals": {},
            "iteration": 0
        }
        
        # Run the pipeline - using fake user context
        result = await orchestrator.run_pipeline(
            message="i am feeling sharp sudden pain in the chest",
            session_state=session_state,
            user_context={"is_returning_user": False}
        )
        
        bot_reply = result.get("message", "")
        print(f"  AURA REPLY: \"{bot_reply}\"")
        
        # RULE-02 CHECK: Did she ask "is it sharp or dull?"
        forbidden_questions = ["sharp, dull, burning", "is it sharp", "character of your pain"]
        violated_sop002 = any(q in bot_reply.lower() for q in forbidden_questions)
        
        if violated_sop002:
            print("  ❌ FAILURE: RULE-02 Violated! Aura asked for information already provided ('sharp').")
        else:
            print("  ✅ SUCCESS: RULE-02 Followed. Aura acknowledged the 'sharp' nature and moved to the next step.")
            
        # SOP-004 CHECK: Is it a differentiation question?
        if "?" in bot_reply:
             print("  ✅ SUCCESS: Aura is asking a focused question to differentiate hypotheses.")
        else:
             print("  ❌ WARNING: Aura did not ask a clear next question.")

    except Exception as e:
        print(f"  ❌ FAILURE: Pipeline test error: {e}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_aura_reliability())
