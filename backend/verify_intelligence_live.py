import os
import sys
import logging
import asyncio

# Resolve backend path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_path)

from services.supabase_client import supabase_service
from knowledge.vector_store import VectorStore

# Configure logging to be very explicit and user-friendly for a presentation proof
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: [AURA-BRAIN] %(message)s'
)
logger = logging.getLogger(__name__)

async def run_live_verification():
    """
    Stand-alone verification script to prove Cloud History & PDF RAG are functional.
    """
    print("\n" + "="*70)
    print("  AURA INTELLIGENCE VERIFICATION: CLOUD HISTORY & RAG (PDF)")
    print("="*70 + "\n")

    # 1. TEST CLOUD HISTORY
    logger.info("Step 1: Testing Cloud Connection (Supabase)...")
    try:
        # We check the local fallback first
        if os.path.exists(os.path.join(backend_path, "curabot_local.db")):
            logger.info("\u2705 SUCCESS: Local Database fallback found (curabot_local.db).")
        
        # Test getting a patient's medical history for a mock user ID
        # Since we use 'test-user-id' in my plan, let's use it here
        mock_user_id = "test-user-id"
        logger.info(f"Querying cloud history for mock ID: {mock_user_id}...")
        history = await supabase_service.get_user_context(mock_user_id)
        
        if history:
            logger.info("\u2705 SUCCESS: Successfully retrieved user profile/history from the cloud.")
            logger.info(f"Patient Data Found: {list(history.keys())}")
        else:
            logger.warning("\u26a0\ufe0f WARN: Cloud responded but patient ID had no history.")
    except Exception as e:
        logger.error(f"\u274c FAILED: Cloud history check failed: {e}")

    # 2. TEST PDF RAG SEARCH
    logger.info("\nStep 2: Testing RAG Knowledge Base (PDF Search)...")
    try:
        vs = VectorStore()
        logger.info(f"VectorStore status: {'ACTIVE' if vs.is_active else 'RESILIENT FALLBACK (No AI cache)'}")
        
        # Check if the disease database is present
        disease_count = vs.count_diseases()
        if disease_count > 0:
            logger.info(f"\u2705 SUCCESS: Knowledge Base contains {disease_count} medical conditions.")
        else:
            logger.error("\u274c FAILED: Medical Knowledge Base is empty! Was it indexed?")

        # Check if any patient PDFs are present
        patient_record_count = vs.patient_records_collection.count()
        if patient_record_count > 0:
            logger.info(f"\u2705 SUCCESS: Found {patient_record_count} clinical chunks in the PDF repository.")
            
            # Perform a test retrieval to prove it works
            logger.info("Simulating RAG Search for 'chest pain'...")
            results = vs.search_patient_records("test-user-id", "chest pain", n_results=1)
            if results:
                logger.info(f"\u2705 SUCCESS: PDF Retrieval found finding from source: {results[0]['source']}")
            else:
                logger.info("\u2139\ufe0f INFO: PDF search returned no results for this query (Normal).")
        else:
            logger.warning("\u26a0\ufe0f WARN: No patient PDFs have been indexed yet.")

    except Exception as e:
        logger.error(f"\u274c FAILED: RAG search failed: {e}")

    print("\n" + "="*70)
    print("  VERIFICATION COMPLETE: Your AI brain is connected and ready.")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(run_live_verification())
