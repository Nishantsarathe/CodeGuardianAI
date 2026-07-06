# Project folder structure

```
codeguardian-ai/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py
│       │   ├── schemas.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── auth.py
│       │       ├── projects.py
│       │       ├── uploads.py
│       │       ├── analyses.py
│       │       ├── agents.py
│       │       ├── chat.py
│       │       ├── reports.py
│       │       └── dashboard.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── coordinator.py
│       │   ├── code_review.py
│       │   ├── security.py
│       │   ├── bug_detection.py
│       │   ├── auto_fix.py
│       │   ├── documentation.py
│       │   ├── refactor.py
│       │   ├── test_generator.py
│       │   ├── uml.py
│       │   └── dependency.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py
│       │   ├── vector_store.py
│       │   ├── project_service.py
│       │   ├── analysis_runner.py
│       │   ├── report_service.py
│       │   └── chat_service.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── constants.py
│       │   ├── exceptions.py
│       │   └── logging.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   └── models.py
│       ├── security/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── rbac.py
│       │   └── rate_limit.py
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── servers.py
│       └── utils/
│           ├── __init__.py
│           └── filesystem.py
├── frontend/
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── tsconfig.json
│   ├── vitest.config.ts
│   ├── tests/
│   │   ├── setup.ts
│   │   └── utils.test.ts
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── login/page.tsx
│   │   └── (app)/
│   │       ├── layout.tsx
│   │       ├── dashboard/page.tsx
│   │       ├── upload/page.tsx
│   │       ├── analysis/page.tsx
│   │       ├── analysis/[id]/page.tsx
│   │       ├── security/page.tsx
│   │       ├── bugs/page.tsx
│   │       ├── docs/page.tsx
│   │       ├── architecture/page.tsx
│   │       ├── dependencies/page.tsx
│   │       ├── reports/page.tsx
│   │       ├── chat/page.tsx
│   │       └── settings/page.tsx
│   ├── components/
│   │   ├── layout/AppShell.tsx
│   │   └── ui/
│   │       ├── card.tsx
│   │       ├── primitives.tsx
│   │       ├── progress.tsx
│   │       └── status.tsx
│   ├── hooks/
│   │   ├── useAuth.tsx
│   │   └── useAnalysis.tsx
│   └── lib/
│       ├── api.ts
│       └── utils.ts
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── database.md
│   ├── deployment.md
│   ├── roadmap.md
│   ├── testing.md
│   ├── troubleshooting.md
│   ├── folder-structure.md
│   └── diagrams/
│       ├── architecture.mmd
│       ├── workflow.mmd
│       └── mcp.mmd
├── tests/
│   ├── conftest.py
│   ├── backend/
│   │   ├── test_api.py
│   │   └── test_reports.py
│   └── agents/
│       └── test_agents.py
└── scripts/
    ├── start.sh
    └── start.ps1
```
