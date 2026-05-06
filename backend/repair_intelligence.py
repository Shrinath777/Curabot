import os
import shutil
import logging
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def repair_intelligence_model():
    """
    Clears the corrupted HuggingFace cache and re-downloads the embedding model.
    """
    model_name = "all-MiniLM-L6-v2"
    cache_root = os.path.expanduser("~/.cache/huggingface/hub")
    model_cache_path = os.path.join(cache_root, f"models--sentence-transformers--{model_name}")
    
    logger.info(f"Target model: {model_name}")
    
    # 1. Clear existing corrupted cache
    if os.path.exists(model_cache_path):
        logger.info(f"Clearing corrupted cache at: {model_cache_path}")
        try:
            shutil.rmtree(model_cache_path)
            logger.info("✅ Cache cleared successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return
    else:
        logger.info("No existing cache found for this model. Proceeding to fresh download.")

    # 2. Re-download model
    logger.info(f"Downloading fresh intelligence model '{model_name}'...")
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"✅ Model downloaded and verified: {model}")
        logger.info("Aura's Semantic Brain is now restored and ready for presentation!")
    except Exception as e:
        logger.error(f"❌ Failed to download model: {e}")
        logger.error("Please check your internet connection and try again.")

if __name__ == "__main__":
    repair_intelligence_model()
