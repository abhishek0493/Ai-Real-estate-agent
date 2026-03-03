# ---- Base stage ----
FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ---- Production stage ----
FROM base AS production

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
