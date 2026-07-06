# CodeGuardian AI — Testing Guide

## Backend

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

The suite covers:

- Auth (register, login, refresh, RBAC)
- Projects (create from folder, ZIP, file, GitHub)
- Analyses (creation, status polling, re-run single agent)
- Reports (markdown, HTML, PDF, patch, bundle)
- Agents (each agent produces findings, schema is correct)
- MCP servers (filesystem, GitHub, SQLite)

## Frontend

```bash
cd frontend
npm install
npm run test
```

The Vitest suite covers:

- Auth provider state transitions
- API client retry / error mapping
- Severity chip / progress / health ring rendering
- Chat send / receive flow

## Linting

```bash
# Python
ruff check backend/app
mypy backend/app

# TypeScript
cd frontend && npm run lint
```

## End-to-end smoke test

1. `docker compose up --build`
2. Visit `http://localhost:3000`.
3. Log in as `admin@codeguardian.ai` / `CodeGuardian!2026`.
4. Upload a small ZIP.
5. Verify that all agents run and findings appear.
6. Download the markdown report from `/reports`.

## Coverage

We aim for **80%+** coverage on the agents and services layer.
Coverage is reported via `pytest --cov=app`.
