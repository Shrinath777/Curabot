import os
import json
import time
import asyncio
import logging
import traceback
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
import httpx
from google import genai
from google.genai import types
from services.llm_cache import llm_cache

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)
logger = logging.getLogger(__name__)

OPENROUTER_FALLBACK_MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-27b-it:free"
]

class LLMClient:
    _api_lock = asyncio.Lock()
    PACING_SECONDS = 2.0  # Increased pacing to avoid 429 rate limits on free tier
    MODEL_RESET_INTERVAL = 90.0

    def __init__(self):
        # Gemini: Support multiple API keys for rotation
        self.gemini_keys = []
        for key_name in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4"]:
            key = os.getenv(key_name, "")
            if key:
                self.gemini_keys.append(key)
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._current_gemini_idx = 0
        self._gemini_exhausted = set()  # Track which key indices are exhausted
        
        # Initialize first Gemini client
        self.gemini_key = self.gemini_keys[0] if self.gemini_keys else ""
        if self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
            logger.info(f"Gemini LLM initialized with {len(self.gemini_keys)} API key(s), model: {self.gemini_model}")
        
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = "llama-3.3-70b-versatile"
        
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv("LLM_MODEL", OPENROUTER_FALLBACK_MODELS[0])

        # SambaNova: Free cloud LLM provider
        self.sambanova_key = os.getenv("SAMBANOVA_API_KEY", "")
        self.sambanova_model = "Meta-Llama-3.1-8B-Instant"

        # DeepSeek Official API: Free tokens on signup, excellent reasoning
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        # Cerebras: 1M tokens/day FREE, ultra-fast inference
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY", "")
        self.cerebras_model = os.getenv("CEREBRAS_MODEL", "llama-3.3-70b")

        # Ollama local LLM (optional — if user installs it)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
        self._ollama_available = None
        
        self._initialized = bool(self.gemini_keys or self.groq_key or self.openrouter_key or self.sambanova_key or self.deepseek_key or self.cerebras_key)
        self._exhausted_models: set = set()
        self._last_model_reset = time.time()
        
        if self.groq_key:
            logger.info(f"Groq LLM initialized with model: {self.groq_model}")
        if self.sambanova_key:
            logger.info(f"SambaNova LLM initialized with model: {self.sambanova_model}")
        if self.deepseek_key:
            logger.info(f"DeepSeek LLM initialized with model: {self.deepseek_model}")
        if self.cerebras_key:
            logger.info(f"Cerebras LLM initialized with model: {self.cerebras_model}")
        if self.openrouter_key:
            logger.info(f"OpenRouter LLM initialized with model: {self.openrouter_model}")

        if not self._initialized:
            logger.warning("No cloud API keys found. Will try Ollama local LLM.")

    @property
    def is_available(self) -> bool:
        return self._initialized or self._ollama_available is not False

    def _maybe_reset_exhausted_models(self):
        now = time.time()
        if self._exhausted_models and (now - self._last_model_reset) > self.MODEL_RESET_INTERVAL:
            logger.info(f"Resetting exhausted LLM models after cooldown.")
            self._exhausted_models.clear()
            self._gemini_exhausted.clear()
            self._current_gemini_idx = 0
            if self.gemini_keys:
                self.gemini_key = self.gemini_keys[0]
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            self._last_model_reset = now

    def _rotate_gemini_key(self):
        """Rotate to the next available Gemini API key."""
        self._gemini_exhausted.add(self._current_gemini_idx)
        
        for i in range(len(self.gemini_keys)):
            next_idx = (self._current_gemini_idx + 1 + i) % len(self.gemini_keys)
            if next_idx not in self._gemini_exhausted:
                self._current_gemini_idx = next_idx
                self.gemini_key = self.gemini_keys[next_idx]
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                logger.info(f"Rotated to Gemini key #{next_idx + 1}/{len(self.gemini_keys)}")
                return True
        
        # All keys exhausted
        logger.warning(f"All {len(self.gemini_keys)} Gemini keys exhausted")
        self._exhausted_models.add("gemini")
        return False

    async def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    logger.info(f"Ollama detected! Available models: {model_names}")
                    self._ollama_available = True
                    return True
        except Exception:
            pass
        self._ollama_available = False
        return False

    async def _async_generate_ollama(self, full_prompt: str, expect_json: bool) -> str:
        """Generate using local Ollama server (FREE, no API key)."""
        payload = {
            "model": self.ollama_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4096,
            }
        }
        if expect_json:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    async def _async_generate_gemini(self, full_prompt: str, expect_json: bool) -> str:
        response = await self.gemini_client.aio.models.generate_content(
            model=self.gemini_model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json" if expect_json else "text/plain",
                temperature=0.3
            )
        )
        return response.text.strip()

    async def _async_generate_groq(self, full_prompt: str, expect_json: bool) -> str:
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _async_generate_openrouter(self, full_prompt: str, expect_json: bool) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "CuraBot Local Dev",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openrouter_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3,
            "top_p": 0.85,
            "max_tokens": 4096
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _async_generate_sambanova(self, full_prompt: str, expect_json: bool) -> str:
        """Generate using SambaNova Cloud API (FREE tier)."""
        headers = {
            "Authorization": f"Bearer {self.sambanova_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.sambanova_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.sambanova.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _async_generate_deepseek(self, full_prompt: str, expect_json: bool) -> str:
        """Generate using DeepSeek Official API (free tokens on signup)."""
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.deepseek_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _async_generate_cerebras(self, full_prompt: str, expect_json: bool) -> str:
        """Generate using Cerebras Cloud API (1M tokens/day FREE, ultra-fast)."""
        headers = {
            "Authorization": f"Bearer {self.cerebras_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.cerebras_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _try_providers(self, full_prompt: str, expect_json: bool) -> str:
        # 0. Try Ollama if available (local, free, unlimited)
        if "ollama" not in self._exhausted_models and await self._check_ollama():
            try:
                result = await self._async_generate_ollama(full_prompt, expect_json)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Ollama local LLM failed: {e}")
                self._exhausted_models.add("ollama")

        # 1. Try Gemini (with automatic key rotation across 4 keys)
        if self.gemini_keys and "gemini" not in self._exhausted_models:
            try:
                return await self._async_generate_gemini(full_prompt, expect_json)
            except Exception as e:
                logger.warning(f"Gemini API key #{self._current_gemini_idx + 1} failed: {e}")
                if "429" in str(e) or "quota" in str(e).lower():
                    # Try rotating to next key
                    if not self._rotate_gemini_key():
                        pass  # All keys exhausted, move to next provider
                    else:
                        # Retry with new key
                        try:
                            return await self._async_generate_gemini(full_prompt, expect_json)
                        except Exception as e2:
                            logger.warning(f"Gemini rotated key also failed: {e2}")
                            if "429" in str(e2) or "quota" in str(e2).lower():
                                self._rotate_gemini_key()

        # 2. Try Groq
        if self.groq_key and "groq" not in self._exhausted_models:
            try:
                return await self._async_generate_groq(full_prompt, expect_json)
            except Exception as e:
                logger.warning(f"Groq API failed: {e}")
                if getattr(e, "response", None) and e.response.status_code == 429:
                    self._exhausted_models.add("groq")

        # 3. Try DeepSeek Official API (free tokens, great reasoning)
        if self.deepseek_key and "deepseek" not in self._exhausted_models:
            try:
                return await self._async_generate_deepseek(full_prompt, expect_json)
            except Exception as e:
                logger.warning(f"DeepSeek API failed: {e}")
                if getattr(e, "response", None) and getattr(e.response, "status_code", 0) in (429, 402):
                    self._exhausted_models.add("deepseek")

        # 4. Try Cerebras (1M tokens/day FREE, ultra-fast)
        if self.cerebras_key and "cerebras" not in self._exhausted_models:
            try:
                return await self._async_generate_cerebras(full_prompt, expect_json)
            except Exception as e:
                logger.warning(f"Cerebras API failed: {e}")
                if getattr(e, "response", None) and getattr(e.response, "status_code", 0) == 429:
                    self._exhausted_models.add("cerebras")

        # 5. Try SambaNova (free tier)
        if self.sambanova_key and "sambanova" not in self._exhausted_models:
            try:
                return await self._async_generate_sambanova(full_prompt, expect_json)
            except Exception as e:
                logger.warning(f"SambaNova API failed: {e}")
                if getattr(e, "response", None) and getattr(e.response, "status_code", 0) == 429:
                    self._exhausted_models.add("sambanova")

        # 6. Try OpenRouter (and its internal fallback models incl. DeepSeek:free)
        if self.openrouter_key and "openrouter" not in self._exhausted_models:
            for model in OPENROUTER_FALLBACK_MODELS:
                if model not in self._exhausted_models:
                    self.openrouter_model = model
                    try:
                        return await self._async_generate_openrouter(full_prompt, expect_json)
                    except Exception as e:
                        logger.warning(f"OpenRouter model {model} failed: {e}")
                        if getattr(e, "response", None) and e.response.status_code == 429:
                            self._exhausted_models.add(model)
            self._exhausted_models.add("openrouter")
            
        raise Exception("All configured LLM providers exhausted or unavailable.")

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        expect_json: bool = True,
        max_retries: int = 2,
        timeout_seconds: float = 90.0,
    ) -> Dict[str, Any]:
        
        if not self.is_available:
            return self._fallback_response(prompt)

        full_prompt = ""
        if system_instruction:
            full_prompt += f"{system_instruction}\n\n"
        full_prompt += prompt

        # Check cache FIRST — avoids burning API quota on repeated prompts
        cached = llm_cache.get(full_prompt)
        if cached is not None:
            logger.info("LLM Cache HIT — saved an API call!")
            return cached

        for attempt in range(max_retries):
            try:
                async with LLMClient._api_lock:
                    self._maybe_reset_exhausted_models()
                    await asyncio.sleep(self.PACING_SECONDS)
                    text = await self._try_providers(full_prompt, expect_json)

                if expect_json:
                    parsed = self._parse_json_response(text)
                    if parsed.get("parse_error"):
                        logger.warning(f"JSON parse failed, raw text: {text[:300]}")
                    else:
                        # Cache successful parsed responses
                        llm_cache.put(full_prompt, parsed)
                    return parsed
                else:
                    result = {"text": text}
                    llm_cache.put(full_prompt, result)
                    return result

            except Exception as e:
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    return self._fallback_response(prompt)

        return self._fallback_response(prompt)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        clean = text
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            parts = clean.split("```")
            if len(parts) >= 3:
                clean = parts[1].strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return {"items": json.loads(text[start:end])}
                except json.JSONDecodeError:
                    pass
            return {"text": text, "parse_error": True}

    def _fallback_response(self, prompt: str) -> Dict[str, Any]:
        return {
            "error": "LLM unavailable",
            "fallback": True,
            "text": "I'm currently unable to process this request. Please try again in a moment.",
            "primary_symptoms": [],
            "secondary_symptoms": [],
            "hypotheses": [],
            "evidence_ledger": [],
            "biases_detected": [],
            "alternative_considerations": [],
            "next_question": "Could you tell me more about your symptoms?",
            "should_conclude": False,
            "summary": "LLM unavailable, using fallback matching.",
            "reasoning": "Fallback reasoning due to OpenRouter limitation."
        }

llm_client = LLMClient()
