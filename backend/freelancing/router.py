from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from backend.ai_engine import model_client, prompt_engine
from backend.database import AsyncSessionLocal
from backend.database.models import Proposal as ProposalModel, ClientLead as ClientLeadModel
from sqlalchemy import select
import logging
from typing import List, Optional
from datetime import datetime
from backend.email_client import send_email

logger = logging.getLogger("freelancing.router")
router = APIRouter(prefix="/freelancing", tags=["freelancing"])


class ProposalRequest(BaseModel):
    client_name: str
    project_summary: str
    budget: Optional[str] = None


class LeadCreate(BaseModel):
    name: str
    source: Optional[str] = None
    data: Optional[str] = None


@router.post("/proposal")
async def generate_proposal(payload: ProposalRequest):
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
                    status="draft",
                )
                session.add(proposal)
    except Exception:
        logger.exception("Failed to save proposal to DB")

    return {"proposal": text}


@router.get("/proposals")
async def list_proposals(limit: int = 50):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ProposalModel).order_by(ProposalModel.created_at.desc()).limit(limit))
            rows = result.scalars().all()
            items = [
                {
                    "id": r.id,
                    "client_name": r.client_name,
                    "project_summary": r.project_summary,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            return {"proposals": items}
    except Exception as e:
        logger.exception("Failed to list proposals: %s", e)
        raise HTTPException(status_code=500, detail="DB error")


@router.post("/leads")
async def create_lead(payload: LeadCreate):
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                lead = ClientLeadModel(name=payload.name, source=payload.source, data=payload.data)
                session.add(lead)
    except Exception:
        logger.exception("Failed to save lead to DB")
        raise HTTPException(status_code=500, detail="DB error")
    return {"status": "ok"}


@router.get("/leads")
async def list_leads(limit: int = 100):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ClientLeadModel).order_by(ClientLeadModel.created_at.desc()).limit(limit))
            rows = result.scalars().all()
            items = [
                {"id": r.id, "name": r.name, "source": r.source, "created_at": r.created_at.isoformat() if r.created_at else None}
                for r in rows
            ]
            return {"leads": items}
    except Exception as e:
        logger.exception("Failed to list leads: %s", e)
        raise HTTPException(status_code=500, detail="DB error")


class SendRequest(BaseModel):
    to_email: EmailStr
    subject: Optional[str] = None


@router.post("/send/{proposal_id}")
async def send_proposal(proposal_id: int, payload: SendRequest):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ProposalModel).where(ProposalModel.id == proposal_id))
            proposal = result.scalars().first()
            if not proposal:
                raise HTTPException(status_code=404, detail="Proposal not found")
            subject = payload.subject or f"Proposal from {proposal.client_name}"
            body = proposal.proposal_text
            # send email (may raise)
            send_email(subject, body, payload.to_email)
            # mark as sent
            proposal.status = "sent"
            proposal.sent_to = payload.to_email
            proposal.sent_at = datetime.utcnow()
            async with session.begin():
                session.add(proposal)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to send proposal: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send proposal")

    return {"status": "sent"}
