# CodeGuardian AI — Database Schema

> SQLite (via SQLAlchemy 2.0). All tables use UUID primary keys and
> have UTC timestamps. JSON columns store flexible payloads.

```
┌─────────────┐       ┌─────────────┐       ┌──────────────┐
│   users     │◀──────│  projects   │──────▶│  project_files │
└─────────────┘       └─────────────┘       └──────────────┘
       │                     │
       │                     ▼
       │              ┌──────────────┐
       │              │  analyses    │ (per-project run)
       │              └──────────────┘
       │                     │
       │         ┌───────────┴────────────┐
       │         ▼                        ▼
       │   ┌──────────────┐        ┌──────────────┐
       │   │  agent_runs  │        │  findings    │ (per-agent result)
       │   └──────────────┘        └──────────────┘
       │
       ▼
┌──────────────┐         ┌────────────────────┐
│  audit_logs  │         │  chat_sessions     │
└──────────────┘         └────────────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  chat_messages │
                         └──────────────┘
```

## Table summary

| Table          | Purpose                                                      |
|----------------|--------------------------------------------------------------|
| `users`        | Account, hashed password, role, audit history.               |
| `projects`     | Imported project metadata, language, stats, health score.    |
| `project_files`| File index per project.                                      |
| `analyses`     | One row per analysis run (status, score, duration, summary).  |
| `agent_runs`   | Per-agent execution log (status, duration, confidence, error).|
| `findings`     | Individual issues produced by agents.                        |
| `chat_sessions`| Multi-turn chat with the AI assistant.                       |
| `chat_messages`| Individual messages in a session.                            |
| `audit_logs`   | Append-only log of privileged actions.                        |

## Relationships

- A **user** owns many **projects**.
- A **project** has many **analyses** and many **project_files**.
- An **analysis** has many **agent_runs** and many **findings**.
- A **chat_session** belongs to a user and optionally an analysis.
- Every privileged action (login, register, create, delete) is
  persisted into **audit_logs**.
