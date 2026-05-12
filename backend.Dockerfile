FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY sprintcycle ./sprintcycle

RUN pip install --upgrade pip setuptools wheel && pip install -e ".[dashboard]"

EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["python", "-m", "uvicorn", "sprintcycle.dashboard.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
