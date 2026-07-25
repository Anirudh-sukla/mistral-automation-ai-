# Nexus Godzilla — minimal backend (dev)

This repository contains a minimal scaffold for the Nexus Godzilla backend focused on the freelancing assistant. It is intended as a developer-friendly starting point for building a powerful assistant using a local-quantized model (Qwen3.5:4B) and SQLite for dev.

WARNING & NOTES
- Local quantized Qwen3.5:4B setup is non-trivial. See the `LOCAL MODEL` section below.
- This scaffold includes a deterministic fallback so you can demo the freelancing proposal endpoint even if the model is not configured.
- For production, replace SQLite with Postgres, add proper secrets management, and secure endpoints.

Quick status
- Minimal FastAPI app at `backend/main.py`
- Freelancing endpoints at `backend/freelancing/router.py` (/freelancing/proposal)
- Local-model loader stub at `backend/ai_engine/model_client.py`
- Prompt builder + deterministic fallback at `backend/ai_engine/prompt_engine.py`
- SQLite async engine + SQLAlchemy models in `backend/database/`

Quick start (developer machine)

1) Clone and enter repo

```bash
git clone https://github.com/Anirudh-sukla/mistral-automation-ai-.git
cd mistral-automation-ai-
```

2) Create a Python virtualenv and install deps

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
```

3) Configure env

```bash
cp backend/.env.example .env
# Edit .env to set MODEL_MODE=local and MODEL_PATH to your quantized model folder (if available)
```

4) Initialize the database (creates SQLite file and tables)

```bash
python - <<'PY'
import asyncio
from backend.database import init_db
asyncio.run(init_db())
print("DB initialized")
PY
```

5) Run the server

```bash
uvicorn backend.main:app --reload
```

6) Demo the proposal endpoint

```bash
curl -X POST "http://127.0.0.1:8000/freelancing/proposal" \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Acme Corp","project_summary":"Landing page + API","budget":"~₹40,000"}'
```

If a local model is not configured or fails to load, the endpoint will return a deterministic template proposal (useful for demos).

LOCAL MODEL
- Running a 4B quantized model on 8GB RAM is possible but requires proper quantization (4-bit) and optimized runtimes (AutoGPTQ + bnb, or GGML/gguf with llama.cpp-like runtimes).
- This scaffold's model client attempts to use transformers pipeline as a simple path, but for quantized Qwen3.5 you will likely need to follow the model vendor's quantization guide and use a specialized loader.

FUTURE STEPS
- Add remote-model fallback (OpenAI/Mistral cloud) for reliability.
- Implement authentication, rate-limiting, and API permissions.
- Add unit & integration tests and CI.

