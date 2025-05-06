FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      apt-transport-https \
      lsb-release \
      gnupg \
      && apt-get install -y azure-cli

COPY pyproject.toml uv.lock ./

RUN uv sync

WORKDIR /app

COPY .env .env
COPY *.py ./
COPY src/ ./src
COPY scripts/* ./
COPY assets/ ./assets
COPY .git/ ./.git