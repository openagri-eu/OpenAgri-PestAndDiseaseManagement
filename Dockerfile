ARG SOURCE_REPO=https://github.com/openagri-eu/openagri-pestanddiseasemanagement

# ===========================================
# Stage 1: Builder
# ===========================================
FROM python:3.11-slim AS builder

WORKDIR /code

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /venv && \
    /venv/bin/pip install -U pip==24.0 && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# ===========================================
# Stage 2: Final Production Image
# ===========================================
FROM python:3.11-slim

ARG SOURCE_REPO
LABEL org.opencontainers.image.source=${SOURCE_REPO}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY data/ data/
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

ENV PATH="/venv/bin:$PATH"
