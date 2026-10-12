FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libreoffice-writer \
    libreoffice-impress \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/api

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

COPY app ./app

EXPOSE 8000
