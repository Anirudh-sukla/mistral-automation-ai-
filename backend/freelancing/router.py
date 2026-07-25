from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.ai_engine import model_client, prompt_engine
from backend.database import AsyncSessionLocal
from backend.database.models import Proposal as ProposalModel
from sqlalchemy import select
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
        logger.exception("Model generation failed, using deterministic fallback: %s", e)
        text = prompt_engine.render_proposal_template(payload.client_name, payload.project_summary, payload.budget)

    # Save to DB (async)
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                proposal = ProposalModel(
                    client_name=payload.client_name,
                    project_summary=payload.project_summary,
                    proposal_text=text,
                )
                session.add(proposal)
    except Exception:
        logger.exception("Failed to save proposal to DB")

    return {"proposal": text}


@router.get("/proposals")
async def list_proposals(limit: int = 50):
    """List recent proposals saved in the DB."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ProposalModel).order_by(ProposalModel.created_at.desc()).limit(limit))
            rows = result.scalars().all()
            items = [
                {
                    "id": r.id,
                    "client_name": r.client_name,
                    "project_summary": r.project_summary,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            return {"proposals": items}
    except Exception as e:
        logger.exception("Failed to list proposals: %s", e)
        raise HTTPException(status_code=500, detail="DB error")
