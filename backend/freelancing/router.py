from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.ai_engine import model_client, prompt_engine
from backend.database import db
import logging

logger = logging.getLogger("freelancing.router")
router = APIRouter(prefix="/freelancing", tags=["freelancing"])


class ProposalRequest(BaseModel):
    client_name: str
    project_summary: str
    budget: str = None


@router.post("/proposal")
async def generate_proposal(payload: ProposalRequest):
    """Generate a proposal using the local quantized model (Qwen3.5:4B) if configured.

    Example request body:
    {
      "client_name": "Acme Corp",
      "project_summary": "We need a landing page and basic API integration",
      "budget": "~₹40,000"
    }
    """
    prompt = prompt_engine.build_proposal_prompt(payload.client_name, payload.project_summary, payload.budget)
    try:
        text = model_client.generate_text(prompt, max_tokens=512)
    except Exception as e:
        logger.exception("Model generation failed")
        raise HTTPException(status_code=500, detail=str(e))

    # Optionally save to DB (stub)
    try:
        # db.save_proposal(...)  # implement persistence as needed
        pass
    except Exception:
        logger.exception("Failed to save proposal to DB (not implemented)")

    return {"proposal": text}


@router.get("/discover/sample")
async def discover_sample():
    return {"message": "Client discovery module not implemented yet. Add crawler/integration to enable."}
