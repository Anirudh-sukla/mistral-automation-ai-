"""Prompt engine — keep templates and prompt-building logic here.
"""
from typing import Dict


def build_proposal_prompt(client_name: str, project_summary: str, budget: str = None) -> str:
    prompt = f"You are a professional freelance consultant.\nClient: {client_name}\nProject: {project_summary}\n\nProduce a concise, professional proposal including:\n- Summary of client needs\n- Proposed solution and deliverables\n- Timeline (weeks)\n- Pricing and payment milestones\n- Call-to-action and next steps\n\nRespond in clear English."
    if budget:
        prompt += f"\nBudget hint: {budget}"
    return prompt
