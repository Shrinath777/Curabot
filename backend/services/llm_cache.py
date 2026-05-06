"""
CuraBot LLM Response Cache
Caches all LLM responses to disk so identical prompts never consume API quota twice.
This makes the free tier go MUCH further.
"""

import os
import json
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "llm_cache"


class LLMCache:
    """Disk-based cache for LLM responses. Zero API calls for repeated prompts."""

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._memory_cache = {}
        self._load_stats()

    def _load_stats(self):
        """Count existing cached responses."""
        count = len(list(CACHE_DIR.glob("*.json")))
        if count > 0:
            logger.info(f"LLM Cache: {count} cached responses available (saves API quota)")

    def _hash_prompt(self, prompt: str) -> str:
        """Create a unique hash for a prompt."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def get(self, prompt: str) -> dict | None:
        """Get cached response for a prompt, or None if not cached."""
        key = self._hash_prompt(prompt)

        # Check memory first
        if key in self._memory_cache:
            logger.debug(f"LLM Cache HIT (memory): {key}")
            return self._memory_cache[key]

        # Check disk
        cache_file = CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._memory_cache[key] = data["response"]
                logger.debug(f"LLM Cache HIT (disk): {key}")
                return data["response"]
            except (json.JSONDecodeError, KeyError):
                pass

        return None

    def put(self, prompt: str, response: dict):
        """Cache a response for a prompt."""
        key = self._hash_prompt(prompt)
        self._memory_cache[key] = response

        cache_file = CACHE_DIR / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "prompt_hash": key,
                    "prompt_preview": prompt[:200],
                    "response": response
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    def clear(self):
        """Clear all cached responses."""
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()
        self._memory_cache.clear()
        logger.info("LLM Cache cleared")

    @property
    def size(self) -> int:
        return len(list(CACHE_DIR.glob("*.json")))


# Singleton
llm_cache = LLMCache()
