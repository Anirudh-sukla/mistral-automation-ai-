"""
Prompt engine — keep templates and prompt-building logic here.
"""
from typing import Dict


def build_proposal_prompt(client_name: str, project_summary: str, budget: str = None) -> str:
    prompt = f"You are a professional freelance consultant.\nClient: {client_name}\nProject: {project_summary}\n\nProduce a concise, professional proposal including:\n- Summary of client needs\n- Proposed solution and deliverables\n- Timeline (weeks)\n- Pricing and payment milestones\n- Call-to-action and next steps\n\nRespond in clear English."
    if budget:
        prompt += f"\nBudget hint: {budget}"
    return prompt


def render_proposal_template(client_name: str, project_summary: str, budget: str = None) -> str:
    """Deterministic template used when the LLM is unavailable. Keeps output structured and demo-friendly.
    """
    lines = []
    lines.append(f"Proposal for {client_name}\n")
    lines.append("Summary of client needs:")
    lines.append(f"- {project_summary}\n")
    lines.append("Proposed solution and deliverables:")
    lines.append("- Deliverable 1: Initial design and landing page implementation")
    lines.append("- Deliverable 2: API integration and basic backend endpoints")
    lines.append("- Deliverable 3: Testing and deployment guidance\n")
    lines.append("Timeline:")
    lines.append("- Week 1: Requirements & design\n- Week 2-3: Implementation\n- Week 4: Testing & handover\n")
    if budget:
        lines.append(f"Pricing (estimated): {budget}\n")
        lines.append("Payment milestones:\n- 30% upfront\n- 50% on delivery\n- 20% on acceptance\n")
    else:
        lines.append("Pricing: To be agreed. Provide a budget range for an estimate.\n")
    lines.append("Next steps:\n- Accept proposal or schedule a 30-min call to refine requirements\n")

    return "\n".join(lines)
