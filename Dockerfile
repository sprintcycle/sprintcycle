FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY sprintcycle ./sprintcycle
COPY --from=frontend-builder /app/sprintcycle/dashboard/static ./sprintcycle/dashboard/static

RUN uv sync --frozen --extra full

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "sprintcycle.dashboard.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
