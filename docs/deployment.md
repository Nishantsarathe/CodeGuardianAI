# CodeGuardian AI — Deployment Guide

This guide describes how to deploy CodeGuardian AI to a local
machine, a private server, or a Kubernetes cluster.

## 1. Prerequisites

| Component   | Version  | Notes                                      |
|-------------|----------|--------------------------------------------|
| Docker      | 24+      | Required for the recommended path.         |
| Docker Compose | 2.20+ | Bundled with Docker Desktop / Engine.      |
| Ollama      | 0.4+     | Pull a model: `ollama pull gemma2:2b`.     |
| Python      | 3.11+    | Only if you want to run from source.       |
| Node.js     | 20+      | Only if you want to run the frontend alone.|

## 2. Quickstart (Docker)

```bash
git clone https://github.com/your-org/codeguardian-ai.git
cd codeguardian-ai
cp .env.example .env
docker compose up --build
```

Once the stack is up:

- API    → http://localhost:8000
- UI     → http://localhost:3000
- Ollama → http://localhost:11434
- API docs → http://localhost:8000/docs

## 3. Local (no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve &        # in another terminal
ollama pull gemma2:2b
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

## 4. Environment variables

Copy `.env.example` to `.env` and adjust. Important keys:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=gemma2:2b
JWT_SECRET=<change-me>
SECRET_KEY=<change-me>
DATABASE_URL=sqlite:///./codeguardian.db
UPLOAD_DIR=./uploads
```

## 5. Production hardening

- Set `APP_ENV=production` and `APP_DEBUG=false`.
- Replace SQLite with PostgreSQL: `DATABASE_URL=postgresql+psycopg://...`.
- Run uvicorn behind Gunicorn + nginx.
- Configure log shipping (`/app/logs/codeguardian.log`).
- Restrict CORS to your frontend domain only.
- Mount `/uploads` and `/chroma_data` on persistent volumes.

## 6. Kubernetes (sketch)

- Build & push backend / frontend images.
- Mount PVCs for `uploads/`, `logs/`, `chroma_data/`.
- Expose via Ingress with TLS.
- Set `OLLAMA_BASE_URL` to the in-cluster Ollama service.

## 7. Troubleshooting

| Symptom                           | Fix                                                   |
|-----------------------------------|-------------------------------------------------------|
| `Cannot connect to Ollama`        | Run `ollama serve`; check `OLLAMA_BASE_URL`.          |
| 401 Unauthorized on every request | JWT secret rotated; users must re-login.              |
| `zip_slip`                        | Archive contains `..` entries; cleaned to fail safely.|
| Frontend cannot reach backend     | `NEXT_PUBLIC_API_URL` set, CORS allowed.              |
| Slow analysis                     | Use larger model; enable GPU; reduce `MAX_UPLOAD_MB`. |
