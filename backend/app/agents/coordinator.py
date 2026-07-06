"""
Coordinator Agent — plans, delegates, and merges agent outputs.

The runtime currently executes a default plan sequentially, so the
Coordinator is mostly responsible for:
  • Validating that the payload is well-formed
  • Producing a top-level summary that the orchestrator uses for the
    repository health score
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import AgentResult, BaseAgent, safe_text


PLAN_ORDER = [
    "code_review", "security", "bug", "refactor",
    "documentation", "test", "uml", "dependency", "auto_fix",
]


class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        meta = self._project_meta(payload)
        plan = PLAN_ORDER
        total_files = meta["file_count"]
        languages = sorted({f.get("language") for f in payload.get("files", []) if f.get("language")})
        # Heuristic top-level plan summary
        summary = {
            "plan": plan,
            "file_count": total_files,
            "languages": languages,
            "score": 80.0 if total_files > 0 else 0.0,
        }
        return AgentResult(
            agent_name=self.name,
            findings=[],
            output={"plan": plan, "meta": meta},
            summary=summary,
            confidence=0.95,
        )
