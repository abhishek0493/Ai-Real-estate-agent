"""Prompt builder — assembles system prompts for the LLM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.entities.lead import Lead, LeadStatus

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptBuilder:
    """Builds structured prompts for the LLM, injecting runtime context."""

    def __init__(self, version: str = "v1") -> None:
        self._version = version

    def _load_template(self, filename: str) -> str:
        path = _PROMPTS_DIR / self._version / filename
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def build_messages(
        self,
        lead: Lead,
        user_message: str,
        conversation_history: list[dict[str, str]],
        allowed_tools: list[str],
    ) -> list[dict[str, str]]:
        """Return the full message list to send to the LLM."""
        system_prompt = self._build_system_prompt(lead, allowed_tools)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Append recent history (last 20 messages max)
        for msg in conversation_history[-20:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})
        return messages

    def _build_system_prompt(self, lead: Lead, allowed_tools: list[str]) -> str:
        template = self._load_template("system_prompt.txt")

        # Show what we have collected and what is still missing
        collected = []
        missing = []

        if lead.preferred_location:
            collected.append(f"Location: {lead.preferred_location}")
        else:
            missing.append("Location (ask where they want to live)")

        if lead.budget_min is not None and lead.budget_max is not None:
            collected.append(f"Budget: ₹{lead.budget_min:,.0f} – ₹{lead.budget_max:,.0f}")
        else:
            missing.append("Budget range (ask for min and max)")

        if lead.bedrooms is not None:
            collected.append(f"Bedrooms: {lead.bedrooms} BHK")
        else:
            missing.append("Bedrooms (ask how many BHK)")

        if lead.preferences:
            collected.append(f"Preferences: {', '.join(lead.preferences)}")

        context_block = (
            f"\n\n--- CURRENT CONTEXT ---\n"
            f"Lead Name: {lead.name}\n"
            f"Lead Status: {lead.status.value}\n"
            f"\n"
            f"✅ Collected: {'; '.join(collected) if collected else 'Nothing yet'}\n"
            f"❓ Still needed: {'; '.join(missing) if missing else 'All required info collected!'}\n"
            f"\n"
            f"Allowed Tools: {', '.join(allowed_tools)}\n"
            f"--- END CONTEXT ---\n"
        )

        rules_block = (
            "\n\n--- RULES ---\n"
            "- Only call tools from the 'Allowed Tools' list.\n"
            "- Never fabricate property data.\n"
            "- Follow the state machine — invalid transitions will be rejected.\n"
            "- Collect ALL required info (location, budget, bedrooms) before validating budget.\n"
            "- If 'Still needed' shows missing fields, ask about them BEFORE calling any transition tools.\n"
            "- Validate budget before property matching.\n"
            "--- END RULES ---\n"
        )

        return template + context_block + rules_block
