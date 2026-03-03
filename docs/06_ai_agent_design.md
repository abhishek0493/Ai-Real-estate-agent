# AI Orchestration Philosophy

The LLM is a reasoning engine only.
It must NOT:

- Directly query the database
- Perform business logic
- Modify system state independently

All system changes must go through validated backend tools.

# Architecture

AI Layer Components:

1. Prompt Builder
2. Tool Registry
3. Tool Validator
4. Conversation State Manager
5. Response Formatter

# Conversation State Machine

States:

- INIT
- COLLECTING_REQUIREMENTS
- VALIDATING_BUDGET
- MATCHING_PROPERTIES
- NEGOTIATING
- CONFIRMING
- CLOSED

State transitions must be deterministic and stored in Redis.

# Tool Contracts

Each tool must have:

- Input schema (Pydantic)
- Output schema
- Strict validation
- Error handling

# Negotiation Engine

Budget negotiation should NOT rely entirely on LLM.

Implement deterministic rules:

If user_budget < property_price by <= 5%:
attempt upsell messaging
If > 15% difference:
suggest alternative properties

# AI Orchestrator Design

LLM is only used for reasoning and structured tool invocation.

The backend controls:

- State transitions
- Validation
- Database writes
- Negotiation rules

# Tools

get_matching_properties(filters)
create_or_update_lead(data)
update_lead_status(status)
store_conversation(message)

# Execution Flow

1. Receive user message
2. Retrieve conversation state from Redis
3. Build structured prompt
4. Call LLM with function definitions
5. Validate returned tool call
6. Execute tool via backend service
7. Persist changes
8. Return structured response

# Prompt Builder

Load system prompt dynamically based on tenant settings.

# Prompt Structure

System Prompt:

- Business rules
- Allowed tool calls
- Response formatting requirements

Conversation Prompt:

- Chat history (last N messages)
- Current state
- Structured schema instructions

# Future RAG Extension

Design abstraction:

interface KnowledgeRetriever:
retrieve(query: str) -> list[ContextChunk]

Implement stub now.
Later integrate pgvector.
