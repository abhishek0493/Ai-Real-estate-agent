# Entities

Tenant

- id
- name
- api_key
- created_at

UserLead

- id
- tenant_id
- name
- email
- phone
- budget_min
- budget_max
- preferred_location
- status (INTERESTED / NOT_INTERESTED)
- created_at

Property

- id
- tenant_id
- location
- price
- bedrooms
- bathrooms
- square_feet
- available

Conversation

- id
- lead_id
- message
- sender_type (USER / AI)
- timestamp

# Indexing Strategy

- Index on tenant_id
- Index on price
- Index on location

# Future Extension

Enable pgvector extension in PostgreSQL.

Future Table:

PropertyEmbedding

- property_id
- embedding vector(1536)

Do not implement now.
Just ensure migration support exists.
