"""
Enhanced model client with OpenAI remote fallback when local model is not available.
This keeps the existing local transformers loader but will call OpenAI's Chat Completions
API when MODEL_MODE!=local or local loading fails and OPENAI_API_KEY is set.
"""
from typing import Optional
import os
import logging
import json

import httpx

logger = logging.getLogger("model_client")

MODEL_MODE = os.getenv("MODEL_MODE", "local")
MODEL_PATH = os.getenv("MODEL_PATH", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Lazy imports — keep startup fast when dependencies not installed
_transformers_available = False
try:
    import torch  # noqa: F401
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    _transformers_available = True
except Exception:
    _transformers_available = False


class LocalModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.pipe = None
        self._load()

    def _load(self):
        if not _transformers_available:
            raise RuntimeError("transformers/torch not available in environment")
        logger.info("Loading local model from %s", self.model_path)
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_path, use_fast=True)
            model = AutoModelForCausalLM.from_pretrained(self.model_path, trust_remote_code=True)
            self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device_map="auto")
            logger.info("Loaded model into pipeline")
        except Exception as e:
            logger.exception("Failed to load model via transformers: %s", e)
            raise

    def generate(self, prompt: str, max_tokens: int = 256, **kwargs) -> str:
        if self.pipe is None:
            raise RuntimeError("Model pipeline not initialized")
        out = self.pipe(prompt, max_new_tokens=max_tokens, do_sample=False, **kwargs)
        return out[0].get("generated_text", "")


# Global client holder
_client: Optional[LocalModel] = None


def get_client() -> Optional[LocalModel]:
    global _client
    if _client is not None:
        return _client
    if MODEL_MODE == "local" and MODEL_PATH:
        try:
            _client = LocalModel(MODEL_PATH)
            return _client
        except Exception:
            logger.exception("Local model load failed")
            _client = None
    return None


# Remote OpenAI fallback
async def _openai_generate_async(prompt: str, max_tokens: int = 256) -> str:
    """Call OpenAI Chat Completions API via httpx (async).
    Requires OPENAI_API_KEY env var to be set.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured for remote generation")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        # Extract assistant content
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            logger.exception("Unexpected OpenAI response: %s", data)
            raise RuntimeError("OpenAI returned unexpected response")


def _openai_generate(prompt: str, max_tokens: int = 256) -> str:
    # sync wrapper
    import asyncio
    return asyncio.run(_openai_generate_async(prompt, max_tokens=max_tokens))


def generate_text(prompt: str, max_tokens: int = 256) -> str:
    """Generate text using local model if available, else try OpenAI remote fallback.

    Raises RuntimeError if no model available.
    """
    client = get_client()
    if client:
        try:
            return client.generate(prompt, max_tokens=max_tokens)
        except Exception:
            logger.exception("Local model generation failed, attempting remote fallback")
    # Try remote OpenAI fallback if key is present
    if OPENAI_API_KEY:
        try:
            return _openai_generate(prompt, max_tokens=max_tokens)
        except Exception:
            logger.exception("OpenAI generation failed")
    raise RuntimeError("No model available. Configure a local quantized model or set OPENAI_API_KEY for remote generation.")
