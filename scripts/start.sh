#!/usr/bin/env bash
# Start CodeGuardian AI locally.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}"}/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "[start] .env not found — copying from .env.example"
  cp .env.example .env
  echo "[start] ⚠️  Edit .env and set SECRET_KEY and JWT_SECRET before running in production."
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "[start] ⚠️  Ollama not found. Install from https://ollama.com/download"
fi

echo "[start] Pulling Ollama model (best effort)..."
ollama pull gemma2:2b || true

echo "[start] Starting Docker Compose stack..."
docker compose -f docker/docker-compose.yml up --build
