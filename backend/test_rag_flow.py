import os
import sys
import logging
from typing import Dict, Any

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge.vector_store import VectorStore
from services.supabase_client import supabase_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_rag_and_history():
    """
    Verifies that History retrieval and PDF RAG are functional.
    """
    logger.info("Starting RAG & History Verification...")
    
    # 1. Test VectorStore Connection
    try:
        vs = VectorStore()
        logger.info("✅ VectorStore initialized.")
        
        # Test generic search (Diseases)
        results = vs.search_diseases("chest pain", n_results=1)
        if results:
            logger.info(f"✅ Disease Search Working. Found: {results[0]['name']}")
        else:
            logger.warning("❌ Disease Search returned no results.")
            
        # Test Patient Record Search (Mock User ID)
        mock_user_id = "test-user-rag-verification"
        pdf_results = vs.search_patient_records(user_id=mock_user_id, query="heart report")
        logger.info(f"ℹ️ Patient RAG Search (Mock ID): Found {len(pdf_results)} results.")
        
    except Exception as e:
        logger.error(f"❌ VectorStore Failure: {e}")

    # 2. Test Supabase History Connection
    try:
        # We try to get context for a known or mock user
        # This checks both cloud and local DB fallbacks
        context = await supabase_service.get_user_context("test-user-id")
        if context:
            logger.info("✅ Supabase/Local History Service active.")
            logger.info(f"ℹ️ Context Keys: {list(context.keys())}")
        else:
            logger.warning("❌ History Service returned empty context.")
            
    except Exception as e:
        logger.error(f"❌ History Service Failure: {e}")

    logger.info("Verification Complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_rag_and_history())
