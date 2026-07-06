# 🛡️ CodeGuardian AI

> **Autonomous Multi-Agent Code Review & Security Platform**

[![CI](https://github.com/your-org/codeguardian-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/codeguardian-ai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

CodeGuardian AI is a next-generation, autonomous multi-agent platform that combines the power of **GitHub Copilot + SonarQube + CodeRabbit + Snyk** into a single, locally-runnable application. It reviews code, detects bugs, finds security vulnerabilities, generates documentation, suggests refactoring, creates unit tests, and visualizes architecture — all powered by autonomous AI agents that collaborate to ship production-ready software.

> Built for the **Kaggle AI Agents Intensive – Vibe Coding Capstone**.

---

## ✨ Highlights

- 🧠 **10 Autonomous AI Agents** collaborating through a Coordinator
- 🔒 **Local-first** — runs entirely on Ollama (Gemma / Qwen) with no data leaving your machine
- 🏛️ **Clean Architecture** — strict separation of Frontend, Backend, Agents, Services
- 🎨 **Premium UI** — Glassmorphism, dark theme, Framer Motion animations
- 📊 **Production Dashboards** — Security, Quality, Bugs, Architecture, Dependencies
- 🐳 **One-command deploy** — `docker compose up` and you're running
- 🧪 **Auto-generated tests, docs, UML, refactor plans, and Git patches**

---

## 🚀 Features

### Multi-Agent System
| Agent | Role |
|-------|------|
| **Coordinator** | Plans, delegates, validates, merges |
| **Code Review** | Quality, complexity, code smells, scoring |
| **Security** | SQLi, XSS, CVSS scoring, secret scanning |
| **Bug Detection** | Static + AI logic error hunting |
| **Auto Fix** | Patches with diff + explanation |
| **Documentation** | README, API, architecture, dev guides |
| **Refactoring** | SOLID, design patterns, modularization |
| **Test Generator** | Pytest unit + integration tests |
| **UML** | Class, sequence, component, dependency diagrams |
| **Dependency** | Vulnerability & upgrade analysis |

### Supported Inputs
- 🐙 GitHub Repository (URL or clone)
- 📦 ZIP Project
- 📂 Local Folder
- 📄 Single Source File

### Supported Languages
Python • Java • JavaScript • TypeScript • C • C++ • C# • Go • Rust

### Output Artifacts
- README.md
- Markdown / HTML / PDF Reports
- Architecture & UML Diagrams (Mermaid)
- Unit + Integration Tests (Pytest)
- Git Patch (`.patch`) with diff
- Documentation Suite
- Health Score (0–100)

---

## 🏗️ Architecture

```
┌──────────────────────┐        ┌──────────────────────┐
│   Next.js 15 Frontend│  ◀──▶  │  FastAPI Backend     │
│   (ShadCN + Framer)  │  HTTP  │  (Python 3.11+)      │
└──────────────────────┘        └──────────┬───────────┘
                                            │
                       ┌────────────────────┼─────────────────────┐
                       │                    │                     │
                  ┌────▼─────┐      ┌───────▼────────┐    ┌───────▼────────┐
                  │  Agents  │      │   Services     │    │   MCP Servers  │
                  │ (10x AI) │      │  LLM/VectorDB  │    │ FS / GH / SQL  │
                  └────┬─────┘      └───────┬────────┘    └───────┬────────┘
                       │                    │                     │
                       └────────────────────┴─────────────────────┘
                                            │
                                ┌───────────▼────────────┐
                                │   SQLite + ChromaDB    │
                                └────────────────────────┘
```

The **Coordinator Agent** orchestrates the other nine agents, merges their outputs, and produces a unified **Repository Health Score**.

---

## 🧰 Technology Stack

**Frontend** — Next.js 15, React 19, TypeScript, TailwindCSS, ShadCN UI, Framer Motion, Recharts
**Backend** — Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2
**AI** — Ollama (Gemma 2 / Qwen 2.5 Coder), local-first inference
**Data** — SQLite (relational), ChromaDB (vector embeddings)
**Security** — JWT auth, bcrypt passwords, RBAC, rate limiting, audit log
**Tooling** — Docker, Docker Compose, GitHub Actions CI

---

## 📦 Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | [python.org](https://www.python.org) |
| Node.js | ≥ 20 | [nodejs.org](https://nodejs.org) |
| Ollama | latest | [ollama.com](https://ollama.com) — local LLM runtime |
| Docker (optional) | latest | For containerized deployment |

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in every value:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | 32-byte hex string — generate with `openssl rand -hex 32` |
| `JWT_SECRET` | ✅ | 32-byte hex string — separate from `SECRET_KEY` |
| `APP_ENV` | ✅ | `development` / `staging` / `production` |
| `DATABASE_URL` | — | Default: `sqlite:///./codeguardian.db` |
| `OLLAMA_BASE_URL` | — | Default: `http://localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | — | Default: `gemma2:2b` |
| `GITHUB_TOKEN` | — | Personal access token for private repo import |
| `DEMO_ADMIN_PASSWORD` | — | Overrides the auto-generated dev admin password |

> **Security note:** `SECRET_KEY` and `JWT_SECRET` default to random values if unset, but you should always set them explicitly so they persist across restarts.

---

## 🚀 Running Locally

### 1. Pull an Ollama model
```bash
ollama pull gemma2:2b
# Or for higher quality:
ollama pull qwen2.5-coder:7b
```

### 2. Clone & configure
```bash
git clone https://github.com/your-org/codeguardian-ai.git
cd codeguardian-ai
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and JWT_SECRET
```

### 3. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend (new terminal)
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### 5. Open the app
- UI: **http://localhost:3000**
- API docs (dev only): **http://localhost:8000/docs**

> **Demo login:** On first startup the backend prints the auto-generated admin credentials to the console log. Look for a line like `demo_user_seeded ... password_hint=CG-***`. You can also set `DEMO_ADMIN_PASSWORD` in your `.env`.

---

## 🐳 Docker Setup

```bash
# Start everything (Ollama + Backend + Frontend)
docker compose -f docker/docker-compose.yml up --build

# Pull the model into the Ollama container (first run only)
docker exec -it codeguardian-ollama ollama pull gemma2:2b
```

Open **http://localhost:3000**.

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm run test
```

---

## 📁 Folder Structure

```
codeguardian-ai/
├── backend/                # FastAPI service
│   ├── app/
│   │   ├── agents/         # 10 AI agents
│   │   ├── api/            # Routes, schemas, deps
│   │   ├── core/           # Config, constants, exceptions, logging
│   │   ├── db/             # SQLAlchemy models & session
│   │   ├── mcp/            # MCP server integrations
│   │   ├── security/       # JWT, RBAC, rate limiting
│   │   ├── services/       # LLM, vector DB, reports, analysis runner
│   │   └── utils/          # Filesystem helpers
│   └── requirements.txt
├── frontend/               # Next.js 15 application
│   ├── app/                # App router pages
│   ├── components/         # UI components
│   ├── hooks/              # React hooks (auth, analysis)
│   └── lib/                # API client, utils
├── docker/                 # Dockerfiles & docker-compose
├── docs/                   # Guides, diagrams, API docs (see docs/api.md)
├── tests/                  # Test suites (backend + agents)
├── scripts/                # start.sh / start.ps1 helpers
├── .env.example            # Environment variable template
├── LICENSE                 # MIT
└── README.md
```

---

## 📖 API Documentation

Full API reference: [`docs/api.md`](docs/api.md)

Interactive Swagger UI is available at `http://localhost:8000/docs` in development mode. In production (`APP_ENV=production`) the docs are disabled for security.

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Obtain JWT tokens |
| POST | `/api/v1/auth/register` | Create new account |
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create / import project |
| POST | `/api/v1/analyses` | Start an analysis run |
| GET | `/api/v1/analyses/{id}/status` | Poll analysis progress |
| GET | `/api/v1/reports/{id}/pdf` | Download PDF report |
| GET | `/api/v1/dashboard/summary` | Dashboard KPIs |

---

## 🛡️ Security

- 🔐 JWT authentication with refresh tokens (bcrypt passwords, cost factor 12)
- 👥 Role-based access control (Admin / Reviewer / Viewer)
- 🛑 Rate limiting (sliding-window, per-user/per-IP)
- 🪵 Audit log for every privileged action
- 🧼 PII / secret redaction in all log output
- 🔒 File-type and size validation on uploads
- 🛡️ Zip-slip and tar-slip protection on archive extraction
- 🌱 All secrets via environment variables — never hardcoded

---

## 🗺️ Roadmap

- [ ] WebSocket streaming for live agent progress
- [ ] Redis-backed rate limiter for multi-worker deployments
- [ ] Multi-repo batch analysis
- [ ] Self-hosted runner for CI integrations
- [ ] VS Code extension
- [ ] Slack & Teams notifications
- [ ] SBOM generation
- [ ] Auto-PR creation on GitHub

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit with Conventional Commits: `git commit -m "feat: add streaming progress"`
4. Push and open a Pull Request

Please run `pytest` (backend) and `npm run test && npm run lint` (frontend) before submitting.

---

## 📄 License

MIT © 2026 CodeGuardian AI Contributors. See [LICENSE](LICENSE).

> *"An AI that reviews your code the way a Staff Engineer would — tirelessly, consistently, and at scale."*
#   C o d e G u a r d i a n A I  
 