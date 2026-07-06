# CodeGuardian AI — Architecture

## High-level

```
   ┌──────────────┐        ┌──────────────┐
   │  Next.js 15  │  ◀──▶  │   FastAPI    │
   │  + ShadCN    │  REST  │   + Pydantic │
   │  + Recharts  │  + WS  │              │
   └──────────────┘        └──────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌────────────┐     ┌────────────┐     ┌────────────┐
       │  Agents    │     │  Services  │     │  MCP       │
       │  (10x)     │     │  LLM/Vec   │     │  FS/GH/SQL │
       └─────┬──────┘     └──────┬─────┘     └─────┬──────┘
             │                   │                 │
             └───────────────────┴─────────────────┘
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                  ┌─────────┐         ┌─────────┐
                  │ SQLite  │         │ChromaDB │
                  └─────────┘         └─────────┘
```

## Multi-agent runtime

- `CoordinatorAgent` owns the high-level plan.
- Each agent is a Python class implementing `BaseAgent.run`.
- Agents receive a `payload` dict containing the project files and metadata.
- Agents return an `AgentResult` containing findings, summaries, and confidence.
- The orchestrator persists results and computes the **Repository Health Score**.

## Multi-agent workflow

```
       ┌─────────────┐
       │ Coordinator │
       └──────┬──────┘
              │ plan
   ┌──────────┼──────────┬────────────┬────────────┐
   ▼          ▼          ▼            ▼            ▼
Security  Code Review  Bug  Refactor  Docs   Tests   UML  Deps  AutoFix
   │          │          │            │            │
   └──────────┴──────────┴────────────┴────────────┘
              │
              ▼
        Merge + Score
              │
              ▼
        Reports + UI
```

## MCP integration

```
   Agent ───▶ MCP Client ───▶ MCP Server (stdio/http)
                                │
                                ├─ FilesystemMCP (workspace IO)
                                ├─ GitHubMCP     (clone / metadata)
                                └─ SQLiteMCP     (typed queries)
```
