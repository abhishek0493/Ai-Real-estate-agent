# Multi-Tenant Isolation

- All queries scoped by tenant_id
- API key validation middleware
- JWT auth for dashboard

# Security Practices

- Rate limiting
- Input validation
- CORS control
- Environment variables for secrets
- Password hashing (bcrypt)
- SQL injection prevention via ORM

# Multi-Tenant Strategy

All queries must include tenant_id filter.

Enforce row-level access at application layer.

Optional future: PostgreSQL Row-Level Security (RLS).
