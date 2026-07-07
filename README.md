# 🛡️ CodeGuardian AI — Project Documentation

---

## 1. 🎯 The Problem

Modern codebases accumulate risk faster than teams can review it. A single pull request can simultaneously introduce a security hole, a subtle bug, a missed test, an undocumented breaking change, and a vulnerable dependency — and a human reviewer, however good, is optimizing for one lens at a time (usually "does this do what it says"). The result, in most real teams, is:

- 🔓 **Security review is inconsistent.** It happens deeply on some PRs, not at all on others, and almost never on legacy code that "already works."
- 🧹 **Static analysis tools are narrow.** A linter catches style. A SAST tool catches a fixed rule-set of vulnerabilities. Neither explains *why* something matters or proposes a fix in context.
- 📚 **Documentation and tests lag the code.** They're the first things cut under deadline pressure, and nobody owns keeping them current.
- 📦 **Dependency risk is invisible until it's an incident.** Most teams only look at their dependency tree when a CVE makes the news.
- 🧠 **A single generalist reviewer (human or AI) has to context-switch** across all of the above, which measurably degrades depth on each one — the same failure mode that makes single-threaded code review slow and inconsistent in the first place.

> **Problem statement:** given an arbitrary codebase (upload, ZIP, GitHub URL, or folder), produce a trustworthy, multi-dimensional health assessment — security, bugs, code quality, tests, docs, architecture, dependencies — fast enough to fit into a normal review workflow, with actionable findings and auto-generated fixes, not just a wall of warnings.

---

## 2. 💡 The Solution

**CodeGuardian AI** is a **local-first, multi-agent code intelligence platform**. You point it at a project; it fans the work out to **9 specialized AI agents** that each own one dimension of code health, run them in parallel waves, merge their findings into a single weighted health score, and surface everything through a dashboard, a chat interface grounded in your actual code (RAG), and exportable reports.

> 🎯 **Core design goal:** treat code review the way a real engineering org treats it — as several distinct expert disciplines working concurrently, not one generalist skimming everything once.

---

## 3. 🧭 Design Principles

| # | Principle | Why it matters |
|---|---|---|
| 1️⃣ | **Specialization over generalization** | A security agent that only thinks about CWEs/CVSS is more reliable than one prompt trying to be a security reviewer, a linter, and a technical writer simultaneously. |
| 2️⃣ | **Parallelism as a first-class constraint** | The orchestration layer is explicitly built around wave-based concurrency — sequential agent execution doesn't scale to real repositories. |
| 3️⃣ | **Local-first / self-hosted by default** | The LLM layer runs against a local **Ollama** instance — code never has to leave the machine/network it's running on. |
| 4️⃣ | **Fail fast, not silently slow** | Every LLM-dependent path checks backend reachability upfront with a short, cached timeout, instead of letting dozens of calls independently retry against a full timeout. |
| 5️⃣ | **Least privilege by default** | New accounts start as read-only viewers; role elevation is never client-controlled — only an explicit admin action can grant it. |
| 6️⃣ | **Findings must be groundable and actionable** | Every finding carries file/line context; RAG chat is grounded in the project's own embedded source, not general knowledge. |
| 7️⃣ | **Everything server-side, verifiable** | Role checks, source validation, zip-slip protection, and rate limiting all live in the backend — never trusted from the client. |

---

## 4. 🤖 Why Multi-Agent Instead of a Single AI

A single LLM call asked to *"review this code for everything"* has structural weaknesses that a multi-agent design directly addresses:

| ⚠️ Failure mode of a single generalist call | ✅ How the multi-agent design fixes it |
|---|---|
| **Attention dilution** — one prompt covering security + bugs + docs + tests + architecture spreads the model's attention thin. | Each agent has a narrow, dedicated prompt and only that dimension's context — depth instead of width. |
| **No parallelism** — one long generalist call is one long serial wait. | 9 agents run as **2 concurrent waves**, cutting wall-clock time from `N × T` to `max(T_wave1, T_wave2) + T_auto_fix`. |
| **Conflated, unstructured output** — hard to score, store, filter, or feed into a dashboard. | Each agent returns a typed `AgentResult` (findings, summary, confidence) the orchestrator can persist, weight, and aggregate. |
| **No separation of finding vs. fixing** — a model doing both at once tends to do a mediocre job of each. | **Auto-Fix** is a dedicated, later-wave agent that only runs after Wave 1's findings exist. |
| **One point of failure** — if the single call times out or hallucinates, the whole review is gone. | If one agent fails, the others still return — graceful degradation, not total loss. |

⚖️ **Trade-off, accepted deliberately:** multi-agent orchestration costs more total compute than one call and needs its own coordination layer (waves, merging, scoring) — in exchange for depth, structure, and real wall-clock speed through concurrency.

---

## 5. 🏗️ Multi-Agent Architecture

### 5.1 The Nine Agents 🧩

| 🤖 Agent | 🎯 Responsibility |
|---|---|
| 🧭 **Coordinator** | Validates the payload, builds the execution plan, produces the top-level meta-summary used for scoring. |
| 👀 **Code Review** | General code-quality issues — style, complexity, maintainability. |
| 🔐 **Security** | Vulnerability detection with CWE/CVSS-style severity scoring. |
| 🐛 **Bug Detection** | Logic errors, edge cases, likely runtime failures. |
| 📦 **Dependency** | Outdated/vulnerable packages, license and version risk. |
| ♻️ **Refactor** | Structural improvement suggestions. |
| 📄 **Documentation** | Generates/checks docs coverage. |
| 🧪 **Test Generator** | Proposes missing test cases. |
| 📐 **UML** | Extracts architecture/class/sequence relationships into diagrams. |
| 🩹 **Auto-Fix** | Generates patches for issues found in Wave 1. |

### 5.2 Wave-Based Execution ⚡ (the core orchestration idea)

```
                              ⏱  T = 0
                                │
              ┌─────────────────┴─────────────────┐
              │                                     │
     🌊 WAVE 1 (parallel)                  🌊 WAVE 2 (parallel)
     fast · static analysis                generative · independent
     ┌──────────────────────┐               ┌──────────────────────┐
     │ 👀 code_review        │               │ ♻️  refactor          │
     │ 🔐 security           │               │ 📄 documentation      │
     │ 🐛 bug                │               │ 🧪 test               │
     │ 📦 dependency         │               │ 📐 uml                │
     └──────────┬───────────┘               └──────────┬───────────┘
                │                                       │
                └───────────────────┬───────────────────┘
                                     │
                                     ▼
                          🌊 WAVE 3 (dependent)
                          patch · needs Wave 1 output
                          ┌──────────────────────┐
                          │ 🩹 auto_fix           │
                          └──────────┬───────────┘
                                     │
                                     ▼
                         📊 Merged Health Score + Findings
```

Waves 1 and 2 have **no data dependency** on each other, so they execute **simultaneously**. Wave 3 (Auto-Fix) intentionally waits, because a good patch needs to know what's broken first.

> 🚀 This concurrency structure is exactly where the **"3–5× faster than sequential"** claim in the product UI comes from — it's architecture, not a faster model.

### 5.3 Merge & Scoring 📊

Each agent returns a structured result (`findings[]`, `summary{}`, `confidence`). The orchestrator:

1. 💾 Persists every finding to the database, tagged with the originating agent.
2. 🧮 Computes a single weighted **health score (0–100)** from each agent's summary score, using per-category weights, with a security-driven fallback formula if no weighted scores are available.
3. 🗂️ Stores everything against the `Analysis` record so the dashboard, reports, and chat all reference one consistent result set.

### 5.4 Reliability Layer 🛟

Before any wave runs, the orchestrator performs a single **cached, short-timeout reachability check** against the LLM backend (Ollama). If it's unreachable, the analysis fails **immediately** with a clear stored error — instead of every agent, across every file, independently retrying and silently compounding into a run that takes hours. ⏳➡️⚡

---

## 6. 🔑 Key Concepts Used

- 🧩 **Agent specialization & typed contracts** — every agent implements a common `BaseAgent` interface and returns an `AgentResult`.
- 🌊 **Concurrent orchestration (waves, not a DAG scheduler)** — a deliberately simple two-tier dependency model, because the real dependency structure of this problem is that simple.
- 🔍 **RAG (Retrieval-Augmented Generation)** — AI Chat embeds project source into a vector store (Chroma) and grounds answers in retrieved code context.
- 🔐 **RBAC (Role-Based Access Control)** — three roles (`viewer`, `reviewer`, `admin`); roles are never client-assignable except through an explicit admin action.
- 📊 **Health scoring as weighted aggregation** — one number, meaningful because it's a principled combination of independently-produced agent scores.
- 🖥️ **Local-first LLM inference (Ollama)** — a default + fallback model pair (`gemma2:2b` / `qwen2.5-coder:7b`).
- ⚡ **Fail-fast reachability checks** — prevents cascading timeout compounding across many independent calls.
- 🗜️ **Zip-slip-safe extraction** — uploaded archives validated against path traversal before extraction.
- 🔑 **JWT-based auth with bcrypt password hashing.**

---

## 7. 🏛️ System Architecture

```
┌────────────────────────────────────┐        ┌──────────────────────────────────────┐
│  🖥️  FRONTEND (Next.js / React)     │  HTTP  │        ⚙️  BACKEND (FastAPI)           │
│  📊 Dashboard  📤 Upload  💬 Chat    │◄──────►│  🔑 Auth  📁 Projects  🔬 Analyses     │
│  🔐 Security   🐛 Bugs    📄 Docs    │        │  📤 Uploads  🤖 Agents  💬 Chat  👥 Users │
│  📐 Architecture   📑 Reports        │        │  📑 Reports  📊 Dashboard             │
└────────────────────────────────────┘        └───────────────────┬────────────────────┘
                                                                    │
                       ┌────────────────────────────────────────────┼─────────────────────────────┐
                       │                                            │                              │
              ┌────────▼─────────┐                       ┌──────────▼──────────┐        ┌──────────▼──────────┐
              │  🗄️  SQLAlchemy    │                       │  🎛️  Analysis Runner  │        │  🧠 Vector Store      │
              │  Users, Projects,  │                       │  wave scheduler,      │        │  (Chroma) — RAG       │
              │  Findings, ...     │                       │  9 agents, LLM        │        │  embeddings of         │
              └────────────────────┘                       │  reachability         │        │  uploaded code          │
                                                             │  fail-fast check      │        └────────────────────────┘
                                                             └──────────┬────────────┘
                                                                        │
                                                              ┌─────────▼──────────┐
                                                              │  🦙 Ollama           │
                                                              │  (local LLM)         │
                                                              │  ⚡ gemma2:2b (fast)  │
                                                              │  🐢 qwen2.5-coder    │
                                                              │     (fallback)       │
                                                              └──────────────────────┘
```

**📥 Ingestion paths:** GitHub URL · ZIP upload (zip-slip protected) · folder path · single file — all normalized into one project representation before agents ever see it.

**🔐 Auth & authorization:** JWT access/refresh tokens, bcrypt-hashed passwords, RBAC middleware gating every mutating/analysis route.

---

## 8. 🛠️ Technology Stack

### ⚙️ Backend
| Tech | Purpose |
|---|---|
| 🚀 FastAPI (0.115) | Async Python web framework |
| 🗄️ SQLAlchemy (2.0) + Alembic | ORM and migrations |
| ✅ Pydantic v2 / pydantic-settings | Request/response validation and config |
| 🔑 PyJWT + bcrypt | Authentication |
| 🌐 httpx | Async HTTP client (Ollama + GitHub API) |
| 🧠 ChromaDB + onnxruntime | Vector store for RAG embeddings |
| 📑 ReportLab | PDF report generation |
| 🔁 tenacity | Retry logic |
| 🧪 pytest / pytest-asyncio / pytest-cov | Testing |
| 🦙 Ollama | Local LLM inference (`gemma2:2b`, `qwen2.5-coder:7b`) |

### 🖥️ Frontend
| Tech | Purpose |
|---|---|
| ⚛️ Next.js 15 / React 19 / TypeScript | Core framework |
| 🎨 Tailwind CSS + CVA + tailwind-merge | Styling |
| 🧱 Radix UI | Dialog, dropdown, select, tabs, toast, tooltip primitives |
| 🎬 Framer Motion | Animation |
| 📈 Recharts | Dashboard charts |
| 🖍️ react-syntax-highlighter | Code display |
| 🧪 Vitest + Testing Library | Frontend tests |

### 🏗️ Infrastructure
| Tech | Purpose |
|---|---|
| 🐳 Docker / docker-compose | Containerized backend, frontend, Ollama service |
| 🔄 GitHub Actions | CI (backend + frontend jobs) |
| 🗃️ SQLite (default) | Swappable via `DATABASE_URL` |

---

## 9. 🌍 Real-World Use Cases

1. 🔀 **Pre-merge PR triage** — automated multi-dimensional pass before a human reviewer looks at it.
2. 🗺️ **Legacy codebase onboarding** — use RAG chat + UML agent to quickly understand architecture and hotspots.
3. 🛡️ **Security baseline for acquired/inherited code** — immediate security + dependency risk baseline without a lengthy manual audit.
4. 📦 **Continuous dependency hygiene** — scheduled runs to catch drift/vulnerabilities before they become incidents.
5. 📚 **Documentation debt remediation** — close gaps on undocumented/undertested modules incrementally.
6. 📋 **Compliance-adjacent evidence generation** — exportable PDF reports for audits, without exposing source to a third-party SaaS.
7. 🎓 **Educational / code-review training tool** — findings + chat explanations as a guided tour of senior-level review.

---

## 10. 🚀 Future Roadmap

### 🔧 Near-term hardening
- ✅ CI-verified build/test pass on every PR as a merge gate
- 🔁 Multi-worker-safe rate limiting (shared store like Redis)
- 🎟️ Self-service invite/approval flow for role promotion

### 🤖 Agent capability
- 🤝 Cross-agent consensus/conflict resolution
- 🔄 Incremental/differential analysis (diff-only re-analysis)
- 🎯 Confidence-calibrated auto-fix (auto-apply vs. suggestion-only)
- 🔌 Pluggable LLM backends beyond Ollama (opt-in hosted models)

### 🏢 Platform
- 🔗 Native GitHub/GitLab App integration (PR status checks, inline comments)
- 📈 Team-level dashboards and health-score trend tracking
- 🪝 Webhook-based CI triggering on push
- 🏘️ Fine-grained per-project roles (today's RBAC is instance-wide)

### 📡 Scale
- 🐘 Move from SQLite to Postgres for multi-user deployments
- ⚙️ Horizontal scaling of the analysis runner via a proper task queue (Celery/RQ)

---

<div align="center">

**🛡️ CodeGuardian AI** — *nine experts, working in parallel, so your codebase doesn't have to wait.*

</div>
