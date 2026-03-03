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

        context_block = (
            f"\n\n--- CURRENT CONTEXT ---\n"
            f"Lead Name: {lead.name}\n"
            f"Lead Status: {lead.status.value}\n"
            f"Budget: {lead.budget_min} - {lead.budget_max}\n"
            f"Location: {lead.preferred_location}\n"
            f"Allowed Tools: {', '.join(allowed_tools)}\n"
            f"--- END CONTEXT ---\n"
        )

        rules_block = (
            "\n\n--- RULES ---\n"
            "- Only call tools from the 'Allowed Tools' list.\n"
            "- Never fabricate property data.\n"
            "- Follow the state machine — invalid transitions will be rejected.\n"
            "- Collect requirements before validating budget.\n"
            "- Validate budget before property matching.\n"
            "--- END RULES ---\n"
        )

        return template + context_block + rules_block
