# Prompt Versioning Strategy

Prompts are versioned similar to APIs.

# Goals

- Track changes
- Allow rollback
- Compare performance
- Enable A/B testing in future

# Implementation

Each tenant can have:

- active_prompt_version (default: v1)

AI Orchestrator loads prompt based on:

tenant.active_prompt_version

# Prompt Storage

Prompts stored in:

backend/app/ai/prompts/{version}/

# Metadata Table

PromptVersion

- id
- version_name
- description
- created_at
- is_active

# Design Principle

Prompt changes must not require code changes.

Prompt builder dynamically loads prompt files.
