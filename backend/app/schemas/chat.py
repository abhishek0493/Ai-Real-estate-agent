"""Chat request/response schemas."""

from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Incoming chat message from a user."""

    message: str
    lead_id: UUID | None = None


class ChatResponse(BaseModel):
    """Response from the /chat endpoint."""

    assistant_message: str
    lead_id: UUID
    current_status: str
    tool_executed: str | None = None
    error: str | None = None
