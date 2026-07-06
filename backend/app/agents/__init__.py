"""Agents package — public surface for the agent runtime."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from .base import AgentResult, BaseAgent, extract_json_blob  # noqa: F401
from .coordinator import CoordinatorAgent  # noqa: F401
from .code_review import CodeReviewAgent  # noqa: F401
from .security import SecurityAgent  # noqa: F401
from .bug_detection import BugDetectionAgent  # noqa: F401
from .auto_fix import AutoFixAgent  # noqa: F401
from .documentation import DocumentationAgent  # noqa: F401
from .refactor import RefactorAgent  # noqa: F401
from .test_generator import TestGeneratorAgent  # noqa: F401
from .uml import UMLAgent  # noqa: F401
from .dependency import DependencyAgent  # noqa: F401


AGENT_REGISTRY: Dict[str, BaseAgent] = {
    "coordinator": CoordinatorAgent(),
    "code_review": CodeReviewAgent(),
    "security": SecurityAgent(),
    "bug": BugDetectionAgent(),
    "auto_fix": AutoFixAgent(),
    "documentation": DocumentationAgent(),
    "refactor": RefactorAgent(),
    "test": TestGeneratorAgent(),
    "uml": UMLAgent(),
    "dependency": DependencyAgent(),
}


def agent_for(name: str) -> BaseAgent:
    if name not in AGENT_REGISTRY:
        raise KeyError(f"Unknown agent: {name}")
    return AGENT_REGISTRY[name]


async def run_agent_safe(agent: BaseAgent, payload: Dict[str, Any]) -> AgentResult:
    """Run an agent and convert any exception into an empty AgentResult."""
    try:
        return await agent.run(payload)
    except Exception as e:  # pragma: no cover
        return AgentResult(
            agent_name=getattr(agent, "name", "unknown"),
            output={"error": str(e)},
            summary={"score": 0, "errors": [str(e)]},
            confidence=0.0,
            error=str(e),
        )
