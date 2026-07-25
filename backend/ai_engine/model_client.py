"""
Simple model client with local-quantized fallback.

This module attempts to load a local quantized model (AutoGPTQ / transformers) when
MODEL_MODE=local and MODEL_PATH is provided. For 8GB RAM machines you will likely
need an 4-bit quantized model and CPU-optimized runtime (ex: GGML/llama.cpp or
AutoGPTQ with bnb on CPU). Getting Qwen3.5:4B quantized artifacts requires
following the model's quantization guide (not included here).

If local loading fails, the client will try to fall back to a remote provider if
configured (not implemented automatically here).
"""
from typing import Optional
import os
import logging

logger = logging.getLogger("model_client")

MODEL_MODE = os.getenv("MODEL_MODE", "local")
MODEL_PATH = os.getenv("MODEL_PATH", "")

# Lazy imports — keep startup fast when dependencies not installed
_transformers_available = False
try:
    import torch
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
        # NOTE: For quantized models you might need AutoGPTQ or custom loading.
        # Here we try a standard transformers pipeline which will work for
        # non-quantized models or if the quantized model is supported by the
        # installed libs.
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
        # pipeline returns a list of generation dicts
        return out[0]["generated_text"]


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
    # Future: fallback to remote provider if configured
    return None


def generate_text(prompt: str, max_tokens: int = 256) -> str:
    """Generate text using local model if available, else raise informative error.

    For production you should implement a remote API fallback and better error handling.
    """
    client = get_client()
    if client:
        return client.generate(prompt, max_tokens=max_tokens)
    raise RuntimeError("No model available. Configure a local quantized model or remote API.")
